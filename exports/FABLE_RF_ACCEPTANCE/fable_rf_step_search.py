"""Fable RF extended delivery-order search with an approval attempt after EVERY step.

usage: fable_rf_step_search.py <project-root> [--family NAME] [--shard I/N] [--limit N] [--json out.json]

Extends fable_re_step_search.py (four families, 480 orders) with families it does not contain. Each family
mixes a claim-free older or conflicting message that is later re-sent carrying its first claim (the RF-01
path) with one or two of: a distinct second claim on an older or a newer message, a revision of the row, a
revised receipt, a replacement of the claimant, a revision of that replacement, a withdrawal and re-send of
the claimant, a claim carried inside the row data, timestamp order, a retained re-send on the replacement
row itself, and a person's target selection. The claimed locked-chain target P arrives at every possible
position, so every family contains orders in which the target arrives after the claim, after a revision of
the claimant and after its replacement. Ten families have five steps (120 orders each) and two have six
(720 each). In the four families that name the open December row B as a second target, B is on file before
the permutation starts; B arriving late is covered by fable_re_step_search.py and probe C7a.

After each step an honest operator prepares December, ties the statement, clears every blocker that has an
ordinary disposition and asks an independent reviewer to approve every December row. November stays locked
and nobody holds the lock grant, so under D-026:

  double    - A1 is approved in locked November while a December row is approved, and that row reaches A1
              (or the late November row L) through claims that were delivered and whose targets are all on
              file. A claimant with two declared targets and no selection counts through either. After an
              accepted selection only the selected target counts (clause 9: the person decided).
  early     - the same, but some target on the path has not arrived yet (observation UC-20). The approval
              must stop governing when the target arrives; the next step checks that as a double.
  released  - a row or receipt that was held under locked November at an earlier step is, at a later step,
              admitted to an open period. Nobody in this search holds the lock grant, so any is a failure.
  unlinked  - the owner's RF-01 invariant: a card row whose first declared target is on file has no link to
              it (a claim recorded without being applied). Skipped only where the link would close a cycle.
  repeat    - (every second order) each delivery is repeated at once in a new envelope; it must answer
              changed=False and add no source snapshot, binding, move, link, event, decision or head change.
              One case is counted apart as an observation (repeat-of-retired-row), not as a failure: the
              repeated row had already been retired by its replacement. The RE checkpoint behaves the same.

Public service operations only; temporary SQLite; fictional data; table reads are read-only.
"""
import importlib.util, itertools, json, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
_p = ROOT / 'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
_s = importlib.util.spec_from_file_location('fable_re_probes', _p); p = importlib.util.module_from_spec(_s)
_a = sys.argv; sys.argv = [str(_p), str(ROOT)]; _s.loader.exec_module(p); sys.argv = _a
h, rb = p.h, p.rb
PREP, PREP2, REV2, DEC = h.PREP, h.PREP2, h.REV2, h.DEC
tx, rc, stmt, sup, packet, run, gov, K = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov, rb.K
T7, T6 = '2026-12-05T10:00:00Z', '2026-12-04T10:00:00Z'


def q(target=None, amount='40.00', date='2026-12-03', inside=None, **kw):
    row = tx('Q', date, amount, **kw)
    if inside:
        row['data']['supersedes_source_id'] = inside
    if target:
        row['supersedes'] = K(target)
    return row


def z(target='Q', amount='40.00', **kw):
    row = tx('Z', '2026-12-05', amount, **kw)
    if target:
        row['supersedes'] = K(target)
    return row


