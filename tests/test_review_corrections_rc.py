"""RC arrival-order regressions; disposable fiction, service mutations only."""
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ReviewCorrectionsRC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT/'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py'
        spec = importlib.util.spec_from_file_location('rc_fixtures', path)
        cls.f = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'argv', [str(path), str(ROOT)]):
            spec.loader.exec_module(cls.f)

    @classmethod
    def tearDownClass(cls):
        cls.f.TMP.cleanup()

    def held(self, os_, *keys):
        f = self.f
        state = os_.export(f.PREP)
        held = {e['source_key'] for e in state['source_exceptions']
                if e['period_id'] == '2026-11' and e['reason'] == 'SOURCE_MOVED_FROM_LOCKED_PERIOD'}
        self.assertTrue(set(keys) <= held, (keys, held))
        for key in keys:
            if key.startswith(f.CARD+':'):
                self.assertIsNone(f.gov(os_, key, '2026-12'))
        return state

    def released(self, os_, terminal):
        f = self.f
        os_.reopen_period(f.PADMIN, '2026-11', 'Fictional RC release')
        f.run(os_, 'card_preparation')
        f.run(os_, 'card_preparation', '2026-12', f.PREP2)
        self.assertIsNone(f.gov(os_, f.CARD+':A1'))
        keys = [a['item_key'] for a in f.arts(os_, None, '2026-12')
                if a['governing'] and a['kind'] == 'card_proposal']
        self.assertEqual(keys, [f.CARD+':'+terminal])
        self.assertIn('SOURCE_TRANSITION_REQUIRES_REVIEW', f.gov(os_, keys[0], '2026-12')['blockers'])

    def test_RC01_withdrawal_then_fresh_or_late_claim_and_relock(self):
        f = self.f
        for late in (True, False):
            with self.subTest(late_claim=late):
                o = f.approved_locked_november()
                plain = [f.tx('B1', '2026-12-02', '40.00'), f.rc('B1', '2026-12-02', '40.00')]
                if late:
                    o.intake(f.PREP2, f.packet('plain', plain+[f.stmt(plain, f.DEC, opening='100.00')]))
                gone = dict(f.tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')
                o.intake(f.PREP2, f.packet('withdraw', [gone]))
                self.assertTrue(any(e['source_key'] == f.CARD+':A1' and e['reason'] == 'LATE_ACTIVITY_IN_LOCKED_PERIOD'
                                    for e in o.state(f.PREP)['source_exceptions']))
                claim = [f.sup('B1', '2026-12-02', '40.00', 'A1')]
                if not late:
                    claim += [plain[1], f.stmt(plain, f.DEC, opening='100.00')]
                o.intake(f.PREP2, f.packet('claim', claim))
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                state = self.held(o, f.CARD+':B1', 'receipt-B1')
                self.assertTrue(any(m['blocked'] and m['had_approval'] for m in state['source_move_history']))
                self.released(o, 'B1')
                o.lock_period(f.PADMIN, '2026-11', 'Fictional relock', 'Known unsettled items')
                o.intake(f.PREP2, f.packet('revision', [f.sup('B1', '2026-12-02', '42.00', 'A1')]))
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                self.assertIsNotNone(f.gov(o, f.CARD+':B1', '2026-12'))
                self.assertTrue(o.verify_audit(f.PREP))

    def test_RC02_middle_late_link_rechecks_eligible_and_approved_terminal(self):
        f = self.f
        for approved in (False, True):
            with self.subTest(terminal_approved=approved):
                o = f.approved_locked_november()
                b = [f.tx('B1', '2026-12-02', '40.00'), f.rc('B1', '2026-12-02', '40.00')]
                c = [f.sup('C1', '2026-12-03', '40.00', 'B1'), f.rc('C1', '2026-12-03', '40.00')]
                o.intake(f.PREP2, f.packet('middle', b+[f.stmt(c, f.DEC, opening='100.00')]))
                o.intake(f.PREP2, f.packet('terminal', c))
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                self.assertEqual(f.dispose(o, f.CARD+':C1', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', period='2026-12')[0], 'ok')
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                self.assertTrue(f.gov(o, f.CARD+':C1', '2026-12')['eligible'])
                if approved:
                    self.assertEqual(f.review(o, f.REV2, f.gov(o, f.CARD+':C1', '2026-12'), 'approve')[0], 'ok')
                o.intake(f.PREP2, f.packet('late', [f.sup('B1', '2026-12-02', '40.00', 'A1')]))
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                state = self.held(o, f.CARD+':B1', f.CARD+':C1', 'receipt-C1')
                if approved:
                    self.assertTrue(any(e['item_key'] == f.CARD+':C1' and e['code'].startswith('APPROVED_SOURCE_')
                                        for e in state['accounting_events']))
                self.released(o, 'C1')

    def test_RC02_unchanged_chain_adds_no_bindings_moves_or_accounting_events(self):
        f = self.f
        o = f.new_os(periods=(f.NOV, f.DEC))
        f.clean_november(o)
        o.intake(f.PREP2, f.packet('replacement', [f.sup('B1', '2026-12-02', '40.00', 'A1')]))
        before = o.export(f.PREP)
        o.intake(f.PREP2, f.packet('unrelated', [f.tx('D1', '2026-12-05', '15.00')]))
        after = o.export(f.PREP)
        self.assertEqual(before['source_move_history'], after['source_move_history'])
        self.assertEqual(before['accounting_events'], after['accounting_events'])
        prior_ids = {s['id'] for s in before['evidence_history']}
        self.assertEqual(before['source_period_history'], [b for b in after['source_period_history'] if b['snapshot_id'] in prior_ids])

    def test_RC03_pending_claim_resolves_before_or_after_claimant_is_replaced(self):
        f = self.f
        for replaced_first in (False, True):
            with self.subTest(replaced_first=replaced_first):
                o = f.approved_locked_november()
                y = [f.sup('Y', '2026-12-03', '40.00', 'X'), f.rc('Y', '2026-12-03', '40.00')]
                z = [f.sup('Z', '2026-12-04', '40.00', 'Y'), f.rc('Z', '2026-12-04', '40.00')]
                o.intake(f.PREP2, f.packet('claimant', y+[f.stmt(z, f.DEC, opening='100.00')]))
                if replaced_first:
                    o.intake(f.PREP2, f.packet('terminal', z))
                o.intake(f.PREP2, f.packet('target', [f.sup('X', '2026-12-02', '40.00', 'A1'), f.rc('X', '2026-12-02', '40.00')]))
                if not replaced_first:
                    f.run(o, 'card_preparation', '2026-12', f.PREP2)
                    self.held(o, f.CARD+':Y')
                    o.intake(f.PREP2, f.packet('terminal', z))
                f.run(o, 'card_preparation', '2026-12', f.PREP2)
                self.held(o, f.CARD+':X', f.CARD+':Z', 'receipt-Z')
                self.released(o, 'Z')

    def test_RC03_open_target_clears_unresolved_without_quarantine(self):
        f = self.f
        o = f.new_os(periods=(f.NOV, f.DEC))
        f.clean_november(o)
        o.intake(f.PREP2, f.packet('claim', [f.sup('Y', '2026-12-03', '40.00', 'X')]))
        o.intake(f.PREP2, f.packet('target', [f.tx('X', '2026-12-02', '40.00')]))
        with o.store.connect() as db:
            ctx = o.context(db, f.PREP2, '2026-12', 'card_preparation')
        self.assertEqual(ctx['unresolved_transitions'], {})
        self.assertEqual(o.export(f.PREP)['source_move_history'], [])

    def test_RC03_pending_cycle_is_not_linked(self):
        f = self.f
        o = f.new_os(periods=(f.NOV, f.DEC))
        f.clean_november(o)
        o.intake(f.PREP2, f.packet('y', [f.sup('Y', '2026-12-03', '40.00', 'X')]))
        o.intake(f.PREP2, f.packet('x', [f.sup('X', '2026-12-02', '40.00', 'Y')]))
        with o.store.connect() as db:
            y = db.execute('SELECT snapshot_id FROM source_heads WHERE scope=? AND source_key=?', (f.SCOPE, f.CARD+':Y')).fetchone()
            self.assertIsNone(o.supersession_link(db, f.SCOPE, y['snapshot_id']))
        self.assertTrue(o.verify_audit(f.PREP))
