# RF/PRV developer correction report

Status: **DEVELOPER_VALIDATED — INDEPENDENT REVIEW PENDING**. This is developer evidence, not independent acceptance. Local fictional data and temporary databases only. D-026/D-029 and all readiness boundaries remain unchanged.

## Final developer results

Every required validation was run by Codex on local fictional inputs and temporary databases. No required validation is NOT_RUN. These are developer results; independent RF acceptance is pending.

- Unmodified baseline RE probes: **16 OK / 3 NOTE / 2 WEAK**, exit 1. Unmodified baseline step search: **480 orders / 40 double / 0 released / 0 audit failures**, exit 1; all 40 doubles are in `older-resent-with-claim`.
- Unmodified corrected RE probes: **19 OK**, only **C9c/C9g NOTE**, exit 0. Final `make rf-gate`: **480 orders / 0 double / 0 released / 0 audit failures**, exit 0.
- All nine required targets pass: `make check`, `batch2-gate`, `reverification-gate`, `acceptance-gate`, `rb-gate`, `rc-gate`, `rd-gate`, `re-gate`, `rf-gate`.
- Retained checks: 12 unmodified RD probes OK; Y05 OK and byte-identical to the RE bundle; 336 RD orders and 120 RC orders with zero double approvals; RC exact 16 IDs = 15 OK/X08 NOTE; RB = 16 OK/N02c+N04e NOTE; RA = 14 OK. Reviewer cases remain **29 PASS / 10 FIXED / 21 DEFERRED-OK**. U4 is the only NOTE in the older maintained acceptance gate.
- **Five consecutive complete `make test` runs passed 241 methods each**, with no skips or expected failures and all eleven HTTP methods executed in every run. All other managed validations finished before the sequence began; no other managed validation ran during it. Source, tests, scripts and Makefile hashes stayed unchanged throughout.

| Run | Methods passed | HTTP methods | Worker wait seconds | Total HTTP class setup seconds | Suite seconds | Exit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 241 | 11 | 2.268372 | 2.424715 | 987.984 | 0 |
| 2 | 241 | 11 | 2.259996 | 2.413763 | 987.862 | 0 |
| 3 | 241 | 11 | 2.355119 | 2.507561 | 994.556 | 0 |
| 4 | 241 | 11 | 2.436205 | 2.592605 | 1007.017 | 0 |
| 5 | 241 | 11 | 2.117719 | 2.291841 | 1008.262 | 0 |

The unchanged Fable timing script measured RF at 2.23–2.70 seconds versus the RD reference at 4.21–5.46 seconds under comparable concurrent load. The five complete suites measured worker wait at **2.117719–2.436205 seconds**, with the original five-second deadline. The observation-only sitecustomize hook and its exact source are retained; it changes no assertion, worker behavior or deadline. The prior exploratory full suite ran 240 methods and failed only the then-unadapted PRV-14 method, before D-031; it is not counted among these five passes.

RF-01 own coverage includes **40 variants** (known/unknown target × eligible/approved row × five replacement/approval timings × older/same-order conflicting retained message), unchanged governing heads, receipts, repeat idempotence, and the first-claim-link invariant after every delivery in **72 own permutations**. RF-02 covers confirming/replacing selections on the row, a revision and a live replacement, plus retargeting away from an earlier selected ancestor; both selectors are refused and an independent reviewer succeeds. RF-03 compares the shortcut against the full computation across all named states and preserves autocommit recomputation. PRV-16 tests both fourth-authority pins, failed verdict/downgrade behavior, all three older re-pinned authorities, rejection of older-following results, and the seven-row order.

[COMMAND_RESULTS.md](COMMAND_RESULTS.md) and [execution-results.json](execution-results.json) retain every recorded command, exit code, cwd, UTC start, duration, raw stdout/stderr and versions. [completion.json](completion.json) records the completed criteria. Environment: Python 3.9.6, SQLite 3.51.0, macOS 26.5.2 x86_64. An optional process-inventory diagnostic was **NOT_RUN** because the sandbox denied `/bin/ps`; file-based progress records were used. This blocked no required validation.

## Preservation and delivery

