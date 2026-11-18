# Batch 1 implementation and verification

All work is local/demo with fictional accounting data. T-01 through T-08 are complete. The prescribed Batch 1 gate passed; Batch 2 has not begun. No stack rewrite, real client connection, posting, paid service or deployment occurred.

## Reproduction before modification

The original 41 tests passed. The supplied runner reproduced PASS=28, KNOWN-FAIL=10 and DEFERRED-OK=22. All 16 diagnostic probes were executed. Raw evidence is retained in `docs/batch1/baseline-original-tests.txt`, `baseline-validation.txt` and `baseline-probes.txt`. Original reviewer scripts remain unchanged in `review/original/`.

## Corrections

| Ticket | Implemented correction |
| --- | --- |
| T-01 | Independent suite adopted; exact blocker sets; P01–P16 required-outcome regressions; strict gate and JSON case results. |
| T-02 | Unicode NFKC/casefold normalization preserves letters/digits and accents; empty aliases are rejected; ambiguous/empty descriptors cannot receive clean vendor coding. |
| T-03 | Explicit human/service identity; immutable hashed contributors cover inputs, configuration, enqueuer, worker and mandate issuer; contributor/self/service review denied. |
| T-04 | Durable unique occurrences, linked execution attempts, re-dispatch of stale holds, explicit skips, independent mandate holds and one completed run per occurrence. |
| T-05 | Durable periods/history, scoped source assignments, independent open/lock/reopen operations, protected reviews and late-activity quarantine. |
| T-06 | Declared workflow inputs/profile sections and period lookback; transport changes and unrelated workflow inputs no longer invalidate approval. |
| T-07 | Artifact/run links reuse identical governing work; historical versions retained; invalid/duplicate decisions denied; conflicting reviewers yield disputed with explicit independent resolution. |
| T-08 | Documentation corrected, package.manifest named honestly, capability documentation checked, screenshot included in the new review bundle. |

## Test results

- Full `make test`: **72 tests run: 67 passed, 5 expected failures** for explicitly unimplemented Batch 2 probe behavior. No unexpected failure, error or unexpected success.
- All **41 original test methods are retained and pass**, with deliberate period/run-link contract adaptations recorded in DECISIONS.md. The additional 31 tests contain 26 passes and the 5 expected failures.
- Independent runner: **28 PASS, 6 FIXED, 4 KNOWN-FAIL, 22 DEFERRED-OK**. Zero FAIL, UNEXPECTED or DEFERRED-LEAK.
- `make check`: passed Python/JSON/profile/DAG checks, safe DOM construction and documentation capability-ID checks. No external linter/typechecker/JS compiler claim.
- Supplied-path scripts both executed successfully through maintained compatibility entry points. The original script versions are preserved.
- Migration tests cover legacy immutable bytes, foreign-key integrity, restart/idempotence and concurrent initialization. Decision/worker/tick concurrency, client isolation, audit/backup, exact money and outbound socket denial remain covered.

## Six required acceptance cases

| Case | Final result |
| --- | --- |
| FV-C15 | FIXED |
| FV-R01 | FIXED |
| FV-R03 | FIXED |
| FV-R04 | FIXED |
| FV-RC01 | FIXED |
| FV-RC02 | FIXED |

## All 60 Fable cases

PASS/FIXED establish only the specified fictional software outcome. DEFERRED-OK means capability invocation is refused; it is not a passed accounting workflow. KNOWN-FAIL marks a reproducible defect deliberately outside Batch 1.

