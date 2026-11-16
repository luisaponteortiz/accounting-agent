"""Fable independent acceptance probes for RE-01..RE-03 under D-026 and owner clarification D-029.

Usage (from anywhere):
    python3 fable_re_acceptance_probes.py <project-root> [PROBE_ID ...]

Drives the application in <project-root> through public service operations only (intake, enqueue/drain,
review, disposition, lock/reopen, finalize, state/export/verify_audit). Temporary SQLite files, fictional
data, no network, model, posting or payment. Table contents are read from the probe's own temporary
database, read-only.

Fixture helpers are loaded unchanged from <project-root>/exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py
(which loads the RC, RB and RA helpers). Every scenario and assertion below is new and uses its own
identities (Q claimant, P locked-chain link, B/B2 open December rows, L late November row).

C2..  clause 2   claim on a late, older or conflicting message
C7..  clause 7   second claim naming a different target (and D-029 frozen-home boundary)
C8..  clause 8   no provider message releases a locked-period hold
C9..  clause 9   who may disposition, and what the disposition does

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
_rd_path = ROOT / 'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py'
_spec = importlib.util.spec_from_file_location('fable_rd_probes', _rd_path)
rdp = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_rd_path), str(ROOT)]
_spec.loader.exec_module(rdp)
sys.argv = _argv
h, rb, rcp = rdp.h, rdp.rb, rdp.rcp

CARD, NOV, DEC, SCOPE = h.CARD, h.NOV, h.DEC, h.SCOPE
PREP, PREP2, REV, REV2, REV3, REV4, FIN, PADMIN, DISP, ADMIN = h.PREP, h.PREP2, h.REV, h.REV2, h.REV3, h.REV4, h.FIN, h.PADMIN, h.DISP, h.ADMIN
tx, rc, stmt, sup, packet, run, gov = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov
review, dispose, brief, show, attempt, human = h.review, h.dispose, h.brief, h.show, h.attempt, h.human
exceptions_of = h.exceptions_of
held_under, approved, K = rb.held_under, rb.approved, rb.K
check, links = rcp.check, rcp.links
lifecycle, delta, prefix_kept, ro = rdp.lifecycle, rdp.delta, rdp.prefix_kept, rdp.ro
CONFLICT, CHOICE = 'SOURCE_CLAIM_CONFLICT', 'select_supersession_target'
UNRESOLVED, TRANSITION = 'SOURCE_TRANSITION_UNRESOLVED', 'SOURCE_TRANSITION_REQUIRES_REVIEW'
MOVED, LATE = 'SOURCE_MOVED_FROM_LOCKED_PERIOD', 'LATE_ACTIVITY_IN_LOCKED_PERIOD'
ROW_TABLES = ('source_snapshots', 'bindings', 'moves', 'links', 'events', 'decisions', 'heads')
HISTORY = ('source_snapshots', 'batch_snapshots', 'bindings', 'moves', 'links', 'events', 'decisions', 'artifacts', 'audit')

# Additional synthetic people. Every grant is made explicitly by grants() on the line that needs it.
DL = human('re-disposition-and-lock', 'reviewer')          # disposition + lock
DR = human('re-disposition-and-review', 'reviewer')        # disposition + review
DR2 = human('re-disposition-and-review-2', 'reviewer')     # disposition + review
S1, S1R = human('re-supplier-one', 'preparer'), human('re-supplier-one', 'reviewer')
S2, S2R = human('re-supplier-two', 'preparer'), human('re-supplier-two', 'reviewer')
S3, S3R = human('re-supplier-three', 'preparer'), human('re-supplier-three', 'reviewer')
PROBES = []


def probe(pid, clause, title):
    def register(fn):
        PROBES.append((pid, clause, title, fn))
        return fn
    return register


def grants(os_):
    os_.grant_authority(ADMIN, DL.id, ['disposition', 'lock'], 'Fictional probe authority: disposition and lock')
    os_.grant_authority(ADMIN, DR.id, ['disposition', 'review'], 'Fictional probe authority: disposition and review')
    os_.grant_authority(ADMIN, DR2.id, ['disposition', 'review'], 'Fictional probe authority: disposition and review')
    for who in (S1R, S2R, S3R):
        os_.grant_authority(ADMIN, who.id, ['disposition', 'lock'], 'Fictional probe authority for a claim supplier (refusal test)')
    return os_


def base():
    return grants(h.approved_locked_november())


def send(os_, name, rows, who=None, period_id=None):
    return attempt(os_.intake, who or PREP2, packet(name, rows, period_id))


def prep(os_, period='2026-12', who=None):
    run(os_, 'card_preparation', period, who or (PREP if period == '2026-11' else PREP2))


def q(target=None, amount='40.00', date='2026-12-03', **kw):
    row = tx('Q', date, amount, **kw)
    if target:
        row['supersedes'] = K(target)
    return row


def q_rows(target=None, **kw):
    rows = [q(target, **kw), rc('Q', '2026-12-03', '40.00')]
    return rows + [stmt(rows, DEC, opening='100.00')]


def p_rows():
    """P replaces A1, the charge approved in locked November."""
    return [sup('P', '2026-12-02', '40.00', 'A1'), rc('P', '2026-12-02', '40.00')]


def b_rows(sid='B', date='2026-12-02', amount='40.00'):
    return [tx(sid, date, amount, desc='OPEN ROW DEMO'), rc(sid, date, amount, vendor='OPEN ROW DEMO')]


def sql(os_, query, args=()):
    db = ro(os_)
    try:
        return [tuple(r) for r in db.execute(query, args)]
    finally:
        db.close()


def head(os_, sid):
    r = sql(os_, "SELECT s.id,h.removed,s.payload,m.order_type,m.as_of FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id LEFT JOIN source_metadata m ON m.snapshot_id=s.id WHERE h.kind='transaction' AND h.source_key=?", (K(sid),))
    if not r:
        return None
    return {'snapshot_id': r[0][0], 'removed': r[0][1], 'amount': json.loads(r[0][2])['amount'], 'date': json.loads(r[0][2])['date'], 'order': (r[0][3], r[0][4])}


def where(os_, key):
    """Effective binding of the identity's head: (period, admitted, reason)."""
    r = sql(os_, "SELECT b.period_id,b.admitted,b.reason FROM source_heads h JOIN source_periods b ON b.snapshot_id=h.snapshot_id WHERE h.source_key=? ORDER BY b.id DESC LIMIT 1", (key,))
    return r[0] if r else None


def claim_events(os_, sid):
    return [(c, json.loads(p)['target_key']) for c, p in sql(os_, "SELECT code,payload FROM accounting_events WHERE item_key=? AND code IN ('SOURCE_CLAIM_DECLARED','SOURCE_CLAIM_CONFLICT_RECORDED','SOURCE_CLAIM_TARGET_SELECTED','SOURCE_SUPERSESSION_UNRESOLVED') ORDER BY id", (K(sid),))]


def conflicts(os_):
    return os_.state(PREP)['source_claim_conflicts']


def ev(os_, key='receipt-Q'):
    r = sql(os_, "SELECT s.id,s.hash FROM source_heads h JOIN snapshots s ON s.id=h.snapshot_id WHERE h.source_key=?", (key,))
    return [{'snapshot_id': r[0][0], 'hash': r[0][1]}]


def select(os_, who, target, item='Q', period='2026-12', evidence=None):
    return attempt(os_.disposition, who, 'card_preparation', period, K(item), CONFLICT, CHOICE, {'target_key': K(target)},
                   ev(os_, 'receipt-' + item) if evidence is None else evidence, 'Fictional independent target selection')


