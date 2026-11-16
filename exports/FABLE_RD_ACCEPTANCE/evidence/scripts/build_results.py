"""Assemble FABLE_RD_ACCEPTANCE_RESULTS.json from the raw logs in this review folder.

usage: build_results.py <review-folder>

Reads only files inside the review folder. Verdict text is the reviewer's; every number is parsed
from a log named next to it.
"""
import json, re, sys
from pathlib import Path

out = Path(sys.argv[1]); ev = out / 'evidence'
BUNDLE = '0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9'
BASE = '9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454'
REPORT = 'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md'
SCOPE = 'Synthetic local preparation controls exercised by the named probes and the retained gates, at the bundle checkpoint named. Not client policy, connected operation, reconciliation completion, close or operating readiness.'


def exit_codes(path, with_secs=True):
    rows = []
    for line in path.read_text().splitlines():
        m = re.match(r'(\S+) exit=(\d+)(?: secs=(\d+))?(?: :: (.*))?$', line)
        if m:
            row = {'label': m.group(1), 'exit_code': int(m.group(2))}
            if m.group(3): row['seconds'] = int(m.group(3))
            if m.group(4): row['command'] = re.sub(r'/private/tmp/\S*scratchpad/out/', '<review-folder>/', m.group(4))
            rows.append(row)
    return rows


def probe_summary(path):
    text = path.read_text(); rows = {}
    for m in re.finditer(r'(?m)^\s*(\S+)\s+(\S+)\s+(OK|WEAK|NOTE|ERROR)\s*$', text[text.rindex('SUMMARY'):]):
        rows[m.group(1)] = m.group(3)
    return rows


def tally(rows):
    return {v: sum(1 for x in rows.values() if x == v) for v in ('OK', 'NOTE', 'WEAK', 'ERROR')}


def search(path):
    d = json.loads(path.read_text()); fam = {}
    for r in d['results']:
        f = fam.setdefault(r['family'], {'orders': 0, 'double': 0}); f['orders'] += 1; f['double'] += bool(r['double'])
    return {'runs': d['runs'], 'double': d['double'], 'finalized_silently': sum(1 for r in d['results'] if r['double'] and r['december_finalized_without_acknowledgement']), 'families': fam}, d


def family_b(d):
    """Split the X+B+Yb+Yc doubles by which claim of A1Y was delivered last."""
    res = {'last_claim_Yc_double': [], 'last_claim_Yb_double': [], 'last_claim_Yc_single': 0, 'last_claim_Yb_single': 0}
    for r in d['results']:
        if r['family'] != 'X+B+Yb+Yc': continue
        o = r['order']; last = 'Yc' if o.index('Yc') > o.index('Yb') else 'Yb'
        if r['double']: res['last_claim_%s_double' % last].append(' '.join(o))
        else: res['last_claim_%s_single' % last] += 1
    return res


cmds = exit_codes(ev / 'commands/exit-codes.txt')
rc = probe_summary(ev / 'commands/01-rc-probes.stdout.txt'); rb = probe_summary(ev / 'commands/03-rb-probes.stdout.txt')
rd = probe_summary(out / 'fable_rd_acceptance_output.txt'); rd_base = probe_summary(ev / 'baseline-rc-source-rd-probes.txt')
base_rc = probe_summary(ev / 'baseline/rc-probes.stdout.txt')
m = re.search(r'SUMMARY runs=(\d+) double=(\d+) finalized_silently=(\d+)', (ev / 'commands/02-order-search.stdout.txt').read_text()); gate_search = dict(zip(('runs', 'double', 'finalized_silently'), map(int, m.groups())))
m = re.search(r'SUMMARY runs=(\d+) double=(\d+) finalized_silently=(\d+)', (ev / 'baseline/order-search.stdout.txt').read_text()); base_search = dict(zip(('runs', 'double', 'finalized_silently'), map(int, m.groups())))
ext, ext_raw = search(ev / 'order-search-extended-rd-source.json')
exp_ext, exp_raw = search(ev / 'experiment/rd-extended-search.json')
test_err = (ev / 'commands/05-make-test.stderr.txt').read_text()
ran = re.search(r'Ran (\d+) tests in ([\d.]+)s\s+(OK[^\n]*)', test_err)
faults_rc = (ev / 'fable-rc-register-faults-on-rd.txt').read_text(); faults_rd = (ev / 'fable-rd-register-faults.txt').read_text()
faults_rb = (ev / 'commands/14-rb-register-faults.stdout.txt').read_text()
register = json.loads((ev / 'commands/13-register-json.stdout.txt').read_text())
exp_codes = exit_codes(ev / 'experiment/exit-codes.txt'); exp_rd = probe_summary(ev / 'experiment/rd-probes-final.stdout.txt')

