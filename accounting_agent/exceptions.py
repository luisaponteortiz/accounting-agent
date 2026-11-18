"""Evidence-bound item decisions. Dispositions never confer review or posting authority."""
import json
from decimal import Decimal
from .modules import card_duplicates, supporting_revisions
from .core import ControlError, canonical, money, text_field, utcnow

VOCABULARY={
 'EVIDENCE_REVISED_REQUIRES_REVIEW':{'revised_evidence_accepted'},
 'POSSIBLE_DUPLICATE':{'distinct_purchases','duplicate_of','source_replay'},
 'UNKNOWN_VENDOR':{'confirm_vendor'},'UNKNOWN_CATEGORY':{'code_category'},
 'CREDIT_REQUIRES_REVIEW':{'refund_of','standalone_credit'},
 'NON_EXPENSE_REQUIRES_REVIEW':{'settlement_of_card_liability','transfer','standalone_credit','code_fee','code_interest'},
 'SPLIT_REQUIRES_REVIEW':{'allocate'},
 'SOURCE_TRANSITION_REQUIRES_REVIEW':{'settlement_verified'},
 'CURRENCY_MISMATCH':{'refer_external'},'PENDING_TRANSACTION':{'refer_external'},'MISSING_RECEIPT':{'refer_external'},
}
for code in ('RECEIPT_AMOUNT_POLICY_UNSET','RECEIPT_AMOUNT_MISMATCH','RECEIPT_DATE_POLICY_UNSET','RECEIPT_DATE_MISMATCH','RECEIPT_VENDOR_POLICY_UNSET','RECEIPT_VENDOR_MISMATCH','RECEIPT_MULTIPLE_POLICY_UNSET','MULTIPLE_RECEIPTS_REQUIRE_REVIEW','RECEIPT_CURRENCY_MISMATCH','RECEIPT_REUSED'):VOCABULARY[code]={'refer_external'}
for choices in VOCABULARY.values():choices.add('refer_external')

