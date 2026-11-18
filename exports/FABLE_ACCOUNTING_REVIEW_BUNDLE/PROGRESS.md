# Accounting Agent OS progress

Release: **0.1.0**, November 14, 2026 (client date). Environment/mode: **local / demo**. All accounting inputs, accounts, vendors, policies, identities and outputs are fictional. Original implementation reference package is unchanged. User's general-platform scope is authoritative.

## Completed and demonstrated

| Component | Actual result | Evidence | Capability state |
| --- | --- | --- | --- |
| Full-cycle foundation | Shared capability registry, workflow DAGs, scoped tools/state/evidence/decisions; six-area contracts | `core.py`, `service.py`, `storage.py`, `modules.py`, `docs/CAPABILITY_CONTRACTS.md` | fixture-demonstrated within local preparation scope |
| Client profiles | Real Bird Bowl template remains unconfigured; separate fictional sandbox; second client runs same core without cross-client reads/reviews | Profile validation/onboarding and cross-client/company tests | fixture-demonstrated; actual client implementation unconnected |
| Durable execution | Exclusive 30-second leases, atomic step artifacts/checkpoints, three-attempt retries, restart/concurrent-worker recovery, stale-result rejection | Lost-lease/crash, concurrency, malformed-output rollback, retry/stale-input and dependency-lineage tests | fixture-demonstrated |
| Card preparation | 12 transactions with aliases/category proposals, duplicate candidates, document/statement controls and exceptions | Teaching outcomes; separate validation fixture; late-evidence browser flow | fixture-demonstrated |
| Journal validation | Two proposed journals: balanced 25.00/25.00 eligible for review; 25.00/24.99 blocked | Balance/line/account/period/currency/support tests and browser approval | fixture-demonstrated mechanical checks only |
| Close readiness | Missing required evidence visible; external verification/final sign-off remain held | Checklist tests and running UI | fixture-demonstrated limited checklist only |
| Review/audit/export | Independent artificial human role, exact artifact/input hashes, stale-approval invalidation, append-only history, audit hash chain and complete JSON package | API/browser review, revocation, source-change/export-race, backup/restore tests | fixture-demonstrated; no real authority verified |
| Recurring work | Human-issued synthetic bounded mandates, persisted simulated clock, occurrence deduplication/caps, unattended worker, expiry/revocation holds | Recurrence tests and duplicate-event browser walkthrough | fixture-demonstrated simulation; live schedules disabled |
| Fable collaboration | Early handoff revised to full Accounting Agent OS architecture, controls, client separation, questions, samples and requested reviewer deliverables | `FABLE_ACCOUNTING_HANDOFF.md`, `FABLE_REVIEW_PROMPT.md` and review bundle | delivered; Fable review pending |

## Executed verification

- `python3 -m unittest discover -s tests -v`: **41 tests passed**, 8.312 seconds on final code. Includes 8 black-box HTTP tests against a real temporary loopback server/worker and a separate 10-case regression fixture exercised as subtests.
- `python3 scripts/check.py`: **passed** Python syntax, JSON parsing/profile validation, workflow DAG/registration and safe DOM construction checks. No claim of external lint, typechecker or JavaScript compiler execution.
- Outbound calls denied in-process during workflow/review/export: **passed** within the test suite. This is an application-level socket denial harness, not an OS firewall certification.
- Local backup/restore preserves artifacts, scoped evidence, decisions and audit integrity: **passed** within the test suite.
- Runtime tested: Python **3.9.6**, SQLite **3.51.0**. No third-party runtime dependencies installed. Material default-stack deviation recorded in DECISIONS.md.
- Initial sandbox could not bind local sockets. Loopback-only execution/test permission was accepted; actual HTTP/browser tests then ran. No live account connection or cloud deployment was involved.

## Browser acceptance observed by the developer agent

Actual local app at `http://127.0.0.1:8765`, not a static mockup:

1. Three workflows completed their step checkpoints; initial latest package showed 15 preparation items, 2 eligible and 13 exceptions.
2. Independent synthetic reviewer approved a balanced journal; later approved a clean card proposal. The UI saved the decisions and retained “not posted / not reconciled / not closed.”
3. Supplying TX-002's fictional receipt made all prior preparation approvals stale. New runs retained old history and produced 3 eligible items and 12 exceptions.
4. Re-prepared TX-002 displayed its category, supporting evidence and pending independent review; no missing-receipt finding remained.
5. Issued one synthetic journal mandate and delivered the same simulated event twice. One recurring run (run 10 in the retained developer demo database) completed three checkpoints without another prompt. Automated tests verify the unique occurrence and caps.
6. Reloaded the final release after dependency-lineage changes: runs 11–13 completed; replaying the supplied receipt correctly reported no input/approval changes.
7. Verified the six-area capability view distinguishes partial implementation from deferred areas. Captured `docs/accounting-agent-os-demo.jpg` and retained the app tab.

These are developer synthetic checks. Luis/Fable accounting acceptance, Theresa's own independent operation, actual unattended client execution, real-model evaluation, connector validation, hosted UAT and production readiness are **not run**.

## Package acceptance mapping

- **AT-58:** accounting-only boundary and cross-client denial tested locally; live hosting/credential/account permissions unverified.
- **AT-59:** zero-model deterministic preparation, missing-model-review hold and no external effects tested; optional model/ledger adapters deferred.
- **AT-60:** immutable version/provenance and inspection export demonstrated; full approved knowledge-package execution import, historical decision scope/effective-date activation and actual November/December validation deferred.
- **AT-61:** synthetic recurrence/restart/exception mechanics demonstrated; human baseline, Theresa teach-back, independent use, effort measurements and operational release remain pending.

No complete M0–M5 claim is made for the broader reference roadmap.

## Remaining work / next implementation

Incorporate Fable's prioritized findings with tests. Obtain client-authorized procedures and reviewed sample results before activating actual accounting knowledge. Add explicit exception dispositions (duplicate resolution, splits, recognition questions), source-lifecycle handling and accounting-knowledge approval history. Then implement one AP/AR/reconciliation/reporting capability at a time behind the same contracts. AP, AR, actual reconciliation, GL maintenance/posting, accrual/adjusting workflows, financial statements/management reports/analysis and final close remain **deferred**.

Real connectors/models, secrets/identity, hosted persistence/migrations, production retention/backups, live schedules and ledger writes remain unconnected. `docs/CONNECTION_READINESS.md` tracks the required later gates. No paid hosting, model calls, live records or accounting entries were used.
