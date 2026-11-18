"""Assemble FABLE_RF_ACCEPTANCE_RESULTS.json from the raw outputs of this review (read-only on the outputs)."""
import hashlib, json, re, sys
from collections import Counter
from pathlib import Path

R = Path('/private/tmp/claude-501/rf'); OUT = R / 'out'; DELIVER = R / 'deliver'; NEW = R / 'rf_x'
BUNDLE = 'c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd'
RE = '4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae'
REPORT = 'exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verdicts(path):
    t = Path(path).read_text(); t = t.split('\nSUMMARY\n')[-1] if '\nSUMMARY\n' in t else t
    return re.findall(r'(?m)^\s*(\S+)\s+(\S+)\s+(OK|WEAK|ERROR|NOTE)\b', t)


def cmd(label):
    d = json.loads((OUT / (label + '.json')).read_text())
    return {'label': label, 'argv': d['argv'], 'exit_code': d['exit_code'], 'elapsed_seconds': d['elapsed_seconds'], 'started_utc': d['started_utc'],
            'stdout': 'evidence/commands/%s.stdout.txt' % label, 'stderr': 'evidence/commands/%s.stderr.txt' % label}


def original_search():
    fams = {}
    for f in sorted(OUT.glob('re-step-search-*.results.json')):
        d = json.loads(f.read_text()); name = d['results'][0]['family']
        fams[name] = {'runs': d['runs'], 'double': d['double'], 'released_without_authority': d['released'],
                      'approved_before_target_known': sum(1 for r in d['results'] if r['approved_before_target_known_at_steps']),
                      'audit_failures': sum(1 for r in d['results'] if not r['audit_ok'])}
    return {'runs': sum(v['runs'] for v in fams.values()), 'double': sum(v['double'] for v in fams.values()),
            'released_without_authority': sum(v['released_without_authority'] for v in fams.values()),
            'audit_failures': sum(v['audit_failures'] for v in fams.values()), 'families': fams}


def extended_search(prefix):
    fams = {}
    for f in sorted((OUT / 'search').glob(prefix + '*.results.json')):
        d = json.loads(f.read_text())
        for r in d['results']:
            v = fams.setdefault(r['family'], Counter()); v['runs'] += 1
            v['double'] += bool(r['double_at_steps']); v['released_without_authority'] += bool(r['released_at_steps']); v['unlinked_first_claim'] += bool(r['unlinked_at_steps'])
            v['repeat_checked'] += bool(r['repeat_checked']); v['repeat_changed'] += bool(r['repeat_failures']); v['repeat_of_retired_row'] += bool(r.get('repeat_of_retired_row'))
            v['audit_failures'] += (not r['audit_ok']); v['approved_before_target_known'] += bool(r['early_at_steps']); v['steps'] = len(r['order'])
    keys = ('runs', 'double', 'released_without_authority', 'unlinked_first_claim', 'repeat_checked', 'repeat_changed', 'repeat_of_retired_row', 'audit_failures', 'approved_before_target_known')
    fams = {k: {x: int(v[x]) for x in keys + ('steps',)} for k, v in fams.items()}
    total = {x: sum(v[x] for v in fams.values()) for x in keys}
    return dict(total, families=fams)


def fault(path):
    m = re.search(r'cases (\d+) \| agree (\d+) \| gaps (\d+)', Path(path).read_text())
    return {'cases': int(m.group(1)), 'agree': int(m.group(2)), 'gaps': int(m.group(3))}


def eq(label):
    t = (OUT / (label + '.stdout.txt')).read_text()
    m = re.search(r'RF-03 EQUIVALENCE (\{.*?\}) wrapped_script_exit=(\S+)', t)
    return dict(json.loads(m.group(1)), wrapped_script_exit=int(m.group(2)))


