"""Assemble FABLE_RE_ACCEPTANCE_RESULTS.json from the raw outputs of this review (read-only on the outputs)."""
import hashlib, json, re, sys
from collections import Counter
from pathlib import Path

OUT = Path('/tmp/fre/out'); DELIVER = Path('/tmp/fre/deliver'); NEW = Path('/tmp/fre/extract')
BUNDLE = '4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae'
RD = '0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verdicts(path):
    t = Path(path).read_text(); t = t.split('\nSUMMARY\n')[-1] if '\nSUMMARY\n' in t else t
    return re.findall(r'(?m)^\s*(\S+)\s+(\S+)\s+(OK|WEAK|ERROR|NOTE)\b', t)


def cmd(label):
    d = json.loads((OUT / (label + '.json')).read_text())
    return {'label': label, 'argv': d['argv'], 'exit_code': d['exit_code'], 'elapsed_seconds': d['elapsed_seconds'], 'started_utc': d['started_utc'],
            'stdout': 'evidence/commands/%s.stdout.txt' % label, 'stderr': 'evidence/commands/%s.stderr.txt' % label}


def search(prefix):
    fams = {}
    for f in sorted(OUT.glob(prefix + '*.results.json')):
        d = json.loads(f.read_text()); name = d['results'][0]['family']
        fams[name] = {'runs': d['runs'], 'double': d['double'], 'released_without_authority': d['released'],
                      'approved_before_target_known': sum(1 for r in d['results'] if r['approved_before_target_known_at_steps']),
                      'audit_failures': sum(1 for r in d['results'] if not r['audit_ok']),
                      'orders_with_double': [' '.join(r['order']) for r in d['results'] if r['double_at_steps']]}
    return {'runs': sum(v['runs'] for v in fams.values()), 'double': sum(v['double'] for v in fams.values()),
            'released_without_authority': sum(v['released_without_authority'] for v in fams.values()),
            'audit_failures': sum(v['audit_failures'] for v in fams.values()), 'families': fams}


own = verdicts(DELIVER / 'fable_re_acceptance_output.txt')
exp = verdicts(OUT / 'experiment/fable-re-probes.stdout.txt') if (OUT / 'experiment/fable-re-probes.stdout.txt').is_file() else []
base = verdicts(OUT / 'baseline-rd-source-re-probes.txt')
labels = [p.stem for p in sorted(OUT.glob('*.json')) if not p.name.endswith('.results.json') and p.name != 'diff-vs-rd-archive.json']
commands = [cmd(l) for l in labels]
fault = lambda f: re.search(r'cases (\d+) \| agree (\d+) \| gaps (\d+)', (OUT / f).read_text()).groups()

