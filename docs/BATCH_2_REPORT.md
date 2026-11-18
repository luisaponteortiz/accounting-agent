> Historical developer checkpoint report. Fable independently rejected current C-01 and Batch 2 in exports/FABLE_REVERIFICATION/FABLE_REVERIFICATION_REPORT.md. Current RV corrections and test evidence are in docs/REVERIFICATION_CORRECTIONS_REPORT.md. The 111-test and eleven-approval results below describe the earlier source, not the revised walkthrough.

# Corrective and Batch 2 implementation report

C-01–C-06 were reproduced, implemented in Fable's order and gated before Batch 2. T-09–T-19 then followed the prescribed dependency order. No technology-stack replacement, Batch 3 implementation, live access, posting, payment or deployment occurred.

## Corrective results

| Correction | Implemented protection | Reproduction/regression evidence |
| --- | --- | --- |
| C-05 | NFKC/casefold retains Unicode L/N/M, including combining marks | N06, exact Unicode/accent tests |
| C-06 | Actor.kind is mandatory; missing kind cannot become human | N07; explicit actor call sites; service review denied |
| C-02 | Every decision refuses PERIOD_LOCKED/409 | N01; all five decision types tested; audited reopen required |
| C-04 | Historical input/configuration preparation cannot disappear behind another author | N04/N05; later rule/item lineage includes applied rule and relevant chart/entity/book authors |
| C-03 | Contributor provenance is append-only outside content identity | N03; identical colleague/recurring preparation preserves rejection/approval and adds contributors |
| C-01 | Locked-origin moves are quarantined until reopen and cannot govern another period | N02; transaction/support binding, cross-period uniqueness and replay tests |

Before changes, N01–N07 all failed. At the frozen corrective checkpoint the exact supplied unmodified script reports all seven OK and Corrective gate PASS; all required earlier probes remain OK. Its full suite was 81 tests: 76 passes, five then-deferred expected failures. The four supplied verification files remain byte-identical.

The current Batch 2 API intentionally requires independent approval and explicit source/authority contracts that the original script's setup cannot express. Current ordinary tests run the maintained adapted harness, with the same corrective assertions and additional Batch 2 checks. Both the unmodified checkpoint rerun and current harness pass. See FABLE_CORRECTION_REVERIFY.md for exact commands and the reason for this distinction; the original script was not silently rewritten.

## Current execution gate

**Final make test: 111 tests passed in 168.653 seconds**, with no expected failures, failures or errors. The complete output is docs/batch2/final-tests.txt. The suite includes the 41 original platform/HTTP methods, corrective regressions, separate journal/receipt-policy behavior tests, source/period/migration/concurrency tests (including deterministic in-flight close waiting), unrelated-rule isolation and item-effective review-policy tests, HTTP approval/disposition/finalization boundaries, both reviewer gates and a full teaching-month walkthrough. There are no expected-failure assertions preserving repaired defects.

- make check passes offline syntax/JSON/profile/registry checks. This is not a JavaScript compiler, external linter or production readiness test.
- make batch2-gate passes all ten original fail-until-fix cases and the stronger current probe gate, including N01–N07. The current run contains no WEAK or ERROR verdict. The remaining N16/N18 diagnostic notes describe policy reversion and intentional punctuation normalization, not claims of distinct merchant identity.
- Independent original verifier rerun on the frozen corrective source: PASS. Raw output is docs/batch2/checkpoint-rerun.txt.
- The 60 maintained reviewer cases: **29 PASS, 10 FIXED, 21 DEFERRED-OK; zero FAIL, UNEXPECTED, KNOWN-FAIL or DEFERRED-LEAK.** The extra executable case is FV-CL04; AP/AR/full reconciliation/reporting specifications remain refused.

| Status | Case IDs |
| --- | --- |
| PASS | FV-C01, FV-C02, FV-C03, FV-C04, FV-C05, FV-C06, FV-C07, FV-C08, FV-C09, FV-C10, FV-C11, FV-C12, FV-C13, FV-C14, FV-C16, FV-C17, FV-C18, FV-C19, FV-J01, FV-J02, FV-J03, FV-J04, FV-J05, FV-J06, FV-J07, FV-CL01, FV-R02, FV-RC03, FV-CL04 |
| FIXED | FV-C15, FV-J08, FV-J09, FV-J10, FV-CL02, FV-R01, FV-R03, FV-R04, FV-RC01, FV-RC02 |
| DEFERRED-OK | FV-AP01, FV-AP02, FV-AP03, FV-AP04, FV-AP05, FV-AR01, FV-AR02, FV-AR03, FV-AR04, FV-BK01, FV-BK02, FV-BK03, FV-BK04, FV-BK05, FV-CL03, FV-GL01, FV-RP01, FV-RP02, FV-RP03, FV-RP04, FV-RP05 |

