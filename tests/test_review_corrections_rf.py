"""RF regressions using fictional service operations and read-only invariants."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class RFCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
        spec=importlib.util.spec_from_file_location('rf_fixtures',path);cls.p=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(cls.p)
    @classmethod
    def tearDownClass(cls):cls.p.h.TMP.cleanup()
    def send(self,o,label,rows):
        result=self.p.send(o,label,rows);self.assertEqual(result[0],'ok',result);return result[1]
    def invariant(self,o):
        """Every first declared target on file is linked, including removed claimants."""
        p=self.p
        with o.store.connect() as db:
            for row in db.execute("SELECT source_key,snapshot_id FROM source_heads WHERE scope=? AND kind='transaction'",(p.SCOPE,)):
                declaration=db.execute("SELECT payload FROM accounting_events WHERE scope=? AND item_key=? AND code='SOURCE_CLAIM_DECLARED' ORDER BY id LIMIT 1",(p.SCOPE,row['source_key'])).fetchone()
                if not declaration:continue
                target=json.loads(declaration['payload'])['target_key']
                on_file=db.execute("SELECT 1 FROM source_heads WHERE scope=? AND kind='transaction' AND source_key=?",(p.SCOPE,target)).fetchone()
                if on_file:
                    link=db.execute("SELECT 1 FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id JOIN snapshots old ON old.id=l.old_snapshot_id WHERE l.scope=? AND n.kind='transaction' AND n.source_key=? AND old.source_key=?",(p.SCOPE,row['source_key'],target)).fetchone()
                    self.assertIsNotNone(link,(row['source_key'],target))
    def approve(self,o,key):
        p=self.p;p.prep(o)
        a=p.gov(o,p.K(key),'2026-12')
        if a and p.rb.REVISED in a['blockers']:
            self.assertEqual(p.dispose(o,p.K(key),p.rb.REVISED,'revised_evidence_accepted',period='2026-12')[0],'ok');p.prep(o)
        a=p.clear_and_approve(o,key)
        self.assertIsNotNone(a);self.assertTrue(a['eligible'],a['blockers']);self.assertTrue(p.approved(o,p.K(key),'2026-12'))
    def test_RF01_retained_message_matrix_and_repeated_claim(self):
        p=self.p
        # A replacement may be absent, present, approved before, or attempted after the claim.
        for known,approved,replacement,conflicting in itertools.product((False,True),(False,True),('none','before','approved-before','after','approve-after'),(False,True)):
            with self.subTest(known=known,approved=approved,replacement=replacement,conflicting=conflicting):
                o=p.base()
                if known:self.send(o,'p',p.p_rows())
                self.send(o,'q7',p.q_rows(as_of=7));p.prep(o)
                if approved:self.approve(o,'Q')
                order=7 if conflicting else 6;amount='41.00' if conflicting else '40.00'
                self.send(o,'q6',[p.q(amount=amount,as_of=order)])
                z=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')]
                if replacement in ('before','approved-before'):
                    self.send(o,'z',z+[p.stmt(z,p.DEC,opening='100.00')])
                    if replacement=='approved-before':self.approve(o,'Z')
                head=p.head(o,'Q')
                self.assertTrue(self.send(o,'claim',[p.q('P',amount=amount,as_of=order)])['changed'])
                self.assertEqual(head,p.head(o,'Q'))
                self.assertFalse(p.approved(o,p.K('Q'),'2026-12'))
                if known or replacement!='approved-before':self.assertFalse(p.approved(o,p.K('Z'),'2026-12'))
                else:self.assertTrue(p.approved(o,p.K('Z'),'2026-12'))  # UC-20 is explicitly outside this pass.
                self.invariant(o)
                if replacement in ('after','approve-after'):self.send(o,'z',z+[p.stmt(z,p.DEC,opening='100.00')])
                if not known:
                    p.prep(o)
                    if replacement=='none':self.assertIn(p.UNRESOLVED,p.gov(o,p.K('Q'),'2026-12')['blockers'])
                    self.send(o,'target-arrives',p.p_rows())
                self.invariant(o);p.prep(o)
                expected={p.K('Q'),'receipt-Q'} if replacement=='none' else {p.K('Z'),'receipt-Z'}
                # A predecessor legitimately retired before the claim has no live artifact.
                self.assertTrue({p.K('Q'),'receipt-Q'} <= p.held_under(o) | {k for k,removed in p.sql(o,'SELECT source_key,removed FROM source_heads') if removed})
                self.assertTrue(expected<=p.held_under(o),(expected,p.held_under(o)))
                if replacement=='approve-after':self.assertIsNone(p.clear_and_approve(o,'Z'))
                before=p.rows_of(o)
                self.assertFalse(self.send(o,'claim-repeat',[p.q('P',amount=amount,as_of=order)])['changed'])
                self.assertEqual(before,p.rows_of(o));self.assertTrue(o.verify_audit(p.PREP))
    def test_RF01_first_claim_link_invariant_across_delivery_matrices(self):
        p=self.p
        families=(('target','head','old','claim'),('target','head','claim','replacement'),('target','claim','conflict','revision'))
        deliveries={'target':p.p_rows,'head':lambda:[p.q(as_of=7)],'old':lambda:[p.q(as_of=6)],'claim':lambda:[p.q('P',as_of=6)],'replacement':lambda:[p.sup('Z','2026-12-05','40.00','Q')],'conflict':lambda:[p.q('B',as_of=8)],'revision':lambda:[p.q(amount='41.00',as_of=9)]}
        for family in families:
            for order in itertools.permutations(family):
                with self.subTest(order=order):
                    o=p.base()
                    for i,name in enumerate(order):
                        self.send(o,'matrix-%d-%s'%(i,name),deliveries[name]());self.invariant(o)
                    self.assertTrue(o.verify_audit(p.PREP))
    def test_RF02_all_selectors_remain_contributors_for_confirm_replace_revision_and_descendant(self):
        p=self.p
        for confirm,version in itertools.product((False,True),('row','revision','replacement')):
            with self.subTest(confirm=confirm,version=version):
                o=p.base();self.send(o,'targets',p.b_rows()+p.b_rows('B2','2026-12-04'))
                self.send(o,'q',p.q_rows('B'));self.send(o,'second',[p.q('B2')]);p.prep(o)
                self.assertEqual(p.select(o,p.DR,'B2')[0],'ok')
                with o.store.connect() as db:before=[tuple(r) for r in db.execute('SELECT * FROM dispositions ORDER BY id')]
                self.assertEqual(p.select(o,p.DR2,'B2' if confirm else 'B')[0],'ok')
                key='Q'
                if version=='revision':self.send(o,'revision',[p.q(amount='41.00'),p.rc('Q','2026-12-03','41.00'),p.stmt([p.q(amount='41.00')],p.DEC,opening='100.00')])
                if version=='replacement':
                    z=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')];self.send(o,'z',z+[p.stmt(z,p.DEC,opening='100.00')]);key='Z'
                p.prep(o)
                # Clear ordinary controls without giving either selector a preparation role.
                for _ in range(4):
                    a=p.gov(o,p.K(key),'2026-12')
                    for code,choice in ((p.TRANSITION,'settlement_verified'),(p.rb.REVISED,'revised_evidence_accepted')):
                        if code in a['blockers']:self.assertEqual(p.dispose(o,p.K(key),code,choice,period='2026-12')[0],'ok')
                    p.prep(o)
                a=p.gov(o,p.K(key),'2026-12');self.assertTrue(a['eligible'],a['blockers'])
                with o.store.connect() as db:
                    artifact=db.execute('SELECT * FROM artifacts WHERE id=?',(a['id'],)).fetchone();contributors=o.contributors(db,p.SCOPE,artifact)
                    self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM dispositions ORDER BY id')][:len(before)],before)
                self.assertTrue({p.DR.id,p.DR2.id}<=set(contributors),contributors)
                for who in (p.DR,p.DR2):self.assertEqual(p.review(o,who,a,'approve')[0],'refused')
                self.assertEqual(p.review(o,p.REV3,a,'approve')[0],'ok');self.assertTrue(o.verify_audit(p.PREP))
    def test_RF03_transaction_reuses_current_result_and_matches_full_computation(self):
        p=self.p;o=p.base();self.send(o,'q',p.q_rows('B'));self.send(o,'second',[p.q('B2')]);p.prep(o)
        for phase in ('waiting','contested','selected','confirmed','revised','replacement','locked'):
            if phase=='contested':self.send(o,'targets',p.b_rows()+p.b_rows('B2','2026-12-04'))
            if phase=='selected':self.assertEqual(p.select(o,p.DR,'B2')[0],'ok')
            if phase=='confirmed':self.assertEqual(p.select(o,p.DR2,'B2')[0],'ok')
            if phase=='revised':self.send(o,'rev',[p.q(amount='41.00')])
            if phase=='replacement':self.send(o,'z',[p.sup('Z','2026-12-05','41.00','Q'),p.rc('Z','2026-12-05','41.00')])
            p.prep(o)
            if phase=='locked':o.lock_period(p.PADMIN,'2026-12','Fictional comparison lock','Unsettled synthetic items acknowledged')
            with self.subTest(phase=phase),o.store.transaction() as db:
                calls=[];original=o._current
                def tracked(db,actor,run):calls.append(run['id']);return original(db,actor,run)
                with patch.object(o,'_current',side_effect=tracked):fast=o.period_outcomes(db,p.PREP,'2026-12')
                self.assertEqual(len(calls),len(set(calls)),calls)
                with patch.object(o,'outcome_run_current',create=True,side_effect=lambda db,actor,run,cache:original(db,actor,run)):
                    full=o.period_outcomes(db,p.PREP,'2026-12')
                self.assertEqual(fast,full)
        # The ordinary demo has many artifacts sharing the same run.
        import tempfile
        from accounting_agent.demo import seed,actor,SCOPE
        from accounting_agent.service import AccountingOS
        with tempfile.TemporaryDirectory() as t:
            demo=AccountingOS(Path(t)/'equivalence.sqlite3',[SCOPE]);seed(demo);demo.drain(actor('worker'))
            with demo.store.transaction() as db:
                calls=[];original=demo._current
                def tracked(db,who,run):calls.append(run['id']);return original(db,who,run)
                with patch.object(demo,'_current',side_effect=tracked):fast=demo.period_outcomes(db,actor(),'2026-11')
                self.assertEqual(len(calls),len(set(calls)),calls)
                with patch.object(demo,'outcome_run_current',create=True,side_effect=lambda db,who,run,cache:original(db,who,run)):
                    self.assertEqual(fast,demo.period_outcomes(db,actor(),'2026-11'))

    def test_RF03_autocommit_always_recomputes_and_cache_is_local_to_one_call(self):
        p=self.p;o=p.base()
        class Autocommit:in_transaction=False
        with patch.object(o,'_current',side_effect=[True,False]) as full:
            cache={};run={'id':123}
            self.assertTrue(o.outcome_run_current(Autocommit(),p.PREP,run,cache))
            self.assertFalse(o.outcome_run_current(Autocommit(),p.PREP,run,cache))
            self.assertEqual(full.call_count,2);self.assertEqual(cache,{})

    def test_RF02_historical_ancestor_selector_survives_descendant_retargeting(self):
        p=self.p;o=p.base();self.send(o,'targets',p.b_rows()+p.b_rows('B2','2026-12-04')+p.b_rows('B3','2026-12-06'))
        self.send(o,'q',p.q_rows('B'));self.send(o,'q-other',[p.q('B2')]);p.prep(o)
        self.assertEqual(p.select(o,p.DR,'B2')[0],'ok')
        z=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')]
        self.send(o,'z',z+[p.stmt(z,p.DEC,opening='100.00')]);self.send(o,'z-other',[dict(p.tx('Z','2026-12-05','40.00'),supersedes=p.K('B3'))]);p.prep(o)
        self.assertEqual(p.select(o,p.DR2,'B3',item='Z')[0],'ok');p.prep(o)
        for _ in range(3):
            a=p.gov(o,p.K('Z'),'2026-12')
            for code,choice in ((p.TRANSITION,'settlement_verified'),(p.rb.REVISED,'revised_evidence_accepted')):
                if code in a['blockers']:self.assertEqual(p.dispose(o,p.K('Z'),code,choice,period='2026-12')[0],'ok')
            p.prep(o)
        a=p.gov(o,p.K('Z'),'2026-12');self.assertTrue(a['eligible'],a['blockers'])
        self.assertEqual(p.review(o,p.DR,a,'approve')[0],'refused')
        self.assertEqual(p.review(o,p.REV3,a,'approve')[0],'ok')
