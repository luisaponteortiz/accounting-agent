"""Fable RE delivery-order search with an approval attempt after EVERY delivery.

usage: fable_re_step_search.py <project-root> [--family NAME] [--json out.json]

Four families of five fictional deliveries that the supplied 336-order search does not contain (a claim on an
older message next to a different claim on a newer one; an older message re-sent with a claim; two different
legacy-order claims with a revision; a late November row as a claimed target). Every permutation is delivered.
After each delivery an honest operator prepares December, ties the statement, clears every blocker that has
an ordinary disposition and asks an independent reviewer to approve. No person records a target selection and
November stays locked, so under D-026:
  double   - at any step, A1 is approved in locked November while Q (or its replacement Z) is approved in
             December although Q has declared that it replaces P or L (the locked chain) AND that target is
             on file. While the target has not arrived nobody can know which charge it replaces; an approval
             of the replacement Z at such a step is counted apart (approved_before_target_known) and must
             stop governing when the target arrives, which the next step then checks.
  released - Q or its receipt was held under locked November at one step and is not held at a later step
Public service operations only; temporary SQLite; fictional data.
"""
import importlib.util, itertools, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
_p = ROOT / 'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py'
_s = importlib.util.spec_from_file_location('fable_rd_probes', _p); rdp = importlib.util.module_from_spec(_s)
_a = sys.argv; sys.argv = [str(_p), str(ROOT)]; _s.loader.exec_module(rdp); sys.argv = _a
h, rb = rdp.h, rdp.rb
PREP, PREP2, REV2, DEC = h.PREP, h.PREP2, h.REV2, h.DEC
tx, rc, stmt, sup, packet, run, gov, K = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov, rb.K


def q(target=None, amount='40.00', **kw):
    row = tx('Q', '2026-12-03', amount, **kw)
    if target:
        row['supersedes'] = K(target)
    return row


RQ = lambda amount='40.00': rc('Q', '2026-12-03', amount)
DELIVERIES = {
    'P': lambda: [sup('P', '2026-12-02', '40.00', 'A1'), rc('P', '2026-12-02', '40.00')],
    'B': lambda: [tx('B', '2026-12-02', '40.00', desc='OPEN ROW DEMO'), rc('B', '2026-12-02', '40.00', vendor='OPEN ROW DEMO')],
    'L': lambda: [tx('L', '2026-11-20', '40.00', desc='LATE NOVEMBER DEMO'), rc('L', '2026-11-20', '40.00', vendor='LATE NOVEMBER DEMO')],
    'Z': lambda: [sup('Z', '2026-12-05', '40.00', 'Q'), rc('Z', '2026-12-05', '40.00')],
    'Q7': lambda: [q(as_of=7), RQ()],
    'Q6': lambda: [q(as_of=6), RQ()],
    'Q6cP': lambda: [q('P', as_of=6), RQ()],
    'Q8cB': lambda: [q('B', as_of=8), RQ()],
    'QcB': lambda: [q('B'), RQ()],
    'QcP': lambda: [q('P'), RQ()],
    'QcL': lambda: [q('L'), RQ()],
    'Qr': lambda: [q(amount='41.00'), RQ('41.00')],
}
FAMILIES = {'older-claim+newer-claim': ('P', 'B', 'Q7', 'Q6cP', 'Q8cB'), 'older-resent-with-claim': ('P', 'Q7', 'Q6', 'Q6cP', 'Z'),
            'two-claims+revision': ('P', 'B', 'QcB', 'QcP', 'Qr'), 'late-row-target': ('L', 'B', 'QcL', 'QcB', 'Qr')}
LOCKED_TARGETS = {K('P'), K('L')}
WATCH = ('Q', 'Z', 'B', 'P')


def quiet(fn, *a, **k):
    try:
        return ('ok', fn(*a, **k))
    except Exception as exc:
        return ('refused', type(exc).__name__ + ': ' + str(exc))