def suite(label):
    err = (OUT / (label + '.stderr.txt')).read_text(); meta = json.loads((OUT / (label + '.json')).read_text())
    ran = re.search(r'Ran (\d+) tests? in ([\d.]+)s', err); status = re.findall(r'(?m)^(OK|FAILED.*)$', err)
    row = {'label': label, 'exit_code': meta['exit_code'], 'started_utc': meta['started_utc'], 'methods_run': int(ran.group(1)) if ran else None, 'suite_seconds': float(ran.group(2)) if ran else None,
           'result_line': status[-1] if status else None, 'methods_ok': len(re.findall(r'(?m) \.\.\. ok$', err)), 'http_methods_ok': len(re.findall(r'(?m)\(test_http\.HTTPCase\) \.\.\. ok$', err)),
           'failures_or_errors': len(re.findall(r'(?m) \.\.\. (FAIL|ERROR)$', err)), 'skipped_or_expected_failures': len(re.findall(r'(?m) \.\.\. (skipped|expected failure)', err))}
    hook = OUT / (label + '.class-setup.jsonl')
    if hook.is_file():
        rows = [json.loads(l) for l in hook.read_text().splitlines() if l.strip()]
        http = [r for r in rows if r['class'] == 'HTTPCase']
        if http:
            row['http_class_setup_seconds'] = http[0]['setup_seconds']; row['http_worker_wait_seconds'] = http[0]['seconds_from_last_thread_start_to_end_of_setup']; row['http_setup_failed'] = http[0]['setup_failed']
    for when in ('before', 'after'):
        u = OUT / ('%s.uptime-%s.txt' % (label, when))
        if u.is_file():
            row['load_averages_' + when] = u.read_text().split('load averages:')[-1].strip()
    return row


own = verdicts(DELIVER / 'fable_rf_acceptance_output.txt')
base = verdicts(OUT / 'baseline-re-source-rf-probes.stdout.txt')
labels = [p.stem for p in sorted(OUT.glob('*.json')) if not p.name.endswith('.results.json') and not p.name.startswith('_')]
commands = [cmd(l) for l in labels]
suites = [suite('consecutive-make-test-%d' % i) for i in range(1, 6) if (OUT / ('consecutive-make-test-%d.json' % i)).is_file()]
extra_suites = [suite(l) for l in ('make-test-under-load', 'make-test-idle-no-hook') if (OUT / (l + '.json')).is_file()]
orig = original_search(); ext = extended_search('rf-'); ext_base = extended_search('baseline-re-')
_uc20 = json.loads([l for l in (OUT / 'uc20-from-trails.txt').read_text().splitlines() if l.startswith('{"UC20_JSON"')][0])['UC20_JSON']
for _n, _v in ext['families'].items():
    _c = _uc20[_n]
    _v['uc20_orders_approved_while_an_ancestor_claim_waits'] = _c.get('orders_waiting', 0); _v['uc20_orders_waiting_claimant_itself_approved'] = _c.get('orders_direct', 0)
    _v['uc20_orders_approval_survived_target_arrival'] = _c.get('orders_survived', 0); _v['uc20_orders_stopped_and_held_on_arrival'] = _c.get('orders_held_on_arrival', 0)
for _k in ('uc20_orders_approved_while_an_ancestor_claim_waits', 'uc20_orders_waiting_claimant_itself_approved', 'uc20_orders_approval_survived_target_arrival', 'uc20_orders_stopped_and_held_on_arrival'):
    ext[_k] = sum(v[_k] for v in ext['families'].values())
ext['uc20_note'] = "approved_before_target_known is the script's own flag, which fires only when the missing row is itself a locked row and is 0 by construction in these families; the uc20_* counts are taken from the kept trails by evidence/scripts/uc20_from_trails.py"
uc20_ok = ext['uc20_orders_waiting_claimant_itself_approved'] == 0 and ext['uc20_orders_approval_survived_target_arrival'] == 0 and ext['uc20_orders_stopped_and_held_on_arrival'] == ext['uc20_orders_approved_while_an_ancestor_claim_waits']
five_ok = len(suites) == 5 and all(s['exit_code'] == 0 and s['methods_run'] == 241 and s['http_methods_ok'] == 11 and s['result_line'] == 'OK' for s in suites)
search_ok = orig['runs'] == 480 and orig['double'] == 0 and orig['released_without_authority'] == 0 and orig['audit_failures'] == 0 and \
    ext['double'] == 0 and ext['released_without_authority'] == 0 and ext['unlinked_first_claim'] == 0 and ext['repeat_changed'] == 0 and ext['audit_failures'] == 0 and uc20_ok
