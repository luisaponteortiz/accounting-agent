# Accounting Agent OS

A runnable **general accounting execution foundation** for isolated clients. Bird Bowl is the first client implementation. The product covers six capability areas by design; this release implements three small, synthetic preparation workflows. It does not implement the entire accounting cycle.

Start with [FABLE_ACCOUNTING_HANDOFF.md](FABLE_ACCOUNTING_HANDOFF.md), [architecture](docs/ARCHITECTURE.md), and [capability contracts](docs/CAPABILITY_CONTRACTS.md). The supplied `ss_agent_system_handoff/` package is preserved as reference. The user's general Accounting Agent OS scope takes precedence over its broader business-agent roadmap.

## Run locally

Requires Python 3.9+ with SQLite (tested on Python 3.9.6 / SQLite version recorded in PROGRESS.md). No pip, Node, Docker, API keys, model subscription or hosting account required. Use a local terminal from this project directory:

```sh
make demo
```

Open **http://127.0.0.1:8765**. The first start creates `data/accounting_demo.sqlite3`, registers a fictional client profile, imports synthetic evidence idempotently, queues the three workflows and starts a background worker. Ctrl+C stops the server/worker. State survives restart. Restarting does not duplicate the same input preparation. Code or evidence changes require a new preparation version.

These commands also run independently:

```sh
make setup
python3 -m accounting_agent drain
python3 -m accounting_agent inspect
make test
make check
make verify-no-egress
make export-demo
make backup
```

Tests create temporary databases and temporary loopback HTTP servers. A managed sandbox may require permission to bind a local port. `make core-test` runs without an HTTP listener. `make check` performs Python syntax, JSON/profile and workflow/registration checks; external lint/type/JS build tools are not installed. Browser acceptance is documented separately, not disguised as an automated Playwright suite.

Export: `exports/synthetic-review-package.json`. Backup: `exports/local-synthetic-backup.sqlite3` (new destination required; a repeat refuses to overwrite it). Use `--db` and `--output` on the CLI for alternate **synthetic** files. Copy a backup to a new database path and inspect it with `python3 -m accounting_agent inspect --db /absolute/path/to/restored.sqlite3`; never overwrite a running database.

## What executes

| Component | Running behavior | Verification | Still unconnected / incomplete |
| --- | --- | --- | --- |
| Shared platform | Workflow DAGs, registered prepare-only tools, durable jobs/checkpoints, expiring exclusive leases, three-attempt retry limit | Restart, lost lease, concurrency, malformed input/output boundary, duplicate intake/event tests | PostgreSQL, hosted identity, production queue, richer cancellation/backoff |
| Client knowledge/isolation | Versioned fictional profiles and scoped sources, runs, artifacts, decisions and mandates; second-client onboarding through Python service | Cross-client/company denial and same-engine second-client tests | Actual Bird Bowl chart/policies/reviewer; client onboarding UI; approved historical-knowledge activation |
| Card preparation | 12 fictional transactions; vendor aliases, proposed category, duplicates, receipt and statement-control checks | Teaching expectations plus separate regression cases | Bank/card feeds, real receipt parsing/OCR, full source lifecycle, splits/duplicate resolution and posting |
| GL/journal preparation | Balanced/unbalanced proposed journals; account/period/currency/evidence checks | Exact cents, wrong account/period/currency, invalid lines and missing support tests | Journal creation from business facts, recognition policy, ledger maintenance and posting |
| Close readiness | Missing-evidence checklist and explicit external/sign-off holds | Missing card statement remains blocked; no completed-close claim | Actual reconciliations, subledger ties, accruals, period locks in a ledger, final close |
| Review/audit | Exact-version independent human demo decisions; append-only evidence/artifacts/decisions, audit hash chain; full JSON export | Role/hash/staleness/revocation/export/backup tests; working browser approval | Real human identities, real authority matrix, WORM/external audit retention |
| Recurring execution | Scoped synthetic mandates, interval occurrences, caps, deduplication, persisted simulated clock; worker proceeds unattended after event | Duplicate occurrences, expiry/revocation and independent-work continuation tests | Real schedules/event delivery, evidence freshness policy and production authority |
| Other capability areas | Six-area capability catalog and module contracts | Deferred capability requests fail closed | AP, AR, full banking/reconciliation, reporting and analysis execution |

No live adapter, model invocation, ledger write, payment, paid hosting or external communication is enabled. All outputs are preparation; approvals do not authorize posting, reconciliation or final close. Optional model integration is **deferred**, not an implemented connector stub. Real account data is not approved for this prototype.

## Try the workflow

1. In **Work & review**, inspect the three completed preparation runs, 15 preparation items, two clean items and 13 exceptions. Other work completes even when one item needs evidence.
2. Filter **Eligible for review**, select a journal/card item, switch to **Demo independent reviewer**, inspect evidence, enter a reason and approve. Preparer/worker approval attempts fail in backend code.
3. Inspect J-002 (one-cent imbalance), the repeated 90.00 charges, unknown vendor, missing receipt, payment, credit, pending transaction and missing close evidence. Approval is blocked on affected items.
4. Return to **Demo preparer** and supply the fictional missing receipt. Prior results become stale. Prepare the workflows again; TX-002 can now reach review, while unrelated accounting exceptions remain open. No prior approval carries forward.
5. In **Recurring work**, issue the fictional journal-preparation mandate. Deliver the November 15 simulated event, then repeat it: one occurrence/run. Advance to November 16 for a second occurrence. The worker handles queued steps without another prompt. Revoke the mandate to stop further dependent work. The simulated clock only moves forward; live schedules stay disabled.
6. Inspect **Accounting capabilities**, **Client knowledge**, **Evidence & audit**, and export the complete review package including blocked work and source history.

The identity selector deliberately switches artificial local roles. It is a demonstration harness, not authentication or actual participation by Luis or Theresa. The service refuses staging/production, connected mode and non-loopback HTTP binding.

## Extend safely

Add a pure accounting handler and `Capability` in `accounting_agent/modules.py`; validate its input source type; compose versioned `Step`/`Workflow` contracts; add client-specific approved-demo configuration; write adversarial outcome tests; only then change the capability status. All modules use the same service, state, evidence and review boundary. No tool exposes arbitrary SQL, shell, HTTP, self-granted permissions or external writes.

Shared controls are in `core.py`; client rules are in `config/`. The real Bird Bowl template is `bird_bowl.unconfigured.json`; `bird_bowl.demo.json` contains fictional test choices. Proposed Fable rules must be reviewed and tested before incorporation; they cannot become actual client accounting policy through this demo.
