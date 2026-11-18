"""Fable verification probes for Accounting Agent OS Batch 2.

Usage: python3 batch1_verification_probes.py <project-root>

Maintained harness adapted to explicit approved profiles/grants/mandates, structured
fictional statements, ordered source metadata and acknowledged lock preconditions.
Original independent inputs remain unchanged in exports/FABLE_BATCH_1_VERIFICATION/.
Synthetic data only; temporary SQLite files; no network, model or ledger access.
Each probe prints VERDICT: OK (control holds), WEAK (control can be defeated or misleads),
DEFERRED (known Batch 2 item, unchanged), or NOTE (behaviour recorded, not a defect).
"""
import copy, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = str(Path(sys.argv[1]).resolve())
sys.path.insert(0, ROOT)
from accounting_agent.core import Actor, ControlError
from accounting_agent.demo import SCOPE, actor, load, seed, prepare_profile, grant_fixture_authority, create_fixture_mandate
from accounting_agent.service import AccountingOS

PROFILE = load('config/bird_bowl.demo.json')
PACKET = load('fixtures/teaching.json')
PREP, REV, WORKER = actor(), actor('reviewer'), actor('worker')
NOV = ('2026-11', '2026-11-01', '2026-11-30')
RESULTS = []


def human(ident, role):
    return Actor(ident, role, 'demo_org', 'bird_bowl_demo', kind='human')


def fresh(seed_it=True):
    tmp = tempfile.TemporaryDirectory()
    os_ = AccountingOS(Path(tmp.name) / 'p.sqlite3', [SCOPE])
    if seed_it:
        seed(os_)
    os_._tmp = tmp
    return os_


def intake(os_, sources, batch, who=None, period_id=None):
    p = {k: v for k, v in PACKET.items() if k != 'sources'}
    p.update(batch_id=batch, sources=sources)
    if period_id:
        p['period_id'] = period_id
    return os_.intake(who or PREP, p)


def src(key):
    return copy.deepcopy(next(s for s in PACKET['sources'] if s['key'] == key))


def arts(os_, key=None):
    return [a for a in os_.state(PREP)['artifacts'] if key is None or a['item_key'] == key]


def item(os_, key, workflow, run_id=None, period_id=None):
    st = os_.state(PREP)
    rid = run_id or next(r for r in st['runs'] if r['workflow'] == workflow and (period_id is None or r['period_id'] == period_id))['id']
    return next(a for a in st['artifacts'] if rid in a['run_ids'] and a['item_key'] == key)


def by_id(os_, aid):
    return next(a for a in os_.state(PREP)['artifacts'] if a['id'] == aid)


def decide(os_, a, who=REV, decision='approve'):
    grant_fixture_authority(os_,who)
    os_.review(who, a['id'], a['hash'], a['fingerprint'], decision, 'verification probe')


def attempt(fn):
    try:
        fn()
        return 'accepted'
    except ControlError as exc:
        return 'refused %s (%s)' % (exc.status, exc)


def probe(pid, title):
    def deco(fn):
        print('\n### %s %s' % (pid, title))
        try:
            verdict = fn()
        except Exception as exc:
            verdict = 'ERROR'
            print('  PROBE ERROR:', type(exc).__name__, exc)
            traceback.print_exc(limit=3)
        print('  VERDICT:', verdict)
        RESULTS.append((pid, verdict, title))
    return deco


# =============================================================== Part A: original probes re-run
@probe('P01', 'evidence+policy author approves through a colleague\'s run')
def _():
    os_ = fresh(False)
    a_prep, b_prep, a_rev = human('human-a', 'preparer'), human('human-b', 'preparer'), human('human-a', 'reviewer')
    prepare_profile(os_,a_prep, PROFILE); os_.open_period(REV, *NOV, 'probe'); os_.intake(a_prep, PACKET)
    os_.enqueue(b_prep, 'journal_preparation'); os_.drain(WORKER)
    out = attempt(lambda: decide(os_, item(os_, 'J-001', 'journal_preparation'), a_rev))
    print('  human-a approving own evidence:', out)
    return 'OK' if out.startswith('refused 403') else 'WEAK'


@probe('P02', 'human/service decided by kind, not by actor id')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation')
    svc = attempt(lambda: decide(os_, j, Actor('automation-agent-7', 'reviewer', 'demo_org', 'bird_bowl_demo', kind='service')))
    hum = attempt(lambda: decide(os_, j, human('worker-of-the-month-jane', 'reviewer')))
    print('  service reviewer:', svc, '| human named worker-...:', hum)
    return 'OK' if svc.startswith('refused 403') and hum == 'accepted' else 'WEAK'


