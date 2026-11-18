"""Fable acceptance probes for the RA-01 to RA-08 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_ra_acceptance_probes.py <project-root> [PROBE_ID ...]

Imports the application from <project-root> and drives it through public service operations
only. Temporary SQLite files, fictional data, no network, model, posting or payment.
Authority is explicit: every synthetic grant is in ROLES or made on the line that needs it.
Each refusal is paired with a positive control.

Verdicts: OK control held | WEAK confirmed gap (exit 1) | NOTE observation needing a decision
          | ERROR probe could not reach its intended state (exit 1)

The helper section is copied unchanged from the earlier independent script
(fable_rv_acceptance_probes.py, lines 30-254); one line is added to new_os to remember the
database path for the restart check.
"""
import copy
import json
import sys
import tempfile
import traceback
from decimal import Decimal
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))

from accounting_agent.core import Actor, ControlError, normalize  # noqa: E402
from accounting_agent.demo import load  # noqa: E402
from accounting_agent.service import AccountingOS  # noqa: E402

ORG, CLIENT = 'demo_org', 'bird_bowl_demo'
SCOPE = ORG + '/' + CLIENT + '/local'
PROFILE = load('config/bird_bowl.demo.json')      # fictional demo profile shipped with the app
NOV = ('2026-11', '2026-11-01', '2026-11-30')
DEC = ('2026-12', '2026-12-01', '2026-12-31')
CARD = 'demo_card_001'


def human(name, role, client=CLIENT):
    return Actor(name, role, ORG, client, kind='human')


ADMIN = human('rv-authority-admin', 'administrator')
PREP = human('rv-preparer', 'preparer')
PREP2 = human('rv-preparer-2', 'preparer')
CTRL = human('rv-policy-approver', 'reviewer')
CTRL2 = human('rv-policy-approver-2', 'reviewer')
REV = human('rv-reviewer', 'reviewer')
REV2 = human('rv-reviewer-2', 'reviewer')
REV3 = human('rv-reviewer-3', 'reviewer')
REV4 = human('rv-reviewer-4', 'reviewer')
DISP = human('rv-dispositioner', 'reviewer')
FIN = human('rv-finalizer', 'reviewer')
PADMIN = human('rv-period-admin', 'reviewer')
WORKER = Actor('rv-worker', 'worker', ORG, CLIENT, kind='service')
# Explicit, complete list of synthetic grants used by the probes.
ROLES = {
    CTRL.id: ['approve_profile', 'approve_rule', 'approve_mandate'],
    CTRL2.id: ['approve_profile', 'approve_rule', 'approve_mandate'],
    REV.id: ['review'], REV2.id: ['review'], REV3.id: ['review'], REV4.id: ['review'],
    DISP.id: ['disposition'],
    FIN.id: ['finalize', 'lock'],
    PADMIN.id: ['lock'],
}

TMP = tempfile.TemporaryDirectory(prefix='fable-ra-accept-')
COUNTER = [0]
PROBES = []


def probe(pid, ticket, title):
    def register(fn):
        PROBES.append((pid, ticket, title, fn))
        return fn
    return register


def attempt(fn, *args, **kwargs):
    """Return ('ok', result) or ('refused', http-style status, message)."""
    try:
        return ('ok', fn(*args, **kwargs))
    except ControlError as exc:
        return ('refused', exc.status, str(exc))


def show(label, result):
    print('   ', label + ':', result if result[0] == 'refused' else ('ok', result[1]))
    return result


def new_os(profile=None, periods=(NOV,), approve=True, proposer=PREP, approver=CTRL):
    COUNTER[0] += 1
    os_ = AccountingOS(Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0]), [SCOPE])
    os_.probe_path = Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0])
    sid = os_.onboard(proposer, copy.deepcopy(profile or PROFILE))        # proposed only
    os_.probe_profile_id = sid
    for subject, permissions in ROLES.items():
        os_.grant_authority(ADMIN, subject, permissions, 'Fictional probe authority; listed in ROLES')
    if approve:
        os_.approve_profile_version(approver, sid, 'Explicit independent approval of the fictional probe profile')
    for p in periods:
        os_.open_period(PADMIN, *p, 'Fictional probe period')
    return os_


def packet(batch, sources, period_id=None):
    p = {'synthetic': True, 'organization_id': ORG, 'client_id': CLIENT,
         'external_company_id': PROFILE['external_company_id'], 'batch_id': batch, 'sources': sources}
    if period_id:
        p['period_id'] = period_id
    return p


def tx(sid, date, amount, desc='ACME PAPER DEMO', currency='USD', status='posted', activity='purchase', as_of=None, **extra):
    data = {'source_id': sid, 'source_system': 'fixture', 'account_id': CARD, 'date': date, 'description': desc,
            'amount': amount, 'currency': currency, 'status': status, 'activity': activity}
    data.update(extra)
    row = {'kind': 'transaction', 'key': CARD + ':' + sid, 'data': data}
    if as_of is not None:
        row['as_of'] = as_of
    return row


def rc(sid, date, amount, vendor='ACME PAPER DEMO', currency='USD', key=None, content=None, as_of=None):
    row = {'kind': 'receipt', 'key': key or 'receipt-' + sid,
           'data': {'transaction_source_id': sid, 'account_id': CARD, 'date': date, 'vendor': vendor, 'amount': amount,
                    'currency': currency, 'content': content or 'Fictional probe receipt for ' + sid}}
    if as_of is not None:
        row['as_of'] = as_of
    return row


def stmt(rows, period=NOV, opening='0.00', line_ids=True, key=None, as_of=None, **override):
    """Fictional statement that ties to the posted, same-currency, in-period rows supplied.
    Used so that a probe isolates the control under test; statement probes build their own."""
    totals = {k: Decimal('0.00') for k in ('purchase', 'credit', 'payment', 'fee', 'interest', 'transfer', 'unknown')}
    ids = []
    for r in rows:
        d = r['data']
        if r['kind'] != 'transaction' or d['status'] != 'posted' or d['currency'] != 'USD' or not period[1] <= d['date'] <= period[2]:
            continue
        totals[d['activity']] += Decimal(d['amount'])
        ids.append(d['source_id'])
    data = {'account_id': CARD, 'statement_id': key or 'stmt-' + period[0], 'currency': 'USD', 'period_start': period[1], 'period_end': period[2],
            'opening_balance': opening, 'closing_balance': str(Decimal(opening) + sum(totals.values())),
            'totals': {k: str(v) for k, v in totals.items()}, 'line_count': len(ids), 'provenance': 'system_extract',
            'sign_convention': 'positive_charges_negative_credits_and_payments', 'content': 'Fictional probe statement'}
    if line_ids:
        data['line_ids'] = ids
    data.update(override)
    row = {'kind': 'statement', 'key': key or 'stmt-' + period[0], 'data': data}
    if as_of is not None:
        row['as_of'] = as_of
    return row


