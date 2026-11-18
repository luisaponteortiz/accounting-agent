# General Accounting Agent OS

The platform executes bounded accounting workflows for isolated clients across the full accounting cycle. Bird Bowl is the first implementation. Card expense preparation is one module, not the product boundary. Executive, marketing, sales and CRM agents are outside this build.

## Layers

1. **Execution core:** workflow DAGs, registered capability handlers, scoped tool permissions, durable jobs, leases and bounded retries, checkpoints, mandates, occurrence deduplication, immutable evidence/artifacts, exceptions, independent human decisions and audit.
2. **Accounting capabilities:** GL/journal preparation, AP, AR, banking, reconciliation, close, reporting, analysis. Every capability declares its version, execution kind, review boundary and honest implementation status. Unsupported operations fail closed. Modules share the runner, not each other's policy assumptions.
3. **Client knowledge:** versioned profiles containing accounting basis/framework, chart, accounts, periods, mappings, procedures, system identities, authority and historical decisions. Approved demo profiles contain only fictional rules; Bird Bowl's real profile is unconfigured. No raw chat or model suggestion activates a policy.
4. **Adapters:** fixture intake now; actual system reads, writes and optional model proposals later. Application code controls adapters. No live connector or paid calls exist in this release.
5. **Interface:** accounting work queue, evidence, exceptions, exact-version review and exports; administration exposes capability and audit status.

## State and authority

All persistent entities bind organization + client + environment. The runtime is local/demo only and enforces an allowed-client list. Every profile and evidence version is immutable. Any input/profile revision invalidates preparation approvals within that client through a generation fingerprint. This deliberately conservative first slice may require re-review of unaffected work; finer dependency graphs are future optimization.

Workflow steps create immutable artifacts through the runner. A failed step is retried at most three times under an exclusive expiring lease. Commit requires the same lease token and unchanged input fingerprint. Completed steps are checkpoints; recovery never reruns their committed work. A changed input generation holds an old run and requires a new run. Job completion means preparation, not reviewed, posted, reconciled or closed.

A human demo reviewer can append approve/reject/revoke decisions for a current eligible artifact. Preparers and workers cannot approve. Decisions bind artifact hash, input generation, rule/workflow versions and client scope. Rejections/revocations do not erase prior records. No approval grants external authority.

A standing mandate permits specific internal workflows for one client, interval, active period and occurrence cap. Local synthetic time events create deduplicated runs. The background worker completes eligible queued preparation without another prompt. Mandates are rechecked before dispatch and commit; expiry/revocation holds affected jobs. Real schedules are disabled. No always-running model loop exists.

## Incremental capability plan

| Area | First slice | Future validation |
| --- | --- | --- |
| GL / journals | Proposed journal validation: exact balancing, account/currency/period/evidence checks | Ledger reads, accruals, reversals, dimensions, locks, approved posting and reconciliation |
| Banking / cards | Card intake, aliases, proposed categories, duplicates, structured document checks | Complete bank coverage, pending/removal lifecycle, settlement/FX, verified ledger matching |
| Close | Checklist readiness and explicit missing prerequisites | Subledger ties, reconciliations, period locks, final human sign-off |
| AP | Deferred contract/catalog entry | Bills, vendor controls, matching, aging, approvals; payments separately reserved |
| AR | Deferred contract/catalog entry | Billing, cash application, aging, customer controls |
| Reconciliation | Deferred contract/catalog entry | Complete populations, one-to-one match allocation, timing/unknown outcomes |
| Financial reporting | Deferred contract/catalog entry | Trial-balance lineage, report definitions, basis, comparative ties |
| Accounting analysis | Deferred contract/catalog entry | Reproducible metrics, client context, reasoned reviewable interpretation |

No catalog entry alone establishes functioning accounting coverage. Proposed journal checks do not establish correct recognition or tax treatment. Close readiness is not close completion.

## Local technical choice

Python standard library + SQLite + static browser UI provide an executable slice on the supplied Python 3.9.6 machine. Node, Docker, Python 3.12 and recommended packages are unavailable. This is a documented deviation from the package default; PostgreSQL, FastAPI, migrations tooling and authenticated hosting remain unimplemented. Domain handlers do not depend on HTTP or SQLite. A later repository adapter must reproduce transaction/lease/isolation invariants under PostgreSQL integration tests before promotion. The HTTP server and local demo identities must never be deployed.

SQLite transactions and compare-and-set leases protect local concurrent workers. Artifact hashes aid inspection but are not a tamper-proof/WORM guarantee against a database administrator. Backups are local copies; hosted retention, encryption, restore drills and external audit retention require design/authorization.
