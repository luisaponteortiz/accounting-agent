"""Reviewer probes against the unmodified bundle. Synthetic data only; temp databases."""
import copy, sys, tempfile, traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from accounting_agent.core import Actor, ControlError
from accounting_agent.demo import SCOPE, actor, load, seed
from accounting_agent.service import AccountingOS

PROFILE = load('config/bird_bowl.demo.json')
PACKET = load('fixtures/teaching.json')
WORKER = actor('worker')
REVIEWER = actor('reviewer')


def fresh(seed_it=True):
    tmp = tempfile.TemporaryDirectory()
    os_ = AccountingOS(Path(tmp.name) / 'p.sqlite3', [SCOPE])
    if seed_it:
        seed(os_)
    os_._tmp = tmp
    return os_


def intake(os_, sources, batch, who=None):
    p = {k: v for k, v in PACKET.items() if k != 'sources'}
    p.update(batch_id=batch, sources=sources)
    return os_.intake(who or actor(), p)


def src(key):
    return copy.deepcopy(next(s for s in PACKET['sources'] if s['key'] == key))


def item(os_, key, workflow, run_id=None):
    st = os_.state(actor())
    rid = run_id or next(r for r in st['runs'] if r['workflow'] == workflow)['id']
    return next(a for a in st['artifacts'] if a['run_id'] == rid and a['item_key'] == key)


def approve(os_, a, who=REVIEWER, decision='approve'):
    os_.review(who, a['id'], a['hash'], a['fingerprint'], decision, 'probe')


def probe(name):
    def deco(fn):
        try:
            print('\n### ' + name)
            fn()
        except Exception as exc:
            print('  PROBE ERROR:', type(exc).__name__, exc)
            traceback.print_exc(limit=2)
    return deco


@probe('P01 same person supplies profile+evidence, a colleague enqueues, first person approves')
def _():
    os_ = fresh(False)
    a_prep = Actor('human-a', 'preparer', 'demo_org', 'bird_bowl_demo')
    b_prep = Actor('human-b', 'preparer', 'demo_org', 'bird_bowl_demo')
    a_rev = Actor('human-a', 'reviewer', 'demo_org', 'bird_bowl_demo')
    os_.onboard(a_prep, PROFILE)
    os_.intake(a_prep, PACKET)
    os_.enqueue(b_prep, 'journal_preparation')
    os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation')
    try:
        approve(os_, j, a_rev)
        print('  RESULT: approval ACCEPTED from the person who registered the policy and supplied the journal + support')
    except ControlError as e:
        print('  RESULT: denied:', e)


@probe('P02 independence check is a string prefix on actor id')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation')
    for ident in ('automation-agent-7', 'worker-of-the-month-jane'):
        try:
            approve(os_, j, Actor(ident, 'reviewer', 'demo_org', 'bird_bowl_demo'))
            print('  %-28s -> approval accepted' % ident)
        except ControlError as e:
            print('  %-28s -> denied (%s)' % (ident, e))


@probe('P03 recurring occurrence consumed when evidence arrives before the worker runs')
def _():
    os_ = fresh(); os_.drain(WORKER)
    os_.create_mandate(actor(), ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3)
    ids = os_.tick(actor(), '2026-11-15T12:00:00+00:00')
    os_.intake(actor(), load('fixtures/late_receipt.json'))
    os_.drain(WORKER, now='2026-11-15T12:05:00+00:00')
    again = os_.tick(actor(), '2026-11-15T13:00:00+00:00')
    os_.drain(WORKER, now='2026-11-15T13:05:00+00:00')
    st = os_.state(actor())
    run = next(r for r in st['runs'] if r['id'] == ids[0])
    arts = [a for a in st['artifacts'] if a['run_id'] == ids[0]]
    cur = [a for a in st['artifacts'] if a['current'] and a['kind'] == 'journal_proposal']
    print('  first tick run ids', ids, 'second tick', again)
    print('  occurrence run status:', run['status'], '| artifacts for occurrence:', len(arts), '| current journal artifacts for client:', len(cur))


