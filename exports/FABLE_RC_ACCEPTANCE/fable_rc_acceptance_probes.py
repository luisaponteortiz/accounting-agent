"""Fable acceptance probes for the RC-01 to RC-03 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_rc_acceptance_probes.py <project-root> [PROBE_ID ...]

Drives the application in <project-root> through public service operations only. Temporary
SQLite files, fictional data, no network, model, posting or payment. Row counts are read from
the probe's own temporary database, read-only.

Helpers are loaded unchanged from <project-root>/exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py
(which loads the earlier RA helper), so all three scripts build identical fixtures.

Part 1 (Q..) re-states every acceptance assertion of RC-01, RC-02 and RC-03 as an explicit check,
because the earlier probes N01b/N01c/N01d only test the outcome "not approved in two periods".
Part 2 (X..) tries arrival orders that no ticket named.

Verdicts: OK control held | WEAK confirmed gap (exit 1) | NOTE observation needing a decision
          | ERROR probe could not reach its intended state (exit 1)
"""
import importlib.util
import json
import sqlite3
import sys
import traceback
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
_rb_path = ROOT / 'exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py'
_spec = importlib.util.spec_from_file_location('fable_rb_probes', _rb_path)
rb = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_rb_path), str(ROOT)]
_spec.loader.exec_module(rb)
sys.argv = _argv
h = rb.h

CARD, NOV, DEC = h.CARD, h.NOV, h.DEC
PREP, PREP2, REV, REV2, REV3 = h.PREP, h.PREP2, h.REV, h.REV2, h.REV3
FIN, PADMIN = h.FIN, h.PADMIN
tx, rc, stmt, sup, packet, run, gov, arts = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov, h.arts
review, dispose, brief, show, attempt = h.review, h.dispose, h.brief, h.show, h.attempt
exceptions_of, governing_keys = h.exceptions_of, h.governing_keys
moves, events, held_under, approved, twice, try_to_approve = rb.moves, rb.events, rb.held_under, rb.approved, rb.twice, rb.try_to_approve
K, MOVED, TRANSITION = rb.K, rb.MOVED, rb.TRANSITION
UNRESOLVED = 'SOURCE_TRANSITION_UNRESOLVED'
LATE = 'LATE_ACTIVITY_IN_LOCKED_PERIOD'
PROBES = []


def probe(pid, ticket, title):
    def register(fn):
        PROBES.append((pid, ticket, title, fn))
        return fn
    return register


def counts(os_):
    """Row counts of the append-only tables the corrections write to (read-only)."""
    db = sqlite3.connect('file:%s?mode=ro' % os_.probe_path, uri=True)
    try:
        out = {t: db.execute('SELECT COUNT(*) FROM ' + t).fetchone()[0] for t in ('snapshots', 'source_periods', 'source_moves', 'source_links', 'decisions')}
        out['chain_events'] = db.execute("SELECT COUNT(*) FROM accounting_events WHERE code LIKE 'APPROVED_SOURCE_%' OR code LIKE 'SOURCE_SUPERSESSION%' OR code='ITEM_LEFT_POPULATION'").fetchone()[0]
        return out
    finally:
        db.close()


def links(os_):
    db = sqlite3.connect('file:%s?mode=ro' % os_.probe_path, uri=True)
    try:
        return [(r[0], r[1]) for r in db.execute('SELECT o.source_key,n.source_key FROM source_links l JOIN snapshots o ON o.id=l.old_snapshot_id JOIN snapshots n ON n.id=l.new_snapshot_id ORDER BY l.id')]
    finally:
        db.close()


def approvals_kept(os_, key):
    """Number of approval decisions ever recorded for artifacts of this item (read-only)."""
    db = sqlite3.connect('file:%s?mode=ro' % os_.probe_path, uri=True)
    try:
        return db.execute("SELECT COUNT(*) FROM decisions d JOIN artifacts a ON a.id=d.artifact_id WHERE a.item_key=? AND d.decision IN ('approve','resolve_approve')", (key,)).fetchone()[0]
    finally:
        db.close()


def approve_fully(os_, key, period='2026-12'):
    """As try_to_approve, and first accept a revised supporting document if that is the only other blocker."""
    a = gov(os_, key, period)
    if a is not None and rb.REVISED in a['blockers']:
        show('revised_evidence_accepted on ' + key, dispose(os_, key, rb.REVISED, 'revised_evidence_accepted', period=period))
        run(os_, 'card_preparation', period, PREP2)
    return try_to_approve(os_, key, period)