RQ = lambda amount='40.00', **kw: rc('Q', '2026-12-03', amount, **kw)
RZ = lambda amount='40.00': rc('Z', '2026-12-05', amount)
# name -> (rows, claims declared by this delivery as (claimant, target))
D = {
    'P': (lambda: [sup('P', '2026-12-02', '40.00', 'A1'), rc('P', '2026-12-02', '40.00')], [('P', 'A1')]),
    'B': (lambda: [tx('B', '2026-12-02', '40.00', desc='OPEN ROW DEMO'), rc('B', '2026-12-02', '40.00', vendor='OPEN ROW DEMO')], []),
    'Q7': (lambda: [q(as_of=7), RQ()], []),
    'Q6': (lambda: [q(as_of=6)], []),
    'Q6cP': (lambda: [q('P', as_of=6)], [('Q', 'P')]),
    'Q6iP': (lambda: [q(inside='P', as_of=6)], [('Q', 'P')]),
    'Q5cB': (lambda: [q('B', as_of=5)], [('Q', 'B')]),
    'Q8cB': (lambda: [q('B', as_of=8), RQ()], [('Q', 'B')]),
    'Q8': (lambda: [q(amount='41.00', as_of=8), RQ('41.00')], []),
    'Q8d': (lambda: [q(amount='41.00', date='2026-12-04', as_of=8), rc('Q', '2026-12-04', '41.00')], []),
    'Q7x': (lambda: [q(amount='41.00', as_of=7)], []),
    'Q7xcP': (lambda: [q('P', amount='41.00', as_of=7)], [('Q', 'P')]),
    'Qdel': (lambda: [dict(q(as_of=8), tombstone=True, removal_reason='feed_removed')], []),
    'Q9': (lambda: [q(as_of=9), RQ()], []),
    'RQ2': (lambda: [RQ(content='Fictional revised receipt for Q')], []),
    'Qt7': (lambda: [q(as_of=T7), RQ()], []),
    'Qt6': (lambda: [q(as_of=T6)], []),
    'Qt6cP': (lambda: [q('P', as_of=T6)], [('Q', 'P')]),
    'Z': (lambda: [z(), RZ()], [('Z', 'Q')]),
    'Zr': (lambda: [z(amount='41.00'), RZ('41.00')], [('Z', 'Q')]),
    'QcP': (lambda: [q('P'), RQ()], [('Q', 'P')]),
    'Z7': (lambda: [z(None, as_of=7), RZ()], []),
    'Z6': (lambda: [z(None, as_of=6)], []),
    'Z6cQ': (lambda: [z('Q', as_of=6)], [('Z', 'Q')]),
}
# person steps: name -> (actor attribute on the probe module, item, target)
SELECT = {'SELB': ('DISP', 'Q', 'B'), 'SELP': ('DR', 'Q', 'P')}
FAMILIES = {
    'retained-claim+row-revision': ('P', 'Q7', 'Q6', 'Q6cP', 'Q8d'),
    'retained-claim+receipt-revision': ('P', 'Q7', 'Q6', 'Q6cP', 'RQ2'),
    'same-order-conflict-resent': ('P', 'Q7', 'Q7x', 'Q7xcP', 'Z'),
    'claim-inside-row-data': ('P', 'Q7', 'Q6', 'Q6iP', 'Z'),
    'timestamp-order': ('P', 'Qt7', 'Qt6', 'Qt6cP', 'Z'),
    'retained-claim-on-replacement': ('P', 'QcP', 'Z7', 'Z6', 'Z6cQ'),
    'retained-claim+older-conflict': ('P', 'Q7', 'Q6', 'Q6cP', 'Q5cB'),
    'retained-claim+newer-conflict': ('P', 'Q7', 'Q6', 'Q6cP', 'Q8cB'),
    'retained-claim+withdrawal+resend': ('P', 'Q7', 'Q6', 'Q6cP', 'Qdel', 'Q9'),
    'conflict+selection-without-lock': ('P', 'Q7', 'Q6cP', 'Q8cB', 'SELB'),
    'retained-conflict+confirming-selection': ('P', 'Q6', 'Q6cP', 'Q8cB', 'SELP'),
    'retained-claim+replacement+revision': ('P', 'Q7', 'Q6', 'Q6cP', 'Z', 'Zr'),
}
# rows that are on file before the permutation starts (the open December row B, where a family names it as a target)
PRE = {'retained-claim+older-conflict': ('B',), 'retained-claim+newer-conflict': ('B',), 'conflict+selection-without-lock': ('B',), 'retained-conflict+confirming-selection': ('B',)}
LOCKED = {K('A1'), K('L')}
DEC_ROWS = ('P', 'B', 'Q', 'Z')


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


def heads(os_):
    return {k: r for k, r in p.sql(os_, "SELECT source_key,removed FROM source_heads WHERE kind='transaction'")}


