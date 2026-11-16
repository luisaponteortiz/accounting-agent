"""Fable acceptance probes for the RB-01 to RB-04 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_rb_acceptance_probes.py <project-root> [PROBE_ID ...]

Drives the application in <project-root> through public service operations only. Temporary
SQLite files, fictional data, no network, model, posting or payment.

Helpers (actors, grants, packet/row builders, run/gov/review/dispose) are loaded unchanged from
<project-root>/exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py, the earlier independent
script, so that the two scripts build identical fixtures. Nothing in that file is modified.
Every additional synthetic grant is made on the line that needs it. Each refusal is paired with
a positive control.

Verdicts: OK control held | WEAK confirmed gap (exit 1) | NOTE observation needing a decision
          | ERROR probe could not reach its intended state (exit 1)
"""
import copy
import importlib.util
import json
import sys
import traceback
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
_helper_path = ROOT / 'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py'
_spec = importlib.util.spec_from_file_location('fable_ra_helpers', _helper_path)
h = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = [str(_helper_path), str(ROOT)]
_spec.loader.exec_module(h)
sys.argv = _argv

from accounting_agent.core import Actor  # noqa: E402
from accounting_agent.service import AccountingOS  # noqa: E402

CARD, NOV, DEC = h.CARD, h.NOV, h.DEC
PREP, PREP2, REV, REV2, REV3, REV4 = h.PREP, h.PREP2, h.REV, h.REV2, h.REV3, h.REV4
DISP, FIN, PADMIN, ADMIN, CTRL, CTRL2 = h.DISP, h.FIN, h.PADMIN, h.ADMIN, h.CTRL, h.CTRL2
tx, rc, stmt, sup, packet, run, gov, arts = h.tx, h.rc, h.stmt, h.sup, h.packet, h.run, h.gov, h.arts
review, dispose, brief, show, attempt, human = h.review, h.dispose, h.brief, h.show, h.attempt, h.human
exceptions_of, governing_keys, workpaper, revs = h.exceptions_of, h.governing_keys, h.workpaper, h.revs
K = lambda sid: CARD + ':' + sid
MOVED = 'SOURCE_MOVED_FROM_LOCKED_PERIOD'
TRANSITION = 'SOURCE_TRANSITION_REQUIRES_REVIEW'
REVISED = 'EVIDENCE_REVISED_REQUIRES_REVIEW'
PROBES = []


def probe(pid, ticket, title):
    def register(fn):
        PROBES.append((pid, ticket, title, fn))
        return fn
    return register


def moves(os_):
    st = os_.export(PREP)
    keyof = {s['id']: s['source_key'] for s in st['evidence_history']}
    return [(keyof.get(m['snapshot_id']), m['from_period_id'], m['to_period_id'], m['blocked'], m['had_approval']) for m in st['source_move_history']]


def events(os_, code_prefix=None):
    return sorted({(e['code'], e['period_id'], e['item_key']) for e in os_.export(PREP)['accounting_events'] if code_prefix is None or e['code'].startswith(code_prefix)})


def held_under(os_, period='2026-11'):
    return {e[0] for e in exceptions_of(os_) if e[1] == period and e[2] == MOVED}


def approved(os_, key, period):
    a = gov(os_, key, period)
    return a is not None and a['review_status'] == 'approve'


def twice(os_, nov_key, dec_key):
    """True when one economic charge is approved and governing in both periods."""
    return approved(os_, nov_key, '2026-11') and approved(os_, dec_key, '2026-12')


def try_to_approve(os_, key, period='2026-12', reviewer=None, who=PREP2):
    """Do what an honest operator would do next: clear the transition blocker with the whole
    evidence list, re-prepare, ask an independent reviewer to approve. Returns the final artifact."""
    a = gov(os_, key, period)
    if a is None:
        return None
    if TRANSITION in a['blockers']:
        show('settlement_verified on ' + key, dispose(os_, key, TRANSITION, 'settlement_verified', period=period))
        run(os_, 'card_preparation', period, who); a = gov(os_, key, period)
    if a is not None and a['review_status'] != 'approve':
        show('independent approval of ' + key, review(os_, reviewer or REV2, a, 'approve'))
    return gov(os_, key, period)


# =======================================================================================
# RB-01  late and later-resolved supersession links
# =======================================================================================

