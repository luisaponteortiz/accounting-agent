"""D-026: fictional card-feed claims and append-only human target selections."""
import json
from .core import ControlError, canonical, digest, instant, text_field, utcnow

CONFLICT='SOURCE_CLAIM_CONFLICT'
ORDER_MIXED='SOURCE_ORDER_MIXED'
SELECT_TARGET='select_supersession_target'


class CardFeedContract:
    def card_locked_hold(self,db,actor,kind,key):
        """Latest identity binding, never an older hold after a valid release."""
        binding=db.execute('SELECT b.* FROM source_periods b JOIN snapshots s ON s.id=b.snapshot_id WHERE s.scope=? AND s.kind=? AND s.source_key=? ORDER BY b.id DESC LIMIT 1',(actor.scope,kind,key)).fetchone()
        if binding and not binding['admitted'] and binding['reason'] in ('SOURCE_MOVED_FROM_LOCKED_PERIOD','LATE_ACTIVITY_IN_LOCKED_PERIOD') and binding['period_id'] and self.period(db,actor,binding['period_id'])['status']=='locked':return binding
        return None

    def card_claim_state(self,db,scope,key):
        declarations=[]
        for e in db.execute("SELECT * FROM accounting_events WHERE scope=? AND item_key=? AND code IN ('SOURCE_CLAIM_DECLARED','SOURCE_CLAIM_CONFLICT_RECORDED','SOURCE_SUPERSESSION_UNRESOLVED') ORDER BY id",(scope,key)):
            value=json.loads(e['payload'])
            sid=value.get('message_snapshot_id',value.get('snapshot_id'))
            if db.execute("SELECT 1 FROM snapshots WHERE scope=? AND kind='transaction' AND source_key=? AND id=?",(scope,key,sid)).fetchone():
                declarations.append((e['created'],e['id'],value['target_key']))
        for link in db.execute("SELECT l.*,o.source_key AS target_key FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id JOIN snapshots o ON o.id=l.old_snapshot_id WHERE l.scope=? AND n.kind='transaction' AND n.source_key=? ORDER BY l.id",(scope,key)):
            declarations.append((link['created'],link['id'],link['target_key']))
        targets=[]
        for _,_,target in sorted(declarations):
            if target not in targets:targets.append(target)
        if not targets:return None
        decision=db.execute("SELECT * FROM dispositions WHERE scope=? AND workflow='card_preparation' AND item_key=? AND code=? AND choice=? AND action='apply' ORDER BY id DESC LIMIT 1",(scope,key,CONFLICT,SELECT_TARGET)).fetchone()
        payload=json.loads(decision['payload']) if decision else {}
        chosen=payload.get('target_key',targets[0])
        return {'targets':targets,'target_key':chosen,'conflicted':len(targets)>1 and not set(targets)<=set(payload.get('declared_targets',[])), 'disposition_id':decision['id'] if decision else None}

    def record_card_claim(self,db,actor,key,target,head_id,message_id):
        state=self.card_claim_state(db,actor.scope,key)
        if state and target in state['targets']:return False
        code='SOURCE_CLAIM_CONFLICT_RECORDED' if state else 'SOURCE_CLAIM_DECLARED'
        self.accounting_event(db,actor,None,key,code,{'snapshot_id':head_id,'message_snapshot_id':message_id,'target_key':target})
        self.store.audit(db,actor.scope,actor.id,'card_source_claim_recorded',{'source_key':key,'target_key':target,'message_snapshot_id':message_id,'code':code})
        if state:self.source_approval_events(db,actor,key,head_id,'APPROVED_SOURCE_REVISED')
        return True

    def card_source_revision(self,db,actor,source,packet):
        key,value=source['key'],source['data'];kind='transaction'
        old=db.execute('SELECT s.*,h.removed FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.scope=? AND h.kind=? AND h.source_key=?',(actor.scope,kind,key)).fetchone()
        as_of=source.get('as_of')
        if type(as_of) is int and as_of>=0:order_type,order_value='sequence',str(as_of)
        elif isinstance(as_of,str):order_type,order_value='timestamp',instant(as_of).isoformat()
        elif as_of is None:order_type,order_value='legacy_arrival',utcnow()
        else:raise ControlError('Invalid source as_of')
        system=source.get('source_system',value.get('source_system','fixture'))
        if system!='fixture':raise ControlError('Only fictional source systems are enabled',403)
        removed=source.get('tombstone',False);reason=source.get('removal_reason')
        if type(removed) is not bool:raise ControlError('Invalid tombstone')
        if removed and reason not in ('feed_removed','voided','superseded'):raise ControlError('Removal reason required')
        target=source.get('supersedes') or value.get('supersedes_source_id');predecessor=None
        if target:
            target=target if ':' in target else value['account_id']+':'+target
            predecessor=db.execute('SELECT * FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(actor.scope,kind,target)).fetchone()
            if target==key:raise ControlError('Supersession requires a different source identity')
            if predecessor and any(r['source_key']==key for r in self.supersession_refs(db,actor.scope,predecessor['snapshot_id'])):raise ControlError('Supersession cycle is not permitted')
        state=self.card_claim_state(db,actor.scope,key)
        different=bool(target and state and target!=state['target_key'])
        meta=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(old['id'],)).fetchone() if old else None
        accepted=True
        if meta and meta['order_type']!='legacy_arrival':
            if order_type!=meta['order_type']:accepted=False
            elif order_type=='sequence' and int(order_value)<int(meta['as_of']):accepted=False
            elif order_type=='timestamp' and order_value<meta['as_of']:accepted=False
            elif order_value==meta['as_of'] and digest(value)!=old['hash']:accepted=False
        same_order=as_of is None or bool(meta and meta['order_type']==order_type and meta['as_of']==order_value)
        # D-038 / UC-21: a row retired by a live replacement is the same row when its
        # message is re-sent unchanged, claim included. A re-send that omits a claim
        # the row has is a later omission (clause 6) and keeps its earlier handling.
        retired=bool(old and old['removed'] and not removed and bool(target)==bool(state) and self.retired_by_live_replacement(db,actor.scope,key))
        same_row=bool(old and old['hash']==digest(value) and (old['removed']==int(removed) or retired))
        # A repeated claim changes no source lifecycle row. Batch evidence is
        # retained by intake, including its supplier, before this call.
        if same_row and same_order and (not target or state):
            changed=self.record_card_claim(db,actor,key,target,old['id'],old['id']) if target else False
            if not target:
                binding=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(old['id'],)).fetchone()
                if binding and binding['reason']=='UNASSIGNED_ACCOUNTING_PERIOD':self.bind_source(db,actor,old['id'],value,packet.get('period_id'))
            return old['id'],changed
        if old and not accepted:
            # D-038 / UC-22: a message with no order value has only its arrival time,
            # so it is recognised on file by its content and kept once.
            unordered=order_type=='legacy_arrival'
            if unordered:retained=db.execute("SELECT s.id FROM snapshots s JOIN source_metadata m ON m.snapshot_id=s.id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND s.hash=? AND m.order_type='legacy_arrival' AND m.tombstone=? ORDER BY s.id DESC LIMIT 1",(actor.scope,kind,key,digest(value),int(removed))).fetchone()
            else:retained=db.execute('SELECT s.id FROM snapshots s JOIN source_metadata m ON m.snapshot_id=s.id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND s.hash=? AND m.order_type=? AND m.as_of=? AND m.tombstone=? ORDER BY s.id DESC LIMIT 1',(actor.scope,kind,key,digest(value),order_type,order_value,int(removed))).fetchone()
            if retained:
                if unordered:self.record_order_mixed(db,actor,key,old['id'],retained['id'],digest(value),meta['order_type'])
                changed=self.record_card_claim(db,actor,key,target,old['id'],retained['id']) if target else False
                if changed and not state:self.apply_first_card_claim(db,actor,key,old['id'],target,predecessor,packet)
                return old['id'],changed
        force=bool(old and (not same_order or not same_row or target and not state))
        sid,is_new=self.store.snapshot(db,actor.scope,kind,key,value,actor.id,force_version=force)
        if not is_new:return sid,False
        db.execute('INSERT INTO source_metadata VALUES(?,?,?,?,?,?,?,?)',(sid,actor.scope,system,order_type,order_value,int(removed),reason,packet.get('period_id') or value.get('period_id')))
        if not accepted:
            self.store.audit(db,actor.scope,actor.id,'older_or_conflicting_source_retained',{'snapshot_id':sid,'governing_snapshot_id':old['id']})
            if order_type=='legacy_arrival':self.record_order_mixed(db,actor,key,old['id'],sid,digest(value),meta['order_type'])
            changed=self.record_card_claim(db,actor,key,target,old['id'],sid) if target else False
            if changed and not state:self.apply_first_card_claim(db,actor,key,old['id'],target,predecessor,packet)
            return sid,changed
        db.execute('INSERT INTO source_heads(scope,kind,source_key,snapshot_id,removed) VALUES(?,?,?,?,?) ON CONFLICT(scope,kind,source_key) DO UPDATE SET snapshot_id=excluded.snapshot_id,removed=excluded.removed',(actor.scope,kind,key,sid,int(removed)))
        if target:self.record_card_claim(db,actor,key,target,sid,sid)
        if target and not different:self.apply_first_card_claim(db,actor,key,sid,target,predecessor,packet)
        if different and old:
            binding=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(old['id'],)).fetchone()
            if binding:db.execute('INSERT INTO source_periods(scope,snapshot_id,period_id,admitted,reason,created) VALUES(?,?,?,?,?,?)',(actor.scope,sid,binding['period_id'],binding['admitted'],binding['reason'],utcnow()))
        self.bind_source(db,actor,sid,value,packet.get('period_id') or value.get('period_id'))
        if old and (old['hash']!=digest(value) or removed):self.source_approval_events(db,actor,key,sid,'APPROVED_SOURCE_REMOVED' if removed else 'APPROVED_SOURCE_REVISED')
        self.store.audit(db,actor.scope,actor.id,'source_revision_accepted',{'snapshot_id':sid,'source_key':key,'as_of':order_value,'ordering':order_type,'removed':removed,'reason':reason})
        return sid,True

    def record_order_mixed(self,db,actor,key,governing_id,message_id,message_hash,governing_order):
        """D-038 / UC-22: flag, once per distinct content, a message with no order value for a row governed by one."""
        for event in db.execute('SELECT payload FROM accounting_events WHERE scope=? AND item_key=? AND code=?',(actor.scope,key,ORDER_MIXED)):
            if json.loads(event['payload']).get('message_hash')==message_hash:return False
        self.accounting_event(db,actor,None,key,ORDER_MIXED,{'snapshot_id':governing_id,'message_snapshot_id':message_id,'message_hash':message_hash,'governing_order_type':governing_order})
        self.store.audit(db,actor.scope,actor.id,'card_source_order_mixed',{'source_key':key,'message_snapshot_id':message_id,'governing_snapshot_id':governing_id,'governing_order_type':governing_order})
        return True

    def card_feed_anomalies(self,db,scope):
        """Unordered messages retained against ordered card rows, for display and export."""
        result=[]
        for event in db.execute('SELECT * FROM accounting_events WHERE scope=? AND code=? ORDER BY id',(scope,ORDER_MIXED)):
            value=json.loads(event['payload'])
            binding=db.execute('SELECT period_id FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(value['snapshot_id'],)).fetchone()
            result.append({'source_key':event['item_key'],'reason':ORDER_MIXED,'period_id':binding['period_id'] if binding else None,'message_snapshot_id':value['message_snapshot_id'],
                           'governing_snapshot_id':value['snapshot_id'],'governing_order_type':value['governing_order_type'],'event_id':event['id'],'created':event['created'],
                           'meaning':'A message with no order value was kept as evidence; it does not govern this row.'})
        return result

    def apply_first_card_claim(self,db,actor,key,sid,target,predecessor,packet):
        if not predecessor:
            self.accounting_event(db,actor,None,key,'SOURCE_SUPERSESSION_UNRESOLVED',{'snapshot_id':sid,'target_key':target})
        elif not self.supersession_link(db,actor.scope,sid):
            db.execute("INSERT INTO source_links(scope,old_snapshot_id,new_snapshot_id,reason,created) VALUES(?,?,?,'superseded',?)",(actor.scope,predecessor['snapshot_id'],sid,utcnow()))
            for ancestor in {r['source_key'] for r in self.supersession_refs(db,actor.scope,sid)}:self.source_approval_events(db,actor,ancestor,sid,'APPROVED_SOURCE_SUPERSEDED')

    def card_claim_conflicts(self,db,actor,period,sources):
        if not any(s['kind']=='transaction' for s in sources):return {}
        # Without any declaration or link in this scope, no identity can have
        # competing claims. Avoid ancestry scans on ordinary unclaimed feeds.
        if (not db.execute('SELECT 1 FROM source_links WHERE scope=? LIMIT 1',(actor.scope,)).fetchone()
            and not db.execute("SELECT 1 FROM accounting_events WHERE scope=? AND code IN ('SOURCE_CLAIM_DECLARED','SOURCE_CLAIM_CONFLICT_RECORDED','SOURCE_SUPERSESSION_UNRESOLVED') LIMIT 1",(actor.scope,)).fetchone()):return {}
        result={}
        for source in sources:
            if source['kind']!='transaction':continue
            keys=[source['source_key']]+[r['source_key'] for r in self.supersession_refs(db,actor.scope,source['id'])]
            states={key:self.card_claim_state(db,actor.scope,key) for key in keys}
            conflicts={key:state for key,state in states.items() if state and state['conflicted']}
            if conflicts:result[source['source_key']]=conflicts
        return result

    def card_target_selections(self,db,actor,workflow,sources):
        if workflow!='card_preparation':return []
        records=list(db.execute("SELECT * FROM dispositions WHERE scope=? AND workflow=? AND choice=? AND action='apply' ORDER BY id",(actor.scope,workflow,SELECT_TARGET)))
        if not records:return []
        keys=set()
        for source in sources:
            if source['kind']=='transaction':
                keys.add(source['source_key'])
                keys.update(r['source_key'] for r in self.supersession_refs(db,actor.scope,source['id']))
        result=[]
        for record in records:
            row=dict(record)
            if row['item_key'] not in keys:continue
            state=self.card_claim_state(db,actor.scope,row['item_key'])
            if state and not state['conflicted'] and state['disposition_id']==row['id']:
                row['payload']=json.loads(row['payload']);row['evidence']=json.loads(row['evidence']);result.append(row)
        return result

    def card_selection_history(self,db,actor,workflow,sources):
        """Selection authorship survives confirmation, replacement and later contests.

        This is provenance, separate from the latest active disposition used to
        clear a blocker. Ordinary disposition activation is unchanged.
        """
        if workflow!='card_preparation':return {}
        records=[dict(r) for r in db.execute("SELECT id,item_key,actor FROM dispositions WHERE scope=? AND workflow=? AND code=? AND choice=? AND action='apply' ORDER BY id",(actor.scope,workflow,CONFLICT,SELECT_TARGET))]
        if not records:return {}
        # Previously selected ancestry remains part of authorship even when a
        # later authorized selection changes the governing link.
        parents={}
        for link in db.execute("SELECT n.source_key AS child,o.source_key AS parent FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id JOIN snapshots o ON o.id=l.old_snapshot_id WHERE l.scope=? AND n.scope=? AND o.scope=? AND n.kind='transaction' AND o.kind='transaction' ORDER BY l.id",(actor.scope,actor.scope,actor.scope)):
            parents.setdefault(link['child'],set()).add(link['parent'])
        result={}
        for source in sources:
            if source['kind']!='transaction':continue
            keys=set();pending=[source['source_key']]
            while pending:
                key=pending.pop()
                if key in keys:continue
                keys.add(key);pending.extend(parents.get(key,()))
            history=[r for r in records if r['item_key'] in keys]
            if history:result[source['source_key']]=history
        return result

    def select_source_target(self,actor,workflow,period_id,key,payload,evidence,reason,scope_kind):
        if workflow!='card_preparation' or scope_kind!='single_item':raise ControlError('Card target selection requires single-item card preparation')
        self.authorize(actor,('reviewer',));text_field(reason,'disposition reason',2000)
        with self.store.transaction() as db:
            self.require_grant(db,actor,'disposition')
            row=db.execute("SELECT s.*,h.removed FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.scope=? AND h.kind='transaction' AND h.source_key=?",(actor.scope,key)).fetchone()
            state=self.card_claim_state(db,actor.scope,key);target=payload.get('target_key')
            if not row or not state or len(state['targets'])<2 or target not in state['targets']:raise ControlError('Declared contested source target required',409)
            source=dict(row,value=json.loads(row['payload']))
            home=db.execute('SELECT * FROM periods WHERE scope=? AND start<=? AND end>=?',(actor.scope,source['value']['date'],source['value']['date'])).fetchone()
            if not home or home['period_id']!=period_id:raise ControlError('Use the source accounting-date period')
            if home['status']=='locked':raise ControlError('PERIOD_LOCKED',409)
            for batch in db.execute("SELECT actor,payload FROM snapshots WHERE scope=? AND kind='batch'",(actor.scope,)):
                for message in json.loads(batch['payload']).get('sources',[]):
                    claim=message.get('supersedes') or message.get('data',{}).get('supersedes_source_id')
                    if claim and ':' not in claim:claim=message['data'].get('account_id','')+':'+claim
                    if message['kind']=='transaction' and message['key']==key and claim in state['targets'] and batch['actor']==actor.id:raise ControlError('Claim message supplier cannot disposition either claim',403)
            affected=[s for s in self.store.latest(db,actor.scope,'transaction') if s['source_key']==key or any(r['source_key']==key for r in self.supersession_refs(db,actor.scope,s['id']))]
            ctx=self.context(db,actor,period_id,workflow)
            available=list({s['id']:s for s in ctx['sources']+[source]+[s for s in self.store.latest(db,actor.scope) if any(self.supports_item(item,s) for item in [source]+affected)]}.values())
            allowed=self.disposition_references(db,actor.scope,source,available)
            if not evidence or any(allowed.get(e.get('snapshot_id'))!=e.get('hash') for e in evidence):raise ControlError('Current scoped evidence references required')
            documents=[s for s in available if any(s['id']==e.get('snapshot_id') for e in evidence)]
            if not any(self.supports_item(item,doc) for item in [source]+affected for doc in documents):raise ControlError('Related receipt, document or statement required as supporting evidence')
            predecessor=db.execute("SELECT snapshot_id FROM source_heads WHERE scope=? AND kind='transaction' AND source_key=?",(actor.scope,target)).fetchone()
            if predecessor and (target==key or any(r['source_key']==key for r in self.supersession_refs(db,actor.scope,predecessor['snapshot_id']))):raise ControlError('Supersession cycle is not permitted')
            new_origin=self.source_origin(db,actor.scope,predecessor['snapshot_id']) if predecessor else None
            changing=target!=state['target_key']
            if changing:
                for item in [source]+affected:
                    binding=self.card_locked_hold(db,actor,'transaction',item['source_key'])
                    if binding:
                        if not new_origin or new_origin['period_id']!=binding['period_id']:self.require_grant(db,actor,'lock')
            chosen={'target_key':target,'declared_targets':state['targets']}
            rid=db.execute("INSERT INTO dispositions(scope,workflow,period_id,item_key,code,choice,payload,evidence,source_hash,actor,reason,action,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,'apply',?)",(actor.scope,workflow,period_id,key,CONFLICT,SELECT_TARGET,canonical(chosen),canonical(evidence),row['hash'],actor.id,reason,utcnow())).lastrowid
            self.accounting_event(db,actor,period_id,key,'SOURCE_CLAIM_TARGET_SELECTED',dict(chosen,disposition_id=rid,snapshot_id=row['id']))
            if changing:
                if predecessor:
                    db.execute("INSERT INTO source_links(scope,old_snapshot_id,new_snapshot_id,reason,created) VALUES(?,?,?,'authorized_target_selection',?)",(actor.scope,predecessor['snapshot_id'],row['id'],utcnow()))
                    for ancestor in {r['source_key'] for r in self.supersession_refs(db,actor.scope,row['id'])}:self.source_approval_events(db,actor,ancestor,row['id'],'APPROVED_SOURCE_SUPERSEDED')
                else:self.accounting_event(db,actor,None,key,'SOURCE_SUPERSESSION_UNRESOLVED',{'snapshot_id':row['id'],'target_key':target})
                for item in sorted(affected,key=lambda s:-len(self.supersession_refs(db,actor.scope,s['id']))):self.bind_source(db,actor,item['id'],item['value'],period_id,allow_locked_release=True)
                for receipt in self.store.latest(db,actor.scope,'receipt'):
                    if any(self.supports_item(item,receipt) for item in affected):self.bind_source(db,actor,receipt['id'],receipt['value'],period_id,allow_locked_release=True)
            self.store.audit(db,actor.scope,actor.id,'source_claim_target_selected',{'disposition_id':rid,'source_key':key,'target_key':target,'reason':reason})
            self.package_changes(db,actor)
            return rid