## What runs and remains unconnected

PROGRESS.md lists every completed component, its tests and its unconnected boundary. A document label alone cannot satisfy a typed reconciliation/tieout requirement while its capability is deferred. The runnable application now has approved effective knowledge, required facts, ordered source lifecycle, independently approved fresh-evidence mandates, structured statement checks, dispositions, common proposed entries, stronger journal controls, receipt policy, frozen preparation packages and outcome-aware readiness. HTTP/UI supports dispositions/revocation, mandate proposal/approval, finalized package inspection and explicit lock acknowledgement. Additional independent reviewers are distinct service actors; the local two-role selector cannot supply real identities or simulate every review role.

The service-only original teaching-month walkthrough records:

- Nine card approvals and two journal approvals, after explicit fictional corrections/dispositions. Receipt/journal originals remain in evidence history.
- TX-007 remains PENDING_TRANSACTION and TX-011 remains CURRENCY_MISMATCH with explicit external-referral dispositions. These items never become clean or approved. October TX-008 stays quarantined and is named in the handover acknowledgement.
- Two immutable preparation packages finalized, then November locked with a recorded acknowledgement. This is not an external closed ledger.
- Approved proposed-entry impact: office supplies +391.00, repairs +200.00, card liability −291.00, cash −300.00; net zero. Tests assert these hand-calculated totals.
- A second isolated client's December journal executes and is independently reviewed without changing the first client's artifact IDs/hashes/statuses or package bytes. Both audit chains verify.

scripts/synthetic_month.py performs only service operations against temporary databases. docs/batch2/synthetic-month.json and final-gate.txt retain execution evidence. These are G0 software criteria for human review, not actual Bird Bowl accounting validation. Human G0 acceptance and independent Fable reverification are pending; G1–G4 remain closed.

## Changes, migrations and retained records

Runtime changes: accounting_agent/core.py, modules.py, service.py, storage.py, controls.py, source_control.py, exceptions.py, packages.py, demo.py, http.py, config/bird_bowl.demo.json, fixtures/, web/ and version metadata. New migrations 6–12 preserve historical evidence/artifact/decision/audit bytes; mutable heads/statuses remain separate from immutable records. Legacy, foreign-key, concurrent startup and immutable-trigger tests pass.

Tests: test_corrections.py, test_corrective_gate.py, test_batch2.py, test_batch2_controls.py, test_synthetic_month.py, test_reviewer_probes.py/test_reviewer_cases.py, original platform/HTTP methods and typed regression fixtures. Maintained reviewer inputs and setup are explicitly adapted; original inputs/scripts are preserved. Scripts build/verify archives, report actual differences, rerun the frozen checkpoint and exercise the synthetic month.

Active docs, PROGRESS.md and DECISIONS.md reflect implemented behavior. docs/batch2/changed-files.json is the exact changed-file/hash inventory; source-and-tests.patch compares against the delivered Batch 1 archive, since this workspace has no tracked source baseline. The bundle contains complete source and a verified SHA-256 manifest, including the frozen corrective checkpoint; no runtime database or credential is packaged.

## Unresolved or deferred limits

The final combined gate passes. No unexpected failing acceptance case remains in this batch. Independent Fable review may reveal additional defects and has not been substituted by developer tests. No actual Bird Bowl facts, accounting framework, mappings, document/FX/recognition policy or real authority have been invented.

Batch 3 remains untouched: full reconciliation, settlement pairing, trial-balance intake, AP/AR execution, worker error/backoff/heartbeat hardening, atomic live-export consistency/audit anchoring, general currency minor units and production identity/bounded reads. Reporting, model use, authentic document verification, noncalendar statement-cycle policy and live scheduling also remain unavailable. Whole live export still uses two transactions with an input guard; finalized package payload/hash are immutable. Existing audit chains are local hashes, not WORM or external attestation.

All records and tests are fictional. No live client connection, accounting posting, payment, paid model/hosting, external communication or production deployment occurred. Stop at this source checkpoint for independent verification; no Batch 3 work is included.
