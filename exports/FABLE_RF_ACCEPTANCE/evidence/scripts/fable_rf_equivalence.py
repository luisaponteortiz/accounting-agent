"""Fable RF-03 equivalence check.

usage: fable_rf_equivalence.py <project-root> <script> [script args...]

Runs <script> (a probe or search script that takes <project-root> as its first argument) unchanged, with one
read-only wrapper around PackageControls.period_outcomes: every time the application computes the period
outcomes, the result of the delivered code (which may reuse a run's currentness inside a transaction) is
compared with the result of the full computation (every artifact asks _current again) on the same
connection, at the same moment. Any difference is printed and counted. It also counts how often _current
ran in each mode, so the report shows that the shortcut was actually exercised, and how many calls were made
outside a transaction (where the delivered code must not reuse anything).
Nothing is written; the wrapped call returns the delivered result.
"""
import json, runpy, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); script = sys.argv[2]
sys.path.insert(0, str(root))
import accounting_agent.packages as pk
from accounting_agent.core import canonical
from accounting_agent.service import AccountingOS
orig = pk.PackageControls.period_outcomes
shortcut = pk.PackageControls.outcome_run_current
real_current = AccountingOS._current
S = {'calls_in_transaction': 0, 'calls_autocommit': 0, 'mismatches': 0, 'current_evaluations_delivered': 0, 'current_evaluations_full': 0,
     'calls_where_shortcut_saved_work': 0, 'autocommit_calls_that_reused': 0}
mode = [None]
def counting_current(self, db, actor, run):
    if mode[0] == 'fast': S['current_evaluations_delivered'] += 1
    elif mode[0] == 'full': S['current_evaluations_full'] += 1
    return real_current(self, db, actor, run)
AccountingOS._current = counting_current
def checked(self, db, actor, period_id):
    if mode[0] is not None:            # nested call from context(); leave it alone
        return orig(self, db, actor, period_id)
    in_tx = bool(db.in_transaction)
    a0 = S['current_evaluations_delivered']
    mode[0] = 'fast'
    try: fast = orig(self, db, actor, period_id)
    finally: mode[0] = None
    used = S['current_evaluations_delivered'] - a0
    b0 = S['current_evaluations_full']
    pk.PackageControls.outcome_run_current = lambda s, d, a, run, cache: s._current(d, a, run)
    mode[0] = 'full'
    try: full = orig(self, db, actor, period_id)
    finally:
        mode[0] = None; pk.PackageControls.outcome_run_current = shortcut
    needed = S['current_evaluations_full'] - b0
    S['calls_in_transaction' if in_tx else 'calls_autocommit'] += 1
    if canonical(fast) != canonical(full):
        S['mismatches'] += 1
        print('RF-03 MISMATCH period=%s in_transaction=%s' % (period_id, in_tx), flush=True)
    if used < needed:
        S['calls_where_shortcut_saved_work'] += 1
        if not in_tx: S['autocommit_calls_that_reused'] += 1
    return fast
pk.PackageControls.period_outcomes = checked
sys.argv = [script, str(root)] + sys.argv[3:]
code = 0
try:
    runpy.run_path(script, run_name='__main__')
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
print('\nRF-03 EQUIVALENCE ' + json.dumps(S) + ' wrapped_script_exit=%s' % code)
sys.exit(1 if S['mismatches'] or S['autocommit_calls_that_reused'] else code)
