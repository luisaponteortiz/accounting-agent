"""Regressions for Fable RA-01..RA-08, using disposable fictional records."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from accounting_agent.core import ControlError

ROOT=Path(__file__).resolve().parents[1]


class AcceptanceCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py'
        spec=importlib.util.spec_from_file_location('fable_ra_fixtures',path)
        cls.f=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(cls.f)

    @classmethod
    def tearDownClass(cls):cls.f.TMP.cleanup()

    def test_RA01_entire_chain_and_receipts_remain_blocked_until_reopen(self):
        f=self.f;o=f.new_os(periods=(f.NOV,f.DEC));f.clean_november(o);f.run(o,'card_preparation')
        for key in ('A1','A2'):self.assertEqual(f.review(o,f.REV,f.gov(o,f.CARD+':'+key),'approve')[0],'ok')
        o.lock_period(f.PADMIN,'2026-11','Fictional chain regression')
        predecessor='A1';chain=('A1X','A1Y','A1Z');last=[]
        for index,key in enumerate(chain,2):
            row=f.tx(key,'2026-12-%02d'%index,'40.00');row['supersedes']=f.CARD+':'+predecessor
            last=[row,f.rc(key,'2026-12-%02d'%index,'40.00')]
            o.intake(f.PREP2,f.packet('chain-'+key,last));predecessor=key
        o.intake(f.PREP2,f.packet('chain-statement',[f.stmt(last,f.DEC,opening='100.00')]))
        f.run(o,'card_preparation','2026-12',f.PREP2)
        expected={s for key in chain for s in (f.CARD+':'+key,'receipt-'+key)}
        state=o.export(f.PREP)
        self.assertEqual({e['source_key'] for e in state['source_exceptions'] if e['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD'},expected)
        history={s['id']:s for s in state['evidence_history']}
        self.assertEqual({history[m['snapshot_id']]['source_key'] for m in state['source_move_history'] if m['blocked']},expected)
        self.assertTrue(all(m['had_approval'] for m in state['source_move_history'] if history[m['snapshot_id']]['source_key'] in {f.CARD+':'+key for key in chain}))
        for key in chain:self.assertIsNone(f.gov(o,f.CARD+':'+key,'2026-12'))
        self.assertEqual(f.gov(o,f.CARD+':A1','2026-11')['review_status'],'approve')
        o.reopen_period(f.PADMIN,'2026-11','Release fictional chain')
        f.run(o,'card_preparation','2026-11');f.run(o,'card_preparation','2026-12',f.PREP2)
        self.assertIsNone(f.gov(o,f.CARD+':A1','2026-11'))
        for key in chain[:-1]:self.assertIsNone(f.gov(o,f.CARD+':'+key,'2026-12'))
        terminal=f.gov(o,f.CARD+':A1Z','2026-12')
        self.assertIsNotNone(terminal);self.assertIn('SOURCE_TRANSITION_REQUIRES_REVIEW',terminal['blockers'])
        self.assertNotIn('MISSING_RECEIPT',terminal['blockers'])
        state=o.export(f.PREP)
        intermediate={f.CARD+':'+key for key in chain[:-1]}
        self.assertFalse(any(b['admitted'] and b['period_id']=='2026-12' and history[b['snapshot_id']]['source_key'] in intermediate for b in state['source_period_history']))
        self.assertTrue(o.verify_audit(f.PREP))

    def test_RA01_supersession_cycle_is_refused_without_mutation(self):
        f=self.f;o=f.new_os();f.clean_november(o)
        row=f.tx('A1X','2026-11-03','40.00');row['supersedes']=f.CARD+':A1'
        o.intake(f.PREP,f.packet('first-link',[row,f.rc('A1X','2026-11-03','40.00')]))
        before=o.state(f.PREP)
        cycle=f.tx('A1','2026-11-03','40.00');cycle['supersedes']=f.CARD+':A1X'
        with self.assertRaisesRegex(ControlError,'cycle'):o.intake(f.PREP,f.packet('cycle',[cycle]))
        self.assertEqual(o.state(f.PREP),before)

    def test_RA03_replacement_key_discloses_old_receipt_and_keeps_both_suppliers_independent(self):
        f=self.f;o=f.new_os();old_supplier=f.human(f.REV3.id,'preparer')
        rows=[f.tx('A1','2026-11-03','40.00'),f.tx('A2','2026-11-04','60.00'),f.rc('A2','2026-11-04','60.00')]
        o.intake(f.PREP,f.packet('base',rows+[f.stmt(rows)]))
        original=f.rc('A1','2026-11-03','39.99')
        o.intake(old_supplier,f.packet('old-receipt',[original]));f.run(o,'card_preparation')
        self.assertIn('RECEIPT_AMOUNT_POLICY_UNSET',f.gov(o,f.CARD+':A1')['blockers'])
        withdrawn=dict(copy.deepcopy(original),tombstone=True,removal_reason='voided')
        o.intake(f.PREP2,f.packet('replacement',[withdrawn,f.rc('A1','2026-11-03','40.00',key='replacement-A1',content='Corrected fictional support')]))
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');revisions=a['payload']['data']['evidence_revisions']
        self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',a['blockers'])
        self.assertTrue(any(r['kind']=='replaced' and r['earlier']['source_key']=='receipt-A1' and r['earlier']['version']==1 and 'amount' in r['changed_fields'] for r in revisions))
        for supplier in (old_supplier,f.PREP2):
            o.grant_authority(f.ADMIN,supplier.id,['disposition'],'Isolate supplier control')
            denied=f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=f.human(supplier.id,'reviewer'))
            self.assertEqual(denied[:2],('refused',403))
        self.assertEqual(f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')[0],'ok')
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible'])
        self.assertIn(old_supplier.id,a['contributors'])
        self.assertEqual(f.review(o,f.REV3,a,'approve')[:2],('refused',403))
        self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')

        self.assertTrue(f.gov(o,f.CARD+':A2')['eligible']);self.assertTrue(o.verify_audit(f.PREP))

    def test_RA06_transition_disposition_with_predecessor_evidence_takes_effect(self):
        f=self.f;o=f.new_os(periods=(f.NOV,f.DEC));f.clean_november(o);f.run(o,'card_preparation')
        for key in ('A1','A2'):self.assertEqual(f.review(o,f.REV,f.gov(o,f.CARD+':'+key),'approve')[0],'ok')
        o.lock_period(f.PADMIN,'2026-11','Fictional origin lock')
        first=f.tx('A1X','2026-12-02','40.00');first['supersedes']=f.CARD+':A1'
        o.intake(f.PREP2,f.packet('transition-first',[first,f.rc('A1X','2026-12-02','40.00')]))
        last=f.tx('A1Y','2026-12-03','40.00');last['supersedes']=f.CARD+':A1X';rows=[last,f.rc('A1Y','2026-12-03','40.00')]
        o.intake(f.PREP2,f.packet('transition-last',rows+[f.stmt(rows,f.DEC,opening='100.00')]))
        o.reopen_period(f.PADMIN,'2026-11','Release origin for transition review')
        f.run(o,'card_preparation','2026-11');f.run(o,'card_preparation','2026-12',f.PREP2)
        a=f.gov(o,f.CARD+':A1Y','2026-12');self.assertTrue(any('link_id' in e for e in a['payload']['data']['evidence']))
        decision=f.dispose(o,f.CARD+':A1Y','SOURCE_TRANSITION_REQUIRES_REVIEW','settlement_verified',period='2026-12')
        self.assertEqual(decision[0],'ok');f.run(o,'card_preparation','2026-12',f.PREP2)
        a=f.gov(o,f.CARD+':A1Y','2026-12');self.assertNotIn('SOURCE_TRANSITION_REQUIRES_REVIEW',a['blockers']);self.assertTrue(a['eligible'])
        self.assertIn(decision[1],a['payload']['data']['disposition_ids'])
        self.assertEqual(f.review(o,f.REV2,a,'approve')[0],'ok')
        o.lock_period(f.PADMIN,'2026-11','Reclose origin after its charge moved','Fictional source departure and remaining statement exceptions acknowledged')
        revision=f.tx('A1Y','2026-12-03','40.00',desc='Acme  Paper  Demo')
        o.intake(f.PREP2,f.packet('destination-revision-after-relock',[revision]))
        f.run(o,'card_preparation','2026-12',f.PREP2)
        self.assertIsNotNone(f.gov(o,f.CARD+':A1Y','2026-12'))
        self.assertFalse(any(e['source_key']==f.CARD+':A1Y' and e['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD' for e in o.state(f.PREP)['source_exceptions']))

    def test_RA05_preapproved_midperiod_rules_do_not_suspend_on_fresh_evidence(self):
        f=self.f;o=f.new_os(periods=(f.NOV,f.DEC));rows=f.clean_november(o)
        value={'id':'extra','name':'Fictional extra','aliases':['EXTRA DEMO'],'category':'DEMO_REPAIRS'}
        rid=o.propose_rule(f.PREP2,'vendor_mapping','extra',value,'2026-11-15');o.approve_rule(f.CTRL,rid,'Approved before authority')
        mid=o.create_mandate(f.PREP,['card_preparation'],'2026-12-01T00:00:00+00:00','2026-12-05T00:00:00+00:00',86400,3,{'kind':'fixed','period_id':'2026-11'},{'transaction':'occurrence_start'})
        o.approve_mandate(f.CTRL,mid,'Standing fictional evidence requirement')
        before=next(m for m in o.state(f.PREP)['mandates'] if m['id']==mid)['bound_rules']
        o.tick(f.PREP,'2026-12-01T12:00:00+00:00')
        fresh=[f.tx('A9','2026-11-25','12.00',as_of='2026-12-01T13:00:00+00:00'),f.rc('A9','2026-11-25','12.00')]
        o.intake(f.PREP,f.packet('fresh-midperiod',fresh+[f.stmt(rows+fresh)]));o.drain(f.WORKER)
        state=o.state(f.PREP);mandate=next(m for m in state['mandates'] if m['id']==mid)
        self.assertTrue(mandate['active']);self.assertEqual(mandate['status'],'active');self.assertEqual(mandate['bound_rules'],before)
        self.assertEqual(len([r for r in state['runs'] if r['mandate_id']==mid]),1)
        after=o.propose_rule(f.PREP2,'vendor_mapping','later',dict(value,id='later',aliases=['LATER DEMO']),'2026-11-20');o.approve_rule(f.CTRL,after,'Actual later policy change')
        o.tick(f.PREP,'2026-12-02T12:00:00+00:00')
        mandate=next(m for m in o.state(f.PREP)['mandates'] if m['id']==mid)
        self.assertFalse(mandate['active']);self.assertEqual(mandate['status'],'needs_reconfirmation')

    def test_RA05_future_retirement_does_not_change_prior_period_authority(self):
        f=self.f;o=f.new_os(periods=(f.NOV,f.DEC));f.clean_november(o)
        mid=o.create_mandate(f.PREP,['card_preparation'],'2026-11-15T00:00:00+00:00','2026-11-18T00:00:00+00:00',86400,2,{'kind':'fixed','period_id':'2026-11'},f.NO_EVIDENCE)
        o.approve_mandate(f.CTRL,mid,'Fictional November authority')
        profile=copy.deepcopy(f.PROFILE);profile['version']='future-retirement';profile['vendors']=[v for v in profile['vendors'] if v['id']!='demo_metro']
        pid=o.onboard(f.PREP2,profile,effective_from='2026-12-01');o.approve_profile_version(f.CTRL,pid,'December retirement only')
        o.tick(f.PREP,'2026-11-15T12:00:00+00:00')
        state=o.state(f.PREP);self.assertTrue(next(m for m in state['mandates'] if m['id']==mid)['active'])
        self.assertEqual(len([r for r in state['runs'] if r['mandate_id']==mid]),1)

    def test_RA03_additional_receipt_is_multiple_support_until_the_original_is_withdrawn(self):
        f=self.f;o=f.new_os();f.clean_november(o);f.run(o,'card_preparation')
        o.intake(f.PREP2,f.packet('second',[f.rc('A1','2026-11-03','40.00',key='second-A1',content='Separate fictional receipt')]))
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1')
        self.assertEqual(a['payload']['data']['evidence_revisions'],[])
        self.assertIn('RECEIPT_MULTIPLE_POLICY_UNSET',a['blockers'])
        old=f.rc('A1','2026-11-03','40.00');old.update(tombstone=True,removal_reason='voided')
        o.intake(f.PREP,f.packet('withdraw-after-arrival',[old]));f.run(o,'card_preparation')
        a=f.gov(o,f.CARD+':A1');self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',a['blockers'])
        self.assertTrue(any(r['kind']=='replaced' for r in a['payload']['data']['evidence_revisions']))

    def test_RA04_statement_revision_holds_each_item_and_requires_non_supplier_acceptance(self):
        f=self.f;o=f.new_os();rows=f.clean_november(o,statement=False)
        supplier=f.human(f.REV3.id,'preparer')
        wrong=f.stmt(rows,totals={'purchase':'90.00','credit':'0.00','payment':'0.00','fee':'0.00','interest':'0.00','transfer':'0.00','unknown':'0.00'},closing_balance='90.00')
        o.intake(supplier,f.packet('wrong-statement',[wrong]));f.run(o,'card_preparation')
        self.assertIn('STATEMENT_CONTROL_MISMATCH',f.gov(o,f.CARD+':A1')['blockers'])
        o.intake(f.PREP2,f.packet('corrected-statement',[f.stmt(rows)]));f.run(o,'card_preparation')
        for key in ('A1','A2'):self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',f.gov(o,f.CARD+':'+key)['blockers'])
        workpaper=f.gov(o,'statement:'+f.CARD,kinds=None)['payload']['data']
        self.assertTrue(any(r['earlier']['version']==1 and r['earlier']['supplier']==supplier.id and 'totals' in r['changed_fields'] for r in workpaper['statement_revisions']))
        for author in (supplier,f.PREP2):
            o.grant_authority(f.ADMIN,author.id,['disposition'],'Isolate statement supplier control')
            denied=f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=f.human(author.id,'reviewer'))
            self.assertEqual(denied[:2],('refused',403))
        self.assertEqual(f.dispose(o,f.CARD+':A1','EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted')[0],'ok')
        f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible'])
        self.assertFalse(f.gov(o,f.CARD+':A2')['eligible'])
        o.grant_authority(f.ADMIN,f.DISP.id,['review'],'Isolate separate final review')
        self.assertEqual(f.review(o,f.DISP,a,'approve')[:2],('refused',403))
        self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')
        o.intake(f.PREP,f.packet('statement-third-version',[f.stmt(rows,opening='10.00')]))
        f.run(o,'card_preparation');self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',f.gov(o,f.CARD+':A1')['blockers'])
        self.assertTrue(o.verify_audit(f.PREP))

    def test_RA04_statement_replacement_key_preserves_revision_control(self):
        f=self.f;o=f.new_os();rows=f.clean_november(o);f.run(o,'card_preparation')
        old=f.stmt(rows);old.update(tombstone=True,removal_reason='voided')
        replacement=f.stmt(rows,opening='10.00',key='replacement-statement')
        o.intake(f.PREP2,f.packet('new-statement-key',[old,replacement]));f.run(o,'card_preparation')
        a=f.gov(o,f.CARD+':A1');self.assertIn('EVIDENCE_REVISED_REQUIRES_REVIEW',a['blockers'])
        self.assertTrue(any(r['kind']=='replaced' and r['earlier']['source_key']=='stmt-2026-11' and 'opening_balance' in r['changed_fields'] for r in a['payload']['data']['evidence_revisions']))

    def test_RA02_unlinked_rule_identity_preserves_semantic_authors_without_unrelated_scope(self):
        f=self.f;base={'id':'demo_acme','name':'Acme Paper Demo','aliases':['ACME PAPER DEMO'],'category':'DEMO_OFFICE_SUPPLIES'}
        for scope,alias,category,barred in ((None,'ACME PAPER DEMO','DEMO_OFFICE_SUPPLIES',True),(f.CARD+':A2','ACME PAPER DEMO','DEMO_OFFICE_SUPPLIES',False),(None,'DIFFERENT VENDOR','DEMO_OFFICE_SUPPLIES',False),(None,'ACME PAPER DEMO','DEMO_REPAIRS',False)):
            with self.subTest(scope=scope,alias=alias,category=category):
                profile=copy.deepcopy(f.PROFILE);profile['vendors']=[v for v in profile['vendors'] if v['id']!='demo_acme']
                o=f.new_os(profile=profile);old=dict(base,aliases=[alias],category=category)
                first=o.propose_rule(f.human(f.REV3.id,'preparer'),'vendor_mapping','demo_acme',old,'2026-11-01',item_key=scope)
                o.approve_rule(f.CTRL,first,'Earlier fictional mapping')
                second=o.propose_rule(f.PREP2,'vendor_mapping','demo_acme',dict(base,name='Acme Paper Demo.'),'2026-11-01')
                o.approve_rule(f.CTRL2,second,'Unlinked current mapping')
                f.clean_november(o);f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible'])
                decision=f.review(o,f.REV3,a,'approve')
                self.assertEqual(decision[:2],('refused',403) if barred else ('ok',None))

    def test_RA02_unlinked_identical_receipt_policy_retains_author(self):
        f=self.f;o=f.new_os();value={'date_window_days':1,'amount_tolerance':None,'multiple_receipts':None,'vendor_method':None,'statement_substitution':None}
        first=o.propose_rule(f.human(f.REV4.id,'preparer'),'receipt_matching','default',value,'2026-11-01');o.approve_rule(f.CTRL,first,'Original policy')
        second=o.propose_rule(f.PREP2,'receipt_matching','default',value,'2026-11-01');o.approve_rule(f.CTRL2,second,'Unlinked identical policy')
        f.clean_november(o);f.run(o,'card_preparation');a=f.gov(o,f.CARD+':A1');self.assertTrue(a['eligible'])
        self.assertEqual(f.review(o,f.REV4,a,'approve')[:2],('refused',403))
        self.assertEqual(f.review(o,f.REV,a,'approve')[0],'ok')

    def test_RA07_unrelated_rows_and_receipts_cannot_support_vendor_coding(self):
        f=self.f;o=f.new_os();f.clean_november(o,extra=[f.tx('U1','2026-11-07','5.00',desc='UNKNOWN DEMO'),f.rc('U1','2026-11-07','5.00',vendor='UNKNOWN DEMO')]);f.run(o,'card_preparation')
        item=f.gov(o,f.CARD+':U1');own=[e for e in item['payload']['data']['evidence'] if e['source_key']==f.CARD+':U1']
        other=f.gov(o,f.CARD+':A1')['payload']['data']['evidence']
        for key in (f.CARD+':A1','receipt-A1'):
            denied=f.dispose(o,f.CARD+':U1','UNKNOWN_VENDOR','confirm_vendor',{'account_id':'DEMO_OFFICE_SUPPLIES'},evidence=own+[e for e in other if e['source_key']==key])
            self.assertEqual(denied[0],'refused');self.assertIn('Related',denied[2])
        receipt=[e for e in item['payload']['data']['evidence'] if e['source_key']=='receipt-U1']
        for code,choice in (('UNKNOWN_VENDOR','confirm_vendor'),('UNKNOWN_CATEGORY','code_category')):
            self.assertEqual(f.dispose(o,f.CARD+':U1',code,choice,{'account_id':'DEMO_OFFICE_SUPPLIES'},evidence=own+receipt)[0],'ok')
        f.run(o,'card_preparation');self.assertTrue(f.gov(o,f.CARD+':U1')['eligible'])

    def test_RA08_circular_duplicate_and_replay_exclusions_are_refused_before_reprepare(self):
        f=self.f
        for choice in ('duplicate_of','source_replay'):
            with self.subTest(choice=choice):
                o,_=f.duplicate_pair()
                first=f.dispose(o,f.CARD+':D2','POSSIBLE_DUPLICATE',choice,{'duplicate_of':f.CARD+':D1'})
                self.assertEqual(first[0],'ok')
                second=f.dispose(o,f.CARD+':D1','POSSIBLE_DUPLICATE',choice,{'duplicate_of':f.CARD+':D2'})
                self.assertEqual(second[0],'refused');self.assertIn('already excluded',second[2])
                f.run(o,'card_preparation');survivor=f.gov(o,f.CARD+':D1');excluded=f.gov(o,f.CARD+':D2')
                self.assertTrue(survivor['eligible']);self.assertIsNotNone(survivor['payload']['data']['proposed_entry'])
                self.assertIn('DUPLICATE_EXCLUDED',excluded['blockers']);self.assertIsNone(excluded['payload']['data']['proposed_entry'])
                o.revoke_disposition(f.DISP,first[1],'Restore both candidates');f.run(o,'card_preparation')
                for key in ('D1','D2'):self.assertIn('POSSIBLE_DUPLICATE',f.gov(o,f.CARD+':'+key)['blockers'])