All **1,198 protected delivered inputs** retain their hashes. All 16 archives listed in `docs/corrections_re/archive-integrity.json`, the RE submitted bundle at `4890b297…98ae` and its returned response at `e0b0a499…cf2a` retain their hashes. The returned RE folder's 167 files match its pinned response ZIP byte for byte, with no extra/missing delivered input. Finder metadata and two pre-existing runtime backups are outside the payload rules; their original host hashes are separately retained and this pass did not edit or remove them.

All 88 IDs and their order, every acceptance criterion, product decision and implementation state, all four previously verified records, BB-01/02 and all six named Proposed records remain unchanged. The schema, HTTP test file/deadline and Y05 adaptation are byte-identical to the RE checkpoint. The entire prior DECISIONS.md is an unchanged prefix, preserving D-016/D-017/D-026/D-029. All 227 earlier methods remain present: **226 unchanged and only the D-031 method rewritten**. Complete before/after text and diff are below. Branch `review/fable-rc-acceptance`, ten commits and HEAD `5af9a6194bc39e2f303cc6b43b0b59094118b8e4` remain unchanged; no commit was added.

The new output label is `FABLE_RF_AND_PRV_CORRECTIONS`. The complete [change inventory](changed-files.json) compares every deliverable payload file against the RE bundle, including pre-existing differences, exports and documentation. The [source-and-tests patch](source-and-tests.patch) reproduces the changed code/test/gate files against that checkpoint. Every payload file is SHA-256 covered by `REVIEW_MANIFEST.json`; its hash is anchored in the adjacent package check, and the ZIP has its own `.zip.sha256` sidecar. The new archive, checksum, external manifest, package check and adjacent final-extraction evidence are an output envelope excluded from the payload to avoid self-reference. The adjacent `FABLE_RF_AND_PRV_CORRECTIONS_FINAL_VERIFICATION.json` records the clean extracted-archive checks. No earlier archive, sidecar or manifest is overwritten.

The next independent prompt is [FABLE_RF_REVIEW_PROMPT.md](../../FABLE_RF_REVIEW_PROMPT.md); it explicitly asks for other recorded-but-unapplied claim paths, extension beyond all four search families, and repeated complete suites. After delivery, await that independent review and a new user assignment. Three affected records remain Verification failed, all open observations remain open, and no human G0, G1–G4, Batch 3, readiness or live authority is granted.


## Ticket corrections

| Ticket | Change and location | Validation |
| --- | --- | --- |
| RF-01 | `accounting_agent/feed_contract.py`: apply the newly recorded first claim in the retained-message branch using the existing first-claim path. | 40-variant before/after matrix and 72-permutation invariant tests in tests/test_review_corrections_rf.py; C2d/C2f OK; baseline 40/480 double, corrected 0/480. |
| RF-02 | `accounting_agent/feed_contract.py`, `service.py`: preserve every selection author through revisions, live replacements and historical selected ancestry, separate from active ordinary dispositions. | Confirming/replacing selections for row/revision/replacement and historical ancestor retargeting pass; C9h OK. |
| RF-03 | `accounting_agent/packages.py`: reuse a run currentness result only within a single transaction and period_outcomes call. Autocommit readers recompute. No HTTP file/deadline change. | Full-computation equivalence across unclaimed, contested, selected, confirmed, revised, replaced and locked states; five consecutive complete suites passed; exact in-suite HTTP timings are below. |
| PRV-16 | Fourth immutable reviewer JSON/report pinned in register checker; latest per-record verdict wins in original seven-row order. All criteria/states/product decisions preserved. | New fourth-authority fault tests; original fault scripts; make check. |

Preflight: response e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a; RE source bundle 4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae; register 97876af92ef2d6e1daba18fd8a846a27d180613884f652bcc3211dfa8e28c34c; DECISIONS cef283d295970010028b9cff76866073a3e79301ac1d30d9575b4ceb0b079626. All matched. Branch review/fable-rc-acceptance, ten commits, HEAD 5af9a6194bc39e2f303cc6b43b0b59094118b8e4.

The unmodified RE probes reproduced 16 OK / 3 NOTE / 2 WEAK, exit 1, before correction. The corrected probes report 19 OK / C9c+C9g NOTE, exit 0. Raw logs and command metadata are retained alongside this report. Early own-test setup errors and intermediate failures are retained, not presented as final passes.

