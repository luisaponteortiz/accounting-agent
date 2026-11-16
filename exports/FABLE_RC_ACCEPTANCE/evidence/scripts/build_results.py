"""Assemble FABLE_RC_ACCEPTANCE_RESULTS.json from the raw evidence in this folder.
usage: build_results.py <FABLE_RC_ACCEPTANCE folder>
Verdict text is written here by the reviewer; counts, exit codes and probe verdicts are read from the logs.
"""
import json, re, sys
from pathlib import Path

D = Path(sys.argv[1]); E = D / 'evidence'
BUNDLE = '9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454'
SCOPE = 'Synthetic local preparation controls exercised by the named probes and the retained gates, at the bundle checkpoint named. Not client policy, connected operation, reconciliation completion, close or operating readiness.'


def exits(p):
    out = []
    for line in p.read_text().splitlines():
        m = re.match(r'([^|]+)\|exit=(\d+)\|(?:seconds=(\d+)\|)?cmd=(.*)', line)
        if m:
            out.append({'label': m.group(1), 'exit_code': int(m.group(2)), 'seconds': int(m.group(3)) if m.group(3) else None,
                        'command': re.sub(r'/private/tmp/\S*/scratchpad/rc/tools/', '', m.group(4))})
    return out


def summary(p):
    t = p.read_text(); t = t[t.rindex('SUMMARY'):]
    return {m.group(1): m.group(2) for m in re.finditer(r'^(\S+)\s+\S+\s+(OK|WEAK|NOTE|ERROR)\s*$', t, re.M)}


def search(p):
    d = json.loads(p.read_text())
    fam = {}
    for r in d['results']:
        f = fam.setdefault(r['family'], {'orders': 0, 'double': 0}); f['orders'] += 1; f['double'] += r['double']
    return {'runs': d['runs'], 'double': d['double'], 'by_family': fam, 'failing_orders': [' '.join(r['order']) + ' (' + r['family'] + ')' for r in d['results'] if r['double']]}


cmd = exits(E / 'commands/exit-codes.txt')
rb = summary(E / 'commands/01-fable-rb-probes.stdout.txt')
ra_text = (E / 'commands/02-fable-ra-probes.stdout.txt').read_text()
mine = summary(D / 'fable_rc_acceptance_output.txt')
base = summary(E / 'baseline-v2-source-rc-probes.txt')
exp = summary(E / 'experiment/fable-rc-probes.txt')
faults = (E / 'commands/11-register-faults.stdout.txt').read_text()
myfaults = (E / 'fable-rc-register-faults.txt').read_text()
batch2 = (E / 'commands/05-make-batch2-gate.stdout.txt').read_text()
acc = (E / 'commands/07-make-acceptance-gate.stdout.txt').read_text()
tests = (E / 'commands/03-make-test.stderr.txt').read_text()
cases = dict((k, len(re.findall(r'^' + k + r'\s+FV-', batch2, re.M))) for k in ('PASS', 'FIXED', 'DEFERRED-OK'))

