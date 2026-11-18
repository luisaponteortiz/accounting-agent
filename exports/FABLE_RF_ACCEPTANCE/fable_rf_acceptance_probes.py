"""Fable independent acceptance probes for RF-01, RF-02 and RF-03 under unchanged D-026 and D-029.

Usage (from anywhere):
    python3 fable_rf_acceptance_probes.py <project-root> [PROBE_ID ...]

Drives the application in <project-root> through public service operations only (intake, enqueue/drain,
review, disposition, finalize, state/export/verify_audit). Temporary SQLite files, fictional data, no
network, model, posting or payment. Table contents are read from the probe's own temporary database,
read-only. Fixture helpers are loaded unchanged from
<project-root>/exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py. Every scenario below is new.

G1..  RF-01  a claim-free older or conflicting message that is later re-sent carrying the row's first claim,
             and every neighbouring path on which a claim could be recorded without being applied
G2..  RF-02  every person who recorded a target selection stays a contributor
G3..  RF-03  is in fable_rf_equivalence.py (it wraps this script and the earlier ones)

Verdicts: OK control held | WEAK confirmed gap (exit 1) | NOTE observation needing a decision
          | ERROR probe could not reach its intended state (exit 1)
"""
import importlib.util
import json
import sys
import traceback
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
_path = ROOT / 'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
_spec = importlib.util.spec_from_file_location('fable_re_probes', _path)
p = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_path), str(ROOT)]
_spec.loader.exec_module(p)
sys.argv = _argv
h = p.h
base, send, prep, q, q_rows, p_rows, b_rows = p.base, p.send, p.prep, p.q, p.q_rows, p.p_rows, p.b_rows
tx, rc, stmt, sup, gov, review, dispose, attempt, brief = p.tx, p.rc, p.stmt, p.sup, p.gov, p.review, p.dispose, p.attempt, p.brief
head, where, claim_events, select, rows_of, dispositions, sql = p.head, p.where, p.claim_events, p.select, p.rows_of, p.dispositions, p.sql
lifecycle, delta, prefix_kept, links, held_under, approved, check, K = p.lifecycle, p.delta, p.prefix_kept, p.links, p.held_under, p.approved, p.check, p.K
clear_and_approve = p.clear_and_approve
DEC, PREP, PREP2, REV2, REV3, REV4, FIN, DISP, ADMIN = p.DEC, p.PREP, p.PREP2, p.REV2, p.REV3, p.REV4, p.FIN, p.DISP, p.ADMIN
DL, DR, DR2 = p.DL, p.DR, p.DR2
CONFLICT, UNRESOLVED, TRANSITION, HISTORY = p.CONFLICT, p.UNRESOLVED, p.TRANSITION, p.HISTORY
REVISED = p.rb.REVISED
PROBES = []


def probe(pid, ticket, title):
    def register(fn):
        PROBES.append((pid, ticket, title, fn))
        return fn
    return register


def declared(os_, sid='Q'):
    return [c for c in claim_events(os_, sid) if c[0] == 'SOURCE_CLAIM_DECLARED']


def clear_all(os_, sid, period='2026-12'):
    """Clear the blockers that have an ordinary disposition (the dispositioner is DISP, never a selector)."""
    for _ in range(4):
        a = gov(os_, K(sid), period)
        if a is None:
            return None
        todo = [(c, ch) for c, ch in ((TRANSITION, 'settlement_verified'), (REVISED, 'revised_evidence_accepted')) if c in a['blockers']]
        if not todo:
            break
        for code, choice in todo:
            dispose(os_, K(sid), code, choice, period=period)
        prep(os_, period)
    return gov(os_, K(sid), period)


# =======================================================================================
# RF-01
# =======================================================================================