A retained-test conflict was reproduced in a disposable fourth-authority implementation. The owner explicitly resolved it in [D-031](../../DECISIONS.md) (quoted verbatim) and [OWNER_CLARIFICATION.md](OWNER_CLARIFICATION.md). Only `test_PRV14_third_authority_is_pinned_and_latest_verdict_controls` is rewritten. Its original first half still alters the RD input by one byte against the real four-authority configuration and asserts the unchanged hash-error message. Its second half omits the fourth JSON/report from the pinned-input data only; the same checker and unchanged assertions enforce the third authority in that historical fixture. The shipped checker always reads all four pinned authorities in chronological order. No validation is stubbed, bypassed or special-cased. All 227 retained methods are present; the other 226 are unchanged. Separate new methods test the real fourth-authority pins, failures/downgrades, older re-pinned inputs, rejection of results following older inputs, and seven-row order.

The earlier unapproved fixture proposal is retained as intermediate evidence only and was never applied to the working tests. The final authorized adaptation is below in full.

RE-02/RE-03 and PRV-14/15 were independently accepted at 4890b297…98ae. RE-01/RB-01 remains unaccepted for RF-01. AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay Verification failed pending independent review of this new checkpoint. All 88 IDs, every acceptance criterion, BB-01/02, six named Proposed records, schema and D-016/D-017/D-026/D-029 remain protected.

Open owner observations remain U4, UC-14, UC-17 (de-selected first target stays retired), UC-18 (exact replay leaves no additional supplier), UC-20 (replacement of a waiting claimant retains only ordinary transition until target arrival). X08, N02c, N04e, C9c and C9g remain NOTE; UC-9 remains journals/read-only. No Batch 3, client records, live connection, paid/model service, sending, posting, payment, deployment or operating authority.


## Interpretation of unchanged historical register faults

The original scripts remain byte-identical. Final exact outputs and exit codes are linked in COMMAND_RESULTS.md; every injected file and pin was restored.

| Script | Exact summary | Exit | Interpretation |
| --- | --- | --- | --- |
| register_faults.py | cases 37 / agree 37 / gaps 0 | 0 | All controls agree. |
| fable_rc_register_faults.py | cases 44 / agree 44 / gaps 0; make check gaps 0 | 0 | All controls agree, including G16/G17/G18/G44. |
| fable_rd_register_faults.py | cases 37 / agree 34 / gaps 3 | 1 | H22–H24 assume the RC review is latest; later pinned reviews override it. |
| fable_re_register_faults.py | cases 35 / agree 29 / gaps 6 | 1 | J14/J15/J16/J18/J22/J25 assume RD is latest or RE is unreviewed; RE is now the fourth authority. |

H22 attempts a downgrade from an older RC verdict and H24 attempts an older RC promotion; matching project results are rejected against the fourth authority. H23 expects an altered older RC failure to defeat the current accepted result; the fourth verdict correctly remains controlling.

J14 and J16 alter/re-pin the older RD verdict but keep current project results: accepted because RE still controls. J15 and J18 make results follow those older altered verdicts: rejected because they disagree with RE. J22 removes the older RD GOV-03 verdict: RE still supplies it, so current results remain accepted. J25 substitutes the RE bundle hash for CTL-04: that is now the correct reviewed hash, so the no-op is accepted. The new fourth-authority tests exercise the actual current precedence and rejection rules without weakening latest-wins.

## RF-03 equivalence argument

`period_outcomes` performs only reads. Within a database transaction every `_current` evaluation sees the same SQLite snapshot; repeated evaluations of the same run are therefore identical. A local dictionary reuses that result only until this one call returns. It is never shared across calls, connections, threads, scopes or states. Autocommit callers use the original computation for every observation, preserving visibility of concurrent commits. No declaration, link, selection, policy, frozen-run, fingerprint, definition-hash, blocker or review check is omitted. Tests compare full report outputs with the full computation for unclaimed demo card/journal rows and waiting, contested, selected, confirmed, revised, replaced and locked states; they also assert that autocommit observations always recompute.

