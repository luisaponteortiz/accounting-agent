"""Scoped accounting knowledge and human-authority controls (local synthetic only)."""
import json
from .core import Actor, ControlError, canonical, day, digest, instant, normalize, require_keys, text_field, utcnow


class AccountingControls:
    def grant_authority(self,actor,subject,permissions,reason,effective_from='0001-01-01',effective_to='9999-12-31'):
        self.authorize(actor,('administrator',))
        if actor.kind!='human':raise ControlError('Human administrator required',403)
        allowed={'review','approve_rule','approve_profile','approve_mandate','disposition','finalize','lock'}
        if not set(permissions)<=allowed or not permissions:raise ControlError('Invalid authority grant')
        text_field(subject,'subject');text_field(reason,'grant reason');day(effective_from);day(effective_to)
        with self.store.transaction() as db:
            for permission in permissions:
                if not db.execute('SELECT 1 FROM authority_grants WHERE scope=? AND subject=? AND permission=? AND effective_from=? AND effective_to=?',(actor.scope,subject,permission,effective_from,effective_to)).fetchone():
                    db.execute('INSERT INTO authority_grants(scope,subject,permission,effective_from,effective_to,issuer,reason,synthetic) VALUES(?,?,?,?,?,?,?,1)',(actor.scope,subject,permission,effective_from,effective_to,actor.id,reason))
            self.store.audit(db,actor.scope,actor.id,'synthetic_authority_granted',{'subject':subject,'permissions':permissions,'reason':reason})

    def require_grant(self,db,actor,permission):
        if actor.kind!='human' or not db.execute('SELECT 1 FROM authority_grants WHERE scope=? AND subject=? AND permission=? AND effective_from<=? AND effective_to>=?',(actor.scope,actor.id,permission,utcnow()[:10],utcnow()[:10])).fetchone():
            raise ControlError('Human authority grant required: '+permission,403)

    def approved_profile(self,db,actor,date=None,allow_proposed=False):
        date=date or '9999-12-31'
        row=db.execute("SELECT s.* FROM snapshots s JOIN profile_proposals p ON p.snapshot_id=s.id WHERE s.scope=? AND p.effective_from<=? AND (p.effective_to IS NULL OR p.effective_to>=?) AND (SELECT d.decision FROM profile_decisions d WHERE d.scope=s.scope AND d.snapshot_id=s.id ORDER BY d.id DESC LIMIT 1)='approve' ORDER BY p.effective_from DESC,s.id DESC LIMIT 1",(actor.scope,date,date)).fetchone()
        if not row and allow_proposed:row=db.execute("SELECT * FROM snapshots WHERE scope=? AND kind='profile' ORDER BY id DESC LIMIT 1",(actor.scope,)).fetchone()
        if not row:raise ControlError('POLICY_NOT_APPROVED',409)
        return row

    def approve_profile_version(self,actor,snapshot_id,reason):
        self.authorize(actor,('reviewer',));text_field(reason,'approval reason',2000)
        with self.store.transaction() as db:
            self.require_grant(db,actor,'approve_profile')
            p=db.execute('SELECT p.*,s.actor,s.payload FROM profile_proposals p JOIN snapshots s ON s.id=p.snapshot_id WHERE p.scope=? AND p.snapshot_id=?',(actor.scope,snapshot_id)).fetchone()
            if not p:raise ControlError('Proposed profile not found',404)
            if p['actor']==actor.id:raise ControlError('Profile proposer cannot approve',403)
            if db.execute('SELECT 1 FROM profile_decisions WHERE scope=? AND snapshot_id=?',(actor.scope,snapshot_id)).fetchone():raise ControlError('Profile already decided',409)
            db.execute('INSERT INTO profile_decisions(scope,snapshot_id,decision,actor,reason,created) VALUES(?, ?,\'approve\',?,?,?)',(actor.scope,snapshot_id,actor.id,reason,utcnow()))
            for r in db.execute('SELECT id FROM policy_rules WHERE scope=? AND profile_id=?',(actor.scope,snapshot_id)).fetchall():self._decide_rule(db,actor,r['id'],'approve',reason)
            self.retire_withdrawn_profile_rules(db,actor,snapshot_id,p)
            db.execute('UPDATE clients SET profile_id=?,generation=generation+1 WHERE scope=?',(snapshot_id,actor.scope))
            self.package_changes(db,actor)
            self.store.audit(db,actor.scope,actor.id,'profile_approved',{'snapshot_id':snapshot_id,'reason':reason})

    def retire_withdrawn_profile_rules(self,db,actor,snapshot_id,proposal):
        from datetime import timedelta
        profile=json.loads(proposal['payload']);start=day(proposal['effective_from'])
        end=(start-timedelta(days=1)).isoformat() if start.toordinal()>1 else '0000-12-31'
        present={('vendor_mapping',v['id']) for v in profile['vendors']}|{('review_policy','review'),('close_checklist','close')}
        managed={(r['kind'],r['rule_key']) for r in db.execute("SELECT DISTINCT kind,rule_key FROM policy_rules WHERE scope=? AND profile_id IS NOT NULL",(actor.scope,))}
        for kind,key in managed-present:
            rows=db.execute("SELECT r.id FROM policy_rules r JOIN rule_decisions d ON d.rule_id=r.id AND d.scope=r.scope WHERE r.scope=? AND r.kind=? AND r.rule_key=? AND d.decision='approve'",(actor.scope,kind,key)).fetchall()
            for row in rows:
                db.execute('INSERT INTO rule_retirements(scope,rule_id,effective_to,actor,profile_id,created) VALUES(?,?,?,?,?,?)',(actor.scope,row['id'],end,actor.id,snapshot_id,utcnow()))
                self.store.audit(db,actor.scope,actor.id,'rule_retired',{'rule_id':row['id'],'effective_to':end,'profile_id':snapshot_id})

    def propose_rule(self,actor,kind,key,value,effective_from,effective_to=None,item_key=None,supersedes=None,evidence=None,profile_id=None):
        self.authorize(actor,('preparer','worker'));day(effective_from)
        if effective_to and day(effective_to)<day(effective_from):raise ControlError('Invalid rule window')
        if kind not in ('vendor_mapping','receipt_matching','review_policy','close_checklist','statement_policy'):raise ControlError('Unsupported rule kind')
        self.validate_rule(kind,value)
        with self.store.transaction() as db:
            return self._propose_rule(db,actor,kind,key,value,effective_from,effective_to,item_key,supersedes,evidence or [],profile_id)

    def validate_rule(self,kind,value):
        if kind not in ('receipt_matching','vendor_mapping','close_checklist','review_policy','statement_policy'):raise ControlError('Unsupported rule kind')
        if kind=='statement_policy':
            require_keys(value,{'allow_without_line_ids'})
            if type(value['allow_without_line_ids']) is not bool:raise ControlError('Explicit statement line-identity policy required')
        elif kind=='receipt_matching':
            require_keys(value,{'date_window_days','amount_tolerance','multiple_receipts','vendor_method','statement_substitution'})
            if value['date_window_days'] is not None and (type(value['date_window_days']) is not int or not 0<=value['date_window_days']<=31):raise ControlError('Invalid receipt date window')
            from .core import money
            if value['amount_tolerance'] is not None and money(value['amount_tolerance'])<0:raise ControlError('Invalid receipt tolerance')
            if value['vendor_method'] not in (None,'exact_alias'):raise ControlError('Unsupported vendor method')
            for key in ('multiple_receipts','statement_substitution'):
                if value[key] is not None and type(value[key]) is not bool:raise ControlError('Invalid receipt matching flag')
        elif kind=='vendor_mapping':
            require_keys(value,{'id','name','aliases','category'})
            if not value['aliases'] or any(not normalize(a) for a in value['aliases']):raise ControlError('Invalid vendor aliases')
        elif kind=='close_checklist':
            if not isinstance(value,list):raise ControlError('Invalid close checklist')
            for r in value:
                if not isinstance(r,dict):raise ControlError('Close checklist requirements must be typed objects')
                if r.get('type') not in ('workflow_outcome','reconciliation','tieout','document'):raise ControlError('Invalid checklist requirement type')
                if r['type']=='workflow_outcome' and r.get('workflow') not in ('card_preparation','journal_preparation'):raise ControlError('Unavailable workflow outcome')
                if r['type']!='workflow_outcome' and not r.get('document_type'):raise ControlError('Document type required')
        elif kind=='review_policy':
            require_keys(value,{'receipt_required','review','model_review_required'})
            if value['review']!='independent_human':raise ControlError('Independent review required')

    def _propose_rule(self,db,actor,kind,key,value,start,end,item,supersedes,evidence,profile_id):
        if supersedes:
            prior=db.execute('SELECT * FROM policy_rules WHERE scope=? AND id=?',(actor.scope,supersedes)).fetchone()
            if not prior or prior['kind']!=kind or prior['rule_key']!=key:raise ControlError('Rule supersession scope mismatch',403)
        version=db.execute('SELECT COUNT(*) FROM policy_rules WHERE scope=? AND kind=? AND rule_key=?',(actor.scope,kind,key)).fetchone()[0]+1
        rid=db.execute('INSERT INTO policy_rules(scope,kind,rule_key,version,value,effective_from,effective_to,item_key,supersedes,proposed_by,proposer_kind,evidence,profile_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(actor.scope,kind,key,version,canonical(value),start,end,item,supersedes,actor.id,actor.kind,canonical(evidence),profile_id)).lastrowid
        self.store.audit(db,actor.scope,actor.id,'rule_proposed',{'rule_id':rid,'kind':kind,'normalized_aliases':[normalize(a) for a in value['aliases']] if kind=='vendor_mapping' else None})
        return rid

    def _decide_rule(self,db,actor,rid,decision,reason):
        self.require_grant(db,actor,'approve_rule')
        r=db.execute('SELECT * FROM policy_rules WHERE scope=? AND id=?',(actor.scope,rid)).fetchone()
        if not r:raise ControlError('Rule not found',404)
        if r['proposed_by']==actor.id:raise ControlError('Rule proposer cannot approve/reject',403)
        if db.execute('SELECT 1 FROM rule_decisions WHERE scope=? AND rule_id=?',(actor.scope,rid)).fetchone():raise ControlError('Rule already decided',409)
        db.execute('INSERT INTO rule_decisions(scope,rule_id,decision,actor,reason,created) VALUES(?,?,?,?,?,?)',(actor.scope,rid,decision,actor.id,reason,utcnow()))
        self.store.audit(db,actor.scope,actor.id,'rule_'+decision,{'rule_id':rid,'reason':reason})

    def approve_rule(self,actor,rule_id,reason):
        self.authorize(actor,('reviewer',))
        with self.store.transaction() as db:self._decide_rule(db,actor,rule_id,'approve',text_field(reason,'reason',2000));self.package_changes(db,actor)

    def reject_rule(self,actor,rule_id,reason):
        self.authorize(actor,('reviewer',))
        with self.store.transaction() as db:self._decide_rule(db,actor,rule_id,'reject',text_field(reason,'reason',2000))

    def rules_at(self,db,scope,date,item_key=None):
        rows=db.execute("SELECT r.*,d.actor AS approved_by FROM policy_rules r JOIN rule_decisions d ON d.rule_id=r.id AND d.scope=r.scope WHERE r.scope=? AND d.decision='approve' AND r.effective_from<=? AND (r.effective_to IS NULL OR r.effective_to>=?) AND (r.item_key IS NULL OR r.item_key=?) AND NOT EXISTS(SELECT 1 FROM rule_retirements t WHERE t.scope=r.scope AND t.rule_id=r.id AND t.effective_to<?) ORDER BY r.effective_from,r.id",(scope,date,date,item_key,date)).fetchall()
        chosen={}
        for r in sorted(rows,key=lambda r:(r["item_key"] is not None,r["effective_from"],r["id"])):chosen[(r['kind'],r['rule_key'])]=dict(r,value=json.loads(r['value']))
        return list(chosen.values())

    def applied_rule_lineage(self,db,scope,rule,item_data):
        if rule['kind'] not in ('vendor_mapping','receipt_matching'):return [rule]
        # Relevant semantic coverage survives optional links, renamed keys and a
        # general policy re-proposed just for this item.
        transaction=item_data.get('transaction',{})
        item_key=transaction.get('account_id','')+':'+transaction.get('source_id','') if transaction else rule['item_key']
        earlier=db.execute("SELECT r.*,d.actor AS approved_by FROM policy_rules r JOIN rule_decisions d ON d.rule_id=r.id AND d.scope=r.scope AND d.decision='approve' WHERE r.scope=? AND r.kind=? AND (r.item_key IS NULL OR r.item_key=?) AND r.id<? ORDER BY r.id",(scope,rule['kind'],item_key,rule['id'])).fetchall()
        candidates={r['id']:dict(r,value=json.loads(r['value'])) for r in earlier}
        result=[rule];seen={rule['id']};parent=rule.get('supersedes')
        while parent and parent not in seen:
            seen.add(parent)
            row=db.execute("SELECT r.*,d.actor AS approved_by FROM policy_rules r LEFT JOIN rule_decisions d ON d.rule_id=r.id AND d.scope=r.scope AND d.decision='approve' WHERE r.scope=? AND r.id=? AND r.kind=? AND (r.item_key IS NULL OR r.item_key=?)",(scope,parent,rule['kind'],item_key)).fetchone()
            if not row:break
            candidates[row['id']]=dict(row,value=json.loads(row['value']))
            parent=row['supersedes']
        for previous in candidates.values():
            same=False
            if rule['kind']=='vendor_mapping':
                alias=normalize(item_data.get('transaction',{}).get('description',''))
                same=bool(alias and alias in [normalize(a) for a in previous['value']['aliases']] and previous['value']['category']==rule['value']['category'])
            else:same=previous['value']==rule['value']
            if same:result.append(previous)
        return result

    def rule_records(self,db,scope):
        records=[dict(r) for r in db.execute('SELECT * FROM policy_rules WHERE scope=? ORDER BY id',(scope,))]
        for rule in records:
            decision=db.execute('SELECT decision,actor FROM rule_decisions WHERE scope=? AND rule_id=? ORDER BY id DESC LIMIT 1',(scope,rule['id'])).fetchone()
            rule['status']=decision['decision'] if decision else 'proposed'
            rule['approved_by']=decision['actor'] if decision and decision['decision']=='approve' else None
            retired=db.execute('SELECT MIN(effective_to) FROM rule_retirements WHERE scope=? AND rule_id=?',(scope,rule['id'])).fetchone()[0]
            rule['effective_end']=min(rule['effective_to'] or '9999-12-31',retired or '9999-12-31')
            if rule['kind']=='vendor_mapping':rule['normalized_aliases']=[normalize(a) for a in json.loads(rule['value'])['aliases']]
        for rule in records:
            if rule['kind']=='vendor_mapping':
                rule['alias_collisions']=[other['id'] for other in records if other['kind']=='vendor_mapping' and other['rule_key']!=rule['rule_key'] and other['status']!='reject' and other['effective_from']<=rule['effective_end'] and rule['effective_from']<=other['effective_end'] and (not other['item_key'] or not rule['item_key'] or other['item_key']==rule['item_key']) and set(other['normalized_aliases'])&set(rule['normalized_aliases'])]
        return records

    def validate_freshness(self,workflows,freshness):
        from .modules import CAPABILITIES,WORKFLOWS
        if not isinstance(freshness,dict) or not freshness:raise ControlError('Nonempty freshness predicate required')
        if 'none' in freshness:
            if set(freshness)!={'none'}:raise ControlError('No-evidence reason must be the sole freshness entry')
            text_field(freshness['none'],'explicit no-evidence reason',2000)
            return dict(freshness)
        kinds={kind for wf in workflows for step in WORKFLOWS[wf].steps for kind in CAPABILITIES[step.capability].reads if kind!='$workflow'}
        result={}
        for kind,cutoff in freshness.items():
            if kind not in kinds:raise ControlError('Freshness kind is not read by these workflows')
            result[kind]='occurrence_start' if cutoff=='occurrence_start' else instant(cutoff).isoformat()
        return result

    def approve_mandate(self,actor,mandate_id,reason):
        self.authorize(actor,('reviewer',));text_field(reason,'mandate approval reason')
        with self.store.transaction() as db:
            self.require_grant(db,actor,'approve_mandate')
            m=db.execute('SELECT * FROM mandates WHERE scope=? AND id=?',(actor.scope,mandate_id)).fetchone()
            if not m:raise ControlError('Mandate not found',404)
            if m['issuer']==actor.id:raise ControlError('Mandate issuer cannot approve',403)
            self.validate_freshness(json.loads(m['workflows']),json.loads(m['freshness']))
            bound={}
            for workflow in json.loads(m['workflows']):
                target=self.mandate_period(db,actor,m,m['starts'],allow_missing=True)
                ctx=self.context(db,actor,target,workflow)
                bound[workflow]=self.policy_signature(db,ctx)
            db.execute("UPDATE mandates SET active=1,status='active',approved_by=?,bound_rules=?,reason=? WHERE scope=? AND id=?",(actor.id,canonical(bound),reason,actor.scope,mandate_id))
            self.store.audit(db,actor.scope,actor.id,'mandate_approved',{'mandate_id':mandate_id,'bound_rules':bound,'freshness':json.loads(m['freshness']),'reason':reason})

    def mandate_period(self,db,actor,mandate,occurrence,allow_missing=False):
        rule=json.loads(mandate['period_rule'])
        if rule['kind']=='fixed':
            target=rule['period_id']
            row=db.execute('SELECT period_id FROM periods WHERE scope=? AND period_id=?',(actor.scope,target)).fetchone()
        else:
            date=occurrence[:10]
            if rule['kind']=='previous_month':
                from datetime import timedelta
                date=(day(date).replace(day=1)-timedelta(days=1)).isoformat()
            row=db.execute('SELECT period_id FROM periods WHERE scope=? AND start<=? AND end>=?',(actor.scope,date,date)).fetchone()
        if row:return row['period_id']
        if allow_missing:return None
        raise ControlError('Accounting period for occurrence not configured',409)

    def mandate_fresh(self,db,actor,mandate,period_id,occurrence):
        required=json.loads(mandate['freshness'])
        if not required:return False
        if set(required)=={'none'}:return bool(isinstance(required['none'],str) and required['none'].strip())
        sources=self.period_sources(db,actor,period_id)
        for kind,cutoff in required.items():
            cutoff=occurrence if cutoff=='occurrence_start' else instant(cutoff).isoformat()
            candidates=[s for s in sources if s['kind']==kind]
            if not any((m:=db.execute('SELECT * FROM source_metadata WHERE snapshot_id=?',(s['id'],)).fetchone()) and m['order_type']=='timestamp' and m['as_of']>=cutoff for s in candidates):return False
        return True


    def policy_signature(self,db,ctx):
        period=ctx['period'] or {'start':'0001-01-01','end':'9999-12-31'}
        kinds={'review_policy'}|{kind for cap in ctx['manifest']['capabilities'] for kind in cap['rule_reads']}
        rules=[]
        for row in db.execute("SELECT r.* FROM policy_rules r JOIN rule_decisions d ON d.scope=r.scope AND d.rule_id=r.id AND d.decision='approve' WHERE r.scope=? AND r.effective_from<=? AND (r.effective_to IS NULL OR r.effective_to>=?) ORDER BY r.id",(ctx['scope'],period['end'],period['start'])):
            if row['kind'] not in kinds:continue
            retired=db.execute('SELECT MIN(effective_to) FROM rule_retirements WHERE scope=? AND rule_id=?',(ctx['scope'],row['id'])).fetchone()[0]
            end=min(row['effective_to'] or '9999-12-31',retired or '9999-12-31',period['end'])
            if end<period['start']:continue
            rules.append({'id':row['id'],'version':row['version'],'effective_from':row['effective_from'] if row['effective_from']>period['start'] else None,'effective_to':end if end<period['end'] else None,'item_key':row['item_key']})
        return {'rule_ids':[r['id'] for r in rules],'policy_windows':rules,'accounting_profile_hash':digest(ctx['manifest']['profile_sections'])}
