# Setup-only compatibility copy for RV-11/RV-12/RV-15; original input is unchanged.
# See docs/reverification/probe-adaptations.md and reverification-probe-adaptations.patch.
"""Fable independent re-verification probes: C-01 to C-06 and Batch 2 (T-09 to T-19).

Usage (from anywhere):
    python3 fable_reverification_probes.py <project-root> [PROBE_ID ...]

What this does
  * Imports the application from <project-root> and drives it through its public service
    operations only. There are no SQL writes and no edits to application files.
  * Every database is a temporary SQLite file holding fictional data. Nothing is posted,
    sent, paid, connected or deployed, and no model or network service is called.
  * Authority is set up explicitly inside each probe: a profile is proposed by one human,
    approved by a different granted human, and every grant is listed in ROLES below. The
    delivered helpers prepare_profile / grant_fixture_authority / create_fixture_mandate are
    not used, so nothing is approved or granted implicitly.
  * Each negative check is paired with a positive control, so that a refusal is known to
    come from the control under test and not from a missing grant or an unrelated blocker.

Verdicts
  OK     the control held
  WEAK   a confirmed control gap (counts against the gate; exit status 1)
  NOTE   a limitation or design observation that needs a decision; does not fail the gate
  ERROR  the probe could not run as written (counts against the gate)
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

TMP = tempfile.TemporaryDirectory(prefix='fable-reverify-')
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


# ---------------------------------------------------------------------------------------
# Part 1. Corrective tickets carried into the current API (original N01 to N07 scenarios)
# ---------------------------------------------------------------------------------------

@probe('RN01', 'C-02', 'every decision type is refused under lock, and accepted again after an authorised reopen')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00'), rc('A2', '2026-11-04', '60.00'),
            tx('A3', '2026-11-05', '70.00'), rc('A3', '2026-11-05', '70.00')]
    os_.intake(PREP, packet('base', rows + [stmt(rows)])); run(os_, 'card_preparation')
    a1, a2, a3 = (gov(os_, CARD + ':' + k) for k in ('A1', 'A2', 'A3'))
    setup = [review(os_, REV, a1, 'approve'), review(os_, REV, a2, 'approve'), review(os_, REV2, a2, 'reject')]
    print('    setup (A1 approved, A2 disputed, A3 pending):', [s[0] for s in setup], [brief(gov(os_, CARD + ':' + k))['status'] for k in ('A1', 'A2', 'A3')])
    lock = show('lock without acknowledgement while A2 disputed / A3 unreviewed', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock'))
    lock2 = show('lock with acknowledgement', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock', 'A2 disputed and A3 unreviewed are carried; fictional'))
    under = {'revoke A1': review(os_, REV2, a1, 'revoke'), 'reject A1': review(os_, REV2, a1, 'reject'), 'approve A3': review(os_, REV, a3, 'approve'),
             'reject A3': review(os_, REV, a3, 'reject'), 'resolve_approve A2': review(os_, REV3, a2, 'resolve_approve'), 'resolve_reject A2': review(os_, REV3, a2, 'resolve_reject')}
    for k, v in under.items():
        show('under lock, ' + k, v)
    statuses = [brief(gov(os_, CARD + ':' + k))['status'] for k in ('A1', 'A2', 'A3')]
    print('    statuses under lock:', statuses)
    disp = show('under lock, disposition attempt', attempt(os_.disposition, DISP, 'card_preparation', '2026-11', CARD + ':A3', 'MISSING_RECEIPT', 'refer_external', {}, [], 'x'))
    fin = show('under lock, finalize attempt', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'x', 'x'))
    reopen_wrong = show('reopen by a reviewer without the lock grant', attempt(os_.reopen_period, REV, '2026-11', 'probe'))
    reopen = show('reopen by the granted period administrator', attempt(os_.reopen_period, PADMIN, '2026-11', 'probe reopen'))
    after = {'approve A3': review(os_, REV, gov(os_, CARD + ':A3'), 'approve'), 'resolve_approve A2': review(os_, REV3, gov(os_, CARD + ':A2'), 'resolve_approve'), 'revoke A1': review(os_, REV2, gov(os_, CARD + ':A1'), 'revoke')}
    for k, v in after.items():
        show('after reopen, ' + k, v)
    history = [h['event'] for h in os_.export(PREP)['audit_history'] if h['event'].startswith('accounting_period_')]
    print('    period audit events:', history)
    ok = (lock[0] == 'refused' and lock2[0] == 'ok' and all(v[0] == 'refused' and v[1] == 409 and v[2] == 'PERIOD_LOCKED' for v in under.values())
          and statuses == ['approve', 'disputed', 'pending'] and disp[0] == 'refused' and fin[0] == 'refused' and reopen_wrong[0] == 'refused'
          and reopen[0] == 'ok' and all(v[0] == 'ok' for v in after.values()) and 'accounting_period_open' in history)
    return 'OK' if ok else 'WEAK'


@probe('RN02', 'C-01', 'a source re-dated out of a locked period enters no other period until the origin is reopened')
def _():
    os_ = new_os(periods=(NOV, DEC))
    rows = clean_november(os_)
    run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1')
    print('    November A1 approve:', review(os_, REV, a1, 'approve')[0], '| A2 approve:', review(os_, REV, gov(os_, CARD + ':A2'), 'approve')[0])
    show('lock November', attempt(os_.lock_period, PADMIN, '2026-11', 'probe lock'))
    moved = [tx('A1', '2026-12-02', '40.00'), rc('A1', '2026-12-02', '40.00')]
    dec_rows = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP2, packet('move-1', moved + dec_rows + [stmt(dec_rows, DEC, opening='100.00')]))
    replay = os_.intake(PREP2, packet('move-1', moved + dec_rows + [stmt(dec_rows, DEC, opening='100.00')]))
    run(os_, 'card_preparation', '2026-12', PREP2)
    st = os_.state(PREP)
    exc = [(e['source_key'], e['period_id'], e['reason']) for e in st['source_exceptions']]
    dec_item = gov(os_, CARD + ':A1', '2026-12')
    nov_item = gov(os_, CARD + ':A1', '2026-11')
    print('    replay result:', replay, '| source exceptions:', exc)
    print('    while November is locked -> December A1:', brief(dec_item), '| November A1:', brief(nov_item))
    moves = [(m['from_period_id'], m['to_period_id'], m['blocked'], m['had_approval']) for m in os_.export(PREP)['source_move_history']]
    print('    move history (from, to, blocked, had_approval):', moves)
    # recurring run for December while the origin is still locked
    mid = os_.create_mandate(PREP2, ['card_preparation'], '2026-12-06T00:00:00+00:00', '2026-12-09T00:00:00+00:00', 86400, 2, {'kind': 'fixed', 'period_id': '2026-12'}, {'none':'Explicit fixed-evidence baseline for the original '+'RN02'+' scenario; freshness rejection is tested in RT10b'})
    os_.approve_mandate(CTRL, mid, 'probe standing authority'); os_.tick(PREP2, '2026-12-06T12:00:00+00:00'); os_.drain(WORKER, now='2026-12-06T12:00:00+00:00')
    dec_after_tick = gov(os_, CARD + ':A1', '2026-12')
    print('    after a recurring December run -> December A1:', brief(dec_after_tick))
    held_while_locked = dec_item is None and dec_after_tick is None and nov_item['review_status'] == 'approve' and any(e[2] == 'SOURCE_MOVED_FROM_LOCKED_PERIOD' for e in exc)
    os_.reopen_period(PADMIN, '2026-11', 'probe reopen')
    run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
    nov_after, dec_after = gov(os_, CARD + ':A1', '2026-11'), gov(os_, CARD + ':A1', '2026-12')
    current = [(a['period_id'], a['id'], a['review_status']) for a in arts(os_, CARD + ':A1') if a['governing'] and a['current']]
    old = [a for a in arts(os_, CARD + ':A1', '2026-11') if a['id'] == a1['id']][0]
    print('    after reopen -> November governing A1:', brief(nov_after), '| old approved artifact status:', old['review_status'], '| December A1:', brief(dec_after))
    print('    current governing A1 artifacts across periods:', current)
    ok = held_while_locked and len(current) <= 1 and old['review_status'] == 'stale' and dec_after is not None
    follows = dec_after is not None and 'MISSING_RECEIPT' not in dec_after['blockers']
    print('    supporting receipt followed the transaction to December:', follows)
    return 'OK' if ok and follows else 'WEAK'


@probe('RN02b', 'C-01', 'a locked, approved item cannot be re-entered in another period through supersession under a new key')
def _():
    os_ = new_os(periods=(NOV, DEC))
    clean_november(os_); run(os_, 'card_preparation')
    print('    November A1 approve:', review(os_, REV, gov(os_, CARD + ':A1'), 'approve')[0], '| A2:', review(os_, REV, gov(os_, CARD + ':A2'), 'approve')[0])
    os_.lock_period(PADMIN, '2026-11', 'probe lock')
    new = tx('A1X', '2026-12-02', '40.00'); new['supersedes'] = CARD + ':A1'      # envelope-level supersession, same economic charge
    dec_rows = [new, rc('A1X', '2026-12-02', '40.00')]
    res = show('intake of superseding source dated December', attempt(os_.intake, PREP2, packet('supersede-1', dec_rows + [stmt(dec_rows, DEC, opening='100.00')])))
    run(os_, 'card_preparation', '2026-12', PREP2)
    dec = gov(os_, CARD + ':A1X', '2026-12'); nov = gov(os_, CARD + ':A1', '2026-11')
    st = os_.state(PREP)
    print('    December A1X:', brief(dec), '| November A1:', brief(nov))
    print('    source exceptions:', [(e['source_key'], e['reason']) for e in st['source_exceptions']], '| events:', [(e['code'], e['item_key']) for e in st['accounting_events']])
    approve = show('independent approval of December A1X', review(os_, REV2, dec, 'approve')) if dec else ('refused', 0, 'no item')
    both = approve[0] == 'ok' and nov is not None and nov['review_status'] == 'approve'
    print('    same charge approved in locked November and in December:', both)
    return 'WEAK' if both else 'OK'


@probe('RN03', 'C-03', 'identical work by another enqueuer or mandate issuer keeps the governing artifact and its rejection')
def _():
    os_ = new_os()
    clean_november(os_); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); b = gov(os_, CARD + ':A2')
    print('    reject A1:', review(os_, REV, a, 'reject')[0], '| approve A2:', review(os_, REV, b, 'approve')[0])
    run(os_, 'card_preparation', who=PREP2)                       # colleague re-enqueues identical inputs
    mid = os_.create_mandate(PREP2, ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-18T00:00:00+00:00', 86400, 2, {'kind': 'fixed', 'period_id': '2026-11'}, {'none':'Explicit fixed-evidence baseline for the original '+'RN03'+' scenario; freshness rejection is tested in RT10b'})
    os_.approve_mandate(CTRL, mid, 'probe standing authority'); os_.tick(PREP2, '2026-11-15T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T12:00:00+00:00')
    a_after = gov(os_, CARD + ':A1'); b_after = gov(os_, CARD + ':A2')
    count = len(arts(os_, CARD + ':A1'))
    print('    A1 artifacts:', count, '| governing id unchanged:', a_after['id'] == a['id'], '| hash unchanged:', a_after['hash'] == a['hash'], '| status:', a_after['review_status'], '| runs linked:', a_after['run_ids'])
    print('    A2 status:', b_after['review_status'], '| contributors of A1:', a_after['contributors'])
    dual = human(PREP2.id, 'reviewer'); os_.grant_authority(ADMIN, dual.id, ['review'], 'probe: same person, reviewer role')
    late = show('colleague who became a contributor tries to decide A1', review(os_, dual, a_after, 'approve'))
    ok = (count == 1 and a_after['id'] == a['id'] and a_after['hash'] == a['hash'] and a_after['review_status'] == 'reject' and b_after['review_status'] == 'approve'
          and PREP2.id in a_after['contributors'] and late[0] == 'refused' and late[1] == 403 and 'contributors' not in a_after['payload'])
    return 'OK' if ok else 'WEAK'


@probe('RN04', 'C-04', 'a supplier of any version of an item input stays barred; a supplier of another item evidence does not')
def _():
    os_ = new_os()
    author = human(REV.id, 'preparer')                                # the future reviewer supplies the first version
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00'), rc('A2', '2026-11-04', '60.00')]
    os_.intake(author, packet('v1', [rows[0]]))
    cosmetic = copy.deepcopy(rows[0]); cosmetic['data']['description'] = 'Acme  Paper  Demo'          # normalises to the same alias
    other_rc = human(REV3.id, 'preparer')
    os_.intake(PREP, packet('v2', [cosmetic, rows[1], rows[2], stmt(rows)]))
    os_.intake(other_rc, packet('v3', [rows[3]]))                    # REV3 supplies only the receipt of A2
    run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1')
    print('    A1:', brief(a1), '| contributors:', a1['contributors'])
    first = show('supplier of the superseded A1 version approves A1', review(os_, REV, a1, 'approve'))
    other = show('supplier of the A2 receipt approves A1 (should be allowed)', review(os_, REV3, a1, 'approve'))
    a2 = gov(os_, CARD + ':A2')
    own = show('supplier of the A2 receipt approves A2 (should be refused)', review(os_, REV3, a2, 'approve'))
    ok = first[0] == 'refused' and first[1] == 403 and other[0] == 'ok' and own[0] == 'refused' and own[1] == 403
    return 'OK' if ok else 'WEAK'


@probe('RN05', 'C-04', 'the author of the chart and policy stays barred after a colleague re-registers the profile')
def _():
    author = human(REV.id, 'preparer')
    os_ = new_os(proposer=author)                                    # REV (as preparer) proposes v1; CTRL approves
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'fictional-demo-batch2-v2'; p2['name'] = PROFILE['name'] + ' (re-registered)'
    sid2 = os_.onboard(PREP, p2, effective_from='2026-11-01')
    show('colleague re-registration approved by a second policy approver', attempt(os_.approve_profile_version, CTRL2, sid2, 'probe approval of cosmetic v2'))
    clean_november(os_); run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1')
    print('    A1:', brief(a1), '| profile ref:', a1['payload']['data']['profile'])
    print('    contributors:', a1['contributors'])
    first = show('author of profile v1 approves A1', review(os_, REV, a1, 'approve'))
    approver = human(CTRL.id, 'reviewer'); os_.grant_authority(ADMIN, CTRL.id, ['review'], 'probe: policy approver also given review')
    second = show('approver of profile v1 approves A1', review(os_, approver, a1, 'approve'))
    control = show('uninvolved reviewer approves A1 (positive control)', review(os_, REV2, a1, 'approve'))
    return 'OK' if first[0] == 'refused' and first[1] == 403 and control[0] == 'ok' else 'WEAK'


@probe('RN05b', 'C-04/T-09', 'the author of a vendor mapping stays barred after a colleague re-proposes the rule with a cosmetic change')
def _():
    p = copy.deepcopy(PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_acme']
    os_ = new_os(profile=p)
    author = human(REV.id, 'preparer')
    v1 = {'id': 'demo_acme', 'name': 'Acme Paper Demo', 'aliases': ['ACME PAPER DEMO'], 'category': 'DEMO_OFFICE_SUPPLIES'}
    r1 = os_.propose_rule(author, 'vendor_mapping', 'demo_acme', v1, '2026-11-01')
    os_.approve_rule(CTRL, r1, 'probe approval of mapping v1')
    v2 = dict(v1, name='Acme Paper Demo.')                           # same alias and category; cosmetic name change
    r2 = os_.propose_rule(PREP, 'vendor_mapping', 'demo_acme', v2, '2026-11-01', supersedes=r1)
    os_.approve_rule(CTRL2, r2, 'probe approval of cosmetic mapping v2')
    clean_november(os_); run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1')
    print('    A1:', brief(a1), '| vendor:', a1['payload']['data']['vendor'], '| applied rules:', a1['payload']['applied_rules'])
    print('    contributors:', a1['contributors'])
    first = show('author of mapping v1 (alias and category unchanged in v2) approves A1', review(os_, REV, a1, 'approve'))
    return 'OK' if first[0] == 'refused' else 'WEAK'


@probe('RN06', 'C-05', 'combining marks survive normalisation; unknown and colliding aliases are held; empty aliases refused')
def _():
    pairs = [('กิน', 'กัน'), ('कि', 'कु'), ('שָׁלוֹם', 'שֵׁלֶם'), ('Café', 'Cafe'), ('ｆｕｌｌ　ｗｉｄｔｈ', 'full width')]
    out = [(a, b, normalize(a) == normalize(b)) for a, b in pairs]
    print('    normalised-equal flags (last pair is the only one that should be equal):', [o[2] for o in out])
    p = copy.deepcopy(PROFILE)
    p['vendors'].append({'id': 'demo_thai', 'name': 'Thai vendor (fictional)', 'aliases': ['กิน'], 'category': 'DEMO_OFFICE_SUPPLIES'})
    p['vendors'].append({'id': 'demo_collide', 'name': 'Colliding vendor (fictional)', 'aliases': ['Metro-Repair DEMO'], 'category': 'DEMO_OFFICE_SUPPLIES'})
    os_ = new_os(profile=p)
    rows = [tx('U1', '2026-11-03', '40.00', desc='กัน'), rc('U1', '2026-11-03', '40.00', vendor='กัน'),
            tx('U2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('U2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO'),
            tx('U3', '2026-11-05', '10.00', desc='กิน'), rc('U3', '2026-11-05', '10.00', vendor='กิน')]
    os_.intake(PREP, packet('u', rows + [stmt(rows)])); run(os_, 'card_preparation')
    u1, u2, u3 = (gov(os_, CARD + ':' + k) for k in ('U1', 'U2', 'U3'))
    print('    different mark:', brief(u1)); print('    alias collision across two vendors:', brief(u2)); print('    exact mark (positive control):', brief(u3))
    bad = copy.deepcopy(PROFILE); bad['version'] = 'bad-alias'; bad['vendors'][0]['aliases'] = ['---']
    e1 = show('profile with an alias that normalises to nothing', attempt(os_.onboard, PREP, bad))
    e2 = show('rule with an alias that normalises to nothing', attempt(os_.propose_rule, PREP, 'vendor_mapping', 'x', {'id': 'x', 'name': 'x', 'aliases': ['***'], 'category': 'DEMO_REPAIRS'}, '2026-11-01'))
    ok = ([o[2] for o in out] == [False, False, False, False, True] and 'UNKNOWN_VENDOR' in u1['blockers'] and not u1['eligible']
          and 'AMBIGUOUS_VENDOR' in u2['blockers'] and u3['eligible'] and e1[0] == 'refused' and e2[0] == 'refused')
    return 'OK' if ok else 'WEAK'


@probe('RN07', 'C-06', 'actor kind is mandatory; a service identity cannot use any human authority whatever its name, role or grants')
def _():
    try:
        Actor('no-kind', 'reviewer', ORG, CLIENT); missing = 'constructed'
    except TypeError:
        missing = 'refused'
    bad_kind = attempt(Actor, 'x', 'reviewer', ORG, CLIENT, kind='robot')
    print('    actor without kind:', missing, '| invalid kind:', bad_kind[0])
    os_ = new_os(approve=False, periods=())
    svc = Actor('human-controller-jane', 'reviewer', ORG, CLIENT, kind='service')
    svc_admin = Actor('human-admin', 'administrator', ORG, CLIENT, kind='service')
    os_.grant_authority(ADMIN, svc.id, ['review', 'approve_rule', 'approve_profile', 'approve_mandate', 'disposition', 'finalize', 'lock'], 'probe: grants issued to a service identity')
    pid = os_.probe_profile_id
    r = {}
    r['service grants authority'] = attempt(os_.grant_authority, svc_admin, 'someone', ['review'], 'x')
    r['service approves profile'] = attempt(os_.approve_profile_version, svc, pid, 'x')
    os_.approve_profile_version(CTRL, pid, 'explicit approval')
    r['service opens period'] = attempt(os_.open_period, svc, *NOV, 'x')
    os_.open_period(PADMIN, *NOV, 'probe')
    clean_november(os_, extra=[tx('A3', '2026-11-06', '5.00', desc='NOBODY KNOWN')]); run(os_, 'card_preparation')
    a1, a3 = gov(os_, CARD + ':A1'), gov(os_, CARD + ':A3')
    r['service approves item'] = review(os_, svc, a1, 'approve')
    r['service rejects item'] = review(os_, svc, a1, 'reject')
    r['service dispositions'] = attempt(os_.disposition, svc, 'card_preparation', '2026-11', CARD + ':A3', 'MISSING_RECEIPT', 'refer_external', {}, a3['payload']['data']['evidence'], 'x')
    rid = os_.propose_rule(PREP, 'receipt_matching', 'default', {'date_window_days': 1, 'amount_tolerance': None, 'multiple_receipts': None, 'vendor_method': None, 'statement_substitution': None}, '2026-11-01')
    r['service approves rule'] = attempt(os_.approve_rule, svc, rid, 'x')
    mid = os_.create_mandate(PREP, ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-18T00:00:00+00:00', 86400, 1, {'kind': 'fixed', 'period_id': '2026-11'}, {'none':'Explicit fixed-evidence baseline for the original '+'RN07'+' scenario; freshness rejection is tested in RT10b'})
    r['service approves mandate'] = attempt(os_.approve_mandate, svc, mid, 'x')
    r['service creates mandate'] = attempt(os_.create_mandate, Actor('svc-prep', 'preparer', ORG, CLIENT, kind='service'), ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-18T00:00:00+00:00', 86400, 1, {'kind': 'fixed', 'period_id': '2026-11'}, {})
    r['service finalizes'] = attempt(os_.finalize_package, svc, '2026-11', 'card_preparation', 'x', 'x')
    r['service locks'] = attempt(os_.lock_period, svc, '2026-11', 'x', 'x')
    for k, v in r.items():
        show(k, v)
    control = show('granted human approves item (positive control)', review(os_, REV, a1, 'approve'))
    ok = missing == 'refused' and bad_kind[0] == 'refused' and all(v[0] == 'refused' and v[1] == 403 for v in r.values()) and control[0] == 'ok'
    return 'OK' if ok else 'WEAK'


# ---------------------------------------------------------------------------------------
# Part 2. Batch 2 tickets, in dependency order: T-09, T-11, T-12, T-10, T-13
# ---------------------------------------------------------------------------------------

@probe('RT09a', 'T-09', 'a proposed profile is inert; the proposer, an ungranted human and a service cannot approve it')
def _():
    os_ = new_os(approve=False)
    clean_november(os_)
    inert = show('enqueue under a proposed profile', attempt(os_.enqueue, PREP, 'card_preparation', '2026-11'))
    os_.grant_authority(ADMIN, PREP.id, ['approve_profile'], 'probe: proposer holds the grant, to isolate the proposer check')
    own = show('proposer approves own profile', attempt(os_.approve_profile_version, human(PREP.id, 'reviewer'), os_.probe_profile_id, 'x'))
    nogrant = show('human without the approve_profile grant', attempt(os_.approve_profile_version, REV, os_.probe_profile_id, 'x'))
    good = show('independent granted approver', attempt(os_.approve_profile_version, CTRL, os_.probe_profile_id, 'explicit approval'))
    run(os_, 'card_preparation'); a1 = gov(os_, CARD + ':A1')
    print('    after approval A1:', brief(a1))
    ok = inert[0] == 'refused' and inert[2] == 'POLICY_NOT_APPROVED' and own[0] == 'refused' and nogrant[0] == 'refused' and good[0] == 'ok' and a1 and a1['eligible']
    return 'OK' if ok else 'WEAK'


@probe('RT09b', 'T-09', 'rules: proposed is inert, effective dates and supersession are applied per item date, earlier approvals survive')
def _():
    p = copy.deepcopy(PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_metro']
    os_ = new_os(profile=p, periods=(NOV, DEC))
    nov = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('M1', '2026-11-20', '60.00', desc='METRO REPAIR DEMO'), rc('M1', '2026-11-20', '60.00', vendor='METRO REPAIR DEMO')]
    dec = [tx('M2', '2026-12-05', '30.00', desc='METRO REPAIR DEMO'), rc('M2', '2026-12-05', '30.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('nov', nov + [stmt(nov)])); os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='100.00')]))
    metro = {'id': 'demo_metro', 'name': 'Metro Repair Demo', 'aliases': ['METRO REPAIR DEMO'], 'category': 'DEMO_REPAIRS'}
    rid = os_.propose_rule(PREP, 'vendor_mapping', 'demo_metro', metro, '2026-12-01')
    run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12')
    s1 = (brief(gov(os_, CARD + ':M1', '2026-11')), brief(gov(os_, CARD + ':M2', '2026-12')))
    print('    rule proposed only -> M1 (Nov):', s1[0]['blockers'], '| M2 (Dec):', s1[1]['blockers'])
    a1 = gov(os_, CARD + ':A1'); print('    approve A1 (Nov):', review(os_, REV, a1, 'approve')[0])
    os_.grant_authority(ADMIN, PREP.id, ['approve_rule'], 'probe: proposer holds the grant, to isolate the proposer check')
    own = show('rule proposer approves own rule', attempt(os_.approve_rule, human(PREP.id, 'reviewer'), rid, 'x'))
    os_.approve_rule(CTRL, rid, 'probe approval, effective 2026-12-01')
    a1_after_rule = gov(os_, CARD + ':A1')
    run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12')
    m1, m2 = gov(os_, CARD + ':M1', '2026-11'), gov(os_, CARD + ':M2', '2026-12')
    print('    rule approved, effective December -> A1 status:', a1_after_rule['review_status'], '| M1 (Nov):', m1['blockers'], '| M2 (Dec):', brief(m2), m2['payload']['data']['proposed_category'])
    cid = os_.propose_rule(PREP, 'close_checklist', 'close', [{'type': 'workflow_outcome', 'workflow': 'card_preparation'}], '2026-11-01'); os_.approve_rule(CTRL, cid, 'probe: unrelated close rule')
    a1_after_close = gov(os_, CARD + ':A1')
    print('    after an unrelated close-checklist rule -> A1 status:', a1_after_close['review_status'], '| same artifact:', a1_after_close['id'] == a1['id'])
    v2 = dict(metro, category='DEMO_OFFICE_SUPPLIES')
    rid2 = os_.propose_rule(PREP, 'vendor_mapping', 'demo_metro', v2, '2027-01-01', supersedes=rid); os_.approve_rule(CTRL, rid2, 'probe: superseding rule effective 2027')
    run(os_, 'card_preparation', '2026-12'); m2b = gov(os_, CARD + ':M2', '2026-12')
    print('    after a superseding rule effective 2027-01-01 -> M2 category:', m2b['payload']['data']['proposed_category'], '| applied rules:', m2b['payload']['applied_rules'])
    pid = os_.propose_rule(PREP, 'review_policy', 'review', {'receipt_required': True, 'review': 'independent_human', 'model_review_required': True}, '2026-11-15'); os_.approve_rule(CTRL, pid, 'probe: review policy from 15 November')
    run(os_, 'card_preparation', '2026-11'); a1c, m1c = gov(os_, CARD + ':A1'), gov(os_, CARD + ':M1')
    print('    review policy effective 15 November -> A1 (3 Nov):', a1c['blockers'], a1c['review_status'], '| M1 (20 Nov):', m1c['blockers'])
    ok = ('UNKNOWN_VENDOR' in s1[0]['blockers'] and 'UNKNOWN_VENDOR' in s1[1]['blockers'] and own[0] == 'refused' and a1_after_rule['review_status'] == 'approve'
          and 'UNKNOWN_VENDOR' in m1['blockers'] and m2['eligible'] and m2['payload']['data']['proposed_category'] == 'DEMO_REPAIRS'
          and a1_after_close['review_status'] == 'approve' and m2b['payload']['data']['proposed_category'] == 'DEMO_REPAIRS'
          and 'MODEL_REVIEW_UNAVAILABLE' not in a1c['blockers'] and 'MODEL_REVIEW_UNAVAILABLE' in m1c['blockers'])
    if ok and a1c['review_status'] != 'approve':
        print('    observation: the approval of A1 (dated before the new policy) did not survive a same-period rule that applies only to later items')
    return 'OK' if ok else 'WEAK'


@probe('RT09c', 'T-09', 'a vendor removed from the approved profile no longer produces a clean match')
def _():
    os_ = new_os()
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'fictional-demo-batch2-v2'; p2['vendors'] = [v for v in p2['vendors'] if v['id'] != 'demo_metro']
    sid2 = os_.onboard(PREP, p2, effective_from='2026-11-01'); os_.approve_profile_version(CTRL, sid2, 'probe: profile v2 retires the Metro mapping')
    clean_november(os_); run(os_, 'card_preparation')
    a2 = gov(os_, CARD + ':A2')
    print('    approved profile v2 vendors:', [v['id'] for v in os_.state(PREP)['profile']['vendors']])
    print('    Metro item under v2:', brief(a2), '| vendor:', a2['payload']['data']['vendor'], '| category:', a2['payload']['data']['proposed_category'])
    return 'WEAK' if a2['eligible'] and a2['payload']['data']['vendor'] else 'OK'


@probe('RT09d', 'T-09', 'normalised alias form is visible to the rule approver; punctuation-only collisions are held')
def _():
    os_ = new_os()
    rid = os_.propose_rule(PREP, 'vendor_mapping', 'demo_other', {'id': 'demo_other', 'name': 'Other vendor (fictional)', 'aliases': ['ACME-PAPER/DEMO'], 'category': 'DEMO_REPAIRS'}, '2026-11-01')
    st = os_.state(CTRL)
    rule = [r for r in st['rules'] if r['id'] == rid][0]
    in_rule = 'acme paper demo' in json.dumps(rule).lower() and 'normal' in json.dumps(rule).lower()
    events = [json.loads(a['payload']) for a in st['audit'] if a['event'] == 'rule_proposed' and json.loads(a['payload']).get('rule_id') == rid]
    print('    rule record keys:', sorted(rule)); print('    normalised form on the rule record:', in_rule, '| in the rule_proposed audit event:', events[0].get('normalized_aliases') if events else None)
    os_.approve_rule(CTRL, rid, 'probe approval'); clean_november(os_); run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1'); print('    ACME item after approving the colliding alias:', brief(a1))
    held = 'AMBIGUOUS_VENDOR' in a1['blockers']
    if not held:
        return 'WEAK'
    return 'OK' if in_rule else 'NOTE'


@probe('RT11', 'T-11', 'client_sample with missing facts yields no eligible item; demo waivers are explicit in artifact and export')
def _():
    p = copy.deepcopy(PROFILE); p['profile_class'] = 'client_sample'
    os_ = new_os(profile=p)
    clean_november(os_, extra=[journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['sup1']), doc('sup1', 'journal_support', journal_keys=['J1'])])
    run(os_, 'card_preparation'); run(os_, 'journal_preparation')
    items = [gov(os_, k) for k in (CARD + ':A1', CARD + ':A2', 'J1')]
    for a in items:
        print('    client_sample', a['item_key'], brief(a))
    os2 = new_os()
    clean_november(os2, extra=[journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['sup1']), doc('sup1', 'journal_support', journal_keys=['J1'])])
    run(os2, 'card_preparation'); run(os2, 'journal_preparation')
    demo = [gov(os2, k) for k in (CARD + ':A1', 'J1')]
    waivers = [sorted(a['payload']['fact_waivers']) for a in demo]
    exported = [a for a in os2.export(PREP)['artifacts'] if a['id'] == demo[0]['id']][0]['payload']['fact_waivers']
    print('    synthetic_demo eligible:', [bool(a['eligible']) for a in demo], '| waivers on artifacts:', waivers, '| in export:', bool(exported))
    ok = (all(not a['eligible'] and any(b.startswith('CLIENT_FACT_MISSING:accounting_basis') for b in a['blockers']) for a in items)
          and all(a['eligible'] for a in demo) and all('accounting_basis' in w for w in waivers) and exported)
    return 'OK' if ok else 'WEAK'


@probe('RT12a', 'T-12', 'older, conflicting, mixed-order and unordered deliveries never replace an accepted ordered head')
def _():
    os_ = new_os()
    base = [tx('A1', '2026-11-03', '50.00', as_of=5), rc('A1', '2026-11-03', '50.00')]
    os_.intake(PREP, packet('s5', base + [stmt(base)]))
    tries = [('older sequence 3', tx('A1', '2026-11-03', '40.00', as_of=3)), ('same sequence 5, different amount', tx('A1', '2026-11-03', '45.00', as_of=5)),
             ('timestamp ordering after sequence', tx('A1', '2026-11-03', '41.00', as_of='2026-11-10T00:00:00+00:00')), ('no ordering value', tx('A1', '2026-11-03', '42.00'))]
    for i, (label, row) in enumerate(tries):
        os_.intake(PREP, packet('late-%d' % i, [row]))
    replay = os_.intake(PREP, packet('late-0', [tries[0][1]]))
    run(os_, 'card_preparation'); a1 = gov(os_, CARD + ':A1')
    retained = [a for a in os_.export(PREP)['audit_history'] if a['event'] == 'older_or_conflicting_source_retained']
    print('    current amount:', a1['payload']['data']['transaction']['amount'], '| eligible:', bool(a1['eligible']), '| retained-as-history events:', len(retained), '| replay:', replay['replay'])
    newer = [tx('A1', '2026-11-03', '55.00', as_of=7), rc('A1', '2026-11-03', '55.00')]
    os_.intake(PREP, packet('s7', newer + [stmt(newer)])); run(os_, 'card_preparation'); accept_revised_evidence(os_,CARD+':A1'); run(os_,'card_preparation'); a1b = gov(os_, CARD + ':A1')
    print('    after newer sequence 7 (positive control):', a1b['payload']['data']['transaction']['amount'], brief(a1b))
    ok = a1['payload']['data']['transaction']['amount'] == '50.00' and a1['eligible'] and len(retained) == 4 and replay['replay'] and a1b['payload']['data']['transaction']['amount'] == '55.00' and a1b['eligible']
    return 'OK' if ok else 'WEAK'


@probe('RT12b', 'T-12/T-18', 'unrelated later intake leaves a locked, finalized period untouched (no new quarantine, no change event)')
def _():
    os_ = new_os(periods=(NOV, DEC))
    clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    show('finalize November card package', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover'))
    os_.lock_period(PADMIN, '2026-11', 'probe lock')
    before = os_.state(PREP)
    dec = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    os_.intake(PREP2, packet('dec', dec + [stmt(dec, DEC, opening='100.00')]))
    after = os_.state(PREP)
    exc = [(e['source_key'], e['period_id'], e['reason']) for e in after['source_exceptions']]
    events = [(e['code'], e['period_id'], e['item_key']) for e in after['accounting_events']]
    print('    source exceptions before:', len(before['source_exceptions']), '| after December-only intake:', exc)
    print('    accounting events after December-only intake:', events)
    print('    November statuses:', [brief(gov(os_, CARD + ':' + k))['status'] for k in ('A1', 'A2')], '| package hash unchanged:', [p['hash'] for p in before['packages']] == [p['hash'] for p in after['packages']])
    return 'WEAK' if exc or events else 'OK'


@probe('RT12c', 'T-12', 'evidence received before its period opens is adopted; a receipt follows its charge across a month boundary in either arrival order')
def _():
    os_ = new_os(periods=())
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00')]
    os_.intake(PREP, packet('early', rows + [stmt(rows), doc('tb', 'trial_balance', period_id=None), doc('tb2', 'card_statement')], period_id='2026-11'))
    early = [(e['source_key'], e['reason']) for e in os_.state(PREP)['source_exceptions']]
    os_.open_period(PADMIN, *NOV, 'probe'); run(os_, 'card_preparation')
    left = [(e['source_key'], e['reason']) for e in os_.state(PREP)['source_exceptions']]
    a1 = gov(os_, CARD + ':A1')
    print('    before opening:', len(early), 'quarantined | after opening November:', left, '| A1:', brief(a1))
    results = []
    for order in ('receipt first', 'charge first'):
        o = new_os(periods=(NOV, DEC))
        charge = [tx('B1', '2026-12-01', '20.00')]; receipt = [rc('B1', '2026-11-30', '20.00')]
        first, second = (receipt, charge + [stmt(charge, DEC)]) if order == 'receipt first' else (charge + [stmt(charge, DEC)], receipt)
        o.intake(PREP, packet('one', first)); o.intake(PREP, packet('two', second)); run(o, 'card_preparation', '2026-12')
        b1 = gov(o, CARD + ':B1', '2026-12'); listed = [e['source_key'] for e in b1['payload']['data']['evidence']]
        print('    %s -> December B1 blockers:' % order, b1['blockers'], '| evidence listed:', listed)
        results.append('MISSING_RECEIPT' not in b1['blockers'] and 'receipt-B1' in listed and 'RECEIPT_DATE_POLICY_UNSET' in b1['blockers'])
    ok = len(early) == 5 and not left and a1['eligible'] and all(results)
    return 'OK' if ok else 'WEAK'


@probe('RT12d', 'T-12/T-18', 'a removed or superseded source leaves no open item behind and raises an event when it had been approved')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00', as_of=1), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', as_of=1), rc('A2', '2026-11-04', '60.00'),
            tx('P1', '2026-11-08', '10.00', status='pending', as_of=1)]
    os_.intake(PREP, packet('b1', rows + [stmt(rows)])); run(os_, 'card_preparation')
    print('    pending P1 before removal:', brief(gov(os_, CARD + ':P1')))
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    gone = copy.deepcopy(rows[4]); gone.update(as_of=2, tombstone=True, removal_reason='feed_removed')          # unchanged content
    os_.intake(PREP, packet('b2', [gone])); run(os_, 'card_preparation')
    p1 = gov(os_, CARD + ':P1'); a1 = gov(os_, CARD + ':A1')
    population = [s['source_key'] for s in os_.state(PREP)['sources']]
    print('    after tombstone -> P1 in current sources:', CARD + ':P1' in population, '| P1 governing artifact:', brief(p1), '| A1:', brief(a1)['status'])
    again = [review(os_, REV, gov(os_, CARD + ':' + k), 'approve')[0] for k in ('A1', 'A2')]
    fin = show('finalize the card package after every remaining item is approved (%s)' % again, attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover', 'P1 was removed by the feed'))
    dead_end = fin[0] == 'refused'
    # approved source later removed, and approved source superseded under a new key
    removed = copy.deepcopy(rows[2]); removed.update(as_of=3, tombstone=True, removal_reason='voided')
    os_.intake(PREP, packet('b3', [removed]))
    newkey = tx('A1N', '2026-11-03', '40.00', as_of=4); newkey['supersedes'] = CARD + ':A1'
    os_.intake(PREP, packet('b4', [newkey, rc('A1N', '2026-11-03', '40.00')]))
    events = [(e['code'], e['item_key']) for e in os_.state(PREP)['accounting_events']]
    print('    events after removing approved A2 and superseding approved A1:', events)
    removed_event = any(c == 'APPROVED_SOURCE_REMOVED' and k == CARD + ':A2' for c, k in events)
    superseded_event = any(k == CARD + ':A1' and c.startswith('APPROVED_SOURCE') for c, k in events)
    print('    removal event raised:', removed_event, '| supersession event raised:', superseded_event, '| finalization blocked by the removed pending row:', dead_end)
    return 'OK' if removed_event and superseded_event and not dead_end else 'WEAK'


@probe('RT10a', 'T-10', 'mandates: independent approval, fixed target period, fresh-evidence wait and wake-up, suspension on policy change')
def _():
    os_ = new_os(periods=(NOV, DEC))
    rows = clean_november(os_)
    args = (['card_preparation'], '2026-12-01T00:00:00+00:00', '2026-12-05T00:00:00+00:00', 86400, 3, {'kind': 'fixed', 'period_id': '2026-11'}, {'transaction': 'occurrence_start'})
    mid = os_.create_mandate(PREP, *args)
    os_.grant_authority(ADMIN, PREP.id, ['approve_mandate'], 'probe: issuer holds the grant, to isolate the issuer check')
    own = show('issuer approves own mandate', attempt(os_.approve_mandate, human(PREP.id, 'reviewer'), mid, 'x'))
    before = os_.tick(PREP, '2026-12-01T06:00:00+00:00')
    print('    tick while the mandate is only proposed -> runs:', before, '| occurrences:', len(os_.state(PREP)['occurrences']))
    os_.approve_mandate(CTRL, mid, 'probe standing authority')
    t1 = os_.tick(PREP, '2026-12-01T12:00:00+00:00')
    occ1 = [(o['status'], o['reason']) for o in os_.state(PREP)['occurrences']]
    print('    tick with no fresh evidence -> runs:', t1, '| occurrences:', occ1)
    fresh = [tx('A9', '2026-11-25', '12.00', as_of='2026-12-01T13:00:00+00:00'), rc('A9', '2026-11-25', '12.00')]
    os_.intake(PREP, packet('fresh', fresh + [stmt(rows + fresh)])); os_.drain(WORKER)
    st = os_.state(PREP)
    runs = [(r['id'], r['period_id'], r['status'], r['mandate_id']) for r in st['runs'] if r['mandate_id']]
    occ2 = [(o['status'], o['completed_run_id'] is not None) for o in st['occurrences']]
    print('    after fresh evidence arrives -> mandate runs (id, period, status, mandate):', runs, '| occurrences:', occ2)
    rid = os_.propose_rule(PREP2, 'vendor_mapping', 'demo_extra', {'id': 'demo_extra', 'name': 'Extra (fictional)', 'aliases': ['EXTRA VENDOR DEMO'], 'category': 'DEMO_REPAIRS'}, '2026-11-01')
    os_.approve_rule(CTRL, rid, 'probe: policy change after the mandate was approved')
    newer = [tx('A10', '2026-11-26', '13.00', as_of='2026-12-02T01:00:00+00:00'), rc('A10', '2026-11-26', '13.00')]
    os_.intake(PREP, packet('fresh2', newer + [stmt(rows + fresh + newer)]))
    t3 = os_.tick(PREP, '2026-12-02T12:00:00+00:00')
    st = os_.state(PREP); m = [x for x in st['mandates'] if x['id'] == mid][0]
    print('    tick after a bound policy change -> runs:', t3, '| mandate:', (m['status'], m['active'], m['reason']))
    ok = (own[0] == 'refused' and before == [] and t1 == [] and occ1 and occ1[0][0] == 'awaiting_evidence' and len(runs) == 1 and runs[0][1] == '2026-11'
          and runs[0][2] in ('awaiting_review', 'prepared_with_exceptions') and t3 == [] and m['status'] == 'needs_reconfirmation' and not m['active'])
    return 'OK' if ok else 'WEAK'


@probe('RT10b', 'T-10', 'a mandate must state what fresh evidence it needs before it can dispatch')
def _():
    os_ = new_os()
    clean_november(os_)
    made = show('create a mandate with an empty freshness predicate', attempt(os_.create_mandate, PREP, ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3, {'kind': 'fixed', 'period_id': '2026-11'}, {}))
    if made[0] == 'refused':
        return 'OK'
    os_.approve_mandate(CTRL, made[1], 'probe standing authority')
    for now in ('2026-11-15T12:00:00+00:00', '2026-11-16T12:00:00+00:00', '2026-11-17T12:00:00+00:00'):
        os_.tick(PREP, now); os_.drain(WORKER, now=now)
    runs = [(r['id'], r['status']) for r in os_.state(PREP)['runs'] if r['mandate_id']]
    print('    runs dispatched on unchanged evidence:', runs)
    return 'WEAK' if len(runs) >= 2 else 'OK'


@probe('RT13', 'T-13', 'statement control: identity swap, purchase/payment offset, opening break and foreign rows are caught or disclosed')
def _():
    os_ = new_os()
    claimed = [tx('S1', '2026-11-03', '40.00'), tx('S2', '2026-11-04', '60.00')]
    actual = [tx('S1', '2026-11-03', '40.00'), rc('S1', '2026-11-03', '40.00'), tx('S9', '2026-11-04', '60.00'), rc('S9', '2026-11-04', '60.00')]
    os_.intake(PREP, packet('swap', actual + [stmt(claimed)])); run(os_, 'card_preparation')
    swap = gov(os_, CARD + ':S9'); print('    same count and total, different line identity:', swap['blockers'])
    o2 = new_os()
    rows = [tx('B1', '2026-11-03', '130.00'), rc('B1', '2026-11-03', '130.00'), tx('B2', '2026-11-12', '-60.00', desc='CARD PAYMENT DEMO', activity='payment')]
    offset = stmt(rows, line_ids=False, totals={'purchase': '100.00', 'credit': '0.00', 'payment': '-30.00', 'fee': '0.00', 'interest': '0.00', 'transfer': '0.00', 'unknown': '0.00'})
    o2.intake(PREP, packet('offset', rows + [offset])); run(o2, 'card_preparation')
    off = gov(o2, CARD + ':B1'); print('    purchases and payments overstated by the same amount (net and count tie):', off['blockers'])
    o3 = new_os(periods=(('2026-10', '2026-10-01', '2026-10-31'), NOV))
    octr = [tx('O1', '2026-10-10', '500.00'), rc('O1', '2026-10-10', '500.00')]
    novr = [tx('C1', '2026-11-03', '40.00'), rc('C1', '2026-11-03', '40.00'), tx('C2', '2026-11-11', '55.00', currency='EUR'), rc('C2', '2026-11-11', '55.00', currency='EUR')]
    o3.intake(PREP, packet('oct', octr + [stmt(octr, ('2026-10', '2026-10-01', '2026-10-31'))]))
    o3.intake(PREP, packet('nov', novr + [stmt(novr, opening='400.00')])); run(o3, 'card_preparation', '2026-11')
    brk = gov(o3, CARD + ':C1', '2026-11'); wp = gov(o3, 'statement:' + CARD, '2026-11', kinds=None)
    print('    opening 400.00 against prior closing 500.00:', brk['blockers'])
    print('    workpaper unreconciled population:', [(u['source_key'], u['reason']) for u in wp['payload']['data']['unreconciled_population']])
    ok = ('STATEMENT_LINE_POPULATION_MISMATCH' in swap['blockers'] and 'STATEMENT_CONTROL_MISMATCH' in off['blockers'] and 'STATEMENT_OPENING_BALANCE_BREAK' in brk['blockers']
          and any(u['source_key'] == CARD + ':C2' and u['reason'] == 'currency' for u in wp['payload']['data']['unreconciled_population']))
    return 'OK' if ok else 'WEAK'


@probe('RT13n', 'T-13', 'limits of the statement control when line identities or the prior statement are absent')
def _():
    os_ = new_os(periods=(('2026-10', '2026-10-01', '2026-10-31'), NOV))
    claimed = [tx('S1', '2026-11-03', '40.00'), tx('S2', '2026-11-04', '60.00')]
    actual = [tx('S1', '2026-11-03', '40.00'), rc('S1', '2026-11-03', '40.00'), tx('S9', '2026-11-04', '60.00'), rc('S9', '2026-11-04', '60.00')]
    os_.intake(PREP, packet('swap', actual + [stmt(claimed, line_ids=False, opening='777.00', provenance='manually_keyed')])); run(os_, 'card_preparation', '2026-11')
    s9 = gov(os_, CARD + ':S9', '2026-11'); wp = gov(os_, 'statement:' + CARD, '2026-11', kinds=None)
    data = wp['payload']['data']
    print('    substituted line, statement without line ids, keyed by the preparer, no October statement on file:', brief(s9))
    print('    workpaper fields:', sorted(data), '| blockers:', wp['blockers'])
    disclosed = any('line' in k or 'identity' in k or 'continuity' in k or 'provenance' in k for k in data)
    print('    workpaper discloses that line identity, continuity or provenance was not checked:', disclosed)
    return 'OK' if not s9['eligible'] or disclosed else 'NOTE'


# ---------------------------------------------------------------------------------------
# Part 3. Batch 2 tickets T-14 to T-19
# ---------------------------------------------------------------------------------------

def accept_revised_evidence(os_, key):
    """RV-12 positive setup: an explicitly granted non-supplier accepts the revision."""
    a=gov(os_,key)
    assert 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'], 'Revised evidence must be held first'
    assert a['payload']['data']['evidence_revisions'], 'Revision history must be disclosed'
    result=dispose(os_,key,'EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=DISP)
    assert result[0]=='ok',result


def dispose(os_, key, code, choice, payload=None, evidence=None, who=DISP, **kw):
    a = gov(os_, key)
    return attempt(os_.disposition, who, 'card_preparation', '2026-11', key, code, choice, payload or {},
                   a['payload']['data']['evidence']+(a['payload']['data'].get('duplicate_evidence',[]) if choice=='distinct_purchases' else []) if evidence is None else evidence, 'Fictional probe disposition', **kw)


def duplicate_pair(extra=()):
    os_ = new_os()
    rows = [tx('D1', '2026-11-06', '90.00'), rc('D1', '2026-11-06', '90.00', content='Fictional receipt one'),
            tx('D2', '2026-11-06', '90.00'), rc('D2', '2026-11-06', '90.00', content='Fictional receipt two')] + list(extra)
    os_.intake(PREP, packet('dups', rows + [stmt(rows)])); run(os_, 'card_preparation')
    return os_, rows


@probe('RT14a', 'T-14', 'dispositions: closed vocabulary, exact split, separate review, revocation, inert rule proposal, referral never clears')
def _():
    extra = [tx('S1', '2026-11-10', '35.00', desc='METRO REPAIR DEMO', requires_split=True), rc('S1', '2026-11-10', '35.00', vendor='METRO REPAIR DEMO'),
             tx('F1', '2026-11-11', '55.00', currency='EUR'), rc('F1', '2026-11-11', '55.00', currency='EUR')]
    os_, rows = duplicate_pair(extra)
    print('    before:', {k: gov(os_, CARD + ':' + k)['blockers'] for k in ('D1', 'D2', 'S1', 'F1')})
    r = {}
    r['override a currency hold with a clearing choice'] = dispose(os_, CARD + ':F1', 'CURRENCY_MISMATCH', 'distinct_purchases')
    r['disposition by a reviewer without the grant'] = dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', who=REV)
    r['split that does not sum to the charge'] = dispose(os_, CARD + ':S1', 'SPLIT_REQUIRES_REVIEW', 'allocate', {'allocations': [{'account_id': 'DEMO_REPAIRS', 'amount': '20.00'}, {'account_id': 'DEMO_OFFICE_SUPPLIES', 'amount': '10.00'}]})
    r['disposition with no evidence'] = dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=[])
    for k, v in r.items():
        show(k, v)
    d1 = dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases'); d2 = dispose(os_, CARD + ':D2', 'POSSIBLE_DUPLICATE', 'distinct_purchases')
    sp = dispose(os_, CARD + ':S1', 'SPLIT_REQUIRES_REVIEW', 'allocate', {'allocations': [{'account_id': 'DEMO_REPAIRS', 'amount': '20.00'}, {'account_id': 'DEMO_OFFICE_SUPPLIES', 'amount': '15.00'}]})
    ref = dispose(os_, CARD + ':F1', 'CURRENCY_MISMATCH', 'refer_external')
    rule = dispose(os_, CARD + ':F1', 'CURRENCY_MISMATCH', 'refer_external', {'rule': {'kind': 'vendor_mapping', 'key': 'demo_new', 'effective_from': '2026-11-01', 'value': {'id': 'demo_new', 'name': 'New (fictional)', 'aliases': ['NEW VENDOR DEMO'], 'category': 'DEMO_REPAIRS'}}}, scope_kind='propose_rule')
    print('    accepted dispositions:', [x[0] for x in (d1, d2, sp, ref)], '| rule proposal via disposition:', rule)
    run(os_, 'card_preparation')
    after = {k: gov(os_, CARD + ':' + k) for k in ('D1', 'D2', 'S1', 'F1')}
    print('    after:', {k: (bool(a['eligible']), a['blockers'], a['payload']['data']['disposition_ids']) for k, a in after.items()})
    lines = after['S1']['payload']['data']['proposed_entry']['lines']
    print('    split entry lines:', [(l['account_id'], l['debit'], l['credit']) for l in lines])
    exp = os_.export(PREP)
    rule_decided = [d for d in exp['rule_decisions'] if d['rule_id'] == rule[1]] if rule[0] == 'ok' else None
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'probe: dispositioner also holds review, to isolate the independence check')
    own = show('dispositioner approves the item they dispositioned', review(os_, DISP, after['D1'], 'approve'))
    ind = show('independent reviewer approves it (positive control)', review(os_, REV, after['D1'], 'approve'))
    show('revoke the D2 disposition', attempt(os_.revoke_disposition, DISP, d2[1], 'probe revoke')); run(os_, 'card_preparation')
    d2b = gov(os_, CARD + ':D2'); print('    D2 after revocation:', brief(d2b))
    ok = (all(v[0] == 'refused' for v in r.values()) and all(x[0] == 'ok' for x in (d1, d2, sp, ref)) and rule[0] == 'ok' and rule_decided == []
          and after['D1']['eligible'] and after['D2']['eligible'] and after['S1']['eligible'] and not after['F1']['eligible'] and 'CURRENCY_MISMATCH' in after['F1']['blockers']
          and sorted((l['account_id'], l['debit'], l['credit']) for l in lines) == [('DEMO_CARD_LIABILITY', '0.00', '35.00'), ('DEMO_OFFICE_SUPPLIES', '15.00', '0.00'), ('DEMO_REPAIRS', '20.00', '0.00')]
          and own[0] == 'refused' and ind[0] == 'ok' and 'POSSIBLE_DUPLICATE' in d2b['blockers'] and not d2b['eligible'])
    return 'OK' if ok else 'WEAK'


@probe('RT14b', 'T-14', 'a distinct-purchases disposition does not cover a duplicate candidate that arrives afterwards')
def _():
    os_, rows = duplicate_pair()
    for k in ('D1', 'D2'):
        own = [e for e in gov(os_, CARD + ':' + k)['payload']['data']['evidence'] if e['source_key'] in (CARD + ':' + k, 'receipt-' + k)]+gov(os_,CARD+':'+k)['payload']['data'].get('duplicate_evidence',[])
        dispose(os_, CARD + ':' + k, 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own)      # charge and its own receipt only
    run(os_, 'card_preparation'); print('    D1 after disposition:', brief(gov(os_, CARD + ':D1')))
    third = [tx('D3', '2026-11-06', '90.00'), rc('D3', '2026-11-06', '90.00', content='Fictional receipt three')]
    os_.intake(PREP, packet('third', third + [stmt(rows + third)])); run(os_, 'card_preparation')
    d1, d3 = gov(os_, CARD + ':D1'), gov(os_, CARD + ':D3')
    print('    after a third identical charge arrives -> D1:', brief(d1), '| candidates listed on D1:', [c['source_key'] for c in d1['payload']['data']['duplicate_candidates']], '| D3:', d3['blockers'])
    return 'WEAK' if d1['eligible'] and 'POSSIBLE_DUPLICATE' not in d1['blockers'] else 'OK'


@probe('RT14c', 'T-14', 'after one of two charges is excluded as a duplicate, the surviving charge has a truthful path to approval')
def _():
    os_, rows = duplicate_pair()
    ex = show('D2 dispositioned as duplicate_of D1', dispose(os_, CARD + ':D2', 'POSSIBLE_DUPLICATE', 'duplicate_of', {'duplicate_of': CARD + ':D1'}))
    run(os_, 'card_preparation'); d1, d2 = gov(os_, CARD + ':D1'), gov(os_, CARD + ':D2')
    print('    excluded D2:', brief(d2), '| entry:', d2['payload']['data']['proposed_entry'])
    print('    surviving D1:', brief(d1))
    excluded_ok = ex[0] == 'ok' and not d2['eligible'] and 'DUPLICATE_EXCLUDED' in d2['blockers'] and d2['payload']['data']['proposed_entry'] is None
    if not excluded_ok:
        return 'WEAK'
    return 'WEAK' if 'POSSIBLE_DUPLICATE' in d1['blockers'] else 'OK'


@probe('RT14d', 'T-14', 'evidence cited for a disposition must be more than the item\'s own source row')
def _():
    os_, rows = duplicate_pair()
    d1 = gov(os_, CARD + ':D1'); own_row = [e for e in d1['payload']['data']['evidence'] if e['source_key'] == CARD + ':D1']
    res = show('distinct_purchases citing only the charge itself', dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own_row))
    return 'NOTE' if res[0] == 'ok' else 'OK'


@probe('RT14e', 'T-14/T-15', 'a card payment cannot be turned into a credit to an expense account through dispositions')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'),
            tx('P1', '2026-11-12', '-300.00', desc='CARD PAYMENT DEMO', activity='payment'), rc('P1', '2026-11-12', '-300.00', vendor='CARD PAYMENT DEMO')]
    os_.intake(PREP, packet('pay', rows + [stmt(rows)])); run(os_, 'card_preparation')
    print('    payment before:', gov(os_, CARD + ':P1')['blockers'])
    acct = {'account_id': 'DEMO_OFFICE_SUPPLIES'}
    steps = [dispose(os_, CARD + ':P1', 'NON_EXPENSE_REQUIRES_REVIEW', 'standalone_credit', acct), dispose(os_, CARD + ':P1', 'UNKNOWN_VENDOR', 'confirm_vendor', acct), dispose(os_, CARD + ':P1', 'UNKNOWN_CATEGORY', 'code_category', acct)]
    print('    dispositions (standalone_credit, confirm_vendor, code_category):', [s if s[0] == 'refused' else 'ok' for s in steps])
    run(os_, 'card_preparation'); p1 = gov(os_, CARD + ':P1')
    entry = p1['payload']['data']['proposed_entry']
    print('    payment after:', brief(p1), '| entry:', [(l['account_id'], l['debit'], l['credit']) for l in entry['lines']] if entry else None)
    approve = show('independent approval', review(os_, REV, p1, 'approve'))
    bad = approve[0] == 'ok' and entry and any(l['account_id'] == 'DEMO_OFFICE_SUPPLIES' and l['credit'] == '300.00' for l in entry['lines'])
    return 'WEAK' if bad else 'OK'


@probe('RT14f', 'T-14', 'an empty inventory blocks the steps that depend on it')
def _():
    os_ = new_os()
    run(os_, 'card_preparation')
    got = {a['item_key']: a['blockers'] for a in arts(os_, kinds=None)}
    print('    artifacts with no source evidence:', got)
    ok = all('NO_SOURCE_EVIDENCE' in b for b in got.values()) and {'inventory', 'no-transactions', 'package-manifest'} <= set(got)
    return 'OK' if ok else 'WEAK'


@probe('RT15', 'T-15', 'one source, one live entry: a journal citing a card item is held on both, and stays held after the source is revised')
def _():
    os_ = new_os()
    clean_november(os_); run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1'); entry = a1['payload']['data']['proposed_entry']
    ref = [e for e in a1['payload']['data']['evidence'] if e['source_key'] == CARD + ':A1'][0]
    print('    card entry:', [(l['account_id'], l['debit'], l['credit']) for l in entry['lines']], '| origin:', entry['origin']['item_key'], [s['snapshot_id'] for s in entry['origin']['source_references']], '| posting:', entry['external_posting'])
    j = journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '40.00', '0.00', None), ('DEMO_CARD_LIABILITY', '0.00', '40.00', None)], ['sup1'], origin_sources=[ref])
    os_.intake(PREP, packet('j', [j, doc('sup1', 'journal_support', journal_keys=['J1'])]))
    run(os_, 'card_preparation'); run(os_, 'journal_preparation')
    c1, j1 = gov(os_, CARD + ':A1'), gov(os_, 'J1')
    print('    journal cites the card source -> card:', c1['blockers'], '| journal:', j1['blockers'])
    held = 'SOURCE_ALREADY_HAS_ENTRY' in c1['blockers'] and 'SOURCE_ALREADY_HAS_ENTRY' in j1['blockers']
    revised = tx('A1', '2026-11-03', '40.00', desc='Acme  Paper  Demo')                 # same accounting content, new version
    os_.intake(PREP, packet('rev', [revised])); run(os_, 'card_preparation'); run(os_, 'journal_preparation')
    c2, j2 = gov(os_, CARD + ':A1'), gov(os_, 'J1')
    print('    after a cosmetic revision of the card source -> card:', brief(c2), '| journal:', brief(j2))
    both = [review(os_, REV, c2, 'approve')[0], review(os_, REV, j2, 'approve')[0]]
    print('    independent approval of both (40.00 expense recorded twice):', both)
    return 'OK' if held and both != ['ok', 'ok'] else 'WEAK'


@probe('RT16', 'T-16', 'journal controls tested one at a time: wrong-type support, unbound support, duplicates, no net effect, dimensions')
def _():
    os_ = new_os()
    def j(key, amount, support, lines=None, **extra):
        return journal(key, '2026-11-13', lines or [('DEMO_OFFICE_SUPPLIES', amount, '0.00', None), ('DEMO_CASH', '0.00', amount, None)], support, **extra)
    rows = [j('J-OK', '25.00', ['sup-ok']), doc('sup-ok', 'journal_support', journal_keys=['J-OK']),
            j('J-WRONGTYPE', '26.00', ['sup-tb']), doc('sup-tb', 'trial_balance', journal_keys=['J-WRONGTYPE']),
            j('J-UNBOUND', '27.00', ['sup-other']), doc('sup-other', 'journal_support', journal_keys=['J-OK']),
            j('J-NOKEYS', '27.50', ['sup-nokeys']), doc('sup-nokeys', 'journal_support'),
            j('J-DUPA', '28.00', ['sup-dupa']), doc('sup-dupa', 'journal_support', journal_keys=['J-DUPA']),
            j('J-DUPB', '28.00', ['sup-dupb'], lines=[('DEMO_CASH', '0.00', '28.00', None), ('DEMO_OFFICE_SUPPLIES', '28.00', '0.00', None)], memo='Different memo, reversed line order'), doc('sup-dupb', 'journal_support', journal_keys=['J-DUPB']),
            j('J-ZERO', '50.00', ['sup-zero'], lines=[('DEMO_OFFICE_SUPPLIES', '50.00', '0.00', None), ('DEMO_OFFICE_SUPPLIES', '0.00', '50.00', None)]), doc('sup-zero', 'journal_support', journal_keys=['J-ZERO']),
            j('J-DIM', '51.00', ['sup-dim'], lines=[('DEMO_OFFICE_SUPPLIES', '51.00', '0.00', {'dept': 'a'}), ('DEMO_OFFICE_SUPPLIES', '0.00', '51.00', {'dept': 'b'})]), doc('sup-dim', 'journal_support', journal_keys=['J-DIM']),
            j('J-DIMZERO', '52.00', ['sup-dimzero'], lines=[('DEMO_OFFICE_SUPPLIES', '52.00', '0.00', {'dept': 'a'}), ('DEMO_OFFICE_SUPPLIES', '0.00', '52.00', {'dept': 'a'})]), doc('sup-dimzero', 'journal_support', journal_keys=['J-DIMZERO']),
            j('J-MISSING', '29.00', ['not-there'])]
    os_.intake(PREP, packet('journals', rows)); run(os_, 'journal_preparation')
    got = {k: gov(os_, k) for k in ('J-OK', 'J-WRONGTYPE', 'J-UNBOUND', 'J-NOKEYS', 'J-DUPA', 'J-DUPB', 'J-ZERO', 'J-DIM', 'J-DIMZERO', 'J-MISSING')}
    for k, a in got.items():
        print('    %-12s eligible=%-5s %s' % (k, bool(a['eligible']), a['blockers']))
    b = {k: a['blockers'] for k, a in got.items()}
    ok = (got['J-OK']['eligible'] and b['J-WRONGTYPE'] == ['JOURNAL_SUPPORT_NOT_BOUND'] and b['J-UNBOUND'] == ['JOURNAL_SUPPORT_NOT_BOUND'] and b['J-NOKEYS'] == ['JOURNAL_SUPPORT_NOT_BOUND']
          and b['J-DUPA'] == ['POSSIBLE_DUPLICATE_JOURNAL'] and b['J-DUPB'] == ['POSSIBLE_DUPLICATE_JOURNAL'] and b['J-ZERO'] == ['NO_NET_LEDGER_EFFECT']
          and 'DIMENSIONS_NOT_CONFIGURED' in b['J-DIM'] and 'NO_NET_LEDGER_EFFECT' not in b['J-DIM'] and 'NO_NET_LEDGER_EFFECT' in b['J-DIMZERO'] and b['J-MISSING'] == ['MISSING_JOURNAL_SUPPORT'])
    return 'OK' if ok else 'WEAK'


@probe('RT17', 'T-17', 'receipt policy: unset stays explicit, a proposed rule has no effect, both sides of the date and amount boundaries')
def _():
    os_ = new_os()
    rows = [tx('R0', '2026-11-08', '19.00'), rc('R0', '2026-11-08', '19.00'),
            tx('R1', '2026-11-10', '20.00'), rc('R1', '2026-11-09', '20.00'), tx('R2', '2026-11-12', '21.00'), rc('R2', '2026-11-10', '21.00'),
            tx('R3', '2026-11-14', '22.00'), rc('R3', '2026-11-14', '22.05'), tx('R4', '2026-11-16', '23.00'), rc('R4', '2026-11-16', '23.06'),
            tx('R5', '2026-11-18', '24.00'), rc('R5', '2026-11-19', '24.00'),
            tx('R6', '2026-11-20', '25.00'), rc('R6', '2026-11-20', '25.00', key='receipt-R6a', content='Fictional receipt R6 a'), rc('R6', '2026-11-20', '25.00', key='receipt-R6b', content='Fictional receipt R6 b'),
            tx('R7', '2026-11-22', '26.00'), rc('R7', '2026-11-22', '26.00', vendor='SOMEONE ELSE DEMO')]
    os_.intake(PREP, packet('receipts', rows + [stmt(rows)])); run(os_, 'card_preparation')
    keys = ('R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7')
    unset = {k: gov(os_, CARD + ':' + k)['blockers'] for k in keys}
    print('    no rule:', unset)
    rule = {'date_window_days': 1, 'amount_tolerance': '0.05', 'multiple_receipts': None, 'vendor_method': None, 'statement_substitution': None}
    rid = os_.propose_rule(PREP, 'receipt_matching', 'default', rule, '2026-11-01'); run(os_, 'card_preparation')
    proposed = {k: gov(os_, CARD + ':' + k)['blockers'] for k in keys}
    print('    rule proposed only, unchanged:', proposed == unset)
    os_.approve_rule(CTRL, rid, 'probe: synthetic one-day window and five-cent tolerance'); run(os_, 'card_preparation')
    approved = {k: gov(os_, CARD + ':' + k)['blockers'] for k in keys}
    print('    approved window 1 day, tolerance 0.05:', approved)
    ok = (unset == {'R0': [], 'R1': ['RECEIPT_DATE_POLICY_UNSET'], 'R2': ['RECEIPT_DATE_POLICY_UNSET'], 'R3': ['RECEIPT_AMOUNT_POLICY_UNSET'], 'R4': ['RECEIPT_AMOUNT_POLICY_UNSET'],
                    'R5': ['RECEIPT_DATE_POLICY_UNSET'], 'R6': ['RECEIPT_MULTIPLE_POLICY_UNSET'], 'R7': ['RECEIPT_VENDOR_POLICY_UNSET']} and proposed == unset
          and approved == {'R0': [], 'R1': [], 'R2': ['RECEIPT_DATE_MISMATCH'], 'R3': [], 'R4': ['RECEIPT_AMOUNT_MISMATCH'], 'R5': [], 'R6': ['RECEIPT_MULTIPLE_POLICY_UNSET'], 'R7': ['RECEIPT_VENDOR_POLICY_UNSET']})
    return 'OK' if ok else 'WEAK'


@probe('RT18', 'T-18', 'finalization: independent granted human, acknowledgement of carried items, frozen bytes, visible later changes')
def _():
    os_ = new_os()
    clean_november(os_, extra=[tx('A3', '2026-11-06', '5.00', desc='NOBODY KNOWN DEMO')]); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    os_.grant_authority(ADMIN, PREP.id, ['finalize'], 'probe: preparer holds the grant, to isolate the independence check')
    r = {'preparer role': attempt(os_.finalize_package, PREP, '2026-11', 'card_preparation', 'x', 'x'),
         'same person in a reviewer role': attempt(os_.finalize_package, human(PREP.id, 'reviewer'), '2026-11', 'card_preparation', 'x', 'x'),
         'reviewer without the finalize grant': attempt(os_.finalize_package, REV2, '2026-11', 'card_preparation', 'x', 'x'),
         'no acknowledgement while A3 is carried': attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover')}
    for k, v in r.items():
        show('finalize refused for ' + k, v)
    pid = show('finalize by the independent finalizer with acknowledgement', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover', 'A3 unknown vendor carried; fictional'))
    pkg0 = [p for p in os_.state(PREP)['packages'] if p['id'] == pid[1]][0]; payload = json.loads(pkg0['payload'])
    print('    package records:', sorted(payload), '| carried:', payload['open_exceptions'], '| authority:', payload['authority'])
    os_.intake(PREP, packet('unrelated', [journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['sup1']), doc('sup1', 'journal_support', journal_keys=['J1'])]))
    ev1 = [e['code'] for e in os_.state(PREP)['accounting_events']]
    base = [tx('A1', '2026-11-03', '40.00'), tx('A3', '2026-11-06', '5.00', desc='NOBODY KNOWN DEMO')]
    changed = [tx('A2', '2026-11-04', '61.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '61.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('revision', changed + [stmt(base + changed)]))
    st = os_.state(PREP); pkg1 = [p for p in st['packages'] if p['id'] == pid[1]][0]; ev2 = [(e['code'], e['item_key']) for e in st['accounting_events']]
    print('    after unrelated journal intake -> events:', ev1, '| after a card source revision -> events:', ev2)
    print('    package bytes unchanged:', pkg0['payload'] == pkg1['payload'] and pkg0['hash'] == pkg1['hash'])
    stale = show('finalize again while items are stale, with acknowledgement', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'x', 'acknowledged'))
    run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1'); review(os_, REV, a1, 'approve'); review(os_, REV2, a1, 'reject')
    disputed = show('finalize while A1 is disputed, with acknowledgement', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'x', 'acknowledged'))
    res = show('third reviewer resolves the dispute', review(os_, REV3, a1, 'resolve_approve'))
    rev = show('mistaken revoke by a fourth reviewer', review(os_, REV4, a1, 'revoke'))
    os_.grant_authority(ADMIN, 'rv-reviewer-5', ['review'], 'probe: fifth reviewer for the recovery path')
    rec = show('recovery by a fifth independent reviewer', review(os_, human('rv-reviewer-5', 'reviewer'), a1, 'resolve_approve'))
    again = show('second package for the same period and workflow', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe second handover', 'A2 re-prepared and unreviewed; A3 carried; fictional'))
    print('    A1 status after recovery:', gov(os_, CARD + ':A1')['review_status'], '| packages on file for November card preparation:', len(os_.state(PREP)['packages']))
    ok = (all(v[0] == 'refused' for v in r.values()) and pid[0] == 'ok' and ev1 == [] and any(c == 'POST_FINALIZATION_CHANGE' for c, _ in ev2)
          and pkg0['payload'] == pkg1['payload'] and stale[0] == 'refused' and disputed[0] == 'refused' and res[0] == 'ok' and rev[0] == 'ok' and rec[0] == 'ok'
          and gov(os_, CARD + ':A1')['review_status'] == 'approve')
    if ok and again[0] == 'ok':
        print('    observation: a second package was accepted with no link to, or supersession of, the first')
    return 'OK' if ok else 'WEAK'


@probe('RT19a', 'T-19', 'close readiness: a document label alone does not complete reconciliation or tie-out requirements')
def _():
    os_ = new_os()
    labels = ['trial_balance', 'card_statement', 'bank_reconciliation', 'ap_tieout', 'ar_tieout']
    clean_november(os_, extra=[doc('label-' + t, t, content='Fictional label-only document; nothing was reconciled') for t in labels] + [doc('wrong-period', 'trial_balance', period_id='2026-10')])
    run(os_, 'card_preparation'); run(os_, 'close_readiness')
    c0 = gov(os_, 'close-checklist', kinds=None)
    print('    items unreviewed -> blockers:', c0['blockers'])
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    stale = gov(os_, 'close-checklist', kinds=None)['review_status']
    run(os_, 'close_readiness'); c1 = gov(os_, 'close-checklist', kinds=None)
    reqs = [(r['requirement']['document_type'], r['satisfied']) for r in c1['payload']['data']['requirements']]
    print('    after review the earlier checklist is:', stale, '| shipped checklist', os_.state(PREP)['profile']['required_close_evidence'])
    print('    requirement results with label-only documents:', reqs, '| blockers:', c1['blockers'])
    rid = os_.propose_rule(PREP, 'close_checklist', 'close', [{'type': 'reconciliation', 'document_type': 'bank_reconciliation'}, {'type': 'tieout', 'document_type': 'ap_tieout'}, {'type': 'workflow_outcome', 'workflow': 'card_preparation'}], '2026-11-01')
    os_.approve_rule(CTRL, rid, 'probe: typed checklist'); run(os_, 'close_readiness'); c2 = gov(os_, 'close-checklist', kinds=None)
    typed = [(r['requirement']['type'], r['satisfied']) for r in c2['payload']['data']['requirements']]
    print('    typed checklist results:', typed, '| blockers:', c2['blockers'])
    always = all(x in c.get('blockers', []) for c in (c0, c1, c2) for x in ('FINAL_CLOSE_SIGNOFF_REQUIRED', 'EXTERNAL_STEPS_UNVERIFIED'))
    base = ('UNREVIEWED_PREPARATION' in c0['blockers'] and stale == 'stale' and always and typed == [('reconciliation', False), ('tieout', False), ('workflow_outcome', True)]
            and 'OPEN_PREPARATION_EXCEPTIONS' in c1['blockers'])          # wrong-period document is quarantined and disclosed
    label_completes = any(t in ('bank_reconciliation', 'ap_tieout', 'ar_tieout') and s for t, s in reqs)
    print('    typed requirements hold:', base, '| label-only documents satisfy reconciliation/tie-out under the shipped checklist:', label_completes)
    return 'OK' if base and not label_completes else 'WEAK'


@probe('RT19b', 'T-19', 'close readiness waits for in-flight preparation and does not adopt changed sources')
def _():
    os_ = new_os()
    clean_november(os_)
    card = os_.enqueue(PREP, 'card_preparation', '2026-11'); close = os_.enqueue(PREP, 'close_readiness', '2026-11')
    order = []
    for _ in range(12):
        c = os_.claim(WORKER)
        if not c:
            break
        order.append((c['run_id'], c['capability']))
        from accounting_agent.modules import CAPABILITIES
        os_.commit(WORKER, c, CAPABILITIES[c['capability']].handler(c['context']))
    first_close = min(i for i, o in enumerate(order) if o[0] == close); last_card = max(i for i, o in enumerate(order) if o[0] == card)
    chk = gov(os_, 'close-checklist', kinds=None)
    seen = sorted(i['item_key'] for i in chk['payload']['data']['period_status']['items'])
    print('    step order (run, capability):', order)
    print('    close started after card finished:', first_close > last_card, '| items seen by the checklist:', seen, '| current:', chk['current'])
    review(os_, REV, gov(os_, CARD + ':A1'), 'approve')
    close2 = os_.enqueue(PREP, 'close_readiness', '2026-11')                                      # queued with A1 approved, A2 pending
    review(os_, REV, gov(os_, CARD + ':A2'), 'approve')                                           # only the review status changes while it waits
    os_.drain(WORKER)
    chk2 = gov(os_, 'close-checklist', kinds=None)
    statuses = sorted((i['item_key'], i['status']) for i in chk2['payload']['data']['period_status']['items'])
    print('    queued close run, then a review decision -> run', close2, 'completed with refreshed statuses:', statuses)
    review(os_, REV2, gov(os_, CARD + ':A2'), 'revoke')
    close3 = os_.enqueue(PREP, 'close_readiness', '2026-11')                                      # queued
    os_.intake(PREP, packet('late-doc', [doc('late', 'trial_balance')], period_id='2026-11'))       # a close input changes while it waits
    os_.drain(WORKER)
    runs = {r['id']: r['status'] for r in os_.state(PREP)['runs']}
    print('    queued close run, then a new close document -> run', close3, 'status:', runs.get(close3), '(must not complete on inputs it was not queued with)')
    ok = (first_close > last_card and seen == [CARD + ':A1', CARD + ':A2'] and close2 != close and all(s == 'approve' for _, s in statuses)
          and close3 not in (close, close2) and runs.get(close3) == 'held')
    return 'OK' if ok else 'WEAK'


# ---------------------------------------------------------------------------------------
# Part 4. Full teaching month, driven independently, and two-client isolation (gate G0)
# ---------------------------------------------------------------------------------------

@probe('RG0', 'G0', 'teaching month through service operations only; lineage, entry impact and second-client isolation recomputed')
def _():
    COUNTER[0] += 1
    scope2 = ORG + '/second_demo/local'
    os_ = AccountingOS(Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0]), [SCOPE, scope2])
    sid = os_.onboard(PREP, copy.deepcopy(PROFILE))
    for subject, permissions in ROLES.items():
        os_.grant_authority(ADMIN, subject, permissions, 'Fictional probe authority; listed in ROLES')
    os_.approve_profile_version(CTRL, sid, 'Explicit independent approval'); os_.open_period(PADMIN, *NOV, 'Fictional teaching month')
    teaching = load('fixtures/teaching.json')
    os_.intake(PREP, teaching); os_.intake(PREP, load('fixtures/late_receipt.json'))
    run(os_, 'card_preparation'); run(os_, 'journal_preparation')
    first = {a['item_key']: a for a in arts(os_) if a['governing']}
    print('    as delivered, before any correction:')
    for k in sorted(first):
        if not first[k]['eligible']:
            print('      %-22s %s' % (k, first[k]['blockers']))
    quarantined = [(e['source_key'], e['reason']) for e in os_.state(PREP)['source_exceptions']]
    print('    quarantined sources:', quarantined)
    from accounting_agent.exceptions import VOCABULARY
    no_path = sorted(k for k, a in first.items() if not a['eligible'] and not any(c in VOCABULARY for c in a['blockers']))
    print('    held items whose blockers have no disposition vocabulary at all:', no_path)
    # The delivered walkthrough clears these two by re-supplying the evidence. Reproduced here so that the rest can be judged.
    src = {s['key']: s for s in teaching['sources']}
    fixed_rc = copy.deepcopy(src['receipt-TX-009']); fixed_rc['data']['amount'] = '80.00'
    fixed_j = copy.deepcopy(src['J-002']); fixed_j['data']['lines'][0]['debit'] = '26.00'; fixed_j['data']['lines'][1]['credit'] = '26.00'
    os_.intake(PREP, packet('teaching-corrections', [fixed_rc, fixed_j])); run(os_, 'card_preparation'); run(os_, 'journal_preparation'); accept_revised_evidence(os_,CARD+':TX-009'); run(os_,'card_preparation')
    K = CARD + ':TX-0'
    steps = [dispose(os_, K + '04', 'POSSIBLE_DUPLICATE', 'distinct_purchases'), dispose(os_, K + '05', 'POSSIBLE_DUPLICATE', 'distinct_purchases'),
             dispose(os_, K + '03', 'UNKNOWN_VENDOR', 'confirm_vendor', {'account_id': 'DEMO_OFFICE_SUPPLIES'}), dispose(os_, K + '03', 'UNKNOWN_CATEGORY', 'code_category', {'account_id': 'DEMO_OFFICE_SUPPLIES'}),
             dispose(os_, K + '06', 'CREDIT_REQUIRES_REVIEW', 'standalone_credit', {'account_id': 'DEMO_OFFICE_SUPPLIES'}),
             dispose(os_, K + '10', 'SPLIT_REQUIRES_REVIEW', 'allocate', {'allocations': [{'account_id': 'DEMO_REPAIRS', 'amount': '20.00'}, {'account_id': 'DEMO_OFFICE_SUPPLIES', 'amount': '15.00'}]}),
             dispose(os_, K + '12', 'NON_EXPENSE_REQUIRES_REVIEW', 'settlement_of_card_liability', {'cash_account': 'DEMO_CASH'}),
             dispose(os_, K + '07', 'PENDING_TRANSACTION', 'refer_external'), dispose(os_, K + '11', 'CURRENCY_MISMATCH', 'refer_external')]
    print('    dispositions accepted:', sum(1 for s in steps if s[0] == 'ok'), 'of', len(steps))
    run(os_, 'card_preparation')
    current = [a for a in arts(os_, period_id='2026-11') if a['governing'] and a['current']]
    approved, carried, impact = [], [], {}
    for a in current:
        if a['eligible']:
            res = review(os_, REV, a, 'approve')
            if res[0] != 'ok':
                print('      approval refused', a['item_key'], res); continue
            approved.append(a['item_key'])
            for l in a['payload']['data']['proposed_entry']['lines']:
                impact[l['account_id']] = impact.get(l['account_id'], Decimal('0.00')) + Decimal(l['debit']) - Decimal(l['credit'])
        else:
            carried.append((a['item_key'], a['blockers'], a['payload']['data'].get('disposition_ids')))
    print('    approved (%d):' % len(approved), sorted(approved)); print('    carried:', carried)
    hand = {'DEMO_OFFICE_SUPPLIES': Decimal('42.50') + 65 + 90 + 90 - Decimal('42.50') + 80 + 15 + 25 + 26, 'DEMO_REPAIRS': Decimal('180.00') + 20,
            'DEMO_CARD_LIABILITY': -(Decimal('42.50') + 180 + 65 + 90 + 90 + 80 + 35) + Decimal('42.50') + 300 - 25 - 26, 'DEMO_CASH': Decimal('-300.00')}
    print('    entry impact from approved artifacts:', {k: str(v) for k, v in sorted(impact.items())}, '| equals hand calculation:', impact == hand, '| nets to zero:', sum(impact.values()) == 0)
    tx9 = [a for a in current if a['item_key'] == K + '09'][0]
    print('    TX-009 evidence versions relied on:', [(e['source_key'], e['version']) for e in tx9['payload']['data']['evidence'] if e['source_key'].startswith('receipt')], '(version 2 is the preparer\'s re-supplied receipt)')
    people = {'reviewer': REV.id, 'dispositioner': DISP.id, 'finalizer': FIN.id, 'period admin': PADMIN.id}
    independent = all(REV.id not in a['contributors'] and FIN.id not in a['contributors'] for a in current)
    ack = 'TX-007 pending and TX-011 foreign currency referred externally and carried; October TX-008 and its receipt quarantined; fictional; no ledger close represented.'
    noack = attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover')
    pk = [attempt(os_.finalize_package, FIN, '2026-11', w, 'Fictional G0 preparation handover', ack) for w in ('card_preparation', 'journal_preparation')]
    lock = attempt(os_.lock_period, PADMIN, '2026-11', 'Fictional G0 lock', ack)
    st1 = os_.state(PREP); card_pkg = json.loads(st1['packages'][0]['payload'])
    print('    finalize without acknowledgement:', noack[0], '| packages:', [p[0] for p in pk], '| lock:', lock[0], '| distinct people:', len(set(people.values())) == 4, '| reviewer and finalizer outside every lineage:', independent)
    print('    card package carries:', [(o['item_key'], o['blockers']) for o in card_pkg['open_exceptions']], '| quarantined named:', sorted({q['source_key'] for q in card_pkg['quarantined_sources']}))
    before = ([(a['id'], a['hash'], a['review_status']) for a in st1['artifacts']], [(p['id'], p['hash'], p['payload']) for p in st1['packages']], len(os_.export(PREP)['evidence_history']))
    # second client, December, same engine
    h2 = lambda name, role: human(name, role, client='second_demo')
    admin2, prep2, ctrl2, rev2, padmin2 = h2('s2-admin', 'administrator'), h2('s2-preparer', 'preparer'), h2('s2-policy', 'reviewer'), h2('s2-reviewer', 'reviewer'), h2('s2-period', 'reviewer')
    worker2 = Actor('s2-worker', 'worker', ORG, 'second_demo', kind='service')
    p2 = copy.deepcopy(PROFILE); p2.update(client_id='second_demo', external_company_id='fictional-second-realm', entity_id='fictional-second-entity', book_id='fictional-second-book')
    sid2 = os_.onboard(prep2, p2)
    os_.grant_authority(admin2, ctrl2.id, ['approve_profile', 'approve_rule'], 'second fictional client'); os_.grant_authority(admin2, rev2.id, ['review'], 'second fictional client')
    os_.approve_profile_version(ctrl2, sid2, 'second fictional client'); os_.open_period(padmin2, *DEC, 'second fictional client')
    pkt = {'synthetic': True, 'organization_id': ORG, 'client_id': 'second_demo', 'external_company_id': 'fictional-second-realm', 'batch_id': 'second-1',
           'sources': [journal('J-900', '2026-12-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['sup-900']), doc('sup-900', 'journal_support', period_id='2026-12', journal_keys=['J-900'])]}
    os_.intake(prep2, pkt); os_.enqueue(prep2, 'journal_preparation', '2026-12'); os_.drain(worker2)
    j900 = [a for a in os_.state(prep2)['artifacts'] if a['item_key'] == 'J-900'][0]
    ok2 = attempt(os_.review, rev2, j900['id'], j900['hash'], j900['fingerprint'], 'approve', 'second fictional client review')
    victim = [a for a in st1['artifacts'] if a['item_key'] == K + '01' and a['governing']][0]
    cross = {'second client reviewer decides a first-client artifact': attempt(os_.review, rev2, victim['id'], victim['hash'], victim['fingerprint'], 'reject', 'x'),
             'first client reviewer decides a second-client artifact': attempt(os_.review, REV, j900['id'], j900['hash'], j900['fingerprint'], 'reject', 'x'),
             'second client preparer sends a first-client packet': attempt(os_.intake, prep2, packet('cross', [doc('x', 'trial_balance')]))}
    for k, v in cross.items():
        show(k, v)
    st2 = os_.state(PREP)
    after = ([(a['id'], a['hash'], a['review_status']) for a in st2['artifacts']], [(p['id'], p['hash'], p['payload']) for p in st2['packages']], len(os_.export(PREP)['evidence_history']))
    isolated = before == after and ok2[0] == 'ok' and all(v[0] == 'refused' for v in cross.values()) and all(a['scope'] == scope2 for a in os_.state(prep2)['artifacts']) and os_.verify_audit(PREP) and os_.verify_audit(prep2)
    print('    second client December journal approved:', ok2[0], '| first client records unchanged and both audit chains verify:', isolated)
    month = (len(approved) == 11 and impact == hand and sorted(c[0] for c in carried) == [K + '07', K + '11'] and all(c[2] for c in carried) and noack[0] == 'refused'
             and all(p[0] == 'ok' for p in pk) and lock[0] == 'ok' and independent and CARD + ':TX-008' in {q['source_key'] for q in card_pkg['quarantined_sources']})
    print('    month reaches approved-or-dispositioned, finalized and locked:', month, '| but only after evidence for', no_path, 'was re-supplied by the preparer')
    return 'OK' if month and isolated else 'WEAK'


# ---------------------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------------------

def main():
    wanted = set(sys.argv[2:])
    import platform
    import sqlite3
    print('Fable re-verification probes | project root:', ROOT.name, '| Python', platform.python_version(), '| SQLite', sqlite3.sqlite_version)
    print('All data fictional; temporary databases only; service operations only.\n')
    results = []
    for pid, ticket, title, fn in PROBES:
        if wanted and pid not in wanted:
            continue
        print('[%s] (%s) %s' % (pid, ticket, title))
        try:
            verdict = fn()
        except Exception:
            traceback.print_exc(limit=4, file=sys.stdout)
            verdict = 'ERROR'
        print('    -> %s\n' % verdict)
        results.append((pid, ticket, verdict, title))
    print('=' * 100)
    for pid, ticket, verdict, title in results:
        print('%-6s %-10s %-6s %s' % (pid, ticket, verdict, title))
    counts = {}
    for r in results:
        counts[r[2]] = counts.get(r[2], 0) + 1
    failing = [r[0] for r in results if r[2] in ('WEAK', 'ERROR')]
    print('\nVerdict counts:', dict(sorted(counts.items())))
    print('Re-verification gate:', 'PASS' if not failing else 'FAIL ' + ', '.join(failing))
    TMP.cleanup()
    sys.exit(1 if failing else 0)


if __name__ == '__main__':
    main()