def journal(key, date, lines, supporting, **extra):
    data = {'date': date, 'currency': 'USD', 'memo': 'Fictional probe journal', 'supporting_keys': supporting,
            'lines': [dict({'account_id': a, 'debit': d, 'credit': c}, **({'dimensions': dim} if dim is not None else {})) for a, d, c, dim in lines]}
    data.update(extra)
    return {'kind': 'journal', 'key': key, 'data': data}


def doc(key, dtype, period_id='2026-11', journal_keys=None, content='Fictional probe document'):
    data = {'document_type': dtype, 'content': content}
    if period_id:
        data['period_id'] = period_id
    if journal_keys is not None:
        data['journal_keys'] = journal_keys
    return {'kind': 'document', 'key': key, 'data': data}


def run(os_, workflow, period_id='2026-11', who=PREP):
    rid = os_.enqueue(who, workflow, period_id)
    os_.drain(WORKER)
    return rid


def arts(os_, key=None, period_id=None, kinds=('card_proposal', 'journal_proposal')):
    return [a for a in os_.state(PREP)['artifacts'] if (key is None or a['item_key'] == key)
            and (period_id is None or a['period_id'] == period_id) and (kinds is None or a['kind'] in kinds)]


def gov(os_, key, period_id='2026-11', kinds=('card_proposal', 'journal_proposal')):
    found = [a for a in arts(os_, key, period_id, kinds) if a['governing']]
    return found[0] if found else None


def review(os_, who, a, decision, reason='Fictional probe review'):
    return attempt(os_.review, who, a['id'], a['hash'], a['fingerprint'], decision, reason)


def brief(a):
    return None if a is None else {'id': a['id'], 'eligible': bool(a['eligible']), 'status': a['review_status'], 'blockers': a['blockers']}


def clean_november(os_, extra=(), batch='base', statement=True):
    """Two ordinary fictional purchases with matching receipts and a tying statement."""
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'),
            tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')] + list(extra)
    if statement:
        rows.append(stmt(rows))
    os_.intake(PREP, packet(batch, rows))
    return rows




def support(a, distinct=False):
    """Evidence references for a disposition: everything the artifact relies on, and for a
    distinct-purchases decision also the receipts of every duplicate candidate."""
    d = a['payload']['data']
    return d['evidence'] + (d.get('duplicate_evidence', []) if distinct else [])


def dispose(os_, key, code, choice, payload=None, evidence=None, who=None, period='2026-11', workflow='card_preparation', **kw):
    a = gov(os_, key, period)
    return attempt(os_.disposition, who or DISP, workflow, period, key, code, choice, payload or {},
                   support(a, choice == 'distinct_purchases') if evidence is None else evidence, 'Fictional probe disposition', **kw)


def lines_of(a):
    e = a['payload']['data'].get('proposed_entry')
    return sorted((l['account_id'], l['debit'], l['credit']) for l in e['lines']) if e else None


def duplicate_pair(extra=()):
    os_ = new_os()
    rows = [tx('D1', '2026-11-06', '90.00'), rc('D1', '2026-11-06', '90.00', content='Fictional receipt one'),
            tx('D2', '2026-11-06', '90.00'), rc('D2', '2026-11-06', '90.00', content='Fictional receipt two')] + list(extra)
    os_.intake(PREP, packet('dups', rows + [stmt(rows)])); run(os_, 'card_preparation')
    return os_, rows


OCT = ('2026-10', '2026-10-01', '2026-10-31')
NO_EVIDENCE = {'none': 'Fixed fictional evidence; demonstration authority only'}

# ---------------------------------------------------------------------------------------
# Part 1. One independent scenario per correction, RV-01 to RV-17

# =======================================================================================
# RA-01  supersession chains, arrival order, reopen, relock, restart
# =======================================================================================

def approved_locked_november(periods=(NOV, DEC)):
    os_ = new_os(periods=periods)
    clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        r = review(os_, REV, gov(os_, CARD + ':' + k), 'approve'); assert r[0] == 'ok', r
    os_.lock_period(PADMIN, '2026-11', 'probe lock')
    return os_


def sup(sid, date, amount, over, **kw):
    row = tx(sid, date, amount, **kw); row['supersedes'] = CARD + ':' + over
    return row


def exceptions_of(os_):
    return sorted((e['source_key'], e['period_id'], e['reason']) for e in os_.state(PREP)['source_exceptions'])


def governing_keys(os_, period):
    return sorted(a['item_key'] for a in arts(os_, None, period) if a['governing'])


