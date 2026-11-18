"""Legacy data check, service operations only: a temporary database is written by the previously
reviewed application version (empty-freshness mandate, untyped close checklist), then opened by the
corrected version, which must migrate it. Usage:
  python3 legacy_upgrade_check.py old <old-root> <db> <facts.json>
  python3 legacy_upgrade_check.py new <new-root> <db> <facts.json>"""
import json, sys
from pathlib import Path
mode, root, db, facts = sys.argv[1:5]
sys.path.insert(0, root)
from accounting_agent.core import Actor
from accounting_agent.demo import load
from accounting_agent.service import AccountingOS
ORG, CLIENT = 'demo_org', 'bird_bowl_demo'; SCOPE = ORG + '/' + CLIENT + '/local'
H = lambda n, r: Actor(n, r, ORG, CLIENT, kind='human')
ADMIN, PREP, CTRL, REV, PADMIN = H('lg-admin', 'administrator'), H('lg-preparer', 'preparer'), H('lg-policy', 'reviewer'), H('lg-reviewer', 'reviewer'), H('lg-period', 'reviewer')
WORKER = Actor('lg-worker', 'worker', ORG, CLIENT, kind='service')
os_ = AccountingOS(Path(db), [SCOPE])
if mode == 'old':
    profile = load('config/bird_bowl.demo.json')
    sid = os_.onboard(PREP, profile)
    os_.grant_authority(ADMIN, CTRL.id, ['approve_profile', 'approve_rule', 'approve_mandate'], 'fictional legacy fixture'); os_.grant_authority(ADMIN, REV.id, ['review'], 'fictional legacy fixture')
    os_.approve_profile_version(CTRL, sid, 'fictional legacy fixture'); os_.open_period(PADMIN, '2026-11', '2026-11-01', '2026-11-30', 'fictional legacy fixture')
    docs = [{'kind': 'document', 'key': 'label-' + t, 'data': {'document_type': t, 'content': 'Fictional label-only document', 'period_id': '2026-11'}} for t in ('trial_balance', 'card_statement', 'bank_reconciliation', 'ap_tieout', 'ar_tieout')]
    os_.intake(PREP, {'synthetic': True, 'organization_id': ORG, 'client_id': CLIENT, 'external_company_id': profile['external_company_id'], 'batch_id': 'legacy', 'sources': docs})
    mid = os_.create_mandate(PREP, ['close_readiness'], '2026-11-15T00:00:00+00:00', '2026-11-25T00:00:00+00:00', 86400, 5, {'kind': 'fixed', 'period_id': '2026-11'}, {})
    os_.approve_mandate(CTRL, mid, 'fictional legacy standing authority'); os_.tick(PREP, '2026-11-15T12:00:00+00:00'); os_.drain(WORKER, now='2026-11-15T12:00:00+00:00')
    st = os_.export(PREP)
    out = {'checklist': profile['required_close_evidence'], 'mandate': [(m['id'], m['status'], m['active'], m['freshness']) for m in st['mandates']], 'mandate_runs': len([r for r in st['runs'] if r['mandate_id']]),
           'artifacts': [(a['id'], a['hash']) for a in st['artifacts']], 'audit_rows': len(st['audit_history']), 'evidence': [(s['id'], s['hash']) for s in st['evidence_history']]}
    json.dump(out, open(facts, 'w'))
    print('old version wrote: checklist', out['checklist'], '| mandate', out['mandate'], '| mandate runs', out['mandate_runs'])
else:
    before = json.load(open(facts)); st = os_.export(PREP)
    m = [(x['id'], x['status'], x['active'], x['reason']) for x in st['mandates']]
    ev = [a['event'] for a in st['audit_history'] if a['event'] in ('legacy_mandate_suspended', 'schema_migrated')]
    new_runs = os_.tick(PREP, '2026-11-16T12:00:00+00:00')
    same = [list(x) for x in before['artifacts']] == [[a['id'], a['hash']] for a in st['artifacts']] and [list(x) for x in before['evidence']] == [[s['id'], s['hash']] for s in st['evidence_history']]
    os_.enqueue(PREP, 'close_readiness', '2026-11'); os_.drain(WORKER)
    c = [a for a in os_.state(PREP)['artifacts'] if a['item_key'] == 'close-checklist' and a['governing']][0]
    res = [(r['requirement'].get('document_type'), r['satisfied'], r.get('reason')) for r in c['payload']['data']['requirements']]
    print('corrected version reads the same database -> mandate:', m, '| migration events:', ev, '| runs dispatched by the next tick:', new_runs)
    print('earlier artifacts and evidence byte-identical:', same, '| audit chain verifies:', os_.verify_audit(PREP), '| audit rows before/after:', before['audit_rows'], len(st['audit_history']))
    print('legacy untyped checklist evaluated:', res, '| blockers:', c['blockers'])
    ok = (m and m[0][1] == 'needs_reconfirmation' and not m[0][2] and 'legacy_mandate_suspended' in ev and new_runs == [] and same and os_.verify_audit(PREP)
          and all(not r[1] and r[2] == 'UNTYPED_REQUIREMENT' for r in res) and 'MISSING_CLOSE_EVIDENCE' in c['blockers'])
    print('legacy upgrade result:', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