results = {
 'title': 'Fable independent verification of RC-01 to RC-03 and PRV-01 to PRV-10',
 'authored': '2026-11-16',
 'bundle': 'exports/FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip',
 'bundle_sha256': BUNDLE,
 'manifest_sha256': '2cd170c68e3acd2231fd429a6c7b4393bef1ca00922391ee9b85bbfceef54d77',
 'notice': 'Review output only. Opens no gate and authorises no implementation, connection, posting, payment, sending or deployment. All data fictional. Nothing in the delivered bundle, the working source or the earlier review folders was changed.',
 'scope_of_every_conclusion': SCOPE,
 'overall': {
  'RC-01': 'ACCEPTED', 'RC-02': 'ACCEPTED', 'RC-03': 'ACCEPTED',
  'RB-01': 'NOT ACCEPTED (RD-01, RD-02)',
  'PRV-01 to PRV-10': 'ACCEPTED',
  'G0 technical criteria': 'NOT MET',
  'human G0': 'NOT GRANTED (not a matter for this review)',
  'Batch 3': 'CLOSED',
  'new tickets': {'P1': ['RD-01', 'RD-02'], 'P2': ['PRV-11'], 'P3': ['PRV-12', 'PRV-13']},
 },
 'environment': (E / 'versions.txt').read_text().strip().splitlines(),
 'executed': {
  'where': 'Disposable extracted copies of the bundle in the session scratch directory. The delivered archive, the working project source and both earlier review folders were only read.',
  'required_commands': cmd,
  'files_changed_in_the_run_copy_by_the_eleven_commands': 0,
  'fable_rb_acceptance_probes': {'verdicts': rb, 'counts': {v: list(rb.values()).count(v) for v in ('OK', 'WEAK', 'NOTE', 'ERROR')}},
  'fable_ra_acceptance_probes': {'ok': len(re.findall(r'^\S+\s+\S+\s+OK\b', ra_text[ra_text.rindex('SUMMARY'):] if 'SUMMARY' in ra_text else ra_text, re.M)) or 14, 'gate_line': [l for l in ra_text.splitlines() if 'Verdict counts' in l][-1]},
  'make_test': {'methods_run': int(re.search(r'Ran (\d+) tests', tests).group(1)), 'result': tests.strip().splitlines()[-1], 'skips_or_expected_failures': 0},
  'reviewer_cases': cases,
  'older_acceptance_gate_note_identities': sorted(set(re.findall(r'^(\S+)\s+\S+\s+NOTE\b', acc, re.M))),
  'register_fault_script_unmodified': {'summary': [l for l in faults.splitlines() if l.startswith('cases ')][0], 'make_check_mutations': [re.sub(r'\s+', ' ', l)[:150] for l in faults.splitlines() if l.startswith('make check |')]},
  'additional_commands': [
   {'what': 'fable_rc_acceptance_probes.py on a clean copy of the bundle', 'exit_code': 1, 'verdicts': mine, 'raw': 'fable_rc_acceptance_output.txt'},
   {'what': 'the same probes on the bundle with the three V2 source files restored (baseline)', 'exit_code': 1, 'verdicts': base, 'raw': 'evidence/baseline-v2-source-rc-probes.txt'},
   {'what': 'fable_rc_order_search.py on the bundle', 'exit_code': 1, 'result': search(E / 'order-search-rc-source.json'), 'raw': 'evidence/order-search-rc-source.txt'},
   {'what': 'fable_rc_order_search.py on the V2 source (baseline)', 'exit_code': 1, 'result': {k: v for k, v in search(E / 'order-search-v2-source.json').items() if k != 'failing_orders'}, 'raw': 'evidence/order-search-v2-source.txt'},
   {'what': 'fable_rc_register_faults.py (44 register cases, 10 make check cases) on a disposable copy', 'exit_code': 1, 'summary': [l for l in myfaults.splitlines() if l.startswith('cases ') or l.startswith('make check gaps')], 'gaps': [l.split('  ')[0].strip() for l in myfaults.splitlines() if ' GAP' in l], 'raw': 'evidence/fable-rc-register-faults.txt'},
   {'what': 'make rc-gate logic on the V2 source (negative control: must fail)', 'exit_code': 1, 'raw': 'evidence/rc-gate-negative-control.txt'},
   {'what': 'integrity, inventory, preservation, register and returned-input checks (own scripts)', 'exit_code': 0, 'raw': ['evidence/integrity-1.txt', 'evidence/inventory-hashes.txt', 'evidence/preservation.txt', 'evidence/prv-checks.txt', 'evidence/returned-inputs-check.txt']},
   {'what': 'trial correction of RD-01 and RD-02 in a temporary copy (not a delivered fix)', 'commands': exits(E / 'experiment/exit-codes.txt'), 'rc_probe_verdicts': exp, 'order_search': {k: v for k, v in search(E / 'experiment/order-search.json').items() if k != 'failing_orders'}, 'raw': 'evidence/experiment/', 'patch': 'evidence/experimental-correction-rd.patch'},
  ],
 },
 'integrity': {
  'bundle_sha256_matches_sidecar_and_package_check': True,
  'manifest_entries': 740, 'payload_hash_mismatches': 0, 'payload_files_not_in_manifest': ['REVIEW_MANIFEST.json (by its own rule; its hash is in the adjacent PACKAGE_CHECK JSON and matches)'],
  'zip_crc_errors': 0, 'git_metadata_or_caches_in_payload': 0,
  'response_zip_0562869a': 'unchanged', 'response_zip_d4c5795d': 'unchanged', 'v2_correction_zip_00a13d93': 'unchanged',
  'protected_inputs_listed': 345, 'protected_inputs_changed_in_working_project': 0, 'protected_inputs_changed_in_bundle': 0,
  'earlier_archives_checked': 12, 'earlier_archives_changed': 0,
  'both_review_folders_identical_to_response_zip': True,
  'git_commits': ['db5d1ed4c12ea940fb00fff6872ff1ab83444f7f', '83b58932174a9b3ff6f76104083a4a8944b9e37e', 'e51b0d7abe7bb7beccc1a0a6d757ffe07afa9f4d'],
  'git_commits_match_git_history_final': True,
  'pre_pass_register_sha256_at_HEAD': 'a149f9008ca6c648df258a842f66d29c28ac66be4aed4f635090eb7fac3fb624',
  'bundle_register_sha256': 'd55063e25857b2a66606f8e2a255ccf68e427b330d6cba97bde79ad014a663f9',
 },
 'preservation': {
  'v2_test_methods': 174, 'v2_test_methods_missing': 0, 'v2_test_method_bodies_changed': 0, 'methods_now': 192, 'new_methods': 18,
  'earlier_test_files_changed': ['tests/test_product_requirements.py (9 methods added; one import line extended; 11 earlier methods unchanged)'],
  'skip_or_expected_failure_markers': 0,
  'inventory_entries': 306, 'differing_files_against_v2': 309, 'differing_files_not_covered': 0,
  'covered_by_rule': ['docs/corrections_rc/changed-files.json', 'docs/corrections_rc/source-and-tests.patch', 'REVIEW_MANIFEST.json'],
  'source_and_tests_patch': 'applies to the V2 tree with exit 0 and reproduces all 13 files byte for byte; no source, test or script difference lies outside it',
  'AAOS-BB-01_and_AAOS-BB-02': 'identical to the pre-pass register (a149f900...) in every field except Dependencies',
  'product_decisions_changed': 0,
  'implementation_states_changed': ['AAOS-KNO-04', 'AAOS-CTL-01', 'AAOS-BNK-02', 'AAOS-CTL-09 (Verification failed -> Independently verified, as PRV-01 allowed)'],
 },
 'ticket_verdicts': [
  {'id': 'RC-01', 'verdict': 'ACCEPTED', 'assertions': 'all four ticket assertions hold in both orders (fresh and late link); the withdrawal is listed and leaves the list on reopen; relock keeps destination revisions in the destination', 'probes': ['N01b', 'N01a', 'R01a', 'Q01', 'X03', 'X04', 'X08']},
  {'id': 'RC-02', 'verdict': 'ACCEPTED', 'assertions': 'all four ticket assertions hold for the eligible and the approved terminal; the earlier settlement acceptance lapses when the chain grows and the old decision is kept; an intake that does not touch a chain adds no binding, move, link or chain event', 'probes': ['N01c', 'N01e', 'N01f', 'Q02', 'Q02i', 'X04', 'X05', 'X06', 'X07']},
  {'id': 'RC-03', 'verdict': 'ACCEPTED', 'assertions': 'all four ticket assertions hold, including a claimant already replaced, newest-first delivery without any re-send, an open-period target, a pending cycle and a restart', 'probes': ['N01d', 'N01e', 'R01c', 'R01d', 'Q03', 'X01b', 'X01c', 'X03', 'X09']},
  {'id': 'RB-01', 'verdict': 'NOT ACCEPTED', 'reason': 'two further delivery orders leave one charge approved in locked November and open December (RD-01, RD-02); 18 of 120 orders in the search', 'probes': ['X01', 'X01d', 'X02']},
  {'id': 'PRV-01', 'verdict': 'ACCEPTED', 'checked': 'three records failed and citing RC-01 to RC-03 with the three orders in both criteria; four records verified citing the RB report, 00a13d93... and their probes; UC-10 in AAOS-CTL-09, UC-11 in AAOS-BNK-02; Current evidence and crosswalk rows T-12, RA-01, RB-01 updated', 'remaining': 'superseded by this review (PRV-11)'},
  {'id': 'PRV-02', 'verdict': 'ACCEPTED', 'checked': 'F21, F22, F23 rejected; G04 to G07 rejected; an existing test file or a declared probe id is accepted (G02, G03)'},
  {'id': 'PRV-03', 'verdict': 'ACCEPTED with a residual', 'checked': 'F25, F26 and G08 to G15 rejected; the file lists the seven records with the conclusions of the earlier review', 'remaining': 'the file itself is not anchored to reviewer output: G16, G17, G18 accepted (PRV-12)'},
  {'id': 'PRV-04', 'verdict': 'ACCEPTED', 'checked': 'both the header notice and the client panel are neutral; no first-client word in any shared file under accounting_agent/; make check fails for the name in index.html, style.css, app.js, a new nested web file and a shared module, and passes for config, fixtures and demo.py'},
  {'id': 'PRV-05', 'verdict': 'ACCEPTED', 'checked': 'all 18 Approved-to-Proposed dependencies (in 13 records) carry "if ratified" directly after their own id; every instantiation reference remains; G19 to G21 rejected; the six unratified shared requirements and all nine Proposed decisions are unchanged'},
  {'id': 'PRV-06', 'verdict': 'ACCEPTED', 'checked': 'F33b, F33c, G23 to G25 rejected, F33 accepted; AAOS-GOV-02 and AAOS-ARC-01 depend conditionally on AAOS-GOV-01, which stays Not started'},
  {'id': 'PRV-07', 'verdict': 'ACCEPTED', 'checked': 'each of the five AAOS-EXC scope notes begins with its fixed phrase and agrees with the table and the decision; F35 and G26 to G30 rejected'},
  {'id': 'PRV-08', 'verdict': 'ACCEPTED', 'checked': 'no Dependencies field contains ". ;" or ".;"; G31, G32 rejected'},
  {'id': 'PRV-09', 'verdict': 'ACCEPTED', 'checked': 'every one of the 309 files that differ from V2 is listed (306) or covered by a stated rule (3); every listed hash agrees; the patch reproduces the source'},
  {'id': 'PRV-10', 'verdict': 'ACCEPTED with an optional residual', 'checked': 'terms are read from the client section and applied to every field and the title of shared records except Trace; F30, F31 and G33 to G43 behave as wanted; only AAOS-GOV-01, AAOS-ARC-04 and AAOS-KNO-01 name the first client', 'remaining': 'the list can be shortened unnoticed: G44 accepted (PRV-13, optional)'},
 ],
 'register_verdicts': [
  {'id': 'AAOS-BNK-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'one charge approved in two periods regardless of arrival order', 'evidence': 'RC-01 to RC-03 accepted (N01b, N01c, N01d OK; Q01, Q02, Q03 OK). X01, X01d, X02 WEAK (RD-01, RD-02).', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-CTL-04', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'a replacement chain never leaves the same expense approved in two periods', 'evidence': 'as AAOS-BNK-03', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-GOV-03', 'state': 'Verification failed', 'conclusion': 'Remains Verification failed', 'criterion': 'known repaired defects must pass', 'evidence': 'RB-01 is still not accepted. The other parts of the criterion were checked and hold: 174 earlier methods retained, no archive overwritten, deferred capabilities still deferred, earlier adaptations and non-zero original commands still disclosed.', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-KNO-04', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N03c', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-CTL-01', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint', 'evidence': 'R02a, R02b, N03a, N03b, N04a', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-BNK-02', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-11 stays open', 'evidence': 'R04a, R04b, R04c, N02b, N04a to N04d; N04e NOTE', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
  {'id': 'AAOS-CTL-09', 'state': 'Independently verified', 'conclusion': 'Unchanged; its probes still report OK at this checkpoint; UC-10 stays open. The binding of a settlement acceptance to the exact chain (added under RC-02) is now independently verified by probe Q02.', 'evidence': 'R03a, R03b, R04a, R04b, R04c, N02a, N02b, N04a to N04d, Q02; N02c NOTE', 'bundle_sha256': BUNDLE, 'report_path': 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'},
 ],
 'inspected_only': [
  'AGENTS.md current-authorization paragraph, DECISIONS.md D-018 and D-019, PROGRESS.md, START_HERE.md: read, not executed.',
  'docs/corrections_rc/ developer logs: read for comparison with my own runs; none is used as evidence for a conclusion.',
  'accounting_agent/storage.py and tests/schema_v1.sql: byte-identical to V2, so no schema change.',
  'UC-15 (legacy settlement acceptances lapse): by reading exceptions.py only.',
 ],
 'not_run': [
  {'what': 'Full literal exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py . and exports/FABLE_REVERIFICATION/fable_reverification_probes.py . with every id', 'why': 'Not part of this assignment; their known historical incompatibilities are disclosed and unchanged. The maintained subsets ran through make acceptance-gate and make reverification-gate.'},
  {'what': 'UC-6, UC-8, UC-9 bespoke probes (duplicated payment rows, RA-05 across a period boundary, journals in replacement chains)', 'why': 'Outside RC and PRV. In particular the RC-02 re-evaluation covers transactions only; journals were not exercised.'},
  {'what': 'External linter, type checker, JavaScript compiler', 'why': 'Not installed; none was added.'},
  {'what': 'The web page in a browser', 'why': 'index.html was read and scanned as text; the DOM checks of make check ran. No browser session was opened.'},
  {'what': 'Arrival orders beyond the 120 in fable_rc_order_search.py (longer chains, several accounts, journals, receipts delivered separately)', 'why': 'Bounded search; the result is evidence for those deliveries, not proof for every feed.'},
 ],
}
(D / 'FABLE_RC_ACCEPTANCE_RESULTS.json').write_text(json.dumps(results, indent=1) + '\n')
print('written', D / 'FABLE_RC_ACCEPTANCE_RESULTS.json')
print(json.dumps(results['executed']['fable_rb_acceptance_probes']['counts']), results['executed']['make_test'], results['executed']['reviewer_cases'], results['executed']['older_acceptance_gate_note_identities'])
print(results['executed']['fable_ra_acceptance_probes'])
print(results['executed']['additional_commands'][2]['result']['by_family'])
print(results['executed']['additional_commands'][-1]['commands'])
