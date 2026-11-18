# Evidence for the feed-contract decisions UC-21, UC-22 and UC-23 (D-038)

17 November 2026. The owner's decision and the record of the work are in D-038 at the end of `DECISIONS.md`. The work and its review tests are by the same Claude (Fable) session, as D-036 and D-037 allow; no separate review has examined them.

## What changed

| Item | Change |
| --- | --- |
| UC-21 | An identical repeat of a card row's message, claim included, or of its receipt, changes nothing when a live replacement that is admitted to its period has retired the row. |
| UC-22 | A message with no sequence number or timestamp, for a row governed by one and carrying different data, is kept as evidence once, never governs, and is flagged once per distinct content as `SOURCE_ORDER_MIXED` in the state, the export and the local page. |
| UC-23 | Accepted as built. No source change. |
| Source | `accounting_agent/feed_contract.py`, `source_control.py`, `service.py`, `web/app.js`: 56 changed lines, in `source.patch`. No schema change. The four files as they stood before are byte-identical to the delivered RF bundle. |
| Tests | `tests/test_feed_repeat_decisions.py`, twelve new review methods. No retained test method, reviewer probe, fault script or gate script changed. |

## Results

All commands ran unmodified, once, on a disposable clone whose 107 source, test, script, review and document files are identical to the final working project. The clone's source was unchanged at the end of the run.

| Check | Result |
| --- | --- |
| `make test` | exit 0; 274 of 274 methods in 1,071.571 s; all eleven HTTP methods; no skips or expected failures |
| `make check` | exit 0 |
| `make batch2-gate`, `reverification-gate`, `acceptance-gate`, `rb-gate`, `rc-gate`, `rd-gate`, `re-gate`, `rf-gate` | all exit 0. RC gate: 16 OK, 2 NOTE, 0 WEAK. RF gate: 19 OK with C9c and C9g NOTE; 480 orders with zero double approvals, zero releases without authority and zero audit failures |
| RE review's unmodified probe script | 21 probes: 19 OK, 2 NOTE (C9c, C9g), 0 WEAK, 0 ERROR, as before the change |
| RF review's unmodified probe script | 15 probes: 14 OK, 1 NOTE (G1c, which is UC-20), 0 WEAK, 0 ERROR. G1g and G5a, which recorded UC-22 and UC-21, changed from NOTE to OK |
| `scripts/check_documentation.py` | PASS; 274 methods, 38 decisions, 88 records, seven Independently verified, none Verification failed |
| The twelve review methods against the source as it stood before the change | 9 of 12 fail or error (6 fail, 3 error; 15 failing sub-cases); 3 pass |
| Final checks in the working project | `make check`, the documentation checker and 65 feed, documentation, register and protected-input methods pass; the page script parses and renders the anomaly line |
| Preservation | all 1,198 protected inputs of the RF pass, all 1,506 entries of the registration inventory, 16 earlier archives, the RF and RE bundles and responses and all 298 returned RF response files unchanged; branch `review/fable-rc-acceptance`, HEAD `5af9a61…` and ten commits untouched; nothing staged |

The three review methods that pass on the earlier source are boundary tests of behaviour that D-038 deliberately keeps: a newer order value or different data is still recorded, a row whose live replacement is held is still recorded and held, and a first claim on a repeated message is still applied. They guard against the change reaching too far, so they are expected to pass both before and after.

Nineteen of the 1,790 payload files of the delivered RF bundle now differ in the working project: the fifteen from the registration and documentation steps and the four source files above.

## The first validation run failed

The first full run is kept in `first-run-failed/`. `make test` exited 2 with one failure, `test_all_18_unmodified_probes_meet_exact_contract`, and `make rc-gate` exited 2: the independent RB review's unmodified probe N01e reported WEAK. A retired middle link of a three-deep chain, re-sent after the chain came to rest under a locked period, no longer took the locked-period hold. The probe was not edited. The change was narrowed so that UC-21 applies only while the live replacement's latest period binding is admitted, a review test was added for that boundary, and the whole validation was run again from the start.

An earlier narrowing came from the retained method `test_RD02_retired_claimant_resent_unchanged_without_claim`, found during development: a re-send that omits a claim the row has is a later omission under clause 6, not a repeat. That method was not edited either.

Two cases of UC-21 are therefore left as they were before D-038: the re-send that omits the row's claim, and the re-send while the live replacement is held.

## Files

| File | Content |
| --- | --- |
| `validation/` | `results.json` (command, exit code, time and load for each step), complete standard output and error of every step, the hashes of the tested source, the source-unchanged comparison and the orchestrating script `validate_uc.py`. |
| `first-run-failed/` | Results, suite output and RC gate output of the failed first run. |
| `development-checks/` | Checks made while developing, before the full run: reviewer probe outputs, the retained-subset run, the RC gate after the second narrowing, an earlier baseline run and the exploration script. The baseline in `validation/` is the one to cite. |
| `source.patch` | Unified diff of the four source files against their state before the change. |
| `apply_source_change.py`, `apply_document_change.py` | The assertion-checked scripts that made the source and document edits. |
| `page_check.js`, `page-check.txt` | Parses `web/app.js` and exercises its source-exceptions line with stub page functions in JavaScriptCore; the output. |
| `final-checks.txt` | The checks run in the working project after the validation. |
| `before.sha256`, `after.sha256` | SHA-256 of every file this step touched, before and after, and of the new test file. `tests/test_documentation_review.py` is listed and did not change. |
| `verify_preservation.py`, `preservation.json` | Read-only preservation check on the final state. Its general flag for "every acceptance criterion unchanged" is false by design, as in the D-037 evidence: the one criterion that differs from the RF bundle is the AAOS-GOV-02 sentence changed under D-037. |

## Limits

- The same data sent without an order value is treated as an ordinary repeat and is not flagged. A provider that mixes ordering without changing data is not detected.
- The anomaly has no acknowledgement or disposition workflow. It stays listed.
- The page line was checked in a JavaScript engine with stub page functions, not opened in a browser.
- Ordering of receipts, statements and documents is unchanged. Journals remain outside the contract. How a real provider orders its messages remains a G2 confirmation.
- Each command ran once.
- These source changes follow the RF checkpoint, which the seven Independently verified records cite, and the owner's G0 acceptance (D-036). No pinned review result covers them, so no record was raised or re-based. Whether to re-affirm G0 for the changed source is the owner's decision.
- Nothing is committed. G1 to G4, Batch 3 and all live actions remain closed, and no further implementation is authorized.