@probe('P04 one mandate naming a workflow later removed from procedures blocks every tick')
def _():
    os_ = fresh(); os_.drain(WORKER)
    os_.create_mandate(actor(), ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3)
    os_.create_mandate(actor(), ['card_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3)
    p = copy.deepcopy(PROFILE); p['version'] = 'fictional-demo-2'; p['procedures'] = ['card_preparation', 'close_readiness']
    os_.onboard(actor(), p)
    try:
        print('  tick result:', os_.tick(actor(), '2026-11-15T12:00:00+00:00'))
    except ControlError as e:
        st = os_.state(actor())
        print('  tick RAISED:', e, '| mandate runs created:', sum(1 for r in st['runs'] if r['mandate_id']))


@probe('P05 two recurring occurrences on identical inputs give two current artifacts for one journal')
def _():
    os_ = fresh(); os_.drain(WORKER)
    os_.create_mandate(actor(), ['journal_preparation'], '2026-11-15T00:00:00+00:00', '2026-11-20T00:00:00+00:00', 86400, 3)
    r1 = os_.tick(actor(), '2026-11-15T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T12:00:01+00:00')
    r2 = os_.tick(actor(), '2026-11-16T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-16T12:00:01+00:00')
    a1 = item(os_, 'J-001', None, r1[0]); a2 = item(os_, 'J-001', None, r2[0])
    approve(os_, a1); approve(os_, a2, decision='reject')
    st = os_.state(actor())
    rows = [(a['run_id'], a['current'], a['review_status'], a['hash'][:8]) for a in st['artifacts'] if a['item_key'] == 'J-001']
    print('  J-001 artifacts (run, current, review_status, hash):', rows)
    print('  same journal source hash in both:', a1['payload']['data']['evidence'][0]['hash'] == a2['payload']['data']['evidence'][0]['hash'])


@probe('P06 non-Latin alias and a different non-Latin descriptor both normalise to the empty string')
def _():
    os_ = fresh(False)
    p = copy.deepcopy(PROFILE)
    p['vendors'].append({'id': 'demo_tokyo', 'name': 'Tokyo stationery (fictional)', 'aliases': ['東京文具'], 'category': 'DEMO_OFFICE_SUPPLIES'})
    os_.onboard(actor(), p); os_.intake(actor(), PACKET)
    tx = src('demo_card_001:TX-001'); tx['data']['description'] = '大阪修理'
    rc = src('receipt-TX-001'); rc['data']['vendor'] = '大阪修理'
    intake(os_, [tx, rc], 'unicode-1')
    os_.enqueue(actor(), 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  descriptor:', tx['data']['description'], '| matched vendor:', a['payload']['data']['vendor'], '| category:', a['payload']['data']['proposed_category'], '| eligible:', bool(a['eligible']), '| blockers:', a['blockers'])


@probe('P07 late delivery of an older batch silently replaces the newer source version')
def _():
    os_ = fresh()
    newer = src('demo_card_001:TX-001'); newer['data']['amount'] = '45.00'
    intake(os_, [newer], 'feed-seq-2')
    older = src('demo_card_001:TX-001')
    r = intake(os_, [older], 'feed-seq-1-arrived-late')
    st = os_.state(actor())
    s = next(s for s in st['sources'] if s['source_key'] == 'demo_card_001:TX-001')
    print('  intake result:', r, '| current version:', s['version'], '| current amount:', s['value']['amount'])


@probe('P08 journal support: unrelated document accepted; identical journal under a second key not flagged')
def _():
    os_ = fresh()
    j = src('J-001'); j['data']['supporting_keys'] = ['trial-balance-placeholder']
    dup = src('J-001'); dup['key'] = 'J-003'
    selfoff = src('J-001'); selfoff['key'] = 'J-004'; selfoff['data']['lines'][1]['account_id'] = 'DEMO_OFFICE_SUPPLIES'
    intake(os_, [j, dup, selfoff], 'journal-probe')
    os_.enqueue(actor(), 'journal_preparation'); os_.drain(WORKER)
    for k in ('J-001', 'J-003', 'J-004'):
        a = item(os_, k, 'journal_preparation')
        print('  %s eligible=%s blockers=%s' % (k, bool(a['eligible']), a['blockers']))


@probe('P09 locking the period voids the approvals it should protect')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); approve(os_, j)
    p = copy.deepcopy(PROFILE); p['version'] = 'fictional-demo-2'; p['period']['locked'] = True
    os_.onboard(actor(), p)
    st = os_.state(actor())
    print('  after lock, previously approved J-001 review_status:', next(a for a in st['artifacts'] if a['id'] == j['id'])['review_status'])
    os_.enqueue(actor(), 'journal_preparation'); os_.drain(WORKER)
    a = item(os_, 'J-001', 'journal_preparation')
    print('  re-prepared J-001 eligible=%s blockers=%s' % (bool(a['eligible']), a['blockers']))


@probe('P10 moving the profile to December strands November')
def _():
    os_ = fresh(); os_.drain(WORKER)
    c = item(os_, 'demo_card_001:TX-001', 'card_preparation'); approve(os_, c)
    p = copy.deepcopy(PROFILE); p['version'] = 'fictional-demo-2'; p['period'] = {'start': '2026-12-01', 'end': '2026-12-31', 'locked': False}
    os_.onboard(actor(), p)
    os_.enqueue(actor(), 'card_preparation'); os_.drain(WORKER)
    st = os_.state(actor())
    print('  approved November TX-001 now:', next(a for a in st['artifacts'] if a['id'] == c['id'])['review_status'])
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  re-prepared TX-001 eligible=%s blockers=%s' % (bool(a['eligible']), a['blockers']))


@probe('P11 any code change (here simulated) marks every approval stale')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); approve(os_, j)
    os2 = AccountingOS(os_.store.path, [SCOPE]); os2.code_hash = 'simulated-http-only-change'
    st = os2.state(actor())
    print('  J-001 review_status after unrelated code change:', next(a for a in st['artifacts'] if a['id'] == j['id'])['review_status'],
          '| current runs:', sum(r['current'] for r in st['runs']), 'of', len(st['runs']))


@probe('P12 close readiness: five placeholder documents, 13 open exceptions elsewhere')
def _():
    os_ = fresh()
    docs = [{'kind': 'document', 'key': 'doc-' + t, 'data': {'document_type': t, 'content': 'Placeholder text only; nothing reconciled; prior period.'}}
            for t in ('card_statement', 'bank_reconciliation', 'ap_tieout', 'ar_tieout')]
    intake(os_, docs, 'close-docs')
    for w in ('card_preparation', 'journal_preparation', 'close_readiness'):
        os_.enqueue(actor(), w)
    os_.drain(WORKER)
    st = os_.state(actor())
    a = item(os_, 'close-checklist', 'close_readiness')
    open_ex = sum(1 for x in st['artifacts'] if x['current'] and x['kind'] in ('card_proposal', 'journal_proposal') and x['blockers'])
    print('  missing_evidence:', a['payload']['data']['missing_evidence'], '| blockers:', a['blockers'])
    print('  open card/journal exceptions not referenced by checklist:', open_ex, '| checklist mentions them:', 'exceptions' in str(a['payload']['data']))


@probe('P13 statement control: swap one posted item for a different one with the same amount')
def _():
    os_ = fresh()
    # TX-003 (65.00, unknown vendor) is revised to pending (drops out of the posted population);
    # a new posted 65.00 item on another date enters. Count and total still agree.
    gone = src('demo_card_001:TX-003'); gone['data']['status'] = 'pending'
    new = src('demo_card_001:TX-001'); new['key'] = 'demo_card_001:TX-NEW'; new['data'].update(source_id='TX-NEW', date='2026-11-20', amount='65.00')
    intake(os_, [gone, new], 'swap')
    os_.enqueue(actor(), 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  TX-001 blockers after population swap:', a['blockers'], '| eligible:', bool(a['eligible']))


@probe('P14 repeated and contradictory decisions on one artifact')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation')
    other = Actor('human-demo-reviewer-2', 'reviewer', 'demo_org', 'bird_bowl_demo')
    approve(os_, j); approve(os_, j); approve(os_, j, other, 'reject'); approve(os_, j)
    a = item(os_, 'J-001', 'journal_preparation')
    print('  decisions:', [(d['actor'][-10:], d['decision']) for d in a['decisions']], '| review_status:', a['review_status'])


@probe('P15 receipt dated one day after the card transaction; receipt with tip-inclusive total')
def _():
    os_ = fresh()
    rc = src('receipt-TX-001'); rc['data']['date'] = '2026-11-02'
    intake(os_, [rc], 'receipt-date')
    os_.enqueue(actor(), 'card_preparation'); os_.drain(WORKER)
    a = item(os_, 'demo_card_001:TX-001', 'card_preparation')
    print('  purchase 11-02, posted 11-03 -> blockers:', a['blockers'])


@probe('P16 export immediately after approval and after an unrelated intake')
def _():
    os_ = fresh(); os_.drain(WORKER)
    j = item(os_, 'J-001', 'journal_preparation'); approve(os_, j)
    e1 = os_.export(actor())
    os_.intake(actor(), load('fixtures/late_receipt.json'))
    e2 = os_.export(actor())
    f = lambda e: [(a['item_key'], a['review_status']) for a in e['artifacts'] if a['id'] == j['id']]
    print('  before unrelated card receipt:', f(e1), '| after:', f(e2))