class ExceptionControls:
    def supports_item(self,source,document):
        item,value=source['value'],document['value']
        if source['kind']=='transaction':
            if document['kind']=='receipt':return value['account_id']==item['account_id'] and value['transaction_source_id']==item['source_id']
            if document['kind']=='statement':return value['account_id']==item['account_id'] and value['period_start']<=item['date']<=value['period_end']
        if source['kind']=='journal' and document['kind']=='document':
            return value['document_type']=='journal_support' and source['source_key'] in value.get('journal_keys',[])
        return False

    def disposition_references(self,db,scope,source,sources):
        allowed={s['id']:s['hash'] for s in sources}
        allowed.update({r['snapshot_id']:r['hash'] for r in self.supersession_refs(db,scope,source['id'])})
        return allowed

    def active_dispositions(self,db,actor,workflow,period_id,sources,evidence_revisions=None):
        heads={s['source_key']:s for s in sources};result=self.card_target_selections(db,actor,workflow,sources)
        if evidence_revisions is None:evidence_revisions=self.evidence_revisions(db,actor.scope,sources)
        for r in db.execute("SELECT * FROM dispositions d WHERE scope=? AND workflow=? AND period_id=? AND action='apply' AND NOT EXISTS(SELECT 1 FROM dispositions x WHERE x.scope=d.scope AND x.prior_id=d.id AND x.action='revoke') ORDER BY id",(actor.scope,workflow,period_id)):
            row=dict(r);source=heads.get(row['item_key']);evidence=json.loads(row['evidence'])
            allowed=self.disposition_references(db,actor.scope,source,sources) if source else {}
            if row['choice']=='select_supersession_target':continue
            if source and source['hash']==row['source_hash'] and all(allowed.get(e['snapshot_id'])==e['hash'] for e in evidence):
                row['payload']=json.loads(row['payload']);row['evidence']=evidence
                if row['choice']=='settlement_verified' and row['payload'].get('transition_refs')!=self.supersession_refs(db,actor.scope,source['id']):continue
                if row['choice']=='revised_evidence_accepted':
                    current=sorted({r['current']['snapshot_id'] for r in supporting_revisions(source,sources,evidence_revisions)})
                    if row['payload'].get('revision_snapshot_ids')!=current:continue
                if row['code']=='POSSIBLE_DUPLICATE':
                    vendors=[r['value'] for r in self.rules_at(db,actor.scope,source['value']['date'],source['source_key']) if r['kind']=='vendor_mapping']
                    candidates=card_duplicates(source,[s for s in sources if s['kind']=='transaction'],vendors)
                    current=sorted((s['source_key'],s['hash']) for s in candidates)
                    bound=row['payload'].get('duplicate_candidate_set')
                    if bound is None or sorted((s['source_key'],s['hash']) for s in bound)!=current:continue
                result.append(row)
        chosen={}
        for r in result:chosen[(r['item_key'],r['code'])]=r
        return list(chosen.values())

    def disposition(self,actor,workflow,period_id,item_key,code,choice,payload,evidence,reason,scope_kind='single_item'):
        if code=='SOURCE_CLAIM_CONFLICT' and choice=='select_supersession_target':return self.select_source_target(actor,workflow,period_id,item_key,payload,evidence,reason,scope_kind)
        self.authorize(actor,('reviewer',));text_field(reason,'disposition reason',2000)
        if scope_kind not in ('single_item','propose_rule'):raise ControlError('Unsupported disposition scope')
        if choice not in VOCABULARY.get(code,set()):raise ControlError('Unsupported disposition; this control cannot be overridden')
        with self.store.transaction() as db:
            self.require_grant(db,actor,'disposition')
            if self.period(db,actor,period_id)['status']=='locked':raise ControlError('PERIOD_LOCKED',409)
            ctx=self.context(db,actor,period_id,workflow);source=next((s for s in ctx['sources'] if s['source_key']==item_key),None)
            current=self.governing_id(db,actor.scope,workflow,period_id,item_key)
            a=db.execute('SELECT * FROM artifacts WHERE scope=? AND id=?',(actor.scope,current)).fetchone()
            if not source or not a or code not in json.loads(a['blockers']):raise ControlError('No governing exception for this source',409)
            allowed=self.disposition_references(db,actor.scope,source,ctx['sources'])
            if not evidence or any(allowed.get(e.get('snapshot_id'))!=e.get('hash') for e in evidence):raise ControlError('Current scoped evidence references required')
            supporting=[]
            data=json.loads(a['payload'])['data']
            targets=[source]
            if choice in ('distinct_purchases','duplicate_of','source_replay'):
                candidates=data.get('duplicate_population',data.get('duplicate_candidates',[]))
                targets += [dict(r,value=json.loads(r['payload'])) for ref in candidates for r in [db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(actor.scope,ref['snapshot_id'])).fetchone()] if r]
            for ref in evidence:
                row=db.execute('SELECT * FROM snapshots WHERE scope=? AND id=?',(actor.scope,ref['snapshot_id'])).fetchone()
                if row:
                    document=dict(row,value=json.loads(row['payload']))
                    if any(self.supports_item(target,document) for target in targets):supporting.append(document)
            if not supporting:raise ControlError('Related receipt, document or statement required as supporting evidence')
            if choice=='distinct_purchases':
                for candidate in targets:
                    value=candidate['value']
                    if not any(doc['kind']=='receipt' and doc['value']['account_id']==value['account_id'] and doc['value']['transaction_source_id']==value['source_id'] for doc in supporting):raise ControlError('Distinct purchases requires supporting documents for the item and every candidate')
            if choice=='settlement_of_card_liability' and source['value'].get('activity')!='payment':raise ControlError('Settlement requires a payment source')
            if choice=='transfer' and source['value'].get('activity')!='transfer':raise ControlError('Transfer requires a transfer source')
            if scope_kind=='propose_rule':
                rule=payload.get('rule',{})
                self.validate_rule(rule.get('kind'),rule.get('value'))
                from .core import day
                day(rule['effective_from'])
                return self._propose_rule(db,actor,rule['kind'],rule['key'],rule['value'],rule['effective_from'],None,None,None,evidence,None)
            activity=source['value'].get('activity');amount=money(source['value'].get('amount','0.00'))
            neutral=choice=='revised_evidence_accepted'
            if activity=='payment' and not neutral and choice not in ('settlement_of_card_liability','refer_external'):raise ControlError('Payments require settlement or referral')
            if activity=='transfer' and not neutral and choice not in ('transfer','refer_external'):raise ControlError('Transfers require transfer treatment or referral')
            if activity=='unknown' and not neutral and choice!='refer_external':raise ControlError('Unknown activity requires referral')
            if choice in ('standalone_credit','refund_of') and not (activity=='credit' or activity=='purchase' and amount<0):raise ControlError('Credit treatment requires credit activity')
            if choice=='code_fee' and (activity!='fee' or amount<=0):raise ControlError('Fee treatment requires positive fee activity')
            if choice=='code_interest' and (activity!='interest' or amount<=0):raise ControlError('Interest treatment requires positive interest activity')
            expense={a['id'] for a in ctx['profile']['accounts'] if a['active'] and a['type']=='expense'}
            assets={a['id'] for a in ctx['profile']['accounts'] if a['active'] and a['type']=='asset'}
            assets-=set(ctx['profile'].get('card_liabilities',{}).values())
            accounts=expense
            if choice in ('code_category','standalone_credit','refund_of','confirm_vendor','code_fee','code_interest') and payload.get('account_id') not in accounts:raise ControlError('Active account required')
            if choice in ('settlement_of_card_liability','transfer') and payload.get('cash_account') not in assets:raise ControlError('Active cash/clearing account required')
            if choice in ('duplicate_of','source_replay') and payload.get('duplicate_of') not in {s['source_key'] for s in ctx['sources'] if s['kind']=='transaction' and s['source_key']!=item_key}:raise ControlError('Scoped duplicate target required')
            if choice in ('duplicate_of','source_replay') and any(d['item_key']==payload.get('duplicate_of') and d['choice'] in ('duplicate_of','source_replay') for d in ctx['dispositions']):raise ControlError('Duplicate target is already excluded; retain a live survivor')
            if choice=='refund_of':
                target=next((s for s in ctx['sources'] if s['kind']=='transaction' and s['source_key']==payload.get('refund_of')),None)
                if not target or target['value']['currency']!=source['value']['currency'] or target['value']['account_id']!=source['value']['account_id'] or money(target['value']['amount'])<=0:raise ControlError('Scoped original purchase reference required')
            if choice=='allocate':
                if activity!='purchase' or amount<=0:raise ControlError('Allocations require positive purchase activity')
                lines=payload.get('allocations',[])
                if not lines or len(lines)>99 or any(l.get('account_id') not in accounts or money(l['amount'])<=0 for l in lines) or sum((money(l['amount']) for l in lines),Decimal('0.00'))!=money(source['value']['amount']):raise ControlError('Allocation must sum exactly to charge')
            payload=dict(payload)
            if choice=='settlement_verified':
                payload['transition_refs']=self.supersession_refs(db,actor.scope,source['id'])
            if choice=='revised_evidence_accepted':
                revisions=json.loads(a['payload'])['data'].get('evidence_revisions',[])
                if not revisions:raise ControlError('No revised supporting evidence to accept')
                revision_ids=sorted({r['current']['snapshot_id'] for r in revisions})
                if not set(revision_ids)<={e['snapshot_id'] for e in evidence}:raise ControlError('Cite all revised supporting documents')
                for sid in {revision[side]['snapshot_id'] for revision in revisions for side in ('earlier','current')}:
                    doc=db.execute('SELECT kind,source_key FROM snapshots WHERE scope=? AND id=?',(actor.scope,sid)).fetchone()
                    if db.execute('SELECT 1 FROM snapshots WHERE scope=? AND kind=? AND source_key=? AND actor=?',(actor.scope,doc['kind'],doc['source_key'],actor.id)).fetchone():raise ControlError('Evidence supplier cannot accept any version of their document',403)
                payload['revision_snapshot_ids']=revision_ids
            if code=='POSSIBLE_DUPLICATE':
                candidates=json.loads(a['payload'])['data'].get('duplicate_population',json.loads(a['payload'])['data'].get('duplicate_candidates',[]))
                payload['duplicate_candidate_set']=[{'source_key':e['source_key'],'hash':e['hash']} for e in sorted(candidates,key=lambda e:e['source_key'])]
            rid=db.execute("INSERT INTO dispositions(scope,workflow,period_id,item_key,code,choice,payload,evidence,source_hash,actor,reason,action,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,'apply',?)",(actor.scope,workflow,period_id,item_key,code,choice,canonical(payload),canonical(evidence),source['hash'],actor.id,reason,utcnow())).lastrowid
            self.package_changes(db,actor)
            self.store.audit(db,actor.scope,actor.id,'exception_dispositioned',{'id':rid,'item_key':item_key,'code':code,'scope':'single_item','reason':reason})
            return rid

    def revoke_disposition(self,actor,disposition_id,reason):
        self.authorize(actor,('reviewer',));text_field(reason,'reason')
        with self.store.transaction() as db:
            self.require_grant(db,actor,'disposition');r=db.execute('SELECT * FROM dispositions WHERE scope=? AND id=? AND action=\'apply\'',(actor.scope,disposition_id)).fetchone()
            if not r:raise ControlError('Disposition not found',404)
            if r['choice']=='select_supersession_target':raise ControlError('Record a new authorized target selection instead of revoking its historical application',409)
            if self.period(db,actor,r['period_id'])['status']=='locked':raise ControlError('PERIOD_LOCKED',409)
            if db.execute("SELECT 1 FROM dispositions WHERE scope=? AND prior_id=?",(actor.scope,disposition_id)).fetchone():raise ControlError('Already revoked',409)
            db.execute("INSERT INTO dispositions(scope,workflow,period_id,item_key,code,choice,payload,evidence,source_hash,actor,reason,action,prior_id,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,'revoke',?,?)",(actor.scope,r['workflow'],r['period_id'],r['item_key'],r['code'],r['choice'],r['payload'],r['evidence'],r['source_hash'],actor.id,reason,disposition_id,utcnow()))
            self.package_changes(db,actor)
            self.store.audit(db,actor.scope,actor.id,'disposition_revoked',{'id':disposition_id,'reason':reason})

    def record_exceptions(self,db,scope,workflow,period_id,item,artifact,blockers,dispositions):
        previous={r['code']:r['status'] for r in db.execute('SELECT * FROM exceptions WHERE scope=? AND workflow=? AND period_id=? AND item_key=?',(scope,workflow,period_id,item))}
        resolved={d['code'] for d in dispositions}
        for code in set(previous)|set(blockers)|resolved:
            status='dispositioned' if code in resolved else 'open' if code in blockers else 'superseded'
            db.execute('INSERT INTO exceptions VALUES(?,?,?,?,?,?,?) ON CONFLICT(scope,workflow,period_id,item_key,code) DO UPDATE SET status=excluded.status,artifact_id=excluded.artifact_id',(scope,workflow,period_id,item,code,status,artifact))
            if previous.get(code)!=status:db.execute('INSERT INTO exception_history(scope,workflow,period_id,item_key,code,status,artifact_id,created) VALUES(?,?,?,?,?,?,?,?)',(scope,workflow,period_id,item,code,status,artifact,utcnow()))
