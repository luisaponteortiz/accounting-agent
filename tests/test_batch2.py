import copy
from accounting_agent.core import Actor, ControlError
from accounting_agent.demo import actor, grant_fixture_authority, prepare_profile
from tests import test_platform as helpers


def reviewer(name='rule-controller'):
    return Actor(name,'reviewer','demo_org','bird_bowl_demo',kind='human')


class Batch2(helpers.PlatformCase):
    def controller(self):
        who=reviewer();grant_fixture_authority(self.os,who,['approve_rule','approve_profile','approve_mandate','review','disposition','finalize','lock']);return who

    def test_T09_proposed_policy_never_runs_and_self_approval_denied(self):
        p=copy.deepcopy(self.profile);p['version']='proposed';p['policies']['receipt_required']=False
        sid=self.os.onboard(actor(),p,effective_from='2026-11-01')
        self.drain();self.assertIn('MISSING_RECEIPT',self.item('demo_card_001:TX-002')['blockers'])
        own=Actor(actor().id,'reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(self.os,own,['approve_profile','approve_rule'])
        with self.assertRaises(ControlError):self.os.approve_profile_version(own,sid,'Self approval forbidden')
        self.os.approve_profile_version(self.controller(),sid,'Independent fictional decision')
        self.os.enqueue(actor(),'card_preparation');self.drain();self.assertNotIn('MISSING_RECEIPT',self.item('demo_card_001:TX-002')['blockers'])

    def test_T09_effective_dated_rule_and_service_proposal(self):
        self.drain();a=self.item('demo_card_001:TX-001');self.review(a)
        value=copy.deepcopy(self.profile['vendors'][0]);value['category']='DEMO_REPAIRS'
        rid=self.os.propose_rule(actor('worker'),'vendor_mapping',value['id'],value,'2026-12-01')
        before=self.item('demo_card_001:TX-001');self.assertEqual(before['review_status'],'approve')
        self.os.approve_rule(self.controller(),rid,'Independent future-period fictional mapping')
        self.os.open_period(actor('reviewer'),'2026-12','2026-12-01','2026-12-31','Fictional December')
        self.assertEqual(self.item('demo_card_001:TX-001')['review_status'],'approve')
        with self.os.store.transaction() as db:
            self.assertEqual(next(r for r in self.os.rules_at(db,actor().scope,'2026-11-03') if r['kind']=='vendor_mapping' and r['rule_key']==value['id'])['value']['category'],'DEMO_OFFICE_SUPPLIES')
            self.assertEqual(next(r for r in self.os.rules_at(db,actor().scope,'2026-12-03') if r['kind']=='vendor_mapping' and r['rule_key']==value['id'])['value']['category'],'DEMO_REPAIRS')
        service=Actor('service-controller','reviewer','demo_org','bird_bowl_demo',kind='service');grant_fixture_authority(self.os,service,['approve_rule'])
        r2=self.os.propose_rule(actor('worker'),'vendor_mapping',value['id'],value,'2027-01-01')
        with self.assertRaises(ControlError):self.os.approve_rule(service,r2,'Services cannot approve')

    def test_T11_client_sample_cannot_waive_missing_basis(self):
        p=copy.deepcopy(self.profile);p['version']='fictional-client-sample';p['profile_class']='client_sample'
        prepare_profile(self.os,actor(),p,effective_from='2026-11-01')
        self.os.enqueue(actor(),'journal_preparation');self.drain()
        a=self.item('J-001','journal_preparation');self.assertIn('CLIENT_FACT_MISSING:accounting_basis',a['blockers']);self.assertFalse(a['eligible'])

    def test_T11_explicit_demo_waivers_are_exported(self):
        self.drain();a=self.item('J-001','journal_preparation')
        self.assertIn('accounting_basis',a['payload']['fact_waivers']);self.assertTrue(a['eligible'])

    def test_T12_order_removal_and_supersession(self):
        t=copy.deepcopy(self.packet['sources'][0]);t['as_of']=2;t['data']['amount']='45.00'
        self.intake_one(t,'seq2');old=copy.deepcopy(t);old['as_of']=1;old['data']['amount']='42.50';self.intake_one(old,'seq1')
        st=self.os.state(actor());self.assertEqual(next(s for s in st['sources'] if s['source_key']==t['key'])['value']['amount'],'45.00')
        removed=copy.deepcopy(t);removed.update(as_of=3,tombstone=True,removal_reason='voided');self.intake_one(removed,'remove')
        self.assertFalse(any(s['source_key']==t['key'] for s in self.os.state(actor())['sources']))
        new=copy.deepcopy(next(s for s in self.packet['sources'] if s['key']=='demo_card_001:TX-007'));new['key']='demo_card_001:SETTLED';new['data'].update(source_id='SETTLED',status='posted',supersedes_source_id='TX-007');new['as_of']=1
        self.intake_one(new,'settled');self.assertFalse(any(s['source_key']=='demo_card_001:TX-007' for s in self.os.state(actor())['sources']))
        self.assertTrue(self.os.export(actor())['source_links'])

    def test_T12_evidence_before_period_and_boundary_receipt(self):
        from accounting_agent.demo import SCOPE,load
        from accounting_agent.service import AccountingOS
        from pathlib import Path
        other=AccountingOS(Path(self.temp.name)/'early.sqlite3',[SCOPE]);prepare_profile(other,actor(),self.profile)
        other.intake(actor(),self.packet);other.open_period(actor('reviewer'),'2026-11','2026-11-01','2026-11-30','Open after intake')
        other.intake(actor(),dict(self.packet,batch_id='replay'))
        st=other.state(actor());self.assertFalse(any(e['source_key'] in ('demo-card-control','journal-support-001','trial-balance-placeholder') for e in st['source_exceptions']))
        t=copy.deepcopy(self.packet['sources'][0]);t['data']['date']='2026-11-01'
        receipt=copy.deepcopy(next(s for s in self.packet['sources'] if s['key']=='receipt-TX-001'));receipt['data']['date']='2026-10-31'
        self.os.intake(actor(),dict(self.packet,batch_id='boundary',sources=[receipt,t]));self.os.enqueue(actor(),'card_preparation');self.drain()
        a=self.item(t['key']);self.assertNotIn('MISSING_RECEIPT',a['blockers']);self.assertTrue(any(e['source_key']==receipt['key'] for e in a['payload']['data']['evidence']))

    def test_T10_mandate_requires_independence_freshness_and_target_period(self):
        m=self.os.create_mandate(actor(),['journal_preparation'],'2026-12-01T00:00:00+00:00','2026-12-04T00:00:00+00:00',86400,3,period_rule={'kind':'fixed','period_id':'2026-11'},freshness={'journal':'occurrence_start'})
        own=Actor(actor().id,'reviewer','demo_org','bird_bowl_demo',kind='human');grant_fixture_authority(self.os,own,['approve_mandate'])
        with self.assertRaises(ControlError):self.os.approve_mandate(own,m,'Cannot approve own authority')
        self.os.approve_mandate(self.controller(),m,'Independent fictional mandate')
        self.assertEqual(self.os.tick(actor(),'2026-12-01T12:00:00+00:00'),[])
        self.assertTrue(any(o['status']=='awaiting_evidence' for o in self.os.state(actor())['occurrences']))
        j=copy.deepcopy(next(s for s in self.packet['sources'] if s['key']=='J-001'));j['as_of']='2026-12-01T12:01:00+00:00';self.intake_one(j,'fresh-journal');self.drain()
        runs=[r for r in self.os.state(actor())['runs'] if r['mandate_id']==m];self.assertEqual(len(runs),1);self.assertEqual(runs[0]['period_id'],'2026-11')
        value=copy.deepcopy(self.profile['policies']);value['receipt_required']=False
        rid=self.os.propose_rule(actor(),'review_policy','review',value,'2026-11-01');self.os.approve_rule(self.controller(),rid,'Changed bound policy')
        self.os.tick(actor(),'2026-12-02T12:00:00+00:00')
        self.assertEqual(next(x for x in self.os.state(actor())['mandates'] if x['id']==m)['status'],'needs_reconfirmation')

    def test_T12_tombstone_without_sequence_and_older_packet_replay(self):
        self.os.open_period(actor('reviewer'),'2026-12','2026-12-01','2026-12-31','Fictional move target')
        t=copy.deepcopy(self.packet['sources'][0]);t['data']['date']='2026-12-03';t['as_of']=2;self.intake_one(t,'dated-seq2')
        self.os.intake(actor(),self.packet)
        with self.os.store.transaction() as db:
            self.assertTrue(any(s['source_key']==t['key'] for s in self.os.period_sources(db,actor(),'2026-12')))
            self.assertFalse(any(s['source_key']==t['key'] for s in self.os.period_sources(db,actor(),'2026-11')))
        pending=copy.deepcopy(next(s for s in self.packet['sources'] if s['key']=='demo_card_001:TX-007'));pending.update(tombstone=True,removal_reason='feed_removed');self.intake_one(pending,'remove-identical-bytes')
        self.assertFalse(any(s['source_key']==pending['key'] for s in self.os.state(actor())['sources']))


    def test_T09_chart_author_cannot_erase_lineage_with_cosmetic_profile(self):
        chart_author=Actor('chart-author','preparer','demo_org','bird_bowl_demo',kind='human')
        p=copy.deepcopy(self.profile);p['version']='chart-edited';p['accounts'].append({'id':'FICTIONAL_UNUSED','type':'expense','active':True})
        prepare_profile(self.os,chart_author,p,effective_from='2026-11-01')
        p['version']='cosmetic-later';p['notice']='Fictional cosmetic revision'
        colleague=Actor('cosmetic-editor','preparer','demo_org','bird_bowl_demo',kind='human');prepare_profile(self.os,colleague,p,effective_from='2026-11-01')
        self.os.enqueue(actor(),'journal_preparation');self.drain()
        a=self.item('J-001','journal_preparation');self.assertIn(chart_author.id,a['contributors'])
        reviewer=Actor(chart_author.id,'reviewer','demo_org','bird_bowl_demo',kind='human')
        with self.assertRaises(ControlError):self.review(a,who=reviewer)


    def test_T09_unrelated_close_rule_preserves_card_and_journal_review(self):
        self.drain();card=self.item('demo_card_001:TX-001');journal=self.item('J-001','journal_preparation');self.review(card);self.review(journal)
        rid=self.os.propose_rule(actor(),'close_checklist','close',[{'type':'document','document_type':'fictional_new_close_document'}],'2026-11-01');self.os.approve_rule(self.controller(),rid,'Unrelated fictional close requirement')
        state=self.os.state(actor());self.assertTrue(all(next(a for a in state['artifacts'] if a['id']==item['id'])['review_status']=='approve' for item in (card,journal)))


    def test_T09_model_requirement_uses_item_effective_date(self):
        value=copy.deepcopy(self.profile['policies']);value['model_review_required']=True
        rid=self.os.propose_rule(actor(),'review_policy','review',value,'2026-11-10');self.os.approve_rule(self.controller(),rid,'Fictional future required model control; model remains unavailable')
        self.os.enqueue(actor(),'card_preparation');self.os.enqueue(actor(),'journal_preparation');self.drain()
        self.assertTrue(self.item('demo_card_001:TX-001')['eligible'])
        self.assertIn('MODEL_REVIEW_UNAVAILABLE',self.item('J-001','journal_preparation')['blockers'])



for _name in list(helpers.PlatformCase.__dict__):
    if _name.startswith('test_'):setattr(Batch2,_name,None)