results = {
    'title': "Fable independent verification of RE-01 to RE-03 and PRV-14/PRV-15 under D-026 and owner clarification D-029",
    'date': '2026-11-16',
    'reviewed_bundle': 'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip',
    'bundle_sha256': BUNDLE,
    'checkpoints': {
        'reviewed_bundle_sha256': BUNDLE,
        'internal_review_manifest_sha256': sha(NEW / 'REVIEW_MANIFEST.json'),
        'payload_files_hash_verified': 1337,
        'baseline_rd_bundle_sha256': RD,
        'rd_review_response_sha256': '97f062e5a1a36ffb995f149bd33c1cfe035453e1d6e837bbc7a9f9f636128b27',
        'codex_re_prompt_sha256': sha(NEW / 'CODEX_RE_CORRECTIONS_PROMPT.md'),
        'register_sha256_at_this_checkpoint': sha(NEW / 'docs/PRODUCT_REQUIREMENTS.md'),
        'decisions_sha256_at_this_checkpoint': sha(NEW / 'DECISIONS.md'),
        'git': {'branch': 'review/fable-rc-acceptance', 'head': '542688b57ece08ea55082d68b713ccf6433fd8ce', 'commits': 8},
    },
    'scope_of_every_conclusion': 'Synthetic local preparation controls at the reviewed bundle hash only. No client accounting policy, reconciliation completion, close or operating readiness. No human G0, G1-G4 or Batch 3 authority. Developer passes are not independent acceptance.',
    'ticket_verdicts': [
        {'id': 'RE-01', 'clause': '2', 'verdict': 'NOT ACCEPTED', 'reason': 'RF-01 (P1): a claim on an older message that repeats an already retained message is recorded but never applied; with a later replacement row one charge is approved in locked November and approved and finalized in open December.', 'probes': {'hold': ['C2a', 'C2b', 'C2c', 'C2e', 'E03', 'E03c'], 'fail': ['C2d', 'C2f']}},
        {'id': 'RE-02', 'clause': '7 with D-029', 'verdict': 'ACCEPTED', 'probes': {'hold': ['C2c', 'C7a', 'C7b', 'C7c', 'C7d', 'E02', 'E06', 'Y05(a) adapted']}},
        {'id': 'RE-03', 'clause': '8 and 9', 'verdict': 'ACCEPTED', 'reason': 'One neighbouring gap in review independence, RF-02 (P3); observations UC-17, UC-18.', 'probes': {'hold': ['C8a', 'C8b', 'C8c', 'C9a', 'C9b', 'C9d', 'C9e', 'C9f'], 'note': ['C9c', 'C9g', 'C9h']}},
        {'id': 'PRV-14', 'verdict': 'ACCEPTED', 'evidence': 'evidence/register-diff.txt; evidence/fable-re-register-faults.txt'},
        {'id': 'PRV-15', 'verdict': 'ACCEPTED', 'evidence': 'evidence/fable-re-register-faults.txt J02-J09; unchanged H13, H14 reject'},
        {'id': 'RB-01 as a whole', 'verdict': 'NOT ACCEPTED', 'reason': 'RF-01'},
        {'id': 'make test', 'verdict': 'PASSES, NOT DEPENDABLY', 'reason': 'RF-03 (P3): three unmodified runs exit 2, 2, 0; the two failures are the unchanged five-second HTTP class setup deadline (216 methods OK, 11 HTTP methods not run); run 3 passes 227; no assertion failed in any run.'},
    ],
    'clause_verdicts': [
        {'clause': 1, 'title': 'Provider order', 'verdict': 'HOLDS', 'probes': ['C2a', 'Y01', 'Y02']},
        {'clause': 2, 'title': 'Claim on a late, older or conflicting message', 'verdict': 'FAILS IN ONE BRANCH', 'ticket': 'RF-01', 'probes_hold': ['C2a', 'C2b', 'C2c', 'C2e'], 'probes_fail': ['C2d', 'C2f']},
        {'clause': 3, 'title': 'Claim after its row', 'verdict': 'HOLDS', 'probes': ['C2a', 'C7c', 'C7d', 'Y01', 'Y02', 'Y03', 'Y04', 'E01']},
        {'clause': 4, 'title': 'Claim before its target', 'verdict': 'HOLDS EXCEPT AS A CONSEQUENCE OF RF-01', 'probes': ['C2a', 'C7a', 'C9c'], 'observation': 'UC-20'},
        {'clause': 5, 'title': 'Identical repeat', 'verdict': 'HOLDS', 'probes': ['C2a', 'C2c', 'C7b', 'C9d', 'C9g', 'E02', 'E04', 'E05']},
        {'clause': 6, 'title': 'Later omission', 'verdict': 'HOLDS', 'probes': ['C8a', 'Y04', 'Y06']},
        {'clause': 7, 'title': 'Second claim naming a different target', 'verdict': 'HOLDS', 'probes': ['C2c', 'C7a', 'C7b', 'C7c', 'C7d'], 'd029': 'frozen approval preserved; incoming version held; PERIOD_LOCKED refusal until reopen; contested blocker after reopen; nothing approved'},
        {'clause': 8, 'title': 'Release from a locked-period hold', 'verdict': 'HOLDS', 'probes': ['C8a', 'C8b', 'C8c', 'C9d'], 'search': 'no release without authority in any order'},
        {'clause': 9, 'title': 'Who may disposition', 'verdict': 'HOLDS', 'ticket': 'RF-02 (P3)', 'probes': ['C9a', 'C9b', 'C9c', 'C9d', 'C9e', 'C9f', 'C9g', 'C9h'], 'observations': ['UC-17', 'UC-18']},
    ],
    'contract_promise': {'verdict': 'NOT MET', 'reason': 'RF-01: one charge approved in locked November and approved and finalized in open December in an order the contract allows.'},
    'register_verdicts': [
        {'id': 'AAOS-BNK-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'one charge approved in two periods, for every delivery order within the feed contract of D-026', 'evidence': 'RE-02 and RE-03 accepted (C7a-C7d, C8a-C8c, C9a-C9f OK; 12 supplied probes OK; adapted Y05 OK; 336 supplied orders 0 double). RE-01 not accepted: C2d and C2f WEAK; own search finds double approval in family older-resent-with-claim (RF-01).', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-CTL-04', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'a replacement chain never leaves the same expense approved in two periods', 'evidence': 'as AAOS-BNK-03; clause 8 holds in every delivery tried', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-GOV-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'known repaired defects must pass', 'evidence': 'RB-01 is still not accepted (RF-01). The other parts were checked and hold: 205 earlier methods present, one authorized rewrite, every retained gate passes.', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-KNO-04', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N03c', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-CTL-01', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N04a', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-BNK-02', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-11 stays open', 'evidence': 'R04a, R04b, R04c, N02b, N04a to N04d; N04e NOTE', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
        {'id': 'AAOS-CTL-09', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-10 stays open', 'evidence': 'R03a, R03b, R04a, R04b, R04c, N02a, N02b, N04a to N04d, Q02; N02c NOTE', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'},
    ],
    'own_probes': {'script': 'fable_re_acceptance_probes.py', 'output': 'fable_re_acceptance_output.txt', 'assertions': (DELIVER / 'fable_re_acceptance_output.txt').read_text().count('    assert'),
                   'verdicts': [{'id': a, 'clause': b.replace('_', ' '), 'verdict': c} for a, b, c in own], 'counts': dict(Counter(v[2] for v in own)),
                   'on_rd_checkpoint_source': dict(Counter(v[2] for v in base)), 'with_experimental_rf01_line': dict(Counter(v[2] for v in exp))},
    'own_order_search': {'script': 'fable_re_step_search.py', 'delivered_source': search('step-search-'), 'with_experimental_rf01_line': search('experiment-step-search-')},
    'supplied_checks': {
        'rd_probes_12': dict(Counter(v[2] for v in verdicts(OUT / 'rd-probes-12.stdout.txt'))),
        'adapted_y05': dict(Counter(v[2] for v in verdicts(OUT / 'y05-adapted.stdout.txt'))),
        'rd_order_search': re.findall(r'(?m)^SUMMARY.*$', (OUT / 'rd-order-search-336.stdout.txt').read_text()),
        'rc_probes': dict(Counter(v[2] for v in verdicts(OUT / 'rc-probes.stdout.txt'))),
        'rc_order_search': re.findall(r'(?m)^SUMMARY.*$', (OUT / 'rc-order-search-120.stdout.txt').read_text()),
        'rb_probes': dict(Counter(v[2] for v in verdicts(OUT / 'rb-probes.stdout.txt'))),
        'ra_probes': re.findall(r'(?m)^Verdict counts.*$', (OUT / 'ra-probes.stdout.txt').read_text()),
        'reviewer_cases': re.findall(r'(?m)^Summary: .*$', (OUT / 'make-batch2-gate.stdout.txt').read_text()),
    },
    'fault_injection': {
        'register_F_unchanged': dict(zip(('cases', 'agree', 'gaps'), re.search(r'(\d+)\D+(\d+)\D+(\d+)', [l for l in (OUT / 'rb-register-faults-F.stdout.txt').read_text().splitlines() if 'agree' in l][-1]).groups())),
        'register_G_unchanged': [l for l in (OUT / 'rc-register-faults-G.stdout.txt').read_text().splitlines() if 'agree' in l or 'gaps' in l][-2:],
        'register_H_unchanged': dict(zip(('cases', 'agree', 'gaps'), fault('rd-register-faults-H.stdout.txt'))),
        'register_J_own': dict(zip(('cases', 'agree', 'gaps'), fault('fable-re-register-faults.txt'))),
        'gate_K_own': dict(zip(('cases', 'agree', 'gaps'), fault('fable-re-gate-faults.txt'))),
    },
    'preservation': {
        'earlier_test_methods': 205, 'present': 205, 'bodies_changed': ['tests/test_review_corrections_rd.py::ReviewCorrectionsRD::test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced'],
        'methods_added': {'tests/test_feed_contract.py': 16, 'tests/test_re_review_gate.py': 4, 'tests/test_product_requirements.py': 2},
        'y05_adaptation': 'four hunks, all inside part (a) (original lines 280-289)', 'skips_or_expected_failures': 0,
        'files_vs_rd_archive': {'removed': 0, 'changed': 17, 'added': 401}, 'schema_and_storage_unchanged': True,
        'patch_reproduces_delivered_source': True, 'prior_archives_unchanged': 16, 'protected_inputs_unchanged': 719,
    },
    'commands': commands,
    'corrective_tickets': 'FABLE_RE_CORRECTIONS.json',
    'open_items_unchanged': ['U4', 'UC-14', 'X08', 'N02c', 'N04e', 'UC-9 reading only'],
    'authorizes': 'Nothing. No implementation, no promotion of any requirement, no readiness, no live action.',
}
(DELIVER / 'FABLE_RE_ACCEPTANCE_RESULTS.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({k: results[k] for k in ('own_probes', 'fault_injection')}, indent=1)[:1500])
print(json.dumps(results['own_order_search'], indent=1)[:2500])
print([(c['label'], c['exit_code']) for c in commands])
