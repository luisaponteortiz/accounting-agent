"""Ordered source lifecycle and scoped provenance; no connector operations."""
import json
from .core import ControlError, canonical, digest, instant, utcnow
from .feed_contract import CardFeedContract


class SourceControl(CardFeedContract):
    def source_revision(self,db,actor,source,packet):
        if source['kind']=='transaction':return self.card_source_revision(db,actor,source,packet)
        kind,key,value=source['kind'],source['key'],source['data']
        old=db.execute('SELECT s.*,h.removed FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.scope=? AND h.kind=? AND h.source_key=?',(actor.scope,kind,key)).fetchone()
        as_of=source.get('as_of')
        if type(as_of) is int and as_of>=0:order_type,order_value='sequence',str(as_of)
        elif isinstance(as_of,str):order_type,order_value='timestamp',instant(as_of).isoformat()
        elif as_of is None:order_type,order_value='legacy_arrival',utcnow()
        else:raise ControlError('Invalid source as_of')
        system=source.get('source_system',value.get('source_system','fixture'))
        if system!='fixture':raise ControlError('Only fictional source systems are enabled',403)
        removed=source.get('tombstone',False)
        if type(removed) is not bool:raise ControlError('Invalid tombstone')
        reason=source.get('removal_reason')
        if removed and reason not in ('feed_removed','voided','superseded'):raise ControlError('Removal reason required')
        supersedes=source.get('supersedes') or value.get('supersedes_source_id')
        predecessor=None
        if supersedes:
            old_key=supersedes if ':' in supersedes else value.get('account_id','')+':'+supersedes
            predecessor=db.execute('SELECT * FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(actor.scope,kind,old_key)).fetchone()
            if old_key==key:raise ControlError('Supersession requires a different source identity')
            if predecessor and any(ref['source_key']==key for ref in self.supersession_refs(db,actor.scope,predecessor['snapshot_id'])):
                raise ControlError('Supersession cycle is not permitted')
        oldmeta=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(old['id'],)).fetchone() if old else None
        # D-038 / UC-21: an identical repeat of a receipt that was retired with its
        # replaced charge changes nothing while that replacement is live.
        if (kind=='receipt' and old and old['removed'] and not removed and old['hash']==digest(value) and oldmeta and not oldmeta['tombstone']
                and (as_of is None or (oldmeta['order_type']==order_type and oldmeta['as_of']==order_value))
                and self.retired_by_live_replacement(db,actor.scope,value['account_id']+':'+value['transaction_source_id'])):
            return old['id'],False
        force=bool(old and int(removed)!=old['removed']) or bool(oldmeta and (oldmeta['order_type']!=order_type or oldmeta['as_of']!=order_value) and as_of is not None)
        if predecessor and not db.execute('SELECT 1 FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id WHERE l.scope=? AND n.kind=? AND n.source_key=? AND l.old_snapshot_id=?',(actor.scope,kind,key,predecessor['snapshot_id'])).fetchone():force=True
        if supersedes and not predecessor and old and (self.pending_claim(db,actor.scope,kind,key) or {}).get('target_key')!=old_key:force=True
        sid,is_new=self.store.snapshot(db,actor.scope,kind,key,value,actor.id,force_version=force)
        if not is_new:
            b=db.execute('SELECT * FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(sid,)).fetchone()
            if b and not b['admitted'] and b['reason']=='UNASSIGNED_ACCOUNTING_PERIOD':self.bind_source(db,actor,sid,value,packet.get('period_id'))
            return sid,False
        accepted=True
        if oldmeta and order_type==oldmeta['order_type'] and order_type!='legacy_arrival':
            if (int(order_value)<int(oldmeta['as_of']) if order_type=='sequence' else order_value<oldmeta['as_of']):accepted=False
            if order_value==oldmeta['as_of'] and old['hash']!=digest(value):accepted=False
        elif oldmeta and order_type!=oldmeta['order_type'] and oldmeta['order_type']!='legacy_arrival':accepted=False
        db.execute('INSERT INTO source_metadata VALUES(?,?,?,?,?,?,?,?)',(sid,actor.scope,system,order_type,order_value,int(removed),reason,packet.get('period_id') or value.get('period_id')))
        if not accepted:
            self.store.audit(db,actor.scope,actor.id,'older_or_conflicting_source_retained',{'snapshot_id':sid,'governing_snapshot_id':old['id'] if old else None})
            return sid,False
        db.execute('INSERT INTO source_heads(scope,kind,source_key,snapshot_id,removed) VALUES(?,?,?,?,?) ON CONFLICT(scope,kind,source_key) DO UPDATE SET snapshot_id=excluded.snapshot_id,removed=excluded.removed',(actor.scope,kind,key,sid,int(removed)))
        if supersedes and not predecessor:
            self.accounting_event(db,actor,None,key,'SOURCE_SUPERSESSION_UNRESOLVED',{'snapshot_id':sid,'target_key':old_key})
        if predecessor:
            db.execute("INSERT INTO source_links(scope,old_snapshot_id,new_snapshot_id,reason,created) VALUES(?,?,?,'superseded',?)",(actor.scope,predecessor['snapshot_id'],sid,utcnow()))
            for ancestor_key in {ref['source_key'] for ref in self.supersession_refs(db,actor.scope,sid)}:
                self.source_approval_events(db,actor,ancestor_key,sid,'APPROVED_SOURCE_SUPERSEDED')
        self.bind_source(db,actor,sid,value,packet.get('period_id') or value.get('period_id'))
        if old and (old['hash']!=digest(value) or removed):
            self.source_approval_events(db,actor,key,sid,'APPROVED_SOURCE_REMOVED' if removed else 'APPROVED_SOURCE_REVISED')
        self.store.audit(db,actor.scope,actor.id,'source_revision_accepted',{'snapshot_id':sid,'source_key':key,'as_of':order_value,'ordering':order_type,'removed':removed,'reason':reason})
        return sid,True

    def retired_by_live_replacement(self,db,scope,key):
        """D-038 / UC-21: this card row's head was retired by a replacement that still governs and is admitted.

        A row the provider itself withdrew, a row whose replacement the provider
        withdrew, and a row no live row's governing chain reaches keep their
        earlier behaviour: restoration is not decided here (U4, UC-17). So does
        a row whose live replacement is held, for instance under a locked
        period: its re-send is still recorded and takes the hold with its chain.
        """
        head=db.execute("SELECT h.removed,m.tombstone FROM source_heads h LEFT JOIN source_metadata m ON m.snapshot_id=h.snapshot_id WHERE h.scope=? AND h.kind='transaction' AND h.source_key=?",(scope,key)).fetchone()
        if not head or not head['removed'] or head['tombstone']:return False
        for live in self.store.latest(db,scope,'transaction'):
            if any(ref['source_key']==key for ref in self.supersession_refs(db,scope,live['id'])):
                binding=db.execute('SELECT admitted FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(live['id'],)).fetchone()
                return bool(binding and binding['admitted'])
        return False

    def supersession_link(self,db,scope,snapshot_id):
        source=db.execute('SELECT kind,source_key FROM snapshots WHERE scope=? AND id=?',(scope,snapshot_id)).fetchone()
        if source and source['kind']=='transaction':
            state=self.card_claim_state(db,scope,source['source_key'])
            if state:
                return db.execute('SELECT l.* FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id JOIN snapshots o ON o.id=l.old_snapshot_id WHERE l.scope=? AND n.kind=? AND n.source_key=? AND o.source_key=? ORDER BY n.version DESC,l.id DESC LIMIT 1',(scope,'transaction',source['source_key'],state['target_key'])).fetchone()
        return db.execute('SELECT l.* FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id JOIN snapshots current ON current.id=? WHERE l.scope=? AND n.scope=? AND n.kind=current.kind AND n.source_key=current.source_key ORDER BY n.version DESC,l.id DESC LIMIT 1',(snapshot_id,scope,scope)).fetchone()

    def supersession_refs(self,db,scope,snapshot_id):
        result=[];seen=set()
        while snapshot_id not in seen:
            seen.add(snapshot_id);link=self.supersession_link(db,scope,snapshot_id)
            if not link:break
            row=db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(scope,link['old_snapshot_id'])).fetchone()
            result.append({'snapshot_id':row['id'],'source_key':row['source_key'],'hash':row['hash'],'version':row['version'],'link_id':link['id']})
            snapshot_id=row['id']
        return result

    def evidence_revisions(self,db,scope,sources):
        result={}
        for source in sources:
            if source['kind'] not in ('receipt','document','statement'):continue
            changes=[]
            for earlier in db.execute('SELECT s.*,h.removed,current.payload AS head_payload FROM snapshots s LEFT JOIN source_heads h ON h.scope=s.scope AND h.kind=s.kind AND h.source_key=s.source_key LEFT JOIN snapshots current ON current.id=h.snapshot_id WHERE s.scope=? AND s.kind=? AND s.id<? ORDER BY s.id',(scope,source['kind'],source['id'])):
                same_key=earlier['source_key']==source['source_key']
                value=json.loads(earlier['payload'])
                identity_fields={'receipt':('account_id','transaction_source_id'),'statement':('account_id','period_start','period_end')}.get(source['kind'])
                head_value=json.loads(earlier['head_payload']) if earlier['head_payload'] else {}
                replaced=bool(not same_key and identity_fields and all(value.get(k)==source['value'].get(k) for k in identity_fields) and (earlier['removed'] or any(head_value.get(k)!=source['value'].get(k) for k in identity_fields)))
                if not same_key and not replaced:continue
                fields=sorted(k for k in set(value)|set(source['value']) if value.get(k)!=source['value'].get(k))
                if not fields:continue
                changes.append({'kind':'replaced' if replaced else 'revised','source_kind':source['kind'],'source_key':source['source_key'],'earlier':{'snapshot_id':earlier['id'],'source_key':earlier['source_key'],'hash':earlier['hash'],'version':earlier['version'],'supplier':earlier['actor']},'current':{'snapshot_id':source['id'],'source_key':source['source_key'],'hash':source['hash'],'version':source['version'],'supplier':source['actor']},'changed_fields':fields,'supplier':source['actor']})
            if changes:result[source['source_key']]=changes
        return result

    def source_identity(self,db,scope,snapshot_id):
        row=db.execute('SELECT kind,source_key FROM snapshots WHERE scope=? AND id=?',(scope,snapshot_id)).fetchone()
        if not row:raise ControlError('Origin source outside client scope',403)
        ancestors=self.supersession_refs(db,scope,snapshot_id)
        return (row['kind'],ancestors[-1]['source_key'] if ancestors else row['source_key'])

    def prior_statement_acceptances(self,db,actor,period,sources):
        """Bind continuity to active, item-bound revision acceptance in its own period."""
        if not period:return {}
        prior=self.period_sources(db,actor,period['period_id'])
        revisions=self.evidence_revisions(db,actor.scope,prior)
        accepted=self.active_dispositions(db,actor,'card_preparation',period['period_id'],prior,revisions)
        result={}
        for statement in sources:
            if statement['kind']!='statement' or statement['value']['period_end']!=period['end'] or not revisions.get(statement['source_key']):continue
            value=statement['value']
            items={s['source_key'] for s in prior if s['kind']=='transaction' and s['value']['account_id']==value['account_id'] and value['period_start']<=s['value']['date']<=value['period_end']}
            decisions=[d for d in accepted if d['choice']=='revised_evidence_accepted' and d['item_key'] in items and statement['id'] in d['payload'].get('revision_snapshot_ids',[])]
            covered={d['item_key'] for d in decisions}
            result[statement['source_key']]={'period_id':period['period_id'],'statement_snapshot_id':statement['id'],'accepted':bool(items) and items<=covered,'relying_item_keys':sorted(items),'accepted_item_keys':sorted(covered),'acceptances':[{'id':d['id'],'actor':d['actor'],'item_key':d['item_key']} for d in decisions]}
        return result

    def pending_claim(self,db,scope,kind,key):
        """Latest recorded claim for an identity, until that identity has a link."""
        head=db.execute('SELECT snapshot_id FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(scope,kind,key)).fetchone()
        if not head or self.supersession_link(db,scope,head['snapshot_id']):return None
        if kind=='transaction':
            state=self.card_claim_state(db,scope,key)
            if state:return {'snapshot_id':head['snapshot_id'],'target_key':state['target_key']}
        for event in db.execute("SELECT payload FROM accounting_events WHERE scope=? AND code='SOURCE_SUPERSESSION_UNRESOLVED' AND item_key=? ORDER BY id DESC",(scope,key)):
            claim=json.loads(event['payload'])
            if db.execute('SELECT 1 FROM snapshots WHERE scope=? AND id=? AND kind=? AND source_key=?',(scope,claim['snapshot_id'],kind,key)).fetchone():return claim
        return None

    def resolve_pending_supersessions(self,db,actor):
        """Resolve event-backed claims without editing their historical evidence."""
        # Include removed heads: a later replacement may already have retired
        # the claimant. Its recorded intent still belongs to this identity.
        claimants=db.execute("SELECT DISTINCT s.* FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id JOIN accounting_events e ON e.scope=h.scope AND e.item_key=h.source_key WHERE h.scope=? AND e.code='SOURCE_SUPERSESSION_UNRESOLVED' ORDER BY s.kind,s.source_key",(actor.scope,)).fetchall()
        for claimant in claimants:
            claim=self.pending_claim(db,actor.scope,claimant['kind'],claimant['source_key'])
            if not claim:continue
            target=db.execute('SELECT snapshot_id FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(actor.scope,claimant['kind'],claim['target_key'])).fetchone()
            if not target or any(ref['source_key']==claimant['source_key'] for ref in self.supersession_refs(db,actor.scope,target['snapshot_id'])):continue
            db.execute("INSERT INTO source_links(scope,old_snapshot_id,new_snapshot_id,reason,created) VALUES(?,?,?,'superseded',?)",(actor.scope,target['snapshot_id'],claimant['id'],utcnow()))
            for ancestor_key in {ref['source_key'] for ref in self.supersession_refs(db,actor.scope,claimant['id'])}:
                self.source_approval_events(db,actor,ancestor_key,claimant['id'],'APPROVED_SOURCE_SUPERSEDED')

    def rebind_chained_sources(self,db,actor,requested_period):
        """Re-evaluate live descendants after intake changes their ancestry."""
        chained=[(len(self.supersession_refs(db,actor.scope,s['id'])),s) for s in self.store.latest(db,actor.scope,'transaction')]
        for depth,source in sorted(chained,key=lambda item:(item[0],item[1]['id'])):
            if depth:self.bind_source(db,actor,source['id'],source['value'],requested_period)

    def source_origin(self,db,scope,snapshot_id):
        """Resolve admitted or quarantined origins across the entire identity chain."""
        owners=[]
        for sid in [snapshot_id]+[r['snapshot_id'] for r in self.supersession_refs(db,scope,snapshot_id)]:
            source=db.execute('SELECT kind,source_key FROM snapshots WHERE scope=? AND id=?',(scope,sid)).fetchone()
            head=db.execute('SELECT removed FROM source_heads WHERE scope=? AND kind=? AND source_key=?',(scope,source['kind'],source['source_key'])).fetchone()
            blocked=db.execute("SELECT b.period_id FROM source_heads h JOIN source_periods b ON b.snapshot_id=h.snapshot_id JOIN periods p ON p.scope=b.scope AND p.period_id=b.period_id WHERE h.scope=? AND h.kind=? AND h.source_key=? AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=h.snapshot_id) AND b.reason='SOURCE_MOVED_FROM_LOCKED_PERIOD' AND p.status='locked'",(scope,source['kind'],source['source_key'])).fetchone()
            if source['kind']=='transaction' and not blocked:
                blocked=db.execute("SELECT b.period_id FROM source_heads h JOIN source_periods b ON b.snapshot_id=h.snapshot_id JOIN periods p ON p.scope=b.scope AND p.period_id=b.period_id WHERE h.scope=? AND h.kind='transaction' AND h.source_key=? AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=h.snapshot_id) AND b.admitted=0 AND b.reason='LATE_ACTIVITY_IN_LOCKED_PERIOD' AND p.status='locked'",(scope,source['source_key'])).fetchone()
            admitted=db.execute('SELECT b.period_id,p.status FROM snapshots s JOIN source_periods b ON b.snapshot_id=s.id JOIN periods p ON p.scope=b.scope AND p.period_id=b.period_id WHERE s.scope=? AND s.kind=? AND s.source_key=? AND b.admitted=1 ORDER BY s.version DESC,b.id DESC LIMIT 1',(scope,source['kind'],source['source_key'])).fetchone()
            owners.append((source,head,blocked,admitted))
        # A late link must not hide a still-live locked ancestor behind this
        # identity's earlier destination admission. A quarantined withdrawal has
        # not released its locked population; an admitted withdrawal has.
        for source,head,blocked,admitted in owners[1:]:
            if head and not head['removed']:
                if blocked:return dict(blocked,source_key=source['source_key'])
                if admitted and admitted['status']=='locked':return dict(admitted,source_key=source['source_key'])
            elif head:
                withdrawal=db.execute("SELECT b.period_id FROM source_heads h JOIN source_periods b ON b.snapshot_id=h.snapshot_id JOIN periods p ON p.scope=b.scope AND p.period_id=b.period_id WHERE h.scope=? AND h.kind=? AND h.source_key=? AND b.id=(SELECT MAX(x.id) FROM source_periods x WHERE x.snapshot_id=h.snapshot_id) AND b.admitted=0 AND b.reason='LATE_ACTIVITY_IN_LOCKED_PERIOD' AND p.status='locked'",(scope,source['kind'],source['source_key'])).fetchone()
                if withdrawal:return dict(withdrawal,source_key=source['source_key'])
        for source,head,blocked,admitted in owners:
            if blocked:return dict(blocked,source_key=source['source_key'])
            if admitted:return dict(admitted,source_key=source['source_key'])
        return None

    def apply_supersession(self,db,actor,snapshot_id):
        link=self.supersession_link(db,actor.scope,snapshot_id)
        if not link:return
        binding=db.execute('SELECT admitted FROM source_periods WHERE snapshot_id=? ORDER BY id DESC LIMIT 1',(snapshot_id,)).fetchone()
        if not binding or not binding['admitted']:return
        for ref in self.supersession_refs(db,actor.scope,snapshot_id):
            old=db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(actor.scope,ref['snapshot_id'])).fetchone()
            db.execute('UPDATE source_heads SET removed=1 WHERE scope=? AND kind=? AND source_key=?',(actor.scope,old['kind'],old['source_key']))
            if old['kind']=='transaction':
                value=json.loads(old['payload'])
                for receipt in self.store.latest(db,actor.scope,'receipt'):
                    if receipt['value']['account_id']==value['account_id'] and receipt['value']['transaction_source_id']==value['source_id']:
                        db.execute("UPDATE source_heads SET removed=1 WHERE scope=? AND kind='receipt' AND source_key=?",(actor.scope,receipt['source_key']))

    def source_had_approval(self,db,scope,key,period_id):
        for a in db.execute('SELECT a.* FROM artifacts a JOIN runs r ON r.id=a.run_id WHERE a.scope=? AND r.period_id=?',(scope,period_id)):
            evidence=json.loads(a['payload']).get('data',{}).get('evidence',[])
            if a['item_key']==key or any(e.get('source_key')==key for e in evidence):
                if db.execute("SELECT 1 FROM decisions WHERE scope=? AND artifact_id=? AND decision IN ('approve','resolve_approve')",(scope,a['id'])).fetchone():return True
        return False

    def source_approval_events(self,db,actor,key,snapshot_id,code):
        for a in db.execute('SELECT a.*,r.period_id FROM artifacts a JOIN runs r ON r.id=a.run_id WHERE a.scope=?',(actor.scope,)).fetchall():
            evidence=json.loads(a['payload']).get('data',{}).get('evidence',[])
            if (a['item_key']==key or any(e.get('source_key')==key for e in evidence)) and db.execute("SELECT 1 FROM decisions WHERE scope=? AND artifact_id=? AND decision IN ('approve','resolve_approve')",(actor.scope,a['id'])).fetchone():
                self.accounting_event(db,actor,a['period_id'],a['item_key'],code,{'artifact_id':a['id'],'source_key':key,'snapshot_id':snapshot_id})

    def accounting_event(self,db,actor,period_id,item_key,code,value):
        db.execute('INSERT INTO accounting_events(scope,period_id,item_key,code,payload,actor,created) VALUES(?,?,?,?,?,?,?)',(actor.scope,period_id,item_key,code,canonical(value),actor.id,utcnow()))
