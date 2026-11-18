# RA-04 positive-setup adaptation; original independent file remains unchanged.
"""Fable acceptance probes for the RV-01 to RV-17 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_rv_acceptance_probes.py <project-root> [PROBE_ID ...]

What this does
  * Imports the application from <project-root> and drives it through its public service
    operations only. No SQL is written and no application file is edited.
  * Every database is a temporary SQLite file holding fictional data. Nothing is posted,
    sent, paid, connected or deployed, and no model or network service is called.
  * Authority is explicit. A profile is proposed by one human and approved by another;
    every synthetic grant is listed in ROLES or made on the line that needs it, with the
    reason stated. The delivered fixture helpers are not used.
  * Each refusal is paired with a positive control, so a refusal is known to come from the
    control under test. Where a scenario needs a valid starting state, the probe asserts it;
    a failed assertion is reported as ERROR and fails the gate.

Verdicts
  OK     the control held
  WEAK   a confirmed control gap (fails the gate; exit status 1)
  NOTE   a limitation or design observation that needs a decision; does not fail the gate
  ERROR  the probe could not reach its intended state (fails the gate)

Parts
  1  one independent scenario per correction, RV-01 to RV-17 (ids A01 to A17)
  2  routes around the corrections that the delivered tests do not cover (ids X..)
  3  unverified concerns UC-1 and UC-4 (ids U..)
  4  the teaching month by both permitted routes, and two-client isolation (ids M..)
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

TMP = tempfile.TemporaryDirectory(prefix='fable-rv-accept-')
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




def support(a, distinct=False):
    """Evidence references for a disposition: everything the artifact relies on, and for a
    distinct-purchases decision also the receipts of every duplicate candidate."""
    d = a['payload']['data']
    return d['evidence'] + (d.get('duplicate_evidence', []) if distinct else [])


def dispose(os_, key, code, choice, payload=None, evidence=None, who=None, period='2026-11', workflow='card_preparation', **kw):
    a = gov(os_, key, period)
    return attempt(os_.disposition, who or DISP, workflow, period, key, code, choice, payload or {},
                   support(a, choice == 'distinct_purchases') if evidence is None else evidence, 'Fictional probe disposition', **kw)


def accept_statement_revision(os_, key, period='2026-11'):
    """Positive fixture only: assert the hold, then obtain explicit human acceptance."""
    a=gov(os_,key,period)
    assert a is not None and 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'], brief(a)
    assert any(r.get('source_kind')=='statement' for r in a['payload']['data']['evidence_revisions']), 'Statement revision must be disclosed'
    result=dispose(os_,key,'EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',period=period)
    assert result[0]=='ok',result
    run(os_,'card_preparation',period)


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
# ---------------------------------------------------------------------------------------

@probe('A04', 'RV-04', 'a locked, finalized period is untouched by later intake; a genuinely changed receipt is still quarantined')
def _():
    os_ = new_os(periods=(NOV, DEC))
    clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    os_.finalize_package(FIN, '2026-11', 'card_preparation', 'probe handover'); os_.lock_period(PADMIN, '2026-11', 'probe lock')
    before = os_.export(PREP)
    d1 = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
    d2 = d1 + [tx('D2', '2026-12-06', '25.00'), rc('D2', '2026-12-06', '25.00')]
    os_.intake(PREP2, packet('dec-1', d1 + [stmt(d1, DEC, opening='100.00')]))
    os_.intake(PREP2, packet('dec-2', [journal('JD', '2026-12-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['supd']), doc('supd', 'journal_support', period_id='2026-12', journal_keys=['JD'])]))
    os_.intake(PREP2, packet('dec-3', d2[2:] + [stmt(d2, DEC, opening='100.00')]))
    after = os_.export(PREP)
    exc = [(e['source_key'], e['reason']) for e in after['source_exceptions']]; events = [(e['code'], e['item_key']) for e in after['accounting_events']]
    nov_ids = {s['id'] for s in before['evidence_history'] if s['kind'] == 'receipt'}
    grew = sum(1 for b in after['source_period_history'] if b['snapshot_id'] in nov_ids) - sum(1 for b in before['source_period_history'] if b['snapshot_id'] in nov_ids)
    print('    after three December packets -> source exceptions:', exc, '| events:', events, '| new binding rows for November receipts:', grew)
    print('    November statuses:', [gov(os_, CARD + ':' + k)['review_status'] for k in ('A1', 'A2')], '| package unchanged:', before['packages'][0]['hash'] == after['packages'][0]['hash'] and before['packages'][0]['payload'] == after['packages'][0]['payload'])
    quiet = not exc and not events and grew == 0
    os_.intake(PREP2, packet('late', [rc('A1', '2026-11-03', '41.00')]))                         # a real late change to locked evidence
    st = os_.state(PREP)
    exc2 = [(e['source_key'], e['period_id'], e['reason']) for e in st['source_exceptions']]; ev2 = [(e['code'], e['item_key']) for e in st['accounting_events']]
    print('    after a genuinely revised November receipt -> source exceptions:', exc2, '| events:', ev2, '| A1:', gov(os_, CARD + ':A1')['review_status'])
    real = exc2 == [('receipt-A1', '2026-11', 'LATE_ACTIVITY_IN_LOCKED_PERIOD')] and gov(os_, CARD + ':A1')['review_status'] == 'approve' and ('APPROVED_SOURCE_REVISED', CARD + ':A1') in ev2
    return 'OK' if quiet and real else 'WEAK'


@probe('A03', 'RV-03', 'removed and voided sources leave no governing item; exceptions are superseded; the package records the removal')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00', as_of=1), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', as_of=1), rc('A2', '2026-11-04', '60.00'),
            tx('P1', '2026-11-08', '10.00', status='pending', as_of=1), tx('V1', '2026-11-09', '7.00', desc='NOBODY KNOWN DEMO', as_of=1)]
    os_.intake(PREP, packet('b1', rows + [stmt(rows)])); run(os_, 'card_preparation')
    print('    before:', {k: gov(os_, CARD + ':' + k)['blockers'] for k in ('P1', 'V1')})
    stale = show('finalize while P1 and V1 are held, no acknowledgement', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'x'))
    gone = [dict(copy.deepcopy(rows[4]), as_of=2, tombstone=True, removal_reason='feed_removed'), dict(copy.deepcopy(rows[5]), as_of=2, tombstone=True, removal_reason='voided')]
    os_.intake(PREP, packet('b2', gone + [stmt(rows[:4])])); run(os_, 'card_preparation'); accept_statement_revision(os_,CARD+':A1'); accept_statement_revision(os_,CARD+':A2')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    st = os_.export(PREP)
    removed = sorted((r['item_key'], r['previous_artifact_id'] is not None) for r in st['removed_items'])
    exc = sorted((e['item_key'], e['code'], e['status']) for e in st['exceptions'] if e['item_key'] in (CARD + ':P1', CARD + ':V1'))
    kept = sum(1 for s in st['evidence_history'] if s['source_key'] in (CARD + ':P1', CARD + ':V1'))
    print('    governing P1/V1:', gov(os_, CARD + ':P1'), gov(os_, CARD + ':V1'), '| removed items:', removed)
    print('    their exceptions:', exc, '| snapshot versions kept in history:', kept)
    fin = show('finalize after the removals, no acknowledgement needed', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover'))
    payload = json.loads(os_.state(PREP)['packages'][-1]['payload']) if fin[0] == 'ok' else {}
    print('    package removed_items:', sorted(r['item_key'] for r in payload.get('removed_items', [])), '| items:', sorted(i['item_key'] for i in payload.get('items', [])))
    ok = (stale[0] == 'refused' and gov(os_, CARD + ':P1') is None and gov(os_, CARD + ':V1') is None and removed == [(CARD + ':P1', True), (CARD + ':V1', True)]
          and exc and all(e[2] == 'superseded' for e in exc) and kept == 4 and fin[0] == 'ok' and sorted(r['item_key'] for r in payload['removed_items']) == [CARD + ':P1', CARD + ':V1'])
    return 'OK' if ok else 'WEAK'


@probe('A01', 'RV-01', 'new-key supersession out of a locked period, by envelope or by data, is quarantined until reopen and never double-approved')
def _():
    verdicts = []
    for variant in ('envelope', 'data'):
        os_ = new_os(periods=(NOV, DEC))
        clean_november(os_); run(os_, 'card_preparation')
        for k in ('A1', 'A2'):
            review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
        os_.lock_period(PADMIN, '2026-11', 'probe lock')
        new = tx('A1X', '2026-12-02', '40.00')
        if variant == 'envelope':
            new['supersedes'] = CARD + ':A1'
        else:
            new['data']['supersedes_source_id'] = 'A1'
        other = [tx('D1', '2026-12-05', '15.00'), rc('D1', '2026-12-05', '15.00')]
        pkt = packet('sup-' + variant, [new, rc('A1X', '2026-12-02', '40.00')] + other + [stmt(other, DEC, opening='100.00')])
        os_.intake(PREP2, pkt); replay = os_.intake(PREP2, pkt)
        run(os_, 'card_preparation', '2026-12', PREP2)
        st = os_.export(PREP)
        exc = sorted((e['source_key'], e['period_id'], e['reason']) for e in st['source_exceptions'])
        events = [(e['code'], e['period_id'], e['item_key']) for e in st['accounting_events']]
        moves = [(m['from_period_id'], m['to_period_id'], m['blocked'], m['had_approval']) for m in st['source_move_history']]
        locked = (gov(os_, CARD + ':A1X', '2026-12'), gov(os_, CARD + ':A1', '2026-11'), gov(os_, CARD + ':D1', '2026-12'))
        print('    [%s] replay: %s | exceptions: %s' % (variant, replay['replay'], exc))
        print('    [%s] events: %s | moves: %s' % (variant, events, moves))
        print('    [%s] while locked -> December A1X: %s | November A1: %s | unrelated December D1 eligible: %s' % (variant, brief(locked[0]), locked[1]['review_status'], bool(locked[2]['eligible'])))
        held = (locked[0] is None and locked[1]['review_status'] == 'approve' and locked[2]['eligible'] and replay['replay']
                and (CARD + ':A1X', '2026-11', 'SOURCE_MOVED_FROM_LOCKED_PERIOD') in exc and ('receipt-A1X', '2026-11', 'SOURCE_MOVED_FROM_LOCKED_PERIOD') in exc
                and ('APPROVED_SOURCE_SUPERSEDED', '2026-11', CARD + ':A1') in events and any(m[0] == '2026-11' and m[2] == 1 and m[3] == 1 for m in moves))
        os_.reopen_period(PADMIN, '2026-11', 'probe reopen'); run(os_, 'card_preparation', '2026-11'); run(os_, 'card_preparation', '2026-12', PREP2)
        nov, dec = gov(os_, CARD + ':A1', '2026-11'), gov(os_, CARD + ':A1X', '2026-12')
        st = os_.export(PREP)
        current = [(a['period_id'], a['item_key'], a['review_status']) for a in st['artifacts'] if a['item_key'] in (CARD + ':A1', CARD + ':A1X') and a['governing'] and a['current']]
        left = [r['item_key'] for r in st['removed_items'] if r['period_id'] == '2026-11']
        hist = sum(1 for s in st['evidence_history'] if s['source_key'] == CARD + ':A1')
        print('    [%s] after reopen -> November A1: %s | removed from November: %s | December A1X: %s' % (variant, brief(nov), left, brief(dec)))
        print('    [%s] current governing artifacts for the charge: %s | A1 history kept: %s' % (variant, current, hist))
        released = (nov is None and CARD + ':A1' in left and dec is not None and 'SOURCE_TRANSITION_REQUIRES_REVIEW' in dec['blockers'] and 'MISSING_RECEIPT' not in dec['blockers']
                    and len(current) == 1 and current[0][0] == '2026-12' and hist >= 1)
        verdicts.append(held and released)
    o = new_os(); clean_november(o); run(o, 'card_preparation')
    lost = tx('Z9', '2026-11-20', '9.00'); lost['supersedes'] = CARD + ':NOT-THERE'
    rows = [tx('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), lost]
    o.intake(PREP, packet('unresolved', [lost, rc('Z9', '2026-11-20', '9.00'), stmt(rows)])); run(o, 'card_preparation')
    z = gov(o, CARD + ':Z9'); print('    supersedes an unknown key:', brief(z))
    forced = show('disposition on the unresolved transition', dispose(o, CARD + ':Z9', 'SOURCE_TRANSITION_UNRESOLVED', 'settlement_verified'))
    unresolved = 'SOURCE_TRANSITION_UNRESOLVED' in z['blockers'] and not z['eligible'] and forced[0] == 'refused'
    return 'OK' if all(verdicts) and unresolved else 'WEAK'


@probe('A02', 'RV-02', 'one origin, one owner: the conflict survives revision, re-citation and supersession of the cited source')
def _():
    os_ = new_os()
    clean_november(os_); run(os_, 'card_preparation')
    ref = lambda key: [e for e in gov(os_, key)['payload']['data']['evidence'] if e['source_key'] == key][0]
    mk = lambda r: journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '40.00', '0.00', None), ('DEMO_CARD_LIABILITY', '0.00', '40.00', None)], ['sup1'], origin_sources=[r])
    free = journal('J2', '2026-11-14', [('DEMO_REPAIRS', '11.00', '0.00', None), ('DEMO_CASH', '0.00', '11.00', None)], ['sup2'])
    os_.intake(PREP, packet('j', [mk(ref(CARD + ':A1')), doc('sup1', 'journal_support', journal_keys=['J1']), free, doc('sup2', 'journal_support', journal_keys=['J2'])]))
    both = lambda: (run(os_, 'card_preparation'), run(os_, 'journal_preparation'))
    both(); s1 = (gov(os_, CARD + ':A1')['blockers'], gov(os_, 'J1')['blockers'], bool(gov(os_, 'J2')['eligible']), bool(gov(os_, CARD + ':A2')['eligible']))
    print('    journal cites the card source -> card:', s1[0], '| journal:', s1[1], '| uninvolved journal and card item eligible:', s1[2], s1[3])
    os_.intake(PREP, packet('rev', [tx('A1', '2026-11-03', '40.00', desc='Acme  Paper  Demo')])); both()
    s2 = (gov(os_, CARD + ':A1')['blockers'], gov(os_, 'J1')['blockers'])
    print('    card source revised -> card:', s2[0], '| journal:', s2[1])
    os_.intake(PREP, packet('recite', [mk(ref(CARD + ':A1'))])); both()
    s3 = (gov(os_, CARD + ':A1')['blockers'], gov(os_, 'J1')['blockers'])
    print('    journal re-supplied against the current version -> card:', s3[0], '| journal:', s3[1])
    newkey = tx('A1N', '2026-11-03', '40.00'); newkey['supersedes'] = CARD + ':A1'
    rows = [newkey, tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('newkey', [newkey, rc('A1N', '2026-11-03', '40.00'), stmt(rows)])); both()
    s4 = (gov(os_, CARD + ':A1'), gov(os_, CARD + ':A1N')['blockers'], gov(os_, 'J1')['blockers'])
    print('    card source superseded under a new key -> old item:', s4[0], '| new item:', s4[1], '| journal:', s4[2])
    approvals = [review(os_, REV, gov(os_, CARD + ':A1N'), 'approve')[0], review(os_, REV, gov(os_, 'J1'), 'approve')[0]]
    void = mk(ref(CARD + ':A1N')); void.update(tombstone=True, removal_reason='voided')
    os_.intake(PREP, packet('void', [void])); both()
    s5 = (gov(os_, 'J1'), gov(os_, CARD + ':A1N')['blockers'])
    print('    approvals attempted while in conflict:', approvals, '| after the journal is withdrawn -> journal:', s5[0], '| card:', s5[1])
    C = 'SOURCE_ALREADY_HAS_ENTRY'
    ok = (C in s1[0] and C in s1[1] and s1[2] and s1[3] and C in s2[0] and C in s2[1] and 'ORIGIN_SOURCE_SUPERSEDED' in s2[1]
          and C in s3[0] and C in s3[1] and 'ORIGIN_SOURCE_SUPERSEDED' not in s3[1] and s4[0] is None and C in s4[1] and C in s4[2] and 'ORIGIN_SOURCE_SUPERSEDED' in s4[2]
          and approvals == ['refused', 'refused'] and s5[0] is None and C not in s5[1])
    return 'OK' if ok else 'WEAK'


@probe('A05', 'RV-05', 'a withdrawn mapping retires only on independent approval, from the effective date; history and reintroduction work')
def _():
    os_ = new_os(periods=(NOV, DEC))
    nov = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('M1', '2026-11-20', '60.00', desc='METRO REPAIR DEMO'), rc('M1', '2026-11-20', '60.00', vendor='METRO REPAIR DEMO')]
    dec = [tx('M2', '2026-12-05', '30.00', desc='METRO REPAIR DEMO'), rc('M2', '2026-12-05', '30.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('nov', nov + [stmt(nov)])); os_.intake(PREP, packet('dec', dec + [stmt(dec, DEC, opening='100.00')]))
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'probe-v2-without-metro'; p2['vendors'] = [v for v in p2['vendors'] if v['id'] != 'demo_metro']
    sid2 = os_.onboard(PREP, p2, effective_from='2026-12-01')
    both = lambda: (run(os_, 'card_preparation', '2026-11'), run(os_, 'card_preparation', '2026-12'))
    both(); pre = (bool(gov(os_, CARD + ':M1', '2026-11')['eligible']), bool(gov(os_, CARD + ':M2', '2026-12')['eligible']))
    metro = lambda: [r for r in os_.state(PREP)['rules'] if r['kind'] == 'vendor_mapping' and r['rule_key'] == 'demo_metro']
    print('    withdrawal only proposed -> November and December Metro eligible:', pre, '| Metro rule effective end:', [r['effective_end'] for r in metro()])
    os_.grant_authority(ADMIN, PREP.id, ['approve_profile', 'approve_rule'], 'probe: proposer holds the grants, to isolate the proposer check')
    own = show('proposer approves own withdrawal', attempt(os_.approve_profile_version, human(PREP.id, 'reviewer'), sid2, 'x'))
    os_.approve_profile_version(CTRL, sid2, 'probe: withdraw Metro from December'); both()
    m1, m2 = gov(os_, CARD + ':M1', '2026-11'), gov(os_, CARD + ':M2', '2026-12')
    retired = [(r['rule_id'], r['effective_to'], r['actor']) for r in os_.export(PREP)['rule_retirements']]
    print('    approved, effective 1 December -> November M1:', brief(m1), m1['payload']['data']['vendor'], '| December M2:', m2['blockers'])
    print('    retirements (rule, effective_to, approver):', retired, '| rule record effective end:', [r['effective_end'] for r in metro()])
    p3 = copy.deepcopy(PROFILE); p3['version'] = 'probe-v3-metro-again'
    sid3 = os_.onboard(PREP, p3, effective_from='2026-12-15'); os_.approve_profile_version(CTRL2, sid3, 'probe: reintroduce Metro from 15 December')
    more = dec + [tx('M3', '2026-12-20', '35.00', desc='METRO REPAIR DEMO'), rc('M3', '2026-12-20', '35.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('dec2', more[2:] + [stmt(more, DEC, opening='100.00')])); both(); accept_statement_revision(os_,CARD+':M3','2026-12')
    m2b, m3 = gov(os_, CARD + ':M2', '2026-12'), gov(os_, CARD + ':M3', '2026-12')
    print('    reintroduced from 15 December -> M2 (5 Dec):', m2b['blockers'], '| M3 (20 Dec):', brief(m3), m3['payload']['data']['vendor'])
    ok = (pre == (True, True) and own[0] == 'refused' and m1['eligible'] and m1['payload']['data']['vendor']['id'] == 'demo_metro' and 'UNKNOWN_VENDOR' in m2['blockers']
          and retired and all(r[1] == '2026-11-30' and r[2] == CTRL.id for r in retired) and 'UNKNOWN_VENDOR' in m2b['blockers'] and m3['eligible'] and m3['payload']['data']['vendor']['id'] == 'demo_metro')
    return 'OK' if ok else 'WEAK'


@probe('A06', 'RV-06', 'untyped checklist entries are refused; labels do not satisfy reconciliation or tie-out lines')
def _():
    os_ = new_os()
    bad = copy.deepcopy(PROFILE); bad['version'] = 'probe-untyped'; bad['required_close_evidence'] = ['bank_reconciliation']
    r1 = show('profile with an untyped checklist entry', attempt(os_.onboard, PREP, bad))
    r2 = show('close_checklist rule with an untyped entry', attempt(os_.propose_rule, PREP, 'close_checklist', 'close', ['bank_reconciliation'], '2026-11-01'))
    labels = ['trial_balance', 'card_statement', 'bank_reconciliation', 'ap_tieout', 'ar_tieout']
    clean_november(os_, extra=[doc('label-' + t, t, content='Fictional label-only document; nothing was reconciled') for t in labels])
    run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    run(os_, 'close_readiness'); c = gov(os_, 'close-checklist', kinds=None)
    res = [(r['requirement']['type'], r['requirement'].get('document_type'), r['satisfied']) for r in c['payload']['data']['requirements']]
    print('    shipped checklist with label-only documents:', res); print('    blockers:', c['blockers'])
    ok = (r1[0] == 'refused' and r2[0] == 'refused' and ('reconciliation', 'bank_reconciliation', False) in res and ('tieout', 'ap_tieout', False) in res and ('tieout', 'ar_tieout', False) in res
          and all(x in c['blockers'] for x in ('MISSING_CLOSE_EVIDENCE', 'FINAL_CLOSE_SIGNOFF_REQUIRED', 'EXTERNAL_STEPS_UNVERIFIED')) and not c['eligible'])
    return 'OK' if ok else 'WEAK'


@probe('A07', 'RV-07', 'dispositions obey activity and account type; valid credit, settlement, transfer, fee and interest paths still work')
def _():
    os_ = new_os()
    def pair(sid, date, amount, desc, activity):
        return [tx(sid, date, amount, desc=desc, activity=activity), rc(sid, date, amount, vendor=desc)]
    rows = (pair('PAY', '2026-11-12', '-300.00', 'CARD PAYMENT DEMO', 'payment') + pair('FEE', '2026-11-13', '12.00', 'ANNUAL FEE DEMO', 'fee') + pair('INT', '2026-11-14', '3.00', 'INTEREST DEMO', 'interest')
            + pair('CR', '2026-11-15', '-42.50', 'ACME PAPER DEMO', 'credit') + pair('UNK', '2026-11-16', '5.00', 'MYSTERY DEMO', 'unknown') + pair('TRF', '2026-11-17', '100.00', 'BALANCE TRANSFER DEMO', 'transfer')
            + pair('A1', '2026-11-03', '40.00', 'ACME PAPER DEMO', 'purchase') + pair('UV', '2026-11-18', '8.00', 'NOBODY KNOWN DEMO', 'purchase'))
    os_.intake(PREP, packet('mix', rows + [stmt(rows)])); run(os_, 'card_preparation')
    K = lambda k: CARD + ':' + k
    print('    before:', {k: gov(os_, K(k))['blockers'] for k in ('PAY', 'FEE', 'INT', 'CR', 'UNK', 'TRF')})
    exp, cash, liab = {'account_id': 'DEMO_OFFICE_SUPPLIES'}, {'cash_account': 'DEMO_CASH'}, 'DEMO_CARD_LIABILITY'
    N = 'NON_EXPENSE_REQUIRES_REVIEW'
    neg = {
        'payment as standalone credit': dispose(os_, K('PAY'), N, 'standalone_credit', exp), 'payment vendor confirmed to expense': dispose(os_, K('PAY'), 'UNKNOWN_VENDOR', 'confirm_vendor', exp),
        'payment coded to expense': dispose(os_, K('PAY'), 'UNKNOWN_CATEGORY', 'code_category', exp), 'payment coded as fee': dispose(os_, K('PAY'), N, 'code_fee', exp),
        'settlement against the liability itself': dispose(os_, K('PAY'), N, 'settlement_of_card_liability', {'cash_account': liab}), 'settlement against an expense account': dispose(os_, K('PAY'), N, 'settlement_of_card_liability', {'cash_account': 'DEMO_OFFICE_SUPPLIES'}),
        'fee coded to cash': dispose(os_, K('FEE'), N, 'code_fee', {'account_id': 'DEMO_CASH'}), 'fee coded to the liability': dispose(os_, K('FEE'), N, 'code_fee', {'account_id': liab}),
        'fee as settlement': dispose(os_, K('FEE'), N, 'settlement_of_card_liability', cash), 'fee as interest': dispose(os_, K('FEE'), N, 'code_interest', exp), 'interest as fee': dispose(os_, K('INT'), N, 'code_fee', exp),
        'credit to cash': dispose(os_, K('CR'), 'CREDIT_REQUIRES_REVIEW', 'standalone_credit', {'account_id': 'DEMO_CASH'}), 'unknown activity coded as fee': dispose(os_, K('UNK'), N, 'code_fee', exp),
        'unknown activity as credit': dispose(os_, K('UNK'), N, 'standalone_credit', exp), 'transfer as settlement': dispose(os_, K('TRF'), N, 'settlement_of_card_liability', cash),
        'transfer against the liability': dispose(os_, K('TRF'), N, 'transfer', {'cash_account': liab}), 'unknown activity coded to cash': dispose(os_, K('UNK'), 'UNKNOWN_CATEGORY', 'code_category', {'account_id': 'DEMO_CASH'}),
        'purchase coded to cash': dispose(os_, K('UV'), 'UNKNOWN_CATEGORY', 'code_category', {'account_id': 'DEMO_CASH'}), 'purchase coded to the card liability': dispose(os_, K('UV'), 'UNKNOWN_CATEGORY', 'code_category', {'account_id': liab}),
        'purchase vendor confirmed to cash': dispose(os_, K('UV'), 'UNKNOWN_VENDOR', 'confirm_vendor', {'account_id': 'DEMO_CASH'})}
    for k, v in neg.items():
        print('    refused? %-42s %s' % (k, v))
    pos = {'payment settled': dispose(os_, K('PAY'), N, 'settlement_of_card_liability', cash), 'credit as standalone credit': dispose(os_, K('CR'), 'CREDIT_REQUIRES_REVIEW', 'standalone_credit', exp),
           'transfer': dispose(os_, K('TRF'), N, 'transfer', cash), 'fee': dispose(os_, K('FEE'), N, 'code_fee', exp), 'fee vendor': dispose(os_, K('FEE'), 'UNKNOWN_VENDOR', 'confirm_vendor', exp), 'fee category': dispose(os_, K('FEE'), 'UNKNOWN_CATEGORY', 'code_category', exp),
           'interest': dispose(os_, K('INT'), N, 'code_interest', exp), 'interest vendor': dispose(os_, K('INT'), 'UNKNOWN_VENDOR', 'confirm_vendor', exp), 'interest category': dispose(os_, K('INT'), 'UNKNOWN_CATEGORY', 'code_category', exp),
           'unknown referred': dispose(os_, K('UNK'), N, 'refer_external'),
           'purchase vendor confirmed': dispose(os_, K('UV'), 'UNKNOWN_VENDOR', 'confirm_vendor', exp), 'purchase coded to expense': dispose(os_, K('UV'), 'UNKNOWN_CATEGORY', 'code_category', exp)}
    print('    accepted:', {k: v[0] for k, v in pos.items()})
    run(os_, 'card_preparation')
    got = {k: gov(os_, K(k)) for k in ('PAY', 'FEE', 'INT', 'CR', 'UNK', 'TRF', 'UV')}
    for k, a in got.items():
        print('    %-4s eligible=%-5s blockers=%s entry=%s' % (k, bool(a['eligible']), a['blockers'], lines_of(a)))
    approve = [review(os_, REV, got[k], 'approve')[0] for k in ('PAY', 'CR', 'TRF', 'FEE', 'INT')] + [review(os_, REV, got['UNK'], 'approve')[0]]
    print('    independent approval of PAY, CR, TRF, FEE, INT, then the referred UNK:', approve)
    ok = (all(v[0] == 'refused' for v in neg.values()) and all(v[0] == 'ok' for v in pos.values())
          and lines_of(got['PAY']) == [('DEMO_CARD_LIABILITY', '300.00', '0.00'), ('DEMO_CASH', '0.00', '300.00')]
          and lines_of(got['CR']) == [('DEMO_CARD_LIABILITY', '42.50', '0.00'), ('DEMO_OFFICE_SUPPLIES', '0.00', '42.50')]
          and lines_of(got['TRF']) == [('DEMO_CARD_LIABILITY', '0.00', '100.00'), ('DEMO_CASH', '100.00', '0.00')]
          and lines_of(got['FEE']) == [('DEMO_CARD_LIABILITY', '0.00', '12.00'), ('DEMO_OFFICE_SUPPLIES', '12.00', '0.00')]
          and lines_of(got['INT']) == [('DEMO_CARD_LIABILITY', '0.00', '3.00'), ('DEMO_OFFICE_SUPPLIES', '3.00', '0.00')]
          and lines_of(got['UV']) == [('DEMO_CARD_LIABILITY', '0.00', '8.00'), ('DEMO_OFFICE_SUPPLIES', '8.00', '0.00')]
          and not got['UNK']['eligible'] and approve == ['ok'] * 5 + ['refused'])
    return 'OK' if ok else 'WEAK'


@probe('A08', 'RV-08/RV-15', 'distinct purchases needs every candidate receipt, binds the exact candidate set, and lapses when a new candidate arrives')
def _():
    os_, rows = duplicate_pair()
    d1 = gov(os_, CARD + ':D1'); ev = d1['payload']['data']['evidence']
    own_row = [e for e in ev if e['source_key'] == CARD + ':D1']; own_rc = [e for e in ev if e['source_key'] == 'receipt-D1']
    peer_rc = [e for e in d1['payload']['data']['duplicate_evidence'] if e['source_key'] == 'receipt-D2']
    neg = {'own row only': dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own_row),
           'own row and own receipt, no candidate receipt': dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own_row + own_rc),
           'candidate receipt only': dispose(os_, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=peer_rc)}
    for k, v in neg.items():
        show('distinct purchases citing ' + k, v)
    first = [dispose(os_, CARD + ':' + k, 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=[e for e in support(gov(os_, CARD + ':' + k), True) if not e['source_key'].startswith('stmt')]) for k in ('D1', 'D2')]
    assert all(f[0] == 'ok' for f in first), ('valid distinct-purchases setup must be accepted', first)
    run(os_, 'card_preparation'); start = gov(os_, CARD + ':D1')
    assert start['eligible'], ('D1 must be eligible before the third charge arrives', brief(start))
    bound = [d for d in os_.state(PREP)['dispositions'] if d['id'] == first[0][1]][0]
    print('    D1 after two supported decisions (no statement cited):', brief(start), '| bound candidate set:', [c['source_key'] for c in json.loads(bound['payload'])['duplicate_candidate_set']])
    third = [tx('D3', '2026-11-06', '90.00'), rc('D3', '2026-11-06', '90.00', content='Fictional receipt three')]
    os_.intake(PREP, packet('third', third + [stmt(rows + third)])); run(os_, 'card_preparation')
    d1b, d2b, d3 = (gov(os_, CARD + ':' + k) for k in ('D1', 'D2', 'D3'))
    print('    after a third identical charge -> D1:', brief(d1b), '| D2:', d2b['blockers'], '| D3:', d3['blockers'])
    ok = all(v[0] == 'refused' for v in neg.values()) and not d1b['eligible'] and 'POSSIBLE_DUPLICATE' in d1b['blockers'] and 'POSSIBLE_DUPLICATE' in d2b['blockers'] and 'POSSIBLE_DUPLICATE' in d3['blockers']
    return 'OK' if ok else 'WEAK'


@probe('A09', 'RV-09', 'excluding a duplicate frees the surviving charge with full lineage; revocation restores both holds and the earlier rejection')
def _():
    os_, rows = duplicate_pair()
    first = gov(os_, CARD + ':D1')
    rej = show('reject the held D1 artifact', review(os_, REV, first, 'reject'))
    ex = show('D2 dispositioned as duplicate_of D1', dispose(os_, CARD + ':D2', 'POSSIBLE_DUPLICATE', 'duplicate_of', {'duplicate_of': CARD + ':D1'}))
    run(os_, 'card_preparation'); d1, d2 = gov(os_, CARD + ':D1'), gov(os_, CARD + ':D2')
    print('    excluded D2:', brief(d2), '| entry:', lines_of(d2)); print('    surviving D1:', brief(d1), '| cites dispositions:', d1['payload']['data']['disposition_ids'], '| contributors:', d1['contributors'])
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'probe: dispositioner also holds review, to isolate the independence check')
    own = show('the person who excluded D2 approves D1', review(os_, DISP, d1, 'approve'))
    ind = show('independent reviewer approves D1 (positive control)', review(os_, REV2, d1, 'approve'))
    show('revoke the exclusion', attempt(os_.revoke_disposition, DISP, ex[1], 'probe revoke')); run(os_, 'card_preparation')
    d1r, d2r = gov(os_, CARD + ':D1'), gov(os_, CARD + ':D2')
    print('    after revocation -> D1:', brief(d1r), '| same artifact as the first, rejected one:', d1r['id'] == first['id'], '| current:', d1r['current'], '| D2:', brief(d2r))
    ok = (rej[0] == 'ok' and ex[0] == 'ok' and not d2['eligible'] and 'DUPLICATE_EXCLUDED' in d2['blockers'] and lines_of(d2) is None
          and d1['eligible'] and ex[1] in d1['payload']['data']['disposition_ids'] and DISP.id in d1['contributors'] and own[0] == 'refused' and ind[0] == 'ok'
          and 'POSSIBLE_DUPLICATE' in d1r['blockers'] and 'POSSIBLE_DUPLICATE' in d2r['blockers'] and d1r['id'] == first['id'] and d1r['review_status'] == 'reject' and d1r['current'])
    return 'OK' if ok else 'WEAK'


@probe('A10', 'RV-10', 'a cosmetic re-proposal keeps the earlier rule author in the item lineage; a different historical category does not')
def _():
    def setup(v1_author, v1, v2, link=True, kind='vendor_mapping', key='demo_acme'):
        p = copy.deepcopy(PROFILE); p['vendors'] = [v for v in p['vendors'] if v['id'] != 'demo_acme']
        o = new_os(profile=p)
        r1 = o.propose_rule(human(v1_author.id, 'preparer'), kind, key, v1, '2026-11-01'); o.approve_rule(CTRL, r1, 'probe approval of version 1')
        r2 = o.propose_rule(PREP, kind, key, v2, '2026-11-01', supersedes=r1 if link else None); o.approve_rule(CTRL2, r2, 'probe approval of version 2')
        if kind != 'vendor_mapping':
            acme = {'id': 'demo_acme', 'name': 'Acme Paper Demo', 'aliases': ['ACME PAPER DEMO'], 'category': 'DEMO_OFFICE_SUPPLIES'}
            o.approve_rule(CTRL, o.propose_rule(PREP2, 'vendor_mapping', 'demo_acme', acme, '2026-11-01'), 'probe mapping')
        clean_november(o); run(o, 'card_preparation'); a = gov(o, CARD + ':A1')
        assert a['eligible'], ('item must be eligible for the review attempt to mean anything', brief(a))
        return o, a
    base = {'id': 'demo_acme', 'name': 'Acme Paper Demo', 'aliases': ['ACME PAPER DEMO'], 'category': 'DEMO_OFFICE_SUPPLIES'}
    o, a = setup(REV, base, dict(base, name='Acme Paper Demo.'))
    linked = show('cosmetic re-proposal linked by supersedes: author of version 1 approves', review(o, REV, a, 'approve'))
    o, a = setup(REV, base, dict(base, name='Acme Paper Demo.'), link=False)
    print('    contributors without the supersedes link:', a['contributors'])
    unlinked = show('same cosmetic re-proposal with no supersedes link: author of version 1 approves', review(o, REV, a, 'approve'))
    o, a = setup(REV3, dict(base, category='DEMO_REPAIRS'), base)
    different = show('version 1 had a different category: its author approves (should be allowed)', review(o, REV3, a, 'approve'))
    rm = {'date_window_days': 1, 'amount_tolerance': None, 'multiple_receipts': None, 'vendor_method': None, 'statement_substitution': None}
    o, a = setup(REV4, rm, dict(rm), kind='receipt_matching', key='default')
    policy = show('identical receipt policy re-proposed by a colleague: author of version 1 approves', review(o, REV4, a, 'approve'))
    ok = linked[0] == 'refused' and unlinked[0] == 'refused' and different[0] == 'ok' and policy[0] == 'refused'
    return 'OK' if ok else 'WEAK'


@probe('A11', 'RV-11', 'freshness must be stated and well formed; explicit no-evidence authority is independently approved and audited')
def _():
    os_ = new_os(); clean_november(os_)
    mk = lambda f: attempt(os_.create_mandate, PREP, ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-18T00:00:00+00:00', 86400, 2, {'kind': 'fixed', 'period_id': '2026-11'}, f)
    neg = {'empty': mk({}), 'none with empty reason': mk({'none': ''}), 'none with blank reason': mk({'none': '   '}), 'none mixed with a kind': mk({'none': 'r', 'transaction': 'occurrence_start'}),
           'kind the workflow does not read': mk({'journal': 'occurrence_start'}), 'malformed cut-off': mk({'transaction': 'yesterday'}), 'not a mapping': mk(None), 'a list': mk(['transaction'])}
    for k, v in neg.items():
        print('    refused? %-34s %s' % (k, v))
    made = mk(NO_EVIDENCE); assert made[0] == 'ok', made
    t0 = os_.tick(PREP, '2026-11-15T06:00:00+00:00')
    os_.grant_authority(ADMIN, PREP.id, ['approve_mandate'], 'probe: issuer holds the grant, to isolate the issuer check')
    own = show('issuer approves own no-evidence mandate', attempt(os_.approve_mandate, human(PREP.id, 'reviewer'), made[1], 'x'))
    os_.approve_mandate(CTRL, made[1], 'probe: independent approval of fixed-evidence authority')
    audit = [json.loads(a['payload']) for a in os_.export(PREP)['audit_history'] if a['event'] == 'mandate_approved']
    t1 = os_.tick(PREP, '2026-11-15T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T12:00:00+00:00')
    runs = [(r['id'], r['status']) for r in os_.state(PREP)['runs'] if r['mandate_id']]
    print('    before approval -> runs:', t0, '| approval audit records freshness:', audit[-1].get('freshness') if audit else None, '| after approval -> runs:', runs)
    ok = all(v[0] == 'refused' for v in neg.values()) and t0 == [] and own[0] == 'refused' and audit and audit[-1].get('freshness') == NO_EVIDENCE and len(runs) == 1 and runs[0][1] in ('awaiting_review', 'prepared_with_exceptions')
    return 'OK' if ok else 'WEAK'


@probe('A12', 'RV-12', 'a revised receipt is disclosed and held; suppliers cannot accept it; acceptance lapses on a further change; referral never clears')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '39.99'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('b1', rows + [stmt(rows)])); run(os_, 'card_preparation')
    ref = show('refer the receipt mismatch externally', dispose(os_, CARD + ':A1', 'RECEIPT_AMOUNT_POLICY_UNSET', 'refer_external')); run(os_, 'card_preparation')
    a0 = gov(os_, CARD + ':A1'); print('    after referral:', brief(a0))
    os_.intake(PREP2, packet('b2', [rc('A1', '2026-11-03', '40.00')])); run(os_, 'card_preparation')
    a1 = gov(os_, CARD + ':A1'); revs = a1['payload']['data']['evidence_revisions']
    print('    receipt re-supplied by a colleague ->', brief(a1))
    print('    disclosed revisions:', [(r['source_key'], r['earlier']['version'], r['earlier']['supplier'], r['current']['version'], r['current']['supplier'], r['changed_fields']) for r in revs])
    for who in (PREP, PREP2):
        os_.grant_authority(ADMIN, who.id, ['disposition'], 'probe: supplier holds the grant, to isolate the supplier check')
    E, R = 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted'
    neg = {'supplier of version 1': dispose(os_, CARD + ':A1', E, R, who=human(PREP.id, 'reviewer')), 'supplier of version 2': dispose(os_, CARD + ':A1', E, R, who=human(PREP2.id, 'reviewer')),
           'reviewer without the disposition grant': dispose(os_, CARD + ':A1', E, R, who=REV),
           'acceptance that does not cite the revised receipt': dispose(os_, CARD + ':A1', E, R, evidence=[e for e in a1['payload']['data']['evidence'] if not e['source_key'].startswith('receipt')])}
    for k, v in neg.items():
        show('acceptance by ' + k, v)
    acc = show('acceptance by a granted human who supplied neither version', dispose(os_, CARD + ':A1', E, R)); run(os_, 'card_preparation')
    a2 = gov(os_, CARD + ':A1'); print('    after acceptance:', brief(a2), '| revisions still disclosed:', bool(a2['payload']['data']['evidence_revisions']))
    os_.grant_authority(ADMIN, DISP.id, ['review'], 'probe: accepter also holds review, to isolate the independence check')
    own = show('the accepter gives final review', review(os_, DISP, a2, 'approve')); ind = show('independent final review', review(os_, REV, a2, 'approve'))
    os_.intake(PREP, packet('b3', [rc('A1', '2026-11-03', '40.00', content='Fictional receipt, changed once more')])); run(os_, 'card_preparation')
    a3 = gov(os_, CARD + ':A1'); ev = [(e['code'], e['item_key']) for e in os_.state(PREP)['accounting_events']]
    print('    receipt changed again -> A1:', brief(a3), '| events:', ev)
    o2 = new_os()
    o2.intake(PREP, packet('j', [journal('J1', '2026-11-13', [('DEMO_OFFICE_SUPPLIES', '25.00', '0.00', None), ('DEMO_CASH', '0.00', '25.00', None)], ['sup1']), doc('sup1', 'journal_support', journal_keys=['J1'])])); run(o2, 'journal_preparation')
    j0 = gov(o2, 'J1'); o2.intake(PREP, packet('j2', [doc('sup1', 'journal_support', journal_keys=['J1'], content='Fictional support, reworded')])); run(o2, 'journal_preparation'); j1 = gov(o2, 'J1')
    print('    journal support revised -> before:', brief(j0)['eligible'], '| after:', j1['blockers'])
    ok = (ref[0] == 'ok' and not a0['eligible'] and 'RECEIPT_AMOUNT_POLICY_UNSET' in a0['blockers'] and a1['blockers'] == [E] and len(revs) == 1
          and revs[0]['earlier']['supplier'] == PREP.id and revs[0]['current']['supplier'] == PREP2.id and revs[0]['changed_fields'] == ['amount']
          and all(v[0] == 'refused' for v in neg.values()) and acc[0] == 'ok' and a2['eligible'] and a2['payload']['data']['evidence_revisions']
          and own[0] == 'refused' and ind[0] == 'ok' and E in a3['blockers'] and not a3['eligible'] and ('APPROVED_SOURCE_REVISED', CARD + ':A1') in ev
          and j0['eligible'] and E in j1['blockers'])
    return 'OK' if ok else 'WEAK'


@probe('A13', 'RV-13', 'statement assurance is disclosed; missing line ids need an approved exception; a missing or quarantined prior statement cannot pass')
def _():
    os_ = new_os()
    rows = [tx('S1', '2026-11-03', '40.00'), rc('S1', '2026-11-03', '40.00'), tx('S2', '2026-11-04', '60.00'), rc('S2', '2026-11-04', '60.00')]
    os_.intake(PREP, packet('nolines', rows + [stmt(rows, line_ids=False, provenance='manually_keyed')])); run(os_, 'card_preparation')
    s1 = gov(os_, CARD + ':S1'); wp = gov(os_, 'statement:' + CARD, kinds=None)['payload']['data']
    print('    no line ids ->', brief(s1)); print('    workpaper discloses:', {k: wp[k] for k in ('line_identity', 'opening_continuity', 'statement_provenance')})
    rid = os_.propose_rule(PREP, 'statement_policy', 'lines', {'allow_without_line_ids': True}, '2026-11-01', item_key='statement:' + CARD); run(os_, 'card_preparation')
    inert = gov(os_, CARD + ':S1')['blockers']
    os_.approve_rule(CTRL, rid, 'probe: synthetic exception for a statement without line identifiers'); run(os_, 'card_preparation'); s1b = gov(os_, CARD + ':S1')
    print('    exception proposed only:', inert, '| approved:', brief(s1b), '| item still says line identity:', s1b['payload']['data'].get('line_identity'))
    o2 = new_os(periods=(OCT, NOV))
    o2.intake(PREP, packet('nov', rows + [stmt(rows)])); run(o2, 'card_preparation', '2026-11')
    missing = gov(o2, CARD + ':S1', '2026-11')['blockers']; print('    October configured but no October statement on file:', missing)
    o3 = new_os(periods=(OCT, NOV))
    octr = [tx('O1', '2026-10-10', '500.00'), rc('O1', '2026-10-10', '500.00')]
    o3.intake(PREP, packet('oct', octr + [stmt(octr, OCT)])); run(o3, 'card_preparation', '2026-10'); review(o3, REV, gov(o3, CARD + ':O1', '2026-10'), 'approve')
    o3.lock_period(PADMIN, '2026-10', 'probe lock')
    o3.intake(PREP2, packet('oct-late', [stmt(octr, OCT, opening='-100.00')]))                 # late revision: closing becomes 400.00
    o3.intake(PREP, packet('nov-400', rows + [stmt(rows, opening='400.00')])); run(o3, 'card_preparation', '2026-11')
    q = gov(o3, CARD + ':S1', '2026-11'); late = [(e['source_key'], e['reason']) for e in o3.state(PREP)['source_exceptions']]
    print('    late October revision quarantined:', late, '| November opening 400.00 against the frozen 500.00:', q['blockers'])
    o3.intake(PREP, packet('nov-500', [stmt(rows, opening='500.00')])); run(o3, 'card_preparation', '2026-11'); good = gov(o3, CARD + ':S1', '2026-11')
    print('    November opening 500.00 (positive control):', brief(good), good['payload']['data'].get('opening_continuity'))
    ok = ('STATEMENT_LINE_IDENTITY_NOT_VERIFIED' in s1['blockers'] and wp['line_identity'] == 'not_supplied' and wp['statement_provenance']['provenance'] == 'manually_keyed'
          and wp['statement_provenance']['supplier'] == PREP.id and wp['statement_provenance']['independent_verification'] == 'not_performed'
          and 'STATEMENT_LINE_IDENTITY_NOT_VERIFIED' in inert and s1b['eligible'] and s1b['payload']['data'].get('line_identity') == 'not_supplied'
          and 'STATEMENT_PRIOR_PERIOD_MISSING' in missing and ('stmt-2026-10', 'LATE_ACTIVITY_IN_LOCKED_PERIOD') in late and 'STATEMENT_OPENING_BALANCE_BREAK' in q['blockers']
          and 'STATEMENT_OPENING_BALANCE_BREAK' not in good['blockers'] and good['payload']['data'].get('opening_continuity') == 'verified')
    return 'OK' if ok else 'WEAK'


@probe('A14', 'RV-14/RV-15', 'the rule record shows normalised aliases, collisions, status and effective end; own-row evidence is refused')
def _():
    os_ = new_os()
    rid = os_.propose_rule(PREP, 'vendor_mapping', 'demo_other', {'id': 'demo_other', 'name': 'Other vendor (fictional)', 'aliases': ['ACME-PAPER/DEMO'], 'category': 'DEMO_REPAIRS'}, '2026-11-01')
    rec = [r for r in os_.state(CTRL)['rules'] if r['id'] == rid][0]
    acme = [r['id'] for r in os_.state(CTRL)['rules'] if r['kind'] == 'vendor_mapping' and r['rule_key'] == 'demo_acme']
    print('    proposed rule as the approver sees it:', {k: rec.get(k) for k in ('status', 'normalized_aliases', 'alias_collisions', 'effective_end', 'approved_by')}, '| Acme rule ids:', acme)
    clean_november(os_, extra=[tx('U1', '2026-11-07', '5.00', desc='NOBODY KNOWN DEMO'), rc('U1', '2026-11-07', '5.00', vendor='NOBODY KNOWN DEMO')]); run(os_, 'card_preparation')
    u1 = gov(os_, CARD + ':U1'); own = [e for e in u1['payload']['data']['evidence'] if e['source_key'] == CARD + ':U1']
    r1 = show('confirm_vendor citing only the item\'s own row', dispose(os_, CARD + ':U1', 'UNKNOWN_VENDOR', 'confirm_vendor', {'account_id': 'DEMO_OFFICE_SUPPLIES'}, evidence=own))
    other_row = [e for e in gov(os_, CARD + ':A1')['payload']['data']['evidence'] if e['source_key'] == CARD + ':A1']
    r2 = show('confirm_vendor citing only another item\'s transaction row', dispose(os_, CARD + ':U1', 'UNKNOWN_VENDOR', 'confirm_vendor', {'account_id': 'DEMO_OFFICE_SUPPLIES'}, evidence=own + other_row))
    ok = rec.get('status') == 'proposed' and rec.get('normalized_aliases') == ['acme paper demo'] and set(rec.get('alias_collisions') or []) == set(acme) and rec.get('effective_end') == '9999-12-31' and r1[0] == 'refused'
    if ok and r2[0] == 'ok':
        print('    observation: a row belonging to a different item counts as supporting evidence for this one')
        return 'NOTE'
    return 'OK' if ok else 'WEAK'


@probe('A17', 'RV-17', 'a second package names the one it replaces; one package governs; the first stays byte-identical; acknowledgement cannot clear stale work')
def _():
    os_ = new_os()
    clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    p1 = os_.finalize_package(FIN, '2026-11', 'card_preparation', 'probe handover one'); first = [p for p in os_.state(PREP)['packages'] if p['id'] == p1][0]
    more = [tx('A3', '2026-11-08', '9.00'), rc('A3', '2026-11-08', '9.00')]
    base = [tx('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('more', more + [stmt(base + more)]))
    stale = show('finalize again while every item is stale, with acknowledgement', attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'x', 'acknowledged'))
    run(os_, 'card_preparation')
    for item in ('A1','A2','A3'):accept_statement_revision(os_,CARD+':'+item)
    for k in ('A1', 'A2', 'A3'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    p2 = os_.finalize_package(FIN, '2026-11', 'card_preparation', 'probe handover two')
    pk = os_.export(PREP)['packages']
    view = [(p['id'], p['governing'], p['supersedes_package_id'], json.loads(p['payload'])['supersedes_package_id']) for p in pk]
    same = [p for p in pk if p['id'] == p1][0]
    print('    packages (id, governing, supersedes in record, supersedes in frozen payload):', view, '| first package bytes unchanged:', same['payload'] == first['payload'] and same['hash'] == first['hash'])
    ok = stale[0] == 'refused' and view == [(p1, False, None, None), (p2, True, p1, p1)] and same['payload'] == first['payload'] and same['hash'] == first['hash'] and json.loads(same['payload'])['authority'] == 'preparation_only_not_external_close'
    return 'OK' if ok else 'WEAK'


# ---------------------------------------------------------------------------------------
# Part 2. Routes around the corrections
# ---------------------------------------------------------------------------------------

@probe('X01', 'RV-01', 'a second supersession step does not release a charge that is still quarantined behind a locked origin')
def _():
    os_ = new_os(periods=(NOV, DEC))
    clean_november(os_); run(os_, 'card_preparation')
    for k in ('A1', 'A2'):
        review(os_, REV, gov(os_, CARD + ':' + k), 'approve')
    os_.lock_period(PADMIN, '2026-11', 'probe lock')
    step1 = tx('A1X', '2026-12-02', '40.00'); step1['supersedes'] = CARD + ':A1'
    os_.intake(PREP2, packet('step-1', [step1, rc('A1X', '2026-12-02', '40.00')]))
    step2 = tx('A1Y', '2026-12-03', '40.00'); step2['supersedes'] = CARD + ':A1X'
    rows = [step2, rc('A1Y', '2026-12-03', '40.00')]
    os_.intake(PREP2, packet('step-2', rows + [stmt(rows, DEC, opening='100.00')])); run(os_, 'card_preparation', '2026-12', PREP2)
    st = os_.state(PREP)
    y, nov = gov(os_, CARD + ':A1Y', '2026-12'), gov(os_, CARD + ':A1', '2026-11')
    print('    source exceptions:', sorted((e['source_key'], e['period_id'], e['reason']) for e in st['source_exceptions']))
    print('    December A1Y (supersedes A1X, which supersedes locked A1):', brief(y), '| November A1:', nov['review_status'])
    print('    heads now marked removed:', sorted(s['source_key'] for s in os_.export(PREP)['evidence_history'] if s['source_key'] in (CARD + ':A1X', 'receipt-A1X')), '| moves recorded:', [(m['from_period_id'], m['to_period_id'], m['blocked']) for m in os_.export(PREP)['source_move_history']])
    if y is None:
        return 'OK'
    d = show('settlement_verified citing everything the artifact lists, predecessors included', dispose(os_, CARD + ':A1Y', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', period='2026-12'))
    run(os_, 'card_preparation', '2026-12', PREP2); inert = gov(os_, CARD + ':A1Y', '2026-12')
    print('    after that disposition:', brief(inert), '(accepted but without effect)' if d[0] == 'ok' and 'SOURCE_TRANSITION_REQUIRES_REVIEW' in inert['blockers'] else '')
    current_only = [e for e in inert['payload']['data']['evidence'] if 'link_id' not in e]
    d2 = show('settlement_verified citing current sources only', dispose(os_, CARD + ':A1Y', 'SOURCE_TRANSITION_REQUIRES_REVIEW', 'settlement_verified', evidence=current_only, period='2026-12'))
    run(os_, 'card_preparation', '2026-12', PREP2); y2 = gov(os_, CARD + ':A1Y', '2026-12')
    print('    after the transition is dispositioned:', brief(y2), '| entry:', lines_of(y2))
    appr = show('independent approval of December A1Y', review(os_, REV2, y2, 'approve'))
    both = appr[0] == 'ok' and gov(os_, CARD + ':A1', '2026-11')['review_status'] == 'approve'
    print('    A1Y admitted to December while A1 is approved in locked November: True | approved in both periods:', both)
    return 'WEAK'


@probe('X09', 'RV-08/RV-09', 'an exclusion does not outlive the charge it pointed to, and two charges cannot both be excluded unseen')
def _():
    os_, rows = duplicate_pair()
    dispose(os_, CARD + ':D2', 'POSSIBLE_DUPLICATE', 'duplicate_of', {'duplicate_of': CARD + ':D1'}); run(os_, 'card_preparation')
    gone = [dict(copy.deepcopy(rows[0]), tombstone=True, removal_reason='voided'), dict(copy.deepcopy(rows[1]), tombstone=True, removal_reason='voided')]
    os_.intake(PREP, packet('void-d1', gone + [stmt(rows[2:])])); run(os_, 'card_preparation'); accept_statement_revision(os_,CARD+':D2')
    d2 = gov(os_, CARD + ':D2'); print('    D2 was excluded as a duplicate of D1; D1 is then voided -> D2:', brief(d2), '| entry:', lines_of(d2))
    restored = d2['eligible'] and lines_of(d2) is not None
    o2, rows2 = duplicate_pair()
    a = dispose(o2, CARD + ':D2', 'POSSIBLE_DUPLICATE', 'duplicate_of', {'duplicate_of': CARD + ':D1'}); b = dispose(o2, CARD + ':D1', 'POSSIBLE_DUPLICATE', 'duplicate_of', {'duplicate_of': CARD + ':D2'})
    run(o2, 'card_preparation'); x1, x2 = gov(o2, CARD + ':D1'), gov(o2, CARD + ':D2')
    print('    each charge excluded as a duplicate of the other (%s, %s) -> D1: %s | D2: %s' % (a[0], b[0], brief(x1), brief(x2)))
    fin = attempt(o2.finalize_package, FIN, '2026-11', 'card_preparation', 'x')
    print('    finalize without acknowledgement:', fin)
    if not restored:
        return 'WEAK'
    if b[0] == 'ok' and lines_of(x1) is None and lines_of(x2) is None:
        visible = not x1['eligible'] and not x2['eligible'] and fin[0] == 'refused'
        print('    observation: both charges can be excluded, leaving no entry for either; both stay visibly held:', visible)
        return 'NOTE' if visible else 'WEAK'
    return 'OK'


@probe('X12k', 'RV-12', 'replacing a receipt under a new key is treated like revising it')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '39.99'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')]
    os_.intake(PREP, packet('b1', rows + [stmt(rows)])); run(os_, 'card_preparation')
    print('    receipt 39.99 against a 40.00 charge:', gov(os_, CARD + ':A1')['blockers'])
    old = dict(copy.deepcopy(rows[1]), tombstone=True, removal_reason='voided')
    os_.intake(PREP, packet('b2', [old, rc('A1', '2026-11-03', '40.00', key='receipt-A1-replacement', content='Fictional replacement receipt')])); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); d = a['payload']['data']
    print('    old receipt withdrawn, a new receipt key supplied at 40.00 ->', brief(a))
    print('    receipts relied on:', [(e['source_key'], e['version']) for e in d['evidence'] if e['source_key'].startswith('receipt')], '| revisions disclosed:', d.get('evidence_revisions'))
    appr = show('independent approval', review(os_, REV, a, 'approve'))
    return 'WEAK' if appr[0] == 'ok' and not d.get('evidence_revisions') else 'OK'


@probe('X12s', 'RV-12/RV-13', 'a statement re-supplied to agree with the population is disclosed as revised evidence')
def _():
    os_ = new_os()
    rows = [tx('A1', '2026-11-03', '40.00'), rc('A1', '2026-11-03', '40.00'), tx('A2', '2026-11-04', '60.00', desc='METRO REPAIR DEMO'), rc('A2', '2026-11-04', '60.00', vendor='METRO REPAIR DEMO')]
    wrong = stmt(rows, totals={'purchase': '90.00', 'credit': '0.00', 'payment': '0.00', 'fee': '0.00', 'interest': '0.00', 'transfer': '0.00', 'unknown': '0.00'}, closing_balance='90.00')
    os_.intake(PREP, packet('b1', rows + [wrong])); run(os_, 'card_preparation')
    print('    statement says purchases 90.00, population is 100.00:', gov(os_, CARD + ':A1')['blockers'])
    os_.intake(PREP, packet('b2', [stmt(rows)])); run(os_, 'card_preparation')
    a = gov(os_, CARD + ':A1'); d = a['payload']['data']; wp = gov(os_, 'statement:' + CARD, kinds=None)['payload']['data']
    print('    preparer re-supplies the statement at 100.00 ->', brief(a))
    print('    statement version relied on:', [(e['source_key'], e['version']) for e in d['evidence'] if e['source_key'].startswith('stmt')], '| revisions disclosed on the item:', d.get('evidence_revisions'), '| workpaper fields:', sorted(wp))
    disclosed = bool(d.get('evidence_revisions')) or any('revis' in k and wp[k] for k in wp) or any('revis' in k and d[k] for k in d)
    appr = show('independent approval', review(os_, REV, a, 'approve'))
    return 'WEAK' if appr[0] == 'ok' and not disclosed else 'OK'


@probe('X15', 'RV-15', 'the supplier of a candidate receipt cited in a distinct-purchases decision cannot review the item it supports')
def _():
    os_ = new_os()
    peer = human(REV3.id, 'preparer')                                  # the future reviewer supplies only the receipt of D2
    rows = [tx('D1', '2026-11-06', '90.00'), rc('D1', '2026-11-06', '90.00', content='Fictional receipt one'), tx('D2', '2026-11-06', '90.00')]
    os_.intake(PREP, packet('d', rows + [stmt(rows)])); os_.intake(peer, packet('d2rc', [rc('D2', '2026-11-06', '90.00', content='Fictional receipt two')]))
    run(os_, 'card_preparation')
    first = [dispose(os_, CARD + ':' + k, 'POSSIBLE_DUPLICATE', 'distinct_purchases') for k in ('D1', 'D2')]
    assert all(f[0] == 'ok' for f in first), first
    run(os_, 'card_preparation'); d1 = gov(os_, CARD + ':D1')
    assert d1['eligible'], brief(d1)
    print('    D1 contributors:', d1['contributors'])
    barred = show('supplier of the D2 receipt, which the D1 decision relies on, approves D1', review(os_, REV3, d1, 'approve'))
    free = show('uninvolved reviewer approves D1 (positive control)', review(os_, REV2, d1, 'approve'))
    return 'OK' if barred[0] == 'refused' and free[0] == 'ok' else 'WEAK'


# ---------------------------------------------------------------------------------------
# Part 3. Unverified concerns from the previous review
# ---------------------------------------------------------------------------------------

@probe('U1', 'UC-1', 'a mandate is not suspended merely because new evidence falls after a rule date that was already approved')
def _():
    os_ = new_os(periods=(NOV, DEC))
    rows = clean_november(os_)
    extra = {'id': 'demo_extra', 'name': 'Extra (fictional)', 'aliases': ['EXTRA VENDOR DEMO'], 'category': 'DEMO_REPAIRS'}
    os_.approve_rule(CTRL, os_.propose_rule(PREP2, 'vendor_mapping', 'demo_extra', extra, '2026-11-15'), 'probe: rule effective 15 November, approved before the mandate')
    mid = os_.create_mandate(PREP, ['card_preparation'], '2026-12-01T00:00:00+00:00', '2026-12-05T00:00:00+00:00', 86400, 3, {'kind': 'fixed', 'period_id': '2026-11'}, {'transaction': 'occurrence_start'})
    os_.approve_mandate(CTRL, mid, 'probe standing authority')
    fresh = [tx('A9', '2026-11-25', '12.00', as_of='2026-12-01T13:00:00+00:00'), rc('A9', '2026-11-25', '12.00')]
    os_.tick(PREP, '2026-12-01T12:00:00+00:00'); os_.intake(PREP, packet('fresh', fresh + [stmt(rows + fresh)])); os_.drain(WORKER)
    m = [x for x in os_.state(PREP)['mandates'] if x['id'] == mid][0]; runs = [(r['id'], r['status']) for r in os_.state(PREP)['runs'] if r['mandate_id']]
    print('    no policy changed after approval; evidence dated 25 November arrived -> mandate:', (m['status'], m['active'], m['reason']), '| runs:', runs)
    return 'OK' if m['active'] and runs else 'NOTE'


@probe('U4', 'UC-4', 'when a superseding source is itself removed, the charge it replaced does not vanish unseen')
def _():
    os_ = new_os()
    rows = clean_november(os_); run(os_, 'card_preparation')
    new = tx('A1N', '2026-11-03', '40.00', as_of=1); new['supersedes'] = CARD + ':A1'
    os_.intake(PREP, packet('sup', [new, rc('A1N', '2026-11-03', '40.00')])); run(os_, 'card_preparation')
    gone = dict(copy.deepcopy(new), as_of=2, tombstone=True, removal_reason='voided'); gone.pop('supersedes')
    os_.intake(PREP, packet('void', [gone])); run(os_, 'card_preparation')
    st = os_.state(PREP)
    keys = sorted(a['item_key'] for a in arts(os_) if a['governing'])
    print('    A1 superseded by A1N, then A1N voided -> governing items:', keys, '| removed items:', sorted(r['item_key'] for r in st['removed_items']))
    a2 = gov(os_, CARD + ':A2'); print('    remaining item A2 (statement still lists A1):', a2['blockers'])
    seen = CARD + ':A1' in keys or any(b.startswith('STATEMENT_') for b in a2['blockers'])
    return 'NOTE' if seen and CARD + ':A1' not in keys else ('OK' if seen else 'WEAK')


# ---------------------------------------------------------------------------------------
# Part 4. Teaching month by both permitted routes, and two-client isolation
# ---------------------------------------------------------------------------------------

def teaching_month(route):
    COUNTER[0] += 1
    scope2 = ORG + '/second_demo/local'
    os_ = AccountingOS(Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0]), [SCOPE, scope2])
    sid = os_.onboard(PREP, copy.deepcopy(PROFILE))
    for subject, permissions in ROLES.items():
        os_.grant_authority(ADMIN, subject, permissions, 'Fictional probe authority; listed in ROLES')
    os_.approve_profile_version(CTRL, sid, 'Explicit independent approval'); os_.open_period(PADMIN, *NOV, 'Fictional teaching month')
    teaching = load('fixtures/teaching.json'); src = {s['key']: s for s in teaching['sources']}
    os_.intake(PREP, teaching); os_.intake(PREP, load('fixtures/late_receipt.json'))
    fixed_j = copy.deepcopy(src['J-002']); fixed_j['data']['lines'][0]['debit'] = '26.00'; fixed_j['data']['lines'][1]['credit'] = '26.00'
    os_.intake(PREP, packet('journal-correction', [fixed_j]))                                  # the preparer corrects their own unbalanced journal
    run(os_, 'card_preparation'); run(os_, 'journal_preparation')
    K = CARD + ':TX-0'
    start = gov(os_, K + '09'); print('    [%s] TX-009 as delivered: %s | receipt amount %s' % (route, start['blockers'], src['receipt-TX-009']['data']['amount']))
    if route == 'accept':
        fixed_rc = copy.deepcopy(src['receipt-TX-009']); fixed_rc['data']['amount'] = '80.00'
        os_.intake(PREP2, packet('receipt-correction', [fixed_rc])); run(os_, 'card_preparation')
        held = gov(os_, K + '09'); revs = held['payload']['data']['evidence_revisions']
        assert held['blockers'] == ['EVIDENCE_REVISED_REQUIRES_REVIEW'] and revs and revs[0]['changed_fields'] == ['amount'], ('revised receipt must be held and disclosed', brief(held), revs)
        print('    [accept] corrected receipt held and disclosed: version %s by %s -> version %s by %s' % (revs[0]['earlier']['version'], revs[0]['earlier']['supplier'], revs[0]['current']['version'], revs[0]['current']['supplier']))
        t9 = dispose(os_, K + '09', 'EVIDENCE_REVISED_REQUIRES_REVIEW', 'revised_evidence_accepted')
    else:
        t9 = dispose(os_, K + '09', 'RECEIPT_AMOUNT_POLICY_UNSET', 'refer_external')
    steps = [t9, dispose(os_, K + '04', 'POSSIBLE_DUPLICATE', 'distinct_purchases'), dispose(os_, K + '05', 'POSSIBLE_DUPLICATE', 'distinct_purchases'),
             dispose(os_, K + '03', 'UNKNOWN_VENDOR', 'confirm_vendor', {'account_id': 'DEMO_OFFICE_SUPPLIES'}), dispose(os_, K + '03', 'UNKNOWN_CATEGORY', 'code_category', {'account_id': 'DEMO_OFFICE_SUPPLIES'}),
             dispose(os_, K + '06', 'CREDIT_REQUIRES_REVIEW', 'standalone_credit', {'account_id': 'DEMO_OFFICE_SUPPLIES'}),
             dispose(os_, K + '10', 'SPLIT_REQUIRES_REVIEW', 'allocate', {'allocations': [{'account_id': 'DEMO_REPAIRS', 'amount': '20.00'}, {'account_id': 'DEMO_OFFICE_SUPPLIES', 'amount': '15.00'}]}),
             dispose(os_, K + '12', 'NON_EXPENSE_REQUIRES_REVIEW', 'settlement_of_card_liability', {'cash_account': 'DEMO_CASH'}),
             dispose(os_, K + '07', 'PENDING_TRANSACTION', 'refer_external'), dispose(os_, K + '11', 'CURRENCY_MISMATCH', 'refer_external')]
    assert all(s[0] == 'ok' for s in steps), ('every teaching disposition must be accepted', steps)
    run(os_, 'card_preparation')
    current = [a for a in arts(os_, period_id='2026-11') if a['governing'] and a['current']]
    approved, carried, impact = [], [], {}
    for a in current:
        if a['eligible']:
            assert review(os_, REV, a, 'approve')[0] == 'ok', a['item_key']
            approved.append(a['item_key'])
            for l in a['payload']['data']['proposed_entry']['lines']:
                impact[l['account_id']] = impact.get(l['account_id'], Decimal('0.00')) + Decimal(l['debit']) - Decimal(l['credit'])
        else:
            carried.append((a['item_key'].replace(CARD + ':', ''), a['blockers'], bool(a['payload']['data'].get('disposition_ids'))))
            assert review(os_, REV, a, 'approve')[0] == 'refused', ('a held item must not be approvable', a['item_key'])
    ack = 'Carried items referred externally and still held; October TX-008 and its receipt quarantined; fictional; no ledger close represented.'
    noack = attempt(os_.finalize_package, FIN, '2026-11', 'card_preparation', 'probe handover')
    pk = [attempt(os_.finalize_package, FIN, '2026-11', w, 'Fictional preparation handover', ack) for w in ('card_preparation', 'journal_preparation')]
    lock = attempt(os_.lock_period, PADMIN, '2026-11', 'Fictional lock', ack)
    st = os_.state(PREP); card_pkg = json.loads(st['packages'][0]['payload'])
    independent = all(REV.id not in a['contributors'] and FIN.id not in a['contributors'] for a in current)
    out = {'approved': sorted(approved), 'carried': sorted(carried), 'impact': {k: str(v) for k, v in sorted(impact.items())}, 'net_zero': sum(impact.values()) == 0,
           'noack': noack[0], 'packages': [p[0] for p in pk], 'lock': lock[0], 'independent': independent,
           'package_carried': sorted(o['item_key'].replace(CARD + ':', '') for o in card_pkg['open_exceptions']), 'quarantined': sorted({q['source_key'] for q in card_pkg['quarantined_sources']}),
           'authority': card_pkg['authority'], 'os': os_, 'state': st, 'scope2': scope2}
    print('    [%s] approved %d: %s' % (route, len(approved), [k.replace(CARD + ':', '') for k in sorted(approved)]))
    print('    [%s] carried: %s' % (route, out['carried']))
    print('    [%s] entry impact of approved items: %s | nets to zero: %s' % (route, out['impact'], out['net_zero']))
    print('    [%s] finalize without acknowledgement: %s | packages: %s | lock: %s | reviewer and finalizer outside every lineage: %s' % (route, noack[0], out['packages'], lock[0], independent))
    print('    [%s] package carries %s | quarantined named %s | package authority: %s' % (route, out['package_carried'], out['quarantined'], out['authority']))
    return out


@probe('M1', 'G0', 'teaching month, referral route: TX-009 keeps its 79.99 receipt and stays held; second client isolated')
def _():
    m = teaching_month('refer'); os_ = m['os']; st1 = m['state']
    hand = {'DEMO_OFFICE_SUPPLIES': '311.00', 'DEMO_REPAIRS': '200.00', 'DEMO_CARD_LIABILITY': '-211.00', 'DEMO_CASH': '-300.00'}
    receipt = [s for s in os_.export(PREP)['evidence_history'] if s['source_key'] == 'receipt-TX-009']
    print('    TX-009 receipt versions on file:', len(receipt), '| amount:', json.loads(receipt[-1]['payload'])['amount'])
    before = ([(a['id'], a['hash'], a['review_status']) for a in st1['artifacts']], [(p['id'], p['hash'], p['payload']) for p in st1['packages']], len(os_.export(PREP)['evidence_history']))
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
    victim = [a for a in st1['artifacts'] if a['item_key'] == CARD + ':TX-001' and a['governing']][0]
    cross = {'second client reviewer decides a first-client artifact': attempt(os_.review, rev2, victim['id'], victim['hash'], victim['fingerprint'], 'reject', 'x'),
             'first client reviewer decides a second-client artifact': attempt(os_.review, REV, j900['id'], j900['hash'], j900['fingerprint'], 'reject', 'x'),
             'second client preparer sends a first-client packet': attempt(os_.intake, prep2, packet('cross', [doc('x', 'trial_balance')])),
             'first client finalizer finalizes for the second client': attempt(os_.finalize_package, human(FIN.id, 'reviewer', client='second_demo'), '2026-12', 'journal_preparation', 'x', 'x')}
    for k, v in cross.items():
        show(k, v)
    st2 = os_.state(PREP)
    after = ([(a['id'], a['hash'], a['review_status']) for a in st2['artifacts']], [(p['id'], p['hash'], p['payload']) for p in st2['packages']], len(os_.export(PREP)['evidence_history']))
    isolated = before == after and ok2[0] == 'ok' and all(v[0] == 'refused' for v in cross.values()) and all(a['scope'] == m['scope2'] for a in os_.state(prep2)['artifacts']) and os_.verify_audit(PREP) and os_.verify_audit(prep2)
    print('    second client December journal approved:', ok2[0], '| first client records unchanged and both audit chains verify:', isolated)
    month = (len(m['approved']) == 10 and m['impact'] == hand and m['net_zero'] and [c[0] for c in m['carried']] == ['TX-007', 'TX-009', 'TX-011'] and all(c[2] for c in m['carried'])
             and m['noack'] == 'refused' and m['packages'] == ['ok', 'ok'] and m['lock'] == 'ok' and m['independent'] and m['package_carried'] == ['TX-007', 'TX-009', 'TX-011']
             and m['quarantined'] == [CARD + ':TX-008', 'receipt-TX-008'] and len(receipt) == 1 and m['authority'] == 'preparation_only_not_external_close')
    return 'OK' if month and isolated else 'WEAK'


@probe('M2', 'G0', 'teaching month, acceptance route: the corrected TX-009 receipt is held, disclosed, accepted by a non-supplier, then reviewed')
def _():
    m = teaching_month('accept')
    hand = {'DEMO_OFFICE_SUPPLIES': '391.00', 'DEMO_REPAIRS': '200.00', 'DEMO_CARD_LIABILITY': '-291.00', 'DEMO_CASH': '-300.00'}
    tx9 = [a for a in arts(m['os'], CARD + ':TX-009') if a['governing']][0]
    print('    TX-009 approved artifact discloses revisions:', [(r['earlier']['version'], r['current']['version'], r['changed_fields']) for r in tx9['payload']['data']['evidence_revisions']], '| accepter in lineage:', DISP.id in tx9['contributors'], '| status:', tx9['review_status'])
    month = (len(m['approved']) == 11 and m['impact'] == hand and m['net_zero'] and [c[0] for c in m['carried']] == ['TX-007', 'TX-011'] and all(c[2] for c in m['carried'])
             and m['noack'] == 'refused' and m['packages'] == ['ok', 'ok'] and m['lock'] == 'ok' and m['independent'] and tx9['payload']['data']['evidence_revisions'] and DISP.id in tx9['contributors'])
    return 'OK' if month else 'WEAK'


# ---------------------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------------------

def main():
    wanted = set(sys.argv[2:])
    import platform
    import sqlite3
    print('Fable RV acceptance probes | project root:', ROOT.name, '| Python', platform.python_version(), '| SQLite', sqlite3.sqlite_version)
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
        print('%-5s %-12s %-6s %s' % (pid, ticket, verdict, title))
    counts = {}
    for r in results:
        counts[r[2]] = counts.get(r[2], 0) + 1
    failing = [r[0] for r in results if r[2] in ('WEAK', 'ERROR')]
    print('\nVerdict counts:', dict(sorted(counts.items())))
    print('Acceptance gate:', 'PASS' if not failing else 'FAIL ' + ', '.join(failing))
    TMP.cleanup()
    sys.exit(1 if failing else 0)


if __name__ == '__main__':
    main()
