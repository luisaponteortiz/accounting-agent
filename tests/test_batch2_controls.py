import copy
import json
from decimal import Decimal
from accounting_agent.core import Actor, ControlError, digest
from accounting_agent.demo import actor, grant_fixture_authority
from tests import test_platform as helpers

class Batch2Controls(helpers.PlatformCase):
    def src(self,key):return copy.deepcopy(next(s for s in self.packet['sources'] if s['key']==key))
    def controller(self,name='disposition-controller',permissions=None):
        r=Actor(name,'reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(self.os,r,permissions);return r
    def rerun(self,workflow='card_preparation'):
        self.os.enqueue(actor(),workflow);self.drain()
    def disposition(self,key,code,choice,payload=None):
        a=self.item(key);return self.os.disposition(self.controller(),'card_preparation','2026-11',key,code,choice,payload or {},a['payload']['data']['evidence']+a['payload']['data'].get('duplicate_evidence',[]),'Explicit fictional item treatment')

    def test_T13_statement_activity_identity_and_opening_controls(self):
        self.drain();c=self.src('demo-card-control');c['data']['closing_balance']='999.00';self.intake_one(c);self.rerun()
        self.assertIn('STATEMENT_ACTIVITY_BALANCE_BREAK',self.item('demo_card_001:TX-001')['blockers'])
        c=self.src('demo-card-control');c['data']['line_ids'][0]='DIFFERENT';self.intake_one(c,'identity');self.rerun()
        self.assertIn('STATEMENT_LINE_POPULATION_MISMATCH',self.item('demo_card_001:TX-001')['blockers'])
        prior=self.src('demo-card-control');prior['key']='oct-statement';prior['data'].update(period_start='2026-10-01',period_end='2026-10-31',closing_balance='900.00')
        self.os.open_period(actor('reviewer'),'2026-10','2026-10-01','2026-10-31','Fictional prior period');self.intake_one(prior,'prior');self.os.enqueue(actor(),'card_preparation',period_id='2026-11');self.drain()
        self.assertIn('STATEMENT_OPENING_BALANCE_BREAK',self.item('demo_card_001:TX-001')['blockers'])

    def test_T14_duplicate_disposition_revoke_and_independence(self):
        self.drain()
        for key in ('demo_card_001:TX-004','demo_card_001:TX-005'):
            self.disposition(key,'POSSIBLE_DUPLICATE','distinct_purchases')
        self.rerun();a=self.item('demo_card_001:TX-004');self.assertTrue(a['eligible']);self.assertTrue(a['payload']['data']['disposition_ids'])
        with self.assertRaises(ControlError):self.review(a,who=self.controller())
        self.review(a);did=a['payload']['data']['disposition_ids'][0]
        self.os.revoke_disposition(self.controller(),did,'Mistaken distinct-purchase decision');self.rerun()
        self.assertIn('POSSIBLE_DUPLICATE',self.item('demo_card_001:TX-004')['blockers'])
        with self.os.store.transaction() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM policy_rules').fetchone()[0],len(self.profile['vendors'])+2)

    def test_T14_split_exact_and_service_refusal(self):
        self.drain();key='demo_card_001:TX-010';a=self.item(key);amount=a['payload']['data']['transaction']['amount']
        with self.assertRaises(ControlError):self.disposition(key,'SPLIT_REQUIRES_REVIEW','allocate',{'allocations':[{'account_id':'DEMO_REPAIRS','amount':'0.01'}]})
        self.disposition(key,'SPLIT_REQUIRES_REVIEW','allocate',{'allocations':[{'account_id':'DEMO_REPAIRS','amount':amount}]});self.rerun();self.assertTrue(self.item(key)['eligible'])
        service=Actor('service','reviewer','demo_org','bird_bowl_demo',kind='service');grant_fixture_authority(self.os,service,['disposition'])
        with self.assertRaises(ControlError):self.os.disposition(service,'card_preparation','2026-11','demo_card_001:TX-004','POSSIBLE_DUPLICATE','distinct_purchases',{},a['payload']['data']['evidence'],'Services cannot decide')

    def test_T14_contributor_is_item_scoped(self):
        self.drain();helper=Actor('receipt-helper','preparer','demo_org','bird_bowl_demo',kind='human')
        from accounting_agent.demo import load
        self.os.intake(helper,load('fixtures/late_receipt.json'));self.rerun()
        helper_rev=Actor('receipt-helper','reviewer','demo_org','bird_bowl_demo',kind='human')
        self.review(self.item('demo_card_001:TX-001'),who=helper_rev)
        with self.assertRaises(ControlError):self.review(self.item('demo_card_001:TX-002'),who=helper_rev)

    def test_T15_shared_entry_impact_and_double_recording(self):
        self.drain();a=self.item('demo_card_001:TX-001');entry=a['payload']['data']['proposed_entry'];self.assertEqual(entry['external_posting'],'not_posted')
        self.assertEqual(sum((Decimal(l['debit'])-Decimal(l['credit']) for l in entry['lines']),Decimal('0.00')),0)
        j=self.src('J-001');j['data']['origin_sources']=[a['payload']['data']['evidence'][0]];self.intake_one(j,'entry-origin');self.rerun();self.rerun('journal_preparation')
        self.assertIn('SOURCE_ALREADY_HAS_ENTRY',self.item('demo_card_001:TX-001')['blockers']);self.assertIn('SOURCE_ALREADY_HAS_ENTRY',self.item('J-001','journal_preparation')['blockers'])

    def test_T18_finalization_stability_changes_and_recovery(self):
        self.drain();a=self.item('J-001','journal_preparation');self.review(a)
        # J-002 is deliberately unbalanced: explicit carry-forward, never clean approval.
        finalizer=self.controller('finalizer');pid=self.os.finalize_package(finalizer,'2026-11','journal_preparation','Fictional handover',acknowledgement='J-002 remains held; no external close claimed')
        before=next(p for p in self.os.export(actor())['packages'] if p['id']==pid)
        self.intake_one({'kind':'document','key':'unrelated','data':{'document_type':'unrelated','content':'Fictional unrelated record','period_id':'2026-11'}},'unrelated')
        after=next(p for p in self.os.export(actor())['packages'] if p['id']==pid);self.assertEqual(before,after);self.assertEqual(digest(json.loads(before['payload'])),before['hash'])
        self.assertTrue(any(e['code']=='POST_FINALIZATION_CHANGE' for e in self.os.export(actor())['accounting_events']))
        with self.assertRaises(ControlError):self.os.finalize_package(Actor(actor().id,'reviewer','demo_org','bird_bowl_demo',kind='human'),'2026-11','journal_preparation','Preparer cannot finalize','Carry-forward')
        # Mistaken revoke is recoverable by a distinct independent human, then bounded.
        self.rerun('journal_preparation');a=self.item('J-001','journal_preparation');self.review(a);self.review(a,'revoke')
        resolver=self.controller('resolver');self.review(a,'resolve_approve',resolver)
        with self.assertRaises(ControlError):self.review(a,'reject',self.controller('overruled'))

    def test_T18_lock_requires_ack_and_disputed_finalization_refused(self):
        self.drain()
        with self.assertRaises(ControlError):self.os.lock_period(actor('reviewer'),'2026-11','Unsettled work')
        a=self.item('J-001','journal_preparation');self.review(a);self.review(a,'reject',self.controller('second'))
        with self.assertRaises(ControlError):self.os.finalize_package(self.controller('finalizer'),'2026-11','journal_preparation','Cannot finalize disputed','Explicit carry-forward')

    def test_T19_period_and_typed_workflow_outcome(self):
        self.drain();value=[{'type':'workflow_outcome','workflow':'journal_preparation'},{'type':'document','document_type':'prior_only'}]
        r=self.os.propose_rule(actor(),'close_checklist','close',value,'2026-11-01');self.os.approve_rule(self.controller('policy',['approve_rule']),r,'Fictional typed checklist')
        self.intake_one({'kind':'document','key':'old','data':{'document_type':'prior_only','content':'Fictional prior period','period_id':'2026-10'}},'old');self.rerun('close_readiness')
        a=self.item('close-checklist','close_readiness');self.assertIn('OPEN_PREPARATION_EXCEPTIONS',a['blockers']);self.assertIn('MISSING_CLOSE_EVIDENCE',a['blockers'])
        self.assertTrue(a['payload']['data']['period_status']['items'])

    def test_T14_empty_inventory_propagates(self):
        from accounting_agent.service import AccountingOS
        from accounting_agent.demo import SCOPE,prepare_profile
        from pathlib import Path
        empty=AccountingOS(Path(self.temp.name)/'empty.sqlite3',[SCOPE]);prepare_profile(empty,actor(),self.profile)
        empty.open_period(actor('reviewer'),'2026-11','2026-11-01','2026-11-30','Fictional empty period')
        empty.enqueue(actor(),'journal_preparation');empty.drain(actor('worker'))
        outputs=empty.state(actor())['artifacts']
        self.assertTrue(all('NO_SOURCE_EVIDENCE' in a['blockers'] for a in outputs))

    def test_T14_rule_scope_proposes_without_resolving(self):
        self.drain();key='demo_card_001:TX-003';a=self.item(key)
        value={'id':'unknown-fictional','name':'Fictional unknown','aliases':['UNKNOWN MARKET DEMO'],'category':'DEMO_OFFICE_SUPPLIES'}
        rid=self.os.disposition(self.controller(),'card_preparation','2026-11',key,'UNKNOWN_VENDOR','confirm_vendor',{'rule':{'kind':'vendor_mapping','key':value['id'],'value':value,'effective_from':'2026-11-01'}},a['payload']['data']['evidence'],'Propose reusable mapping only',scope_kind='propose_rule')
        self.rerun();self.assertIn('UNKNOWN_VENDOR',self.item(key)['blockers'])
        self.assertFalse(any(d['item_key']==key for d in self.os.state(actor())['dispositions']))
        self.assertFalse(any(d['rule_id']==rid for d in self.os.export(actor())['rule_decisions']))


    def test_T17_approved_amount_tolerance_is_bounded(self):
        self.drain();value={'date_window_days':None,'amount_tolerance':'0.05','multiple_receipts':False,'vendor_method':'exact_alias','statement_substitution':False}
        rid=self.os.propose_rule(actor(),'receipt_matching','matching',value,'2026-11-01');self.os.approve_rule(self.controller('tolerance-controller',['approve_rule']),rid,'Explicit fictional five-cent tolerance')
        r=self.src('receipt-TX-001');r['data']['amount']='42.55';self.intake_one(r,'five-cents');self.rerun();self.accept_revised_evidence('demo_card_001:TX-001');self.assertTrue(self.item('demo_card_001:TX-001')['eligible'])
        r['data']['amount']='42.56';self.intake_one(r,'six-cents');self.rerun();self.assertIn('RECEIPT_AMOUNT_MISMATCH',self.item('demo_card_001:TX-001')['blockers'])


    def test_T15_transfer_direction_respects_signed_card_activity(self):
        self.drain();t=self.src('demo_card_001:TX-012');t['data'].update(activity='transfer',amount='300.00')
        r=self.src('receipt-TX-012');r['data']['amount']='300.00'
        c=self.src('demo-card-control');c['data']['totals'].update(payment='0.00',transfer='300.00');c['data']['closing_balance']=str(Decimal(c['data']['closing_balance'])+Decimal('600.00'))
        p=copy.deepcopy(self.packet);p.update(batch_id='positive-transfer',sources=[t,r,c]);self.os.intake(actor(),p);self.rerun()
        self.disposition(t['key'],'NON_EXPENSE_REQUIRES_REVIEW','transfer',{'cash_account':'DEMO_CASH'});self.rerun();self.accept_revised_evidence(t['key'])
        a=self.item(t['key']);self.assertTrue(a['eligible'])
        lines={l['account_id']:l for l in a['payload']['data']['proposed_entry']['lines']}
        self.assertEqual(lines['DEMO_CASH']['debit'],'300.00');self.assertEqual(lines['DEMO_CARD_LIABILITY']['credit'],'300.00')


    def test_T19_waits_for_inflight_preparation_before_readiness(self):
        from accounting_agent.modules import CAPABILITIES
        first=self.os.claim(actor('worker'));second=self.os.claim(actor('worker'))
        self.assertEqual(first['capability'],'evidence.inventory');self.assertEqual(second['capability'],'evidence.inventory')
        self.assertIsNone(self.os.claim(actor('worker')))
        self.os.commit(actor('worker'),second,CAPABILITIES[second['capability']].handler(second['context']))
        self.os.commit(actor('worker'),first,CAPABILITIES[first['capability']].handler(first['context']))
        self.drain();self.assertTrue(self.item('close-checklist','close_readiness')['current'])
        self.assertEqual(len(self.os.state(actor())['artifacts']),21)


    def test_T19_document_label_cannot_complete_deferred_reconciliation(self):
        self.drain();requirement={'type':'reconciliation','document_type':'bank_reconciliation','account_id':'demo_card_001'}
        rid=self.os.propose_rule(actor(),'close_checklist','close',[requirement],'2026-11-01');self.os.approve_rule(self.controller('close-policy-controller',['approve_rule']),rid,'Fictional required reconciliation')
        self.intake_one({'kind':'document','key':'not-a-reconciliation','data':{'document_type':'bank_reconciliation','period_id':'2026-11','account_id':'demo_card_001','content':'Fictional document label alone proves no reconciliation'}},'label-only');self.rerun('close_readiness')
        a=self.item('close-checklist','close_readiness');self.assertIn('MISSING_CLOSE_EVIDENCE',a['blockers']);self.assertFalse(a['payload']['data']['requirements'][0]['satisfied'])


for _name in list(helpers.PlatformCase.__dict__):
    if _name.startswith('test_'):setattr(Batch2Controls,_name,None)