def reach(start, declared, selected, on_file):
    """(reaches a locked row through targets on file, reaches one only through a target not on file)."""
    edges = {}
    for c, t in declared:
        edges.setdefault(K(c), [])
        if K(t) not in edges[K(c)]:
            edges[K(c)].append(K(t))
    for c, t in selected.items():
        edges[K(c)] = [K(t)]
    known = early = False
    stack = [(K(start), True)]; seen = set()
    while stack:
        key, ok = stack.pop()
        if (key, ok) in seen:
            continue
        seen.add((key, ok))
        for t in edges.get(key, []):
            ok2 = ok and t in on_file
            if t in LOCKED:
                known |= ok2; early |= not ok2
            stack.append((t, ok2))
    return known, early and not known


def unlinked(os_):
    bad = []
    file = heads(os_); pairs = set(p.links(os_))
    for key in file:
        first = p.sql(os_, "SELECT payload FROM accounting_events WHERE item_key=? AND code='SOURCE_CLAIM_DECLARED' ORDER BY id LIMIT 1", (key,))
        if not first:
            continue
        target = json.loads(first[0][0])['target_key']
        chosen = p.sql(os_, "SELECT payload FROM dispositions WHERE item_key=? AND choice=? AND action='apply' ORDER BY id DESC LIMIT 1", (key, p.CHOICE))
        if chosen:
            target = json.loads(chosen[0][0])['target_key']
        if target in file and (target, key) not in pairs:
            # a link that would close a cycle is legitimately refused
            chain = set(); cur = target
            while cur and cur not in chain:
                chain.add(cur); nxt = [o for o, n in pairs if n == cur]; cur = nxt[0] if nxt else None
            if key not in chain:
                bad.append((key.split(':')[-1], target.split(':')[-1]))
    return bad


def one(order, repeat, pre=()):
    os_ = p.base()
    declared = []; selected = {}
    for name in pre:
        os_.intake(PREP2, packet('pre-%s' % name, D[name][0]())); declared += D[name][1]
    out = {'order': list(order), 'repeat_checked': repeat, 'double_at_steps': [], 'early_at_steps': [], 'released_at_steps': [], 'left_hold_at_steps': [],
           'unlinked_at_steps': [], 'repeat_failures': [], 'repeat_of_retired_row': [], 'trail': []}
    was_held = set()
    for i, step in enumerate(order):
        if step in SELECT:
            who, item, target = SELECT[step]
            r = quiet(p.select, os_, getattr(p, who), target, item)
            r = r[1] if r[0] == 'ok' else r
            if r[0] == 'ok':
                selected[item] = target
        else:
            rows, claims = D[step]
            r = quiet(os_.intake, PREP2, packet('s%d-%s' % (i, step), rows()))
            if r[0] == 'ok':
                declared += claims
            if repeat:
                before = p.rows_of(os_); live = heads(os_)
                retired = sorted(m['key'].split(':')[-1] for m in rows() if m['kind'] == 'transaction' and not m.get('tombstone') and live.get(m['key']) == 1)
                r2 = quiet(os_.intake, PREP2, packet('s%d-%s-again' % (i, step), rows()))
                if r[0] == 'ok' and not (r2[0] == 'ok' and r2[1]['changed'] is False and p.rows_of(os_) == before):
                    out['repeat_of_retired_row' if retired else 'repeat_failures'].append((i, step, retired, str(r2)[:160]))
        bad = unlinked(os_)
        if bad:
            out['unlinked_at_steps'].append((i, bad))
        run(os_, 'card_preparation', '2026-12', PREP2)
        rows = []
        for k in DEC_ROWS:
            a = gov(os_, K(k), '2026-12')
            if a is not None:
                t = a['payload']['data']['transaction']; rows.append(tx(k, t['date'], t['amount']))
        if rows:
            quiet(os_.intake, PREP2, packet('statement-%d' % i, [stmt(rows, DEC, opening='100.00')]))
            run(os_, 'card_preparation', '2026-12', PREP2)
        for k in DEC_ROWS:
            settle(os_, K(k))
        bad = unlinked(os_)
        if bad and not (out['unlinked_at_steps'] and out['unlinked_at_steps'][-1][0] == i):
            out['unlinked_at_steps'].append((i, bad))
        nov = rb.approved(os_, K('A1'), '2026-11')
        dec = [k for k in DEC_ROWS if rb.approved(os_, K(k), '2026-12')]
        file = heads(os_)
        hits = {k: reach(k, declared, selected, set(file)) for k in dec}
        if nov and any(v[0] for v in hits.values()):
            out['double_at_steps'].append((i, [k for k, v in hits.items() if v[0]]))
        elif nov and any(v[1] for v in hits.values()):
            out['early_at_steps'].append((i, [k for k, v in hits.items() if v[1]]))
        held = set(rb.held_under(os_))
        gone = was_held - held
        if gone:
            out['left_hold_at_steps'].append((i, sorted(gone)))
            real = [k for k in gone if (p.where(os_, k) or (None, 0, None))[1] == 1]
            if real:
                out['released_at_steps'].append((i, sorted(real)))
        was_held |= held
        out['trail'].append({'step': step, 'result': r[0] if r[0] != 'ok' else 'ok', 'detail': None if r[0] == 'ok' else str(r)[:200], 'december_approved': dec,
                             'held': sorted(k.split(':')[-1] for k in held), 'declared': sorted({'%s>%s' % d for d in declared}), 'selected': dict(selected)})
    out['final'] = {k: (lambda a: None if a is None else {'status': a['review_status'], 'blockers': a['blockers']})(gov(os_, K(k), '2026-12')) for k in DEC_ROWS}
    out['final_held'] = sorted(k.split(':')[-1] for k in rb.held_under(os_))
    out['final_links'] = sorted('%s>%s' % (n.split(':')[-1], o.split(':')[-1]) for o, n in p.links(os_))
    out['audit_ok'] = bool(os_.verify_audit(PREP))
    return out


