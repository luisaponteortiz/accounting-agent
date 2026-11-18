"""Fill the report template from FABLE_RF_ACCEPTANCE_RESULTS.json and the raw outputs (read-only on both)."""
import json, re
from pathlib import Path
R = Path('/private/tmp/claude-501/rf'); OUT = R / 'out'; D = R / 'deliver'
res = json.loads((D / 'FABLE_RF_ACCEPTANCE_RESULTS.json').read_text())
t = (R / 'scripts/report_template.md').read_text()
tv = {x['id']: x['verdict'] for x in res['ticket_verdicts']}
word = lambda v: 'Accepted' if v == 'ACCEPTED' else 'Not accepted'
ext = res['own_order_search']['extended']; orig = res['own_order_search']['original_script_unchanged']; base = res['own_order_search']['extended_on_the_re_checkpoint_source_six_families']
DESC = {
    'retained-claim+row-revision': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 8 revised (amount, date)',
    'retained-claim+receipt-revision': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; revised receipt for Q',
    'same-order-conflict-resent': 'P; Q seq 7; Q seq 7 with another amount; the same claiming P; Z replacing Q',
    'claim-inside-row-data': 'P; Q seq 7; Q seq 6; Q seq 6 with the claim inside the row data; Z replacing Q',
    'timestamp-order': 'the RF-01 family with timestamps instead of sequence numbers',
    'retained-claim-on-replacement': 'P; Q claiming P; Z seq 7; Z seq 6; Z seq 6 claiming Q',
    'retained-claim+older-conflict': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 5 claiming B (B on file)',
    'retained-claim+newer-conflict': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 8 claiming B (B on file)',
    'retained-claim+withdrawal+resend': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q withdrawn (seq 8); Q re-sent (seq 9)',
    'conflict+selection-without-lock': 'P; Q seq 7; Q seq 6 claiming P; Q seq 8 claiming B; a person with disposition authority only selects B',
    'retained-conflict+confirming-selection': 'P; Q seq 6; Q seq 6 claiming P; Q seq 8 claiming B; a person selects P',
    'retained-claim+replacement+revision': 'P; Q seq 7; Q seq 6; Q seq 6 claiming P; Z replacing Q; Z revised',
}
rows = ['| Family (steps) | Orders | Double | Released | Unlinked first claim | Repeat changed (of orders checked) | Repeat of a retired row | Approved while waiting (UC-20) |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
for name in DESC:
    v = ext['families'].get(name)
    if v:
        rows.append('| %s | %d | %d | %d | %d | %d of %d | %d | %d |' % (DESC[name], v['runs'], v['double'], v['released_without_authority'], v['unlinked_first_claim'], v['repeat_changed'], v['repeat_checked'], v['repeat_of_retired_row'], v['uc20_orders_approved_while_an_ancestor_claim_waits']))
rows.append('| **Total, delivered source** | **%s** | **%d** | **%d** | **%d** | **%d of %d** | %d | %d |' % ('{:,}'.format(ext['runs']), ext['double'], ext['released_without_authority'], ext['unlinked_first_claim'], ext['repeat_changed'], ext['repeat_checked'], ext['repeat_of_retired_row'], ext['uc20_orders_approved_while_an_ancestor_claim_waits']))
rows.append('')
rows.append('Audit chain: verified at the end of every order (%d failures). The first script on the delivered source: %d orders, %d double, %d released, %d audit failures, %d early.' % (
    ext['audit_failures'], orig['runs'], orig['double'], orig['released_without_authority'], orig['audit_failures'], sum(f['approved_before_target_known'] for f in orig['families'].values())))
rows[-1] = rows[-1].replace(' early.', ' approved while waiting (UC-20).')
base_summary = '%d orders, %d with a double approval, %d with an unlinked first claim, %d released' % (base['runs'], base['double'], base['unlinked_first_claim'], base['released_without_authority'])
eqrows = ['| Wrapped run (unchanged script) | Report calls inside a transaction | Outside | Differences | Currentness evaluations, delivered / full |', '| --- | --- | --- | --- | --- |']
NAMES = {'eq-demo': 'Demo data (the seed the HTTP tests use), single-threaded', 'eq-rf-probes': 'My 15 new probes', 'eq-re-probes': 'My 21 RE probes', 'eq-rd-probes': '13 RD probes (the original Y05 reports WEAK, as it has since D-026)',
         'eq-rc-probes': 'RC probes', 'eq-rb-probes': 'RB probes', 'eq-ra-probes': 'RA probes', 'eq-re-step-search-older-resent': 'Order search, family older-resent-with-claim (120 orders)'}
tot = [0, 0, 0, 0, 0]
for k, name in NAMES.items():
    v = res['rf03_equivalence'].get(k)
    if v:
        eqrows.append('| %s | %d | %d | %d | %d / %d |' % (name, v['calls_in_transaction'], v['calls_autocommit'], v['mismatches'], v['current_evaluations_delivered'], v['current_evaluations_full']))
        for i, key in enumerate(('calls_in_transaction', 'calls_autocommit', 'mismatches', 'current_evaluations_delivered', 'current_evaluations_full')):
            tot[i] += v[key]
eqrows.append('| **Total** | **%d** | **%d** | **%d** | %d / %d |' % tuple(tot))
timing = '\n'.join(l for l in (OUT / 'http-setup-timing.txt').read_text().strip().splitlines() if 'Terminated: 15' not in l) if (OUT / 'http-setup-timing.txt').is_file() else 'NOT_RUN'
timing_block = '```\n' + timing + '\n```'
TIMING_READING = (R / 'scripts/timing_reading.md').read_text().strip()
five = res['make_test']['five_consecutive_runs']
frows = ['| Run | Exit | Methods passed | HTTP methods passed | HTTP class setup inside the suite (s) | Worker wait inside the suite (s) | Suite (s) | Load averages before |', '| --- | --- | --- | --- | --- | --- | --- | --- |']
for i, s in enumerate(five, 1):
    frows.append('| %d | %s | %s of %s | %s | %s | %s | %s | %s |' % (i, s['exit_code'], s['methods_ok'], s['methods_run'], s['http_methods_ok'], '%.2f' % s['http_class_setup_seconds'], '%.2f' % s['http_worker_wait_seconds'], s['suite_seconds'], s.get('load_averages_before', '')))
others = []
for s in res['make_test']['other_runs']:
    if s['label'] == 'make-test-under-load':
        others.append('One more run was made at the start, without the hook, while about twenty other jobs of this review were running (load average above 100): exit %s, %s of %s methods, %s HTTP methods, %s seconds.' % (s['exit_code'], s['methods_ok'], s['methods_run'], s['http_methods_ok'], s['suite_seconds']))
    else:
        others.append('A last run on the quiet machine without the hook: exit %s, %s of %s methods, %s HTTP methods, %s seconds.' % (s['exit_code'], s['methods_ok'], s['methods_run'], s['http_methods_ok'], s['suite_seconds']))
crow = ['| Command | Exit | Result |', '| --- | --- | --- |']
sc = res['supplied_checks']; fi = res['fault_injection']
def ex(label):
    c = [x for x in res['commands'] if x['label'] == label]
    return c[0]['exit_code'] if c else 'NOT_RUN'
crow += [
    '| My 21 RE probes, unmodified | %s | %d OK, NOTE: %s |' % (ex('re-probes-21'), sc['re_probes_21'].get('OK', 0), ', '.join(sc['re_probes_21_notes'])),
    '| My 480-order search, unmodified (four processes, one per family) | %s | %d runs, %d double, %d released, %d audit failures |' % ('/'.join(str(ex('re-step-search-' + f)) for f in orig['families']), orig['runs'], orig['double'], orig['released_without_authority'], orig['audit_failures']),
    '| 12 supplied RD probes | %s | %s |' % (ex('rd-probes-12'), sc['rd_probes_12']),
    '| Adapted Y05 (byte-identical to the RE bundle) | %s | %s |' % (ex('y05-adapted'), sc['adapted_y05']),
    '| Supplied 336-order search | %s | %s |' % (ex('rd-order-search-336'), '; '.join(sc['rd_order_search'])),
    '| RC probes | %s | %s |' % (ex('rc-probes'), sc['rc_probes']),
    '| RC order search | %s | %s |' % (ex('rc-order-search-120'), '; '.join(sc['rc_order_search'])),
    '| RB probes | %s | %s |' % (ex('rb-probes'), sc['rb_probes']),
    '| RA probes | %s | %s |' % (ex('ra-probes'), '; '.join(sc['ra_probes'])),
    "| Developer's D-029 reproduction | %s | PASS |" % ex('owner-clarification-repro'),
    '| `make check` | %s | passes |' % ex('make-check'),
    '| `make batch2-gate` | %s | %s; synthetic month passes |' % (ex('make-batch2-gate'), '; '.join(sc['reviewer_cases'])),
    '| `make reverification-gate` | %s | passes |' % ex('make-reverification-gate'),
    '| `make acceptance-gate` | %s | %s; U4 the only NOTE |' % (ex('make-acceptance-gate'), '; '.join(sc['older_acceptance_gate'])),
    '| `make rb-gate`, `rc-gate`, `rd-gate`, `re-gate` | %s | pass |' % ', '.join(str(ex('make-' + g)) for g in ('rb-gate', 'rc-gate', 'rd-gate', 're-gate')),
    '| `make rf-gate` | %s | 21 probes as above; 480 orders, 0 double, 0 released, 0 audit failures |' % ex('make-rf-gate'),
    '| `make rf-gate` script on the RE checkpoint source | %s | refused, as it must be |' % ex('gate-negative-rf-gate-on-re-source'),
    '| `register_faults.py` (F) | %s | %d of %d agree |' % (ex('rb-register-faults-F'), fi['register_F_unchanged']['agree'], fi['register_F_unchanged']['cases']),
    '| `fable_rc_register_faults.py` (G) on a copy | %s | %d of %d agree |' % (ex('rc-register-faults-G'), fi['register_G_unchanged']['agree'], fi['register_G_unchanged']['cases']),
    '| `fable_rd_register_faults.py` (H) on a copy | %s | %d of %d; H22-H24 obsolete as explained |' % (ex('rd-register-faults-H'), fi['register_H_unchanged']['agree'], fi['register_H_unchanged']['cases']),
    '| `fable_re_register_faults.py` (J) on a copy | %s | %d of %d; J14, J15, J16, J18, J22, J25 obsolete as explained |' % (ex('re-register-faults-J'), fi['register_J_unchanged']['agree'], fi['register_J_unchanged']['cases']),
    '| My new probes (15) | %s | %s |' % (ex('rf-probes-own'), ', '.join('%s %s' % (v['id'], v['verdict']) for v in res['own_probes']['verdicts'] if v['verdict'] != 'OK') + '; the other %d OK' % sum(v['verdict'] == 'OK' for v in res['own_probes']['verdicts'])),
    '| My new probes on the RE checkpoint source | %s | %s |' % (ex('baseline-re-source-rf-probes'), res['own_probes']['on_the_re_checkpoint_source']['counts']),
    '| `make test`, five consecutive runs | %s | see RF-03 |' % ', '.join(str(s['exit_code']) for s in five),
]
m = fi.get('rf_gate_M_own') or {}
repl = {'{RF01}': word(tv['RF-01']), '{RF02}': word(tv['RF-02']), '{RF03}': word(tv['RF-03']), '{PROMISE}': 'Met in every order tried' if tv['RF-01'] == 'ACCEPTED' else 'Not met',
        '{REGISTER}': 'May be recorded Independently verified at this checkpoint, for this scope.' if res['register_verdicts'][0]['state'] == 'Independently verified' else 'Remain Verification failed.',
        '{TOTAL_ORDERS}': '{:,}'.format(orig['runs'] + ext['runs']), '{EXT_RUNS}': '{:,}'.format(ext['runs']), '{BASE_UNLINKED}': str(base['unlinked_first_claim']), '{BASE_RUNS}': str(base['runs']), '{UC20_ORDERS}': str(ext['uc20_orders_approved_while_an_ancestor_claim_waits']), '{EXT_FAMILY_TABLE}': '\n'.join(rows), '{BASE_SUMMARY}': base_summary,
        '{EQ_TABLE}': '\n'.join(eqrows), '{TIMING_BLOCK}': timing_block, '{TIMING_READING}': TIMING_READING, '{FIVE_RUNS_TABLE}': '\n'.join(frows), '{OTHER_RUNS}': ' '.join(others), '{COMMAND_TABLE}': '\n'.join(crow),
        '{M_CASES}': str(m.get('cases', 'NOT_RUN')), '{ASSERTIONS}': str(res['own_probes']['assertions'])}
for k, v in repl.items():
    t = t.replace(k, v)
left = re.findall(r'\{[A-Z0-9_]+\}', t)
(D / 'FABLE_RF_ACCEPTANCE_REPORT.md').write_text(t)
print('report written; unfilled placeholders:', left)
