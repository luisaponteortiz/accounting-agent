"""Review tests for owner decision D-038: UC-21 and UC-22 of the card-feed contract.

UC-21: an identical repeat of a card row, or of its receipt, that a live
replacement has retired changes nothing. UC-22: a message with no order value
for a row governed by one is kept once and flagged. Every scenario uses the
fictional fixtures of the independent RE review through service operations.
"""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
ORDERS=(7,'2026-12-03T10:00:00+00:00',None)
MIXED='SOURCE_ORDER_MIXED'


class FeedRepeatDecisions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
        spec=importlib.util.spec_from_file_location('uc_fixtures',path);cls.p=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]),contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(cls.p)
    @classmethod
    def tearDownClass(cls):cls.p.h.TMP.cleanup()

    def quiet(self,function,*args,**kwargs):
        with contextlib.redirect_stdout(io.StringIO()):return function(*args,**kwargs)
    def send(self,o,label,rows):
        result=self.quiet(self.p.send,o,label,rows);self.assertEqual(result[0],'ok',result);return result[1]
    def batches(self,o):
        return self.p.sql(o,"SELECT COUNT(*) FROM snapshots WHERE kind='batch'")[0][0]
    def mixed_events(self,o,sid='Q'):
        return self.p.sql(o,"SELECT id,payload FROM accounting_events WHERE item_key=? AND code=?",(self.p.K(sid),MIXED))
    def retired(self,order):
        """Q with its receipt, replaced in open December by Z, which is then approved."""
        p=self.p;o=self.quiet(p.base)
        q_rows=[p.q(None,**({} if order is None else {'as_of':order})),p.rc('Q','2026-12-03','40.00')]
        self.send(o,'uc21-q',q_rows)
        z_rows=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')]
        self.send(o,'uc21-z',z_rows+[p.stmt(z_rows,p.DEC,opening='100.00')]);self.quiet(p.prep,o)
        artifact=self.quiet(p.clear_and_approve,o,'Z')
        self.assertTrue(artifact['eligible'],artifact['blockers']);self.assertTrue(p.approved(o,p.K('Z'),'2026-12'))
        self.assertEqual(p.head(o,'Q')['removed'],1)
        return o,q_rows
    def governed(self,order=7):
        """Q governed by a sequence number or timestamp, prepared in open December."""
        p=self.p;o=self.quiet(p.base);self.send(o,'uc22-q',p.q_rows(as_of=order));self.quiet(p.prep,o)
        return o

    # ---------------------------------------------------------------- UC-21
    def test_UC21_identical_repeat_of_a_row_retired_by_a_live_replacement_changes_nothing(self):
        p=self.p
        for order in ORDERS:
            for label,pick in (('row and receipt',lambda rows:rows),('row only',lambda rows:rows[:1]),('receipt only',lambda rows:rows[1:])):
                with self.subTest(order=order,repeat=label):
                    o,q_rows=self.retired(order)
                    before=p.rows_of(o);head=p.head(o,'Q');generation=o.state(p.PREP)['generation'];delivered=self.batches(o)
                    for attempt in range(2):
                        result=self.send(o,'uc21-again-%d'%attempt,pick(q_rows))
                        self.assertIs(result['changed'],False);self.assertIs(result['replay'],False)
                    self.assertEqual(p.rows_of(o),before)
                    self.assertEqual(p.head(o,'Q'),head)
                    self.assertEqual(o.state(p.PREP)['generation'],generation)
                    # Each new batch still keeps its own delivery record (clause 5).
                    self.assertEqual(self.batches(o),delivered+2)
                    self.quiet(p.prep,o)
                    self.assertIsNone(p.gov(o,p.K('Q'),'2026-12'))
                    self.assertTrue(p.approved(o,p.K('Z'),'2026-12'))
                    self.assertTrue(o.verify_audit(p.PREP))

    def test_UC21_repeat_through_a_chain_of_replacements_changes_nothing(self):
        p=self.p;o,q_rows=self.retired(7)
        y_rows=[p.sup('Y','2026-12-06','40.00','Z'),p.rc('Y','2026-12-06','40.00')]
        self.send(o,'uc21-y',y_rows+[p.stmt(y_rows,p.DEC,opening='100.00')]);self.quiet(p.prep,o)
        self.assertEqual((p.head(o,'Q')['removed'],p.head(o,'Z')['removed'],p.head(o,'Y')['removed']),(1,1,0))
        before=p.rows_of(o)
        self.assertIs(self.send(o,'uc21-q-again',q_rows)['changed'],False)
        z_rows=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')]
        self.assertIs(self.send(o,'uc21-z-again',z_rows)['changed'],False)
        self.assertEqual(p.rows_of(o),before)

    def test_UC21_boundary_a_newer_order_value_or_different_data_is_still_recorded(self):
        p=self.p
        # The provider reasserts the charge with a newer sequence number: a real message, kept as before.
        o,q_rows=self.retired(7);before=p.rows_of(o)
        newer=self.send(o,'uc21-newer',[p.q(None,as_of=8)])
        self.assertIs(newer['changed'],True)
        self.assertEqual(len(p.rows_of(o)['source_snapshots']),len(before['source_snapshots'])+1)
        self.quiet(p.prep,o)
        self.assertIsNone(p.gov(o,p.K('Q'),'2026-12'));self.assertEqual(p.head(o,'Q')['removed'],1)
        # Same order value with different data is a conflicting message: kept as evidence, never governing.
        o,q_rows=self.retired(7);before=p.rows_of(o);head=p.head(o,'Q')
        conflicting=self.send(o,'uc21-conflict',[p.q(None,amount='41.00',as_of=7)])
        self.assertIs(conflicting['changed'],False)
        self.assertEqual(len(p.rows_of(o)['source_snapshots']),len(before['source_snapshots'])+1)
        self.assertEqual(p.head(o,'Q'),head)

    def test_UC21_boundary_restoration_cases_keep_their_earlier_behaviour(self):
        p=self.p
        # The provider withdrew the replacement: re-sending Q is the open restoration question (U4), not a repeat.
        o,q_rows=self.retired(7)
        self.assertIs(self.send(o,'uc21-z-withdrawn',[dict(p.tx('Z','2026-12-05','40.00'),tombstone=True,removal_reason='voided')])['changed'],True)
        self.assertEqual(p.head(o,'Z')['removed'],1)
        before=p.rows_of(o)
        self.assertIs(self.send(o,'uc21-q-after-withdrawal',q_rows)['changed'],True)
        self.assertEqual(len(p.rows_of(o)['source_snapshots']),len(before['source_snapshots'])+2)
        self.assertEqual(p.head(o,'Q')['removed'],0)
        # The provider withdrew Q itself: its identical earlier message is not a repeat of a retired row.
        o=self.quiet(p.base);rows=[p.q(None,as_of=7),p.rc('Q','2026-12-03','40.00')];self.send(o,'uc21-q7',rows)
        self.assertIs(self.send(o,'uc21-q-withdrawn',[dict(p.q(None,as_of=8),tombstone=True,removal_reason='feed_removed')])['changed'],True)
        self.assertEqual(p.head(o,'Q')['removed'],1)
        with o.store.connect() as db:self.assertFalse(o.retired_by_live_replacement(db,p.SCOPE,p.K('Q')))

    def test_UC21_boundary_a_resend_that_omits_the_rows_claim_is_a_later_omission_not_a_repeat(self):
        p=self.p;o=self.quiet(p.base)
        # Y claims X before X arrives, then Z replaces Y: Y is retired while its claim waits.
        self.send(o,'uc21-y',[p.sup('Y','2026-12-03','40.00','X'),p.rc('Y','2026-12-03','40.00')])
        self.send(o,'uc21-z',[p.sup('Z','2026-12-04','40.00','Y'),p.rc('Z','2026-12-04','40.00')])
        self.assertEqual(p.head(o,'Y')['removed'],1)
        # The identical message, claim included, is a repeat.
        before=p.rows_of(o)
        self.assertIs(self.send(o,'uc21-y-again',[p.sup('Y','2026-12-03','40.00','X'),p.rc('Y','2026-12-03','40.00')])['changed'],False)
        self.assertEqual(p.rows_of(o),before)
        # The same row without its claim is not that message: it is recorded as before, and the claim survives (clause 6).
        self.assertIs(self.send(o,'uc21-y-without-claim',[p.tx('Y','2026-12-03','40.00'),p.rc('Y','2026-12-03','40.00')])['changed'],True)
        self.assertGreater(len(p.rows_of(o)['source_snapshots']),len(before['source_snapshots']))
        self.send(o,'uc21-x',[p.sup('X','2026-12-02','40.00','A1'),p.rc('X','2026-12-02','40.00')])
        self.assertIn((p.K('X'),p.K('Y')),p.links(o))
        self.quiet(p.prep,o)
        self.assertTrue({p.K('Z'),'receipt-Z'}<=p.held_under(o))
        self.assertIsNone(p.gov(o,p.K('Z'),'2026-12'))
        self.assertTrue(o.verify_audit(p.PREP))

    def test_UC21_boundary_a_row_whose_live_replacement_is_held_is_still_recorded_and_held(self):
        p=self.p;o=self.quiet(p.base)
        # Newest first: Z replaces Y, Y replaces X, X replaces A1, the charge approved in locked November.
        z=[p.sup('Z','2026-12-04','40.00','Y'),p.rc('Z','2026-12-04','40.00')]
        y=[p.sup('Y','2026-12-03','40.00','X'),p.rc('Y','2026-12-03','40.00')]
        x=[p.sup('X','2026-12-02','40.00','A1'),p.rc('X','2026-12-02','40.00')]
        self.send(o,'uc21-held-z',z+[p.stmt(z,p.DEC,opening='100.00')]);self.send(o,'uc21-held-y',y);self.send(o,'uc21-held-x',x)
        self.quiet(p.prep,o)
        self.assertEqual(p.head(o,'Y')['removed'],1)
        self.assertTrue({p.K('X'),p.K('Z')}<=p.held_under(o));self.assertNotIn(p.K('Y'),p.held_under(o))
        # Z is live but held under November, so Y's identical re-send is not a no-op: Y takes the hold with its chain.
        before=p.rows_of(o)
        self.assertIs(self.send(o,'uc21-held-y-again',[y[0]])['changed'],True)
        self.assertGreater(len(p.rows_of(o)['source_snapshots']),len(before['source_snapshots']))
        self.quiet(p.prep,o)
        self.assertTrue({p.K('X'),p.K('Y'),p.K('Z')}<=p.held_under(o))
        self.assertIsNone(p.gov(o,p.K('Z'),'2026-12'));self.assertTrue(p.approved(o,p.K('A1'),'2026-11'))
        self.assertTrue(o.verify_audit(p.PREP))

    def test_UC21_a_first_claim_on_the_repeated_message_is_still_recorded_and_applied(self):
        p=self.p;o,q_rows=self.retired(7)
        self.send(o,'uc21-p',p.p_rows())
        result=self.send(o,'uc21-q-claims-p',[p.q('P',as_of=7)])
        self.assertIs(result['changed'],True)
        self.assertEqual([event for event in p.claim_events(o,'Q') if event[0]=='SOURCE_CLAIM_DECLARED'],[('SOURCE_CLAIM_DECLARED',p.K('P'))])
        self.assertIn((p.K('P'),p.K('Q')),p.links(o))
        snapshot=p.rows_of(o)
        self.assertIs(self.send(o,'uc21-q-claims-p-again',[p.q('P',as_of=7)])['changed'],False)
        self.assertEqual(p.rows_of(o),snapshot)
        self.assertTrue(o.verify_audit(p.PREP))

    # ---------------------------------------------------------------- UC-22
    def test_UC22_unordered_message_with_different_data_is_kept_once_and_flagged_once(self):
        p=self.p
        for order in ORDERS[:2]:
            with self.subTest(governing_order=order):
                o=self.governed(order);head=p.head(o,'Q');before=p.rows_of(o);generation=o.state(p.PREP)['generation']
                first=self.send(o,'uc22-plain-0',[p.q(amount='41.00')]);after=p.rows_of(o)
                self.assertIs(first['changed'],False)
                self.assertEqual(len(after['source_snapshots']),len(before['source_snapshots'])+1)
                self.assertEqual(len(after['events']),len(before['events'])+1)
                self.assertEqual(len(self.mixed_events(o)),1)
                for attempt in (1,2,3):
                    self.assertIs(self.send(o,'uc22-plain-%d'%attempt,[p.q(amount='41.00')])['changed'],False)
                self.assertEqual(p.rows_of(o),after)
                self.assertEqual(p.head(o,'Q'),head)
                self.assertEqual(o.state(p.PREP)['generation'],generation)
                self.assertTrue(o.verify_audit(p.PREP))

    def test_UC22_each_distinct_unordered_message_is_kept_and_flagged_once(self):
        p=self.p;o=self.governed();before=p.rows_of(o)
        for amount in ('41.00','42.00','41.00','42.00','43.00'):
            self.send(o,'uc22-'+amount+'-'+str(self.batches(o)),[p.q(amount=amount)])
        after=p.rows_of(o)
        self.assertEqual(len(after['source_snapshots']),len(before['source_snapshots'])+3)
        self.assertEqual(len(self.mixed_events(o)),3)
        anomalies=o.state(p.PREP)['feed_anomalies']
        self.assertEqual(len({a['message_snapshot_id'] for a in anomalies}),3)

    def test_UC22_anomaly_is_visible_in_state_and_export_and_the_message_never_governs(self):
        p=self.p;o=self.governed();head=p.head(o,'Q')
        self.assertEqual(o.state(p.PREP)['feed_anomalies'],[])
        artifact=p.gov(o,p.K('Q'),'2026-12')
        self.quiet(p.review,o,p.REV2,artifact,'approve');self.assertTrue(p.approved(o,p.K('Q'),'2026-12'))
        approved_hash=p.gov(o,p.K('Q'),'2026-12')['hash']
        self.send(o,'uc22-plain',[p.q(amount='41.00')])
        for view in (o.state(p.PREP),o.export(p.PREP)):
            anomalies=view['feed_anomalies']
            self.assertEqual(len(anomalies),1)
            self.assertEqual((anomalies[0]['source_key'],anomalies[0]['reason'],anomalies[0]['period_id'],anomalies[0]['governing_order_type']),(p.K('Q'),MIXED,'2026-12','sequence'))
            self.assertEqual(anomalies[0]['governing_snapshot_id'],head['snapshot_id'])
            self.assertNotEqual(anomalies[0]['message_snapshot_id'],head['snapshot_id'])
            self.assertIn(MIXED,[event['code'] for event in view['accounting_events']])
        # The governing row, its approval and the held population are untouched by the anomaly.
        self.assertEqual(p.head(o,'Q'),head)
        self.assertFalse(any(e['source_key']==p.K('Q') for e in o.state(p.PREP)['source_exceptions']))
        self.quiet(p.prep,o)
        self.assertEqual(p.gov(o,p.K('Q'),'2026-12')['hash'],approved_hash)
        self.assertTrue(p.approved(o,p.K('Q'),'2026-12'))
        page=(ROOT/'accounting_agent/web/app.js').read_text()
        self.assertIn('state.feed_anomalies',page)

    def test_UC22_claim_on_an_unordered_message_applies_once_and_its_repeat_adds_nothing(self):
        p=self.p;o=self.governed();head=p.head(o,'Q')
        self.send(o,'uc22-p',p.p_rows());self.send(o,'uc22-plain',[p.q(amount='41.00')])
        result=self.send(o,'uc22-claim',[p.q('P',amount='41.00')])
        self.assertIs(result['changed'],True)
        self.assertEqual([event for event in p.claim_events(o,'Q') if event[0]=='SOURCE_CLAIM_DECLARED'],[('SOURCE_CLAIM_DECLARED',p.K('P'))])
        self.assertEqual(p.head(o,'Q')['snapshot_id'],head['snapshot_id'])
        self.assertIn((p.K('P'),p.K('Q')),p.links(o))
        self.assertTrue({p.K('Q'),'receipt-Q'}<=p.held_under(o))
        snapshot=p.rows_of(o)
        for attempt in (1,2):
            self.assertIs(self.send(o,'uc22-claim-again-%d'%attempt,[p.q('P',amount='41.00')])['changed'],False)
        self.assertEqual(p.rows_of(o),snapshot)
        self.quiet(p.prep,o)
        self.assertIsNone(p.gov(o,p.K('Q'),'2026-12'));self.assertFalse(p.approved(o,p.K('Q'),'2026-12'))
        self.assertTrue(o.verify_audit(p.PREP))

    def test_UC22_messages_that_are_not_mixed_ordering_raise_no_anomaly(self):
        p=self.p
        # Same data without an order value: an ordinary repeat.
        o=self.governed();before=p.rows_of(o)
        self.assertIs(self.send(o,'uc22-same',[p.q()])['changed'],False)
        self.assertEqual(p.rows_of(o),before);self.assertEqual(self.mixed_events(o),[])
        # An older ordered message: retained under clause 1, not an ordering anomaly.
        self.send(o,'uc22-older',[p.q(amount='41.00',as_of=6)])
        self.assertEqual(self.mixed_events(o),[]);self.assertEqual(o.state(p.PREP)['feed_anomalies'],[])
        # A row that has never carried an order value: arrival order governs as before.
        o=self.quiet(p.base);self.send(o,'uc22-legacy',p.q_rows());self.quiet(p.prep,o)
        revised=self.send(o,'uc22-legacy-revised',[p.q(amount='41.00')])
        self.assertIs(revised['changed'],True)
        self.assertEqual(p.head(o,'Q')['amount'],'41.00')
        self.assertEqual(self.mixed_events(o),[]);self.assertEqual(o.state(p.PREP)['feed_anomalies'],[])