@probe('N01a', 'RB-01', 'late link on a destination that is already approved: approval stops governing, events and blocked move recorded, root history kept; reopen admits only the replacement; relock, replay and restart are stable')
def _():
    os_ = h.approved_locked_november()
    plain = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    other = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP2, packet('plain', plain + other + [stmt(plain + other, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    r = show('B1 approved in December before any claim', review(os_, REV2, gov(os_, K('B1'), '2026-12'), 'approve'))
    claim = packet('claim', [sup('B1', '2026-12-02', '40.00', 'A1')])
    os_.intake(PREP2, claim); replay = os_.intake(PREP2, claim); run(os_, 'card_preparation', '2026-12', PREP2)
    b = gov(os_, K('B1'), '2026-12'); mv = moves(os_); ev = events(os_)
    print('    after the claim -> December B1:', brief(b), '| held under November:', sorted(held_under(os_)))
    print('    moves:', mv); print('    events:', ev)
    quarantined = b is None and {K('B1'), 'receipt-B1'} <= held_under(os_) and approved(os_, K('A1'), '2026-11')
    evidence = (any(m[0] == K('B1') and m[1] == '2026-11' and m[2] == '2026-12' and m[3] == 1 and m[4] == 1 for m in mv)
                and all(m[1] != m[2] for m in mv)
                and any(e[0].startswith('APPROVED_SOURCE_') and e[1] == '2026-12' and e[2] == K('B1') for e in ev)
                and any(e[0] == 'ITEM_LEFT_POPULATION' and e[2] == K('B1') for e in ev))
    st = os_.export(PREP)
    root = [s for s in st['evidence_history'] if s['source_key'] == K('A1')]
    all_b1 = [a for a in arts(os_, K('B1'), '2026-12')]
    print('    replay flagged:', replay.get('replay'), '| A1 versions kept:', len(root), '| B1 artifacts kept (history):', len(all_b1), '| any still governing:', any(a['governing'] for a in all_b1))
    fin = show('finalize December while B1 is quarantined, no acknowledgement', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    # authorised reopen
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    nov, dec = governing_keys(os_, '2026-11'), governing_keys(os_, '2026-12'); b = gov(os_, K('B1'), '2026-12')
    print('    after reopen -> November:', nov, '| December:', dec, '| B1:', brief(b))
    released = K('A1') not in nov and K('B1') in dec and b is not None and TRANSITION in b['blockers'] and b['review_status'] != 'approve'
    b = try_to_approve(os_, K('B1'))
    single = approved(os_, K('B1'), '2026-12') and gov(os_, K('A1'), '2026-11') is None
    # relock and revise the destination
    for k in governing_keys(os_, '2026-11'):
        a = gov(os_, k, '2026-11')
        if a['eligible'] and a['review_status'] == 'pending':
            review(os_, REV, a, 'approve')
    show('relock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'probe acknowledgement'))
    rev = [sup('B1', '2026-12-02', '42.00', 'A1'), rc('B1', '2026-12-02', '42.00')]
    os_.intake(PREP2, packet('b-rev', rev + [stmt(rev + other, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    b3 = gov(os_, K('B1'), '2026-12')
    relock = b3 is not None and b3['payload']['data']['transaction']['amount'] == '42.00' and K('B1') not in held_under(os_)
    print('    after relock and a destination revision -> B1:', brief(b3), '| held:', sorted(held_under(os_)))
    before = (governing_keys(os_, '2026-11'), governing_keys(os_, '2026-12'), exceptions_of(os_), moves(os_))
    again = AccountingOS(os_.probe_path, [h.SCOPE])
    after = (governing_keys(again, '2026-11'), governing_keys(again, '2026-12'), exceptions_of(again), moves(again))
    print('    restart identical:', before == after, '| audit chain:', again.verify_audit(PREP), '| no same-period move rows:', all(m[1] != m[2] for m in moves(again)))
    ok = r[0] == 'ok' and quarantined and evidence and len(root) >= 1 and released and single and relock and before == after and again.verify_audit(PREP) and all(m[1] != m[2] for m in moves(again))
    print('    quarantined=%s evidence=%s released=%s single=%s relock=%s' % (quarantined, evidence, released, single, relock))
    return 'OK' if ok else 'WEAK'


@probe('N01b', 'RB-01', 'late link when the locked ancestor was withdrawn (tombstoned) after the lock: the replacement is not approvable in a second period')
def _():
    out = {}
    for order in ('fresh-link-after-tombstone', 'late-link-after-tombstone'):
        os_ = h.approved_locked_november()
        gone = dict(tx('A1', '2026-11-03', '40.00'), tombstone=True, removal_reason='voided')
        b_plain = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
        b_claim = [sup('B1', '2026-12-02', '40.00', 'A1'), rc('B1', '2026-12-02', '40.00')]
        if order == 'fresh-link-after-tombstone':
            os_.intake(PREP2, packet('void', [gone]))
            os_.intake(PREP2, packet('b', b_claim + [stmt(b_claim, DEC, opening='100.00')]))
        else:
            os_.intake(PREP2, packet('b', b_plain + [stmt(b_plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
            os_.intake(PREP2, packet('void', [gone]))
            os_.intake(PREP2, packet('claim', [b_claim[0]]))
        run(os_, 'card_preparation', '2026-12', PREP2)
        b = gov(os_, K('B1'), '2026-12')
        print('    [%s] December B1: %s' % (order, brief(b)))
        print('    [%s] exceptions: %s' % (order, exceptions_of(os_)))
        print('    [%s] moves: %s' % (order, moves(os_)))
        print('    [%s] events: %s' % (order, events(os_)))
        try_to_approve(os_, K('B1'))
        both = twice(os_, K('A1'), K('B1'))
        fin = show('[%s] finalize December without acknowledgement' % order, attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe')) if both else None
        print('    [%s] November A1: %s | December B1: %s | approved in both periods: %s' % (order, brief(gov(os_, K('A1'), '2026-11')), brief(gov(os_, K('B1'), '2026-12')), both))
        out[order] = both
    return 'WEAK' if any(out.values()) else 'OK'


@probe('N01c', 'RB-01', 'late link declared on a middle source whose replacement is already admitted (and approved) in December: the replacement does not stay approved beside the locked root')
def _():
    out = {}
    for pre_approved in (False, True):
        os_ = h.approved_locked_november()
        b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
        c = [sup('C1', '2026-12-03', '40.00', 'B1'), rc('C1', '2026-12-03', '40.00')]
        # the December statement names the final population (C1) from the start: no statement revision
        os_.intake(PREP2, packet('b', b + [stmt(c, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
        os_.intake(PREP2, packet('c', c)); run(os_, 'card_preparation', '2026-12', PREP2)
        if pre_approved:
            try_to_approve(os_, K('C1'))
        print('    [pre_approved=%s] C1 replaces B1 inside December: %s' % (pre_approved, brief(gov(os_, K('C1'), '2026-12'))))
        os_.intake(PREP2, packet('late', [sup('B1', '2026-12-02', '40.00', 'A1')])); run(os_, 'card_preparation', '2026-12', PREP2)
        c1 = gov(os_, K('C1'), '2026-12')
        print('    [pre_approved=%s] B1 then declares it supersedes A1 (locked) -> C1: %s | December governing: %s' % (pre_approved, brief(c1), governing_keys(os_, '2026-12')))
        print('    [pre_approved=%s] exceptions: %s' % (pre_approved, exceptions_of(os_)))
        try_to_approve(os_, K('C1')); try_to_approve(os_, K('B1'))
        both = twice(os_, K('A1'), K('C1')) or twice(os_, K('A1'), K('B1'))
        print('    [pre_approved=%s] November A1: %s | December C1: %s | December B1: %s | approved in both periods: %s' % (pre_approved, brief(gov(os_, K('A1'), '2026-11')), brief(gov(os_, K('C1'), '2026-12')), brief(gov(os_, K('B1'), '2026-12')), both))
        out[pre_approved] = both
    return 'WEAK' if any(out.values()) else 'OK'


@probe('N01d', 'RB-01', 'an unresolved link that is never re-sent: a further replacement of the unresolved source is not released while the root is locked')
def _():
    os_ = h.approved_locked_november()
    y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
    z = [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')]
    # the December statement names the final population (A1Z) from the start: no statement revision
    os_.intake(PREP2, packet('y-first', y + [stmt(z, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    A1Y (supersedes A1X, not yet received):', brief(gov(os_, K('A1Y'), '2026-12')))
    os_.intake(PREP2, packet('x-second', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    A1X arrives (supersedes locked A1) -> held:', sorted(held_under(os_)), '| A1Y:', brief(gov(os_, K('A1Y'), '2026-12')))
    os_.intake(PREP2, packet('z-third', z)); run(os_, 'card_preparation', '2026-12', PREP2)
    az = gov(os_, K('A1Z'), '2026-12')
    print('    A1Z arrives superseding A1Y (A1Y never re-sent) -> A1Z:', brief(az), '| December governing:', governing_keys(os_, '2026-12'))
    print('    exceptions:', exceptions_of(os_))
    if az is not None:
        print('    A1Z disclosed chain:', sorted(e['source_key'] for e in az['payload']['data']['evidence'] if 'link_id' in e))
    try_to_approve(os_, K('A1Z'))
    both = twice(os_, K('A1'), K('A1Z'))
    fin = show('finalize December without acknowledgement', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe')) if both else None
    print('    November A1:', brief(gov(os_, K('A1'), '2026-11')), '| December A1Z:', brief(gov(os_, K('A1Z'), '2026-12')), '| approved in both periods:', both)
    return 'WEAK' if both else 'OK'


@probe('N01e', 'RB-01', 'three-deep chain delivered newest first with every link later resolved by re-sending: nothing is released while the root is locked; reopen admits only the terminal source')
def _():
    os_ = h.approved_locked_november()
    z = [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')]
    y = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
    x = [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]
    os_.intake(PREP2, packet('z', z + [stmt(z, DEC, opening='100.00')]))
    os_.intake(PREP2, packet('y', y)); os_.intake(PREP2, packet('x', x))
    run(os_, 'card_preparation', '2026-12', PREP2)
    print('    newest first, nothing re-sent -> December governing:', [(k, brief(gov(os_, k, '2026-12'))['blockers']) for k in governing_keys(os_, '2026-12') if k.startswith(CARD)])
    os_.intake(PREP2, packet('y-again', [y[0]])); os_.intake(PREP2, packet('z-again', [z[0]]))
    run(os_, 'card_preparation', '2026-12', PREP2)
    dec = [k for k in governing_keys(os_, '2026-12') if k.startswith(CARD)]
    print('    A1Y then A1Z re-sent -> December governing:', dec, '| held under November:', sorted(held_under(os_)))
    # every link and the receipts of the first and last link are held; the receipt of a superseded
    # middle link may be held or retired with its transaction, so it is not asserted
    want = {K(k) for k in ('A1X', 'A1Y', 'A1Z')} | {'receipt-' + k for k in ('A1X', 'A1Z')}
    held = not dec and want <= held_under(os_) and approved(os_, K('A1'), '2026-11')
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    nov = governing_keys(os_, '2026-11'); dec = [k for k in governing_keys(os_, '2026-12') if k.startswith(CARD)]
    st = os_.export(PREP)
    ever = sorted({s['source_key'] for s in st['evidence_history'] for b in st['source_period_history'] if b['snapshot_id'] == s['id'] and b['period_id'] == '2026-12' and b['admitted'] and s['source_key'] in (K('A1'), K('A1X'))})
    print('    after reopen -> November:', nov, '| December:', dec, '| A1 or A1X ever admitted to December:', ever)
    released = K('A1') not in nov and dec == [K('A1Z')] and not ever
    return 'OK' if held and released else 'WEAK'


@probe('N01f', 'RB-01', 'control: a late link to a charge in an OPEN prior period is an ordinary supersession, not a quarantine; no same-period move row')
def _():
    os_ = h.new_os(periods=(NOV, DEC)); h.clean_november(os_); run(os_, 'card_preparation')
    review(os_, REV, gov(os_, K('A1')), 'approve')
    b = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(b, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    os_.intake(PREP2, packet('claim', [sup('B1', '2026-12-02', '40.00', 'A1')]))
    run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    b1 = gov(os_, K('B1'), '2026-12'); a1 = gov(os_, K('A1'), '2026-11'); mv = moves(os_)
    print('    November open -> A1:', brief(a1), '| December B1:', brief(b1), '| held:', sorted(held_under(os_)), '| moves:', mv)
    ok = a1 is None and b1 is not None and TRANSITION in b1['blockers'] and not held_under(os_) and all(m[1] != m[2] for m in mv)
    return 'OK' if ok else 'WEAK'


@probe('N01g', 'RB-01/RV-01', 'a charge superseded while its period was open, the period then locked before it was re-prepared: the superseded charge does not stay approved beside its replacement')
def _():
    os_ = h.new_os(periods=(NOV, DEC)); h.clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, K(k)), 'approve')
    b = [sup('B1', '2026-12-02', '40.00', 'A1'), rc('B1', '2026-12-02', '40.00')]
    os_.intake(PREP2, packet('b', b + [stmt(b, DEC, opening='100.00')]))
    lk = show('lock November without re-preparing it, no acknowledgement', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock'))
    if lk[0] == 'refused':
        lk = show('lock November without re-preparing it, with acknowledgement', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock', 'probe acknowledgement'))
    run(os_, 'card_preparation', '2026-12', PREP2)
    try_to_approve(os_, K('B1'))
    a1 = gov(os_, K('A1'), '2026-11'); b1 = gov(os_, K('B1'), '2026-12')
    both = twice(os_, K('A1'), K('B1'))
    print('    November A1:', brief(a1), '| December B1:', brief(b1), '| approved in both periods:', both)
    return 'WEAK' if both else 'OK'


# =======================================================================================
# RB-02  re-pointed documents
# =======================================================================================

def accept_cycle(os_, label, suppliers, later):
    """Common RB-02 assertions on item A1 after a replacement was detected."""
    a = gov(os_, K('A1'))
    direct = show('[%s] independent approval without acceptance' % label, review(os_, REV, a, 'approve'))
    refusals = []
    for s in suppliers:
        os_.grant_authority(ADMIN, s.id, ['disposition'], 'Fictional probe grant: supplier attempts acceptance')
        refusals.append(show('[%s] supplier %s accepts' % (label, s.id), dispose(os_, K('A1'), REVISED, 'revised_evidence_accepted', who=human(s.id, 'reviewer'))))
    ok = show('[%s] granted non-supplier accepts for A1' % label, dispose(os_, K('A1'), REVISED, 'revised_evidence_accepted'))
    run(os_, 'card_preparation'); a2 = gov(os_, K('A1'))
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'Fictional probe grant: acceptor attempts final review')
    self_review = show('[%s] the acceptor gives the final review' % label, review(os_, DISP, a2, 'approve'))
    final = show('[%s] independent final review' % label, review(os_, REV, a2, 'approve'))
    os_.intake(PREP2, packet('later-' + label, [later])); run(os_, 'card_preparation')
    a3 = gov(os_, K('A1'))
    print('    [%s] after a further change: %s' % (label, brief(a3)))
    return (direct[0] == 'refused' and all(r[0] == 'refused' and r[1] == 403 for r in refusals) and ok[0] == 'ok' and a2['eligible'] and bool(revs(a2))
            and self_review[0] == 'refused' and final[0] == 'ok' and REVISED in a3['blockers'] and not a3['eligible'] and a3['review_status'] != 'approve')


@probe('N02a', 'RB-02', 'receipt re-pointed to another existing charge or to a void id, in one packet or two and in either order, by a second supplier: held, disclosed with both identities, both suppliers refused, acceptance item-bound and separate from final review, later change lapses it')
def _():
    out = []
    for label, target, order in (('void-one-packet', 'A1-VOID', 'one'), ('other-charge-repoint-first', 'A2', 'repoint-first'), ('void-replacement-first', 'A1-VOID', 'replacement-first')):
        os_, rows = h.mismatch_november()
        away = rc(target, '2026-11-03', '39.99', key='receipt-A1')
        new = rc('A1', '2026-11-03', '40.00', key='receipt-A1-new', content='Fictional replacement receipt')
        if order == 'one':
            os_.intake(PREP2, packet('r', [away, new]))
        elif order == 'repoint-first':
            os_.intake(PREP2, packet('r1', [away])); run(os_, 'card_preparation')
            print('    [%s] after the re-point only -> A1: %s' % (label, brief(gov(os_, K('A1')))))
            os_.intake(PREP2, packet('r2', [new]))
        else:
            os_.intake(PREP2, packet('r1', [new])); run(os_, 'card_preparation')
            os_.intake(PREP2, packet('r2', [away]))
        run(os_, 'card_preparation'); a = gov(os_, K('A1')); a2 = gov(os_, K('A2'))
        print('    [%s] A1: %s' % (label, brief(a))); print('    [%s] revisions: %s' % (label, revs(a)))
        if target == 'A2':
            print('    [%s] A2 (now carries two receipts): %s' % (label, a2['blockers']))
        r = a['payload']['data'].get('evidence_revisions', [])
        disclosed = REVISED in a['blockers'] and not a['eligible'] and any(x['kind'] == 'replaced' and x['earlier']['source_key'] == 'receipt-A1' and x['earlier']['version'] == 1 and x['earlier']['supplier'] == PREP.id and x['current']['source_key'] == 'receipt-A1-new' and x['current']['supplier'] == PREP2.id and 'amount' in x['changed_fields'] for x in r)
        later = rc('A1', '2026-11-03', '40.00', key='receipt-A1-new', content='Fictional replacement receipt, edited again')
        out.append(disclosed and accept_cycle(os_, label, (PREP, PREP2), later))
    # a genuine additional receipt stays a multiple-support question
    os_ = h.new_os(); h.clean_november(os_); run(os_, 'card_preparation')
    os_.intake(PREP2, packet('second', [rc('A1', '2026-11-03', '40.00', key='receipt-A1-second', content='Fictional second receipt')])); run(os_, 'card_preparation')
    a = gov(os_, K('A1')); print('    additional still-active receipt:', a['blockers'], '| revisions:', revs(a))
    extra = not revs(a) and REVISED not in a['blockers'] and any('MULTIPLE' in b for b in a['blockers'])
    print('    variants:', out, '| additional-receipt control:', extra)
    return 'OK' if all(out) and extra else 'WEAK'


@probe('N02b', 'RB-02', 'statement re-pointed to another cycle in a separate packet before or after the tying replacement: every relying item held, workpaper discloses, suppliers refused, acceptance item-bound, later change lapses it')
def _():
    out = []
    for label in ('repoint-first', 'replacement-first'):
        os_, rows = h.short_statement()
        away = stmt(rows, period=('2027-01', '2027-01-01', '2027-01-31'), key='stmt-2026-11', totals=h.WRONG, closing_balance='90.00')
        new = stmt(rows, key='stmt-2026-11-b')
        first, second = (away, new) if label == 'repoint-first' else (new, away)
        os_.intake(PREP2, packet('s1', [first])); run(os_, 'card_preparation')
        print('    [%s] after the first packet -> A1: %s' % (label, brief(gov(os_, K('A1')))))
        os_.intake(PREP2, packet('s2', [second])); run(os_, 'card_preparation')
        a1, a2, wp = gov(os_, K('A1')), gov(os_, K('A2')), workpaper(os_)
        sr = wp['payload']['data'].get('statement_revisions', [])
        print('    [%s] A1: %s | A2: %s' % (label, brief(a1), brief(a2)))
        print('    [%s] workpaper statement_revisions: %s' % (label, [(x['kind'], x['earlier']['source_key'], x['earlier']['version'], x['earlier']['supplier'], x['current']['source_key'], x['current']['supplier'], x['changed_fields']) for x in sr]))
        held = all(REVISED in a['blockers'] and not a['eligible'] and revs(a) for a in (a1, a2)) and any(x['kind'] == 'replaced' and x['earlier']['source_key'] == 'stmt-2026-11' and x['earlier']['version'] == 1 and 'totals' in x['changed_fields'] for x in sr)
        later = stmt(rows, key='stmt-2026-11-b', content='Fictional probe statement, edited again')
        cycle = accept_cycle(os_, label, (PREP, PREP2), later)
        b2 = gov(os_, K('A2'))
        out.append(held and cycle and REVISED in b2['blockers'])
    print('    variants:', out)
    return 'OK' if all(out) else 'WEAK'


@probe('N02c', 'RB-02', 'observation: a contradicting receipt supplied AFTER the one now relied on, then moved away from the charge')
def _():
    os_ = h.new_os(); h.clean_november(os_); run(os_, 'card_preparation')
    os_.intake(PREP2, packet('second', [rc('A1', '2026-11-03', '39.99', key='receipt-A1-second', content='Fictional contradicting receipt')])); run(os_, 'card_preparation')
    a = gov(os_, K('A1')); print('    two active receipts (40.00 then 39.99):', a['blockers'])
    os_.intake(PREP2, packet('away', [rc('A1-VOID', '2026-11-03', '39.99', key='receipt-A1-second', content='Fictional contradicting receipt')])); run(os_, 'card_preparation')
    a = gov(os_, K('A1'))
    print('    the later receipt is re-pointed away -> A1:', brief(a), '| revisions:', revs(a))
    told = bool(revs(a)) or not a['eligible']
    return 'OK' if told else 'NOTE'


# =======================================================================================
# RB-03  rule authorship across scope and key
# =======================================================================================

def second_reviewer_free(o, a, who=REV2):
    return show('independent reviewer approves (positive control)', review(o, who, a, 'approve'))


@probe('N03a', 'RB-03', 'identical vendor mapping and receipt policy re-proposed with item scope, under a new key, and as a three-step chain keep every earlier author and approver barred; an independent reviewer approves')
def _():
    res = []
    for kind, key, value in (('vendor_mapping', 'demo_acme', h.ACME), ('receipt_matching', 'default', h.RM)):
        for route, opts in (('item-scope', {'item2': K('A1')}), ('new-key', {'key2': key + '_b', 'end1': '2026-11-02', 'start2': '2026-11-03'})):
            o, a = h.rule_case(REV3, value, copy.deepcopy(value), kind=kind, key=key, **opts)
            barred = show('[%s %s] author of the earlier rule approves' % (kind, route), review(o, REV3, a, 'approve'))
            o.grant_authority(ADMIN, CTRL.id, ['review'], 'Fictional probe grant: earlier rule approver attempts item review')
            appr = show('[%s %s] approver of the earlier rule approves' % (kind, route), review(o, CTRL, a, 'approve'))
            free = second_reviewer_free(o, a)
            res.append(barred[0] == 'refused' and barred[1] == 403 and appr[0] == 'refused' and free[0] == 'ok' and REV3.id in a['contributors'])
    # three steps: general (REV3) -> item scope (PREP) -> new key (PREP2)
    p = copy.deepcopy(h.PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_acme']
    o = h.new_os(profile=p)
    r1 = o.propose_rule(human(REV3.id, 'preparer'), 'vendor_mapping', 'demo_acme', h.ACME, '2026-11-01', '2026-11-02'); o.approve_rule(CTRL, r1, 'probe 1')
    r2 = o.propose_rule(human(REV4.id, 'preparer'), 'vendor_mapping', 'demo_acme', dict(h.ACME), '2026-11-01', '2026-11-02', K('A1')); o.approve_rule(CTRL2, r2, 'probe 2')
    r3 = o.propose_rule(PREP2, 'vendor_mapping', 'demo_acme_c', dict(h.ACME, name='Acme Paper Demo Co'), '2026-11-03', None); o.approve_rule(CTRL, r3, 'probe 3')
    h.clean_november(o); run(o, 'card_preparation'); a = gov(o, K('A1'))
    print('    three-step chain contributors:', a['contributors'])
    c1 = show('author of step 1 approves', review(o, REV3, a, 'approve'))
    c2 = show('author of step 2 approves', review(o, REV4, a, 'approve'))
    c3 = second_reviewer_free(o, a)
    res.append(a['eligible'] and c1[0] == 'refused' and c2[0] == 'refused' and c3[0] == 'ok')
    print('    results:', res)
    return 'OK' if all(res) else 'WEAK'


@probe('N03b', 'RB-03', 'unrelated earlier rules do not bar a reviewer: another item scope, another description, another category, another policy value, another client')
def _():
    res = {}
    # identical mapping scoped to another item (A2)
    p = copy.deepcopy(h.PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_acme']
    o = h.new_os(profile=p)
    r1 = o.propose_rule(human(REV3.id, 'preparer'), 'vendor_mapping', 'demo_acme_item', h.ACME, '2026-11-01', None, K('A2')); o.approve_rule(CTRL, r1, 'probe: scoped to A2')
    r2 = o.propose_rule(PREP, 'vendor_mapping', 'demo_acme', dict(h.ACME), '2026-11-01', None); o.approve_rule(CTRL2, r2, 'probe: general')
    h.clean_november(o); run(o, 'card_preparation'); a = gov(o, K('A1'))
    res['other item scope'] = a['eligible'] and show('earlier identical mapping was scoped to another charge (A2): its author approves A1', review(o, REV3, a, 'approve'))[0] == 'ok'
    o, a = h.rule_case(REV3, dict(h.ACME, aliases=['OTHER VENDOR DEMO']), h.ACME, key2='demo_acme_b', end1='2026-11-02', start2='2026-11-03')
    res['other description'] = show('earlier rule under another key covered another description: its author approves', review(o, REV3, a, 'approve'))[0] == 'ok'
    o, a = h.rule_case(REV3, dict(h.ACME, category='DEMO_REPAIRS'), h.ACME, item2=K('A1'))
    res['other category'] = show('earlier general rule had another category: its author approves', review(o, REV3, a, 'approve'))[0] == 'ok'
    o, a = h.rule_case(REV4, dict(h.RM, date_window_days=3), dict(h.RM), kind='receipt_matching', key='default', key2='default_b', end1='2026-11-02', start2='2026-11-03')
    res['other policy value'] = show('earlier receipt policy under another key had another value: its author approves', review(o, REV4, a, 'approve'))[0] == 'ok'
    # another client in the same database: same person id authored the identical rule there
    other = 'second_fictional_client'; scope2 = h.ORG + '/' + other + '/local'
    path = Path(h.TMP.name) / 'n03b-two-clients.sqlite3'
    o = AccountingOS(path, [h.SCOPE, scope2])
    p1 = copy.deepcopy(h.PROFILE); p1['vendors'] = [v for v in p1['vendors'] if v['id'] != 'demo_acme']
    sid = o.onboard(PREP, p1)
    for subject, perms in h.ROLES.items():
        o.grant_authority(ADMIN, subject, perms, 'Fictional probe authority; client one')
    o.approve_profile_version(CTRL, sid, 'probe'); o.open_period(PADMIN, *NOV, 'probe')
    p2 = copy.deepcopy(p1); p2.update(client_id=other, name='Second fictional client')
    admin2, prep2, ctrl2 = human('rv-authority-admin', 'administrator', other), human(REV3.id, 'preparer', other), human('second-policy-approver', 'reviewer', other)
    sid2 = o.onboard(human('second-preparer', 'preparer', other), p2)
    o.grant_authority(admin2, ctrl2.id, ['approve_profile', 'approve_rule'], 'Fictional probe authority; client two')
    o.approve_profile_version(ctrl2, sid2, 'probe')
    rr = o.propose_rule(prep2, 'vendor_mapping', 'demo_acme', h.ACME, '2026-11-01', None); o.approve_rule(ctrl2, rr, 'probe: client two')
    r = o.propose_rule(PREP, 'vendor_mapping', 'demo_acme', dict(h.ACME), '2026-11-01', None); o.approve_rule(CTRL, r, 'probe: client one')
    h.clean_november(o); run(o, 'card_preparation'); a = gov(o, K('A1'))
    res['other client'] = a['eligible'] and REV3.id not in a['contributors'] and show('same person authored the identical rule for another client: approves here', review(o, REV3, a, 'approve'))[0] == 'ok'
    print('    results:', res)
    return 'OK' if all(res.values()) else 'WEAK'


@probe('N03c', 'RB-03/RA-02', 'a receipt policy cannot be re-proposed with the same money value written differently (0.0 for 0.00), so exact value comparison cannot be sidestepped that way')
def _():
    o = h.new_os()
    good = show('tolerance 0.00 proposed', attempt(o.propose_rule, PREP, 'receipt_matching', 'default', dict(h.RM, amount_tolerance='0.00'), '2026-11-01', None))
    bad = [show('tolerance %r proposed' % v, attempt(o.propose_rule, PREP, 'receipt_matching', 'default_b', dict(h.RM, amount_tolerance=v), '2026-11-01', None)) for v in ('0.0', '0', '0.000', ' 0.00')]
    return 'OK' if good[0] == 'ok' and all(r[0] == 'refused' for r in bad) else 'WEAK'


# =======================================================================================
# RB-04  prior-period statement restatement
# =======================================================================================

def break_then_restate(restater=PREP2, lock_november=False):
    os_ = h.new_os(periods=(NOV, DEC)); rows = h.clean_november(os_); run(os_, 'card_preparation')
    dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='120.00')])); run(os_, 'card_preparation', '2026-12')
    assert 'STATEMENT_OPENING_BALANCE_BREAK' in gov(os_, K('D1'), '2026-12')['blockers']
    os_.intake(restater, packet('restate', [stmt(rows, opening='20.00')]))
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12')
    return os_, rows, dec


def dec_view(os_):
    wp = workpaper(os_, '2026-12'); d = wp['payload']['data']; d1 = gov(os_, K('D1'), '2026-12')
    return d1, wp, d


@probe('N04a', 'RB-04', 'restated November statement: December discloses it and stays unverified with no and with partial acceptance; verified only when every November item is accepted; restater and acceptor cannot review December; revocation re-blocks and removes the approval, also before December is re-prepared')
def _():
    os_, rows, dec = break_then_restate()
    d1, wp, d = dec_view(os_)
    print('    after the restatement -> D1:', brief(d1)); print('    December workpaper: continuity=%s | prior revisions=%s | acceptance=%s' % (d['opening_continuity'], [(x['kind'], x['earlier']['version'], x['earlier']['supplier'], x['current']['supplier'], x['changed_fields']) for x in d.get('prior_statement_revisions', [])], d.get('prior_statement_acceptance')))
    none = (not d1['eligible'] and d['opening_continuity'] != 'verified' and bool(d.get('prior_statement_revisions')) and 'STATEMENT_PRIOR_REVISION_REQUIRES_REVIEW' in wp['blockers']
            and any(x['earlier']['supplier'] == PREP.id and x['current']['supplier'] == PREP2.id and 'opening_balance' in x['changed_fields'] and 'closing_balance' in x['changed_fields'] for x in d['prior_statement_revisions']))
    direct = show('independent approval of D1 with no November acceptance', review(os_, REV, d1, 'approve'))
    first = show('acceptance for November A1 only', dispose(os_, K('A1'), REVISED, 'revised_evidence_accepted'))
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    print('    partial -> D1:', brief(d1), '| continuity:', d['opening_continuity'], '| accepted items:', (d.get('prior_statement_acceptance') or {}).get('accepted_item_keys'))
    partial = not d1['eligible'] and d['opening_continuity'] != 'verified'
    second = show('acceptance for November A2', dispose(os_, K('A2'), REVISED, 'revised_evidence_accepted'))
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    print('    all accepted -> D1:', brief(d1), '| continuity:', d['opening_continuity'], '| D1 contributors:', d1['contributors'])
    full = d1['eligible'] and d['opening_continuity'] == 'verified' and bool(d.get('prior_statement_revisions'))
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'Fictional probe grant: acceptor attempts December review')
    os_.grant_authority(ADMIN, PREP2.id, ['review'], 'Fictional probe grant: restater attempts December review')
    by_acceptor = show('the November acceptor reviews December D1', review(os_, DISP, d1, 'approve'))
    by_restater = show('the supplier of the restated November statement reviews December D1', review(os_, human(PREP2.id, 'reviewer'), d1, 'approve'))
    final = show('independent final review of D1', review(os_, REV, d1, 'approve'))
    separate = by_acceptor[0] == 'refused' and by_restater[0] == 'refused' and final[0] == 'ok'
    # revocation, checked before and after December is re-prepared
    show('revoke the A1 acceptance', attempt(os_.revoke_disposition, DISP, first[1], 'probe revocation'))
    stale = gov(os_, K('D1'), '2026-12')
    fin = show('finalize December after the revocation, before re-preparing it', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    print('    before re-preparation -> D1:', brief(stale))
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    print('    after re-preparation -> D1:', brief(d1), '| continuity:', d['opening_continuity'])
    reblocked = fin[0] == 'refused' and not d1['eligible'] and d1['review_status'] != 'approve' and 'STATEMENT_PRIOR_REVISION_REQUIRES_REVIEW' in d1['blockers'] and d['opening_continuity'] != 'verified'
    print('    none=%s partial=%s full=%s separate=%s reblocked=%s audit=%s' % (none, partial, full, separate, reblocked, os_.verify_audit(PREP)))
    return 'OK' if none and direct[0] == 'refused' and partial and full and separate and reblocked and os_.verify_audit(PREP) else 'WEAK'


@probe('N04b', 'RB-04', 'new evidence after full acceptance: a further change to the November statement lapses the acceptance and re-blocks an approved December item')
def _():
    os_, rows, dec = break_then_restate()
    for k in ('A1', 'A2'):
        assert dispose(os_, K(k), REVISED, 'revised_evidence_accepted')[0] == 'ok'
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    appr = show('D1 approved with continuity ' + d['opening_continuity'], review(os_, REV, d1, 'approve'))
    os_.intake(PREP2, packet('restate-again', [stmt(rows, opening='20.00', content='Fictional probe statement, edited again')]))
    fin = show('finalize December after the further change, before re-preparing', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    print('    after a further change -> D1:', brief(d1), '| continuity:', d['opening_continuity'])
    ok = appr[0] == 'ok' and fin[0] == 'refused' and not d1['eligible'] and d1['review_status'] != 'approve' and d['opening_continuity'] != 'verified'
    return 'OK' if ok else 'WEAK'


@probe('N04c', 'RB-04/RB-02', 'the November statement replaced by re-pointing its key (or withdrawn and replaced) so that the opening agrees is disclosed to December; a withdrawn statement with no replacement is reported missing')
def _():
    res = {}
    for label in ('repointed', 'withdrawn-and-replaced', 'withdrawn-only'):
        os_ = h.new_os(periods=(NOV, DEC)); rows = h.clean_november(os_); run(os_, 'card_preparation')
        dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
        os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='120.00')])); run(os_, 'card_preparation', '2026-12')
        new = stmt(rows, opening='20.00', key='stmt-2026-11-b')
        if label == 'repointed':
            away = stmt(rows, period=('2027-01', '2027-01-01', '2027-01-31'), key='stmt-2026-11')
            os_.intake(PREP2, packet('x', [away, new]))
        else:
            gone = dict(stmt(rows), tombstone=True, removal_reason='voided')
            os_.intake(PREP2, packet('x', [gone] + ([new] if label == 'withdrawn-and-replaced' else [])))
        run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
        print('    [%s] D1: %s | continuity: %s | prior revisions: %s' % (label, brief(d1), d['opening_continuity'], [(x['kind'], x['earlier']['source_key'], x['changed_fields']) for x in d.get('prior_statement_revisions', [])]))
        if label == 'withdrawn-only':
            res[label] = not d1['eligible'] and d['opening_continuity'] not in ('verified', 'no_prior_statement')
        else:
            res[label] = not d1['eligible'] and d['opening_continuity'] != 'verified' and any(x['kind'] == 'replaced' and x['earlier']['source_key'] == 'stmt-2026-11' for x in d.get('prior_statement_revisions', []))
    print('    results:', res)
    return 'OK' if all(res.values()) else 'WEAK'


@probe('N04d', 'RB-04', 'locked November: a late restatement is quarantined and December keeps the frozen balance; a restatement made before the lock and never accepted is not authenticated by the lock')
def _():
    # (1) late restatement of a locked prior period
    os_ = h.approved_locked_november()
    dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='120.00')])); run(os_, 'card_preparation', '2026-12')
    rows = [tx('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO')]
    os_.intake(PREP2, packet('late', [stmt(rows, opening='20.00')])); run(os_, 'card_preparation', '2026-12')
    d1, wp, d = dec_view(os_)
    print('    late restatement of locked November -> D1:', d1['blockers'], '| continuity:', d['opening_continuity'], '| exceptions:', exceptions_of(os_))
    frozen = 'STATEMENT_OPENING_BALANCE_BREAK' in d1['blockers'] and d['opening_continuity'] == 'mismatch' and any(e[0] == 'stmt-2026-11' and e[2] == 'LATE_ACTIVITY_IN_LOCKED_PERIOD' for e in exceptions_of(os_))
    # (2) restated while open, never accepted, November then locked with acknowledgement
    os_, rows, dec = break_then_restate()
    lk = show('lock November with the restatement unaccepted (acknowledged)', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock', 'probe acknowledgement of unsettled items'))
    run(os_, 'card_preparation', '2026-12'); d1, wp, d = dec_view(os_)
    print('    November locked with an unaccepted restatement -> D1:', brief(d1), '| continuity:', d['opening_continuity'])
    not_authenticated = lk[0] == 'ok' and not d1['eligible'] and d['opening_continuity'] != 'verified' and bool(d.get('prior_statement_revisions'))
    print('    frozen=%s not_authenticated=%s' % (frozen, not_authenticated))
    return 'OK' if frozen and not_authenticated else 'WEAK'


@probe('N04e', 'RB-04', 'observation: a restated prior statement whose period has no card activity has no acceptance route')
def _():
    os_ = h.new_os(periods=(NOV, DEC))
    os_.intake(PREP, packet('nov', [stmt([], opening='100.00')])); run(os_, 'card_preparation')
    dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='120.00')])); run(os_, 'card_preparation', '2026-12')
    os_.intake(PREP2, packet('restate', [stmt([], opening='120.00')])); run(os_, 'card_preparation'); run(os_, 'card_preparation', '2026-12')
    d1, wp, d = dec_view(os_)
    print('    zero-activity November restated -> D1:', brief(d1), '| continuity:', d['opening_continuity'], '| acceptance:', d.get('prior_statement_acceptance'))
    return 'NOTE' if not d1['eligible'] and d['opening_continuity'] != 'verified' else 'WEAK'


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
