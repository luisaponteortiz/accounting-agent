# Accounting Agent OS progress — Batch 1

Status: **T-01–T-08 complete; Batch 1 gate passed. Batch 2 not started.** Local/demo, fictional data only. The Python/SQLite foundation is preserved. Actual Bird Bowl policies, accounts, system readiness, hosting and human authority remain unconfigured.

## Verified outcome

- Baseline reproduced before code changes: original 41 tests pass; Fable 28 PASS / 10 KNOWN-FAIL / 22 DEFERRED-OK. All 16 diagnostic probes executed.
- Final `make test`: **72 tests: 67 pass, 5 expected Batch 2 failures**, no unexpected errors/failures/successes. All original 41 test methods are retained and pass with documented period/run-link contract changes.
- All 60 reviewer cases: **28 PASS, 6 FIXED, 4 KNOWN-FAIL, 22 DEFERRED-OK**. No FAIL, UNEXPECTED or DEFERRED-LEAK.
- Six-case gate: FV-C15, FV-R01, FV-R03, FV-R04, FV-RC01 and FV-RC02 all FIXED.
- Required probes P01–P06, P09–P11, P14 and P16 pass as unit tests. P07/P08/P12/P13/P15 are explicit expected failures for deferred Batch 2 defects.
- `make check` passes. Independent runner and probe scripts also pass using the user's exports/FABLE_REVIEW_RESPONSE command paths.
- Developer browser checks verify period selection, independent approval, opening another month, lock-preserved approval, reopening and unrelated card-evidence isolation. Screenshot is included in the updated bundle.

## Implemented corrections

| Ticket | Result |
| --- | --- |
| T-01 | Exact blocker assertions and independent reviewer gate adopted; derived regression fixture labeled honestly. |
| T-02 | Unicode-safe normalization and empty-alias rejection; ambiguous vendors remain held. |
| T-03 | Explicit actor kind and immutable contributor-based review independence. |
| T-04 | Occurrences separated from runs; stale re-dispatch, explicit skips, mandate fault isolation, one completed attempt per occurrence. |
| T-05 | Durable periods/status history, source-period binding, independent administration, protected locked work and late-activity exceptions. |
| T-06 | Workflow/period-scoped declared input manifests and accounting-code lineage; unrelated workflow/transport changes preserve approvals. |
| T-07 | One governing artifact per item, identical artifact reuse, append-only run links/decisions, duplicate rejection and visible disputes. |
| T-08 | Docs align with behavior; package.manifest records provenance only; documentation IDs checked; screenshot bundled. |

Schema migrations 2–5 are covered by legacy-byte/foreign-key/restart/concurrent-start tests. Existing audit/evidence/artifact/decision records remain immutable. Client isolation, recovery, bounded retries, exact money, review revocation and socket-denied preparation remain tested.

## Accounting coverage and remaining defects

Only the existing card preparation, mechanical journal validation and document-presence close checklist execute. Four Fable cases intentionally remain KNOWN-FAIL: FV-J08 (journal duplicates), FV-J09 (no-effect journal), FV-J10 (unbound support) and FV-CL02 (close ignores upstream exceptions). Source revision ordering, statement population identity, receipt-policy configuration, independent policy/mandate activation, shared proposed entries, exception dispositions, formal entity/book/review-policy binding, finalized packages and atomic export remain unimplemented.

AP, AR, full banking/reconciliation, reporting/analysis, real connectors/models, live schedules, ledger writes, payments, final close, production identity/persistence/deployment remain deferred. No accounting framework, client policy or commercial/support authority was invented. No paid services or live systems were used. Full G0 synthetic acceptance requires later work and is not claimed.

## Evidence and next boundary

See docs/BATCH_1_REPORT.md for the complete 60-case classification, changed files, contract changes, unresolved defects and commands. Raw before/after evidence is in docs/batch1/. The original reviewer scripts remain in review/original/. Active architecture and capability contracts describe exact current behavior; DECISIONS.md records each ticket's changes.

Stop at the Batch 1 gate. Do not begin Batch 2 or activate any deferred capability without the user's next assignment. Human accounting acceptance and Theresa's own teach-back/independent operation, real-model evaluation, connector validation, hosted UAT and production readiness have not been performed.
