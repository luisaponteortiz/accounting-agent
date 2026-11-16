"""Fable acceptance probes for the RD-01 and RD-02 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_rd_acceptance_probes.py <project-root> [PROBE_ID ...]

Drives the application in <project-root> through public service operations only. Temporary
SQLite files, fictional data, no network, model, posting or payment. Table contents are read
from the probe's own temporary database, read-only.

Helpers are loaded unchanged from <project-root>/exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py
(which loads the RB and RA helpers), so all four scripts build identical fixtures.

Part 1 (Y..) states every acceptance assertion of RD-01 and RD-02 as an explicit check, including
the state BEFORE the target arrives, which probes X01/X01d/X02 only test by outcome.
Part 2 (E..) tries neighbouring deliveries that no ticket named.

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
import os
# The RC probe script is read from <project-root>; FABLE_RC_PROBES may point at an identical copy when
# the root is an earlier checkpoint that does not contain it (used only for the regression comparison).
_rc_path = Path(os.environ.get('FABLE_RC_PROBES') or ROOT / 'exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py')
_spec = importlib.util.spec_from_file_location('fable_rc_probes', _rc_path)
rcp = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_rc_path), str(ROOT)]
_spec.loader.exec_module(rcp)
sys.argv = _argv
rb, h = rcp.rb, rcp.h

CARD, NOV, DEC = h.CARD, h.NOV, h.DEC
PREP, PREP2, REV, REV2, REV3, FIN, PADMIN = h.PREP, h.PREP2, h.REV, h.REV2, h.REV3, h.FIN, h.PADMIN
tx, rc, stmt, sup, packet, run, gov = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov
review, dispose, brief, show, attempt = h.review, h.dispose, h.brief, h.show, h.attempt
exceptions_of = h.exceptions_of
events, held_under, approved, twice, try_to_approve = rb.events, rb.held_under, rb.approved, rb.twice, rb.try_to_approve
K, MOVED, TRANSITION, REVISED = rb.K, rb.MOVED, rb.TRANSITION, rb.REVISED
UNRESOLVED = 'SOURCE_TRANSITION_UNRESOLVED'
check, links, approve_fully = rcp.check, rcp.links, rcp.approve_fully
PROBES = []


def probe(pid, ticket, title):
    def register(fn):
        PROBES.append((pid, ticket, title, fn))
        return fn
    return register


def ro(os_):
    return sqlite3.connect('file:%s?mode=ro' % os_.probe_path, uri=True)


def lifecycle(os_):
    """Full contents of every table the corrections write to, batch envelopes listed apart (read-only)."""
    db = ro(os_)
    try:
        q = {'source_snapshots': "SELECT * FROM snapshots WHERE kind!='batch' ORDER BY id",
             'batch_snapshots': "SELECT * FROM snapshots WHERE kind='batch' ORDER BY id",
             'bindings': 'SELECT * FROM source_periods ORDER BY id', 'moves': 'SELECT * FROM source_moves ORDER BY id',
             'links': 'SELECT * FROM source_links ORDER BY id', 'events': 'SELECT * FROM accounting_events ORDER BY id',
             'decisions': 'SELECT * FROM decisions ORDER BY id', 'heads': 'SELECT * FROM source_heads ORDER BY scope,kind,source_key',
             'artifacts': 'SELECT * FROM artifacts ORDER BY id', 'packages': 'SELECT * FROM packages ORDER BY id',
             'audit': 'SELECT * FROM audit ORDER BY id'}
        out = {}
        for name, sql in q.items():
            try:
                out[name] = [tuple(r) for r in db.execute(sql)]
            except sqlite3.OperationalError as exc:
                out[name] = 'unreadable: %s' % exc
        return out
    finally:
        db.close()


def delta(before, after):
    return {k: (len(after[k]) - len(before[k])) if isinstance(after[k], list) and isinstance(before[k], list) else '?' for k in after}


def prefix_kept(before, after, tables):
    """True when every earlier row of the named tables is still present, byte for byte, as a prefix."""
    return all(after[t][:len(before[t])] == before[t] for t in tables)


def unresolved_events(os_, key):
    return [e for e in os_.export(PREP)['accounting_events'] if e['code'] == 'SOURCE_SUPERSESSION_UNRESOLVED' and e['item_key'] == key]


def y_plain():
    return [tx('A1Y', '2026-12-03', '40.00'), rc('A1Y', '2026-12-03', '40.00')]


def x_rows():
    return [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]


def prep(os_):
    run(os_, 'card_preparation', '2026-12', PREP2)


# =======================================================================================
# Part 1. The acceptance assertions of RD-01 and RD-02, one check each
# =======================================================================================

@probe('Y01', 'RD-01', 'unchanged row re-sent with a claim on an unknown target: recorded once, both blockers before the target, held after; eligible and approved')
def _():
    good = True
    for was_approved in (False, True):
        tag = '[approved before]' if was_approved else '[eligible]'
        os_ = h.approved_locked_november()
        os_.intake(PREP2, packet('y-plain', y_plain() + [stmt(y_plain(), DEC, opening='100.00')])); prep(os_)
        prior = gov(os_, K('A1Y'), '2026-12')
        good &= check('%s A1Y is eligible in December before any claim' % tag, prior['eligible'])
        if was_approved:
            show('%s A1Y approved in December' % tag, review(os_, REV2, prior, 'approve'))
            good &= check('%s A1Y approved and governing before the claim' % tag, approved(os_, K('A1Y'), '2026-12'))
        before = lifecycle(os_)
        r = show('%s A1Y re-sent unchanged with supersedes=A1X (not received)' % tag, attempt(os_.intake, PREP2, packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')])))
        after = lifecycle(os_); d = delta(before, after)
        print('    %s row deltas after the claim: %s' % (tag, d))
        good &= check('%s the intake answers changed=True' % tag, r[0] == 'ok' and r[1]['changed'] is True)
        good &= check('%s exactly one new source version' % tag, d['source_snapshots'] == 1)
        good &= check('%s exactly one SOURCE_SUPERSESSION_UNRESOLVED event for A1Y' % tag, len(unresolved_events(os_, K('A1Y'))) == 1)
        good &= check('%s no link yet' % tag, d['links'] == 0)
        good &= check('%s earlier snapshots, decisions, artifacts, audit rows are an unchanged prefix' % tag, prefix_kept(before, after, ('source_snapshots', 'batch_snapshots', 'decisions', 'artifacts', 'audit', 'events', 'bindings', 'moves')))
        # state BEFORE the target arrives, first without re-preparing, then after re-preparing
        stale = gov(os_, K('A1Y'), '2026-12')
        print('    %s governing A1Y straight after the claim (no new run): %s' % (tag, brief(stale)))
        if was_approved:
            good &= check('%s the earlier approval no longer governs, even before a new run' % tag, not approved(os_, K('A1Y'), '2026-12'))
            fin = show('%s finalize December before re-preparing' % tag, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
            good &= check('%s December cannot be finalized on the earlier approval' % tag, fin[0] == 'refused')
        prep(os_)
        y = gov(os_, K('A1Y'), '2026-12')
        print('    %s A1Y after re-preparing, target still unknown: %s' % (tag, brief(y)))
        good &= check('%s both transition blockers before the target arrives' % tag, y is not None and {TRANSITION, UNRESOLVED} <= set(y['blockers']))
        good &= check('%s A1Y is not eligible and not approved' % tag, y is not None and not y['eligible'] and y['review_status'] != 'approve')
        rv = show('%s independent approval attempt while unresolved' % tag, review(os_, REV3, y, 'approve'))
        good &= check('%s approval refused while unresolved' % tag, rv[0] == 'refused')
        dv = show('%s settlement_verified attempt while unresolved' % tag, dispose(os_, K('A1Y'), TRANSITION, 'settlement_verified', period='2026-12'))
        prep(os_); y = gov(os_, K('A1Y'), '2026-12')
        good &= check('%s the unresolved blocker cannot be cleared by a disposition' % tag, y is not None and UNRESOLVED in y['blockers'] and not y['eligible'])
        fin = show('%s finalize December while unresolved' % tag, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        good &= check('%s December cannot be finalized while unresolved' % tag, fin[0] == 'refused')
        n_approvals = rcp.approvals_kept(os_, K('A1Y'))
        mid = lifecycle(os_)
        os_.intake(PREP2, packet('x', x_rows())); prep(os_)
        end = lifecycle(os_)
        ev = os_.export(PREP)['accounting_events']
        print('    %s after A1X: held=%s links=%s' % (tag, sorted(held_under(os_)), links(os_)))
        good &= check('%s December has no governing artifact for A1Y' % tag, gov(os_, K('A1Y'), '2026-12') is None)
        good &= check('%s A1Y and its receipt are held under November as MOVED' % tag, {K('A1Y'), 'receipt-A1Y'} <= held_under(os_))
        good &= check('%s A1X and its receipt are held under November as MOVED' % tag, {K('A1X'), 'receipt-A1X'} <= held_under(os_))
        good &= check('%s A1 is still approved and governing in November' % tag, approved(os_, K('A1'), '2026-11'))
        good &= check('%s links are A1->A1X and A1X->A1Y' % tag, set(links(os_)) == {(K('A1'), K('A1X')), (K('A1X'), K('A1Y'))})
        if was_approved:
            named = [e for e in ev if e['code'].startswith('APPROVED_SOURCE_') and json.loads(e['payload']).get('artifact_id') == prior['id']]
            print('    %s approved-source events naming the December approval: %s' % (tag, sorted({(e['code'], e['period_id'], e['item_key']) for e in named})))
            good &= check('%s an approved-source event names the former December approval' % tag, bool(named))
            good &= check('%s ITEM_LEFT_POPULATION recorded for A1Y' % tag, any(e['code'] == 'ITEM_LEFT_POPULATION' and e['item_key'] == K('A1Y') for e in ev))
            good &= check('%s the approval decision remains (%d)' % (tag, n_approvals), rcp.approvals_kept(os_, K('A1Y')) == n_approvals >= 1)
        good &= check('%s no earlier snapshot, decision, artifact, event or audit row rewritten' % tag, prefix_kept(mid, end, ('source_snapshots', 'batch_snapshots', 'decisions', 'artifacts', 'audit', 'events', 'bindings', 'moves', 'links')))
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
        fin = show('%s finalize December after the hold' % tag, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        good &= check('%s not approved in both periods' % tag, not twice(os_, K('A1'), K('A1Y')))
    return 'OK' if good else 'WEAK'


@probe('Y02', 'RD-01', 'the same unresolved claim repeated twice in new envelopes, then an exact packet replay')
def _():
    good = True
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y-plain', y_plain() + [stmt(y_plain(), DEC, opening='100.00')])); prep(os_)
    claim = packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')])
    good &= check('first claim: changed=True', os_.intake(PREP2, claim)['changed'] is True)
    prep(os_)
    before = lifecycle(os_)
    for name in ('y-claim-2', 'y-claim-3'):
        r = os_.intake(PREP2, dict(claim, batch_id=name)); after = lifecycle(os_); d = delta(before, after)
        print('    repeat %s -> %s ; deltas %s' % (name, r, d))
        good &= check('%s: changed=False and not a replay' % name, r['changed'] is False and r['replay'] is False)
        good &= check('%s: no source snapshot, binding, move, link, decision or accounting event added' % name, all(after[t] == before[t] for t in ('source_snapshots', 'bindings', 'moves', 'links', 'events', 'decisions', 'heads', 'artifacts')))
        good &= check('%s: only the batch envelope (1) and its intake audit row are added' % name, len(after['batch_snapshots']) - len(before['batch_snapshots']) == 1)
        print('    audit rows added by %s: %d' % (name, len(after['audit']) - len(before['audit'])))
        before = dict(before, batch_snapshots=after['batch_snapshots'], audit=after['audit'])
    g = gov(os_, K('A1Y'), '2026-12')
    good &= check('the governing December artifact is unchanged by the repeats (still blocked, still governing)', g is not None and UNRESOLVED in g['blockers'])
    r = os_.intake(PREP2, claim); after = lifecycle(os_)
    print('    exact replay ->', r)
    good &= check('exact packet replay: replay=True, changed=False', r['replay'] is True and r['changed'] is False)
    good &= check('exact packet replay adds no snapshot of any kind and no lifecycle row', all(after[t] == before[t] for t in ('source_snapshots', 'batch_snapshots', 'bindings', 'moves', 'links', 'events', 'decisions', 'heads')))
    good &= check('exactly one unresolved event in total', len(unresolved_events(os_, K('A1Y'))) == 1)
    return 'OK' if good else 'WEAK'


@probe('Y03', 'RD-02', 'claimant revised (amount) with and without the claim, service restarted, target arrives')
def _():
    good = True
    for repeat in (False, True):
        tag = '[claim repeated=%s]' % repeat
        os_ = h.approved_locked_november()
        y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')])); prep(os_)
        y2 = [sup('A1Y', '2026-12-03', '41.00', 'A1X') if repeat else tx('A1Y', '2026-12-03', '41.00'), rc('A1Y', '2026-12-03', '41.00')]
        os_.intake(PREP2, packet('y-rev', y2 + [stmt(y2, DEC, opening='100.00')])); prep(os_)
        a = gov(os_, K('A1Y'), '2026-12'); print('    %s revised A1Y: %s' % (tag, brief(a)))
        good &= check('%s the revised version still carries both transition blockers' % tag, a is not None and {TRANSITION, UNRESOLVED} <= set(a['blockers']))
        good &= check('%s unresolved events for A1Y: %d' % (tag, 2 if repeat else 1), len(unresolved_events(os_, K('A1Y'))) == (2 if repeat else 1))
        show('%s revised_evidence_accepted' % tag, dispose(os_, K('A1Y'), REVISED, 'revised_evidence_accepted', period='2026-12')); prep(os_)
        a = gov(os_, K('A1Y'), '2026-12')
        good &= check('%s accepting the revised evidence does not release the unresolved hold' % tag, a is not None and UNRESOLVED in a['blockers'] and not a['eligible'])
        path, scopes, probe_path = os_.store.path, os_.allowed_scopes, os_.probe_path
        os_ = type(os_)(path, scopes); os_.probe_path = probe_path                      # restart: a new service on the same file
        a = gov(os_, K('A1Y'), '2026-12')
        good &= check('%s after a restart the hold is still shown' % tag, a is not None and UNRESOLVED in a['blockers'])
        os_.intake(PREP2, packet('x', x_rows())); prep(os_)
        print('    %s after A1X: held=%s links=%s' % (tag, sorted(held_under(os_)), links(os_)))
        good &= check('%s A1Y and its receipt held under November' % tag, {K('A1Y'), 'receipt-A1Y'} <= held_under(os_) and gov(os_, K('A1Y'), '2026-12') is None)
        db = ro(os_)
        try:
            head = db.execute('SELECT snapshot_id FROM source_heads WHERE source_key=?', (K('A1Y'),)).fetchone()[0]
            linked = [r[0] for r in db.execute('SELECT new_snapshot_id FROM source_links l JOIN snapshots n ON n.id=l.new_snapshot_id WHERE n.source_key=?', (K('A1Y'),))]
        finally:
            db.close()
        good &= check('%s the link is on the CURRENT head of A1Y' % tag, linked == [head])
        approve_fully(os_, K('A1Y'))
        good &= check('%s not approved in both periods' % tag, not twice(os_, K('A1'), K('A1Y')))
    return 'OK' if good else 'WEAK'


@probe('Y04', 'RD-02', 'claimant retired by its own replacement and re-sent without the claim: orders Yc Z Yp X and Z Yc Yp X')
def _():
    good = True
    d = {'Yc': lambda: [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')],
         'Z': lambda: [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')],
         'Yp': y_plain, 'X': x_rows}
    for order in (('Yc', 'Z', 'Yp', 'X'), ('Z', 'Yc', 'Yp', 'X')):
        tag = '[%s]' % ' '.join(order)
        os_ = h.approved_locked_november()
        for i, step in enumerate(order[:3]):
            os_.intake(PREP2, packet('s%d' % i, d[step]()))
            db = ro(os_)
            try:
                heads = {r[0].split(':')[-1]: r[1] for r in db.execute("SELECT source_key,removed FROM source_heads WHERE kind='transaction' AND source_key LIKE ?", (CARD + ':A1_',))}
            finally:
                db.close()
            print('    %s after %s: removed flags %s, unresolved events for A1Y: %d' % (tag, step, heads, len(unresolved_events(os_, K('A1Y')))))
        rows = [tx('A1Z', '2026-12-04', '40.00')]
        os_.intake(PREP2, packet('statement', [stmt(rows, DEC, opening='100.00')])); prep(os_)
        z = gov(os_, K('A1Z'), '2026-12'); yv = gov(os_, K('A1Y'), '2026-12')
        print('    %s before A1X: A1Z %s | A1Y %s' % (tag, brief(z), brief(yv)))
        good &= check('%s before the target: no member of the chain is eligible without a transition blocker' % tag, all(a is None or TRANSITION in a['blockers'] for a in (z, yv)))
        good &= check('%s before the target: A1Y, if in the population, shows the unresolved hold' % tag, yv is None or UNRESOLVED in yv['blockers'])
        os_.intake(PREP2, packet('x', d['X']())); prep(os_)
        print('    %s after A1X: held=%s links=%s' % (tag, sorted(held_under(os_)), links(os_)))
        good &= check('%s the claim resolved onto A1Y (link A1X->A1Y exists)' % tag, (K('A1X'), K('A1Y')) in links(os_))
        good &= check('%s A1Z and its receipt held under November' % tag, {K('A1Z'), 'receipt-A1Z'} <= held_under(os_))
        for k in ('A1X', 'A1Y', 'A1Z'):
            approve_fully(os_, K(k))
        dec = [k for k in ('A1X', 'A1Y', 'A1Z') if approved(os_, K(k), '2026-12')]
        good &= check('%s no chain member approved in December (%s)' % (tag, dec), not dec)
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('Y05', 'RD-02', 'most recent target wins; open target; cycle refusal; already linked identity; unrelated intake')
def _():
    good = True
    # (a) most recent target
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('first', [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]))
    os_.intake(PREP2, packet('retarget', [sup('A1Y', '2026-12-03', '40.00', 'A1W')]))
    good &= check('(a) re-declaring a different unknown target records a second claim', len(unresolved_events(os_, K('A1Y'))) == 2)
    os_.intake(PREP2, packet('old-target', [tx('A1X', '2026-12-02', '40.00'), rc('A1X', '2026-12-02', '40.00')]))
    good &= check('(a) the earlier target arriving creates no link', links(os_) == [])
    os_.intake(PREP2, packet('new-target', [sup('A1W', '2026-12-02', '40.00', 'A1'), rc('A1W', '2026-12-02', '40.00')])); prep(os_)
    print('    (a) links=%s held=%s' % (links(os_), sorted(held_under(os_))))
    good &= check('(a) the latest target is linked and A1Y is held under November', (K('A1W'), K('A1Y')) in links(os_) and K('A1Y') in held_under(os_))
    # (b) open target: the claimed row is an ordinary December row
    os_ = h.approved_locked_november()
    y = [sup('A1Y', '2026-12-03', '40.00', 'B9'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')]))
    os_.intake(PREP2, packet('b9', [tx('B9', '2026-12-02', '40.00'), rc('B9', '2026-12-02', '40.00')])); prep(os_)
    a = gov(os_, K('A1Y'), '2026-12'); b = gov(os_, K('B9'), '2026-12')
    print('    (b) A1Y %s | B9 %s | links %s | held %s' % (brief(a), brief(b), links(os_), sorted(held_under(os_))))
    good &= check('(b) open target: linked, the target is retired, the claimant stays in December with a review blocker and no hold', (K('B9'), K('A1Y')) in links(os_) and b is None and a is not None and TRANSITION in a['blockers'] and UNRESOLVED not in a['blockers'] and not held_under(os_))
    # (c) cycle
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y', [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]))
    r = show('(c) A1X arrives claiming A1Y, which claims A1X', attempt(os_.intake, PREP2, packet('x', [sup('A1X', '2026-12-02', '40.00', 'A1Y'), rc('A1X', '2026-12-02', '40.00')])))
    print('    (c) links=%s' % links(os_))
    good &= check('(c) at most one direction is linked', len(links(os_)) <= 1)
    r2 = show('(c) A1Y repeats its claim on A1X', attempt(os_.intake, PREP2, packet('y-again', [sup('A1Y', '2026-12-03', '40.00', 'A1X')])))
    good &= check('(c) the closing claim is refused or ignored; still at most one link', len(links(os_)) <= 1)
    # (d) already linked identity: nothing is resolved a second time by unrelated intake
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y', [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]))
    os_.intake(PREP2, packet('x', x_rows())); prep(os_)
    before = lifecycle(os_)
    r = os_.intake(PREP2, packet('unrelated', [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')])); after = lifecycle(os_)
    chain_rows = lambda L: [e for e in L['events'] if e[4].startswith('APPROVED_SOURCE_') or e[4].startswith('SOURCE_SUPERSESSION') or e[4] == 'ITEM_LEFT_POPULATION'] if all(isinstance(e[4], str) for e in L['events']) else None
    good &= check('(d) unrelated intake adds no link, move or chain binding', after['links'] == before['links'] and after['moves'] == before['moves'])
    db = ro(os_)
    try:
        n_chain = db.execute("SELECT COUNT(*) FROM accounting_events WHERE code LIKE 'APPROVED_SOURCE_%' OR code LIKE 'SOURCE_SUPERSESSION%' OR code='ITEM_LEFT_POPULATION'").fetchone()[0]
        chain_binds = db.execute("SELECT COUNT(*) FROM source_periods b JOIN snapshots s ON s.id=b.snapshot_id WHERE s.source_key IN (?,?,?,?)", (K('A1Y'), K('A1X'), 'receipt-A1Y', 'receipt-A1X')).fetchone()[0]
    finally:
        db.close()
    os_.intake(PREP2, packet('unrelated-2', [tx('D2', '2026-12-06', '16.00'), rc('D2', '2026-12-06', '16.00')]))
    db = ro(os_)
    try:
        n_chain2 = db.execute("SELECT COUNT(*) FROM accounting_events WHERE code LIKE 'APPROVED_SOURCE_%' OR code LIKE 'SOURCE_SUPERSESSION%' OR code='ITEM_LEFT_POPULATION'").fetchone()[0]
        chain_binds2 = db.execute("SELECT COUNT(*) FROM source_periods b JOIN snapshots s ON s.id=b.snapshot_id WHERE s.source_key IN (?,?,?,?)", (K('A1Y'), K('A1X'), 'receipt-A1Y', 'receipt-A1X')).fetchone()[0]
    finally:
        db.close()
    good &= check('(d) a second unrelated intake adds no chain event (%d) and no chain binding (%d)' % (n_chain, chain_binds), n_chain2 == n_chain and chain_binds2 == chain_binds)
    # (e) release and relock, then unrelated intake
    show('(e) reopen November', attempt(os_.reopen_period, PADMIN, '2026-11', 'probe reopen'))
    os_.intake(PREP2, packet('unrelated-3', [tx('D3', '2026-12-07', '17.00'), rc('D3', '2026-12-07', '17.00')]))
    rl = show('(e) relock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock'))
    if rl[0] == 'refused':
        rl = show('(e) relock November with acknowledgement', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'Fictional probe acknowledgement of unsettled preparation'))
    good &= check('(e) November is locked again', rl[0] == 'ok')
    print('    (e) held after relock: %s' % sorted(held_under(os_)))
    mid = lifecycle(os_)
    os_.intake(PREP2, packet('unrelated-4', [tx('D4', '2026-12-08', '18.00'), rc('D4', '2026-12-08', '18.00')]))
    end = lifecycle(os_)
    chain = lambda L: [b for b in L['bindings'] if b[2] in chain_ids]
    db = ro(os_)
    try:
        chain_ids = {r[0] for r in db.execute("SELECT id FROM snapshots WHERE source_key IN (?,?,?,?,?)", (K('A1'), K('A1Y'), K('A1X'), 'receipt-A1Y', 'receipt-A1X'))}
    finally:
        db.close()
    good &= check('(e) after release and relock, unrelated intake adds no link, move or chain binding', end['links'] == mid['links'] and end['moves'] == mid['moves'] and chain(end) == chain(mid))
    return 'OK' if good else 'WEAK'


@probe('Y06', 'RD-01', 'finalized packages: November finalized and locked, December finalized with A1Y approved, then the late claim and its target')
def _():
    good = True
    os_ = h.new_os(periods=(NOV, DEC))
    h.clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, K(k)), 'approve')
    f1 = show('finalize November', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe'))
    os_.lock_period(PADMIN, '2026-11', 'probe lock')
    os_.intake(PREP2, packet('y-plain', y_plain() + [stmt(y_plain(), DEC, opening='100.00')])); prep(os_)
    show('A1Y approved in December', review(os_, REV2, gov(os_, K('A1Y'), '2026-12'), 'approve'))
    f2 = show('finalize December', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    good &= check('both packages finalized before the claim', f1[0] == 'ok' and f2[0] == 'ok')
    before = lifecycle(os_)
    r = os_.intake(PREP2, packet('y-claim', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
    mid = lifecycle(os_)
    pfc = lambda L: [(e[2], e[3]) for e in L['events'] if e[4] == 'POST_FINALIZATION_CHANGE']
    print('    after the claim: changed=%s | package rows %d -> %d | POST_FINALIZATION_CHANGE (period, item): %s' % (r['changed'], len(before['packages']), len(mid['packages']), pfc(mid)))
    good &= check('the claim is recorded (changed=True, one unresolved event)', r['changed'] is True and len(unresolved_events(os_, K('A1Y'))) == 1)
    good &= check('no package row is rewritten or added by the claim', mid['packages'] == before['packages'])
    good &= check('a POST_FINALIZATION_CHANGE event is recorded for December before the target arrives', any(p == '2026-12' for p, _ in pfc(mid)))
    good &= check('no POST_FINALIZATION_CHANGE event for locked November from the claim', not any(p == '2026-11' for p, _ in pfc(mid)))
    good &= check('the December approval no longer governs', not approved(os_, K('A1Y'), '2026-12'))
    os_.intake(PREP2, packet('x', x_rows())); prep(os_)
    end = lifecycle(os_)
    print('    after A1X: held=%s | POST_FINALIZATION_CHANGE: %s' % (sorted(held_under(os_)), pfc(end)))
    good &= check('A1Y and its receipt are held under November', {K('A1Y'), 'receipt-A1Y'} <= held_under(os_) and gov(os_, K('A1Y'), '2026-12') is None)
    good &= check('A1 still approved and governing in November', approved(os_, K('A1'), '2026-11'))
    good &= check('no package, snapshot, decision, artifact, event or audit row rewritten', end['packages'][:len(before['packages'])] == before['packages'] and prefix_kept(before, end, ('source_snapshots', 'batch_snapshots', 'decisions', 'artifacts', 'audit', 'events', 'bindings', 'moves', 'links')))
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    st = os_.export(PREP)
    print('    packages in export: %s' % [(p.get('id'), p.get('period_id'), p.get('status')) for p in st.get('packages', [])])
    return 'OK' if good else 'WEAK'


# =======================================================================================
# Part 2. Neighbouring deliveries that no ticket named
# =======================================================================================

@probe('E01', 'RD-01', 'the unchanged row that receives the late claim sits in a LOCKED period (A1 itself claims an unknown row)')
def _():
    os_ = h.approved_locked_november()
    before = lifecycle(os_)
    a0 = gov(os_, K('A1'), '2026-11')
    r = show('A1 re-sent unchanged with supersedes=A0 (not received)', attempt(os_.intake, PREP2, packet('a1-claim', [sup('A1', '2026-11-03', '40.00', 'A0')])))
    after = lifecycle(os_)
    a1 = gov(os_, K('A1'), '2026-11')
    print('    deltas: %s' % delta(before, after))
    print('    November A1 before: %s | after: %s' % (brief(a0), brief(a1)))
    print('    exceptions: %s' % exceptions_of(os_))
    print('    events: %s' % events(os_))
    still = approved(os_, K('A1'), '2026-11')
    print('    A1 still approved and governing in locked November: %s' % still)
    return 'OK' if still else 'NOTE'


@probe('E02', 'RD-01', 'an identity that already has a link declares a second claim on an unknown row, repeatedly')
def _():
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('x', x_rows()))
    os_.intake(PREP2, packet('y', [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')])); prep(os_)
    base = lifecycle(os_)
    out = []
    for i in range(3):
        before = lifecycle(os_)
        r = attempt(os_.intake, PREP2, packet('y-second-claim-%d' % i, [sup('A1Y', '2026-12-03', '40.00', 'A1W')]))
        d = delta(before, lifecycle(os_)); out.append((r[1] if r[0] == 'ok' else r, {k: v for k, v in d.items() if v}))
        print('    repeat %d -> %s ; deltas %s' % (i, out[-1][0], out[-1][1]))
    prep(os_)
    a = gov(os_, K('A1Y'), '2026-12')
    print('    A1Y in December: %s | held: %s | unresolved events for A1Y: %d' % (brief(a), sorted(held_under(os_)), len(unresolved_events(os_, K('A1Y')))))
    os_.intake(PREP2, packet('w', [tx('A1W', '2026-12-01', '40.00'), rc('A1W', '2026-12-01', '40.00')])); prep(os_)
    print('    after A1W arrives: links=%s held=%s' % (links(os_), sorted(held_under(os_))))
    idempotent = all(not o[1].get('source_snapshots') and not o[1].get('events') for o in out[1:])
    print('    repeats after the first are lifecycle no-ops: %s' % idempotent)
    safe = K('A1Y') in held_under(os_) and not approved(os_, K('A1Y'), '2026-12')
    print('    A1Y still held under November: %s' % safe)
    return 'OK' if idempotent and safe else ('NOTE' if safe else 'WEAK')


@probe('E03', 'RD-01', 'the claim arrives in a message ORDERED BEFORE the governing version (provider sequence), delivered late')
def _():
    out = {}
    for variant in ('unknown-target', 'known-target'):
        os_ = h.approved_locked_november()
        y = [tx('A1Y', '2026-12-03', '40.00', as_of=5), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y-seq5', y + [stmt(y, DEC, opening='100.00')])); prep(os_)
        if variant == 'known-target':
            claim = dict(tx('A1Y', '2026-12-03', '40.00', as_of=4), supersedes=K('A1'))
            r = show('[%s] A1Y sequence 4 (older) delivered late with supersedes=A1' % variant, attempt(os_.intake, PREP2, packet('y-seq4', [claim])))
        else:
            claim = dict(tx('A1Y', '2026-12-03', '40.00', as_of=4), supersedes=K('A1X'))
            r = show('[%s] A1Y sequence 4 (older) delivered late with supersedes=A1X (not received)' % variant, attempt(os_.intake, PREP2, packet('y-seq4', [claim])))
            os_.intake(PREP2, packet('x', x_rows()))
        prep(os_)
        print('    [%s] events: %s' % (variant, [e for e in events(os_) if 'SUPERSESSION' in e[0] or 'APPROVED_SOURCE' in e[0]]))
        print('    [%s] links: %s | held: %s | A1Y: %s' % (variant, links(os_), sorted(held_under(os_)), brief(gov(os_, K('A1Y'), '2026-12'))))
        approve_fully(os_, K('A1Y'))
        out[variant] = twice(os_, K('A1'), K('A1Y'))
        if out[variant]:
            show('[%s] finalize December without acknowledgement' % variant, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        print('    [%s] approved in both periods: %s' % (variant, out[variant]))
    return 'WEAK' if any(out.values()) else 'OK'


@probe('E04', 'RD-02', 'the claimant is withdrawn by the feed (tombstone) while its claim is unresolved, then re-sent plain; target arrives last')
def _():
    out = {}
    for resend in (True, False):
        os_ = h.approved_locked_november()
        y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')]))
        os_.intake(PREP2, packet('y-gone', [dict(tx('A1Y', '2026-12-03', '40.00'), tombstone=True, removal_reason='feed_removed')]))
        if resend:
            os_.intake(PREP2, packet('y-back', y_plain()))
        os_.intake(PREP2, packet('x', x_rows())); prep(os_)
        print('    [re-sent=%s] links=%s held=%s A1Y=%s' % (resend, links(os_), sorted(held_under(os_)), brief(gov(os_, K('A1Y'), '2026-12'))))
        approve_fully(os_, K('A1Y'))
        out[resend] = twice(os_, K('A1'), K('A1Y'))
        print('    [re-sent=%s] approved in both periods: %s' % (resend, out[resend]))
    return 'WEAK' if any(out.values()) else 'OK'


@probe('E05', 'RD-01', 'the late claim on an unchanged row is declared on the RECEIPT-free path twice with a different target in between (A1X, A1W, A1X)')
def _():
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('y-plain', y_plain() + [stmt(y_plain(), DEC, opening='100.00')])); prep(os_)
    for i, t in enumerate(('A1X', 'A1W', 'A1X')):
        r = os_.intake(PREP2, packet('claim-%d' % i, [sup('A1Y', '2026-12-03', '40.00', t)]))
        print('    claim on %s -> changed=%s, unresolved events=%d' % (t, r['changed'], len(unresolved_events(os_, K('A1Y')))))
    os_.intake(PREP2, packet('w', [tx('A1W', '2026-12-01', '40.00'), rc('A1W', '2026-12-01', '40.00')]))
    print('    after A1W (the superseded target) arrives: links=%s' % links(os_))
    os_.intake(PREP2, packet('x', x_rows())); prep(os_)
    print('    after A1X arrives: links=%s held=%s' % (links(os_), sorted(held_under(os_))))
    approve_fully(os_, K('A1Y'))
    both = twice(os_, K('A1'), K('A1Y'))
    print('    approved in both periods: %s' % both)
    return 'WEAK' if both or K('A1Y') not in held_under(os_) else 'OK'


@probe('E03c', 'RD-01', 'control for E03: the same two messages delivered in provider order (sequence 4 with the claim, then sequence 5)')
def _():
    out = {}
    for variant in ('unknown-target', 'known-target'):
        os_ = h.approved_locked_november()
        target = 'A1' if variant == 'known-target' else 'A1X'
        y4 = [dict(tx('A1Y', '2026-12-03', '40.00', as_of=4), supersedes=K(target)), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y-seq4', y4 + [stmt(y4, DEC, opening='100.00')]))
        os_.intake(PREP2, packet('y-seq5', [tx('A1Y', '2026-12-03', '40.00', as_of=5)]))
        if variant == 'unknown-target':
            os_.intake(PREP2, packet('x', x_rows()))
        prep(os_)
        print('    [%s] links: %s | held: %s | A1Y: %s' % (variant, links(os_), sorted(held_under(os_)), brief(gov(os_, K('A1Y'), '2026-12'))))
        approve_fully(os_, K('A1Y'))
        out[variant] = twice(os_, K('A1'), K('A1Y')) or K('A1Y') not in held_under(os_)
        print('    [%s] approved in both periods or not held: %s' % (variant, out[variant]))
    return 'WEAK' if any(out.values()) else 'OK'


@probe('E06', 'RD-02', 'an identity already linked to an open December row later declares a claim on an unknown row that turns out to replace locked A1')
def _():
    out = {}
    for order in ('claim-before-target', 'target-before-claim'):
        os_ = h.approved_locked_november()
        b9 = [tx('B9', '2026-12-02', '40.00'), rc('B9', '2026-12-02', '40.00')]
        os_.intake(PREP2, packet('b9', b9))
        y = [sup('A1Y', '2026-12-03', '40.00', 'B9'), rc('A1Y', '2026-12-03', '40.00')]
        os_.intake(PREP2, packet('y', y + [stmt(y, DEC, opening='100.00')])); prep(os_)
        claim = lambda: os_.intake(PREP2, packet('y-claim-x', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
        if order == 'claim-before-target':
            r = claim(); os_.intake(PREP2, packet('x', x_rows()))
        else:
            os_.intake(PREP2, packet('x', x_rows())); r = claim()
        prep(os_)
        a = gov(os_, K('A1Y'), '2026-12')
        print('    [%s] claim intake %s | links=%s | held=%s | A1Y=%s | unresolved events=%d' % (order, r, links(os_), sorted(held_under(os_)), brief(a), len(unresolved_events(os_, K('A1Y')))))
        approve_fully(os_, K('A1Y'))
        out[order] = twice(os_, K('A1'), K('A1Y'))
        if out[order]:
            show('[%s] finalize December without acknowledgement' % order, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
        print('    [%s] A1 approved in November and A1Y approved in December: %s' % (order, out[order]))
    print('    outcome depends on arrival order: %s' % (out['claim-before-target'] != out['target-before-claim']))
    return 'WEAK' if any(out.values()) else 'OK'


def main():
    wanted = set(sys.argv[2:])
    results = []
    for pid, ticket, title, fn in PROBES:
        if wanted and pid not in wanted:
            continue
        print('\n=== %s [%s] %s' % (pid, ticket, title))
        try:
            verdict = fn()
        except Exception:
            traceback.print_exc(file=sys.stdout); verdict = 'ERROR'
        print('--- %s: %s' % (pid, verdict)); results.append((pid, ticket, verdict))
    print('\nSUMMARY')
    for pid, ticket, verdict in results:
        print('  %-5s %-8s %s' % (pid, ticket, verdict))
    tally = {v: sum(1 for r in results if r[2] == v) for v in ('OK', 'NOTE', 'WEAK', 'ERROR')}
    print('  totals: %s' % tally)
    h.TMP.cleanup()
    return 1 if tally['WEAK'] or tally['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