probes_ok = not [v for v in own if v[2] in ('WEAK', 'ERROR')]
eq_labels = [l for l in labels if l.startswith('eq-')]
eqs = {l: eq(l) for l in eq_labels}
eq_ok = all(v['mismatches'] == 0 and v['autocommit_calls_that_reused'] == 0 for v in eqs.values())
rf01 = probes_ok and search_ok
print('five consecutive suites ok:', five_ok, '| searches ok:', search_ok, '| own probes ok:', probes_ok, '| equivalence ok:', eq_ok)

V, F = 'Independently verified', 'Verification failed'
state = V if (rf01 and five_ok and eq_ok) else F
rv = lambda i, criterion, evidence, st=state, concl=None: {'id': i, 'state': st, 'conclusion': concl or ('May be recorded Independently verified at this checkpoint, for this scope' if st == V else 'Remains Verification failed'),
                                                             'criterion': criterion, 'evidence': evidence, 'bundle_sha256': BUNDLE, 'report_path': REPORT}
results = {
    'title': 'Fable independent verification of RF-01 to RF-03 and PRV-16 under unchanged D-026 and D-029',
    'date': '2026-11-17',
    'reviewed_bundle': 'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip',
    'bundle_sha256': BUNDLE,
    'checkpoints': {
        'reviewed_bundle_sha256': BUNDLE,
        'internal_review_manifest_sha256': sha(NEW / 'REVIEW_MANIFEST.json'),
        'payload_files_hash_verified': 1790,
        'baseline_re_bundle_sha256': RE,
        're_review_response_sha256': 'e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a',
        'codex_rf_prompt_sha256': sha(NEW / 'CODEX_RF_CORRECTIONS_PROMPT.md'),
        'fable_rf_review_prompt_sha256': sha(NEW / 'FABLE_RF_REVIEW_PROMPT.md'),
        'register_sha256_at_this_checkpoint': sha(NEW / 'docs/PRODUCT_REQUIREMENTS.md'),
        'decisions_sha256_at_this_checkpoint': sha(NEW / 'DECISIONS.md'),
        'source_and_tests_patch_sha256': sha(NEW / 'docs/corrections_rf/source-and-tests.patch'),
        'git': {'branch': 'review/fable-rc-acceptance', 'head': '5af9a6194bc39e2f303cc6b43b0b59094118b8e4', 'commits': 10, 'commit_added_by_the_developer_pass': False},
    },
    'scope_of_every_conclusion': 'Synthetic local preparation controls at the reviewed bundle hash only. No client accounting policy, reconciliation completion, close or operating readiness. No human G0, G1-G4 or Batch 3 authority. Developer passes are not independent acceptance.',
    'ticket_verdicts': [
        {'id': 'RF-01', 'priority': 'P1', 'clause': '2', 'verdict': 'ACCEPTED' if rf01 else 'NOT ACCEPTED',
         'reason': 'A claim-free older or conflicting message that is re-sent carrying the row\'s first claim now applies that claim: linked at once when the target is on file, held with its receipt when the chain reaches the locked period, waiting as unresolved and linking without a re-send when the target arrives. No other path was found on which a first claim is recorded without being applied.',
         'probes': ['C2d', 'C2f', 'G1a', 'G1b', 'G1c', 'G1d', 'G1e', 'G1f', 'G1g', 'G1h'], 'searches': ['fable_re_step_search.py (480)', 'fable_rf_step_search.py (%d)' % ext['runs']]},
        {'id': 'RF-02', 'priority': 'P3', 'clause': '9', 'verdict': 'ACCEPTED' if probes_ok else 'NOT ACCEPTED',
         'reason': 'Every person who recorded a target selection stays a contributor of the row, its revisions and its live replacements after confirming and replacing selections and after the replacement is retargeted; none can approve or finalize; an independent person can. Earlier records are byte-identical. Ordinary dispositions behave exactly as at the RE checkpoint. Scopes are isolated.',
         'probes': ['C9h', 'G2a', 'G2b', 'G2c', 'G2d', 'G2e', 'G2f']},
        {'id': 'RF-03', 'priority': 'P3', 'clause': None, 'verdict': 'ACCEPTED' if (five_ok and eq_ok) else 'NOT ACCEPTED',
         'reason': 'The shortcut gives the same report as the full computation at every call made by seven probe suites, one search family and the demo data; it is local to one call inside one transaction and is not used outside a transaction. tests/test_http.py and its five-second deadline are byte-identical. Five consecutive complete make test runs, made one after another with no other job of this review running, passed all 241 methods, the 11 HTTP methods included; under the same load the delivered HTTP setup finishes sooner than that of the RD checkpoint.' if (five_ok and eq_ok) else 'See the report.',
         'evidence': ['evidence/equivalence.txt', 'evidence/http-setup-timing.txt', 'evidence/commands/consecutive-make-test-1..5']},
        {'id': 'PRV-16', 'priority': None, 'clause': None, 'verdict': 'ACCEPTED',
         'reason': 'The fourth authority (RE results and report) is hash pinned; the latest verdict wins per record; the seven rows keep their original order; no acceptance criterion, state, product decision or protected record changed; D-026 and D-029 text and the schema are byte-identical.',
         'evidence': ['evidence/fable-rf-register-faults.txt', 'evidence/preservation.txt']},
        {'id': 'RE-01 / RB-01', 'priority': None, 'clause': '2', 'verdict': 'ACCEPTED' if rf01 else 'NOT ACCEPTED', 'reason': 'RF-01 was the only remaining failure of RE-01; with it corrected, RB-01 holds for every delivery order tried.'},
    ],
    'clause_verdicts': [
        {'clause': 1, 'title': 'Provider order', 'verdict': 'HOLDS', 'probes': ['C2a', 'G1a', 'G1f', 'G1g', 'Y01', 'Y02']},
        {'clause': 2, 'title': 'Claim on a late, older or conflicting message', 'verdict': 'HOLDS' if rf01 else 'FAILS', 'probes': ['C2a', 'C2b', 'C2c', 'C2d', 'C2e', 'C2f', 'G1a', 'G1b', 'G1d', 'G1f', 'G1g', 'G1h']},
        {'clause': 3, 'title': 'Claim after its row', 'verdict': 'HOLDS', 'probes': ['C2a', 'C7c', 'C7d', 'G1a', 'G1h', 'Y01', 'Y02', 'Y03', 'Y04', 'E01']},
        {'clause': 4, 'title': 'Claim before its target', 'verdict': 'HOLDS', 'probes': ['C2a', 'C7a', 'C9c', 'G1a', 'G1c', 'G1d', 'G1e'], 'observation': 'UC-20 (unchanged)'},
        {'clause': 5, 'title': 'Identical repeat', 'verdict': 'HOLDS for a repeated claim', 'probes': ['C2a', 'C2c', 'C7b', 'C9d', 'G1a', 'G1b', 'E02', 'E04', 'E05'], 'observation': 'UC-21, UC-22 (both the same at the RE checkpoint)'},
        {'clause': 6, 'title': 'Later omission', 'verdict': 'HOLDS', 'probes': ['C8a', 'G1d', 'G1e', 'Y04', 'Y06']},
        {'clause': 7, 'title': 'Second claim naming a different target', 'verdict': 'HOLDS', 'probes': ['C7a', 'C7b', 'C7c', 'C7d', 'C2c', 'G1b']},
        {'clause': 8, 'title': 'Release from a locked-period hold', 'verdict': 'HOLDS', 'probes': ['C8a', 'C8b', 'C8c', 'C9d'], 'searches': 'no release in %d orders' % (orig['runs'] + ext['runs'])},
        {'clause': 9, 'title': 'Who may disposition', 'verdict': 'HOLDS', 'probes': ['C9a', 'C9b', 'C9c', 'C9d', 'C9e', 'C9f', 'C9g', 'C9h', 'G2a', 'G2b', 'G2d', 'G2e', 'G2f'], 'observation': 'UC-17, UC-18 (unchanged), UC-23'},
    ],
    'contract_promise': {'verdict': 'MET in every delivery order tried' if rf01 else 'NOT MET',
                         'reason': 'No charge is approved in locked November and again in open December, and nothing leaves a locked-period hold without a person\'s authority, in %d stepwise orders and in every probe.' % (orig['runs'] + ext['runs'])},
    'register_verdicts': [
        rv('AAOS-BNK-03', 'one charge approved in two periods, for every delivery order within the feed contract of D-026',
           'RF-01 accepted: C2d and C2f OK; 21 RE probes 19 OK with C9c and C9g NOTE; own probes G1a-G1h OK (G1c and G1g NOTE); 480 original and %d further stepwise orders with 0 double approvals, 0 releases, 0 unlinked first claims; 12 supplied RD probes and adapted Y05 OK; 336 and 120 supplied orders 0 double.' % ext['runs']),
        rv('AAOS-CTL-04', 'a replacement chain never leaves the same expense approved in two periods', 'as AAOS-BNK-03; clause 8 holds in every delivery tried; RF-02 accepted (C9h, G2a-G2f)'),
        rv('AAOS-GOV-03', 'known repaired defects must pass',
           'RB-01 is accepted at this checkpoint (RF-01). All 227 earlier methods present, 226 unchanged, one rewritten under D-031; every retained gate passes; five consecutive complete make test runs pass 241 methods (RF-03).'),
        rv('AAOS-KNO-04', None, 'R02a, R02b, N03a, N03b, N03c', V, 'Unchanged; its probes still report OK at this checkpoint'),
        rv('AAOS-CTL-01', None, 'R02a, R02b, N03a, N03b, N04a', V, 'Unchanged; its probes still report OK at this checkpoint'),
        rv('AAOS-BNK-02', None, 'R04a, R04b, R04c, N02b, N04a to N04d; N04e NOTE', V, 'Unchanged; its probes still report OK at this checkpoint; UC-11 stays open'),
        rv('AAOS-CTL-09', None, 'R03a, R03b, R04a, R04b, R04c, N02a, N02b, N04a to N04d, Q02; N02c NOTE', V, 'Unchanged; its probes still report OK at this checkpoint; UC-10 stays open'),
    ],
    'own_probes': {'script': 'fable_rf_acceptance_probes.py', 'output': 'fable_rf_acceptance_output.txt',
                   'assertions': len(re.findall(r'(?m)^    assert ', (DELIVER / 'fable_rf_acceptance_output.txt').read_text())),
                   'assertions_failed': len(re.findall(r'(?m)^    assert .* NO$', (DELIVER / 'fable_rf_acceptance_output.txt').read_text())),
                   'verdicts': [{'id': a, 'ticket': b.replace('_', ' '), 'verdict': c} for a, b, c in own],
                   'on_the_re_checkpoint_source': {'counts': dict(Counter(v[2] for v in base)), 'verdicts': {a: c for a, b, c in base}, 'output': 'evidence/baseline-re-source-rf-probes.txt'}},
    'own_order_search': {'original_script_unchanged': dict(orig, script='exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py'),
                         'extended': dict(ext, script='fable_rf_step_search.py'),
                         'extended_on_the_re_checkpoint_source_six_families': ext_base},
    'supplied_checks': {
        're_probes_21': dict(Counter(v[2] for v in verdicts(OUT / 're-probes-21.stdout.txt'))),
        're_probes_21_notes': [v[0] for v in verdicts(OUT / 're-probes-21.stdout.txt') if v[2] == 'NOTE'],
        'rd_probes_12': dict(Counter(v[2] for v in verdicts(OUT / 'rd-probes-12.stdout.txt'))),
        'adapted_y05': dict(Counter(v[2] for v in verdicts(OUT / 'y05-adapted.stdout.txt'))),
        'rd_order_search': re.findall(r'(?m)^SUMMARY.*$', (OUT / 'rd-order-search-336.stdout.txt').read_text()),
        'rc_probes': dict(Counter(v[2] for v in verdicts(OUT / 'rc-probes.stdout.txt'))),
        'rc_order_search': re.findall(r'(?m)^SUMMARY.*$', (OUT / 'rc-order-search-120.stdout.txt').read_text()),
        'rb_probes': dict(Counter(v[2] for v in verdicts(OUT / 'rb-probes.stdout.txt'))),
        'ra_probes': re.findall(r'(?m)^Verdict counts.*$', (OUT / 'ra-probes.stdout.txt').read_text()),
        'reviewer_cases': re.findall(r'(?m)^Summary:.*$', (OUT / 'make-batch2-gate.stdout.txt').read_text()),
        'older_acceptance_gate': re.findall(r'(?m)^Verdict counts.*$', (OUT / 'make-acceptance-gate.stdout.txt').read_text()),
        'gate_targets': {l[5:]: json.loads((OUT / (l + '.json')).read_text())['exit_code'] for l in labels if l.startswith('make-') and 'test' not in l},
    },
    'fault_injection': {
        'register_F_unchanged': fault(OUT / 'rb-register-faults-F.stdout.txt'), 'register_G_unchanged': fault(OUT / 'rc-register-faults-G.stdout.txt'),
        'register_H_unchanged': dict(fault(OUT / 'rd-register-faults-H.stdout.txt'), disagree=['H22', 'H23', 'H24'], reason='written when the RC review was the latest authority'),
        'register_J_unchanged': dict(fault(OUT / 're-register-faults-J.stdout.txt'), disagree=['J14', 'J15', 'J16', 'J18', 'J22', 'J25'], reason='written when the RD review was the latest authority and the RE bundle was unreviewed'),
        'register_K_own_fourth_authority': fault(OUT / 'rf-register-faults-K.stdout.txt'),
        're_gate_K_unchanged': fault(OUT / 're-gate-faults-K-unchanged.stdout.txt'),
        'rf_gate_M_own': fault(OUT / 'rf-gate-faults-M.stdout.txt') if (OUT / 'rf-gate-faults-M.stdout.txt').is_file() else None,
        'rf_gate_on_re_checkpoint_source': {'exit_code': json.loads((OUT / 'gate-negative-rf-gate-on-re-source.json').read_text())['exit_code'], 'expected': 'non-zero'},
    },
    'rf03_equivalence': eqs,
    'make_test': {'five_consecutive_runs': suites, 'other_runs': extra_suites, 'http_setup_timing': 'evidence/http-setup-timing.txt'},
    'preservation': {'earlier_test_methods': 227, 'present': 227, 'unchanged': 226,
                     'rewritten_under_D-031': ['tests/test_product_requirements.py::ProductRequirements::test_PRV14_third_authority_is_pinned_and_latest_verdict_controls'],
                     'methods_added': {'tests/test_product_requirements_rf.py': 5, 'tests/test_review_corrections_rf.py': 6, 'tests/test_rf_review_gate.py': 3},
                     'skips_or_expected_failures': 0, 'tests_test_http_py_byte_identical': True, 'schema_byte_identical': True, 'adapted_y05_byte_identical': True,
                     'decisions_md_re_text_is_unchanged_prefix': True, 'register_records': 88, 'register_records_changed': ['AAOS-GOV-02', 'AAOS-GOV-03', 'AAOS-BNK-03', 'AAOS-CTL-04'],
                     'register_fields_changed': ['Scope note', 'Evidence'], 'protected_inputs_verified_in_bundle_and_working_project': 1198, 'prior_archives_verified': 16,
                     'changed_files_vs_re_bundle': 15, 'added_files_vs_re_bundle': 453, 'removed_files': 0, 'patch_reproduces_code_tests_scripts_review_makefile': 89,
                     'working_project_equals_bundle_payload': 1790},
    'commands': commands,
    'corrective_tickets': 'FABLE_RF_CORRECTIONS.json',
    'open_items_unchanged': ['U4', 'UC-14', 'UC-17', 'UC-18', 'UC-20', 'X08', 'N02c', 'N04e', 'C9c', 'C9g', 'UC-9 reading only'],
    'new_observations_for_the_owner': ['UC-21', 'UC-22', 'UC-23', 'UC-24', 'UC-25'],
    'authorizes': 'Nothing. No implementation, no promotion of any requirement by itself, no readiness, no live action. Recording the three verdicts in the register is a separate, owner-assigned change.',
}
(DELIVER / 'FABLE_RF_ACCEPTANCE_RESULTS.json').write_text(json.dumps(results, indent=1) + '\n')
print('written', DELIVER / 'FABLE_RF_ACCEPTANCE_RESULTS.json')
print(json.dumps({'ticket_verdicts': [(t['id'], t['verdict']) for t in results['ticket_verdicts']], 'register': [(r['id'], r['state']) for r in results['register_verdicts']]}))