@probe('P03', 'recurring occurrence survives evidence arriving before the worker runs')
def _():
    os_ = fresh(); os_.drain(WORKER)
    create_fixture_mandate(os_,PREP, ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    first = os_.tick(PREP, '2026-11-15T12:00:00+00:00')
    j = src('J-001'); j['data']['memo'] = 'Revised before worker ran'
    intake(os_, [j], 'late-journal')
    os_.drain(WORKER, now='2026-11-15T12:05:00+00:00')
    second = os_.tick(PREP, '2026-11-15T13:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T13:05:00+00:00')
    st = os_.state(PREP)
    occ = [(o['occurrence_key'][:10], o['status']) for o in st['occurrences']]
    done = [r['id'] for r in st['runs'] if r['occurrence_id'] and r['status'] in ('awaiting_review', 'prepared_with_exceptions')]
    cur = [a['id'] for a in st['artifacts'] if a['current'] and a['item_key'] == 'J-001']
    print('  ticks', first, second, '| occurrences', occ, '| completed runs for occurrence', done, '| current J-001 artifacts', cur)
    return 'OK' if len(done) == 1 and len(cur) == 1 and occ == [('2026-11-15', 'completed')] else 'WEAK'


@probe('P04', 'one unfit mandate does not stop the others')
def _():
    os_ = fresh(); os_.drain(WORKER)
    for wf in ('journal_preparation', 'card_preparation'):
        create_fixture_mandate(os_,PREP, [wf], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    p = copy.deepcopy(PROFILE); p['version'] = 'fictional-demo-2'; p['procedures'] = ['card_preparation', 'close_readiness']
    prepare_profile(os_,PREP, p)
    out = attempt(lambda: os_.tick(PREP, '2026-11-15T12:00:00+00:00'))
    st = os_.state(PREP)
    print('  tick:', out, '| occurrences', [(o['workflow'], o['status'], o['reason']) for o in st['occurrences']], '| mandate status', [(m['id'], m['status']) for m in st['mandates']])
    ok = out == 'accepted' and any(o['workflow'] == 'card_preparation' and o['status'] == 'dispatched' for o in st['occurrences']) and any(o['workflow'] == 'journal_preparation' and o['status'] == 'held' for o in st['occurrences'])
    return 'OK' if ok else 'WEAK'


@probe('P05', 'two recurring occurrences on identical inputs: one governing artifact')
def _():
    os_ = fresh(); os_.drain(WORKER)
    create_fixture_mandate(os_,PREP, ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    for now in ('2026-11-15T12:00:00+00:00', '2026-11-16T12:00:00+00:00'):
        os_.tick(PREP, now); os_.drain(WORKER, now=now)
    rows = [(a['id'], a['run_ids'], a['governing'], a['review_status']) for a in arts(os_, 'J-001')]
    print('  J-001 artifacts (id, runs, governing, status):', rows)
    return 'OK' if len(rows) == 1 and len(rows[0][1]) == 3 else 'WEAK'


@probe('P06', 'CJK alias does not match a different CJK descriptor')
def _():
    os_ = fresh(False)
    p = copy.deepcopy(PROFILE); p['vendors'].append({'id': 'demo_tokyo', 'name': 'Tokyo stationery (fictional)', 'aliases': ['東京文具'], 'category': 'DEMO_OFFICE_SUPPLIES'})
    prepare_profile(os_,PREP, p); os_.open_period(REV, *NOV, 'probe'); os_.intake(PREP, PACKET)
    tx = src('demo_card_001:TX-001'); tx['data']['description'] = '大阪修理'
    rc = src('receipt-TX-001'); rc['data']['vendor'] = '大阪修理'
    intake(os_, [tx, rc], 'unicode-1'); os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  vendor:', a['payload']['data']['vendor'], '| eligible:', bool(a['eligible']), '| blockers:', a['blockers'])
    return 'OK' if not a['eligible'] and 'UNKNOWN_VENDOR' in a['blockers'] else 'WEAK'


@probe('P07', 'late older batch replaces newer source version (Batch 2: F-13)')
def _():
    os_ = fresh()
    newer = src('demo_card_001:TX-001'); newer['data']['amount'] = '45.00'; newer['as_of']=2
    older=src('demo_card_001:TX-001');older['as_of']=1
    intake(os_, [newer], 'feed-seq-2'); intake(os_, [older], 'feed-seq-1-arrived-late')
    s = next(s for s in os_.state(PREP)['sources'] if s['source_key'] == 'demo_card_001:TX-001')
    print('  current version:', s['version'], '| amount:', s['value']['amount'])
    return 'OK' if s['value']['amount'] == '45.00' else 'DEFERRED'


@probe('P08', 'journal support / duplicate / no-effect (Batch 2: F-15)')
def _():
    os_ = fresh()
    j = src('J-001'); j['data']['supporting_keys'] = ['trial-balance-placeholder']
    dup = src('J-001'); dup['key'] = 'J-003'
    selfoff = src('J-001'); selfoff['key'] = 'J-004'; selfoff['data']['lines'][1]['account_id'] = 'DEMO_OFFICE_SUPPLIES'
    intake(os_, [j, dup, selfoff], 'journal-probe'); os_.enqueue(PREP, 'journal_preparation'); os_.drain(WORKER)
    rows = [(k, bool(item(os_, k, 'journal_preparation')['eligible'])) for k in ('J-001', 'J-003', 'J-004')]
    print('  eligible:', rows)
    return 'DEFERRED' if all(e for _, e in rows) else 'OK'


@probe('P09', 'locking the period preserves approvals and blocks new dispatch')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j)
    os_.lock_period(REV, '2026-11', 'probe lock',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
    status = by_id(os_, j['id'])['review_status']
    enq = attempt(lambda: os_.enqueue(PREP, 'journal_preparation', '2026-11'))
    print('  status after lock:', status, '| enqueue in locked period:', enq)
    return 'OK' if status == 'approve' and enq.startswith('refused 409') else 'WEAK'


@probe('P10', 'opening December does not strand November')
def _():
    os_ = fresh(); os_.drain(WORKER)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation'); decide(os_, c)
    os_.open_period(REV, '2026-12', '2026-12-01', '2026-12-31', 'probe December')
    os_.enqueue(PREP, 'card_preparation', '2026-12'); os_.drain(WORKER)
    status = by_id(os_, c['id'])['review_status']
    dec = [a['item_key'] for a in os_.state(PREP)['artifacts'] if a['period_id'] == '2026-12' and a['kind'] == 'card_proposal']
    print('  November TX-001 status:', status, '| December card items:', dec)
    return 'OK' if status == 'approve' else 'WEAK'


def status_with_edit(db_path, artifact_id, filename):
    """Copy the package, append a comment to one file, and read the review status from a fresh process."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(Path(ROOT) / 'accounting_agent', Path(tmp) / 'accounting_agent')
        with open(Path(tmp) / 'accounting_agent' / filename, 'a') as fh:
            fh.write('\n# reviewer probe: no-op change\n')
        code = ("import sys;sys.dont_write_bytecode=True;sys.path.insert(0,%r);"
                "from accounting_agent.service import AccountingOS;from accounting_agent.demo import SCOPE,actor;"
                "o=AccountingOS(%r,[SCOPE]);print(next(a for a in o.state(actor())['artifacts'] if a['id']==%d)['review_status'])" % (tmp, str(db_path), artifact_id))
        return subprocess.run([sys.executable, '-c', code], capture_output=True, text=True).stdout.strip()


@probe('P11', 'real file edits: transport change keeps approval, handler change stales it')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j)
    out = {f: status_with_edit(os_.store.path, j['id'], f) for f in ('http.py', '__main__.py', 'demo.py', 'service.py', 'storage.py', 'modules.py', 'core.py')}
    print('  status after editing each file:', out)
    ok = all(out[f] == 'approve' for f in ('http.py', '__main__.py', 'demo.py')) and all(out[f] == 'stale' for f in ('modules.py', 'core.py'))
    return 'OK' if ok else 'WEAK'


@probe('P12', 'close readiness ignores open exceptions (Batch 2: F-11)')
def _():
    os_ = fresh()
    docs = [{'kind': 'document', 'key': 'doc-' + t, 'data': {'document_type': t, 'content': 'Placeholder; nothing reconciled.'}} for t in ('card_statement', 'bank_reconciliation', 'ap_tieout', 'ar_tieout')]
    intake(os_, docs, 'close-docs')
    for w in ('card_preparation', 'journal_preparation', 'close_readiness'):
        os_.enqueue(PREP, w)
    os_.drain(WORKER)
    a = item(os_, 'close-checklist', 'close_readiness')
    print('  blockers:', a['blockers'])
    return 'OK' if 'OPEN_PREPARATION_EXCEPTIONS' in a['blockers'] else 'DEFERRED'


@probe('P13', 'statement control passes on population substitution (Batch 2: F-12)')
def _():
    os_ = fresh()
    gone = src('demo_card_001:TX-003'); gone['data']['status'] = 'pending'
    new = src('demo_card_001:TX-001'); new['key'] = 'demo_card_001:TX-NEW'; new['data'].update(source_id='TX-NEW', date='2026-11-20', amount='65.00')
    intake(os_, [gone, new], 'swap'); os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  TX-001 eligible after swap:', bool(a['eligible']))
    return 'DEFERRED' if a['eligible'] else 'OK'


@probe('P14', 'repeated and contradictory decisions on one artifact')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); r2 = human('human-demo-reviewer-2', 'reviewer')
    seq = [('REV approve', attempt(lambda: decide(os_, j))), ('REV approve again', attempt(lambda: decide(os_, j))),
           ('R2 reject', attempt(lambda: decide(os_, j, r2, 'reject'))), ('REV approve again', attempt(lambda: decide(os_, j)))]
    status = item(os_, 'J-001', 'journal_preparation')['review_status']
    print('  ', seq, '| status:', status)
    return 'OK' if status == 'disputed' and seq[1][1].startswith('refused 409') and seq[3][1].startswith('refused 409') else 'WEAK'


@probe('P15', 'receipt dated the day before posting (Batch 2: F-16)')
def _():
    os_ = fresh()
    rc = src('receipt-TX-001'); rc['data']['date'] = '2026-11-02'
    intake(os_, [rc], 'receipt-date'); os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  blockers:', a['blockers'])
    return 'DEFERRED' if a['blockers'] == ['RECEIPT_DATE_MISMATCH'] else 'OK'


@probe('P16', 'unrelated card receipt leaves an approved journal intact')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j)
    os_.intake(PREP, load('fixtures/late_receipt.json'))
    status = next(a for a in os_.export(PREP)['artifacts'] if a['id'] == j['id'])['review_status']
    card = item(os_, 'demo_card_001:TX-001', 'card_preparation')['review_status']
    print('  journal status in export:', status, '| card TX-001 (same workflow as the receipt):', card)
    return 'OK' if status == 'approve' and card == 'stale' else 'WEAK'


# =============================================================== Part B: new adversarial probes
@probe('N01', 'decisions recorded in a locked period')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    os_.lock_period(REV, '2026-11', 'probe lock',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
    r2 = human('second-reviewer', 'reviewer')
    out = {'approve pending TX-001': attempt(lambda: decide(os_, c)), 'revoke approved J-001': attempt(lambda: decide(os_, j, r2, 'revoke'))}
    print('  under lock:', out, '| J-001 now:', by_id(os_, j['id'])['review_status'], '| TX-001 now:', by_id(os_, c['id'])['review_status'])
    return 'WEAK' if 'accepted' in out.values() else 'OK'


@probe('N02', 'source re-dated out of a locked period is approvable in both periods')
def _():
    os_ = fresh(); os_.drain(WORKER)
    nov = item(os_, 'demo_card_001:TX-001', 'card_preparation'); decide(os_, nov)
    os_.lock_period(REV, '2026-11', 'November closed',acknowledgement="Explicit fictional carry-forward of unsettled fixture items")
    os_.open_period(REV, '2026-12', '2026-12-01', '2026-12-31', 'December')
    tx = src('demo_card_001:TX-001'); tx['data']['date'] = '2026-12-01'
    rc = src('receipt-TX-001'); rc['data']['date'] = '2026-12-01'
    ctl = src('demo-card-control'); ctl['key'] = 'demo-card-control-dec'; ctl['data'].update(period_start='2026-12-01',period_end='2026-12-31',line_count=1,line_ids=['TX-001'],totals={k:('42.50' if k=='purchase' else '0.00') for k in ctl['data']['totals']},opening_balance='1000.00',closing_balance='1042.50')
    intake(os_, [tx, rc, ctl], 'feed-revision-after-lock')
    os_.enqueue(PREP, 'card_preparation', '2026-12'); os_.drain(WORKER)
    try:
        dec = item(os_, 'demo_card_001:TX-001', 'card_preparation', period_id='2026-12')
        dec_out = attempt(lambda: decide(os_, dec))
    except StopIteration:
        dec, dec_out = {'blockers': None, 'payload': {'data': {'transaction': {'date': None}}}}, 'no December item exists'
    st = os_.state(PREP)
    nov_now = by_id(os_, nov['id'])
    flags = [(e['source_key'], e['reason']) for e in st['source_exceptions']]
    print('  November TX-001:', nov_now['review_status'], 'amount', nov_now['payload']['data']['transaction']['amount'], 'date', nov_now['payload']['data']['transaction']['date'])
    print('  December TX-001: blockers', dec['blockers'], '| approval', dec_out, '| date', dec['payload']['data']['transaction']['date'])
    print('  exceptions raised against November for the moved source:', [f for f in flags if 'TX-001' in f[0]])
    both = nov_now['review_status'] == 'approve' and dec_out == 'accepted'
    return 'WEAK' if both else 'OK'


@probe('N03', 'rejection displaced by an identical re-preparation under another actor')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j, REV, 'reject')
    colleague = human('human-colleague', 'preparer')
    create_fixture_mandate(os_,colleague, ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    os_.tick(colleague, '2026-11-15T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T12:00:01+00:00')
    new = item(os_, 'J-001', 'journal_preparation')
    same_data = new['payload']['data'] == j['payload']['data']
    out = attempt(lambda: decide(os_, new, human('second-reviewer', 'reviewer')))
    rows = [(a['id'], a['governing'], a['review_status'], [d['decision'] for d in a['decisions']]) for a in arts(os_, 'J-001')]
    print('  new artifact created:', new['id'] != j['id'], '| identical accounting data:', same_data, '| approval of the copy:', out)
    print('  J-001 artifacts (id, governing, status, decisions):', rows)
    return 'WEAK' if new['id'] != j['id'] and same_data and out == 'accepted' else 'OK'


@probe('N04', 'evidence author regains review rights after a colleague\'s trivial revision')
def _():
    os_ = fresh(False)
    a_prep, b_prep, a_rev = human('human-a', 'preparer'), human('human-b', 'preparer'), human('human-a', 'reviewer')
    prepare_profile(os_,b_prep, PROFILE); os_.open_period(REV, *NOV, 'probe'); os_.intake(b_prep, PACKET)
    mine = src('J-001'); mine['key'] = 'J-900'; mine['data']['memo'] = 'Entry authored by human-a'
    intake(os_, [mine], 'a-authored', a_prep)
    tweak = copy.deepcopy(mine); tweak['data']['memo'] = 'Entry authored by human-a.'
    intake(os_, [tweak], 'b-trivial-revision', b_prep)
    os_.enqueue(b_prep, 'journal_preparation'); os_.drain(WORKER)
    a = item(os_, 'J-900', 'journal_preparation')
    out = attempt(lambda: decide(os_, a, a_rev))
    print('  contributors on artifact:', a['payload'].get('contributors', a.get('contributors')), '| human-a approving own entry:', out)
    return 'WEAK' if out == 'accepted' else 'OK'


@probe('N05', 'policy author regains review rights after a colleague re-registers the profile')
def _():
    os_ = fresh(False)
    a_prep, b_prep, a_rev = human('human-a', 'preparer'), human('human-b', 'preparer'), human('human-a', 'reviewer')
    prepare_profile(os_,a_prep, PROFILE)
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'fictional-demo-2'; p2['notice'] = PROFILE['notice'] + ' (wording edit)'
    prepare_profile(os_,b_prep, p2)
    os_.open_period(REV, *NOV, 'probe'); os_.intake(b_prep, PACKET)
    os_.enqueue(b_prep, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    out = attempt(lambda: decide(os_, a, a_rev))
    print('  mapping rules authored by human-a; contributors:', a['payload'].get('contributors', a.get('contributors')), '| human-a approving item coded by own mapping:', out)
    return 'WEAK' if out == 'accepted' else 'OK'


@probe('N06', 'combining-mark scripts: different words collapse to the same alias')
def _():
    from accounting_agent.core import normalize
    pairs = [('กิน', 'กัน', 'Thai'), ('किताब', 'कुताब', 'Devanagari'), ('דָּבָר', 'דֶּבֶר', 'Hebrew pointed')]
    for a, b, script in pairs:
        print('  %-15s %r vs %r -> %r vs %r  equal=%s' % (script, a, b, normalize(a), normalize(b), normalize(a) == normalize(b)))
    os_ = fresh(False)
    p = copy.deepcopy(PROFILE); p['vendors'].append({'id': 'demo_thai', 'name': 'Thai vendor (fictional)', 'aliases': [pairs[0][0]], 'category': 'DEMO_OFFICE_SUPPLIES'})
    prepare_profile(os_,PREP, p); os_.open_period(REV, *NOV, 'probe'); os_.intake(PREP, PACKET)
    tx = src('demo_card_001:TX-001'); tx['data']['description'] = pairs[0][1]
    rc = src('receipt-TX-001'); rc['data']['vendor'] = pairs[0][1]
    intake(os_, [tx, rc], 'thai'); os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  end to end: vendor', a['payload']['data']['vendor'], '| category', a['payload']['data']['proposed_category'], '| eligible', bool(a['eligible']), '| blockers', a['blockers'])
    return 'WEAK' if a['eligible'] else 'OK'


@probe('N07', 'actor created without an explicit kind')
def _():
    try:
        k = Actor('some-automation', 'reviewer', 'demo_org', 'bird_bowl_demo').kind
    except Exception as exc:
        print('  an actor without a kind cannot be constructed:', type(exc).__name__)
        return 'OK'
    os_ = fresh(); os_.drain(WORKER)
    out = attempt(lambda: decide(os_, item(os_, 'J-001', 'journal_preparation'), Actor('some-automation', 'reviewer', 'demo_org', 'bird_bowl_demo')))
    print('  default kind:', k, '| review by actor with no kind supplied:', out)
    return 'WEAK' if k == 'human' and out == 'accepted' else 'OK'


@probe('N08', 'evidence received before its period is opened')
def _():
    os_ = fresh(False)
    prepare_profile(os_,PREP, PROFILE); os_.intake(PREP, PACKET)
    os_.open_period(REV, *NOV, 'opened after the evidence arrived')
    replay = dict(PACKET, batch_id='teaching-resupplied')
    r = os_.intake(PREP, replay)
    for w in ('card_preparation', 'journal_preparation'):
        os_.enqueue(PREP, w)
    os_.drain(WORKER)
    st = os_.state(PREP)
    stuck = sorted({(e['source_key'], e['reason']) for e in st['source_exceptions']})
    j = item(os_, 'J-001', 'journal_preparation'); c = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  re-supply of identical evidence:', r)
    print('  still quarantined after the period opened:', [s[0] for s in stuck])
    print('  J-001 blockers:', j['blockers'], '| TX-001 blockers:', c['blockers'])
    undated = [s for s in stuck if s[0] in ('demo-card-control', 'journal-support-001', 'trial-balance-placeholder')]
    return 'WEAK' if undated else 'OK'


@probe('N09', 'receipt dated in the prior month for a first-of-month charge')
def _():
    os_ = fresh()
    tx = src('demo_card_001:TX-001'); tx['data']['date'] = '2026-11-01'
    rc = src('receipt-TX-001'); rc['data']['date'] = '2026-10-31'
    intake(os_, [tx, rc], 'month-boundary'); os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    exc = [(e['source_key'], e['reason']) for e in os_.state(PREP)['source_exceptions'] if e['source_key'] == 'receipt-TX-001']
    print('  TX-001 blockers:', a['blockers'], '| receipt status:', exc, '| evidence listed on artifact:', [e['source_key'] for e in a['payload']['data']['evidence']])
    return 'WEAK' if 'MISSING_RECEIPT' in a['blockers'] else 'OK'


@probe('N10', 'lock then reopen with no new evidence keeps approvals; lock preconditions')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); decide(os_, j)
    os_.intake(PREP, load('fixtures/late_receipt.json'))   # card workflow now stale, not re-prepared
    st = os_.state(PREP)
    open_items = sum(1 for a in st['artifacts'] if a['kind'] in ('card_proposal', 'journal_proposal') and a['governing'] and (a['blockers'] or a['review_status'] in ('pending', 'stale')))
    lock = attempt(lambda: os_.lock_period(REV, '2026-11', 'lock with open work',acknowledgement="Explicit fictional carry-forward of unsettled fixture items"))
    card_locked = item(os_, 'demo_card_001:TX-001', 'card_preparation')['review_status']
    os_.reopen_period(REV, '2026-11', 'reopen, nothing new')
    after = by_id(os_, j['id'])['review_status']
    print('  governing items unreviewed, blocked or stale at lock time:', open_items, '| lock:', lock, '| card TX-001 while locked:', card_locked, '| J-001 after lock+reopen:', after)
    return 'OK' if after == 'approve' and lock == 'accepted' else 'WEAK'


@probe('N11', 'recurring run across a period boundary; held occurrence recovers')
def _():
    os_ = fresh(); os_.drain(WORKER)
    create_fixture_mandate(os_,PREP, ['journal_preparation'], '2026-11-29T00:00:00+00:00', '2026-12-04T00:00:00+00:00', 86400, 5,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    a = os_.tick(PREP, '2026-11-29T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-29T12:00:01+00:00')
    b = os_.tick(PREP, '2026-12-01T12:00:00+00:00')
    held = [(o['occurrence_key'][:10], o['status'], o['reason']) for o in os_.state(PREP)['occurrences']]
    os_.open_period(REV, '2026-12', '2026-12-01', '2026-12-31', 'December')
    c = os_.tick(PREP, '2026-12-02T12:00:00+00:00'); os_.drain(WORKER, now='2026-12-02T12:00:01+00:00')
    st = os_.state(PREP)
    final = [(o['occurrence_key'][:10], o['status']) for o in st['occurrences']]
    per = sorted({(r['period_id'], r['status']) for r in st['runs'] if r['occurrence_id']})
    print('  before December exists:', held)
    print('  after opening December:', final, '| run periods:', per, '| ticks', a, b, c)
    ok = ('2026-11-30', 'skipped_no_catch_up') in final and ('2026-12-01', 'completed') in final and ('2026-12-02', 'completed') in final
    return 'OK' if ok else 'WEAK'


@probe('N12', 'concurrent ticks, drains and contrary decisions')
def _():
    from concurrent.futures import ThreadPoolExecutor
    os_ = fresh()
    create_fixture_mandate(os_,PREP, ['journal_preparation', 'card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3,freshness={'none':'Historical fixed-evidence recurrence regression; freshness is tested separately'})
    with ThreadPoolExecutor(max_workers=4) as pool:
        ticks = list(pool.map(lambda _: tuple(os_.tick(PREP, '2026-11-15T12:00:00+00:00')), range(4)))
        list(pool.map(lambda _: os_.drain(WORKER, now='2026-11-15T12:00:05+00:00'), range(4)))
    st = os_.state(PREP)
    per_occ = {}
    for r in st['runs']:
        if r['occurrence_id'] and r['status'] in ('awaiting_review', 'prepared_with_exceptions'):
            per_occ[r['occurrence_id']] = per_occ.get(r['occurrence_id'], 0) + 1
    governing = {}
    for a in st['artifacts']:
        if a['governing']:
            governing[(a['payload']['workflow'], a['item_key'])] = governing.get((a['payload']['workflow'], a['item_key']), 0) + 1
    j = item(os_, 'J-001', 'journal_preparation'); r2 = human('second-reviewer', 'reviewer')
    with ThreadPoolExecutor(max_workers=2) as pool:
        outs = list(pool.map(lambda args: attempt(lambda: decide(os_, j, args[0], args[1])), [(REV, 'approve'), (r2, 'reject')]))
    status = item(os_, 'J-001', 'journal_preparation')['review_status']
    print('  identical tick results:', len(set(ticks)) == 1, '| completed runs per occurrence:', sorted(per_occ.values()), '| max governing per item:', max(governing.values()))
    print('  simultaneous approve/reject by two reviewers:', outs, '| status:', status, '| audit chain intact:', os_.verify_audit(PREP))
    ok = len(set(ticks)) == 1 and set(per_occ.values()) == {1} and max(governing.values()) == 1 and status == 'disputed' and os_.verify_audit(PREP)
    return 'OK' if ok else 'WEAK'


@probe('N13', 'approval invalidation: evidence, policy and source changes inside one workflow')
def _():
    os_ = fresh(); os_.drain(WORKER)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation'); decide(os_, c)
    r = {}
    os_.intake(PREP, load('fixtures/late_receipt.json')); r['after card receipt'] = by_id(os_, c['id'])['review_status']
    stale_approve = attempt(lambda: decide(os_, c, human('second-reviewer', 'reviewer'), 'reject'))
    os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    c2 = item(os_, 'demo_card_001:TX-001', 'card_preparation'); r['re-prepared'] = (c2['id'] != c['id'], c2['review_status'])
    decide(os_, c2)
    p = copy.deepcopy(PROFILE); p['version'] = 'fictional-demo-2'; p['policies']['receipt_required'] = False
    prepare_profile(os_,PREP, p); r['after policy change'] = by_id(os_, c2['id'])['review_status']
    print('  ', r, '| decision on stale artifact:', stale_approve)
    ok = r['after card receipt'] == 'stale' and r['re-prepared'] == (True, 'pending') and r['after policy change'] == 'stale' and stale_approve.startswith('refused 409')
    return 'OK' if ok else 'WEAK'


@probe('N14', 'reviewer who supplied one document is barred from the whole workflow population')
def _():
    os_ = fresh(); os_.drain(WORKER)
    helper_as_preparer, helper_as_reviewer = human('human-helper', 'preparer'), human('human-helper', 'reviewer')
    os_.intake(helper_as_preparer, load('fixtures/late_receipt.json'))     # supplies the TX-002 receipt only
    os_.enqueue(PREP, 'card_preparation'); os_.drain(WORKER)
    out = attempt(lambda: decide(os_, item(os_, 'demo_card_001:TX-001', 'card_preparation'), helper_as_reviewer))
    own=attempt(lambda:decide(os_,item(os_,'demo_card_001:TX-002','card_preparation'),helper_as_reviewer))
    print('  unrelated TX-001:',out,'| own receipt TX-002:',own)
    return 'OK' if out=='accepted' and own.startswith('refused 403') else 'WEAK'


@probe('N15', 'revoked approval and repeated dispute')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); r2, r3, r4 = (human('reviewer-%d' % n, 'reviewer') for n in (2, 3, 4))
    decide(os_, j); decide(os_, j, REV, 'revoke')
    again = attempt(lambda: decide(os_, j, r2))
    rid = os_.enqueue(PREP, 'journal_preparation'); os_.drain(WORKER)
    same = item(os_, 'J-001', 'journal_preparation')['id'] == j['id']
    recovery=attempt(lambda:decide(os_,j,r3,'resolve_approve'))
    print('  after revoke: new approval', again, '| unchanged artifact:', same,'| independent recovery:',recovery)
    os2 = fresh(); os2.drain(WORKER); k = item(os2, 'J-001', 'journal_preparation')
    decide(os2, k); decide(os2, k, r2, 'reject'); decide(os2, k, r3, 'resolve_approve')
    redispute = attempt(lambda: decide(os2, k, r2, 'reject'))
    print('  after third-reviewer resolution, the overruled reviewer rejects again:', redispute, '| status:', item(os2, 'J-001', 'journal_preparation')['review_status'])
    return 'OK' if recovery=='accepted' and redispute.startswith('refused 409') and item(os2,'J-001','journal_preparation')['review_status']=='approve' else 'WEAK'


print('\n================ summary')
for pid, verdict, title in RESULTS:
    print('%-4s %-9s %s' % (pid, verdict, title))


# =============================================================== Part C: supplementary checks
@probe('N16', 'policy changed and reverted: does the earlier approval come back without review?')
def _():
    os_ = fresh(); os_.drain(WORKER)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation'); decide(os_, c)
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'fictional-demo-2'; p2['policies']['receipt_required'] = False
    prepare_profile(os_,PREP, p2); mid = by_id(os_, c['id'])['review_status']
    p3 = copy.deepcopy(PROFILE); p3['version'] = 'fictional-demo-3'
    prepare_profile(os_,human('human-colleague', 'preparer'), p3); end = by_id(os_, c['id'])['review_status']
    print('  after change:', mid, '| after revert by another registrant:', end)
    return 'NOTE'


@probe('N17', 'later policy change versus earlier periods (Batch 2: F-06 effective dating)')
def _():
    os_ = fresh(); os_.drain(WORKER)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation'); decide(os_, c)
    os_.open_period(REV, '2026-12', '2026-12-01', '2026-12-31', 'December')
    p2 = copy.deepcopy(PROFILE); p2['version'] = 'fictional-demo-2'
    p2['vendors'].append({'id': 'demo_new_dec_vendor', 'name': 'New December vendor (fictional)', 'aliases': ['NEW DECEMBER VENDOR DEMO'], 'category': 'DEMO_REPAIRS'})
    prepare_profile(os_,PREP, p2)
    open_nov = by_id(os_, c['id'])['review_status']
    os2 = fresh(); os2.drain(WORKER)
    d = item(os2, 'demo_card_001:TX-001', 'card_preparation'); decide(os2, d)
    os2.lock_period(REV, '2026-11', 'November closed',acknowledgement="Explicit fictional carry-forward of unsettled fixture items"); prepare_profile(os2,PREP, p2)
    locked = by_id(os2, d['id'])['review_status']
    os2.reopen_period(REV, '2026-11', 'reopened for an unrelated query')
    reopened = by_id(os2, d['id'])['review_status']
    print('  new December vendor rule added -> approved November item: open period', open_nov, '| locked period', locked, '| after reopen', reopened)
    return 'OK' if open_nov==locked==reopened=='approve' else 'WEAK'


@probe('N18', 'punctuation that distinguishes merchants is discarded')
def _():
    from accounting_agent.core import normalize
    pairs = [('A+ CLEANERS', 'A CLEANERS'), ('#1 PIZZA', '1 PIZZA'), ('C++ CONSULTING', 'C CONSULTING'), ('AT&T', 'AT T')]
    for a, b in pairs:
        print('  %-16r %-16r equal=%s' % (a, b, normalize(a) == normalize(b)))
    return 'NOTE'


print('\n================ supplementary')
for pid, verdict, title in RESULTS[-3:]:
    print('%-4s %-9s %s' % (pid, verdict, title))


GATE = ('N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N07')
MUST_HOLD = ('P07','P08','P12','P13','P15','N08','N09','N10','N14','N15','N17','P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P09', 'P10', 'P11', 'P14', 'P16', 'N11', 'N12', 'N13')
verdicts = {pid: v for pid, v, _ in RESULTS}
failed = [p for p in GATE + MUST_HOLD if verdicts.get(p) != 'OK'] + [p for p, v in verdicts.items() if v == 'ERROR']
print('\nCorrective gate (C-01 to C-06), retained in Batch 2:', 'PASS' if not failed else 'FAIL ' + ', '.join(sorted(set(failed))))
sys.exit(1 if failed else 0)