def card_gov(os_, period='2026-12'):
    return [k for k in governing_keys(os_, period) if k.startswith(CARD)]


def check(label, ok):
    print('    assert %-78s %s' % (label, 'yes' if ok else 'NO'))
    return bool(ok)


def approve_pending(os_, period='2026-11', reviewer=None):
    for k in governing_keys(os_, period):
        a = gov(os_, k, period)
        if a['eligible'] and a['review_status'] == 'pending':
            review(os_, reviewer or REV, a, 'approve')


# =======================================================================================
# Part 1. The acceptance assertions of the three tickets, one check each
# =======================================================================================

@probe('Q01', 'RC-01', 'every RC-01 assertion: withdrawal after the lock, fresh and late link; listing; blocked move; reopen; relock')
def _():
    good = True
    for order in ('fresh', 'late'):
        os_ = h.approved_locked_november()
        gone = dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')
        other = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
        b_plain = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
        b_claim = [sup('B1', '2026-12-02', '40.00', 'A1'), rc('B1', '2026-12-02', '40.00')]
        if order == 'fresh':
            os_.intake(PREP2, packet('void', [gone]))
            os_.intake(PREP2, packet('b', b_claim + other + [stmt(b_claim + other, DEC, opening='100.00')]))
        else:
            os_.intake(PREP2, packet('b', b_plain + other + [stmt(b_plain + other, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
            show('[late] B1 approved in December before the withdrawal and the claim', review(os_, REV2, gov(os_, K('B1'), '2026-12'), 'approve'))
            os_.intake(PREP2, packet('void', [gone]))
            os_.intake(PREP2, packet('claim', [b_claim[0]]))
        run(os_, 'card_preparation', '2026-12', PREP2)
        ex, mv = exceptions_of(os_), moves(os_)
        print('    [%s] exceptions: %s' % (order, ex)); print('    [%s] moves: %s' % (order, mv))
        good &= check('[%s] December has no governing artifact for B1' % order, gov(os_, K('B1'), '2026-12') is None)
        good &= check('[%s] B1 and its receipt are held under November as MOVED' % order, {K('B1'), 'receipt-B1'} <= held_under(os_))
        good &= check('[%s] a blocked move row with had_approval exists for B1' % order, any(m[0] == K('B1') and m[1] == '2026-11' and m[3] == 1 and m[4] == 1 for m in mv))
        good &= check('[%s] no move row has the same origin and destination' % order, all(m[1] != m[2] for m in mv))
        good &= check('[%s] state.source_exceptions lists the withdrawal of A1 under November' % order, (K('A1'), '2026-11', LATE) in ex)
        good &= check('[%s] A1 is still approved and governing in locked November' % order, approved(os_, K('A1'), '2026-11'))
        fin = show('[%s] finalize December without acknowledgement' % order, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        good &= check('[%s] December cannot be finalized silently while B1 is held' % order, fin[0] == 'refused')
        before = len([s for s in os_.export(PREP)['evidence_history'] if s['source_key'] == K('A1')])
        os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
        b = gov(os_, K('B1'), '2026-12'); ex = exceptions_of(os_)
        print('    [%s] after reopen -> November: %s | December: %s | B1: %s | exceptions: %s' % (order, governing_keys(os_, '2026-11'), card_gov(os_), brief(b), ex))
        good &= check('[%s] after reopen November has no governing A1' % order, gov(os_, K('A1'), '2026-11') is None)
        good &= check('[%s] after reopen December has exactly one item for the charge, with TRANSITION' % order, [k for k in card_gov(os_) if k != K('D1')] == [K('B1')] and b is not None and TRANSITION in b['blockers'] and b['review_status'] != 'approve')
        good &= check('[%s] after reopen the withdrawal is admitted and no longer listed' % order, not any(e[0] == K('A1') for e in ex))
        good &= check('[%s] no version of A1 was rewritten or dropped' % order, len([s for s in os_.export(PREP)['evidence_history'] if s['source_key'] == K('A1')]) == before)
        try_to_approve(os_, K('B1'))
        good &= check('[%s] B1 approvable once, A1 not governing' % order, approved(os_, K('B1'), '2026-12') and gov(os_, K('A1'), '2026-11') is None)
        approve_pending(os_)
        show('[%s] relock November' % order, attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'probe acknowledgement'))
        rev = [sup('B1', '2026-12-02', '42.00', 'A1'), rc('B1', '2026-12-02', '42.00')]
        os_.intake(PREP2, packet('b-rev', rev + [stmt(rev + other, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
        b3 = gov(os_, K('B1'), '2026-12')
        print('    [%s] after relock and a revision of B1 -> B1: %s | held: %s' % (order, brief(b3), sorted(held_under(os_))))
        good &= check('[%s] after relock a revision of B1 stays in December' % order, b3 is not None and b3['payload']['data']['transaction']['amount'] == '42.00' and K('B1') not in held_under(os_))
    return 'OK' if good else 'WEAK'


@probe('Q02', 'RC-02', 'every RC-02 assertion: late link on a middle source, terminal eligible and already approved; events; reopen; lapse of the earlier acceptance')
def _():
    good = True
    for pre_approved in (False, True):
        tag = 'approved' if pre_approved else 'eligible'
        os_ = h.approved_locked_november()
        b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
        c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('b', b + [stmt(c, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
        os_.intake(PREP2, packet('c', c)); run(os_, 'card_preparation', '2026-12', PREP2)
        if pre_approved:
            try_to_approve(os_, K('C1'))
            good &= check('[approved] C1 is approved in December before the late link', approved(os_, K('C1'), '2026-12'))
        n_dec = counts(os_)['decisions']
        os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')])); run(os_, 'card_preparation', '2026-12', PREP2)
        ex, mv, ev = exceptions_of(os_), moves(os_), events(os_)
        print('    [%s] exceptions: %s' % (tag, ex)); print('    [%s] moves: %s' % (tag, mv)); print('    [%s] events: %s' % (tag, ev))
        good &= check('[%s] December has no governing artifact for C1 or B1' % tag, gov(os_, K('C1'), '2026-12') is None and gov(os_, K('B1'), '2026-12') is None)
        good &= check('[%s] C1, B1 and the receipt of C1 are held under November as MOVED' % tag, {K('C1'), K('B1'), 'receipt-C1'} <= held_under(os_))
        good &= check('[%s] A1 still approved and governing in locked November' % tag, approved(os_, K('A1'), '2026-11'))
        if pre_approved:
            good &= check('[approved] an accounting event names the December approval of C1', any(e[0].startswith('APPROVED_SOURCE_') and e[1] == '2026-12' and e[2] == K('C1') for e in ev))
            good &= check('[approved] ITEM_LEFT_POPULATION is recorded for C1', any(e[0] == 'ITEM_LEFT_POPULATION' and e[2] == K('C1') for e in ev))
            good &= check('[approved] a blocked move row with had_approval exists for C1', any(m[0] == K('C1') and m[1] == '2026-11' and m[3] == 1 and m[4] == 1 for m in mv))
            hist = arts(os_, K('C1'), '2026-12')
            print('    [approved] C1 artifacts kept: %s | approval decisions kept for C1: %d' % ([(a['id'], a['review_status'], bool(a['governing'])) for a in hist], approvals_kept(os_, K('C1'))))
            good &= check('[approved] the earlier approval decision of C1 is kept; no C1 artifact governs', approvals_kept(os_, K('C1')) >= 1 and len(hist) >= 1 and not any(a['governing'] for a in hist))
            good &= check('[approved] no decision row was removed', counts(os_)['decisions'] >= n_dec)
        fin = show('[%s] finalize December without acknowledgement' % tag, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        good &= check('[%s] December cannot be finalized silently while C1 is held' % tag, fin[0] == 'refused')
        os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
        c1 = gov(os_, K('C1'), '2026-12')
        print('    [%s] after reopen -> November: %s | December: %s | C1: %s' % (tag, governing_keys(os_, '2026-11'), card_gov(os_), brief(c1)))
        good &= check('[%s] after reopen November has no governing A1' % tag, gov(os_, K('A1'), '2026-11') is None)
        good &= check('[%s] after reopen December has exactly one governing item, C1' % tag, card_gov(os_) == [K('C1')])
        good &= check('[%s] C1 carries TRANSITION and is not approved (earlier acceptance lapsed)' % tag, c1 is not None and TRANSITION in c1['blockers'] and c1['review_status'] != 'approve' and not c1['eligible'])
        st = os_.export(PREP)
        ever = sorted({s['source_key'] for s in st['evidence_history'] for bnd in st['source_period_history'] if bnd['snapshot_id'] == s['id'] and bnd['period_id'] == '2026-12' and bnd['admitted'] and s['source_key'] == K('A1')})
        good &= check('[%s] A1 was never admitted to December' % tag, not ever)
        if c1 is not None:
            chain = sorted(e['source_key'] for e in c1['payload']['data']['evidence'] if 'link_id' in e)
            print('    [%s] C1 disclosed chain: %s' % (tag, chain))
            good &= check('[%s] C1 discloses the whole chain B1 and A1' % tag, chain == [K('A1'), K('B1')])
        try_to_approve(os_, K('C1'))
        good &= check('[%s] C1 approvable once after a new acceptance; A1 and B1 not governing' % tag, approved(os_, K('C1'), '2026-12') and gov(os_, K('A1'), '2026-11') is None and gov(os_, K('B1'), '2026-12') is None)
    return 'OK' if good else 'WEAK'


@probe('Q02i', 'RC-02', 'no-op rule: an intake that does not touch a chain adds no binding, move, link or chain event for it (held chain, released chain, open-period chain)')
def _():
    good = True
    extra = lambda n: [tx('E%d' % n, '2026-12-0%d' % (5 + n), '11.00'), rc('E%d' % n, '2026-12-0%d' % (5 + n), '11.00')]

    def unrelated(os_, tag, n):
        before = counts(os_)
        os_.intake(PREP2, packet('extra-%s-%d' % (tag, n), extra(n)))
        rep = os_.intake(PREP2, packet('extra-%s-%d' % (tag, n), extra(n)))
        after = counts(os_)
        delta = {k: after[k] - before[k] for k in before}
        print('    [%s] unrelated intake of 2 sources (+ replay %s) -> row deltas: %s' % (tag, rep.get('replay'), delta))
        return check('[%s] 2 new snapshots, 2 new bindings, no move, link or chain event' % tag, delta['snapshots'] == 3 and delta['source_periods'] == 2 and delta['source_moves'] == 0 and delta['source_links'] == 0 and delta['chain_events'] == 0)

    # held chain
    os_ = h.approved_locked_november()
    b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(c, DEC, opening='100.00')])); os_.intake(PREP2, packet('c', c))
    os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')]))
    good &= check('[held] chain is held', {K('C1'), K('B1')} <= held_under(os_))
    good &= unrelated(os_, 'held', 1)
    # released chain, relocked
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    approve_pending(os_)
    show('relock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'probe acknowledgement'))
    good &= unrelated(os_, 'released-relocked', 2)
    good &= check('[released-relocked] C1 still governs December, nothing held', card_gov(os_) and K('C1') in card_gov(os_) and not held_under(os_))
    # open-period chain
    os2 = h.new_os(periods=(NOV, DEC)); h.clean_november(os2)
    os2.intake(PREP2, packet('b', b + [stmt(b, DEC, opening='100.00')])); os2.intake(PREP2, packet('claim', [sup('B1', '2026-12-02', '40.00', 'A1')]))
    good &= unrelated(os2, 'open', 3)
    good &= check('[open] no quarantine and no move row at all', not exceptions_of(os2) and not moves(os2))
    return 'OK' if good else 'WEAK'


@probe('Q03', 'RC-03', 'every RC-03 assertion: target arrives without the claimant being re-sent; claimant already replaced; newest first; open target; cycle')
def _():
    good = True
    y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
    z = [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')]
    x = [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]
    # (a) the ticket's order: Y, X, Z
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y', y + [stmt(z, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    ay = gov(os_, K('A1Y'), '2026-12')
    good &= check('[a] before its target arrives A1Y is held as unresolved', ay is not None and UNRESOLVED in ay['blockers'])
    os_.intake(PREP2, packet('x', x)); run(os_, 'card_preparation', '2026-12', PREP2)
    good &= check('[a] after A1X arrives A1Y is listed under November', K('A1Y') in held_under(os_) and gov(os_, K('A1Y'), '2026-12') is None)
    os_.intake(PREP2, packet('z', z)); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    [a] exceptions: %s | links: %s' % (exceptions_of(os_), links(os_)))
    good &= check('[a] after A1Z arrives December has no governing A1Z and A1Z is under November', gov(os_, K('A1Z'), '2026-12') is None and K('A1Z') in held_under(os_))
    good &= check('[a] nothing of the chain governs December; A1 approved in November', not card_gov(os_) and approved(os_, K('A1'), '2026-11'))
    # (b) claimant already replaced when its target arrives: Y, Z, X
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y', y + [stmt(z, DEC, opening='100.00')])); os_.intake(PREP2, packet('z', z)); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    [b] before the target: December %s | A1Z: %s' % (card_gov(os_), brief(gov(os_, K('A1Z'), '2026-12'))))
    os_.intake(PREP2, packet('x', x)); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    [b] exceptions: %s | links: %s' % (exceptions_of(os_), links(os_)))
    good &= check('[b] the replaced claimant A1Y is linked to A1X', (K('A1X'), K('A1Y')) in links(os_))
    good &= check('[b] December has no governing chain member; A1Z and A1X under November', not card_gov(os_) and {K('A1Z'), K('A1X')} <= held_under(os_))
    try_to_approve(os_, K('A1Z'))
    good &= check('[b] not approved in two periods', not twice(os_, K('A1'), K('A1Z')))
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    good &= check('[b] after reopen only A1Z governs December and A1 has left November', card_gov(os_) == [K('A1Z')] and gov(os_, K('A1'), '2026-11') is None)
    # (c) newest first, nothing re-sent: Z, Y, X
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('z', z + [stmt(z, DEC, opening='100.00')])); os_.intake(PREP2, packet('y', y)); os_.intake(PREP2, packet('x', x)); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    [c] exceptions: %s | links: %s' % (exceptions_of(os_), links(os_)))
    # A1Y was already replaced by A1Z inside December, so it is a retired head and is not listed; see [b]
    good &= check('[c] newest first without any re-send: nothing governs December; A1Z and A1X held', not card_gov(os_) and {K('A1X'), K('A1Z'), 'receipt-A1Z'} <= held_under(os_) and (K('A1X'), K('A1Y')) in links(os_) and (K('A1Y'), K('A1Z')) in links(os_))
    try_to_approve(os_, K('A1Z'))
    good &= check('[c] not approved in two periods', not twice(os_, K('A1'), K('A1Z')))
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    st = os_.export(PREP)
    ever = sorted({s['source_key'] for s in st['evidence_history'] for bnd in st['source_period_history'] if bnd['snapshot_id'] == s['id'] and bnd['period_id'] == '2026-12' and bnd['admitted'] and s['source_key'] in (K('A1'), K('A1X'))})
    good &= check('[c] after reopen only A1Z is admitted; A1 and A1X never entered December', card_gov(os_) == [K('A1Z')] and not ever and gov(os_, K('A1'), '2026-11') is None)
    # (d) target in an open period: ordinary supersession, no unresolved blocker left
    os_ = h.new_os(periods=(NOV, DEC)); h.clean_november(os_); run(os_, 'card_preparation')
    os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    good &= check('[d] open November: A1Y first shows UNRESOLVED', UNRESOLVED in gov(os_, K('A1Y'), '2026-12')['blockers'])
    os_.intake(PREP2, packet('x', x)); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    ay = gov(os_, K('A1Y'), '2026-12')
    print('    [d] A1Y: %s | December: %s | November: %s | exceptions: %s | moves: %s' % (brief(ay), card_gov(os_), governing_keys(os_, '2026-11'), exceptions_of(os_), moves(os_)))
    good &= check('[d] claim resolved: TRANSITION stays, UNRESOLVED is gone', ay is not None and TRANSITION in ay['blockers'] and UNRESOLVED not in ay['blockers'])
    good &= check('[d] ordinary supersession: only A1Y in December, A1 left November, no quarantine, no blocked move', card_gov(os_) == [K('A1Y')] and gov(os_, K('A1'), '2026-11') is None and not exceptions_of(os_) and not any(m[3] for m in moves(os_)))
    # (e) a pending claim must not close a cycle
    os_ = h.approved_locked_november()
    p = [sup('P1', '2026-12-06', '20.00', 'P2'), rc('P1', '2026-12-06', '20.00')]
    q = [sup('P2', '2026-12-07', '20.00', 'P1'), rc('P2', '2026-12-07', '20.00')]
    os_.intake(PREP2, packet('p', p + [stmt(q, DEC, opening='100.00')]))
    r = show('[e] P2 arrives claiming P1 while P1 claims P2', attempt(os_.intake, PREP2, packet('q', q)))
    more = show('[e] a later unrelated intake', attempt(os_.intake, PREP2, packet('more', [tx('E9', '2026-12-09', '11.00'), rc('E9', '2026-12-09', '11.00')])))
    run(os_, 'card_preparation', '2026-12', PREP2)
    lk = [l for l in links(os_) if l[0] in (K('P1'), K('P2'))]
    print('    [e] links between P1 and P2: %s | December: %s' % (lk, card_gov(os_)))
    good &= check('[e] at most one link between the two; the application still prepares', len(lk) <= 1 and more[0] == 'ok' and len([k for k in card_gov(os_) if k in (K('P1'), K('P2'))]) == 1)
    return 'OK' if good else 'WEAK'


# =======================================================================================
# Part 2. Arrival orders that no ticket named
# =======================================================================================

def outcome(os_, dec_key, label, approver=None):
    """Shared ending: honest operator tries to approve the December item; report double approval."""
    run(os_, 'card_preparation', '2026-12', PREP2)
    a = gov(os_, dec_key, '2026-12')
    print('    %s -> December %s: %s | held under November: %s' % (label, dec_key, brief(a), sorted(held_under(os_))))
    print('    exceptions: %s' % exceptions_of(os_)); print('    links: %s' % links(os_))
    (approver or try_to_approve)(os_, dec_key)
    both = twice(os_, K('A1'), dec_key)
    if both:
        show('finalize December without acknowledgement', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    print('    November A1: %s | December %s: %s | approved in both periods: %s' % (brief(gov(os_, K('A1'), '2026-11')), dec_key, brief(gov(os_, dec_key, '2026-12')), both))
    return both


@probe('X01', 'RC-03', 'the claim is declared by re-sending an unchanged row (same bytes) before its target has arrived; the target then arrives and is held')
def _():
    os_ = h.approved_locked_november()
    y_plain = [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y-plain', y_plain + [stmt(y_plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    r = show('A1Y re-sent unchanged with supersedes=A1X (A1X not yet received)', attempt(os_.intake, PREP2, packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')])))
    ev = [e for e in events(os_, 'SOURCE_SUPERSESSION')]
    print('    claim recorded as an event:', ev)
    os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    both = outcome(os_, K('A1Y'), 'A1X arrives (supersedes locked A1)')
    return 'WEAK' if both else 'OK'


@probe('X01b', 'RC-03', 'control for X01: the same steps, but the claim is repeated once more after the target has arrived')
def _():
    os_ = h.approved_locked_november()
    y_plain = [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y-plain', y_plain + [stmt(y_plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    os_.intake(PREP2, packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
    os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    os_.intake(PREP2, packet('y-claim-again', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
    both = outcome(os_, K('A1Y'), 'claim repeated after A1X arrived')
    return 'WEAK' if both or K('A1Y') not in held_under(os_) else 'OK'


@probe('X01c', 'RC-03', 'control for X01: the claim is carried inside the row (supersedes_source_id), so the bytes change')
def _():
    os_ = h.approved_locked_november()
    y_plain = [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y-plain', y_plain + [stmt(y_plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    r = show('A1Y re-sent with supersedes_source_id=A1X inside the row', attempt(os_.intake, PREP2, packet('y-claim', [tx('A1Y', '2026-12-03', '40.00', supersedes_source_id='A1X')])))
    print('    claim recorded as an event:', events(os_, 'SOURCE_SUPERSESSION'))
    os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    both = outcome(os_, K('A1Y'), 'A1X arrives', approve_fully)
    return 'WEAK' if both or K('A1Y') not in held_under(os_) else 'OK'


@probe('X01d', 'RC-03', 'X01 with the claimant already approved in December when the unchanged row is re-sent with its claim')
def _():
    os_ = h.approved_locked_november()
    y_plain = [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y-plain', y_plain + [stmt(y_plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    show('A1Y approved in December before any claim', review(os_, REV2, gov(os_, K('A1Y'), '2026-12'), 'approve'))
    os_.intake(PREP2, packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
    os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    run(os_, 'card_preparation', '2026-12', PREP2)
    a = gov(os_, K('A1Y'), '2026-12'); both = twice(os_, K('A1'), K('A1Y'))
    print('    December A1Y: %s | held: %s | events: %s' % (brief(a), sorted(held_under(os_)), events(os_)))
    fin = show('finalize December without acknowledgement', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe')) if both else None
    print('    approved in both periods with no new decision: %s' % both)
    return 'WEAK' if both else 'OK'


@probe('X02', 'RC-03', 'the claimant is revised (claim not repeated) while its claim is still unresolved; the target then arrives and is held')
def _():
    out = {}
    for repeat in (False, True):
        os_ = h.approved_locked_november()
        y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
        y2 = [sup('A1Y', '2026-12-03', '41.00', 'A1X') if repeat else tx('A1Y', '2026-12-03', '41.00'), rc('A1Y', '2026-12-03', '41.00')]
        os_.intake(PREP2, packet('y-rev', y2 + [stmt(y2, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
        print('    [claim repeated=%s] revised A1Y: %s' % (repeat, brief(gov(os_, K('A1Y'), '2026-12'))))
        os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
        out[repeat] = outcome(os_, K('A1Y'), '[claim repeated=%s] A1X arrives' % repeat, approve_fully)
    return 'WEAK' if any(out.values()) else 'OK'


@probe('X03', 'RC-01+RC-03', 'withdrawn locked root and an unresolved claim together: B1 claims A1X before A1X arrives; A1X claims the withdrawn A1')
def _():
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('void', [dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')]))
    b = [sup('B1', '2026-12-03', '40.00', 'A1X'), rc('B1', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(b, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    os_.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    both = outcome(os_, K('B1'), 'A1X arrives')
    return 'WEAK' if both or not {K('B1'), K('A1X')} <= held_under(os_) else 'OK'


@probe('X04', 'RC-01+RC-02', 'withdrawn locked root and a late middle link together: C1 replaces B1 in December, A1 is withdrawn, B1 then claims A1')
def _():
    out = {}
    for pre_approved in (False, True):
        os_ = h.approved_locked_november()
        b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
        c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('b', b + [stmt(c, DEC, opening='100.00')])); os_.intake(PREP2, packet('c', c)); run(os_, 'card_preparation', '2026-12', PREP2)
        if pre_approved:
            try_to_approve(os_, K('C1'))
        os_.intake(PREP2, packet('void', [dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')]))
        os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')]))
        both = outcome(os_, K('C1'), '[pre_approved=%s] B1 claims the withdrawn A1' % pre_approved)
        out[pre_approved] = both or not {K('C1'), K('B1')} <= held_under(os_)
    return 'WEAK' if any(out.values()) else 'OK'


@probe('X05', 'RC-02', 'the late middle link and the terminal source arrive in one batch, terminal listed first')
def _():
    os_ = h.approved_locked_november()
    b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(c, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    os_.intake(PREP2, packet('both', c + [sup('B1', '2026-12-02', '40.00', 'A1')]))
    both = outcome(os_, K('C1'), 'C1 and the late link on B1 in one batch')
    return 'WEAK' if both or not {K('C1'), K('B1')} <= held_under(os_) else 'OK'


@probe('X06', 'RC-02', 'four-deep chain: the late link is declared two levels above the admitted terminal source')
def _():
    os_ = h.approved_locked_november()
    b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
    d = [sup('D1', '2026-12-04', '40.00', 'C1'), rc('D1', '2026-12-04', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(d, DEC, opening='100.00')])); os_.intake(PREP2, packet('c', c)); os_.intake(PREP2, packet('d', d)); run(os_, 'card_preparation', '2026-12', PREP2)
    try_to_approve(os_, K('D1'))
    os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')]))
    both = outcome(os_, K('D1'), 'B1 claims A1 with C1 and D1 above it')
    held = {K('D1'), 'receipt-D1'} <= held_under(os_)
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    d1 = gov(os_, K('D1'), '2026-12')
    print('    after reopen -> December: %s | D1: %s' % (card_gov(os_), brief(d1)))
    released = card_gov(os_) == [K('D1')] and gov(os_, K('A1'), '2026-11') is None and d1 is not None and d1['review_status'] != 'approve'
    return 'OK' if not both and held and released else 'WEAK'


@probe('X07', 'RC-02', 'a second charge with its own unchanged chain in December is untouched when another chain is quarantined')
def _():
    os_ = h.approved_locked_november()
    b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
    m = [tx('M1', '2026-12-08', '22.00'), rc('M1', '2026-12-08', '22.00')]
    n = [sup('N1', '2026-12-09', '22.00', 'M1'), rc('N1', '2026-12-09', '22.00')]
    os_.intake(PREP2, packet('b', b + m + [stmt(c + n, DEC, opening='100.00')])); os_.intake(PREP2, packet('cn', c + n)); run(os_, 'card_preparation', '2026-12', PREP2)
    try_to_approve(os_, K('N1'))
    was = gov(os_, K('N1'), '2026-12'); ev_before = [e for e in events(os_) if e[2] in (K('N1'), K('M1'))]
    os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')])); run(os_, 'card_preparation', '2026-12', PREP2)
    now = gov(os_, K('N1'), '2026-12'); ev_after = [e for e in events(os_) if e[2] in (K('N1'), K('M1'))]
    print('    N1 before: %s | after: %s | held: %s' % (brief(was), brief(now), sorted(held_under(os_))))
    print('    N1/M1 events before: %s | after: %s' % (ev_before, ev_after))
    # The December statement names C1, which has just left December, so a statement blocker on every December
    # item is the expected, separate control. The chain control must leave N1 in December with no move row.
    ok = (now is not None and K('N1') not in held_under(os_) and {K('C1'), K('B1')} <= held_under(os_)
          and not any(mv[0] in (K('N1'), K('M1'), 'receipt-N1') for mv in moves(os_))
          and rb.MOVED not in now['blockers'] and all(b.startswith('STATEMENT_') for b in now['blockers']))
    return 'OK' if ok else 'WEAK'


@probe('X08', 'RC-01', 'the withdrawal is admitted on reopen and November is relocked; a new replacement then claims the withdrawn charge')
def _():
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('void', [dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')]))
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11')
    print('    after reopen -> November governing: %s | exceptions: %s' % (governing_keys(os_, '2026-11'), exceptions_of(os_)))
    approve_pending(os_)
    show('relock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'probe acknowledgement'))
    b = [sup('B1', '2026-12-02', '40.00', 'A1'), rc('B1', '2026-12-02', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(b, DEC, opening='100.00')]))
    both = outcome(os_, K('B1'), 'B1 claims the validly withdrawn A1 after the relock')
    a1 = gov(os_, K('A1'), '2026-11'); b1 = gov(os_, K('B1'), '2026-12')
    if both:
        return 'WEAK'
    # A1 is no longer in the November books; B1 may be admitted (released) or conservatively held. Both are single-period.
    print('    reading: A1 governing in November: %s | B1 in December: %s' % (a1 is not None, b1 is not None))
    return ('NOTE' if a1 is None and b1 is None else 'OK') if a1 is None or b1 is None else 'WEAK'


@probe('X09', 'RC-03', 'restart: the pending claim survives a new service instance on the same database and is resolved when the target arrives')
def _():
    os_ = h.approved_locked_november()
    y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    path = os_.probe_path
    os2 = rb.AccountingOS(path, [h.SCOPE]); os2.probe_path = path
    os2.intake(PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    both = outcome(os2, K('A1Y'), 'after restart A1X arrives')
    return 'WEAK' if both or K('A1Y') not in held_under(os2) else 'OK'


def main():
    wanted = set(sys.argv[2:])
    results = {}
    for pid, ticket, title, fn in PROBES:
        if wanted and pid not in wanted:
            continue
        print('%s [%s] %s' % (pid, ticket, title))
        try:
            verdict = fn()
        except Exception:
            traceback.print_exc(file=sys.stdout)
            verdict = 'ERROR'
        results[pid] = (ticket, verdict)
        print('    => %s\n' % verdict)
    print('SUMMARY')
    for pid, (ticket, verdict) in results.items():
        print('%-6s %-12s %s' % (pid, ticket, verdict))
    print(json.dumps({'counts': {v: sum(1 for x in results.values() if x[1] == v) for v in ('OK', 'WEAK', 'NOTE', 'ERROR')}}))
    h.TMP.cleanup()
    return 1 if any(v in ('WEAK', 'ERROR') for _, v in results.values()) else 0


if __name__ == '__main__':
    sys.exit(main())