@probe('G1a', 'RF-01', 'claim-free older / same-order conflicting message, retained (twice), then re-sent with the first claim: sequence and timestamp order, known and unknown target, eligible and approved row, claim outside and inside the row data')
def _():
    good = True; n = 0
    for ordering in ('sequence', 'timestamp'):
        new, older = (7, 6) if ordering == 'sequence' else ('2026-12-05T10:00:00Z', '2026-12-04T10:00:00Z')
        for carrier in ('outside', 'inside'):
            for known in (True, False):
                for was_approved in (False, True):
                    for conflicting in (False, True):
                        if carrier == 'inside' and (ordering != 'sequence' or conflicting):
                            continue
                        n += 1
                        tag = '[%s %s %s %s %s]' % (ordering, carrier, 'known' if known else 'unknown', 'approved' if was_approved else 'eligible', 'same-order-conflict' if conflicting else 'older')
                        os_ = base()
                        send(os_, 'g1a-plain', q_rows(as_of=new)); prep(os_)
                        if was_approved:
                            r = review(os_, REV2, gov(os_, K('Q'), '2026-12'), 'approve')
                            good &= check('%s Q approved and governing before the late claim' % tag, r[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
                        amount, order = ('41.00', new) if conflicting else ('40.00', older)
                        hd = head(os_, 'Q'); snap = rows_of(os_)
                        r0 = send(os_, 'g1a-old-plain', [q(amount=amount, as_of=order)])
                        r1 = send(os_, 'g1a-old-plain-again', [q(amount=amount, as_of=order)])
                        after_plain = rows_of(os_)
                        good &= check('%s claim-free old message: kept once as evidence, changed=False both times, head unchanged' % tag,
                                      r0[0] == 'ok' and r0[1]['changed'] is False and r1[0] == 'ok' and r1[1]['changed'] is False and head(os_, 'Q') == hd
                                      and len(after_plain['source_snapshots']) - len(snap['source_snapshots']) == 1 and declared(os_) == [])
                        if was_approved:
                            good &= check('%s the claim-free old message leaves the approval governing' % tag, approved(os_, K('Q'), '2026-12'))
                        target = 'A1' if known else 'P'
                        late = q(target, amount=amount, as_of=order) if carrier == 'outside' else tx('Q', '2026-12-03', amount, as_of=order, supersedes_source_id=target)
                        before = lifecycle(os_)
                        r = send(os_, 'g1a-old-claim', [late])
                        after = lifecycle(os_)
                        good &= check('%s re-sent with the claim: changed=True' % tag, r[0] == 'ok' and r[1]['changed'] is True)
                        good &= check('%s governing head unchanged (same snapshot, amount, order)' % tag, head(os_, 'Q') == hd)
                        good &= check('%s source versions added: %d' % (tag, 0 if carrier == 'outside' else 1), delta(before, after)['source_snapshots'] == (0 if carrier == 'outside' else 1))
                        good &= check('%s claim recorded exactly once' % tag, declared(os_) == [('SOURCE_CLAIM_DECLARED', K(target))])
                        good &= check('%s earlier history is an unchanged prefix' % tag, prefix_kept(before, after, HISTORY))
                        good &= check('%s no approval governs in December straight after the claim (before any new run)' % tag, not approved(os_, K('Q'), '2026-12'))
                        if known:
                            good &= check('%s known target: linked and held with its receipt straight after the claim' % tag, (K('A1'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_))
                        else:
                            good &= check('%s unknown target: no link yet, recorded as unresolved' % tag, not [l for l in links(os_) if l[1] == K('Q')] and ('SOURCE_SUPERSESSION_UNRESOLVED', K('P')) in claim_events(os_, 'Q'))
                            prep(os_); a = gov(os_, K('Q'), '2026-12')
                            good &= check('%s unknown target: blocked as unresolved, not eligible, approval refused' % tag, a is not None and UNRESOLVED in a['blockers'] and not a['eligible'] and review(os_, REV3, a, 'approve')[0] == 'refused')
                            send(os_, 'g1a-p', p_rows())
                            good &= check('%s target arrives: linked and held with its receipt at once, without a re-send' % tag, (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_))
                        prep(os_)
                        good &= check('%s after preparation: held under November with its receipt, no December artifact' % tag, {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
                        good &= check('%s November approval of A1 governs; nothing approved twice' % tag, approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12'))
                        snap = rows_of(os_)
                        r = send(os_, 'g1a-old-claim-repeat', [late]); r2 = send(os_, 'g1a-old-plain-repeat', [q(amount=amount, as_of=order)])
                        good &= check('%s repeats of the claim message and of the claim-free message: changed=False, no lifecycle row added' % tag,
                                      r[0] == 'ok' and r[1]['changed'] is False and r2[0] == 'ok' and r2[1]['changed'] is False and rows_of(os_) == snap)
                        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    print('    variants:', n)
    return 'OK' if good else 'WEAK'


@probe('G1b', 'RF-01 / clause 7', 'clause 7 still governs: a retained message re-sent with a DIFFERENT claim is a second claim (not applied); a second claim after a first claim that came by the retained path leaves the first standing')
def _():
    good = True
    for first_linked in (True, False):
        tag = '[first claim linked]' if first_linked else '[first claim waiting]'
        os_ = base()
        if first_linked:
            send(os_, 'g1b-b', b_rows())
        send(os_, 'g1b-first', q_rows('B', as_of=7)); prep(os_)
        r0 = send(os_, 'g1b-old-plain', [q(as_of=6)])
        before = rows_of(os_); place = where(os_, K('Q')); hd = head(os_, 'Q')
        r = send(os_, 'g1b-old-different', [q('P', as_of=6)])
        after = rows_of(os_)
        good &= check('%s claim-free old message retained with changed=False; re-sent with a different target: changed=True' % tag, r0[0] == 'ok' and r0[1]['changed'] is False and r[0] == 'ok' and r[1]['changed'] is True)
        good &= check('%s recorded as a conflict for P, once' % tag, [c for c in claim_events(os_, 'Q') if c[1] == K('P')] == [('SOURCE_CLAIM_CONFLICT_RECORDED', K('P'))])
        good &= check('%s head unchanged; no link, move or binding row added; no source version added' % tag,
                      head(os_, 'Q') == hd and all(before[t] == after[t] for t in ('links', 'moves', 'bindings', 'source_snapshots')) and where(os_, K('Q')) == place)
        send(os_, 'g1b-p', p_rows()); prep(os_)
        a = gov(os_, K('Q'), '2026-12')
        good &= check('%s after P (replacing locked A1) arrives: no link P->Q, Q not moved into the hold' % tag, (K('P'), K('Q')) not in links(os_) and K('Q') not in held_under(os_))
        good &= check('%s Q carries the conflict blocker and cannot be approved' % tag, a is not None and CONFLICT in a['blockers'] and not a['eligible'] and review(os_, REV2, a, 'approve')[0] == 'refused')
        snap = rows_of(os_)
        r = send(os_, 'g1b-old-different-repeat', [q('P', as_of=6)])
        good &= check('%s repeat adds nothing' % tag, r[0] == 'ok' and r[1]['changed'] is False and rows_of(os_) == snap)
    # the first claim arrived by the retained path; then a newer message names a different target
    os_ = base()
    send(os_, 'g1b2-p', p_rows()); send(os_, 'g1b2-q7', [q(as_of=7), rc('Q', '2026-12-03', '40.00')]); send(os_, 'g1b2-q6', [q(as_of=6)])
    send(os_, 'g1b2-q6-claim', [q('P', as_of=6)]); prep(os_)
    good &= check('[retained first claim] Q linked to P and held with its receipt', (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_))
    send(os_, 'g1b2-b', b_rows())
    before = rows_of(os_)
    r = send(os_, 'g1b2-newer-different', [q('B', as_of=8)])
    good &= check('[retained first claim] newer message naming B: changed=True, recorded as a conflict', r[0] == 'ok' and r[1]['changed'] is True and ('SOURCE_CLAIM_CONFLICT_RECORDED', K('B')) in claim_events(os_, 'Q'))
    prep(os_)
    good &= check('[retained first claim] first claim stands: still held under November with its receipt, not linked to B', {K('Q'), 'receipt-Q'} <= held_under(os_) and (K('B'), K('Q')) not in links(os_))
    good &= check('[retained first claim] B is not retired and Q has no December artifact', head(os_, 'B')['removed'] == 0 and gov(os_, K('B'), '2026-12') is not None and gov(os_, K('Q'), '2026-12') is None)
    good &= check('[retained first claim] audit chain verifies', os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('G1c', 'RF-01 / clause 4', 'the claimant of an unknown target is replaced by Z, approved before or after the retained claim; when the target arrives nothing stays approved twice')
def _():
    good = True; note = False
    z = sup('Z', '2026-12-05', '40.00', 'Q')
    z_rows = [z, rc('Z', '2026-12-05', '40.00'), stmt([z], DEC, opening='100.00')]
    for z_first in (True, False):
        tag = '[Z approved before the claim]' if z_first else '[Z arrives after the claim]'
        os_ = base()
        send(os_, 'g1c-q7', [q(as_of=7), rc('Q', '2026-12-03', '40.00')]); send(os_, 'g1c-q6', [q(as_of=6)])
        if z_first:
            send(os_, 'g1c-z', z_rows); prep(os_)
            a = clear_and_approve(os_, 'Z')
            good &= check('%s Z approved in December before any claim exists' % tag, a is not None and a['review_status'] == 'approve')
        r = send(os_, 'g1c-q6-claim', [q('P', as_of=6)])
        good &= check('%s claim recorded, waiting for P' % tag, r[0] == 'ok' and r[1]['changed'] and ('SOURCE_SUPERSESSION_UNRESOLVED', K('P')) in claim_events(os_, 'Q'))
        if z_first:
            still = approved(os_, K('Z'), '2026-12')
            print('    %s while P has not arrived, the approval of Z governs: %s (UC-20, owner observation; not counted)' % (tag, still)); note |= still
        else:
            send(os_, 'g1c-z', z_rows); prep(os_)
            a = clear_and_approve(os_, 'Z')
            still = a is not None and a['review_status'] == 'approve'
            print('    %s while P has not arrived, Z can be approved: %s (UC-20, owner observation; not counted)' % (tag, still)); note |= still
        send(os_, 'g1c-p', p_rows())
        good &= check('%s P arrives: Q links to P without a re-send' % tag, (K('P'), K('Q')) in links(os_))
        good &= check('%s P arrives: the December approval of Z stops governing at once (before any new run)' % tag, not approved(os_, K('Z'), '2026-12'))
        good &= check('%s P arrives: Z and its receipt are held under locked November at once' % tag, {K('Z'), 'receipt-Z'} <= held_under(os_))
        prep(os_)
        a = clear_and_approve(os_, 'Z')
        fin = attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'Fictional finalization without acknowledgement')
        print('    %s Z %s | links %s | held %s | finalize December: %s' % (tag, brief(a), links(os_), sorted(held_under(os_)), fin))
        good &= check('%s NOT approved twice: A1 in locked November and Z (or Q) in open December' % tag, approved(os_, K('A1'), '2026-11') and not approved(os_, K('Z'), '2026-12') and not approved(os_, K('Q'), '2026-12'))
        good &= check('%s December does not finalize without acknowledgement' % tag, fin[0] == 'refused')
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return ('NOTE' if note else 'OK') if good else 'WEAK'


@probe('G1d', 'RF-01', 'removed head: the claimant was withdrawn by the feed before the retained message is re-sent with the claim; the claim is linked and holds the row when it comes back')
def _():
    good = True
    for known in (True, False):
        tag = '[known]' if known else '[unknown]'
        os_ = base()
        if known:
            send(os_, 'g1d-p', p_rows())
        send(os_, 'g1d-q7', q_rows(as_of=7)); send(os_, 'g1d-q6', [q(as_of=6)]); prep(os_)
        r = send(os_, 'g1d-withdrawn', [dict(q(as_of=8), tombstone=True, removal_reason='feed_removed')]); prep(os_)
        good &= check('%s Q withdrawn by the feed (head removed)' % tag, r[0] == 'ok' and head(os_, 'Q')['removed'] == 1)
        hd = head(os_, 'Q')
        r = send(os_, 'g1d-q6-claim', [q('P', as_of=6)])
        good &= check('%s the retained older message re-sent with the claim: changed=True, recorded once, withdrawal still governs' % tag, r[0] == 'ok' and r[1]['changed'] is True and declared(os_) == [('SOURCE_CLAIM_DECLARED', K('P'))] and head(os_, 'Q') == hd)
        if not known:
            send(os_, 'g1d-p', p_rows())
        good &= check('%s the withdrawn claimant is linked to P' % tag, (K('P'), K('Q')) in links(os_))
        r = send(os_, 'g1d-q9', [q(as_of=9), rc('Q', '2026-12-03', '40.00')])
        good &= check('%s Q re-sent after the withdrawal, without the claim: held under locked November with its receipt at once' % tag, r[0] == 'ok' and head(os_, 'Q')['removed'] == 0 and {K('Q'), 'receipt-Q'} <= held_under(os_))
        prep(os_)
        a = clear_and_approve(os_, 'Q')
        good &= check('%s no December artifact, nothing approved twice' % tag, a is None and approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12'))
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('G1e', 'RF-01 / clauses 4, 6', 'the target arrives after the claimant row and its receipt were revised without the claim; later versions that omit the claim do not withdraw it')
def _():
    good = True
    os_ = base()
    send(os_, 'g1e-q7', q_rows(as_of=7)); send(os_, 'g1e-q6', [q(as_of=6)])
    r = send(os_, 'g1e-q6-claim', [q('P', as_of=6)])
    good &= check('retained message re-sent with the claim for an unknown target: recorded', r[0] == 'ok' and r[1]['changed'] and declared(os_) == [('SOURCE_CLAIM_DECLARED', K('P'))])
    send(os_, 'g1e-q8', [q(amount='41.00', as_of=8), rc('Q', '2026-12-03', '41.00'), stmt([q(amount='41.00')], DEC, opening='100.00')]); prep(os_)
    a = clear_all(os_, 'Q')
    good &= check('row revised without the claim (clause 6): still blocked as unresolved, approval refused', a is not None and UNRESOLVED in a['blockers'] and review(os_, REV3, a, 'approve')[0] == 'refused')
    send(os_, 'g1e-receipt', [rc('Q', '2026-12-03', '41.00', content='Fictional revised receipt for Q')]); prep(os_)
    a = clear_all(os_, 'Q')
    good &= check('receipt revised: still blocked as unresolved, approval refused', a is not None and UNRESOLVED in a['blockers'] and review(os_, REV3, a, 'approve')[0] == 'refused')
    hd = head(os_, 'Q')
    send(os_, 'g1e-p', p_rows())
    good &= check('P arrives after both revisions: the revised row is linked and held with its receipt at once; head unchanged', (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_) and head(os_, 'Q') == hd)
    send(os_, 'g1e-q9', [q(amount='42.00', as_of=9), rc('Q', '2026-12-03', '42.00')]); prep(os_)
    good &= check('a later version without the claim stays held with its receipt; no December artifact', {K('Q'), 'receipt-Q'} <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
    good &= check('nothing approved twice; audit verifies', approved(os_, K('A1'), '2026-11') and not approved(os_, K('Q'), '2026-12') and os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('G1f', 'RF-01', 'several retained versions: the claim arrives on the oldest of two claim-free retained messages, and on a retained message whose data differs from the governing row')
def _():
    good = True
    for variant in ('oldest-of-two', 'different-data'):
        os_ = base(); send(os_, 'g1f-p', p_rows())
        send(os_, 'g1f-q7', q_rows(as_of=7)); prep(os_)
        if variant == 'oldest-of-two':
            send(os_, 'g1f-q6', [q(as_of=6)]); send(os_, 'g1f-q5', [q(as_of=5)]); late = q('P', as_of=5)
        else:
            send(os_, 'g1f-q6', [q(amount='39.00', as_of=6)]); late = q('P', amount='39.00', as_of=6)
        hd = head(os_, 'Q'); before = lifecycle(os_)
        r = send(os_, 'g1f-claim', [late]); after = lifecycle(os_)
        good &= check('[%s] changed=True, no source version added, head unchanged, declared once' % variant, r[0] == 'ok' and r[1]['changed'] is True and delta(before, after)['source_snapshots'] == 0 and head(os_, 'Q') == hd and declared(os_) == [('SOURCE_CLAIM_DECLARED', K('P'))])
        good &= check('[%s] linked and held with its receipt at once' % variant, (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_))
        prep(os_)
        good &= check('[%s] no December artifact; governing amount still 40.00' % variant, gov(os_, K('Q'), '2026-12') is None and head(os_, 'Q')['amount'] == '40.00')
    return 'OK' if good else 'WEAK'


@probe('G1g', 'RF-01 / clause 5', 'a message without any order value (legacy arrival) against a row governed by a sequence number: claim-free first, then with the claim; repeats')
def _():
    good = True; note = False
    os_ = base(); send(os_, 'g1g-p', p_rows())
    send(os_, 'g1g-q7', q_rows(as_of=7)); prep(os_)
    hd = head(os_, 'Q')
    for same in (True, False):
        amount = '40.00' if same else '41.00'
        tag = '[unordered message, %s data]' % ('same' if same else 'different')
        before = rows_of(os_)
        r0 = send(os_, 'g1g-plain-%s' % amount, [q(amount=amount)]); mid = rows_of(os_)
        r1 = send(os_, 'g1g-plain-again-%s' % amount, [q(amount=amount)]); after = rows_of(os_)
        print('    %s claim-free: %s then %s | source versions added: %d then %d | head unchanged: %s' % (tag, r0[1] if r0[0] == 'ok' else r0, r1[1] if r1[0] == 'ok' else r1,
              len(mid['source_snapshots']) - len(before['source_snapshots']), len(after['source_snapshots']) - len(mid['source_snapshots']), head(os_, 'Q') == hd))
        good &= check('%s never replaces the governing row' % tag, head(os_, 'Q') == hd)
        if len(after['source_snapshots']) - len(mid['source_snapshots']):
            note = True
            print('    observation: an identical repeat of an unordered message with different data adds one more retained source version each time (changed=False).')
    os2 = base(); send(os2, 'g1g2-p', p_rows()); send(os2, 'g1g2-q7', q_rows(as_of=7)); prep(os2); hd2 = head(os2, 'Q')
    send(os2, 'g1g2-plain', [q()]); r = send(os2, 'g1g2-claim', [q('P')])
    good &= check('unordered message with the SAME data, claim-free and then carrying the first claim: changed=True, declared once, head unchanged, linked and held at once',
                  r[0] == 'ok' and r[1]['changed'] is True and declared(os2) == [('SOURCE_CLAIM_DECLARED', K('P'))] and head(os2, 'Q') == hd2 and (K('P'), K('Q')) in links(os2) and {K('Q'), 'receipt-Q'} <= held_under(os2))
    snap2 = rows_of(os2); r = send(os2, 'g1g2-claim-repeat', [q('P')])
    good &= check('its repeat: changed=False and no lifecycle row added', r[0] == 'ok' and r[1]['changed'] is False and rows_of(os2) == snap2)
    r = send(os_, 'g1g-claim', [q('P', amount='41.00')])
    good &= check('unordered message with different data, now carrying the first claim: changed=True, declared once, head unchanged', r[0] == 'ok' and r[1]['changed'] is True and declared(os_) == [('SOURCE_CLAIM_DECLARED', K('P'))] and head(os_, 'Q') == hd)
    good &= check('applied: linked and held with its receipt at once', (K('P'), K('Q')) in links(os_) and {K('Q'), 'receipt-Q'} <= held_under(os_))
    snap = rows_of(os_)
    r = send(os_, 'g1g-claim-repeat', [q('P', amount='41.00')]); after = rows_of(os_)
    same_rows = all(snap[t] == after[t] for t in ('bindings', 'moves', 'links', 'events', 'decisions', 'heads'))
    good &= check('repeat of the claim message: changed=False; no binding, move, link, event, decision or head change', r[0] == 'ok' and r[1]['changed'] is False and same_rows)
    if len(after['source_snapshots']) != len(snap['source_snapshots']):
        note = True
        print('    observation: the repeat added %d retained source version(s).' % (len(after['source_snapshots']) - len(snap['source_snapshots'])))
    prep(os_)
    good &= check('no December artifact; nothing approved twice; audit verifies', gov(os_, K('Q'), '2026-12') is None and not approved(os_, K('Q'), '2026-12') and os_.verify_audit(PREP))
    return ('NOTE' if note else 'OK') if good else 'WEAK'


@probe('G1h', 'RF-01 / clause 3', 'the retained message re-sent with a first claim on an OPEN December row that is itself approved: linked at once, the target retired, both approvals stop governing, the transition review is required')
def _():
    good = True
    for was_approved in (False, True):
        tag = '[Q approved]' if was_approved else '[Q eligible]'
        os_ = base()
        rows = [tx('B', '2026-12-02', '45.00'), rc('B', '2026-12-02', '45.00'), q(as_of=7), rc('Q', '2026-12-03', '40.00')]
        send(os_, 'g1h-rows', rows + [stmt(rows, DEC, opening='100.00')]); prep(os_)
        r = review(os_, REV2, gov(os_, K('B'), '2026-12'), 'approve')
        good &= check('%s B approved in open December' % tag, r[0] == 'ok' and approved(os_, K('B'), '2026-12'))
        if was_approved:
            r = review(os_, REV2, gov(os_, K('Q'), '2026-12'), 'approve')
            good &= check('%s Q approved in open December' % tag, r[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
        send(os_, 'g1h-q6', [q(as_of=6)])
        good &= check('%s the claim-free old message changes nothing' % tag, approved(os_, K('B'), '2026-12') and approved(os_, K('Q'), '2026-12') == was_approved)
        hd = head(os_, 'Q'); count = p.approval_count(os_)
        r = send(os_, 'g1h-q6-claim', [q('B', as_of=6)])
        good &= check('%s re-sent with the claim: changed=True, linked to B at once, head unchanged, B retired' % tag, r[0] == 'ok' and r[1]['changed'] is True and (K('B'), K('Q')) in links(os_) and head(os_, 'Q') == hd and head(os_, 'B')['removed'] == 1)
        good &= check('%s straight after the claim neither approval governs in December; no decision added' % tag, not approved(os_, K('Q'), '2026-12') and not approved(os_, K('B'), '2026-12') and p.approval_count(os_) == count)
        send(os_, 'g1h-statement', [stmt([q(as_of=7)], DEC, opening='100.00')]); prep(os_)
        a = gov(os_, K('Q'), '2026-12')
        good &= check('%s after preparation Q carries the transition review and is not eligible; B has left the population' % tag, a is not None and TRANSITION in a['blockers'] and not a['eligible'] and gov(os_, K('B'), '2026-12') is None)
        good &= check('%s approval of Q is refused until the transition is dispositioned' % tag, review(os_, REV3, a, 'approve')[0] == 'refused')
        a = clear_all(os_, 'Q'); r = review(os_, REV3, a, 'approve'); print('    %s Q after the ordinary dispositions: %s | review: %s' % (tag, brief(a), r))
        good &= check('%s after the ordinary dispositions an independent reviewer approves Q; one charge approved once in December' % tag, r[0] == 'ok' and approved(os_, K('Q'), '2026-12') and not approved(os_, K('B'), '2026-12'))
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('G5a', 'clause 5', 'an identical repeat of the message for a row that its replacement has already retired (both rows in open December; and with the chain held under locked November)')
def _():
    good = True; note = False
    for locked in (False, True):
        tag = '[chain held under November]' if locked else '[open December only]'
        os_ = base()
        if locked:
            send(os_, 'g5a-p', p_rows())
        qrows = [q('P' if locked else None, as_of=7), rc('Q', '2026-12-03', '40.00')]
        send(os_, 'g5a-q', qrows)
        zr = [sup('Z', '2026-12-05', '40.00', 'Q'), rc('Z', '2026-12-05', '40.00')]
        send(os_, 'g5a-z', zr + [stmt(zr, DEC, opening='100.00')]); prep(os_)
        a = clear_and_approve(os_, 'Z')
        before = rows_of(os_); hd = head(os_, 'Q'); was = approved(os_, K('Z'), '2026-12'); held = held_under(os_)
        r = send(os_, 'g5a-q-again', qrows)
        after = rows_of(os_)
        added = len(after['source_snapshots']) - len(before['source_snapshots'])
        print('    %s Q before the repeat: %s | Z approved: %s | held: %s' % (tag, hd, was, sorted(held)))
        print('    %s identical repeat of Q in a new envelope: %s | source versions added: %d | Q now: %s' % (tag, r[1] if r[0] == 'ok' else r, added, head(os_, 'Q')))
        if r[0] == 'ok' and (r[1]['changed'] or added):
            note = True
        prep(os_)
        good &= check('%s nothing left its hold; Q has no December artifact' % tag, held <= held_under(os_) and gov(os_, K('Q'), '2026-12') is None)
        good &= check('%s nothing approved twice (A1 in November with Q or Z in December while the chain reaches A1)' % tag, not (locked and (approved(os_, K('Q'), '2026-12') or approved(os_, K('Z'), '2026-12'))))
        good &= check('%s audit chain verifies' % tag, os_.verify_audit(PREP))
    if note:
        print('    observation: the repeat is stored as a new version of the retired row and answers changed=True; the row is retired again in the same intake.')
    return ('NOTE' if note else 'OK') if good else 'WEAK'


# =======================================================================================
# RF-02
# =======================================================================================

def three_selectors(os_):
    os_.grant_authority(ADMIN, DL.id, ['disposition', 'lock', 'review', 'finalize'], 'Fictional probe authority: a third selector who could otherwise review and finalize')
    os_.grant_authority(ADMIN, DR.id, ['disposition', 'review', 'finalize'], 'Fictional probe authority: a selector who could otherwise review and finalize')
    return os_


@probe('G2a', 'RF-02', 'three people select in turn (first, confirming, replacing): all three stay contributors of the row, its revision, its replacement and the replacement of that; none can approve or finalize; an independent person can; earlier records unchanged')
def _():
    good = True
    for version in ('row', 'revision', 'replacement', 'second replacement'):
        tag = '[%s]' % version
        os_ = three_selectors(base())
        send(os_, 'g2a-targets', b_rows() + b_rows('B2', '2026-12-04', '40.00'))
        send(os_, 'g2a-first', q_rows('B')); send(os_, 'g2a-second', [q('B2')]); prep(os_)
        r1 = select(os_, DR, 'B2'); one = dispositions(os_)
        r2 = select(os_, DR2, 'B2'); two = dispositions(os_)
        r3 = select(os_, DL, 'B'); three = dispositions(os_)
        good &= check('%s three selections recorded (choose B2, confirm B2, replace by B)' % tag, r1[0] == 'ok' and r2[0] == 'ok' and r3[0] == 'ok' and len(three) == len(two) + 1 == len(one) + 2)
        good &= check('%s earlier selection records are byte-identical after each later one' % tag, two[:len(one)] == one and three[:len(two)] == two)
        key = 'Q'
        if version == 'revision':
            send(os_, 'g2a-rev', [q(amount='41.00'), rc('Q', '2026-12-03', '41.00'), stmt([q(amount='41.00')], DEC, opening='100.00')])
        if version in ('replacement', 'second replacement'):
            zr = [sup('Z', '2026-12-05', '40.00', 'Q'), rc('Z', '2026-12-05', '40.00')]; send(os_, 'g2a-z', zr + [stmt(zr, DEC, opening='100.00')]); key = 'Z'
        if version == 'second replacement':
            wr = [sup('W', '2026-12-06', '40.00', 'Z'), rc('W', '2026-12-06', '40.00')]; send(os_, 'g2a-w', wr + [stmt(wr, DEC, opening='100.00')]); key = 'W'
        prep(os_)
        a = clear_all(os_, key)
        good &= check('%s %s is eligible and pending' % (tag, key), a is not None and a['eligible'] and a['review_status'] == 'pending')
        if a is None:
            continue
        good &= check('%s all three selectors are contributors of %s' % (tag, key), {DR.id, DR2.id, DL.id} <= set(a['contributors'] or []))
        for who in (DR, DR2, DL):
            r = review(os_, who, a, 'approve')
            good &= check('%s selector %s is refused as reviewer of %s' % (tag, who.id, key), r[0] == 'refused' and 'Independent' in r[2])
        for who in (DR, DL):
            r = attempt(os_.finalize_package, who, '2026-12', 'card_preparation', 'Fictional finalization by a selector', 'Fictional acknowledgement of carried items')
            good &= check('%s selector %s is refused as finalizer' % (tag, who.id), r[0] == 'refused' and 'Independent finalizer' in r[2])
        r = review(os_, REV3, a, 'approve')
        good &= check('%s an independent reviewer approves %s' % (tag, key), r[0] == 'ok' and approved(os_, K(key), '2026-12'))
        r = attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'Fictional independent finalization', 'Fictional acknowledgement of carried items')
        good &= check('%s an independent finalizer finalizes December' % tag, r[0] == 'ok')
        good &= check('%s selection records still byte-identical; audit verifies' % tag, dispositions(os_)[:len(three)] == three and os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


@probe('G2b', 'RF-02', "a person who approved the row as an independent reviewer and LATER records the selection: the earlier approval is not revived, and that person cannot approve again")
def _():
    good = True
    os_ = three_selectors(base())
    send(os_, 'g2b-targets', b_rows() + b_rows('B2', '2026-12-04', '40.00'))
    send(os_, 'g2b-first', q_rows('B'))
    send(os_, 'g2b-statement', [stmt([q(), tx('B2', '2026-12-04', '40.00', desc='OPEN ROW DEMO')], DEC, opening='100.00')]); prep(os_)
    a = clear_all(os_, 'Q'); r = review(os_, DR, a, 'approve')
    good &= check('DR approves Q as an independent reviewer (one claim, linked to B)', r[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
    count = p.approval_count(os_)
    send(os_, 'g2b-second', [q('B2')])
    good &= check('second claim: the approval stops governing at once', not approved(os_, K('Q'), '2026-12'))
    prep(os_)
    r = select(os_, DR, 'B'); print('    DR records the selection (first target stands):', r)
    prep(os_); a = clear_all(os_, 'Q')
    print('    Q after the selection:', brief(a), '| contributors:', a['contributors'] if a else None)
    good &= check('the earlier approval by DR does not govern after the selection', not approved(os_, K('Q'), '2026-12') and p.approval_count(os_) == count)
    if r[0] == 'ok':
        good &= check('DR is a contributor and is refused as reviewer', a is not None and DR.id in (a['contributors'] or []) and review(os_, DR, a, 'approve')[0] == 'refused')
        good &= check('an independent reviewer approves', review(os_, REV3, a, 'approve')[0] == 'ok' and approved(os_, K('Q'), '2026-12'))
    return 'OK' if good else 'WEAK'


@probe('G2c', 'RF-02', 'ordinary dispositions keep their rule: signature of contributors after a first and a superseding ordinary disposition by different people (compare the printed line between checkpoints)')
def _():
    os_ = three_selectors(base())
    send(os_, 'g2c-b', b_rows()); send(os_, 'g2c-q', q_rows('B')); prep(os_)
    sig = []
    r = dispose(os_, K('Q'), TRANSITION, 'settlement_verified', period='2026-12', who=DR); prep(os_)
    a = gov(os_, K('Q'), '2026-12'); sig.append(('after DR settlement_verified', r[0], sorted(a['contributors'] or []), a['blockers']))
    send(os_, 'g2c-receipt', [rc('Q', '2026-12-03', '40.00', content='Fictional revised receipt for Q')]); prep(os_)
    a = gov(os_, K('Q'), '2026-12'); sig.append(('after receipt revision', sorted(a['contributors'] or []), a['blockers']))
    for code, choice in ((REVISED, 'revised_evidence_accepted'), (TRANSITION, 'settlement_verified')):
        a = gov(os_, K('Q'), '2026-12')
        if code in a['blockers']:
            r = dispose(os_, K('Q'), code, choice, period='2026-12', who=DR2); prep(os_)
            a = gov(os_, K('Q'), '2026-12'); sig.append(('after DR2 ' + choice, r[0], sorted(a['contributors'] or []), a['blockers']))
    a = gov(os_, K('Q'), '2026-12')
    sig.append(('DR may approve', review(os_, DR, a, 'approve')[0], 'DR2 may approve', review(os_, DR2, a, 'approve')[0], 'REV3 may approve', review(os_, REV3, a, 'approve')[0]))
    print('    ORDINARY-RULE-SIGNATURE ' + json.dumps(sig))
    return 'OK'


@probe('G2d', 'RF-02', 'a selection for one row does not make its author a contributor of an unrelated row in the same period, nor of a row in another period')
def _():
    good = True
    os_ = three_selectors(base())
    send(os_, 'g2d-targets', b_rows() + b_rows('B2', '2026-12-04', '40.00') + [tx('U', '2026-12-08', '15.00'), rc('U', '2026-12-08', '15.00')])
    send(os_, 'g2d-first', q_rows('B')); send(os_, 'g2d-second', [q('B2')]); prep(os_)
    r = select(os_, DR, 'B2')
    send(os_, 'g2d-statement', [stmt([q(), tx('U', '2026-12-08', '15.00')], DEC, opening='100.00')]); prep(os_)
    u = clear_all(os_, 'U'); a1 = gov(os_, K('A2'), '2026-11')
    good &= check('selection recorded', r[0] == 'ok')
    good &= check('the selector is not a contributor of the unrelated December row U', u is not None and DR.id not in (u['contributors'] or []))
    good &= check('the selector is not a contributor of the locked November row A2', a1 is not None and DR.id not in (a1['contributors'] or []))
    r = review(os_, DR, u, 'approve'); print('    U:', brief(u), '| DR approves U:', r)
    good &= check('the selector may approve the unrelated row U (ordinary independence unchanged)', r[0] == 'ok')
    qa = clear_all(os_, 'Q')
    good &= check('the selector is a contributor of Q and refused there', qa is not None and DR.id in (qa['contributors'] or []) and review(os_, DR, qa, 'approve')[0] == 'refused')
    b2 = gov(os_, K('B2'), '2026-12'); b = clear_all(os_, 'B')
    print('    B2 (selected target, retired by the link):', brief(b2), '| B (de-selected target):', brief(b), '| contributors of B:', b['contributors'] if b else None)
    return 'OK' if good else 'WEAK'


@probe('G2e', 'RF-02', 'scope isolation: the same row identities and the same person ids in a second client scope of the same database; a selection in one scope adds no contributor in the other')
def _():
    import copy
    from accounting_agent.core import Actor
    from accounting_agent.service import AccountingOS
    good = True
    second = 'second_probe_client'; scope2 = h.ORG + '/' + second + '/local'
    path = Path(h.TMP.name) / 'fable-rf-two-scopes.sqlite3'
    os_ = AccountingOS(path, [h.SCOPE, scope2]); os_.probe_path = path
    people = dict(ADMIN=ADMIN, PREP=PREP, PREP2=PREP2, CTRL=h.CTRL, REV3=REV3, PADMIN=p.PADMIN, DISP=DISP, WORKER=h.WORKER, DR=DR, DR2=DR2)
    A = people; B = {k: Actor(v.id, v.role, h.ORG, second, kind=v.kind) for k, v in people.items()}
    for X, client in ((A, h.CLIENT), (B, second)):
        profile = copy.deepcopy(h.PROFILE); profile['client_id'] = client
        sid = os_.onboard(X['PREP'], profile)
        for who, perms in ((X['CTRL'], ['approve_profile', 'approve_rule', 'approve_mandate']), (X['REV3'], ['review']), (X['DISP'], ['disposition']), (X['PADMIN'], ['lock']),
                           (X['DR'], ['disposition', 'review']), (X['DR2'], ['disposition', 'review'])):
            os_.grant_authority(X['ADMIN'], who.id, perms, 'Fictional two-scope probe authority')
        os_.approve_profile_version(X['CTRL'], sid, 'Explicit independent approval of the fictional probe profile')
        os_.open_period(X['PADMIN'], *DEC, 'Fictional probe period')

    def deliver(X, client, name, rows):
        pk = h.packet(name, rows); pk['client_id'] = client
        return attempt(os_.intake, X['PREP2'], pk)

    def prepare(X):
        os_.enqueue(X['PREP2'], 'card_preparation', '2026-12'); os_.drain(X['WORKER'])

    def artifact(X, sid):
        found = [a for a in os_.state(X['PREP'])['artifacts'] if a['item_key'] == K(sid) and a['period_id'] == '2026-12' and a['governing'] and a['kind'] == 'card_proposal']
        return found[0] if found else None

    def choose(X, who, target):
        r = [(row['id'], row['hash']) for row in os_.export(X['PREP'])['evidence_history'] if row['source_key'] == 'receipt-Q']
        return attempt(os_.disposition, X[who], 'card_preparation', '2026-12', K('Q'), CONFLICT, p.CHOICE, {'target_key': K(target)}, [{'snapshot_id': r[-1][0], 'hash': r[-1][1]}], 'Fictional independent target selection')

    for X, client in ((A, h.CLIENT), (B, second)):
        r1 = deliver(X, client, 'g2e-targets', b_rows() + b_rows('B2', '2026-12-04', '40.00'))
        r2 = deliver(X, client, 'g2e-first', q_rows('B')); r3 = deliver(X, client, 'g2e-second', [q('B2')]); prepare(X)
        a = artifact(X, 'Q')
        good &= check('[%s] same identities delivered; Q is contested' % client, r1[0] == r2[0] == r3[0] == 'ok' and a is not None and CONFLICT in a['blockers'])
    r = choose(A, 'DR', 'B2'); prepare(A); prepare(B)
    qa, qb = artifact(A, 'Q'), artifact(B, 'Q')
    good &= check('selection by DR recorded in the first scope only', r[0] == 'ok' and len([d for d in os_.export(A['PREP'])['dispositions'] if d['choice'] == p.CHOICE]) == 1 and not [d for d in os_.export(B['PREP'])['dispositions'] if d['choice'] == p.CHOICE])
    good &= check('first scope: DR is a contributor of Q and the conflict is cleared', qa is not None and DR.id in (qa['contributors'] or []) and CONFLICT not in qa['blockers'])
    good &= check('second scope: Q is still contested and the person with the same id is not a contributor', qb is not None and CONFLICT in qb['blockers'] and DR.id not in (qb['contributors'] or []))
    r = choose(B, 'DR2', 'B'); prepare(A); prepare(B)
    qa, qb = artifact(A, 'Q'), artifact(B, 'Q')
    good &= check('selection by DR2 recorded in the second scope', r[0] == 'ok')
    good &= check('second scope: DR2 is a contributor, DR is not', qb is not None and DR2.id in (qb['contributors'] or []) and DR.id not in (qb['contributors'] or []))
    good &= check('first scope: unchanged, DR is a contributor, DR2 is not', qa is not None and DR.id in (qa['contributors'] or []) and DR2.id not in (qa['contributors'] or []))
    good &= check('both audit chains verify', os_.verify_audit(A['PREP']) and os_.verify_audit(B['PREP']))
    return 'OK' if good else 'WEAK'


@probe('G2f', 'RF-02', 'ancestry retargeted: the replacement Z of Q is itself contested and a person selects a target other than Q; the earlier selector for Q is still a contributor of Z and cannot approve it')
def _():
    good = True
    os_ = three_selectors(base())
    send(os_, 'g2f-targets', b_rows() + b_rows('B2', '2026-12-04', '40.00') + b_rows('B3', '2026-12-06', '40.00'))
    send(os_, 'g2f-first', q_rows('B')); send(os_, 'g2f-second', [q('B2')]); prep(os_)
    r1 = select(os_, DR, 'B2')
    zr = [sup('Z', '2026-12-05', '40.00', 'Q'), rc('Z', '2026-12-05', '40.00')]
    send(os_, 'g2f-z', zr + [stmt(zr, DEC, opening='100.00')]); send(os_, 'g2f-z-second', [dict(tx('Z', '2026-12-05', '40.00'), supersedes=K('B3'))]); prep(os_)
    a = gov(os_, K('Z'), '2026-12')
    good &= check('Q selected by DR; Z replaces Q and is itself contested (Q, B3)', r1[0] == 'ok' and a is not None and CONFLICT in a['blockers'])
    r2 = select(os_, DR2, 'B3', item='Z'); prep(os_)
    a = clear_all(os_, 'Z')
    print('    DR2 selects B3 for Z:', r2, '| Z:', brief(a), '| links:', links(os_))
    good &= check('Z is eligible after the selection and the ordinary dispositions', a is not None and a['eligible'])
    good &= check('both the selector for Q (DR) and the selector for Z (DR2) are contributors of Z', a is not None and {DR.id, DR2.id} <= set(a['contributors'] or []))
    good &= check('neither can approve Z; an independent reviewer can', a is not None and review(os_, DR, a, 'approve')[0] == 'refused' and review(os_, DR2, a, 'approve')[0] == 'refused' and review(os_, REV3, a, 'approve')[0] == 'ok')
    good &= check('audit chain verifies', os_.verify_audit(PREP))
    return 'OK' if good else 'WEAK'


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
            traceback.print_exc(file=sys.stdout)
            verdict = 'ERROR'
        print('--> %s %s' % (pid, verdict))
        results.append((pid, ticket, verdict))
    print('\nSUMMARY')
    for pid, ticket, verdict in results:
        print('  %-5s %-22s %s' % (pid, ticket.replace(' ', '_'), verdict))
    bad = [r for r in results if r[2] in ('WEAK', 'ERROR')]
    print('\n%d probes: %d OK, %d NOTE, %d WEAK, %d ERROR' % (len(results), sum(r[2] == 'OK' for r in results), sum(r[2] == 'NOTE' for r in results), sum(r[2] == 'WEAK' for r in results), sum(r[2] == 'ERROR' for r in results)))
    h.TMP.cleanup()
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
