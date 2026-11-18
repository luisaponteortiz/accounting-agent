"""RD claim persistence regressions; fictional service operations and read-only history checks."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TRANSITION = 'SOURCE_TRANSITION_REQUIRES_REVIEW'
UNRESOLVED = 'SOURCE_TRANSITION_UNRESOLVED'


class ReviewCorrectionsRD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT/'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py'
        spec = importlib.util.spec_from_file_location('rd_fixtures', path)
        cls.f = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'argv', [str(path), str(ROOT)]):
            spec.loader.exec_module(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.TMP.cleanup()

    def prepare(self, os_):
        self.f.run(os_, 'card_preparation', '2026-12', self.f.PREP2)

    def held(self, os_, *keys):
        f = self.f
        state = os_.export(f.PREP)
        held = {e['source_key'] for e in state['source_exceptions']
                if e['period_id'] == '2026-11' and e['reason'] == 'SOURCE_MOVED_FROM_LOCKED_PERIOD'}
        self.assertTrue(set(keys) <= held, (keys, held))
        for key in keys:
            if key.startswith(f.CARD+':'):
                self.assertIsNone(f.gov(os_, key, '2026-12'))
        self.assertTrue(os_.verify_audit(f.PREP))
        return state

    def lifecycle(self, os_):
        # Batch envelopes have their own immutable intake record. Compare the
        # claimed source's snapshots and all lifecycle tables, not new envelopes.
        with os_.store.connect() as db:
            return {t: [tuple(r) for r in db.execute(sql)] for t, sql in {
                'sources': "SELECT * FROM snapshots WHERE kind!='batch' ORDER BY id",
                'bindings': 'SELECT * FROM source_periods ORDER BY id',
                'moves': 'SELECT * FROM source_moves ORDER BY id',
                'links': 'SELECT * FROM source_links ORDER BY id',
                'events': 'SELECT * FROM accounting_events ORDER BY id',
                'decisions': 'SELECT * FROM decisions ORDER BY id',
            }.items()}

    def test_RD01_unchanged_late_claim_blocks_eligible_and_approved_before_target(self):
        f = self.f
        for approved in (False, True):
            with self.subTest(approved=approved):
                o = f.approved_locked_november()
                rows = [f.tx('Y', '2026-12-03', '40.00'), f.rc('Y', '2026-12-03', '40.00')]
                o.intake(f.PREP2, f.packet('plain', rows+[f.stmt(rows, f.DEC, opening='100.00')]))
                self.prepare(o)
                prior = f.gov(o, f.CARD+':Y', '2026-12')
                self.assertTrue(prior['eligible'])
                if approved:
                    self.assertEqual(f.review(o, f.REV2, prior, 'approve')[0], 'ok')
                before = self.lifecycle(o)
                result = o.intake(f.PREP2, f.packet('claim', [f.sup('Y', '2026-12-03', '40.00', 'X')]))
                self.assertTrue(result['changed'])
                self.prepare(o)
                y = f.gov(o, f.CARD+':Y', '2026-12')
                self.assertTrue({TRANSITION, UNRESOLVED} <= set(y['blockers']))
                self.assertFalse(y['eligible'])
                self.assertNotEqual(y['review_status'], 'approve')
                after = self.lifecycle(o)
                self.assertEqual(len(after['sources']), len(before['sources'])+1)
                unresolved = [e for e in o.export(f.PREP)['accounting_events']
                              if e['code'] == 'SOURCE_SUPERSESSION_UNRESOLVED' and e['item_key'] == f.CARD+':Y']
                self.assertEqual(len(unresolved), 1)
                o.intake(f.PREP2, f.packet('target', [f.sup('X', '2026-12-02', '40.00', 'A1'), f.rc('X', '2026-12-02', '40.00')]))
                self.prepare(o)
                state = self.held(o, f.CARD+':Y', 'receipt-Y')
                self.assertIsNotNone(f.gov(o, f.CARD+':A1', '2026-11'))
                if approved:
                    self.assertTrue(any(e['code'].startswith('APPROVED_SOURCE_') and json.loads(e['payload'])['artifact_id'] == prior['id']
                                        for e in state['accounting_events']))
                    self.assertTrue(any(e['code'] == 'ITEM_LEFT_POPULATION' and e['item_key'] == f.CARD+':Y'
                                        for e in state['accounting_events']))
                    with o.store.connect() as db:
                        self.assertEqual(db.execute("SELECT COUNT(*) FROM decisions WHERE artifact_id=? AND decision='approve'", (prior['id'],)).fetchone()[0], 1)
                self.assertEqual(after['decisions'], self.lifecycle(o)['decisions'])

    def test_RD01_repeated_unresolved_claim_is_a_lifecycle_noop(self):
        f = self.f
        o = f.approved_locked_november()
        o.intake(f.PREP2, f.packet('plain', [f.tx('Y', '2026-12-03', '40.00')]))
        claim = f.packet('claim', [f.sup('Y', '2026-12-03', '40.00', 'X')])
        self.assertTrue(o.intake(f.PREP2, claim)['changed'])
        before = self.lifecycle(o)
        for name in ('repeat-1', 'repeat-2'):
            result = o.intake(f.PREP2, dict(claim, batch_id=name))
            self.assertFalse(result['changed'])
            self.assertEqual(before, self.lifecycle(o))
        with o.store.connect() as db:
            n = db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0]
        self.assertTrue(o.intake(f.PREP2, claim)['replay'])
        with o.store.connect() as db:
            self.assertEqual(n, db.execute('SELECT COUNT(*) FROM snapshots').fetchone()[0])
        self.assertEqual(before, self.lifecycle(o))

    def test_RD02_amount_revision_keeps_claim_with_or_without_repeat_and_restart(self):
        f = self.f
        for repeat in (False, True):
            with self.subTest(claim_repeated=repeat):
                o = f.approved_locked_november()
                rows = [f.sup('Y', '2026-12-03', '40.00', 'X'), f.rc('Y', '2026-12-03', '40.00')]
                o.intake(f.PREP2, f.packet('claim', rows+[f.stmt(rows, f.DEC, opening='100.00')]))
                revision = f.sup('Y', '2026-12-03', '41.00', 'X') if repeat else f.tx('Y', '2026-12-03', '41.00')
                o.intake(f.PREP2, f.packet('revision', [revision, f.rc('Y', '2026-12-03', '41.00')]))
                self.prepare(o)
                self.assertTrue({TRANSITION, UNRESOLVED} <= set(f.gov(o, f.CARD+':Y', '2026-12')['blockers']))
                # A fresh service instance must use persisted claims, not memory.
                o = type(o)(o.store.path, o.allowed_scopes)
                o.intake(f.PREP2, f.packet('target', [f.sup('X', '2026-12-02', '40.00', 'A1'), f.rc('X', '2026-12-02', '40.00')]))
                self.prepare(o)
                self.held(o, f.CARD+':Y', 'receipt-Y')
                with o.store.connect() as db:
                    head = db.execute('SELECT snapshot_id FROM source_heads WHERE source_key=?', (f.CARD+':Y',)).fetchone()[0]
                    self.assertEqual(o.supersession_link(db, f.SCOPE, head)['new_snapshot_id'], head)

    def test_RD02_retired_claimant_resent_unchanged_without_claim(self):
        f = self.f
        for order in (('claim', 'terminal'), ('terminal', 'claim')):
            with self.subTest(order=order):
                o = f.approved_locked_november()
                deliveries = {
                    'claim': [f.sup('Y', '2026-12-03', '40.00', 'X'), f.rc('Y', '2026-12-03', '40.00')],
                    'terminal': [f.sup('Z', '2026-12-04', '40.00', 'Y'), f.rc('Z', '2026-12-04', '40.00')],
                }
                for name in order:
                    o.intake(f.PREP2, f.packet(name, deliveries[name]))
                with o.store.connect() as db:
                    self.assertEqual(db.execute('SELECT removed FROM source_heads WHERE source_key=?', (f.CARD+':Y',)).fetchone()[0], 1)
                self.assertTrue(o.intake(f.PREP2, f.packet('resend', [f.tx('Y', '2026-12-03', '40.00'), f.rc('Y', '2026-12-03', '40.00')]))['changed'])
                with o.store.connect() as db:
                    ctx = o.context(db, f.PREP2, '2026-12', 'card_preparation')
                # Rebinding the live terminal can retire Y again immediately.
                # Any Y version still in the population must retain its hold.
                if any(s['source_key'] == f.CARD+':Y' for s in ctx['sources']):
                    self.assertIn(f.CARD+':Y', ctx['unresolved_transitions'])
                o.intake(f.PREP2, f.packet('target', [f.sup('X', '2026-12-02', '40.00', 'A1'), f.rc('X', '2026-12-02', '40.00')]))
                self.prepare(o)
                self.held(o, f.CARD+':Z', 'receipt-Z')
                with o.store.connect() as db:
                    head = db.execute('SELECT snapshot_id FROM source_heads WHERE source_key=?', (f.CARD+':Y',)).fetchone()[0]
                    self.assertIsNotNone(o.supersession_link(db, f.SCOPE, head))

    def test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced(self):
        # D-026 supersedes the old method name's latest-target rule.
        f = self.f
        o = f.approved_locked_november()
        o.intake(f.PREP2, f.packet('first', [f.sup('Y', '2026-12-03', '40.00', 'X')]))
        o.intake(f.PREP2, f.packet('new-target', [f.sup('Y', '2026-12-03', '41.00', 'W')]))
        o.intake(f.PREP2, f.packet('old-target-arrives', [f.tx('X', '2026-12-02', '40.00')]))
        with o.store.connect() as db:
            head = db.execute('SELECT snapshot_id FROM source_heads WHERE source_key=?', (f.CARD+':Y',)).fetchone()[0]
            link = o.supersession_link(db, f.SCOPE, head)
            self.assertIsNotNone(link)
            self.assertEqual(o.card_claim_state(db, f.SCOPE, f.CARD+':Y')['target_key'], f.CARD+':X')
        o.intake(f.PREP2, f.packet('new-target-arrives', [f.sup('W', '2026-12-02', '40.00', 'A1')]))
        f.run(o, 'card_preparation', '2026-12', f.PREP2)
        y = f.gov(o, f.CARD+':Y', '2026-12')
        self.assertIsNotNone(y)
        self.assertIn('SOURCE_CLAIM_CONFLICT', y['blockers'])
        self.assertFalse(y['eligible'])
        before = self.lifecycle(o)
        o.intake(f.PREP2, f.packet('unrelated', [f.tx('D1', '2026-12-05', '15.00')]))
        after = self.lifecycle(o)
        for table in ('links', 'moves', 'events'):
            self.assertEqual(before[table], after[table])