results = {
 'title': 'Fable independent verification of RD-01, RD-02 and PRV-11 to PRV-13',
 'authored': '2026-11-16',
 'bundle': 'exports/FABLE_RD_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip',
 'bundle_sha256': BUNDLE,
 'manifest_sha256': '9d27ea03c4f374ff2e4a801250206332ebf5aa47f003e47d933ea0059cc44f33',
 'baseline_bundle_sha256': BASE,
 'notice': 'Review output only. Opens no gate and authorises no implementation, connection, posting, payment, sending or deployment. All data fictional. Nothing in the submitted bundle, its sidecars, the working source or the earlier review folders and archives was changed.',
 'scope_of_every_conclusion': SCOPE,
 'overall': {'RD-01': 'ACCEPTED', 'RD-02': 'ACCEPTED', 'PRV-11': 'ACCEPTED', 'PRV-12': 'ACCEPTED', 'PRV-13': 'ACCEPTED', 'RB-01': 'NOT ACCEPTED (RE-01, RE-02)',
             'G0 technical criteria': 'NOT MET', 'human G0': 'NOT GRANTED (not a matter for this review)', 'Batch 3': 'CLOSED',
             'new tickets': {'P1': ['RE-01'], 'P2': ['RE-02', 'PRV-14'], 'P3': ['PRV-15']}, 'new observation needing a decision': ['UC-16'],
             'owner decision requested': 'Bound AAOS-BNK-03 and AAOS-CTL-04 by a stated feed contract (option A), or keep them open-ended and commission RE-01 and RE-02 (option B). See FABLE_RD_CORRECTIONS.json, owner_choice.'},
 'environment': [l for l in (ev / 'versions.txt').read_text().splitlines() if l.strip()] + ['commands ran in disposable extracted copies of the two bundles under the session scratch directory'],
 'executed': {
  'where': 'Disposable extracted copies in the session scratch directory: one pristine reference per bundle (re-hashed against the manifest after all runs: unchanged), one copy for the required commands, a second for the supplied mutating fault script, a third for my own fault script, and separate copies for my probes, the negative control and the experiment. The submitted archive, its sidecars, the working project and every earlier review folder and archive were only read.',
  'baseline_reproduction': {'bundle_sha256': BASE, 'rc_probes': {'exit_code': 1, 'verdicts': base_rc, 'counts': tally(base_rc)}, 'order_search': dict(base_search, exit_code=1), 'logs': 'evidence/baseline/'},
  'required_commands': cmds,
  'required_command_results': {
   'rc_probes': {'ids': len(rc), 'counts': tally(rc), 'not_OK': {k: v for k, v in rc.items() if v != 'OK'}},
   'order_search': gate_search,
   'rb_probes': {'ids': len(rb), 'counts': tally(rb), 'not_OK': {k: v for k, v in rb.items() if v != 'OK'}},
   'ra_probes': {'OK': 14},
   'make_test': {'methods': int(ran.group(1)), 'seconds': float(ran.group(2)), 'result': ran.group(3).strip(), 'http_methods': len(re.findall(r'\(test_http\.HTTPCase\) \.\.\. ok', test_err)), 'skipped_or_expected_failures': 0},
   'batch2_gate_reviewer_cases': {'PASS': 29, 'FIXED': 10, 'DEFERRED-OK': 21},
   'acceptance_gate': 'PASS; U4 is the only NOTE',
   'register_counts': {'requirements': register['requirements'], 'backlog_tickets': register['backlog_tickets'], 'product_decision_counts': register['product_decision_counts'], 'implementation_state_counts': register['implementation_state_counts']},
   'earlier_register_faults': re.findall(r'(?m)^cases.*$|^make check gaps.*$', faults_rb),
  },
  'second_copy_fault_script': {'command': 'python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py <second disposable copy>', 'exit_code': 0, 'summary': re.findall(r'(?m)^cases.*$|^make check gaps.*$', faults_rc), 'rejected': ['G16', 'G17', 'G18', 'G44'], 'log': 'evidence/fable-rc-register-faults-on-rd.txt'},
  'new_probes': {'script': 'fable_rd_acceptance_probes.py', 'on_this_bundle': {'exit_code': 1, 'verdicts': rd, 'counts': tally(rd), 'log': 'fable_rd_acceptance_output.txt'},
                 'on_the_rc_baseline_source': {'exit_code': 1, 'verdicts': rd_base, 'counts': tally(rd_base), 'log': 'evidence/baseline-rc-source-rd-probes.txt'}},
  'extended_order_search': dict(ext, exit_code=1, script='fable_rd_order_search.py', log='evidence/order-search-extended-rd-source.txt', family_X_B_Yb_Yc_by_last_claim=family_b(ext_raw),
                                reading='0 double in the two five-delivery families and the two withdrawn-claimant families (288 runs). X+Y5+Y4c+Z: 12 double, every order with Y4c delivered after Y5 (RE-01). X+B+Yb+Yc: 2 double with Yc as the last claim (RE-02) and 10 with Yb as the last claim (UC-16, a policy question, not counted as a defect).'),
  'my_register_faults': {'script': 'evidence/scripts/fable_rd_register_faults.py', 'exit_code': 1, 'summary': re.findall(r'(?m)^cases.*$|^every file restored.*$', faults_rd), 'gaps': re.findall(r'(?m)^(H\d+ .*?)\s+want=', '\n'.join(l for l in faults_rd.splitlines() if ' GAP' in l)), 'log': 'evidence/fable-rd-register-faults.txt'},
  'gate_faults': {'script': 'evidence/scripts/fable_rd_gate_faults.py', 'exit_code': 0, 'summary': re.findall(r'(?m)^cases.*$', (ev / 'fable-rd-gate-faults.txt').read_text()), 'what': 'the validators of scripts/verify_rc_review.py fed the real outputs of my run and altered copies: exit code, missing, duplicated, unknown and extra probe ids, WEAK and ERROR, altered notes, missing and duplicated order rows, unknown family, stated and hidden double approval, false and missing summary', 'log': 'evidence/fable-rd-gate-faults.txt'},
  'gate_negative_control': {'what': 'make rd-gate on this bundle with accounting_agent/source_control.py and service.py reverted to the baseline', 'exit_code': 2, 'log': 'evidence/rd-gate-negative-control.txt'},
 },
 'experiment': {
  'what': 'RE-01 and RE-02 applied together to a temporary copy of this bundle (evidence/experimental-correction-re.patch). Not a delivered fix.',
  'commands': exp_codes,
  'rd_probes_final_script': {'verdicts': exp_rd, 'counts': tally(exp_rd)},
  'extended_order_search': dict(exp_ext, family_X_B_Yb_Yc_by_last_claim=family_b(exp_raw)),
  'logs': 'evidence/experiment/',
 },
 'integrity': {
  'bundle_sha256_matches_sidecar_package_check_and_final_verification': True, 'archive_entries': 937, 'unsafe_paths_or_symlinks': 0, 'duplicate_entries': 0,
  'manifest_entries': 936, 'payload_hash_mismatches': 0, 'payload_files_not_in_manifest': 0, 'manifest_sha256_matches_package_check': True,
  'bundle_files_differing_from_working_project': 0, 'pristine_extraction_unchanged_after_all_runs': True,
  'baseline_bundle_sha256_verified': BASE, 'returned_response_sha256_verified': '1c47259742cfed78a2dcd2059c8cdadb72787df208d9d9232ddd8946bcfcbc23',
  'owner_prompt_sha256_verified': '4ae020a6d2111d4db33bd30d909f4968c60b89e8114ba044189f21d3e66c913f',
  'review_prompt_sha256': '13db1078aa5045474b44976a3f9fcde08219f623e90d9575e134205ee7992f34',
  'logs': ['evidence/integrity.txt', 'evidence/diff-vs-rc-baseline.json'],
 },
 'preservation': {
  'baseline_test_methods': 192, 'baseline_test_methods_missing': 0, 'baseline_test_method_bodies_changed': 0, 'methods_added': 13, 'methods_total': 205,
  'earlier_test_files_changed': ['tests/test_product_requirements.py (baseline bytes are an exact prefix; 4 methods appended)'],
  'payload_differences_from_baseline': {'added': 196, 'changed': 14, 'removed': 0, 'listed_in_developer_inventory': 207, 'not_listed': ['docs/corrections_rd/changed-files.json', 'docs/corrections_rd/source-and-tests.patch', 'REVIEW_MANIFEST.json'], 'not_listed_reason': 'the two declared self-artifacts and the manifest, covered by the manifest rule'},
  'patch_applies_to_baseline_and_reproduces_source_tests_scripts_makefile': True, 'files_compared_after_patch': 61, 'source_test_script_makefile_files_differing_from_baseline': 10,
  'protected_inputs': 484, 'protected_inputs_mismatching_in_bundle': 0, 'protected_inputs_mismatching_in_working_project': 0, 'protected_inputs_present_in_baseline_and_unchanged': 415,
  'earlier_archives_checked': 14, 'earlier_archives_differing': 0, 'sidecars_present_and_matching': 11, 'archives_without_sidecar': 3,
  'v2_sha256': '00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d',
  'rc_review_folder_vs_response_zip': {'files': 62, 'identical_in_bundle': 62, 'identical_in_working_project': 62},
  'schema_files_identical_to_baseline': ['accounting_agent/storage.py', 'tests/schema_v1.sql'],
  'register': {'records': 88, 'ids_and_order_retained': True, 'records_changed': ['AAOS-GOV-02', 'AAOS-GOV-03', 'AAOS-BNK-03', 'AAOS-CTL-04', 'AAOS-CTL-09'], 'product_decisions_changed': 0, 'implementation_states_changed': 0,
               'BB-01_BB-02_every_field_identical': True, 'KNO-04_CTL-01_BNK-02_identical': True, 'six_unratified_records_still_Proposed_and_identical': True, 'results_file_order_same_as_baseline': True},
  'working_project_git_read_only': {'branch': 'review/fable-rc-acceptance', 'head': '5a12ab0', 'commits': 5, 'matches_recorded_history': True},
  'logs': ['evidence/preservation.txt', 'evidence/test-inventory.txt', 'evidence/register-diff.txt', 'evidence/inventory-and-states.txt'],
 },
 'ticket_verdicts': [
  {'id': 'RD-01', 'verdict': 'ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed',
   'assertions': 'All four ticket assertions hold. The first unchanged re-send with an unknown-target claim adds exactly one source version and one unresolved event; both transition blockers appear before the target arrives for an eligible and for a previously approved claimant; an earlier approval stops governing before the target arrives; when the target arrives claimant and receipt are held under November, an approved-source event names the former approval, ITEM_LEFT_POPULATION is recorded and the approval decision remains; two repeats in new envelopes answer changed False and add no source snapshot, binding, move, link or accounting event; an exact replay adds no snapshot of any kind; no package row is rewritten.',
   'probes': ['X01', 'X01d', 'X01b', 'X01c', 'Y01', 'Y02', 'Y06', 'E01', 'E05'], 'note': 'My assertion said "no snapshot"; a distinct batch envelope keeps its ordinary immutable record (one batch snapshot, one intake audit row). I agree with the developer reading in D-023; no disagreement with the contract.'},
  {'id': 'RD-02', 'verdict': 'ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed',
   'assertions': 'All four ticket assertions hold. The latest unresolved claim belongs to the scoped identity, survives an amount revision with and without the claim, survives a restart, survives retirement and re-send in orders Yc Z Yp X and Z Yc Yp X, and resolves onto the current head, removed or not. Most recent target wins; an open target resolves to an ordinary supersession; a cycle is refused; unrelated intake adds nothing to a resolved chain, also after release and relock. 120 gate orders and 240 five-delivery orders: 0 double.',
   'probes': ['X02', 'Q02i', 'Q03', 'N01d', 'N01e', 'N01f', 'R01c', 'R01d', 'Y03', 'Y04', 'Y05', 'E04'], 'note': 'Claims omitted from later versions persist pending the owner feed-policy decision (D-023); verified as the stronger control, not as decided policy.'},
  {'id': 'RB-01', 'verdict': 'NOT ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed', 'assertions': 'The requirement is "regardless of arrival order". Two further kinds of delivery end with A1 approved in locked November and a replacement approved in open December, finalized without acknowledgement.', 'probes': ['E03', 'E06'], 'new_tickets': ['RE-01', 'RE-02']},
  {'id': 'RE-01', 'verdict': 'CONFIRMED DEFECT, P1, not a regression', 'bundle_sha256': BUNDLE, 'method': 'executed', 'probes': ['E03', 'E03c'], 'search': 'X+Y5+Y4c+Z: 12 of 24'},
  {'id': 'RE-02', 'verdict': 'CONFIRMED DEFECT, P2, control outcome not a regression; non-idempotent repeat is new in this pass', 'bundle_sha256': BUNDLE, 'method': 'executed', 'probes': ['E06', 'E02'], 'search': 'X+B+Yb+Yc: orders B Yb Yc X and Yb B Yc X'},
  {'id': 'PRV-11', 'verdict': 'ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed comparison of every record field with the baseline, and reading'},
  {'id': 'PRV-12', 'verdict': 'ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed', 'evidence': 'G16, G17, G18 rejected (44 of 44); H02 to H27: 24 of 26, the two gaps are PRV-15'},
  {'id': 'PRV-13', 'verdict': 'ACCEPTED', 'bundle_sha256': BUNDLE, 'method': 'executed', 'evidence': 'G44 rejected; H30 to H39: 10 of 10; make check unchanged'},
  {'id': 'PRV-14', 'verdict': 'NEW, P2, documentation: the register must record this review and the check should read these verdicts'},
  {'id': 'PRV-15', 'verdict': 'NEW, P3: the seven-row order named in AAOS-GOV-02 is not checked (H13, H14)'},
  {'id': 'X08/UC-14, N02c/UC-10, N04e/UC-11, U4', 'verdict': 'UNCHANGED NOTE; not fixed, as instructed'},
  {'id': 'UC-9 journal chains', 'verdict': 'NOT_RUN; reading only'},
  {'id': 'UC-16', 'verdict': 'NEW NOTE: a later claim on a different open row releases a row held under a locked period; needs a feed-contract decision'},
 ],
 'register_verdicts': [
  {'id': 'AAOS-BNK-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'one charge approved in two periods regardless of arrival order',
   'evidence': 'RD-01 and RD-02 accepted (X01, X01d, X02 OK; 120 orders 0 double; Y01 to Y06 OK). E03 and E06 WEAK (RE-01, RE-02).', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-CTL-04', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'a replacement chain never leaves the same expense approved in two periods', 'evidence': 'as AAOS-BNK-03', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-GOV-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'known repaired defects must pass',
   'evidence': 'RB-01 is still not accepted. The other parts of the criterion were checked and hold: 192 earlier methods retained, no archive overwritten, deferred capabilities still deferred, earlier adaptations and non-zero original commands still disclosed.', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-KNO-04', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N03c', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-CTL-01', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N04a', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-BNK-02', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-11 stays open', 'evidence': 'R04a, R04b, R04c, N02b, N04a to N04d; N04e NOTE', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
  {'id': 'AAOS-CTL-09', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-10 stays open', 'evidence': 'R03a, R03b, R04a, R04b, R04c, N02a, N02b, N04a to N04d, Q02; N02c NOTE', 'bundle_sha256': BUNDLE, 'report_path': REPORT},
 ],
 'inspected_only': [
  'AGENTS.md, DECISIONS.md D-022 to D-025, PROGRESS.md, START_HERE.md, REVIEW_FREEZE.md, docs/CONNECTION_READINESS.md, FABLE_RD_CORRECTIONS_HANDOFF.md, docs/corrections_rd/RD_CORRECTIONS_REPORT.md: read, not executed.',
  'docs/corrections_rd/ developer logs and exports/FABLE_RD_AND_PRV_CORRECTIONS_FINAL_VERIFICATION*: read for comparison with my own runs; none is used as evidence for a conclusion.',
  'scripts/build_rd_review_bundle.py and scripts/verify_rd_bundle.py: read, not executed; I verified the archive with my own scripts.',
  'UC-9: journal claim handling, by reading accounting_agent/source_control.py and modules.py.',
 ],
 'not_run': [
  {'what': 'A bespoke journal-chain probe (UC-9)', 'why': 'Outside RD; the prompt reports it as reading-only and gives no permission to expand the pass. My reading agrees with docs/corrections_rd/journal-scope-reading.txt.'},
  {'what': 'UC-6 and UC-8 bespoke probes', 'why': 'Outside RD and PRV.'},
  {'what': 'Full literal exports/FABLE_RV_ACCEPTANCE and exports/FABLE_REVERIFICATION scripts with every id', 'why': 'Not part of this assignment; their historical incompatibilities are disclosed and unchanged. The maintained subsets ran through make acceptance-gate and make reverification-gate.'},
  {'what': 'Deliveries beyond the 120 gate orders and the 336 extended orders', 'why': 'The search is bounded evidence for those deliveries, not proof for every possible feed.'},
  {'what': 'The remaining gates (make check, rb-gate, rd-gate, register fault scripts) on the experimental copy', 'why': 'The experiment is a worked reference; I ran the probe scripts, both searches, make test and four gates on it.'},
  {'what': 'Browser rendering; an external linter, type checker or JavaScript compiler', 'why': 'Not installed; no toolchain was added.'},
  {'what': 'Any connection, model call, client data, sending, posting, payment, hosting or deployment', 'why': 'Not authorised and not needed.'},
 ],
}
(out / 'FABLE_RD_ACCEPTANCE_RESULTS.json').write_text(json.dumps(results, indent=1) + '\n')
print('written', out / 'FABLE_RD_ACCEPTANCE_RESULTS.json')
print(json.dumps({k: results['executed'][k] for k in ('required_command_results', 'second_copy_fault_script', 'my_register_faults')}, indent=1)[:3000])
print(json.dumps(results['experiment'], indent=1)[:2500])