Using the unchanged Fable timing script under comparable concurrent load, RF worker completion was 2.23, 2.44, 2.70, 2.33, 2.31 seconds; the unchanged RD reference was 4.67, 4.21, 5.42, 4.75, 5.46 seconds. These are comparison measurements, not the five consecutive suite criterion. The initial in-suite observation measured 2.456262 seconds for worker wait and 2.634189 seconds for total setup; final consecutive-suite measurements are recorded separately.

## Disclosed intermediate results

All raw logs remain. The default sandbox refused the local HTTP bind; the authorized loopback-enabled timing rerun passed. An early disposable rb-gate copy omitted a protected response ZIP; a complete copy passed. The new preservation inventory initially included Finder metadata and two runtime database files excluded by the established payload rules; their original host hashes remain in excluded-host-metadata.json, while delivered protected inputs are checked separately. No such host file was changed or removed. Early own-test assertions incorrectly expected retired predecessors in the live hold list and expected UC-20 to change; those new fixture assertions were corrected while preserving all retained tests/probes and the expressly excluded UC-20 behavior. The original retained PRV-14 conflict was reported before D-031 authorized its sole adaptation. Extending the new precedence fault to the earliest authority also invalidated that fixture's old evidence citation. The fixture now cites the fourth accepted checkpoint while running the same validation; the production register's verified citations remain unchanged. No intermediate failure is represented as a final pass.


## D-031: complete retained-method before/after and diff

Before:

```python
    def test_PRV14_third_authority_is_pinned_and_latest_verdict_controls(self):
        import hashlib,json
        from unittest.mock import patch
        import scripts.check_product_requirements as cpr
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;original=path.read_bytes()
            path.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):validate_register(self.text,root)
            data=json.loads(original)
            for row in data['register_verdicts']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            changed=json.dumps(data).encode();path.write_bytes(changed)
            result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
            for row in results['results']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            result_path.write_text(json.dumps(results))
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
                validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
```

After:

```python
    def test_PRV14_third_authority_is_pinned_and_latest_verdict_controls(self):
        import hashlib,json
        from unittest.mock import patch
        import scripts.check_product_requirements as cpr
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;original=path.read_bytes()
            path.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):validate_register(self.text,root)
            path.write_bytes(original)
            # Historical three-authority fixture: omit only the fourth pinned inputs as data.
            fourth={'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json',
                    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'}
            three_inputs={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in fourth}
            with patch.dict(cpr.REVIEW_INPUT_HASHES,three_inputs,clear=True):
                data=json.loads(original)
                for row in data['register_verdicts']:
                    if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
                changed=json.dumps(data).encode();path.write_bytes(changed)
                result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
                # Derive the fixture rows with the same unmodified validation code.
                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                    results['results']=list(cpr.reviewer_verdicts(root)[0].values())
                result_path.write_text(json.dumps(results))
                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
                    validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
```

Complete diff:

```diff
--- a/tests/test_product_requirements.py
+++ b/tests/test_product_requirements.py
@@ -199,14 +199,21 @@
             root=self.reviewer_fault_copy(tmp);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;original=path.read_bytes()
             path.write_bytes(original+b'\n')
             with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):validate_register(self.text,root)
-            data=json.loads(original)
-            for row in data['register_verdicts']:
-                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
-            changed=json.dumps(data).encode();path.write_bytes(changed)
-            result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
-            for row in results['results']:
-                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
-            result_path.write_text(json.dumps(results))
-            with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
-                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
-                validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
+            path.write_bytes(original)
+            # Historical three-authority fixture: omit only the fourth pinned inputs as data.
+            fourth={'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json',
+                    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'}
+            three_inputs={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in fourth}
+            with patch.dict(cpr.REVIEW_INPUT_HASHES,three_inputs,clear=True):
+                data=json.loads(original)
+                for row in data['register_verdicts']:
+                    if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
+                changed=json.dumps(data).encode();path.write_bytes(changed)
+                result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
+                # Derive the fixture rows with the same unmodified validation code.
+                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
+                    results['results']=list(cpr.reviewer_verdicts(root)[0].values())
+                result_path.write_text(json.dumps(results))
+                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
+                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
+                    validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
```