@probe('R01a', 'RA-01/RA-06', 'a four-link chain with mixed receipt order stays quarantined under lock; reopen admits only the last link; whole-evidence disposition takes effect; no double approval; relock and restart are stable')
def _():
    os_ = approved_locked_november()
    os_.intake(PREP2, packet('s1', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')]))
    os_.intake(PREP2, packet('s2-receipt-first', [rc('A1Y', '2026-12-03', '40.00')]))          # receipt before its transaction
    os_.intake(PREP2, packet('s2', [sup('A1Y', '2026-12-03', '40.00', 'A1X')]))
    last = [sup('A1Z', '2026-12-04', '40.00', 'A1Y'), rc('A1Z', '2026-12-04', '40.00')]
    other = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    pk = packet('s3', last + other + [stmt(last + other, DEC, opening='100.00')])
    os_.intake(PREP2, pk); replay = os_.intake(PREP2, pk)
    run(os_, 'card_preparation', '2026-12', PREP2)
    exc = exceptions_of(os_); st = os_.export(PREP)
    keyof = {s['id']: s['source_key'] for s in st['evidence_history']}
    moves = [(m['from_period_id'], m['to_period_id'], m['blocked'], m['had_approval'], keyof.get(m['snapshot_id'])) for m in st['source_move_history']]
    dec = governing_keys(os_, '2026-12')
    print('    exceptions under lock:', exc)
    print('    December governing items under lock:', dec, '| blocked moves:', sum(1 for m in moves if m[2]), '| moves with approval evidence:', sum(1 for m in moves if m[3]))
    want = {(CARD + ':' + k, '2026-11', 'SOURCE_MOVED_FROM_LOCKED_PERIOD') for k in ('A1X', 'A1Y', 'A1Z')} | {('receipt-' + k, '2026-11', 'SOURCE_MOVED_FROM_LOCKED_PERIOD') for k in ('A1X', 'A1Y', 'A1Z')}
    held = want <= set(exc) and not any(k in dec for k in (CARD + ':A1X', CARD + ':A1Y', CARD + ':A1Z')) and replay['replay'] and gov(os_, CARD + ':A1', '2026-11')['review_status'] == 'approve' and all(m[2] == 1 for m in moves if m[0] == '2026-11') and {m[4] for m in moves if m[2] == 1 and m[3] == 1} == {CARD + ':A1X', CARD + ':A1Y', CARD + ':A1Z'}
    # a revision of a quarantined middle link changes nothing
    os_.intake(PREP2, packet('s1-rev', [dict(sup('A1X', '2026-12-02', '41.00', 'A1'))])); run(os_, 'card_preparation', '2026-12', PREP2)
    held = held and not any(k in governing_keys(os_, '2026-12') for k in (CARD + ':A1X', CARD + ':A1Y', CARD + ':A1Z'))
    print('    after a revision of the quarantined middle link, December governing:', governing_keys(os_, '2026-12'))
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    nov_keys, dec_keys = governing_keys(os_, '2026-11'), governing_keys(os_, '2026-12')
    z = gov(os_, CARD + ':A1Z', '2026-12'); st = os_.export(PREP)
    print('    after reopen -> November governing:', nov_keys, '| December governing:', dec_keys, '| A1Z:', brief(z))
    kept = {k: sum(1 for s in st['evidence_history'] if s['source_key'] == CARD + ':' + k) for k in ('A1', 'A1X', 'A1Y', 'A1Z')}
    ever_dec = sorted({s['source_key'] for s in st['evidence_history'] for b in st['source_period_history'] if b['snapshot_id'] == s['id'] and b['period_id'] == '2026-12' and b['admitted'] and s['source_key'] in (CARD + ':A1', CARD + ':A1X', CARD + ':A1Y')})
    print('    history kept (versions per link):', kept, '| intermediates ever admitted to December:', ever_dec)
    released = (CARD + ':A1' not in nov_keys and CARD + ':A1Z' in dec_keys and not any(k in dec_keys for k in (CARD + ':A1', CARD + ':A1X', CARD + ':A1Y'))
                and z is not None and 'SOURCE_TRANSITION_REQUIRES_REVIEW' in z['blockers'] and 'MISSING_RECEIPT' not in z['blockers'] and all(kept.values()) and not ever_dec)
    # RA-06: cite the whole evidence list, predecessor snapshots included
    whole = z['payload']['data']['evidence']
    print('    evidence list of A1Z includes predecessor snapshots:', sorted(e['source_key'] for e in whole if 'link_id' in e))
    stranger = [e for e in gov(os_, CARD + ':A2', '2026-11')['payload']['data']['evidence'] if e['source_key'] == CARD + ':A2']
    unrelated = show('same disposition also citing the row of an unrelated November item (A2)', attempt(os_.disposition, DISP, 'card_preparation', '2026-12', CARD + ':A1Z', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', {}, whole + stranger, 'probe'))
    d = show('settlement_verified citing the whole evidence list', dispose(os_, CARD + ':A1Z', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', period='2026-12'))
    run(os_, 'card_preparation', '2026-12', PREP2); z2 = gov(os_, CARD + ':A1Z', '2026-12')
    print('    after the disposition:', brief(z2))
    ra06 = (d[0] == 'ok' and 'SOURCE_TRANSITION_REQUIRES_REVIEW' not in z2['blockers']) or (d[0] == 'refused' and 'reference' in d[2].lower())
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'Fictional probe grant: dispositioner attempts final review')
    by_disp = show('the dispositioner then approves A1Z', review(os_, DISP, z2, 'approve'))
    appr = show('independent approval of December A1Z', review(os_, REV2, z2, 'approve')) if z2['eligible'] else ('skipped',)
    nov_a1 = gov(os_, CARD + ':A1', '2026-11')
    single = appr[0] == 'ok' and nov_a1 is None
    print('    approved in December:', appr[0], '| governing November A1:', brief(nov_a1))
    # relock the former origin, then revise the destination
    for k in governing_keys(os_, '2026-11'):
        a = gov(os_, k, '2026-11')
        if a['eligible'] and a['review_status'] == 'pending':
            review(os_, REV, a, 'approve')
    lk = show('relock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe relock', 'probe acknowledgement'))
    rev = [sup('A1Z', '2026-12-04', '42.00', 'A1Y'), rc('A1Z', '2026-12-04', '42.00')]
    os_.intake(PREP2, packet('z-rev', rev + [stmt(rev + other, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    z3 = gov(os_, CARD + ':A1Z', '2026-12'); exc3 = exceptions_of(os_)
    print('    after relock and a later revision of A1Z -> December A1Z:', brief(z3), '| exceptions:', exc3)
    relock = z3 is not None and z3['payload']['data']['transaction']['amount'] == '42.00' and not any(e[0] == CARD + ':A1Z' for e in exc3)
    # restart
    before = (governing_keys(os_, '2026-11'), governing_keys(os_, '2026-12'), exceptions_of(os_))
    again = AccountingOS(os_.store.path if hasattr(os_.store, 'path') else os_.probe_path, [SCOPE])
    after = (governing_keys(again, '2026-11'), governing_keys(again, '2026-12'), exceptions_of(again))
    print('    state identical after restart:', before == after, '| audit chain:', again.verify_audit(PREP))
    ok = held and released and ra06 and unrelated[0] == 'refused' and by_disp[0] == 'refused' and single and relock and before == after
    print('    held=%s released=%s ra06=%s single=%s relock=%s' % (held, released, ra06, single, relock))
    return 'OK' if ok else 'WEAK'


@probe('R01b', 'RA-01', 'a charge already admitted to December that later declares it supersedes an approved charge in locked November is not approvable in both periods')
def _():
    os_ = approved_locked_november()
    plain = [tx('B1', '2026-12-02', '40.00'), rc('B1', '2026-12-02', '40.00')]
    os_.intake(PREP2, packet('b-plain', plain + [stmt(plain, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    B1 arrives in December with no supersession claim:', brief(gov(os_, CARD + ':B1', '2026-12')))
    os_.intake(PREP2, packet('b-claims', [sup('B1', '2026-12-02', '40.00', 'A1')])); run(os_, 'card_preparation', '2026-12', PREP2)
    b = gov(os_, CARD + ':B1', '2026-12'); exc = exceptions_of(os_); st = os_.export(PREP)
    print('    B1 is re-sent declaring it supersedes A1 (approved, November locked) -> December B1:', brief(b))
    print('    exceptions:', exc, '| moves:', [(m['from_period_id'], m['to_period_id'], m['blocked'], m['had_approval']) for m in st['source_move_history']])
    print('    events:', sorted({(e['code'], e['period_id'], e['item_key']) for e in st['accounting_events']}))
    if b is None:
        return 'OK'
    d = show('settlement_verified citing the whole evidence list', dispose(os_, CARD + ':B1', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', period='2026-12'))
    run(os_, 'card_preparation', '2026-12', PREP2); b2 = gov(os_, CARD + ':B1', '2026-12')
    appr = show('independent approval of December B1', review(os_, REV2, b2, 'approve'))
    nov = gov(os_, CARD + ':A1', '2026-11')
    both = appr[0] == 'ok' and nov is not None and nov['review_status'] == 'approve'
    print('    December B1:', brief(gov(os_, CARD + ':B1', '2026-12')), '| November A1:', brief(nov), '| approved in both periods:', both)
    fin = show('finalize December without acknowledgement', attempt(os_.finalize_package, FIN, '2026-12', 'card_preparation', 'probe'))
    return 'WEAK' if both else 'OK'


@probe('R01c', 'RA-01', 'a link that arrives before the link it replaces (unresolved), and is later resolved, is not released while the root is locked')
def _():
    os_ = approved_locked_november()
    early = [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('y-first', early + [stmt(early, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    print('    A1Y (supersedes A1X, not yet received):', brief(gov(os_, CARD + ':A1Y', '2026-12')))
    os_.intake(PREP2, packet('x-second', [sup('A1X', '2026-12-02', '40.00', 'A1'), rc('A1X', '2026-12-02', '40.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    y = gov(os_, CARD + ':A1Y', '2026-12'); print('    A1X then arrives (supersedes locked A1) -> A1Y:', brief(y), '| exceptions:', exceptions_of(os_))
    os_.intake(PREP2, packet('y-resent', [dict(sup('A1Y', '2026-12-03', '40.00', 'A1X'), as_of=None) if False else sup('A1Y', '2026-12-03', '40.00', 'A1X')])); run(os_, 'card_preparation', '2026-12', PREP2)
    y = gov(os_, CARD + ':A1Y', '2026-12'); exc = exceptions_of(os_)
    print('    A1Y re-sent so that its link resolves -> A1Y:', brief(y), '| exceptions:', exc)
    if y is None:
        return 'OK'
    d = show('settlement_verified on A1Y', dispose(os_, CARD + ':A1Y', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', period='2026-12'))
    run(os_, 'card_preparation', '2026-12', PREP2); y2 = gov(os_, CARD + ':A1Y', '2026-12')
    appr = show('independent approval of December A1Y', review(os_, REV2, y2, 'approve'))
    nov = gov(os_, CARD + ':A1', '2026-11')
    both = appr[0] == 'ok' and nov is not None and nov['review_status'] == 'approve'
    print('    December A1Y:', brief(gov(os_, CARD + ':A1Y', '2026-12')), '| November A1:', brief(nov), '| approved in both periods:', both)
    return 'WEAK' if both else 'OK'


@probe('R01d', 'RA-01', 'two- and three-source supersession cycles are refused and leave nothing behind')
def _():
    os_ = new_os(periods=(NOV, DEC))
    clean_november(os_)
    os_.intake(PREP, packet('c1', [sup('C2', '2026-11-05', '40.00', 'A1')]))
    os_.intake(PREP, packet('c2', [sup('C3', '2026-11-06', '40.00', 'C2')]))
    before = len(os_.export(PREP)['evidence_history'])
    two = show('A1 re-sent superseding C2 (two-step cycle through C2 -> A1)', attempt(os_.intake, PREP, packet('cyc2', [sup('A1', '2026-11-03', '40.00', 'C2')])))
    three = show('A1 re-sent superseding C3 (three-step cycle)', attempt(os_.intake, PREP, packet('cyc3', [sup('A1', '2026-11-03', '40.00', 'C3'), tx('Q1', '2026-11-07', '5.00')])))
    selfref = show('a source superseding itself', attempt(os_.intake, PREP, packet('self', [sup('C3', '2026-11-06', '40.00', 'C3')])))
    after = os_.export(PREP)
    atomic = len(after['evidence_history']) == before and not any(s['source_key'] == CARD + ':Q1' for s in after['evidence_history'])
    print('    evidence rows unchanged after the refusals (atomic):', atomic)
    return 'OK' if two[0] == three[0] == selfref[0] == 'refused' and atomic else 'WEAK'


# =======================================================================================
# RA-03  receipt replacement
# =======================================================================================

def mismatch_november():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '39.99'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('b1', rows + [stmt(rows)])); run(os_, 'card_preparation')
    assert 'RECEIPT_AMOUNT_POLICY_UNSET' in gov(os_, CARD + ':A1')['blockers']
    return os_, rows


def revs(a):
    return [(r['kind'], r['earlier']['source_key'], r['earlier']['version'], r['earlier']['supplier'], r['current']['source_key'], r['current']['supplier'], r['changed_fields']) for r in a['payload']['data'].get('evidence_revisions', [])]


@probe('R03a', 'RA-03', 'same-key and new-key receipt replacement are held and disclosed; both suppliers are refused; a non-supplier accepts; final review is separate; a further change lapses the acceptance')
def _():
    out = []
    for order in ('withdraw-with-replacement', 'replacement-before-withdrawal'):
        os_, rows = mismatch_november()
        old = dict(copy.deepcopy(rows[1]), tombstone=True, removal_reason='voided')
        new = rc('A1', '2026-11-03', '40.00', key='receipt-A1-new', content='Fictional replacement receipt')
        if order == 'withdraw-with-replacement':
            os_.intake(PREP2, packet('r', [old, new]))
        else:
            os_.intake(PREP2, packet('r1', [new])); run(os_, 'card_preparation')
            mid = gov(os_, CARD + ':A1'); print('    [%s] both receipts active:' % order, mid['blockers'], '| revisions:', revs(mid))
            assert any(b.startswith('RECEIPT_MULTIPLE') or b.startswith('MULTIPLE_RECEIPTS') for b in mid['blockers'])
            os_.intake(PREP2, packet('r2', [old]))
        run(os_, 'card_preparation'); a = gov(os_, CARD + ':A1')
        print('    [%s] after replacement:' % order, brief(a)); print('    [%s] revisions:' % order, revs(a))
        r = a['payload']['data'].get('evidence_revisions', [])
        disclosed = ('EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'] and any(x['kind'] == 'replaced' and x['earlier']['source_key'] == 'receipt-A1' and x['earlier']['supplier'] == PREP.id and x['current']['supplier'] == PREP2.id and 'amount' in x['changed_fields'] for x in r))
        g = lambda who: os_.grant_authority(ADMIN, who.id, ['disposition'], 'Fictional probe grant: supplier attempts acceptance')
        g(PREP); g(PREP2)
        s1 = show('supplier of the withdrawn receipt accepts', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted', who=human(PREP.id, 'reviewer')))
        s2 = show('supplier of the replacement accepts', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted', who=human(PREP2.id, 'reviewer')))
        ok = show('granted non-supplier accepts', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted'))
        run(os_, 'card_preparation'); a2 = gov(os_, CARD + ':A1'); print('    [%s] after acceptance:' % order, brief(a2), '| revisions still disclosed:', bool(revs(a2)))
        os_.grant_authority(ADMIN, DISP.id, ['review'], 'Fictional probe grant: acceptor attempts final review')
        self_review = show('the acceptor gives the final review', review(os_, DISP, a2, 'approve'))
        old_supplier = show('supplier of the withdrawn receipt gives the final review', (os_.grant_authority(ADMIN, PREP.id, ['review'], 'Fictional probe grant'), review(os_, human(PREP.id, 'reviewer'), a2, 'approve'))[1])
        final = show('independent final review', review(os_, REV, a2, 'approve'))
        os_.intake(PREP2, packet('r3', [rc('A1', '2026-11-03', '40.00', key='receipt-A1-new', content='Fictional replacement receipt, edited again')])); run(os_, 'card_preparation')
        a3 = gov(os_, CARD + ':A1'); print('    [%s] after a further change to the replacement:' % order, brief(a3))
        out.append(disclosed and s1[0] == s2[0] == 'refused' and ok[0] == 'ok' and a2['eligible'] and bool(revs(a2)) and self_review[0] == 'refused' and old_supplier[0] == 'refused' and final[0] == 'ok' and 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a3['blockers'] and not a3['eligible'])
    # a genuine additional receipt is a multiple-support question, not a revision
    os_ = new_os(); clean_november(os_); run(os_, 'card_preparation')
    os_.intake(PREP2, packet('second', [rc('A1', '2026-11-03', '40.00', key='receipt-A1-second', content='Fictional second receipt')])); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); print('    additional still-active receipt:', a['blockers'], '| revisions:', revs(a))
    extra = not revs(a) and 'EVIDENCE_REVISED_REQUIRES_REVIEW' not in a['blockers'] and any('MULTIPLE' in b for b in a['blockers'])
    return 'OK' if all(out) and extra else 'WEAK'


@probe('R03b', 'RA-03', 'replacing a receipt by re-pointing the old key at another transaction id and supplying a new key is still held and disclosed')
def _():
    os_, rows = mismatch_november()
    repointed = rc('A1-VOID', '2026-11-03', '39.99', key='receipt-A1')            # same key, now names a transaction id that does not exist
    new = rc('A1', '2026-11-03', '40.00', key='receipt-A1-new', content='Fictional replacement receipt')
    os_.intake(PREP, packet('repoint', [repointed, new])); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); d = a['payload']['data']
    print('    old key re-pointed away, new key supplied at 40.00 ->', brief(a))
    print('    receipts relied on:', [(e['source_key'], e['version']) for e in d['evidence'] if e['source_key'].startswith('receipt')], '| revisions disclosed:', revs(a), '| exceptions:', exceptions_of(os_))
    appr = show('independent approval', review(os_, REV, a, 'approve'))
    return 'WEAK' if appr[0] == 'ok' and not revs(a) else 'OK'


# =======================================================================================
# RA-04  statement revision
# =======================================================================================

WRONG = {'purchase': '90.00', 'credit': '0.00', 'payment': '0.00', 'fee': '0.00', 'interest': '0.00', 'transfer': '0.00', 'unknown': '0.00'}


def short_statement(key=None):
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('b1', rows + [stmt(rows, totals=WRONG, closing_balance='90.00', key=key)])); run(os_, 'card_preparation')
    assert 'STATEMENT_CONTROL_MISMATCH' in gov(os_, CARD + ':A1')['blockers']
    return os_, rows


def workpaper(os_, period='2026-11'):
    return gov(os_, 'statement:' + CARD, period, kinds=None)


@probe('R04a', 'RA-04', 'a statement corrected to tie (same key, or withdrawn and replaced under a new key) is held on every relying item and disclosed on the workpaper; suppliers of any version are refused; acceptance is item-bound, lapses on new evidence and confers no final review')
def _():
    out = []
    for variant in ('same-key', 'new-key'):
        os_, rows = short_statement()
        if variant == 'same-key':
            os_.intake(PREP2, packet('b2', [stmt(rows)]))
        else:
            gone = dict(stmt(rows, totals=WRONG, closing_balance='90.00'), tombstone=True, removal_reason='voided')
            os_.intake(PREP2, packet('b2', [gone, stmt(rows, key='stmt-2026-11-replacement')]))
        run(os_, 'card_preparation')
        a1, a2, wp = gov(os_, CARD + ':A1'), gov(os_, CARD + ':A2'), workpaper(os_)
        sr = wp['payload']['data'].get('statement_revisions', [])
        print('    [%s] A1: %s | A2: %s' % (variant, brief(a1), brief(a2)))
        print('    [%s] item revisions: %s' % (variant, revs(a1)))
        print('    [%s] workpaper statement_revisions: %s' % (variant, [(r['kind'], r['earlier']['source_key'], r['earlier']['supplier'], r['current']['supplier'], r['changed_fields']) for r in sr]))
        held = all('EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'] and not a['eligible'] and revs(a) for a in (a1, a2)) and bool(sr) and sr[0]['earlier']['supplier'] == PREP.id and sr[0]['current']['supplier'] == PREP2.id and 'totals' in sr[0]['changed_fields']
        direct = show('independent approval without acceptance', review(os_, REV, a1, 'approve'))
        for who in (PREP, PREP2):
            os_.grant_authority(ADMIN, who.id, ['disposition'], 'Fictional probe grant: supplier attempts acceptance')
        s1 = show('supplier of the first statement accepts', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted', who=human(PREP.id, 'reviewer')))
        s2 = show('supplier of the corrected statement accepts', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted', who=human(PREP2.id, 'reviewer')))
        partial = show('acceptance that omits the revised statement from its evidence', attempt(os_.disposition, DISP, 'card_preparation', '2026-11', CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted', {}, [e for e in a1['payload']['data']['evidence'] if not e['source_key'].startswith('stmt')], 'probe'))
        ok = show('granted non-supplier accepts for A1 only', dispose(os_, CARD + ':A1', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted'))
        run(os_, 'card_preparation'); b1, b2 = gov(os_, CARD + ':A1'), gov(os_, CARD + ':A2')
        print('    [%s] after acceptance for A1 -> A1: %s | A2: %s' % (variant, brief(b1), brief(b2)))
        item_bound = b1['eligible'] and not b2['eligible'] and 'EVIDENCE_REVISED_REQUIRES_REVIEW' in b2['blockers']
        os_.grant_authority(ADMIN, DISP.id, ['review'], 'Fictional probe grant: acceptor attempts final review')
        self_review = show('the acceptor gives the final review of A1', review(os_, DISP, b1, 'approve'))
        final = show('independent final review of A1', review(os_, REV, b1, 'approve'))
        key = 'stmt-2026-11' if variant == 'same-key' else 'stmt-2026-11-replacement'
        os_.intake(PREP2, packet('b3', [stmt(rows, key=key, content='Fictional probe statement, re-keyed again')])); run(os_, 'card_preparation')
        c1 = gov(os_, CARD + ':A1'); print('    [%s] after a further change to the statement -> A1: %s' % (variant, brief(c1)))
        lapsed = 'EVIDENCE_REVISED_REQUIRES_REVIEW' in c1['blockers'] and not c1['eligible']
        out.append(held and direct[0] == 'refused' and s1[0] == s2[0] == partial[0] == 'refused' and ok[0] == 'ok' and item_bound and self_review[0] == 'refused' and final[0] == 'ok' and lapsed)
    return 'OK' if all(out) else 'WEAK'


@probe('R04b', 'RA-04', 'a statement replaced by re-pointing the old key at another cycle and supplying a new key for the period is still held and disclosed')
def _():
    os_, rows = short_statement()
    away = stmt(rows, period=('2027-01', '2027-01-01', '2027-01-31'), key='stmt-2026-11', totals=WRONG, closing_balance='90.00')   # same key, different cycle
    os_.intake(PREP, packet('b2', [away, stmt(rows, key='stmt-2026-11-b')])); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); wp = workpaper(os_)
    print('    old statement key re-pointed to another cycle; a new key supplied that ties ->', brief(a))
    print('    item revisions:', revs(a), '| workpaper statement_revisions:', wp['payload']['data'].get('statement_revisions'), '| workpaper blockers:', wp['blockers'], '| exceptions:', exceptions_of(os_))
    appr = show('independent approval', review(os_, REV, a, 'approve'))
    disclosed = bool(revs(a)) or bool(wp['payload']['data'].get('statement_revisions'))
    return 'WEAK' if appr[0] == 'ok' and not disclosed else 'OK'


@probe('R04c', 'RA-04', 'observation: a prior-period statement revised while its period is still open, so that the next opening balance agrees, is disclosed to the next period')
def _():
    os_ = new_os(periods=(NOV, DEC))
    rows = clean_november(os_)                                                     # November closes at 100.00
    dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='120.00')])); run(os_, 'card_preparation', '2026-12')
    d1 = gov(os_, CARD + ':D1', '2026-12'); print('    December opens at 120.00, November closed at 100.00:', d1['blockers'])
    assert 'STATEMENT_OPENING_BALANCE_BREAK' in d1['blockers']
    os_.intake(PREP, packet('nov-fix', [stmt(rows, opening='20.00')])); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12')
    d1 = gov(os_, CARD + ':D1', '2026-12'); wp = workpaper(os_, '2026-12'); a1 = gov(os_, CARD + ':A1', '2026-11')
    print('    preparer restates November (opening 20.00, closing 120.00) -> December D1:', brief(d1), '| November A1:', brief(a1))
    print('    December workpaper continuity:', wp['payload']['data']['opening_continuity'], '| statement_revisions:', wp['payload']['data'].get('statement_revisions'), '| D1 revisions:', revs(d1))
    nov_held = 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a1['blockers']
    dec_told = bool(revs(d1)) or bool(wp['payload']['data'].get('statement_revisions')) or not d1['eligible']
    return 'OK' if dec_told else ('NOTE' if nov_held else 'WEAK')


# =======================================================================================
# RA-02  rule authorship
# =======================================================================================

ACME = {'id': 'demo_acme', 'name': 'Acme Paper Demo', 'aliases': ['ACME PAPER DEMO'], 'category': 'DEMO_OFFICE_SUPPLIES'}
RM = {'date_window_days': 1, 'amount_tolerance': None, 'multiple_receipts': None, 'vendor_method': None, 'statement_substitution': None}


def rule_case(v1_author, v1, v2, kind='vendor_mapping', key='demo_acme', key2=None, item2=None, end1=None, start2='2026-11-01', link=False):
    p = copy.deepcopy(PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_acme']
    o = new_os(profile=p)
    r1 = o.propose_rule(human(v1_author.id, 'preparer'), kind, key, v1, '2026-11-01', end1); o.approve_rule(CTRL, r1, 'probe approval of version 1')
    r2 = o.propose_rule(PREP, kind, key2 or key, v2, start2, None, item2, r1 if link else None); o.approve_rule(CTRL2, r2, 'probe approval of version 2')
    if kind != 'vendor_mapping':
        o.approve_rule(CTRL, o.propose_rule(PREP2, 'vendor_mapping', 'demo_acme', ACME, '2026-11-01'), 'probe mapping')
    clean_november(o); run(o, 'card_preparation'); a = gov(o, CARD + ':A1')
    assert a['eligible'], ('item must be eligible for the review attempt to mean anything', brief(a))
    return o, a


@probe('R02a', 'RA-02', 'unlinked re-proposals keep the earlier author barred (vendor mapping and receipt policy); cosmetic and non-cosmetic values, other categories and aliases behave as specified; an independent reviewer can approve')
def _():
    o, a = rule_case(REV, ACME, dict(ACME, name='Acme Paper Demo.'))
    v = show('unlinked cosmetic vendor re-proposal: author of version 1 approves', review(o, REV, a, 'approve'))
    free = show('independent reviewer approves (positive control)', review(o, REV2, a, 'approve'))
    o, a = rule_case(REV4, RM, dict(RM), kind='receipt_matching', key='default')
    p = show('unlinked identical receipt policy: author of version 1 approves', review(o, REV4, a, 'approve'))
    o, a = rule_case(REV4, dict(RM, date_window_days=3), dict(RM), kind='receipt_matching', key='default')
    p2 = show('unlinked receipt policy with a different earlier value: its author approves (should be allowed)', review(o, REV4, a, 'approve'))
    o, a = rule_case(REV3, dict(ACME, category='DEMO_REPAIRS'), ACME)
    cat = show('earlier version had a different category: its author approves (should be allowed)', review(o, REV3, a, 'approve'))
    o, a = rule_case(REV3, dict(ACME, aliases=['SOMETHING ELSE DEMO']), ACME)
    alias = show('earlier version did not cover this description: its author approves (should be allowed)', review(o, REV3, a, 'approve'))
    o, a = rule_case(REV3, ACME, dict(ACME, aliases=['ACME PAPER DEMO', 'ACME PAPER']))
    wider = show('later version adds an alias, same category for this description: author of version 1 approves', review(o, REV3, a, 'approve'))
    ok = v[0] == 'refused' and free[0] == 'ok' and p[0] == 'refused' and p2[0] == 'ok' and cat[0] == 'ok' and alias[0] == 'ok' and wider[0] == 'refused'
    return 'OK' if ok else 'WEAK'


@probe('R02b', 'RA-02', 'the earlier author stays barred when the identical mapping is re-proposed for the single item, or under a new rule key')
def _():
    o, a = rule_case(REV, ACME, dict(ACME), item2=CARD + ':A1')
    print('    contributors (item-scoped re-proposal):', a['contributors'])
    item = show('identical mapping re-proposed with item scope for this charge: author of the general rule approves', review(o, REV, a, 'approve'))
    o, a = rule_case(REV, ACME, dict(ACME, id='demo_acme'), key2='demo_acme_b', end1='2026-11-02', start2='2026-11-03')
    print('    contributors (new rule key, earlier rule ended the day before):', a['contributors'])
    rekey = show('identical mapping re-proposed under a new rule key: author of the earlier rule approves', review(o, REV, a, 'approve'))
    if item[0] == 'ok':
        return 'WEAK'
    return 'OK' if rekey[0] == 'refused' else 'NOTE'


# =======================================================================================
# RA-05  mandate binding
# =======================================================================================

def mandate_case(periods=(NOV, DEC)):
    os_ = new_os(periods=periods)
    rows = clean_november(os_)
    mid = os_.create_mandate(PREP, ['card_preparation'], '2026-12-01T00:00:00+00:00', '2026-12-05T00:00:00+00:00', 86400, 3, {'kind': 'fixed', 'period_id': '2026-11'}, {'transaction': 'occurrence_start'})
    return os_, rows, mid


def mandate_state(os_, mid):
    m = [x for x in os_.state(PREP)['mandates'] if x['id'] == mid][0]
    return (m['status'], bool(m['active']), m['reason']), [(r['id'], r['status']) for r in os_.state(PREP)['runs'] if r['mandate_id']]


@probe('R05', 'RA-05', 'a relevant rule approved after the mandate suspends it; an irrelevant close rule and a rule outside the period do not; a held occurrence does not dispatch twice')
def _():
    extra = {'id': 'demo_extra', 'name': 'Extra (fictional)', 'aliases': ['EXTRA VENDOR DEMO'], 'category': 'DEMO_REPAIRS'}
    fresh = lambda: [tx('A9', '2026-11-25', '12.00', as_of='2026-12-01T13:00:00+00:00'), rc('A9', '2026-11-25', '12.00')]
    # (a) relevant later rule
    os_, rows, mid = mandate_case(); os_.approve_mandate(CTRL, mid, 'probe standing authority')
    os_.approve_rule(CTRL, os_.propose_rule(PREP2, 'vendor_mapping', 'demo_extra', extra, '2026-11-15'), 'probe: relevant rule approved after the mandate')
    os_.tick(PREP, '2026-12-01T12:00:00+00:00'); f = fresh(); os_.intake(PREP, packet('fresh', f + [stmt(rows + f)])); os_.drain(WORKER)
    a = mandate_state(os_, mid); print('    relevant vendor rule approved after the mandate ->', a)
    # (b) irrelevant kind and (c) outside the period
    os_, rows, mid = mandate_case(); os_.approve_mandate(CTRL, mid, 'probe standing authority')
    os_.approve_rule(CTRL, os_.propose_rule(PREP2, 'close_checklist', 'close', [{'type': 'document', 'document_type': 'trial_balance'}], '2026-11-01'), 'probe: close rule, not read by card preparation')
    os_.approve_rule(CTRL, os_.propose_rule(PREP2, 'vendor_mapping', 'demo_extra', extra, '2027-03-01'), 'probe: vendor rule effective after the target period')
    os_.tick(PREP, '2026-12-01T12:00:00+00:00'); f = fresh(); os_.intake(PREP, packet('fresh', f + [stmt(rows + f)])); os_.drain(WORKER)
    b = mandate_state(os_, mid); print('    close rule and a rule effective next year approved after the mandate ->', b)
    again = os_.tick(PREP, '2026-12-01T18:00:00+00:00'); os_.drain(WORKER); b2 = mandate_state(os_, mid)
    print('    second tick in the same occurrence ->', b2)
    ok = (not a[0][1] and a[0][0] == 'needs_reconfirmation' and not a[1]) and (b[0][1] and len(b[1]) == 1) and len(b2[1]) == 1
    return 'OK' if ok else 'WEAK'


# =======================================================================================
# RA-07  supporting evidence
# =======================================================================================

@probe('R07', 'RA-07', 'own or unrelated transaction rows and unrelated receipts are not supporting evidence; the item receipt or its account statement is')
def _():
    def case():
        os_ = new_os()
        rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('V1', '2026-11-09', '7.00', desc='NOBODY KNOWN DEMO'), rc('V1', '2026-11-09', '7.00', vendor='NOBODY KNOWN DEMO')]
        os_.intake(PREP, packet('b', rows + [stmt(rows)])); run(os_, 'card_preparation')
        v = gov(os_, CARD + ':V1'); assert 'UNKNOWN_VENDOR' in v['blockers'], brief(v)
        ev = {e['source_key']: e for a in arts(os_) if a['governing'] for e in a['payload']['data']['evidence']}
        return os_, ev
    pay = {'account_id': 'DEMO_OFFICE_SUPPLIES'}
    def go(label, keys):
        os_, ev = case()
        return show(label, attempt(os_.disposition, DISP, 'card_preparation', '2026-11', CARD + ':V1', 'UNKNOWN_VENDOR', 'confirm_vendor', pay, [ev[k] for k in keys], 'probe'))
    own = go('own row only', [CARD + ':V1'])
    other_row = go('own row and the row of another item', [CARD + ':V1', CARD + ':A1'])
    other_rc = go('own row and the receipt of another item', [CARD + ':V1', 'receipt-A1'])
    own_rc = go('own row and its own receipt', [CARD + ':V1', 'receipt-V1'])
    st = go('own row and the account statement', [CARD + ':V1', 'stmt-2026-11'])
    ok = own[0] == other_row[0] == other_rc[0] == 'refused' and own_rc[0] == st[0] == 'ok'
    return 'OK' if ok else 'WEAK'


# =======================================================================================
# RA-08  circular exclusion
# =======================================================================================

@probe('R08', 'RA-08', 'two- and three-charge exclusion cycles are refused before and after re-preparation; one live entry remains; revocation and withdrawal of the survivor restore the excluded charge')
def _():
    dup = lambda o, k, t, choice='duplicate_of': dispose(o, CARD + ':' + k, 'POSSIBLE_DUPLICATE', choice, {'duplicate_of': CARD + ':' + t})
    o, rows = duplicate_pair()
    a = show('D2 duplicate_of D1', dup(o, 'D2', 'D1')); b = show('D1 source_replay of D2, before re-preparation', dup(o, 'D1', 'D2', 'source_replay'))
    run(o, 'card_preparation'); c = show('D1 duplicate_of D2, after re-preparation', dup(o, 'D1', 'D2'))
    x1, x2 = gov(o, CARD + ':D1'), gov(o, CARD + ':D2'); print('    D1:', brief(x1), lines_of(x1), '| D2:', brief(x2), lines_of(x2))
    two = a[0] == 'ok' and b[0] == c[0] == 'refused' and lines_of(x1) is not None and lines_of(x2) is None
    extra = [tx('D3', '2026-11-06', '90.00'), rc('D3', '2026-11-06', '90.00', content='Fictional receipt three')]
    o, rows = duplicate_pair(extra)
    s1 = show('D1 duplicate_of D2', dup(o, 'D1', 'D2')); s2 = show('D2 duplicate_of D3', dup(o, 'D2', 'D3')); s3 = show('D3 duplicate_of D1 (closes the cycle)', dup(o, 'D3', 'D1'))
    run(o, 'card_preparation'); live = [k for k in ('D1', 'D2', 'D3') if lines_of(gov(o, CARD + ':' + k)) is not None]
    print('    charges that still have a proposed entry:', live, '|', {k: brief(gov(o, CARD + ':' + k))['blockers'] for k in ('D1', 'D2', 'D3')})
    three = s3[0] == 'refused' and len(live) >= 1
    # revocation
    o, rows = duplicate_pair(); r = dup(o, 'D2', 'D1'); run(o, 'card_preparation')
    o.revoke_disposition(DISP, r[1], 'probe revocation'); run(o, 'card_preparation'); y1, y2 = gov(o, CARD + ':D1'), gov(o, CARD + ':D2')
    print('    after revocation -> D1:', brief(y1), '| D2:', brief(y2))
    revoked = 'POSSIBLE_DUPLICATE' in y1['blockers'] and 'POSSIBLE_DUPLICATE' in y2['blockers'] and lines_of(y2) is not None
    return 'OK' if two and three and revoked else 'WEAK'


def main():
    wanted = set(sys.argv[2:])
    import platform
    import sqlite3
    print('Fable RA acceptance probes | project root:', ROOT.name, '| Python', platform.python_version(), '| SQLite', sqlite3.sqlite_version)
    print('All data fictional; temporary databases only; service operations only.\n')
    results = []
    for pid, ticket, title, fn in PROBES:
        if wanted and pid not in wanted:
            continue
        print('[%s] (%s) %s' % (pid, ticket, title))
        try:
            verdict = fn()
        except Exception:
            traceback.print_exc(limit=6, file=sys.stdout)
            verdict = 'ERROR'
        print('    -> %s\n' % verdict)
        results.append((pid, ticket, verdict, title))
    print('=' * 100)
    for pid, ticket, verdict, title in results:
        print('%-5s %-12s %-6s %s' % (pid, ticket, verdict, title))
    counts = {}
    for r in results:
        counts[r[2]] = counts.get(r[2], 0) + 1
    failing = [r[0] for r in results if r[2] in ('WEAK', 'ERROR')]
    print('\nVerdict counts:', dict(sorted(counts.items())))
    print('RA acceptance gate:', 'PASS' if not failing else 'FAIL ' + ', '.join(failing))
    TMP.cleanup()
    sys.exit(1 if failing else 0)


if __name__ == '__main__':
    main()