def main():
    names = [sys.argv[sys.argv.index('--family') + 1]] if '--family' in sys.argv else list(FAMILIES)
    shard = [int(x) for x in sys.argv[sys.argv.index('--shard') + 1].split('/')] if '--shard' in sys.argv else [0, 1]
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    results = []
    for name in names:
        for n, order in enumerate(itertools.permutations(FAMILIES[name])):
            if n % shard[1] != shard[0] or (limit is not None and n >= limit):
                continue
            r = one(order, repeat=bool(n % 2), pre=PRE.get(name, ())); r['family'] = name; r['index'] = n; r['on_file_before'] = list(PRE.get(name, ())); results.append(r)
            flags = ['DOUBLE@%s' % r['double_at_steps'] if r['double_at_steps'] else 'single', 'RELEASED@%s' % r['released_at_steps'] if r['released_at_steps'] else 'no-release',
                     'UNLINKED@%s' % r['unlinked_at_steps'] if r['unlinked_at_steps'] else 'linked', 'REPEAT-CHANGED@%s' % r['repeat_failures'] if r['repeat_failures'] else ('repeat-of-retired-row@%s' % [x[:3] for x in r['repeat_of_retired_row']] if r['repeat_of_retired_row'] else 'repeat-ok' if r['repeat_checked'] else 'repeat-n/a'),
                     'audit-ok' if r['audit_ok'] else 'AUDIT-FAILED']
            print('%-38s %4d %-30s %s early=%s held=%s links=%s' % (name, n, ' '.join(order), ' '.join(flags), [s for s, _ in r['early_at_steps']], r['final_held'], r['final_links']), flush=True)
    c = lambda key: sum(1 for r in results if r[key])
    print('\nSUMMARY runs=%d double=%d released_without_authority=%d unlinked_first_claim=%d repeat_changed=%d audit_failures=%d approved_before_target_known=%d left_hold_listing=%d repeat_checked=%d repeat_of_retired_row=%d' % (
        len(results), c('double_at_steps'), c('released_at_steps'), c('unlinked_at_steps'), c('repeat_failures'), sum(1 for r in results if not r['audit_ok']), c('early_at_steps'), c('left_hold_at_steps'),
        c('repeat_checked'), c('repeat_of_retired_row')))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps({'runs': len(results), 'results': results}, indent=1))
    h.TMP.cleanup()
    return 1 if any(c(k) for k in ('double_at_steps', 'released_at_steps', 'unlinked_at_steps', 'repeat_failures')) or any(not r['audit_ok'] for r in results) else 0


if __name__ == '__main__':
    sys.exit(main())