def rows_of(os_):
    d = lifecycle(os_)
    return {k: d[k] for k in ROW_TABLES}


def dispositions(os_):
    return sql(os_, 'SELECT * FROM dispositions ORDER BY id')


def approval_count(os_):
    return sql(os_, "SELECT COUNT(*) FROM decisions WHERE decision IN ('approve','resolve_approve')")[0][0]


def clear_and_approve(os_, sid, period='2026-12', reviewer=None):
    """What an honest operator does next: clear the transition blocker with the full evidence, re-prepare,
    ask an independent reviewer. Returns the governing artifact afterwards."""
    a = gov(os_, K(sid), period)
    if a is None:
        return None
    if TRANSITION in a['blockers']:
        show('settlement_verified on ' + sid, dispose(os_, K(sid), TRANSITION, 'settlement_verified', period=period))
        prep(os_, period); a = gov(os_, K(sid), period)
    if a is not None and a['review_status'] != 'approve':
        show('independent approval of ' + sid, review(os_, reviewer or REV2, a, 'approve'))
    return gov(os_, K(sid), period)


# =======================================================================================
# Clause 2. Claim on a late, older or conflicting message
# =======================================================================================

@probe('C2a', 'clause 2', 'late older / same-order conflicting message carrying the first claim: known and unknown target, eligible and approved row, sequence and timestamp order, repeated')
def _():
    good = True
    for ordering in ('sequence', 'timestamp'):
        new, older = (7, 6) if ordering == 'sequence' else ('2026-12-05T10:00:00Z', '2026-12-04T10:00:00Z')
        for known in (True, False):
            for was_approved in (False, True):
                for conflicting in (False, True):
                    tag = '[%s %s %s %s]' % (ordering, 'known' if known else 'unknown', 'approved' if was_approved else 'eligible', 'same-order-conflict' if conflicting else 'older')
                    os_ = base()
                    send(os_, 'c2a-plain', q_rows(as_of=new)); prep(os_)
                    if was_approved:
                        r = review(os_, REV2, gov(os_, K('Q'), '2026-12'), 'approve')
                        good &= check('%s Q approved and governing before the late claim' % tag, r[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
                    before_head = head(os_, 'Q'); before = lifecycle(os_)
                    late = q('A1' if known else 'P', amount='41.00' if conflicting else '40.00', as_of=new if conflicting else older)
                    r = send(os_, 'c2a-late', [late])
                    after = lifecycle(os_)
                    good &= check('%s intake answers changed=True' % tag, r[0] == 'ok' and r[1]['changed'] is True)
                    good &= check('%s governing head is unchanged (same snapshot, amount, order)' % tag, head(os_, 'Q') == before_head)
                    good &= check('%s the late message is kept as evidence (one new source version)' % tag, delta(before, after)['source_snapshots'] == 1)
                    good &= check('%s claim recorded exactly once' % tag, [c for c in claim_events(os_, 'Q') if c[0] == 'SOURCE_CLAIM_DECLARED'] == [('SOURCE_CLAIM_DECLARED', K('A1' if known else 'P'))])
                    good &= check('%s earlier history is an unchanged prefix' % tag, prefix_kept(before, after, HISTORY))
                    good &= check('%s no approval governs in December straight after the claim' % tag, not approved(os_, K('Q'), '2026-12'))
                    if not known:
                        prep(os_); a = gov(os_, K('Q'), '2026-12')
                        good &= check('%s unknown target: blocked as unresolved and not eligible' % tag, a is not None and UNRESOLVED in a['blockers'] and not a['eligible'])
                        good &= check('%s unknown target: approval refused' % tag, review(os_, REV3, a, 'approve')[0] == 'refused')
                        send(os_, 'c2a-p', p_rows())
                    prep(os_)
                    good &= check('%s Q is held under locked November with its receipt' % tag, {K('Q'), 'receipt-Q'} <= held_under(os_))
                    good &= check('%s Q has no governing December artifact' % tag, gov(os_, K('Q'), '2026-12') is None)
                    good &= check('%s the link is to the claimed target' % tag, (K('A1' if known else 'P'), K('Q')) in links(os_))
                    good &= check('%s November approval of A1 still governs; nothing approved twice' % tag, approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12'))
                    snap = rows_of(os_)
                    r = send(os_, 'c2a-late-repeat', [late])
                    good &= check('%s repeated old message: changed=False and no lifecycle row added' % tag, r[0] == 'ok' and r[1]['changed'] is False and rows_of(os_) == snap)
                    good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('C2b', 'clause 2', 'control: the same claim delivered in provider order gives the same end state as C2a (held, linked, nothing approved twice)')
def _():
    good = True
    for known in (True, False):
        os_ = base()
        send(os_, 'c2b-plain', q_rows(as_of=6)); prep(os_)
        r = send(os_, 'c2b-claim', [q('A1' if known else 'P', as_of=7)])
        good &= check('in-order claim accepted (changed=True)', r[0] == 'ok' and r[1]['changed'])
        if not known:
            send(os_, 'c2b-p', p_rows())
        prep(os_)
        good &= check('%s target: held under November with its receipt, no December artifact' % ('known' if known else 'unknown'), {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
    return 'OK' if good else 'WEAK'


@probe('C2c', 'clause 2/7', 'a late older message whose claim differs from the one the row already has is a second claim: recorded, not applied')
def _():
    good = True
    for first_linked in (True, False):
        tag = '[first claim linked]' if first_linked else '[first claim waiting]'
        os_ = base()
        if first_linked:
            send(os_, 'c2c-b', b_rows())
        send(os_, 'c2c-first', q_rows('B', as_of=7)); prep(os_)
        before = rows_of(os_); place = where(os_, K('Q')); hd = head(os_, 'Q')
        r = send(os_, 'c2c-older-different', [q('P', as_of=6)])
        after = rows_of(os_)
        good &= check('%s changed=True for the first declaration of a different target' % tag, r[0] == 'ok' and r[1]['changed'] is True)
        good &= check('%s recorded as a conflict for P' % tag, ('SOURCE_CLAIM_CONFLICT_RECORDED', K('P')) in claim_events(os_, 'Q'))
        good &= check('%s head unchanged; no link, move or binding row added' % tag, head(os_, 'Q') == hd and all(before[t] == after[t] for t in ('links', 'moves', 'bindings')) and where(os_, K('Q')) == place)
        send(os_, 'c2c-p', p_rows()); prep(os_)
        a = gov(os_, K('Q'), '2026-12')
        good &= check('%s after P (replacing locked A1) arrives: no link P->Q, Q not moved into the hold' % tag, (K('P'), K('Q')) not in links(os_) and K('Q') not in held_under(os_))
        good &= check('%s Q carries the conflict blocker and cannot be approved' % tag, a is not None and CONFLICT in a['blockers'] and not a['eligible'] and review(os_, REV2, a, 'approve')[0] == 'refused')
        snap = rows_of(os_)
        r = send(os_, 'c2c-older-different-repeat', [q('P', as_of=6)])
        good &= check('%s repeating the old conflicting claim adds nothing' % tag, r[0] == 'ok' and r[1]['changed'] is False and rows_of(os_) == snap)
    return 'OK' if good else 'WEAK'


@probe('C2d', 'clause 2', 'the older message was first delivered WITHOUT a claim and is delivered again with the claim (provider declares the replacement later, on the older message)')
def _():
    good = True
    for known in (True, False):
        for was_approved in (False, True):
            tag = '[%s %s]' % ('known' if known else 'unknown', 'approved' if was_approved else 'eligible')
            os_ = base()
            send(os_, 'c2d-plain', q_rows(as_of=7)); prep(os_)
            r = send(os_, 'c2d-old-no-claim', [q(as_of=6)])
            print('    %s older message without a claim: %s' % (tag, r))
            if was_approved:
                review(os_, REV2, gov(os_, K('Q'), '2026-12'), 'approve')
            r = send(os_, 'c2d-old-with-claim', [q('A1' if known else 'P', as_of=6)])
            print('    %s the same older message, now carrying supersedes: %s | events: %s' % (tag, r, claim_events(os_, 'Q')))
            good &= check('%s the claim is recorded for the row' % tag, ('SOURCE_CLAIM_DECLARED', K('A1' if known else 'P')) in claim_events(os_, 'Q'))
            good &= check('%s no approval governs in December straight after the claim' % tag, not approved(os_, K('Q'), '2026-12'))
            if not known:
                send(os_, 'c2d-p', p_rows())
            prep(os_)
            a = gov(os_, K('Q'), '2026-12')
            print('    %s after preparation: Q %s | held under November: %s | links: %s' % (tag, brief(a), sorted(held_under(os_)), links(os_)))
            good &= check('%s "applies as if it had arrived in order": Q linked to its target' % tag, (K('A1' if known else 'P'), K('Q')) in links(os_))
            good &= check('%s Q and its receipt held under locked November (clause 4)' % tag, {K('Q'), 'receipt-Q'} <= held_under(os_))
            # is the failure at least safe?
            safe = a is None or (not a['eligible'] and review(os_, REV3, a, 'approve')[0] == 'refused')
            print('    %s fail-safe check: Q cannot be approved in December: %s; A1 approved in November: %s' % (tag, safe, approved(os_, K('A1'), '2026-11')))
            if a is not None:
                r = select(os_, DL, 'A1' if known else 'P')
                print('    %s is there a person route out of this state? target selection: %s' % (tag, r))
                send(os_, 'c2d-unrelated', b_rows('B9', '2026-12-09', '12.00')); prep(os_)
                print('    %s after unrelated later intake: Q %s | links: %s' % (tag, brief(gov(os_, K('Q'), '2026-12')), links(os_)))
            good &= safe
    return 'OK' if good else 'WEAK'


@probe('C2f', 'clause 2', 'C2d continued: the row with the recorded-but-unapplied claim is then replaced by Z; is one charge approved in locked November and again in open December?')
def _():
    good = True
    z = sup('Z', '2026-12-05', '40.00', 'Q')
    z_rows = [z, rc('Z', '2026-12-05', '40.00'), stmt([z], DEC, opening='100.00')]
    for z_first in (False, True):
        tag = '[Z approved before the late claim]' if z_first else '[Z arrives after the late claim]'
        os_ = base()
        send(os_, 'c2f-p', p_rows())
        send(os_, 'c2f-q7', [q(as_of=7), rc('Q', '2026-12-03', '40.00')])
        send(os_, 'c2f-q6', [q(as_of=6)])
        if z_first:
            send(os_, 'c2f-z', z_rows); prep(os_)
            a = clear_and_approve(os_, 'Z')
            good &= check('%s Z approved in December before any claim exists (legitimate at that moment)' % tag, a is not None and a['review_status'] == 'approve')
        r = send(os_, 'c2f-q6-claim', [q('P', as_of=6)])
        print('    %s older message re-sent with supersedes=P: %s | %s' % (tag, r, claim_events(os_, 'Q')))
        good &= check('%s the claim Q->P is recorded' % tag, ('SOURCE_CLAIM_DECLARED', K('P')) in claim_events(os_, 'Q'))
        if z_first:
            good &= check('%s the December approval of Z stops governing at once' % tag, not approved(os_, K('Z'), '2026-12'))
        else:
            send(os_, 'c2f-z', z_rows)
        prep(os_)
        a = clear_and_approve(os_, 'Z')
        fin = attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'Fictional finalization without acknowledgement')
        print('    %s Z %s | links %s | held %s | finalize December: %s' % (tag, brief(a), links(os_), sorted(held_under(os_)), fin))
        good &= check('%s chain Z->Q->P->A1 is linked' % tag, (K('P'), K('Q')) in links(os_))
        good &= check('%s Z is held under locked November' % tag, K('Z') in held_under(os_))
        good &= check('%s NOT approved twice: A1 in locked November and Z in open December' % tag, not (approved(os_, K('A1'), '2026-11') and approved(os_, K('Z'), '2026-12')))
        good &= check('%s December is not finalized without acknowledgement on that approval' % tag, fin[0] == 'refused')
    # control: the same late claim carried inside the row data (a different message hash) is applied
    os_ = base()
    send(os_, 'c2f-p', p_rows()); send(os_, 'c2f-q7', [q(as_of=7), rc('Q', '2026-12-03', '40.00')]); send(os_, 'c2f-q6', [q(as_of=6)])
    send(os_, 'c2f-q6-claim-in-data', [tx('Q', '2026-12-03', '40.00', as_of=6, supersedes_source_id='P')])
    send(os_, 'c2f-z', z_rows); prep(os_)
    good &= check('[control: claim inside the row data] Q and Z held under November; nothing approved twice', {K('Q'), K('Z')} <= held_under(os_) and not approved(os_, K('Z'), '2026-12'))
    return 'OK' if good else 'WEAK'


@probe('C2e', 'clause 2', 'late older claim on an open, known December target: links and retires the target as an in-order claim would')
def _():
    good = True
    outcomes = []
    for in_order in (True, False):
        os_ = base()
        send(os_, 'c2e-b', b_rows())
        send(os_, 'c2e-plain', [q(as_of=6 if in_order else 7), rc('Q', '2026-12-03', '40.00'), stmt([q()], DEC, opening='100.00')]); prep(os_)
        send(os_, 'c2e-claim', [q('B', as_of=7 if in_order else 6)]); prep(os_)
        a = gov(os_, K('Q'), '2026-12')
        outcomes.append((sorted(a['blockers']) if a else None, (K('B'), K('Q')) in links(os_), head(os_, 'B')['removed'], where(os_, K('Q'))))
        print('    %s: Q %s | B->Q link %s | B retired %s' % ('in provider order' if in_order else 'late older message', brief(a), outcomes[-1][1], outcomes[-1][2]))
    good &= check('late older claim gives the same blockers, link, retirement and binding as the in-order claim', outcomes[0] == outcomes[1])
    good &= check('the claim is applied (link exists, target retired, transition review required)', outcomes[1][1] and outcomes[1][2] == 1 and TRANSITION in (outcomes[1][0] or []))
    return 'OK' if good else 'WEAK'


# =======================================================================================
# Clause 7. Second claim naming a different target
# =======================================================================================

def second_claim_case(first, second, first_known, second_known_before, approve_first):
    """Q claims `first`, then `second`. P replaces locked A1; B is an open December row."""
    os_ = base()
    arrive = lambda t: send(os_, 'c7-target-' + t, p_rows() if t == 'P' else b_rows())
    if first_known:
        arrive(first)
    if second_known_before:
        arrive(second)
    send(os_, 'c7-first', q_rows(first)); prep(os_)
    return os_, arrive


@probe('C7a', 'clause 7', 'second different claim in both claim orders and all target arrival orders: recorded, not applied, row stays where it is, target not retired, blocker cannot be cleared by existing dispositions')
def _():
    good = True
    for first, second in (('B', 'P'), ('P', 'B')):
        for first_known in (True, False):
            for second_known_before in (True, False):
                tag = '[%s then %s; first %s; second %s]' % (first, second, 'linked' if first_known else 'waiting', 'on file' if second_known_before else 'arrives later')
                os_, arrive = second_claim_case(first, second, first_known, second_known_before, False)
                place = where(os_, K('Q')); before = rows_of(os_); hist = lifecycle(os_)
                second_head = head(os_, second)
                r = send(os_, 'c7-second', [q(second)])
                after = rows_of(os_)
                good &= check('%s changed=True, recorded once as a conflict' % tag, r[0] == 'ok' and r[1]['changed'] is True and claim_events(os_, 'Q').count(('SOURCE_CLAIM_CONFLICT_RECORDED', K(second))) == 1)
                good &= check('%s no link, no move row, claimant bound where it was' % tag, before['links'] == after['links'] and before['moves'] == after['moves'] and where(os_, K('Q')) == place)
                good &= check('%s second target not retired by the declaration' % tag, head(os_, second) == second_head)
                good &= check('%s earlier history is an unchanged prefix' % tag, prefix_kept(hist, lifecycle(os_), HISTORY))
                good &= check('%s the open question is visible in state' % tag, K('Q') in conflicts(os_))
                if not second_known_before:
                    arrive(second)
                if not first_known:
                    arrive(first)
                prep(os_)
                good &= check('%s never a link to the second target' % tag, (K(second), K('Q')) not in links(os_))
                good &= check('%s second target still live' % tag, head(os_, second)['removed'] == 0)
                a = gov(os_, K('Q'), '2026-12'); held = K('Q') in held_under(os_)
                if first == 'P':
                    good &= check('%s first claim keeps working: Q held under November via P' % tag, held and a is None and (K('P'), K('Q')) in links(os_))
                else:
                    good &= check('%s first claim keeps working: Q linked to B, stays in December, not moved into the hold' % tag, not held and a is not None and (K('B'), K('Q')) in links(os_))
                    good &= check('%s Q blocked by the conflict, not eligible, approval refused' % tag, CONFLICT in a['blockers'] and not a['eligible'] and review(os_, REV2, a, 'approve')[0] == 'refused')
                    for code, choice in ((TRANSITION, 'settlement_verified'), (CONFLICT, 'settlement_verified'), (CONFLICT, 'revised_evidence_accepted'), (rb.REVISED, 'revised_evidence_accepted')):
                        dispose(os_, K('Q'), code, choice, period='2026-12')
                    prep(os_); a = gov(os_, K('Q'), '2026-12')
                    good &= check('%s settlement/evidence dispositions leave the conflict blocker' % tag, a is not None and CONFLICT in a['blockers'] and review(os_, REV3, a, 'approve')[0] == 'refused')
                    fin = attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'Fictional finalization without acknowledgement')
                    good &= check('%s December does not finalize without acknowledgement' % tag, fin[0] == 'refused')
                good &= check('%s nothing approved twice' % tag, not (approved(os_, K('A1'), '2026-11') and approved(os_, K('Q'), '2026-12')))
                good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('C7b', 'clause 7', 'third and later targets join the same question; every repeat of any declared claim is a no-op')
def _():
    good = True
    os_ = base(); send(os_, 'c7b-b', b_rows()); send(os_, 'c7b-first', q_rows('B')); prep(os_)
    for i, target in enumerate(('P', 'W', 'V')):
        r = send(os_, 'c7b-new-%d' % i, [q(target)])
        good &= check('new target %s: changed=True' % target, r[0] == 'ok' and r[1]['changed'] is True)
    good &= check('declared targets in order B, P, W, V; still one open question', conflicts(os_).get(K('Q'), {}).get('targets') == [K(t) for t in ('B', 'P', 'W', 'V')])
    for i, target in enumerate(('B', 'P', 'W', 'V', 'P', 'B')):
        snap = rows_of(os_)
        r = send(os_, 'c7b-repeat-%d' % i, [q(target)])
        good &= check('repeat of %s: changed=False, no lifecycle row' % target, r[0] == 'ok' and r[1]['changed'] is False and rows_of(os_) == snap)
    send(os_, 'c7b-p', p_rows()); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('Q still linked only to B, in December, with the conflict blocker', links(os_).count((K('B'), K('Q'))) == 1 and not any(l[1] == K('Q') and l[0] != K('B') for l in links(os_)) and a is not None and CONFLICT in a['blockers'])
    good &= check('P (second target) was not retired', head(os_, 'P')['removed'] == 0)
    return 'OK' if good else 'WEAK'


@probe('C7c', 'clause 7', 'an earlier open-period approval of the row stops governing at once; a live descendant inherits the blocker')
def _():
    good = True
    os_ = base(); send(os_, 'c7c-b', b_rows()); send(os_, 'c7c-first', q_rows('B')); prep(os_)
    a = clear_and_approve(os_, 'Q')
    good &= check('Q approved in December on its first claim', a is not None and a['review_status'] == 'approve')
    n = approval_count(os_)
    send(os_, 'c7c-second', [q('P')])
    good &= check('straight after the second claim (no new run) the approval no longer governs', not approved(os_, K('Q'), '2026-12'))
    prep(os_); a = gov(os_, K('Q'), '2026-12')
    good &= check('after preparation: conflict blocker, not eligible, not approved, no approval decision added', CONFLICT in a['blockers'] and not a['eligible'] and a['review_status'] != 'approve' and approval_count(os_) == n)
    # descendant: Z replaces Q
    z = [sup('Z', '2026-12-05', '40.00', 'Q'), rc('Z', '2026-12-05', '40.00')]
    send(os_, 'c7c-z', z); prep(os_)
    az = gov(os_, K('Z'), '2026-12')
    print('    descendant Z:', brief(az))
    good &= check('live descendant Z carries the conflict blocker and cannot be approved', az is not None and CONFLICT in az['blockers'] and review(os_, REV2, az, 'approve')[0] == 'refused')

    # descendant approved first, then the ancestor is contested
    os_ = base(); send(os_, 'c7c2-b', b_rows()); send(os_, 'c7c2-first', [q('B'), rc('Q', '2026-12-03', '40.00')])
    send(os_, 'c7c2-z', z + [stmt([z[0]], DEC, opening='100.00')]); prep(os_)
    az = clear_and_approve(os_, 'Z')
    ok_before = az is not None and az['review_status'] == 'approve'
    print('    Z approved before its ancestor is contested:', ok_before, brief(az))
    r = send(os_, 'c7c2-second', [q('P')])
    print('    second claim on the already replaced ancestor Q:', r, '| conflicts:', sorted(conflicts(os_)))
    if ok_before:
        good &= check('descendant approval stops governing at once when its ancestor is contested', not approved(os_, K('Z'), '2026-12'))
    prep(os_); az = gov(os_, K('Z'), '2026-12')
    good &= check('descendant Z blocked by the ancestor conflict after preparation', az is not None and CONFLICT in az['blockers'] and not az['eligible'])
    return 'OK' if good else 'WEAK'


@probe('C7d', 'clause 7 + D-029', 'frozen home: a row approved inside its own locked period keeps that approval; the incoming claimed versions are held; reopen keeps the contested blocker and approves nothing')
def _():
    good = True
    os_ = base()
    n = approval_count(os_); frozen = gov(os_, K('A1'), '2026-11')
    r1 = send(os_, 'c7d-first', [dict(tx('A1', '2026-11-03', '40.00'), supersedes=K('U0'))])
    r2 = send(os_, 'c7d-second', [dict(tx('A1', '2026-11-03', '40.00'), supersedes=K('U1'))])
    print('    first claim:', r1, '| second claim:', r2)
    good &= check('both declarations recorded (one declared, one conflict)', [c[0] for c in claim_events(os_, 'A1') if c[0].startswith('SOURCE_CLAIM')] == ['SOURCE_CLAIM_DECLARED', 'SOURCE_CLAIM_CONFLICT_RECORDED'])
    now = gov(os_, K('A1'), '2026-11')
    good &= check('D-029: the frozen November approval of A1 is preserved (same artifact, approved)', now is not None and now['id'] == frozen['id'] and now['review_status'] == 'approve')
    good &= check('D-029: the incoming version is held as late activity in the locked period', where(os_, K('A1')) == ('2026-11', 0, LATE))
    good &= check('no approval decision was added', approval_count(os_) == n)
    r = select(os_, DL, 'U0', item='A1', period='2026-11', evidence=ev(os_, 'receipt-A1'))
    good &= check('D-029: target selection is refused PERIOD_LOCKED while the home period is locked (even with disposition + lock)', r[0] == 'refused' and r[2] == 'PERIOD_LOCKED')
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    os_.reopen_period(PADMIN, '2026-11', 'Fictional authorized reopen')
    straight = gov(os_, K('A1'), '2026-11')
    print('    straight after reopen (no new run):', brief(straight))
    good &= check('straight after reopen the old approval no longer governs', not approved(os_, K('A1'), '2026-11'))
    prep(os_, '2026-11'); a = gov(os_, K('A1'), '2026-11')
    print('    after reopen and preparation:', brief(a))
    good &= check('after reopen: A1 carries the contested blocker', a is not None and CONFLICT in a['blockers'] and not a['eligible'])
    good &= check('after reopen: not approved, approval refused, no approval decision created', a['review_status'] != 'approve' and review(os_, REV2, a, 'approve')[0] == 'refused' and approval_count(os_) == n)
    r = select(os_, DISP, 'U0', item='A1', period='2026-11', evidence=ev(os_, 'receipt-A1'))
    good &= check('after reopen an authorized target selection is accepted', r[0] == 'ok')
    prep(os_, '2026-11'); a = gov(os_, K('A1'), '2026-11')
    print('    after selecting the first target:', brief(a))
    good &= check('the selection clears only the conflict and approves nothing', CONFLICT not in a['blockers'] and a['review_status'] != 'approve' and approval_count(os_) == n)
    return 'OK' if good else 'WEAK'


# =======================================================================================
# Clause 8. No provider message releases a locked-period hold
# =======================================================================================

def held_q(open_target_first):
    """December Q replaces P, which replaces A1 approved in locked November. Q and its receipt are held."""
    os_ = base()
    if open_target_first:
        send(os_, 'c8-b', b_rows())
    send(os_, 'c8-p', p_rows()); send(os_, 'c8-q', q_rows('P')); prep(os_)
    return os_


def still_held(os_):
    return {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None and where(os_, K('Q')) == ('2026-11', 0, MOVED)


@probe('C8a', 'clause 8', 'December Q held under locked November: no later provider message releases it or its receipt (second claim on an open row on file before or after, re-sends, revisions, date changes, receipts, period hints)')
def _():
    good = True
    for open_first in (True, False):
        tag = '[open target %s]' % ('on file first' if open_first else 'arrives last')
        os_ = held_q(open_first)
        good &= check('%s setup: Q and receipt held under November' % tag, still_held(os_))
        steps = [
            ('second claim naming open B', [q('B')]),
            ('repeat of the second claim', [q('B')]),
            ('repeat of the first claim', [q('P')]),
            ('row re-sent with no claim', [q()]),
            ('amount revised, claim B', [q('B', amount='41.00')]),
            ('date revised inside December, claim B', [q('B', amount='41.00', date='2026-12-09')]),
            ('date revised into November', [q('B', amount='41.00', date='2026-11-20')]),
            ('date revised back to December', [q('B', amount='41.00', date='2026-12-03')]),
            ('receipt revised', [rc('Q', '2026-12-03', '41.00')]),
            ('a second receipt under a new key', [rc('Q', '2026-12-03', '41.00', key='receipt-Q-second')]),
            ('third claim on an unknown row', [q('W', amount='41.00')]),
            ('new statement covering Q', [stmt([q(amount='41.00')], DEC, opening='100.00', key='stmt-2026-12-b')]),
            ('row withdrawn by the feed', [dict(q(amount='41.00'), tombstone=True, removal_reason='feed_removed')]),
            ('row re-sent after the withdrawal, no claim', [q(amount='41.00')]),
        ]
        for i, (label, rows) in enumerate(steps):
            r = send(os_, 'c8a-%d' % i, rows, period_id='2026-12' if i % 2 else None)
            if i == 0 and not open_first:
                send(os_, 'c8-b-late', b_rows())
            prep(os_)
            ok = K('Q') in held_under(os_) and 'receipt-Q' in held_under(os_) and gov(os_, K('Q'), '2026-12') is None
            if label == 'row withdrawn by the feed':
                ok = gov(os_, K('Q'), '2026-12') is None and not approved(os_, K('Q'), '2026-12')
            if label == 'date revised into November':
                ok = gov(os_, K('Q'), '2026-12') is None and not approved(os_, K('Q'), '2026-11') and where(os_, K('Q'))[1] == 0
            good &= check('%s after "%s" (%s): still not in December, still held' % (tag, label, r[0] if r[0] == 'refused' else r[1]['changed']), ok)
        good &= check('%s the extra receipt is held too' % tag, 'receipt-Q-second' in held_under(os_))
        good &= check('%s B (open second target) was never retired and no link B->Q exists' % tag, head(os_, 'B')['removed'] == 0 and (K('B'), K('Q')) not in links(os_))
        good &= check('%s nothing approved twice; A1 still approved in November' % tag, approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12'))
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
        # authorized reopen releases the hold and leaves the contested blocker
        os_.reopen_period(PADMIN, '2026-11', 'Fictional authorized reopen'); prep(os_, '2026-11'); prep(os_)
        a = gov(os_, K('Q'), '2026-12')
        print('    %s after authorized reopen: Q %s | held: %s' % (tag, brief(a), sorted(held_under(os_))))
        good &= check('%s reopen releases the hold' % tag, a is not None and K('Q') not in held_under(os_))
        good &= check('%s reopen leaves the contested blocker; approval refused' % tag, a is not None and CONFLICT in a['blockers'] and review(os_, REV2, a, 'approve')[0] == 'refused')
        good &= check('%s nothing approved twice after reopen' % tag, not (approved(os_, K('A1'), '2026-11') and approved(os_, K('Q'), '2026-12')))
    return 'OK' if good else 'WEAK'


@probe('C8b', 'clause 8', 'messages for other identities in the chain do not release the held row (intermediate link re-claimed, tombstoned, descendant added)')
def _():
    good = True
    os_ = held_q(True)
    r = send(os_, 'c8b-p-reclaim', [sup('P', '2026-12-02', '40.00', 'B')]); prep(os_)
    print('    intermediate P now also claims open B:', r, '| conflicts:', sorted(conflicts(os_)))
    good &= check('P re-claimed to an open row: P contested, Q still held under November', K('P') in conflicts(os_) and still_held(os_) and K('P') in held_under(os_))
    r = send(os_, 'c8b-z', [sup('Z', '2026-12-06', '40.00', 'Q'), rc('Z', '2026-12-06', '40.00')]); prep(os_)
    good &= check('a new descendant Z of the held row is held as well', K('Z') in held_under(os_) and gov(os_, K('Z'), '2026-12') is None)
    r = send(os_, 'c8b-p-void', [dict(tx('P', '2026-12-02', '40.00'), tombstone=True, removal_reason='voided')]); prep(os_)
    a = gov(os_, K('Q'), '2026-12'); az = gov(os_, K('Z'), '2026-12')
    print('    intermediate P voided:', r, '| Q', brief(a), '| Z', brief(az), '| held:', sorted(held_under(os_)))
    good &= check('voiding the intermediate link does not put Q or Z into December as approvable', all(x is None or not x['eligible'] for x in (a, az)))
    good &= check('nothing approved twice', approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12') and not approved(os_, K('Z'), '2026-12'))
    return 'OK' if good else 'WEAK'


@probe('C8c', 'clause 8/9', 'selecting a target that is itself held as locked late activity quarantines the claimant')
def _():
    good = True
    os_ = base()
    send(os_, 'c8c-b', b_rows()); send(os_, 'c8c-first', q_rows('B')); prep(os_)
    r = send(os_, 'c8c-late', [tx('L', '2026-11-20', '40.00', desc='LATE NOVEMBER DEMO'), rc('L', '2026-11-20', '40.00', vendor='LATE NOVEMBER DEMO')])
    good &= check('L (November date, after the lock) is held as late activity', where(os_, K('L')) == ('2026-11', 0, LATE))
    send(os_, 'c8c-second', [q('L')]); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('before selection Q stays in December with the conflict blocker', a is not None and CONFLICT in a['blockers'] and K('Q') not in held_under(os_))
    r = select(os_, DISP, 'L')
    print('    select the late-activity target L (disposition grant only):', r)
    good &= check('selection of a locked target needs no lock grant (it moves into a hold, not out of one)', r[0] == 'ok')
    prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    print('    after selection: Q', brief(a), '| binding', where(os_, K('Q')), '| held', sorted(held_under(os_)))
    good &= check('Q is quarantined under locked November and has no December artifact', a is None and where(os_, K('Q'))[0] == '2026-11' and where(os_, K('Q'))[1] == 0)
    good &= check('its receipt is quarantined too', where(os_, 'receipt-Q')[0] == '2026-11' and where(os_, 'receipt-Q')[1] == 0)
    good &= check('nothing approved by the selection', not approved(os_, K('Q'), '2026-12'))
    return 'OK' if good else 'WEAK'


# =======================================================================================
# Clause 9. Who may disposition, and what the disposition does
# =======================================================================================

def contested(first='B', second='P', s1=None, s2=None):
    """Q in December first claims `first` then `second`; both targets on file."""
    os_ = base()
    send(os_, 'c9-b', b_rows()); send(os_, 'c9-p', p_rows())
    send(os_, 'c9-first', q_rows(first), s1); prep(os_)
    send(os_, 'c9-second', [q(second)], s2); prep(os_)
    return os_


@probe('C9a', 'clause 9', 'every refusal, each leaving no trace: no disposition grant, either claim supplier (also via a repeat envelope), undeclared target, absent / stale / foreign / unrelated evidence')
def _():
    good = True
    os_ = contested(s1=S1, s2=S2)
    r = send(os_, 'c9a-repeat-envelope', [q('P')], S3)
    good &= check('a third person re-sends the second claim in a new envelope: no-op for the row', r[0] == 'ok' and r[1]['changed'] is False)
    old_receipt = ev(os_)
    send(os_, 'c9a-receipt-revision', [rc('Q', '2026-12-03', '40.00', content='Fictional revised receipt for Q')]); prep(os_)
    other = ev(os_, 'receipt-A2')
    before = (dispositions(os_), rows_of(os_))
    cases = [
        ('no disposition grant (review only)', select(os_, REV2, 'B'), 403),
        ('lock grant without disposition grant', select(os_, PADMIN, 'B'), 403),
        ('supplier of the first claim message', select(os_, S1R, 'B'), 403),
        ('supplier of the second claim message', select(os_, S2R, 'B'), 403),
        ('supplier of a repeat envelope of the second claim', select(os_, S3R, 'P'), 403),
        ('undeclared target', select(os_, DISP, 'A2'), 409),
        ('unknown undeclared target', select(os_, DISP, 'NOPE'), 409),
        ('no evidence', select(os_, DISP, 'B', evidence=[]), None),
        ('stale evidence (superseded receipt version)', select(os_, DISP, 'B', evidence=old_receipt), None),
        ('foreign evidence (reference that does not exist in scope)', select(os_, DISP, 'B', evidence=[{'snapshot_id': 999999, 'hash': 'f' * 64}]), None),
        ('current receipt with a wrong hash', select(os_, DISP, 'B', evidence=[{'snapshot_id': ev(os_)[0]['snapshot_id'], 'hash': '0' * 64}]), None),
        ('unrelated evidence only (receipt of another charge)', select(os_, DISP, 'B', evidence=other), None),
        ('wrong period', select(os_, DISP, 'B', period='2026-11'), None),
        ('not single-item scope', attempt(os_.disposition, DISP, 'card_preparation', '2026-12', K('Q'), CONFLICT, CHOICE, {'target_key': K('B')}, ev(os_), 'Fictional', scope_kind='propose_rule'), None),
    ]
    for label, r, status in cases:
        print('    %-58s %s' % (label + ':', r))
        good &= check('refused: ' + label, r[0] == 'refused' and (status is None or r[1] == status))
    good &= check('no refusal left a disposition, event, link, binding or move row', (dispositions(os_), rows_of(os_)) == before)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('the blocker is still in place after all refusals', a is not None and CONFLICT in a['blockers'])
    r = select(os_, DISP, 'B')
    good &= check('positive control: an independent person with the disposition grant and the current related receipt is accepted', r[0] == 'ok')
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('C9b', 'clause 9', 'first target stands: the blocker clears, nothing moves, nothing is approved; the selector cannot approve; an independent reviewer can')
def _():
    good = True
    os_ = contested()
    before = lifecycle(os_); rows = rows_of(os_); n = approval_count(os_); nd = len(dispositions(os_))
    r = select(os_, DR, 'B')
    after = rows_of(os_)
    good &= check('accepted and recorded as one disposition', r[0] == 'ok' and len(dispositions(os_)) == nd + 1)
    good &= check('nothing moves: no link, binding, move, snapshot or head change', all(rows[t] == after[t] for t in ('links', 'bindings', 'moves', 'source_snapshots', 'heads', 'decisions')))
    good &= check('exactly one SOURCE_CLAIM_TARGET_SELECTED event', claim_events(os_, 'Q').count(('SOURCE_CLAIM_TARGET_SELECTED', K('B'))) == 1)
    good &= check('append-only: earlier history is an unchanged prefix; earlier dispositions unchanged', prefix_kept(before, lifecycle(os_), HISTORY))
    good &= check('the selection itself approves nothing', approval_count(os_) == n and not approved(os_, K('Q'), '2026-12'))
    prep(os_); a = gov(os_, K('Q'), '2026-12')
    print('    after selection and preparation:', brief(a))
    good &= check('conflict blocker cleared; ordinary transition review remains', a is not None and CONFLICT not in a['blockers'] and TRANSITION in a['blockers'])
    show('settlement_verified', dispose(os_, K('Q'), TRANSITION, 'settlement_verified', period='2026-12')); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    r = review(os_, DR, a, 'approve')
    good &= check('the selector cannot approve the artifact that depends on the selection', r[0] == 'refused' and r[1] == 403)
    r = review(os_, REV2, a, 'approve')
    good &= check('an independent reviewer can approve after the ordinary controls', r[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
    good &= check('P (not selected) stays live and unlinked to Q', head(os_, 'P')['removed'] == 0 and (K('P'), K('Q')) not in links(os_))
    sel = [d for d in sql(os_, "SELECT id FROM dispositions WHERE choice=?", (CHOICE,))][0][0]
    r = attempt(os_.revoke_disposition, DISP, sel, 'Fictional revoke attempt')
    good &= check('a target selection cannot be revoked through the ordinary route', r[0] == 'refused')
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('C9c', 'clause 9', 'second target stands: known open row, unknown row, and a row whose chain reaches the locked period; never approved by the disposition')
def _():
    good = True
    # (1) known open second target
    os_ = base(); send(os_, 'c9c-b', b_rows()); send(os_, 'c9c-b2', b_rows('B2', '2026-12-04', '40.00'))
    send(os_, 'c9c-first', q_rows('B')); prep(os_); send(os_, 'c9c-second', [q('B2')]); prep(os_)
    n = approval_count(os_); hist = lifecycle(os_)
    r = select(os_, DR, 'B2'); prep(os_); a = gov(os_, K('Q'), '2026-12')
    print('    [open second target] select:', r, '| Q', brief(a), '| links', links(os_), '| B removed', head(os_, 'B')['removed'], '| B2 removed', head(os_, 'B2')['removed'])
    good &= check('[open] accepted; link to B2 governs; Q stays in December', r[0] == 'ok' and (K('B2'), K('Q')) in links(os_) and where(os_, K('Q')) == ('2026-12', 1, None))
    good &= check('[open] B2 retired as an ordinary replacement; transition review required; not approved', head(os_, 'B2')['removed'] == 1 and a is not None and TRANSITION in a['blockers'] and CONFLICT not in a['blockers'] and approval_count(os_) == n)
    good &= check('[open] append-only: earlier history is an unchanged prefix (old link kept as evidence)', prefix_kept(hist, lifecycle(os_), HISTORY) and (K('B'), K('Q')) in links(os_))
    b_state = head(os_, 'B'); ab = gov(os_, K('B'), '2026-12')
    print('    [open] former first target B after it was de-selected: removed=%s governing artifact=%s' % (b_state['removed'], brief(ab)))
    former_target_dropped = b_state['removed'] == 1 and ab is None
    st = os_.state(PREP)
    print('    [open] B in removed_items: %s | B in source_exceptions: %s' % ([i for i in st['removed_items'] if K('B') in json.dumps(i)][:1], [e for e in exceptions_of(os_) if e[0] == K('B')]))
    show('settlement_verified', dispose(os_, K('Q'), TRANSITION, 'settlement_verified', period='2026-12')); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('[open] the selector cannot approve Q', review(os_, DR, a, 'approve')[0] == 'refused')
    good &= check('[open] audit chain verifies', os_.verify_audit(PREP))

    # (2) unknown second target
    os_ = base(); send(os_, 'c9c-b', b_rows()); send(os_, 'c9c-first', q_rows('B')); prep(os_); send(os_, 'c9c-second', [q('P')]); prep(os_)
    r = select(os_, DISP, 'P'); prep(os_); a = gov(os_, K('Q'), '2026-12')
    print('    [unknown second target] select:', r, '| Q', brief(a))
    good &= check('[unknown] accepted; Q unresolved until the target arrives; not approvable', r[0] == 'ok' and a is not None and UNRESOLVED in a['blockers'] and CONFLICT not in a['blockers'] and review(os_, REV2, a, 'approve')[0] == 'refused')
    send(os_, 'c9c-p', p_rows()); prep(os_)
    good &= check('[unknown] when P (replacing locked A1) arrives, Q links and is held under November with its receipt', (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
    good &= check('[unknown] nothing approved twice', approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12'))

    # (3) known second target whose chain reaches locked November
    os_ = contested('B', 'P')
    r = select(os_, DISP, 'P'); prep(os_)
    print('    [locked-chain second target] select (disposition grant only):', r, '| binding', where(os_, K('Q')))
    good &= check('[locked chain] accepted without the lock grant; Q and receipt held under November; no December artifact', r[0] == 'ok' and {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
    good &= check('[locked chain] nothing approved twice; audit verifies', approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12') and os_.verify_audit(PREP))
    if former_target_dropped:
        print('    observation: after B2 was selected, the former first target B stays retired with no artifact and no flag.')
        return 'NOTE' if good else 'WEAK'
    return 'OK' if good else 'WEAK'


@probe('C9d', 'clause 8/9', 'release from a locked-period hold by disposition: refused without the lock grant on the same person; accepted with both; never approved by the disposition')
def _():
    good = True
    os_ = held_q(True)
    send(os_, 'c9d-second', [q('B')]); prep(os_)
    good &= check('setup: Q contested and still held under November', K('Q') in conflicts(os_) and still_held(os_))
    before = (dispositions(os_), rows_of(os_))
    for label, who in (('disposition grant only', DISP), ('disposition + review, no lock', DR), ('lock grant only', PADMIN), ('finalize + lock, no disposition', FIN)):
        r = select(os_, who, 'B')
        print('    %-34s %s' % (label + ':', r))
        good &= check('release refused: ' + label, r[0] == 'refused' and r[1] == 403)
    good &= check('refusals left no trace and Q is still held', (dispositions(os_), rows_of(os_)) == before and still_held(os_))
    r = select(os_, DISP, 'P')
    good &= check('confirming the standing (locked) target needs no lock grant and moves nothing', r[0] == 'ok' and still_held(os_))
    prep(os_)
    good &= check('after confirmation Q remains held; no conflict listed', still_held(os_) and K('Q') not in conflicts(os_))

    os_ = held_q(True); send(os_, 'c9d-second', [q('B')]); prep(os_)
    n = approval_count(os_); hist = lifecycle(os_)
    r = select(os_, DL, 'B'); prep(os_); a = gov(os_, K('Q'), '2026-12')
    print('    same person holds disposition + lock:', r, '| Q', brief(a), '| binding', where(os_, K('Q')))
    good &= check('release accepted for a person holding both grants', r[0] == 'ok')
    good &= check('Q and its receipt are released into December', where(os_, K('Q')) == ('2026-12', 1, None) and where(os_, 'receipt-Q') == ('2026-12', 1, None) and a is not None)
    good &= check('ordinary transition review applies; nothing approved by the disposition', a is not None and TRANSITION in a['blockers'] and CONFLICT not in a['blockers'] and approval_count(os_) == n and a['review_status'] != 'approve')
    good &= check('append-only: history prefix unchanged; the former link P->Q is kept as evidence', prefix_kept(hist, lifecycle(os_), HISTORY) and (K('P'), K('Q')) in links(os_))
    good &= check('the releasing person cannot approve Q', review(os_, DL, a, 'approve')[0] == 'refused')
    good &= check('P stays held under November (its own chain still reaches A1)', K('P') in held_under(os_))
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    # a later provider message cannot undo the person's selection, and a new distinct target reopens the question
    r = send(os_, 'c9d-repeat-first', [q('P')]); prep(os_)
    good &= check('repeating the de-selected claim afterwards changes nothing', r[0] == 'ok' and r[1]['changed'] is False and where(os_, K('Q')) == ('2026-12', 1, None) and K('Q') not in conflicts(os_))
    r = send(os_, 'c9d-new-target', [q('W')]); prep(os_); a = gov(os_, K('Q'), '2026-12')
    good &= check('a new distinct target reopens the question and blocks the row again', r[0] == 'ok' and r[1]['changed'] and K('Q') in conflicts(os_) and a is not None and CONFLICT in a['blockers'])
    return 'OK' if good else 'WEAK'


@probe('C9e', 'clause 9', 'the selection contributor follows row revisions and live descendants: the selector cannot approve either')
def _():
    good = True
    os_ = contested()
    r = select(os_, DR, 'B'); prep(os_)
    good &= check('selection recorded', r[0] == 'ok')
    r = send(os_, 'c9e-revision', [q('B', amount='42.00'), rc('Q', '2026-12-03', '42.00'), stmt([q(amount='42.00')], DEC, opening='100.00')]); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    print('    after a row revision:', brief(a), '| contributors:', a['contributors'] if a else None)
    good &= check('selection persists through the revision (no conflict reopened)', a is not None and CONFLICT not in a['blockers'] and K('Q') not in conflicts(os_))
    for code, choice in ((TRANSITION, 'settlement_verified'), (rb.REVISED, 'revised_evidence_accepted')):
        a = gov(os_, K('Q'), '2026-12')
        if a and code in a['blockers']:
            show(choice, dispose(os_, K('Q'), code, choice, period='2026-12')); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    print('    revised Q before review:', brief(a))
    r = review(os_, DR, a, 'approve')
    good &= check('the selector cannot approve the revised row', r[0] == 'refused' and r[1] == 403)
    good &= check('the selector is listed as a contributor', a['contributors'] is not None and DR.id in a['contributors'])
    zrow = sup('Z', '2026-12-06', '42.00', 'Q')
    send(os_, 'c9e-z', [zrow, rc('Z', '2026-12-06', '42.00'), stmt([zrow], DEC, opening='100.00')]); prep(os_)
    az = gov(os_, K('Z'), '2026-12')
    for code, choice in ((TRANSITION, 'settlement_verified'), (rb.REVISED, 'revised_evidence_accepted')):
        az = gov(os_, K('Z'), '2026-12')
        if az and code in az['blockers']:
            show(choice + ' on Z', dispose(os_, K('Z'), code, choice, period='2026-12')); prep(os_)
    az = gov(os_, K('Z'), '2026-12')
    print('    live descendant Z before review:', brief(az), '| contributors:', az['contributors'] if az else None)
    r = review(os_, DR, az, 'approve')
    good &= check('the selector cannot approve the live descendant', az is not None and r[0] == 'refused' and r[1] == 403)
    r = review(os_, REV3, az, 'approve')
    good &= check('an independent reviewer can', r[0] == 'ok')
    return 'OK' if good else 'WEAK'


@probe('C9f', 'clause 9 + D-029', 'locked home: the PERIOD_LOCKED refusal stands until an authorized reopen, separately from the held-December release')
def _():
    good = True
    os_ = contested()                      # Q is in December (open) and contested
    r = attempt(os_.lock_period, PADMIN, '2026-12', 'Fictional lock of December')
    print('    lock December while Q is contested:', r)
    if r[0] == 'refused':
        r = attempt(os_.lock_period, PADMIN, '2026-12', 'Fictional lock of December', 'Fictional acknowledgement of the open contested claim')
        print('    lock December with acknowledgement:', r)
    if r[0] != 'ok':
        print('    December could not be locked with the conflict open; the locked-home refusal is covered by C7d.')
        return 'OK'
    for who in (DISP, DL):
        r = select(os_, who, 'B')
        good &= check('locked home period: selection refused PERIOD_LOCKED for %s' % who.id, r[0] == 'refused' and r[2] == 'PERIOD_LOCKED')
    os_.reopen_period(PADMIN, '2026-12', 'Fictional authorized reopen'); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('after reopen the conflict is still open and blocks approval', a is not None and CONFLICT in a['blockers'])
    good &= check('after reopen the selection is accepted', select(os_, DISP, 'B')[0] == 'ok')
    return 'OK' if good else 'WEAK'


@probe('C9g', 'clause 9', 'a second, equally authorized selection replaces the first without rewriting it; the envelope replay of a claim by another person')
def _():
    good = True
    os_ = contested()
    r1 = select(os_, DR, 'B'); prep(os_)
    hist = lifecycle(os_); d = dispositions(os_)
    r2 = select(os_, DR2, 'B')
    print('    a second selection with no open question:', r2)
    r = send(os_, 'c9g-new', [q('W')]); prep(os_)
    r3 = select(os_, DR2, 'P'); prep(os_)
    print('    after a new target reopened the question, another person selects P:', r3, '| binding', where(os_, K('Q')))
    good &= check('second selection accepted and appended; the first record is byte-identical', r3[0] == 'ok' and dispositions(os_)[:len(d)] == d and prefix_kept(hist, lifecycle(os_), HISTORY))
    good &= check('the new selection governs: Q held under November via P', {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    # exact replay of a claim batch by another person
    os_ = base(); send(os_, 'c9g-b', b_rows()); send(os_, 'c9g-p', p_rows())
    send(os_, 'c9g-first', q_rows('B'), S1); prep(os_)
    pk = packet('c9g-second', [q('P')])
    os_.intake(S2, pk); replay = attempt(os_.intake, S3, pk); prep(os_)
    print('    exact replay of the second claim batch by a third person:', replay)
    r = select(os_, S3R, 'B')
    print('    that third person then selects a target:', r)
    if r[0] == 'ok':
        print('    observation: an exact batch replay leaves no delivery record for the replaying person, so that person is not treated as a supplier.')
        return 'NOTE' if good else 'WEAK'
    return 'OK' if good else 'WEAK'


@probe('C9h', 'clause 9', 'review independence after a later confirming selection by another person: can the earlier selector then approve?')
def _():
    good = True
    os_ = base(); send(os_, 'c9h-b', b_rows()); send(os_, 'c9h-b2', b_rows('B2', '2026-12-04', '40.00'))
    send(os_, 'c9h-first', [q('B'), rc('Q', '2026-12-03', '40.00'), stmt([q()], DEC, opening='100.00')]); prep(os_); send(os_, 'c9h-second', [q('B2')]); prep(os_)
    r1 = select(os_, DR, 'B2'); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    good &= check('first selector chose B2 (the link was created by that decision) and is a contributor', r1[0] == 'ok' and a is not None and DR.id in (a['contributors'] or []))
    r2 = select(os_, DR2, 'B2'); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    print('    a second person records a confirming selection of the same target:', r2, '| contributors now:', a['contributors'] if a else None)
    if a and TRANSITION in a['blockers']:
        show('settlement_verified', dispose(os_, K('Q'), TRANSITION, 'settlement_verified', period='2026-12')); prep(os_)
    a = gov(os_, K('Q'), '2026-12')
    print('    Q before review:', brief(a), '| contributors:', a['contributors'] if a else None)
    good &= check('the latest selector cannot approve', review(os_, DR2, a, 'approve')[0] == 'refused')
    r = review(os_, DR, a, 'approve')
    print('    the EARLIER selector, whose decision created the governing link, tries to approve:', r)
    if r[0] == 'ok':
        print('    observation: once another person confirms the selection, the earlier selector is no longer a contributor and may approve.')
        return 'NOTE' if good else 'WEAK'
    return 'OK' if good else 'WEAK'


def main():
    wanted = set(sys.argv[2:])
    results = []
    for pid, clause, title, fn in PROBES:
        if wanted and pid not in wanted:
            continue
        print('\n=== %s [%s] %s' % (pid, clause, title))
        try:
            verdict = fn()
        except Exception:
            traceback.print_exc(file=sys.stdout)
            verdict = 'ERROR'
        print('--> %s %s' % (pid, verdict))
        results.append((pid, clause, verdict))
    print('\nSUMMARY')
    for pid, clause, verdict in results:
        print('  %-5s %-18s %s' % (pid, clause.replace(' ', '_'), verdict))
    bad = [r for r in results if r[2] in ('WEAK', 'ERROR')]
    print('\n%d probes: %d OK, %d NOTE, %d WEAK, %d ERROR' % (len(results), sum(r[2] == 'OK' for r in results), sum(r[2] == 'NOTE' for r in results), sum(r[2] == 'WEAK' for r in results), sum(r[2] == 'ERROR' for r in results)))
    h.TMP.cleanup()
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