def settle(os_, key):
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


def declared(os_):
    out = set()
    for e in os_.export(PREP)['accounting_events']:
        if e['item_key'] == K('Q') and e['code'] in ('SOURCE_CLAIM_DECLARED', 'SOURCE_CLAIM_CONFLICT_RECORDED', 'SOURCE_SUPERSESSION_UNRESOLVED'):
            out.add(json.loads(e['payload'])['target_key'] if isinstance(e['payload'], str) else e['payload']['target_key'])
    return out


def one(order):
    os_ = h.approved_locked_november()
    trail = []; double_at = []; early_at = []; released_at = []; was_held = set()
    for i, step in enumerate(order):
        r = quiet(os_.intake, PREP2, packet('s%d-%s' % (i, step), DELIVERIES[step]()))
        run(os_, 'card_preparation', '2026-12', PREP2)
        rows = []
        for k in WATCH:
            a = gov(os_, K(k), '2026-12')
            if a is not None:
                t = a['payload']['data']['transaction']; rows.append(tx(k, t['date'], t['amount']))
        if rows:
            quiet(os_.intake, PREP2, packet('statement-%d' % i, [stmt(rows, DEC, opening='100.00')]))
            run(os_, 'card_preparation', '2026-12', PREP2)
        for k in WATCH:
            settle(os_, K(k))
        nov = rb.approved(os_, K('A1'), '2026-11')
        dec = [k for k in ('Q', 'Z') if rb.approved(os_, K(k), '2026-12')]
        held = {k for k in rb.held_under(os_) if k in (K('Q'), 'receipt-Q')}
        claims = declared(os_)
        on_file = {s['source_key'] for s in os_.export(PREP)['evidence_history']}
        if nov and dec and claims & LOCKED_TARGETS & on_file:
            double_at.append(i)
        elif nov and dec and claims & LOCKED_TARGETS:
            early_at.append(i)
        if was_held - held:
            released_at.append((i, sorted(was_held - held)))
        was_held |= held
        trail.append({'step': step, 'intake': r[0], 'december_approved': dec, 'held': sorted(held), 'declared': sorted(c.split(':')[-1] for c in claims)})
    a = gov(os_, K('Q'), '2026-12')
    return {'order': list(order), 'double_at_steps': double_at, 'approved_before_target_known_at_steps': early_at, 'released_at_steps': released_at, 'trail': trail,
            'final_Q_blockers': a['blockers'] if a else None, 'final_held': sorted(rb.held_under(os_)), 'audit_ok': bool(os_.verify_audit(PREP))}


def main():
    names = [sys.argv[sys.argv.index('--family') + 1]] if '--family' in sys.argv else list(FAMILIES)
    results = []
    for name in names:
        for order in itertools.permutations(FAMILIES[name]):
            r = one(order); r['family'] = name; results.append(r)
            print('%-24s %-22s %s %s final_Q=%s held=%s' % (name, ' '.join(order), 'DOUBLE@%s' % r['double_at_steps'] if r['double_at_steps'] else 'single',
                  'RELEASED@%s' % r['released_at_steps'] if r['released_at_steps'] else 'no-release', r['final_Q_blockers'], [k.split(':')[-1] for k in r['final_held']]), flush=True)
    bad_d = [r for r in results if r['double_at_steps']]; bad_r = [r for r in results if r['released_at_steps']]; bad_a = [r for r in results if not r['audit_ok']]
    print('\nSUMMARY runs=%d double=%d released_without_authority=%d audit_failures=%d approved_before_target_known=%d' % (len(results), len(bad_d), len(bad_r), len(bad_a), sum(1 for r in results if r['approved_before_target_known_at_steps'])))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps({'runs': len(results), 'double': len(bad_d), 'released': len(bad_r), 'results': results}, indent=1))
    h.TMP.cleanup()
    return 1 if bad_d or bad_r or bad_a else 0


if __name__ == '__main__':
    sys.exit(main())
