# Accounting Agent OS

A reusable accounting execution foundation for isolated clients, with shared execution, evidence, policy and approval controls. Bird Bowl is the first client implementation. The six accounting areas remain the product architecture; this release demonstrates card preparation, journal validation and close readiness on fictional data.

The authoritative [product requirements register](docs/PRODUCT_REQUIREMENTS.md) preserves the universal multi-client vision, current capability status and future requirements. Consult it alongside the existing Fable backlog and current corrective gates before implementation; it does not authorize new features, live actions or Batch 3.

**Current state (17 November 2026).** The independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 with no corrective ticket, and that review is registered: the register has seven Independently verified records and none Verification failed. Read the [current handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md), the [registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and the [G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md). **The accounting owner accepted human G0 on 17 November 2026 (D-036)** and re-affirmed it the same day for the feed-contract source changes of D-038 (D-039): a statement that the software controls behave as specified on fictional data, not a claim about accounting correctness, any client or readiness. It does not start G1. The register has 88 retained records; proposed shared additions are documentation, not implemented features.

The correction handoffs, review prompts and reports for the RA to RF passes remain in the repository as dated records of each checkpoint. [DECISIONS.md](DECISIONS.md) and [PROGRESS.md](PROGRESS.md) hold the full history; all delivered archives and reviewer inputs are immutable.

## Run locally

Requires Python 3.9+ and SQLite; tested on Python 3.9.6. No dependencies, API keys, paid services or hosting required.

```sh
make demo
```

Open http://127.0.0.1:8765. A background worker continues queued work. Ctrl+C stops it; SQLite retains progress. This command seeds only the fictional demo, independently approves its test profile/grants, and starts three workflows. It does not activate real policy. Back up existing synthetic databases before migration. Historical records remain immutable.

For an isolated scratch database:

```sh
python3 -m accounting_agent demo --db /private/tmp/accounting-os-synthetic.sqlite3
```

Other commands:

```sh
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
make rb-gate
make rc-gate
make rd-gate
make re-gate
make rf-gate
python3 scripts/synthetic_month.py
python3 scripts/verify_corrective_checkpoint.py
python3 -m accounting_agent inspect
make export-demo
make backup
```

Tests use temporary databases and loopback servers; the local environment may require loopback permission. The suite has 274 test methods; the latest complete results for the suite and all gates are in docs/registration_rf/commands/. The rb to rf gates run the independent reviewers' unmodified probes and delivery-order searches; rf-gate takes about 50 minutes. The 60-case gate reports 29 PASS, 10 FIXED and 21 DEFERRED-OK. check performs offline syntax/JSON/profile/registry checks; it is not an external linter or JavaScript build. Backup refuses to overwrite an existing destination. CLI --db/--output select alternative synthetic paths.

## Implemented and unconnected

| Component | Running behavior | Still unconnected or deferred |
| --- | --- | --- |
| Common engine | Durable DAG jobs, leases/checkpoints/recovery, scoped periods, source lifecycle, manifests, evidence and audit | Production queue, worker backoff/heartbeat and hosted persistence |
| Client knowledge | Independently approved effective profiles/rules, explicit grants, fact requirements and synthetic waivers | Actual Bird Bowl facts/policies/authority, real identity and credentials |
| Card preparation | Vendor/category proposals, duplicates, document policies, statement checks, dispositions and derived entries | Real feeds/OCR, full reconciliation, FX and posting |
| GL preparation | Shared entry validator, support binding, duplicate/no-effect/origin collision controls | Ledger balances, accrual creation, recognition policy and posting |
| Close readiness | Typed outcome/evidence checks, quarantined/unreviewed work and immutable preparation handover | External reconciliations, AP/AR ties and actual close sign-off |
| Card-feed contract (D-026) | Provider order, replacement claims on late, older or conflicting messages, contested-target holds, and a recorded target selection under disposition and lock authority, for fictional card rows and their receipts | Journals, confirmation against a real provider (G2), and a web control for target selection |
| Recurrence | Independently approved bounded mandates with period/freshness predicates and simulated events | Live schedules and external event delivery |
| Other accounting areas | Six-area contracts and refused deferred tools | AP, AR, full banking/reconciliation, reporting and analysis execution |

All approvals concern preparation. No connector, model call, ledger write, payment, production deployment or paid hosting is enabled. The local role selector and fixture grants are artificial identities, not authentication or participation by real people.

## Demonstrate the controls

1. Inspect 11 November card items, two journals and the close checklist. October's transaction is quarantined pending its period. Structured statement checks also produce a workpaper. The original intentionally defective items remain blocked.
2. Switch to Demo independent reviewer, inspect a clean item, enter a reason and approve. Source/preparation/rule/disposition contributors cannot review their own work; all historical versions of the item's evidence count.
3. Supply the fictional missing receipt as preparer and re-prepare cards. Journal review stays current. Revising existing supporting evidence produces an explicit hold and version history; a granted non-supplier must accept the revision before separate final review. Policy changes require proposed/approved records through the Python service. Withdrawn mappings retire on their approved effective date.
4. Reviewers can record a supported item disposition, then re-prepare. A different independent human must review that item; the two-role UI cannot impersonate additional reviewers. scripts/synthetic_month.py demonstrates the full multi-person service sequence, including distinct purchases, a split, credit and settlement.
5. Finalize a preparation package with an explicit acknowledgement of any carried item exceptions. Stale/disputed work and package controls refuse. A new package names its predecessor; the UI distinguishes governing and historical versions. Removed items remain in the audit and package removal history. Locked periods refuse all decisions; unsettled work requires a recorded lock acknowledgement. Reopening is audited.
6. Propose a fictional mandate with the UI's explicit occurrence-start freshness requirement, switch to reviewer to approve it, then deliver simulated events as preparer. A repeated event reuses its occurrence; freshness and policy changes can hold future work. Empty freshness is refused. A no-evidence mandate requires a stated reason and independent approval through the service; live schedules remain disabled.
7. Export scoped evidence, rule/grant/decision histories, exceptions, immutable packages and audit. Full live export's transaction-consistency hardening remains T-25; finalized package bytes remain fixed.

See [architecture](docs/ARCHITECTURE.md), [capability contracts](docs/CAPABILITY_CONTRACTS.md), the [RF registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and the [current handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md). The original ss_agent_system_handoff/ package is preserved as reference; executive/marketing/sales work remains outside scope.

**History of the RA pass, kept as written at that checkpoint.** Fable accepted 14 of 17 RV corrections and all seven earlier probe adaptations, including strengthened RT14b, then identified RA-01–RA-08. This pass addresses those findings. All original inputs and the submitted archive remain unchanged. The current gates run 27 compatible older probes and 20 compatible acceptance probes directly from their supplied files, with all 35/24 controls exercised through explicit current setup. RA-04 requires independent acceptance after statement changes; four new positive setups and older RT18 now supply that decision after asserting the hold/history. Their original verdicts remain intact. Full original-script setup failures remain disclosed; read [the new adapter explanation](docs/acceptance_ra/probe-adaptations.md). Independent acceptance of these additions and G0 remain pending. No real operating readiness or Batch 3 authority is claimed. (Since then the RA to RF reviews have returned; see the current state above.)
