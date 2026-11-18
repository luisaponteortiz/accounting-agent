"""Owner D-026 contract: fictional feed deliveries, authority and append-only decisions."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
CONFLICT='SOURCE_CLAIM_CONFLICT'
CHOICE='select_supersession_target'

class FeedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py'
        spec=importlib.util.spec_from_file_location('feed_contract_fixtures',path);cls.p=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(cls.p)
        cls.f=cls.p.h

    @classmethod
    def tearDownClass(cls):cls.f.TMP.cleanup()

    def send(self,o,name,rows,who=None):return o.intake(who or self.f.PREP2,self.f.packet(name,rows))
    def row(self,target,amount='40.00',**kw):return dict(self.f.tx('Y','2026-12-03',amount,**kw),supersedes=self.f.CARD+':'+target)
    def prep(self,o):self.f.run(o,'card_preparation','2026-12',self.f.PREP2)
    def gov(self,o):return self.f.gov(o,self.f.CARD+':Y','2026-12')
    def evidence(self,o):
        with o.store.connect() as db:
            r=db.execute("SELECT s.id,s.hash FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.scope=? AND h.source_key='receipt-Y'",(self.f.SCOPE,)).fetchone()
        return [{'snapshot_id':r['id'],'hash':r['hash']}]
    def decide(self,o,target,who=None,evidence=None):
        return o.disposition(who or self.f.DISP,'card_preparation','2026-12',self.f.CARD+':Y',CONFLICT,CHOICE,{'target_key':self.f.CARD+':'+target},self.evidence(o) if evidence is None else evidence,'Fictional independent feed-target decision')
    def setup_claim(self,first='B',known=True):
        f=self.f;o=f.approved_locked_november()
        if known:self.send(o,'target',[f.tx('B','2026-12-02','40.00'),f.rc('B','2026-12-02','40.00')])
        rows=[self.row(first),f.rc('Y','2026-12-03','40.00')]
        self.send(o,'first',rows+[f.stmt(rows,f.DEC,opening='100.00')]);self.prep(o)
        return o
    def chain_rows(self):return [self.f.sup('X','2026-12-02','40.00','A1'),self.f.rc('X','2026-12-02','40.00')]
    def retained(self,o):
        d=self.p.lifecycle(o);return {k:d[k] for k in ('source_snapshots','bindings','moves','links','events','decisions','heads')}

    def test_clause2_known_unknown_older_conflicting_and_approved(self):
        f=self.f
        for known in (True,False):
            for approved in (False,True):
                for conflict in (False,True):
                    with self.subTest(known=known,approved=approved,conflict=conflict):
                        o=f.approved_locked_november();rows=[f.tx('Y','2026-12-03','40.00',as_of=5),f.rc('Y','2026-12-03','40.00')]
                        self.send(o,'plain',rows+[f.stmt(rows,f.DEC,opening='100.00')]);self.prep(o)
                        if approved:self.assertEqual(f.review(o,f.REV2,self.gov(o),'approve')[0],'ok')
                        claim=self.row('A1' if known else 'X',amount='41.00' if conflict else '40.00',as_of=5 if conflict else 4)
                        self.assertTrue(self.send(o,'late',[claim])['changed'])
                        self.assertFalse(self.p.approved(o,f.CARD+':Y','2026-12'))
                        if not known:
                            self.prep(o);self.assertIn('SOURCE_TRANSITION_UNRESOLVED',self.gov(o)['blockers'])
                            self.send(o,'x',self.chain_rows())
                        self.prep(o);self.assertIsNone(self.gov(o));self.assertIn(f.CARD+':Y',self.p.held_under(o))
                        with o.store.connect() as db:
                            head=db.execute('SELECT s.payload,m.as_of FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id JOIN source_metadata m ON m.snapshot_id=s.id WHERE h.source_key=?',(f.CARD+':Y',)).fetchone()
                        self.assertEqual(json.loads(head['payload'])['amount'],'40.00');self.assertEqual(head['as_of'],'5')
                        before=self.retained(o)
                        self.assertFalse(self.send(o,'late-repeat',[claim])['changed']);self.assertEqual(before,self.retained(o))

    def test_clause7_both_targets_orders_pending_linked_third_and_repeats(self):
        f=self.f
        for first,second in (('B','X'),('X','B')):
            for known in (True,False):
                with self.subTest(first=first,known=known):
                    o=self.setup_claim(first,known=False)
                    if known:
                        self.send(o,'first-target',self.chain_rows() if first=='X' else [f.tx('B','2026-12-02','40.00')]);self.prep(o)
                    before=self.retained(o)
                    self.assertTrue(self.send(o,'second',[self.row(second)])['changed'])
                    after=self.retained(o)
                    for t in ('bindings','moves','links'):self.assertEqual(before[t],after[t])
                    self.assertTrue(self.send(o,'third',[self.row('W')])['changed'])
                    for i,target in enumerate((first,second,'W',second)):
                        before=self.retained(o);self.assertFalse(self.send(o,'repeat%d'%i,[self.row(target)])['changed']);self.assertEqual(before,self.retained(o))
                    self.send(o,'second-target',self.chain_rows() if second=='X' else [f.tx('B','2026-12-02','40.00')]);self.prep(o)
                    if self.gov(o):self.assertIn(CONFLICT,self.gov(o)['blockers'])
                    self.assertNotIn((f.CARD+':'+second,f.CARD+':Y'),self.p.links(o))
                    self.assertTrue(o.verify_audit(f.PREP))

    def test_clause7_earlier_approval_stales_and_existing_dispositions_cannot_clear(self):
        f=self.f;o=self.setup_claim()
        self.assertEqual(f.dispose(o,f.CARD+':Y','SOURCE_TRANSITION_REQUIRES_REVIEW','settlement_verified',period='2026-12')[0],'ok');self.prep(o)
        self.assertEqual(f.review(o,f.REV2,self.gov(o),'approve')[0],'ok')
        self.send(o,'second',[self.row('X')]);self.assertFalse(self.p.approved(o,f.CARD+':Y','2026-12'));self.prep(o)
        a=self.gov(o);self.assertIn(CONFLICT,a['blockers']);self.assertFalse(a['eligible'])
        f.dispose(o,f.CARD+':Y','SOURCE_TRANSITION_REQUIRES_REVIEW','settlement_verified',period='2026-12');self.prep(o)
        self.assertIn(CONFLICT,self.gov(o)['blockers'])
        for choice in ('settlement_verified','revised_evidence_accepted'):
            with self.assertRaises(Exception):o.disposition(f.DISP,'card_preparation','2026-12',f.CARD+':Y',CONFLICT,choice,{},self.evidence(o),'Cannot bypass the conflict')
        self.assertEqual(f.review(o,f.REV3,self.gov(o),'approve')[0],'refused')
        with self.assertRaises(Exception):o.finalize_package(f.FIN,'2026-12','card_preparation','No acknowledgement')

    def test_clause2_different_older_claim_is_contested_and_timestamp_order(self):
        f=self.f;o=self.setup_claim()
        self.send(o,'sequence-new',[self.row('B',as_of='2026-12-04T12:00:00Z')])
        self.send(o,'sequence-old',[self.row('X',as_of='2026-12-03T12:00:00Z')]);self.prep(o)
        self.assertIn(CONFLICT,self.gov(o)['blockers']);self.assertNotIn((f.CARD+':X',f.CARD+':Y'),self.p.links(o))

    def test_clause8_no_provider_release_with_open_target_early_or_last(self):
        f=self.f
        for early in (True,False):
            with self.subTest(early=early):
                o=self.setup_claim('X',False);self.send(o,'x',self.chain_rows())
                if early:self.send(o,'open-before',[f.tx('B','2026-12-02','40.00')])
                before=self.retained(o);self.send(o,'second',[self.row('B')]);mid=self.retained(o)
                for t in ('bindings','moves','links'):self.assertEqual(before[t],mid[t])
                if not early:self.send(o,'open-last',[f.tx('B','2026-12-02','40.00')])
                self.prep(o);self.assertIsNone(self.gov(o));self.assertIn(f.CARD+':Y',self.p.held_under(o))
                o.reopen_period(f.PADMIN,'2026-11','Authorized reopen');self.prep(o)
                self.assertIn(CONFLICT,self.gov(o)['blockers'])

    def test_clause9_refuses_missing_grant_suppliers_undeclared_and_bad_support(self):
        f=self.f;o=self.setup_claim();other=f.human('second-supplier','preparer')
        self.send(o,'second',[self.row('X')],other)
        for actor in (f.REV3,f.human(f.PREP2.id,'reviewer'),f.human(other.id,'reviewer')):
            if actor.id!=f.REV3.id:o.grant_authority(f.ADMIN,actor.id,['disposition'],'Fictional test grant')
            with self.subTest(actor=actor.id),self.assertRaises(Exception):self.decide(o,'B',actor)
        for target,refs in (('UNDECLARED',None),('B',[]),('B',[{'snapshot_id':999999,'hash':'ab'*32}])):
            with self.subTest(target=target,refs=refs),self.assertRaises(Exception):self.decide(o,target,evidence=refs)

    def test_clause9_first_target_stands_clears_only_conflict_and_preserves_history(self):
        f=self.f;o=self.setup_claim();self.send(o,'second',[self.row('X')]);self.prep(o)
        before=self.p.lifecycle(o);self.decide(o,'B');after=self.p.lifecycle(o)
        for table in ('bindings','moves','links'):self.assertEqual(before[table],after[table])
        self.assertTrue(self.p.prefix_kept(before,after,('source_snapshots','events','decisions','artifacts','packages','audit')))
        self.prep(o);a=self.gov(o);self.assertNotIn(CONFLICT,a['blockers']);self.assertIn('SOURCE_TRANSITION_REQUIRES_REVIEW',a['blockers']);self.assertNotEqual(a['review_status'],'approve');self.assertTrue(o.verify_audit(f.PREP))

    def test_clause9_second_target_known_or_unknown_has_ordinary_consequences(self):
        f=self.f
        for known,locked in ((False,False),(True,False),(True,True)):
            with self.subTest(known=known,locked=locked):
                o=self.setup_claim();self.send(o,'second',[self.row('X')])
                if known:self.send(o,'x',self.chain_rows() if locked else [f.tx('X','2026-12-02','40.00')])
                self.decide(o,'X');self.prep(o)
                if locked:self.assertIsNone(self.gov(o));self.assertIn(f.CARD+':Y',self.p.held_under(o))
                else:
                    a=self.gov(o);self.assertNotIn(CONFLICT,a['blockers']);self.assertNotEqual(a['review_status'],'approve')
                    self.assertEqual('SOURCE_TRANSITION_UNRESOLVED' in a['blockers'],not known)
                self.assertTrue(o.verify_audit(f.PREP))

    def test_clause9_release_needs_lock_and_reopen_does_not_clear_conflict(self):
        f=self.f;o=self.setup_claim('X',False);self.send(o,'x',self.chain_rows());self.send(o,'b',[f.tx('B','2026-12-02','40.00')]);self.send(o,'second',[self.row('B')])
        with self.assertRaises(Exception):self.decide(o,'B')
        o.grant_authority(f.ADMIN,f.DISP.id,['lock'],'Fictional combined release authority')
        self.decide(o,'B');self.prep(o);self.assertNotIn(f.CARD+':Y',self.p.held_under(o));self.assertIsNotNone(self.gov(o));self.assertNotEqual(self.gov(o)['review_status'],'approve')
        self.assertTrue(o.verify_audit(f.PREP))

    def test_cycle_self_refusals_remain_atomic_before_contest(self):
        f=self.f;o=self.setup_claim('X',False);self.send(o,'x',[f.sup('X','2026-12-02','40.00','Y')])
        before=self.p.lifecycle(o)
        for target in ('Y','X'):
            with self.assertRaises(Exception):self.send(o,'invalid-'+target,[self.row(target)])
            self.assertEqual(before,self.p.lifecycle(o))

    def test_conflict_follows_descendants_and_their_release_requires_lock(self):
        f=self.f;o=self.setup_claim('X',False)
        self.send(o,'z',[f.sup('Z','2026-12-04','40.00','Y'),f.rc('Z','2026-12-04','40.00')])
        self.send(o,'second',[self.row('B')]);self.send(o,'x',self.chain_rows());self.send(o,'b',[f.tx('B','2026-12-02','40.00')])
        self.prep(o);self.assertIsNone(f.gov(o,f.CARD+':Z','2026-12'))
        with self.assertRaises(Exception):self.decide(o,'B',evidence=[{'snapshot_id':s['id'],'hash':s['hash']} for s in o.export(f.PREP)['evidence_history'] if s['source_key']=='receipt-Z'])
        o.reopen_period(f.PADMIN,'2026-11','Authorized reopen');self.prep(o)
        self.assertIn(CONFLICT,f.gov(o,f.CARD+':Z','2026-12')['blockers'])

    def test_confirmation_held_target_needs_no_lock_and_new_third_claim_reopens(self):
        f=self.f;o=self.setup_claim('X',False);self.send(o,'x',self.chain_rows());self.send(o,'second',[self.row('B')])
        before=self.retained(o);self.decide(o,'X');after=self.retained(o)
        for table in ('bindings','moves','links'):self.assertEqual(before[table],after[table])
        self.assertNotIn(f.CARD+':Y',o.export(f.PREP)['source_claim_conflicts'])
        self.send(o,'third',[self.row('W')]);self.assertIn(f.CARD+':Y',o.export(f.PREP)['source_claim_conflicts'])
        self.prep(o);self.assertIsNone(self.gov(o))

    def test_target_decision_persists_through_revision_and_retains_review_contributor(self):
        f=self.f;o=self.setup_claim();self.send(o,'second',[self.row('X')]);rid=self.decide(o,'B')
        self.send(o,'revision',[f.tx('Y','2026-12-03','41.00')]);self.prep(o)
        a=self.gov(o);self.assertNotIn(CONFLICT,a['blockers'])
        self.assertIn(rid,a['payload']['data']['disposition_ids'])
        self.send(o,'third',[self.row('W',amount='41.00')]);self.prep(o)
        self.assertIn(CONFLICT,self.gov(o)['blockers'])
        self.assertNotIn(rid,self.gov(o)['payload']['data']['disposition_ids'])

    def test_clause8_plain_date_revision_cannot_release_locked_late_activity(self):
        f=self.f;o=f.approved_locked_november()
        self.send(o,'december',[f.tx('Y','2026-12-03','40.00'),f.rc('Y','2026-12-03','40.00')])
        self.send(o,'late-november',[f.tx('Y','2026-11-20','40.00')])
        self.assertTrue(any(e['source_key']==f.CARD+':Y' and e['period_id']=='2026-11' for e in o.state(f.PREP)['source_exceptions']))
        self.send(o,'date-back-to-december',[f.tx('Y','2026-12-03','40.00')]);self.prep(o)
        self.assertIsNone(self.gov(o));self.assertIn(f.CARD+':Y',self.p.held_under(o))
        o.reopen_period(f.PADMIN,'2026-11','Fictional authorized release');self.prep(o)
        self.assertIsNotNone(self.gov(o));self.assertNotEqual(self.gov(o)['review_status'],'approve')

    def test_selected_target_in_locked_late_activity_quarantines_the_claimant(self):
        f=self.f;o=self.setup_claim()
        self.send(o,'other-target',[f.tx('L','2026-12-02','40.00')])
        self.send(o,'late-target-date',[f.tx('L','2026-11-20','40.00')])
        self.send(o,'second',[self.row('L')]);self.decide(o,'L');self.prep(o)
        self.assertIsNone(self.gov(o));self.assertIn(f.CARD+':Y',self.p.held_under(o))
        self.assertTrue(o.verify_audit(f.PREP))

    def test_target_selector_cannot_review_a_descendant_using_their_selection(self):
        f=self.f;o=f.approved_locked_november();selector=f.human('independent-target-selector','reviewer')
        o.grant_authority(f.ADMIN,selector.id,['disposition','review'],'Fictional separate target reviewer')
        z=[f.sup('Z','2026-12-04','40.00','Y'),f.rc('Z','2026-12-04','40.00')]
        self.send(o,'b',[f.tx('B','2026-12-02','40.00'),f.rc('B','2026-12-02','40.00')])
        self.send(o,'y',[self.row('B'),f.rc('Y','2026-12-03','40.00'),f.stmt(z,f.DEC,opening='100.00')]);self.send(o,'z',z)
        self.send(o,'second',[self.row('X')]);self.prep(o)
        with o.store.connect() as db:
            doc=db.execute("SELECT s.id,s.hash FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.source_key='receipt-Z'").fetchone()
        rid=self.decide(o,'B',selector,[{'snapshot_id':doc['id'],'hash':doc['hash']}]);self.prep(o)
        self.assertEqual(f.dispose(o,f.CARD+':Z','SOURCE_TRANSITION_REQUIRES_REVIEW','settlement_verified',period='2026-12')[0],'ok');self.prep(o)
        a=f.gov(o,f.CARD+':Z','2026-12');self.assertTrue(a['eligible'])
        self.assertIn(rid,a['payload']['data']['disposition_ids'])
        self.assertEqual(f.review(o,selector,a,'approve')[0],'refused')
        self.assertEqual(f.review(o,f.REV3,a,'approve')[0],'ok')