| Case | Result |
| --- | --- |
| FV-C01 | PASS |
| FV-C02 | PASS |
| FV-C03 | PASS |
| FV-C04 | PASS |
| FV-C05 | PASS |
| FV-C06 | PASS |
| FV-C07 | PASS |
| FV-C08 | PASS |
| FV-C09 | PASS |
| FV-C10 | PASS |
| FV-C11 | PASS |
| FV-C12 | PASS |
| FV-C13 | PASS |
| FV-C14 | PASS |
| FV-C15 | FIXED |
| FV-C16 | PASS |
| FV-C17 | PASS |
| FV-C18 | PASS |
| FV-C19 | PASS |
| FV-J01 | PASS |
| FV-J02 | PASS |
| FV-J03 | PASS |
| FV-J04 | PASS |
| FV-J05 | PASS |
| FV-J06 | PASS |
| FV-J07 | PASS |
| FV-J08 | KNOWN-FAIL |
| FV-J09 | KNOWN-FAIL |
| FV-J10 | KNOWN-FAIL |
| FV-CL01 | PASS |
| FV-CL02 | KNOWN-FAIL |
| FV-R01 | FIXED |
| FV-R02 | PASS |
| FV-R03 | FIXED |
| FV-R04 | FIXED |
| FV-RC01 | FIXED |
| FV-RC02 | FIXED |
| FV-RC03 | PASS |
| FV-AP01 | DEFERRED-OK |
| FV-AP02 | DEFERRED-OK |
| FV-AP03 | DEFERRED-OK |
| FV-AP04 | DEFERRED-OK |
| FV-AP05 | DEFERRED-OK |
| FV-AR01 | DEFERRED-OK |
| FV-AR02 | DEFERRED-OK |
| FV-AR03 | DEFERRED-OK |
| FV-AR04 | DEFERRED-OK |
| FV-BK01 | DEFERRED-OK |
| FV-BK02 | DEFERRED-OK |
| FV-BK03 | DEFERRED-OK |
| FV-BK04 | DEFERRED-OK |
| FV-BK05 | DEFERRED-OK |
| FV-CL03 | DEFERRED-OK |
| FV-CL04 | DEFERRED-OK |
| FV-GL01 | DEFERRED-OK |
| FV-RP01 | DEFERRED-OK |
| FV-RP02 | DEFERRED-OK |
| FV-RP03 | DEFERRED-OK |
| FV-RP04 | DEFERRED-OK |
| FV-RP05 | DEFERRED-OK |

Machine-readable details: `docs/batch1/final-validation.json`. Exact commands/output: `final-tests.txt`, `final-check.txt`, `final-validation.txt`, `final-probes.txt` and `final-delivered-runner.txt`.

## Unresolved defects and boundaries

- FV-J08: duplicate journals remain approval-eligible; stronger journal duplicate controls are Batch 2.
- FV-J09: an entry with no net ledger effect remains approval-eligible; Batch 2.
- FV-J10: unrelated document types can still satisfy journal support; typed/bound support is Batch 2.
- FV-CL02: close readiness still ignores open upstream accounting exceptions; outcome-aware close is Batch 2.
- Probes P07/P08/P12/P13/P15 remain expected failures: source revision ordering, journal substance, close dependencies, statement population identity and configurable receipt policy.
- Independent activation of policy/mandates, evidence freshness, shared proposed entries, exception dispositions, formal entity/book binding, finalized packages, externally anchored audit and atomic export remain unimplemented. These limitations block real-client readiness.
- AP, AR, full reconciliation, financial reporting/analysis, connectors, model calls, posting and final close remain deferred. Batch 1 completion authorizes none of them.

## Intentional original-test contract changes

Durable periods replace profile.period. FV-J05 and teaching-derived V-10 now assert unassigned-period quarantine rather than preparing in the wrong month; FV-J07 locks through the service and verifies dispatch refusal. October TX-008 is retained but not emitted in November. Initial November output therefore has 20 total artifacts and 14 review items (2 eligible, 12 held), rather than 21/15. Opening October routes TX-008 there exactly once. Source evidence is never dropped. Run membership uses artifact.run_ids because identical artifacts can serve multiple executions; run_id retains immutable origin. All changes are recorded in DECISIONS.md.

## Documentation control corrections (F-22)

| Reviewed claim | Corrected behavior/documentation |
| --- | --- |
| Envelope binds entity/book/review policy | Exact implemented scope/period/version/contributor/input/dependency fields listed; missing bindings explicitly deferred. |
| Human-issued mandates | Human kind + preparer role required; independent activation/freshness still deferred. |
| Independent review | Human reviewer outside the immutable contributor set; no actor-name shortcut. |
| Separate validation fixture | Original fixture labeled teaching-derived; independent 60-case suite identified separately. |
| package.check | Renamed package.manifest; no accounting check implied. |
| Missing screenshot | Actual Batch 1 screenshot and lock-preservation proof included in the updated bundle. |

## Browser verification

An isolated synthetic database at data/batch1_browser.sqlite3 was used on loopback port 8766. The actual interface saved independent journal review, opened December without staling November, locked November while preserving the approval, reopened it, and accepted a card receipt while the journal remained approved. The card workflow was re-prepared in its selected period. These are developer checks, not Theresa/Luis UAT or accounting-policy validation.

## Changed files

The complete baseline-manifest comparison is retained in `docs/batch1/changed-files.txt`. Main changes: accounting_agent/core.py, modules.py, service.py, storage.py, demo.py, http.py, web/index.html, web/app.js; the demo profile and teaching-derived validation fixture; original tests plus reviewer/period regressions; Makefile/scripts/check.py; maintained review suite; README, architecture/contracts/verification/handoff, PROGRESS and DECISIONS.
