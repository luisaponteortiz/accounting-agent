# RA-01–RA-08 correction response

Local fictional accounting preparation only. All eight assigned RA corrections are implemented in the prescribed order. **154 tests and all maintained gates pass with the disclosed statement-setup adaptations.** Independent verification of this pass, human G0 and Batch 3 remain closed.

## Independent inputs and reproduction

Fable accepted 14 of 17 RV corrections, all seven prior probe adaptations and strengthened RT14b. It found one new P1, three P2 and four P3 issues. All 27 returned files under exports/FABLE_RV_ACCEPTANCE/ are unchanged. Before editing source, all 243 working files matched the submitted frozen archive, SHA-256 `247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75`. The new unmodified script reproduced **16 OK / 4 WEAK / 4 NOTE**, exit 1, with A10/X01/X12k/X12s failing. Raw baseline evidence and 57 input/archive preservation hashes are in docs/acceptance_ra/.

The user returned the independent results and authorized this correction pass. The old archive and freeze sidecar are preserved. Working source may change for RA tickets only. The packager now refuses to overwrite any submission with a .FROZEN.json sidecar. No runtime accounting database, live client system, model call, posting, payment, deployment or paid service was used.

## Implementation, in order

| Ticket | Correction | Regression and independent evidence |
| --- | --- | --- |
| RA-01 (P1) | Resolve the full supersession chain, inherit locked-origin quarantine, keep all blocked predecessors/receipts visible and record root approval/move evidence. Reopen admits the terminal replacement first and removes all ancestors; intermediate transactions never enter the destination binding history. Cycles refuse atomically. | X01/A01; three-link quarantine/reopen/history test, cycle refusal, valid destination revision after former-origin relock, original lock/move tests. |
| RA-03 (P2) | Compare current receipt support with prior same-key versions and withdrawn other keys for the same account/transaction. Retain replaced/revised classification, old/current identities, hashes, fields and suppliers. Both identities' suppliers cannot accept; old support authors remain final-review contributors. | X12k/A12; replacement supplier/lineage tests; adding a still-active second receipt remains a multiple-document issue, not a revision. |
| RA-04 (P2) | Include statements in revision/replacement detection. Each relying item receives the revised-evidence hold. Workpapers disclose statement_revisions. Acceptance is item-bound, requires a granted non-supplier and does not confer final review; later change lapses it. | X12s/A13; same-key/new-key statement tests, both suppliers refused, selective item acceptance and subsequent-change hold. |
| RA-02 (P2) | Find prior approved rules by scoped kind/key/item identity without relying on optional supersedes. Preserve semantic author/approver history while allowing different historical category, unrelated alias or unrelated item scope. | A10; unlinked vendor/receipt-policy regressions and positive review controls; earlier RN04/RN05/RN05b retained. |
| RA-06 (P3) | Use one reference predicate at disposition submission and activation: current sources plus that item's immutable predecessor refs. Whole-evidence transition acceptance now takes effect after reopen. | New after-reopen whole-evidence disposition regression; X01/A01 and source-history controls. |
| RA-05 (P3) | Bind mandates to approved workflow-relevant policy windows and retirement effects, independently of source dates/presence. Full-period coverage has stable boundary representation across the existing recurring period transition. Real relevant policy changes still suspend; future retirement outside the target window does not. | U1; mid-period arrival dispatch, actual subsequent rule suspension, future-retirement test; old RT10a/N11 retained. |
| RA-07 (P3) | Count only related supporting documents: a transaction's receipt/account-cycle statement or a journal's named journal_support; duplicate comparisons may cite actual candidates' receipts. A transaction row is never supporting evidence. | A14; unrelated row/receipt refusal and valid own-receipt coding; A07/A08/A09/M1/M2. |
| RA-08 (P3) | Reject duplicate_of/source_replay when the target already has an active exclusion, even before re-preparation. Retain one live survivor and preserve revocation behavior. | X09 circular phase; both exclusion choices tested before re-preparation, entry preservation and restored holds on revocation. |

No schema migration, new accounting module or stack replacement was needed. Historical evidence, artifacts, decisions, packages and audit bytes remain immutable. An older mandate signature may require explicit reconfirmation under the changed control; it is never silently rebound. Existing original platform/HTTP methods remain retained.

## Gates and the required setup boundary

Final raw logs, exit codes and machine-readable results are in docs/acceptance_ra/. The completed results are:

