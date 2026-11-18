from accounting_agent.demo import prepare_profile, grant_fixture_authority, create_fixture_mandate
"""Required outcomes from probes P01-P16, independent of diagnostic printouts."""
import copy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from accounting_agent.core import Actor, ControlError
from accounting_agent.demo import SCOPE, actor, load
from tests import test_platform as helpers


class ReviewerProbes(helpers.PlatformCase):
    # Inherit helpers, not the original test methods (removed below).
    def journal(self):
        self.drain()
        return self.item('J-001', 'journal_preparation')

    def source(self, key):
        return copy.deepcopy(next(s for s in self.packet['sources'] if s['key']==key))

    def test_P01_contributor_cannot_review_colleague_run(self):
        a=self.journal()
        contributor=Actor(actor().id,'reviewer','demo_org','bird_bowl_demo', kind="human")
        # A fresh colleague's recurring run removes enqueuer equality as a shortcut.
        colleague=Actor('human-colleague','preparer','demo_org','bird_bowl_demo', kind="human")
        create_fixture_mandate(self.os,colleague,['journal_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        self.os.tick(colleague,'2026-11-15T12:00:00+00:00');self.drain(now='2026-11-15T12:00:01+00:00')
        a=self.item('J-001','journal_preparation')
        with self.assertRaises(ControlError) as caught:self.review(a,who=contributor)
        self.assertEqual(caught.exception.status,403)

    def test_P02_identity_kind_not_name_controls_review(self):
        a=self.journal()
        service=Actor('automation-agent-7','reviewer','demo_org','bird_bowl_demo',kind='service')
        with self.assertRaises(ControlError):self.review(a,who=service)
        human=Actor('worker-of-the-month-jane','reviewer','demo_org','bird_bowl_demo',kind='human')
        self.review(a,who=human)

    def test_mandate_issuer_is_recorded_contributor(self):
        self.drain()
        issuer=Actor('mandate-owner','preparer','demo_org','bird_bowl_demo', kind="human")
        create_fixture_mandate(self.os,issuer,['journal_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        self.os.tick(actor(),'2026-11-15T12:00:00+00:00');self.drain(now='2026-11-15T12:00:01+00:00')
        a=self.item('J-001','journal_preparation')
        self.assertIn('mandate-owner',a['contributors'])
        with self.assertRaises(ControlError):self.review(a,who=Actor('mandate-owner','reviewer','demo_org','bird_bowl_demo', kind="human"))

    def test_expired_partial_slot_is_recorded_as_skipped(self):
        create_fixture_mandate(self.os,actor(),['journal_preparation'],'2026-11-15T00:00:00+00:00','2026-11-16T12:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        self.os.tick(actor(),'2026-11-17T00:00:00+00:00')
        self.assertEqual([o['occurrence_key'] for o in self.os.state(actor())['occurrences']],['2026-11-15T00:00:00+00:00','2026-11-16T00:00:00+00:00'])
        self.assertTrue(all(o['status']=='skipped_no_catch_up' for o in self.os.state(actor())['occurrences']))

    def test_concurrent_ticks_and_skipped_occurrences(self):
        from concurrent.futures import ThreadPoolExecutor
        self.drain();self.mandate(3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda _:self.os.tick(actor(),'2026-11-17T12:00:00+00:00'),range(2)))
        self.assertEqual(result[0],result[1]);self.drain(now='2026-11-17T12:01:00+00:00')
        occ=self.os.state(actor())['occurrences']
        self.assertEqual([o['status'] for o in occ],['skipped_no_catch_up','skipped_no_catch_up','completed'])
        self.assertEqual(len([r for r in self.os.state(actor())['runs'] if r['occurrence_id']==occ[-1]['id']]),1)

    def test_P03_stale_occurrence_redispatched(self):
        self.drain();self.mandate()
        first=self.os.tick(actor(),'2026-11-15T12:00:00+00:00')
        j=self.source('J-001');j['data']['memo']='Revised fictional support context'
        self.intake_one(j,'late-journal');self.drain(now='2026-11-15T12:05:00+00:00')
        second=self.os.tick(actor(),'2026-11-15T13:00:00+00:00');self.drain(now='2026-11-15T13:05:00+00:00')
        self.assertNotEqual(first,second)
        state=self.os.state(actor())
        self.assertTrue(any(a['current'] and a['item_key']=='J-001' for a in state['artifacts']))
        self.assertEqual(len(state['occurrences']),1)

    def test_P04_unfit_mandate_does_not_stop_others(self):
        self.mandate();create_fixture_mandate(self.os,actor(),['card_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        p=copy.deepcopy(self.profile);p['version']='no-journal';p['procedures']=['card_preparation','close_readiness'];prepare_profile(self.os,actor(),p)
        ids=self.os.tick(actor(),'2026-11-15T12:00:00+00:00')
        self.assertEqual(len(ids),1)
        state=self.os.state(actor());self.assertTrue(any(o['status']=='held' for o in state['occurrences']))

    def test_P05_one_governing_artifact_across_occurrences(self):
        self.journal();self.mandate()
        for now in ('2026-11-15T12:00:00+00:00','2026-11-16T12:00:00+00:00'):
            self.os.tick(actor(),now);self.drain(now=now)
        rows=[a for a in self.os.state(actor())['artifacts'] if a['current'] and a['item_key']=='J-001']
        self.assertEqual(len(rows),1)

    def test_P06_unicode_vendor_never_collapses_to_another(self):
        p=copy.deepcopy(self.profile);p['version']='unicode';p['vendors'].append({'id':'tokyo','name':'Fictional Tokyo','aliases':['東京文具'],'category':'DEMO_OFFICE_SUPPLIES'});prepare_profile(self.os,actor(),p)
        t=self.source('demo_card_001:TX-001');t['data']['description']='大阪修理';r=self.source('receipt-TX-001');r['data']['vendor']='大阪修理'
        self.intake_one(t,'unicode-t');self.intake_one(r,'unicode-r');self.os.enqueue(actor(),'card_preparation');self.drain()
        a=self.item('demo_card_001:TX-001');self.assertEqual(a['blockers'],['EVIDENCE_REVISED_REQUIRES_REVIEW','UNKNOWN_CATEGORY','UNKNOWN_VENDOR']);self.assertFalse(a['eligible'])

    def test_unicode_alias_validation_and_accents(self):
        from accounting_agent.core import normalize
        self.assertEqual(normalize('ＰＡＰＥＲ   café'), 'paper café')
        self.assertNotEqual(normalize('café'), normalize('cafe'))
        p=copy.deepcopy(self.profile);p['version']='bad-alias';p['vendors'][0]['aliases']=['---']
        with self.assertRaises(ControlError):prepare_profile(self.os,actor(),p)
        p['version']='accent';p['vendors'][0]['aliases']=['Café']
        prepare_profile(self.os,actor(),p)
        t=self.source('demo_card_001:TX-001');t['data']['description']='Cafe';r=self.source('receipt-TX-001');r['data']['vendor']='Cafe'
        self.intake_one(t,'accent-t');self.intake_one(r,'accent-r');self.os.enqueue(actor(),'card_preparation');self.drain()
        self.assertEqual(self.item('demo_card_001:TX-001')['blockers'],['EVIDENCE_REVISED_REQUIRES_REVIEW','UNKNOWN_CATEGORY','UNKNOWN_VENDOR'])

    def test_P07_stale_source_revision_cannot_replace_newer(self):
        t=self.source('demo_card_001:TX-001');t['data']['amount']='45.00';t['as_of']=2;self.intake_one(t,'seq2');old=self.source('demo_card_001:TX-001');old['as_of']=1;self.intake_one(old,'seq1-late')
        t=next(s for s in self.os.state(actor())['sources'] if s['source_key']=='demo_card_001:TX-001')
        self.assertEqual(t['value']['amount'],'45.00')

    def test_P08_unbound_journal_support(self):
        j=self.source('J-001');j['data']['supporting_keys']=['trial-balance-placeholder'];self.intake_one(j)
        self.os.enqueue(actor(),'journal_preparation');self.drain()
        self.assertIn('JOURNAL_SUPPORT_NOT_BOUND',self.item('J-001','journal_preparation')['blockers'])

    def test_P08_duplicate_journals(self):
        j=self.source('J-001');j['key']='J-DUP';self.intake_one(j)
        self.os.enqueue(actor(),'journal_preparation');self.drain()
        for key in ('J-001','J-DUP'):self.assertIn('POSSIBLE_DUPLICATE_JOURNAL',self.item(key,'journal_preparation')['blockers'])

    def test_P08_no_effect_journal(self):
        j=self.source('J-001');j['data']['lines'][1]['account_id']=j['data']['lines'][0]['account_id'];self.intake_one(j)
        self.os.enqueue(actor(),'journal_preparation');self.drain()
        self.assertIn('NO_NET_LEDGER_EFFECT',self.item('J-001','journal_preparation')['blockers'])

    def test_P09_lock_preserves_review_and_blocks_new_dispatch(self):
        a=self.journal();self.review(a)
        self.os.lock_period(actor('reviewer'),'2026-11','Synthetic period lock',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        a=next(x for x in self.os.state(actor())['artifacts'] if x['id']==a['id']);self.assertEqual(a['review_status'],'approve')
        with self.assertRaises(ControlError):self.os.enqueue(actor(),'journal_preparation',period_id='2026-11')

    def test_P10_second_period_does_not_strand_first(self):
        a=self.journal();self.review(a)
        self.os.open_period(actor('reviewer'),'2026-12','2026-12-01','2026-12-31','Fictional December')
        self.os.enqueue(actor(),'journal_preparation',period_id='2026-12');self.drain()
        a=next(x for x in self.os.state(actor())['artifacts'] if x['id']==a['id']);self.assertEqual(a['review_status'],'approve')

    def test_P11_transport_change_does_not_invalidate_accounting(self):
        a=self.journal();self.review(a)
        old=Path.read_text
        def changed(path,*args,**kw):
            content=old(path,*args,**kw)
            return content+'\n# hypothetical transport change\n' if path.name=='http.py' else content
        with patch.object(Path,'read_text',changed):
            from accounting_agent.service import AccountingOS
            fresh=AccountingOS(self.path,[SCOPE])
        a=next(x for x in fresh.state(actor())['artifacts'] if x['id']==a['id']);self.assertEqual(a['review_status'],'approve')

    def test_P12_close_considers_open_preparation_exceptions(self):
        for kind in ('card_statement','bank_reconciliation','ap_tieout','ar_tieout'):
            self.intake_one({'kind':'document','key':'close-'+kind,'data':{'document_type':kind,'content':'Fictional placeholder'}},'close-'+kind)
        self.os.enqueue(actor(),'close_readiness');self.drain()
        self.assertIn('OPEN_PREPARATION_EXCEPTIONS',self.item('close-checklist','close_readiness')['blockers'])

    def test_P13_statement_population_swap_detected(self):
        t=self.source('demo_card_001:TX-003');t['data']['status']='pending';self.intake_one(t)
        t=self.source('demo_card_001:TX-001');t['key']='demo_card_001:NEW';t['data'].update(source_id='NEW',date='2026-11-20',amount='65.00');self.intake_one(t,'new')
        self.os.enqueue(actor(),'card_preparation');self.drain()
        self.assertFalse(self.item('demo_card_001:TX-001')['eligible'])

    def test_reused_artifact_keeps_review_and_dispute_requires_third_reviewer(self):
        a=self.journal();self.review(a);self.mandate()
        ids=self.os.tick(actor(),'2026-11-15T12:00:00+00:00');self.drain(now='2026-11-15T12:00:01+00:00')
        latest=self.item('J-001','journal_preparation')
        self.assertEqual(latest['id'],a['id']);self.assertIn(ids[0],latest['run_ids']);self.assertEqual(latest['review_status'],'approve')
        other=Actor('other-independent-reviewer','reviewer','demo_org','bird_bowl_demo', kind="human")
        self.review(latest,'reject',other)
        self.assertEqual(self.item('J-001','journal_preparation')['review_status'],'disputed')
        with self.assertRaises(ControlError):self.review(latest,'resolve_approve',other)
        resolver=Actor('third-independent-reviewer','reviewer','demo_org','bird_bowl_demo', kind="human")
        self.review(latest,'resolve_approve',resolver)
        latest=self.item('J-001','journal_preparation');self.assertEqual(latest['review_status'],'approve')
        self.assertEqual([d['decision'] for d in latest['decisions']],['approve','reject','resolve_approve'])

    def test_concurrent_duplicate_approvals_commit_one_decision(self):
        from concurrent.futures import ThreadPoolExecutor
        a=self.journal()
        def decide(_):
            try:self.review(a);return 'saved'
            except ControlError as exc:return exc.status
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(decide,range(2)))
        self.assertCountEqual(outcomes,['saved',409]);self.assertEqual(len(self.item('J-001','journal_preparation')['decisions']),1)

    def test_P14_decisions_cannot_be_repeated_or_overwritten(self):
        a=self.journal();self.review(a)
        with self.assertRaises(ControlError):self.review(a)
        other=Actor('other-reviewer','reviewer','demo_org','bird_bowl_demo', kind="human")
        self.review(a,'reject',other)
        a=self.item('J-001','journal_preparation');self.assertEqual(a['review_status'],'disputed')
        with self.assertRaises(ControlError):self.review(a)

    def test_P15_receipt_tolerance_is_explicit_client_policy(self):
        self.drain();r=self.source('receipt-TX-001');r['data']['date']='2026-11-02';self.intake_one(r)
        self.os.enqueue(actor(),'card_preparation');self.drain()
        self.assertIn('RECEIPT_DATE_POLICY_UNSET',self.item('demo_card_001:TX-001')['blockers'])
        value={'date_window_days':1,'amount_tolerance':None,'multiple_receipts':None,'vendor_method':None,'statement_substitution':None}
        rid=self.os.propose_rule(actor(),'receipt_matching','matching',value,'2026-11-01')
        self.os.enqueue(actor(),'card_preparation');self.drain()
        self.assertIn('RECEIPT_DATE_POLICY_UNSET',self.item('demo_card_001:TX-001')['blockers'])
        controller=Actor('receipt-controller','reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(self.os,controller,['approve_rule'])
        self.os.approve_rule(controller,rid,'Fictional one-day policy');self.os.enqueue(actor(),'card_preparation');self.drain();self.accept_revised_evidence('demo_card_001:TX-001')
        self.assertTrue(self.item('demo_card_001:TX-001')['eligible'])
        r['data']['date']='2026-11-01';self.intake_one(r,'two-days');self.os.enqueue(actor(),'card_preparation');self.drain()
        self.assertIn('RECEIPT_DATE_MISMATCH',self.item('demo_card_001:TX-001')['blockers'])

    def test_handlers_only_receive_declared_sources_and_accounting_code_changes_stale(self):
        claim=self.os.claim(actor('worker'))
        self.os.commit(actor('worker'),claim,__import__('accounting_agent.modules',fromlist=['CAPABILITIES']).CAPABILITIES[claim['capability']].handler(claim['context']))
        claim=self.os.claim(actor('worker'))
        self.assertTrue(all(s['kind'] in ('transaction','receipt','statement','statement_control') for s in claim['context']['sources']))
        self.assertNotIn('required_close_evidence',claim['context']['profile'])
        self.drain();a=self.item('J-001','journal_preparation');self.review(a)
        old=Path.read_text
        def changed(path,*args,**kw):
            value=old(path,*args,**kw)
            return value+'\n# changed accounting handler\n' if path.name=='modules.py' else value
        with patch.object(Path,'read_text',changed):
            from accounting_agent.service import AccountingOS
            fresh=AccountingOS(self.path,[SCOPE])
        self.assertEqual(next(x for x in fresh.state(actor())['artifacts'] if x['id']==a['id'])['review_status'],'stale')

    def test_journal_document_does_not_invalidate_card_review(self):
        self.drain();a=self.item('demo_card_001:TX-001');self.review(a)
        self.intake_one({'kind':'document','key':'unrelated-support','data':{'document_type':'journal_support','content':'Fictional support unrelated to card'}},'support-only')
        a=next(x for x in self.os.state(actor())['artifacts'] if x['id']==a['id'])
        self.assertEqual(a['review_status'],'approve')

    def test_P16_unrelated_receipt_keeps_approved_journal(self):
        a=self.journal();self.review(a);self.os.intake(actor(),load('fixtures/late_receipt.json'))
        a=next(x for x in self.os.export(actor())['artifacts'] if x['id']==a['id']);self.assertEqual(a['review_status'],'approve')


# Share setup/helpers while keeping the original 41 tests executed exactly once.
for _name in list(helpers.PlatformCase.__dict__):
    if _name.startswith('test_'):
        setattr(ReviewerProbes,_name,None)
