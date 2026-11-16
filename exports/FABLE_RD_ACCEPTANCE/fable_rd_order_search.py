"""Fable extended arrival-order search for the RB-01 invariant after RD-01/RD-02 (Accounting Agent OS).

Usage:
    python3 fable_rd_order_search.py <project-root> [--json out.json]

Same invariant, fixture, operator behaviour and failure rule as fable_rc_order_search.py (which stays
the gate script and is not replaced by this one). This script widens the deliveries:

    X    A1X (2 Dec) with its receipt, declaring that it supersedes A1
    Yp   A1Y (3 Dec) with its receipt, no claim
    Yc   A1Y (3 Dec), the same bytes, declaring that it supersedes A1X
    Yr   A1Y revised to 41.00 with its receipt, no claim
    Z    A1Z (4 Dec) with its receipt, declaring that it supersedes A1Y
    V    A1 withdrawn by the feed (voided)
    B    B9 (2 Dec), an ordinary December row, with its receipt
    Yb   A1Y (3 Dec) with its receipt, declaring that it supersedes B9
    Y5   A1Y (3 Dec) with its receipt, provider sequence 5, no claim
    Y4c  A1Y (3 Dec), the same bytes, provider sequence 4, declaring that it supersedes A1X
    Yt   A1Y withdrawn by the feed (feed_removed)

Families: two of five deliveries (2 x 120 orders) deepen the gate families; four of four deliveries
(4 x 24 orders) add an identity that already has a link, provider sequence numbers, and a withdrawn
claimant. 336 runs, each in its own temporary database. The run FAILS when A1 is approved and governing
in November and A1X, A1Y or A1Z is approved and governing in December.

Public service operations only; fictional data; no network, model, posting or payment.
"""
import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
_rb_path = ROOT / 'exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py'
_spec = importlib.util.spec_from_file_location('fable_rb_probes', _rb_path)
rb = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_rb_path), str(ROOT)]
_spec.loader.exec_module(rb)
sys.argv = _argv
h = rb.h
CARD, DEC, PREP2, REV2, FIN = h.CARD, h.DEC, h.PREP2, h.REV2, h.FIN
tx, rc, stmt, sup, packet, run, gov = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov
K = rb.K
CHAIN = ('A1X', 'A1Y', 'A1Z')

DELIVERIES = {
    'X': lambda: [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')],
    'Yp': lambda: [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')],
    'Yc': lambda: [sup('A1Y', '2026-12-03', '40.00', 'A1X')],
    'Yr': lambda: [tx('A1Y', '2026-12-03', '41.00'), rc('A1Y', '2026-12-03', '41.00')],
    'Z': lambda: [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')],
    'V': lambda: [dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')],
    'B': lambda: [tx('B9', '2026-12-02', '40.00'), rc('B9', '2026-12-02', '40.00')],
    'Yb': lambda: [sup('A1Y', '2026-12-03', '40.00', 'B9'), rc('A1Y', '2026-12-03', '40.00')],
    'Y5': lambda: [tx('A1Y', '2026-12-03', '40.00', as_of=5), rc('A1Y', '2026-12-03', '40.00')],
    'Y4c': lambda: [dict(tx('A1Y', '2026-12-03', '40.00', as_of=4), supersedes=K('A1X'))],
    'Yt': lambda: [dict(tx('A1Y', '2026-12-03', '40.00'), tombstone=True, removal_reason='feed_removed')],
}
FAMILIES = [('X', 'Yp', 'Yc', 'Yr', 'Z'), ('X', 'Yp', 'Yc', 'Z', 'V'), ('X', 'B', 'Yb', 'Yc'), ('X', 'Y5', 'Y4c', 'Z'), ('X', 'Yc', 'Yt', 'Yp'), ('X', 'Yc', 'Yt', 'Z')]
OTHER = ('B9',)


def quiet(fn, *a, **k):
    try:
        return ('ok', fn(*a, **k))
    except Exception as exc:  # ControlError and anything else: recorded, never hidden
        return ('refused', type(exc).__name__ + ': ' + str(exc))


def settle(os_, key):
    """Clear every blocker that has a disposition, then ask for independent approval."""
    for _ in range(4):
        a = gov(os_, key, '2026-12')
        if a is None or a['review_status'] == 'approve':
            return
        todo = [(c, ch) for c, ch in ((rb.REVISED, 'revised_evidence_accepted'), (rb.TRANSITION, 'settlement_verified')) if c in a['blockers']]
        if not todo:
            break
        quiet(h.dispose, os_, key, todo[0][0], todo[0][1], period='2026-12')
        run(os_, 'card_preparation', '2026-12', PREP2)
    a = gov(os_, key, '2026-12')
    if a is not None and a['review_status'] != 'approve':
        quiet(os_.review, REV2, a['id'], a['hash'], a['fingerprint'], 'approve', 'Fictional search review')


def one(order):
    os_ = h.approved_locked_november()
    log = []
    for i, step in enumerate(order):
        r = quiet(os_.intake, PREP2, packet('s%d-%s' % (i, step), DELIVERIES[step]()))
        log.append(step + ('' if r[0] == 'ok' else '!'))
    run(os_, 'card_preparation', '2026-12', PREP2)
    rows = []
    for k in CHAIN + OTHER:
        a = gov(os_, K(k), '2026-12')
        if a is not None:
            rows.append(tx(k, a['payload']['data']['transaction']['date'], a['payload']['data']['transaction']['amount']))
    quiet(os_.intake, PREP2, packet('statement', [stmt(rows, DEC, opening='100.00')]))
    run(os_, 'card_preparation', '2026-12', PREP2)
    for k in CHAIN + OTHER:
        settle(os_, K(k))
    nov = rb.approved(os_, K('A1'), '2026-11')
    dec = [k for k in CHAIN if rb.approved(os_, K(k), '2026-12')]
    fin = quiet(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'search') if nov and dec else None
    held = sorted(k.split(':')[-1] for k in rb.held_under(os_) if k.startswith(CARD))
    blockers = {k: gov(os_, K(k), '2026-12')['blockers'] for k in CHAIN if gov(os_, K(k), '2026-12') is not None}
    return {'order': list(order), 'log': log, 'november_A1_approved': nov, 'december_approved': dec, 'double': bool(nov and dec),
            'december_finalized_without_acknowledgement': bool(fin and fin[0] == 'ok'), 'held_under_november': held, 'december_blockers': blockers}


def main():
    results = []
    for fam in FAMILIES:
        for order in itertools.permutations(fam):
            r = one(order); r['family'] = '+'.join(fam); results.append(r)
            print('%-12s %-16s %s dec_approved=%s held=%s blockers=%s' % (r['family'], ' '.join(r['order']), 'DOUBLE' if r['double'] else 'single', r['december_approved'], r['held_under_november'], r['december_blockers']))
    bad = [r for r in results if r['double']]
    print('\nSUMMARY runs=%d double=%d finalized_silently=%d' % (len(results), len(bad), sum(r['december_finalized_without_acknowledgement'] for r in bad)))
    for fam in FAMILIES:
        f = '+'.join(fam)
        print('  %-14s double in %d of %d orders' % (f, sum(1 for r in bad if r['family'] == f), sum(1 for r in results if r['family'] == f)))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps({'runs': len(results), 'double': len(bad), 'results': results}, indent=1))
    h.TMP.cleanup()
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
