from accounting_agent.demo import prepare_profile, grant_fixture_authority, create_fixture_mandate
"""Regression tests for the independent N01-N07 failure paths."""
import copy
import sqlite3
from pathlib import Path
from accounting_agent.core import Actor, ControlError, normalize
from accounting_agent.demo import SCOPE, actor
from tests import test_platform as helpers


def human(ident,role='preparer'):
    return Actor(ident,role,'demo_org','bird_bowl_demo',kind='human')


class Corrections(helpers.PlatformCase):
    def source(self,key):return copy.deepcopy(next(s for s in self.packet['sources'] if s['key']==key))

    def test_N06_combining_marks_are_semantic(self):
        for left,right in [('กิน','กัน'),('किताब','कुताब'),('דָּבָר','דֶּבֶר')]:
            self.assertNotEqual(normalize(left),normalize(right))
        p=copy.deepcopy(self.profile);p['version']='marks';p['vendors'].append({'id':'thai','name':'Fictional Thai vendor','aliases':['กิน'],'category':'DEMO_OFFICE_SUPPLIES'})
        prepare_profile(self.os,actor(),p)
        t=self.source('demo_card_001:TX-001');t['data']['description']='กัน';r=self.source('receipt-TX-001');r['data']['vendor']='กัน'
        self.intake_one(t,'thai-t');self.intake_one(r,'thai-r');self.os.enqueue(actor(),'card_preparation');self.drain()
        a=self.item('demo_card_001:TX-001');self.assertEqual(a['blockers'],['EVIDENCE_REVISED_REQUIRES_REVIEW','UNKNOWN_CATEGORY','UNKNOWN_VENDOR']);self.assertFalse(a['eligible'])

    def test_N07_actor_kind_is_required(self):
        with self.assertRaises(TypeError):Actor('omitted','reviewer','demo_org','bird_bowl_demo')
        self.assertEqual(actor('worker').kind,'service')

    def test_N01_all_decisions_refused_under_lock(self):
        self.drain();a=self.item('J-001','journal_preparation');self.review(a)
        self.os.lock_period(actor('reviewer'),'2026-11','Synthetic lock',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        before=len(self.os.state(actor())['artifacts'])
        for choice in ('approve','reject','revoke','resolve_approve','resolve_reject'):
            with self.subTest(choice=choice),self.assertRaises(ControlError) as caught:self.review(a,choice)
            self.assertEqual(caught.exception.status,409);self.assertEqual(str(caught.exception),'PERIOD_LOCKED')
        self.assertEqual(self.item('J-001','journal_preparation')['review_status'],'approve')
        self.os.reopen_period(actor('reviewer'),'2026-11','Synthetic reopen');self.review(a,'revoke')
        self.assertEqual(len(self.os.state(actor())['artifacts']),before)

    def test_N04_historical_evidence_supplier_cannot_review(self):
        author=human('original-source-author');editor=human('editor')
        j=self.source('J-001');j['key']='J-900'
        packet=dict(self.packet,batch_id='author',sources=[j]);self.os.intake(author,packet)
        j=copy.deepcopy(j);j['data']['memo']+='.';self.os.intake(editor,dict(packet,batch_id='editor',sources=[j]))
        self.os.enqueue(editor,'journal_preparation');self.drain()
        with self.assertRaises(ControlError) as caught:self.review(self.item('J-900','journal_preparation'),who=human(author.id,'reviewer'))
        self.assertEqual(caught.exception.status,403)

    def test_N05_historical_profile_author_cannot_review(self):
        first=human('mapping-author');other=human('profile-editor')
        p=copy.deepcopy(self.profile);p['version']='authored';p['vendors'][0]['aliases'].append('Fictional authored alias');prepare_profile(self.os,first,p)
        p=copy.deepcopy(p);p['version']='edited';p['notice']+=' wording';prepare_profile(self.os,other,p)
        self.os.enqueue(other,'card_preparation');self.drain()
        with self.assertRaises(ControlError) as caught:self.review(self.item('demo_card_001:TX-001'),who=human(first.id,'reviewer'))
        self.assertEqual(caught.exception.status,403)

    def test_N03_other_enqueuer_does_not_displace_rejection(self):
        self.drain();a=self.item('J-001','journal_preparation');self.review(a,'reject')
        colleague=human('colleague');create_fixture_mandate(self.os,colleague,['journal_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        self.os.tick(colleague,'2026-11-15T12:00:00+00:00');self.drain(now='2026-11-15T12:00:01+00:00')
        b=self.item('J-001','journal_preparation');self.assertEqual(a['id'],b['id']);self.assertEqual(b['review_status'],'reject');self.assertIn(colleague.id,b['contributors'])
        self.assertNotIn('contributors',b['payload'])
        self.review(b,who=human('second-reviewer','reviewer'))
        self.assertEqual(self.item('J-001','journal_preparation')['review_status'],'disputed')
        with self.os.store.transaction() as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute('DELETE FROM artifact_contributors')

    def test_later_contributor_loses_further_review_rights(self):
        self.drain();a=self.item('J-001','journal_preparation');reviewer=human('future-enqueuer','reviewer');self.review(a,who=reviewer)
        prep=human(reviewer.id);create_fixture_mandate(self.os,prep,['journal_preparation'],'2026-11-15T00:00:00+00:00','2026-11-20T00:00:00+00:00',86400,3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
        self.os.tick(prep,'2026-11-15T12:00:00+00:00');self.drain(now='2026-11-15T12:00:01+00:00')
        b=self.item('J-001','journal_preparation');self.assertEqual(b['id'],a['id']);self.assertEqual(b['review_status'],'approve')
        with self.assertRaises(ControlError) as caught:self.review(b,'revoke',reviewer)
        self.assertEqual(caught.exception.status,403)

    def test_N02_locked_source_move_cannot_govern_two_periods(self):
        self.drain();a=self.item('demo_card_001:TX-001');self.review(a)
        self.os.lock_period(actor('reviewer'),'2026-11','Lock fictional November',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
        self.os.open_period(actor('reviewer'),'2026-12','2026-12-01','2026-12-31','Fictional December')
        t=self.source('demo_card_001:TX-001');t['data']['date']='2026-12-01'
        r=self.source('receipt-TX-001');r['data']['date']='2026-12-01'
        c=self.source('demo-card-control');c['key']='control-dec';c['data'].update(period_start='2026-12-01',period_end='2026-12-31',line_count=1,line_ids=['TX-001'],totals={k:('42.50' if k=='purchase' else '0.00') for k in c['data']['totals']},opening_balance='1000.00',closing_balance='1042.50')
        self.os.intake(actor(),dict(self.packet,batch_id='moved',sources=[t,r,c]))
        rid=self.os.enqueue(actor(),'card_preparation','2026-12');self.drain()
        st=self.os.state(actor());self.assertFalse(any(rid in x['run_ids'] and x['item_key']==a['item_key'] for x in st['artifacts']))
        self.assertTrue(any(e['reason']=='SOURCE_MOVED_FROM_LOCKED_PERIOD' and e['source_key']==a['item_key'] for e in st['source_exceptions']))
        self.assertEqual(sum(x['current'] for x in st['artifacts'] if x['item_key']==a['item_key']),1)
        self.os.reopen_period(actor('reviewer'),'2026-11','Authorize review of moved item')
        rid=self.os.enqueue(actor(),'card_preparation','2026-12');self.drain()
        st=self.os.state(actor());current=[x for x in st['artifacts'] if x['current'] and x['item_key']==a['item_key']]
        self.assertEqual(len(current),1);self.assertEqual(current[0]['period_id'],'2026-12')
        self.assertEqual(next(x for x in st['artifacts'] if x['id']==a['id'])['review_status'],'stale')
        self.assertTrue(all(m['had_approval'] for m in self.os.export(actor())['source_move_history'] if m['snapshot_id'] in [e['snapshot_id'] for e in st['source_exceptions'] if e['source_key']==a['item_key']]))


for _name in list(helpers.PlatformCase.__dict__):
    if _name.startswith('test_'):setattr(Corrections,_name,None)
