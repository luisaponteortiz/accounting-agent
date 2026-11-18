"""Assemble FABLE_RA_ACCEPTANCE_RESULTS.json from the raw logs in evidence/. usage: build_results.py <FABLE_RA_ACCEPTANCE dir>"""
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]); ev = root/'evidence'
row = re.compile(r'(?m)^((?:A|X|U|M|RN|RT|RG|R)\w+)\s+(\S+)\s+(OK|WEAK|ERROR|NOTE)\s+(.*)$')
def rows(name):
    return [{'id': a, 'ticket': b, 'raw': c, 'title': d.strip()} for a, b, c, d in row.findall((ev/name).read_text() if (ev/name).exists() else (root/name).read_text())]
exits = dict(re.findall(r'(?m)^(\S+) exit=(\d+)', (ev/'exit-codes.txt').read_text()))
acc = rows('make-acceptance-gate.stdout.txt'); rv = rows('make-reverification-gate.stdout.txt')
mine = rows('fable_ra_acceptance_output.txt'); base = rows('baseline-frozen-rv-comparison.txt')
tests = (ev/'make-test.stderr.txt').read_text()
assessed = {
 'RA-01': ('NOT_ACCEPTED', 'X01, A01 and R01a OK; R01b and R01c WEAK. RB-01 (P1), a regression against the frozen RV submission for R01b.'),
 'RA-03': ('ACCEPTED_WITH_REMAINING_ROUTE', 'X12k, A12, R03a OK; R03b WEAK. RB-02 (P2).'),
 'RA-04': ('ACCEPTED_WITH_REMAINING_ROUTE', 'X12s, A13, R04a OK; R04b WEAK (RB-02, P2); R04c NOTE (RB-04, P3).'),
 'RA-02': ('ACCEPTED', 'A10 and R02a OK. Adjacent routes R02b WEAK recorded as RB-03 (P3), outside the RA-02 assertions.'),
 'RA-06': ('ACCEPTED', 'R01a: whole-evidence disposition takes effect after reopen; outside reference refused.'),
 'RA-05': ('ACCEPTED', 'U1, RT10a, RT10b, R05 OK. Period-boundary recurrence not independently run (UC-8).'),
 'RA-07': ('ACCEPTED', 'A14 and R07 OK. Journal-support path by inspection and delivered tests only (UC-9).'),
 'RA-08': ('ACCEPTED', 'X09 (reviewed setup) and R08 OK.'),
 'C-01 to C-06 retained': ('RETAINED_EXCEPT_C-01', 'Corrective gate and frozen corrective checkpoint pass. The C-01 objective is breached by RB-01.'),
 'RV-01 to RV-17 retained': ('RETAINED_EXCEPT_RV-01_RV-12', '27 unmodified originals OK, all 35 current-setup OK. RV-01 reopened by RB-01; RV-12 route remains (RB-02).'),
 'Batch 2 (T-09 to T-19) and 60 cases': ('REPRODUCED', '29 PASS / 10 FIXED / 21 DEFERRED-OK in my run. DEFERRED-OK is a refusal, not accounting functionality.'),
 'Adaptation A03': ('ACCEPTED', 'Hold and statement disclosure asserted first; existing granted non-supplier accepts; original returns and assignments identical.'),
 'Adaptation A05': ('ACCEPTED', 'Acceptance for M3 only; M2 unknown-vendor hold retained.'),
 'Adaptation A17': ('ACCEPTED', 'Stale-finalization refusal stays before acceptance.'),
 'Adaptation X09': ('ACCEPTED', 'Acceptance for D2 only; circular-exclusion phase untouched.'),
 'Adaptation older RT18': ('ACCEPTED', 'Stale-package refusal first; helper asserts hold and disclosure but not that the revision is a statement (minor).'),
 'Seven earlier adaptations and strengthened RT14b': ('RETAINED', 'Diff of original against the maintained copy shows only the reviewed changes; both RT14b guard tests pass in make test.'),
 'Unmodified full acceptance command': ('NONZERO_AS_DISCLOSED', 'Exit 1: A03, A05, X09 WEAK; A17 ERROR; U4 NOTE; 19 OK. Not relabelled.'),
 'Teaching month, referral route': ('REPRODUCED', 'M1 OK: ten approvals, three held, supplies +311.00, repairs +200.00, liability -211.00, cash -300.00, nets to zero.'),
 'Teaching month, acceptance route': ('REPRODUCED', 'M2 OK: eleven approvals, supplies +391.00, liability -291.00, same repairs and cash, nets to zero.'),
 'Two-client isolation': ('REPRODUCED', 'M1: cross-client decisions and packets refused; first client unchanged; both audit chains verify.'),
 'G0 technical criteria': ('NOT_MET', 'One P1 (RB-01) and one P2 (RB-02) are open.'),
}
out = {
 'title': 'Fable independent verification results for RA-01 to RA-08',
 'authored': '2026-11-15',
 'notice': 'All data fictional. Temporary databases. No source change, connection, model call, posting, payment or deployment.',
 'bundle': {'outer_sha256': 'b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea', 'ra_checkpoint_sha256': 'dec028b06a745ba52ceca448c766893c33e863f98d5728aafd8b6edadb274e4f', 'frozen_rv_sha256': '247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75',
            'outer_manifest': '26 of 26 files match', 'ra_manifest': '324 of 324 files match', 'archive_paths': 'no duplicate, absolute, parent or symlink entries', 'input_checksums': '57 of 57 match (evidence/inventory_checks_output.txt)'},
 'limits_of_this_verification': [
  'The 27 independent input files were compared with the hashes the developer recorded; no separately held copy was available in this session to compare against.',
  'Commands ran on a byte copy of the extracted checkpoint so that the supplied files stayed untouched; the copy was identical to the original after the run apart from Python caches.',
  'HTTP tests ran with loopback access and passed.'],
 'versions': (ev/'versions.txt').read_text().strip().splitlines(),
 'commands': [{'name': k, 'exit': int(v), 'stdout': 'evidence/%s.stdout.txt' % k, 'stderr': 'evidence/%s.stderr.txt' % k} for k, v in exits.items()] + [
  {'name': 'fable_ra_acceptance_probes.py (RA source)', 'exit': 1, 'stdout': 'fable_ra_acceptance_output.txt'},
  {'name': 'fable_ra_acceptance_probes.py R01b R01c R03b R04b R02b R04c (frozen RV baseline)', 'exit': 1, 'stdout': 'evidence/baseline-frozen-rv-comparison.txt'}],
 'make_test': {'methods_ok': len(re.findall(r'\.\.\. ok', tests)), 'ran': re.search(r'Ran (\d+) tests', tests).group(1), 'result': tests.strip().splitlines()[-1], 'methods_in_frozen_rv_baseline': 136, 'baseline_methods_missing': 0, 'new_methods': 18, 'expected_failure_or_skip_markers': 0},
 'acceptance_gate': {'unmodified_originals_20': acc[:20], 'reviewed_setup_all_24': acc[20:44]},
 'reverification_gate': {'unmodified_originals_27': rv[:27], 'reviewed_setup_all_35': rv[27:62]},
 'unmodified_full_acceptance_script': rows('original-full-acceptance.stdout.txt'),
 'unmodified_full_reverification_script': rows('original-full-reverification.stdout.txt'),
 'new_independent_probes': mine,
 'new_probes_on_frozen_rv_baseline': base,
 'sixty_cases': json.loads((ev/'my-60-case-results.json').read_text()),
 'assessed': [{'criterion': k, 'assessed': v[0], 'basis': v[1]} for k, v in assessed.items()],
 'not_run': [
  {'item': 'UC-6 duplicated payment row vocabulary', 'status': 'NOT_RUN'},
  {'item': 'RA-05 recurrence across a period boundary, caps, expiry and concurrency beyond the existing probes', 'status': 'NOT_RUN independently; delivered tests only'},
  {'item': 'RA-07 journal-support disposition', 'status': 'NOT_RUN independently; inspection and delivered tests only'},
  {'item': 'External linter, type checker or JavaScript compiler', 'status': 'NOT_RUN; none is part of the project'}],
 'deferred': 'The 21 DEFERRED-OK cases validate refusal of AP, AR, reconciliation, reporting and posting capabilities that are not built.',
}
(root/'FABLE_RA_ACCEPTANCE_RESULTS.json').write_text(json.dumps(out, indent=1) + '\n')
print('acceptance rows', len(acc), '| reverification rows', len(rv), '| mine', len(mine), '| baseline', len(base), '| full acc', len(out['unmodified_full_acceptance_script']), '| full rv', len(out['unmodified_full_reverification_script']), '| tests ok', out['make_test']['methods_ok'])