| Command | Exit | Result |
| --- | --- | --- |
| make test | 0 | **154 methods OK**, no expected failure/skip; original methods retained |
| make check | 0 | Offline Python/JSON/profile/registry/DOM checks pass; no external linter/typechecker claim |
| make batch2-gate | 0 | **29 PASS / 10 FIXED / 21 DEFERRED-OK**, old maintained probes and teaching month pass |
| make reverification-gate | 0 | **27 compatible originals OK / all 35 current-setup OK**; unmodified frozen corrective checkpoint passes |
| make acceptance-gate | 0 | **20 compatible originals: 19 OK + U4 NOTE; all 24 current-setup: 23 OK + U4 NOTE** |
| Full original acceptance command | 1 | **19 OK / 3 WEAK / 1 ERROR / U4 NOTE**; four revised-statement positive setups lack the new required acceptance |
| Full original older RV command | 1 | **28 OK / 4 WEAK / 3 ERROR**; prior seven setup conflicts plus RT18's revised statement |

Raw final command logs use final-*.txt. The complete 60-case report and per-ticket acceptance criteria/method links are in execution-results.json. The focused period-relock regression was reproduced failing, corrected, and included in the final full run. The gate commands are:

```sh
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
```

The original four failed acceptance IDs now pass directly from the unchanged independent script. The current-setup acceptance file runs all 24 original controls, with **23 OK and one permitted U4 NOTE**. U4 is Fable's accepted visible non-restoration behavior, not an assigned defect. The 60-case gate remains **29 PASS / 10 FIXED / 21 DEFERRED-OK**; every case ID is retained individually in docs/batch2/final-validation.json. DEFERRED-OK validates refusal, not future AP/AR/reconciliation/reporting execution.

**The full original acceptance command still exits 1 for four statement-setup incompatibilities: A03/A05/X09 WEAK, A17 ERROR. It is not claimed to pass.** Those positive fixtures re-supply statements then expect immediate eligibility. RA-04 now requires independent acceptance. The separately generated copy adds that explicit setup, after first asserting the revision hold/history, with the original identities/grants and every original return/assignment unchanged. No blocker is weakened. The original script runs directly on its 20 unaffected probes in the normal gate.

Older RT18 has the same new setup requirement; its explicit acceptance step preserves the original stale-package negative and all dispute/recovery assertions. The older gate now runs 27 unchanged-setup originals and all 35 current-setup controls. The seven previously accepted adaptations and strengthened RT14b remain intact. The frozen unmodified historical corrective checkpoint is also required to pass.

Read docs/acceptance_ra/probe-adaptations.md and both exact patches. These additional setup changes are returned under Fable's explicit API-change exception and require its independent judgment. Passing an adapted developer gate is not acceptance of the original full command, G0 or the adapter itself.

## Teaching month, isolation and preservation

Both existing routes remain required and distinct. The delivered referral route retains TX-009's 79.99 receipt unchanged: ten approvals, TX-007/TX-009/TX-011 held, office supplies +311.00, repairs +200.00, card liability −211.00 and cash −300.00. The explicit evidence-acceptance route retains eleven approvals and +391.00 supplies / −291.00 liability, with the same repairs/cash. Both net to zero and retain quarantined October evidence, independent review, immutable preparation packages, acknowledged lock and a scoped second-client December run. Neither is a completed accounting close.

All 27 new independent inputs, prior inputs and four historical ZIPs are protected by checksums. New tests also exercise frozen-package refusal, audit integrity and source/contributor history. No actual Bird Bowl facts/policies/accounts/authority were invented. Manual statements and document content remain unauthenticated fictional evidence.

## Changed files and new bundle

The actual correction inventory and source/tests patch compare against the frozen submitted RV archive in docs/acceptance_ra/changed-files.json and source-and-tests.patch. The cumulative Batch 1 comparison in docs/batch2/ is also refreshed and includes web assets. Primary runtime changes are in source_control.py, service.py, controls.py, exceptions.py and modules.py; tests, review-setup generators, Makefile, packager and current documentation expose the new contracts. The original supplied scripts remain untouched.

Return archive: `exports/FABLE_RA_CORRECTIONS_REVIEW_BUNDLE.zip`. Its outer source is current; the nested frozen RV archive is the reviewed baseline. The new handoff/prompt, original 27 files, all older independent inputs, exact deltas, regression tests, command results, source inventories and checksum manifest are included. Runtime databases, credentials and live records are excluded.

No assigned RA correction is being deferred. Independent confirmation of the fixes and new setup changes remains pending. Human G0 and G1–G4 remain closed; Batch 3, AP/AR, full reconciliation/reporting, live connections, posting, payments, final close and production deployment are not authorized. The next step is independent re-verification of this correction checkpoint.
