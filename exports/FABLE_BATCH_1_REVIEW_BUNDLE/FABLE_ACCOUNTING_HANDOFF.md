# General Accounting Agent OS — architecture handoff for Claude Fable

Prepared November 14, 2026. Revision 2 incorporates the user’s explicit general-platform scope correction. Status: Fable review received; Batch 1 control corrections implemented and undergoing the defined gate. Please return a review packet, not an authorization to connect or post.

## Assignment and boundaries

Act as a senior accounting architect and independent reviewer of a **General Accounting Agent OS** serving multiple isolated clients across the full accounting cycle: general ledger, AP, AR, banking, reconciliations, journal entries, month-end close, financial reporting and accounting analysis. Bird Bowl is the first client implementation; it does not define the platform. Credit-card expense preparation is only the first small demonstration: intake → vendor identification → proposed category → duplicate and document checks → exceptions → independent human review → review-package export. This is local, synthetic software testing. No actual Bird Bowl accounting policies, mappings, financial records, approved reviewers, ledger readiness, or hosting access have been supplied. Do not fill those gaps with plausible business facts.

The current user instruction narrows the broader implementation package to accounting execution. Do not design Executive Director, sales, marketing, CRM, or other business-development agents. Please critique accounting substance and failure modes before recommending more technology.

## Source of known context

Read `ss_agent_system_handoff/BIRD_BOWL_ACCOUNTING_PILOT.md` version 1.4 first. Also see the accounting sections of `BUILD_PLAN.md`, project `AGENTS.md`, and AT-58–61 in `ACCEPTANCE_TESTS.md`. These documents describe intended capabilities; they are not evidence of live operation.

What is actually known:

- Luis selected Bird Bowl as the accounting pilot candidate. This request selects credit-card expense processing for the first **synthetic** demonstration.
- Luis plans to capture November 2026 procedures and validate them on separate December cases. These months have not been represented as processed. December close may await January source availability.
- Theresa's independent daily operation is the intended outcome; her precise preparation/review authority is unconfirmed.
- Jeff may support the client's own hosting. Provider, runtime, persistence, identity, costs, authority, and responsibilities are unknown.
- SS/Luis accounting co-management is proposed, not an established engagement.
- Desktop/QBO migration and current accounting edition are unverified. No bank/card intake provider or posting route is selected.
- Existing client checklists, Claude assets, approved mappings and worked examples must be preserved when supplied. None has been supplied in this workspace.
- A human must validate accounting-policy changes; raw chats, model proposals and one-off corrections cannot silently activate a global rule.

## General accounting platform architecture to review first

The product is an accounting execution platform, not a card-specific agent. Review its ability to grow without rebuilding the core:

- **Core orchestration:** typed workflow definitions composed of versioned capability steps and dependencies; registered tools with explicit read/prepare/review/write permissions; durable runs, jobs, leases, retries, checkpoints, evidence, artifacts, exceptions, approvals, recurring occurrences and audit records.
- **General accounting modules:** GL and journals; AP; AR; banking and card activity; reconciliations; close; reporting; analysis. The capability registry must honestly distinguish executable preparation from deferred functionality. Adding AP or AR should add a module/workflow, not a separate orchestrator or unscoped autonomous agent.
- **Shared accounting controls:** scoped source identity, exact monetary arithmetic, balanced proposed journals, cutoff/currency/account validation, evidence provenance, no guessing, version-bound independent review, idempotency, clear external outcomes and final-close sign-off. Do not claim one accounting framework, materiality level or recognition policy applies to every client.
- **Client knowledge boundary:** legal entity, accounting framework/basis, chart of accounts, periods, dimensions, policies, vendor/customer mappings, procedures, systems, decision register and authority matrix. Unknowns remain null. Approved versions are executable knowledge; proposed rules and historical decisions remain scoped and cannot self-promote.
- **Recurring execution:** human-issued scoped standing mandates authorize specific internal preparation workflows, effective dates and limits. A deduplicated occurrence creates durable work; workers proceed without another prompt, pause affected exceptions, survive restart and recheck revocation/expiry. Synthetic event/time advancement demonstrates scheduling locally; live schedules remain disabled. Human silence grants nothing.
- **Client isolation:** every query, job, evidence snapshot, artifact, approval and recurrence is bound to organization/client/environment. A deployment allowlist can expose only one client. Demo role switching is not hosted authentication.
- **Growth sequence:** prove the common runner using card preparation and at least one non-card module (journal validation / close readiness), then add independently validated AP, AR, ledger, reconciliation, reporting and analysis modules. A catalog entry is not an implemented capability. None of these demonstrations posts entries or completes an actual close.

Please identify missing cross-cycle concepts: accounting periods and locks, subledger-to-GL ties, control accounts, accrual/reversal dependencies, rollforwards, consolidation/intercompany scope, approval hierarchies, evidence retention, source completeness and reporting lineage. Prioritize foundations needed now; keep later functionality explicit.

## First executable slice within that platform

One local accounting application, no running model or external connectors:

1. **Registered accounting modules behind a shared execution engine:** exact decimal amounts; validation; conservative vendor normalization; versioned proposal evaluation; duplicate candidate identification; document checks; period/currency/account checks; blocking exception codes; traceable explanations. These are application controls, not assertions about tax or GAAP treatment.
2. **Client configurations:** separate organization/client/ledger/account identities, period, currency, allowed categories, vendor aliases/mapping proposals and review requirements. Bird Bowl's factual profile remains unconfigured. A separately labeled `bird_bowl_demo` sandbox contains fictional vendor/category rules solely for software demonstration. Synthetic USD/card identities/November dates are test choices, not client facts.
3. **Evidence store:** immutable intake batches, source revisions and structured supporting-document snapshots with hashes and scope. No OCR or verification of receipt authenticity is claimed. Statement row counts and totals are compared to declared synthetic control totals; that does not prove real source completeness.
4. **Durable workflow:** generic database-backed runs and step checkpoints, scoped recurring mandates and occurrence deduplication; bounded attempts; exclusive expiring worker leases; idempotent batch intake and preparation. Missing evidence blocks only affected work. New evidence/rules/source populations invalidate dependent results and approvals. Crash recovery resumes durable work without counting a review as posting.
5. **Review artifacts:** immutable versioned proposals binding exact source, evidence, client/shared rules and duplicate-population fingerprints. Review decisions are separate append-only records. A local synthetic reviewer can approve only an eligible current version; preparer/worker cannot approve. Rejection and revocation retain history. An approval authorizes only inclusion as reviewed preparation in the export.
6. **Local UI/API/export:** visible synthetic labels, exception/review queue, evidence and audit view, human decision reasons and exact-version controls; backend tenant scope enforced independently of the interface. Export includes unresolved items and explicit external status. There is no ledger write route.

Initial implementation choice: Python standard library, SQLite, and static HTML/JavaScript for an immediately executable local slice. The machine lacks Python 3.12, Docker, Node and the proposed Python packages. The package's default FastAPI/Pydantic/SQLAlchemy/Alembic/React/PostgreSQL stack remains a later architecture decision. This first slice does not claim PostgreSQL integration, hosted security, production backups, or full M0–M5 completion. Local demo identity is restricted to loopback and must fail for staging/production. Core accounting rules will be separate from persistence and HTTP transport.

## Cross-cycle synthetic demonstrations and expectations

- **Journal preparation:** fictional balanced USD journal (debit DEMO_OFFICE_SUPPLIES 25.00 / credit DEMO_CARD_LIABILITY 25.00) with supporting evidence → prepared, awaiting independent review, unposted. Change credit to 24.99 → UNBALANCED_JOURNAL, approval blocked. Inactive/unknown account, wrong period/currency, missing evidence or unsupported dimensions → hold. No journal is generated from real Bird Bowl data.
- **Close readiness:** synthetic checklist with reviewed journal preparation but a missing required card statement → incomplete close readiness, never final-close sign-off. Review acceptance is not proof of external posting or reconciliation.
- **Recurring preparation:** simulate two eligible occurrences under a bounded synthetic mandate; repeat an occurrence → one run only; revoke/expire mandate → no new run and no further dependent dispatch. Another client’s records remain inaccessible throughout.
- **Future module seams:** request an AP/AR/reporting capability listed as deferred → explicit unavailable result; no fixture success substituted for an implementation.

## Reusable principles and controls to challenge

- Preserve source IDs, versions, raw descriptions, signs and evidence; normalize only for matching. An alias identifies a candidate vendor, not sufficient proof of accounting purpose.
- Positive amounts mean card charges; negative amounts mean credits in this **fixture contract**. Credits, card payments/transfers, pending items, splits, assets, prepaid items, mixed-purpose purchases and unsupported currency require judgment in the first slice. Do not force all card activity into an expense.
- Same amount/date/vendor is a duplicate candidate, not conclusive proof. Do not delete, merge or select arbitrarily. Exact source replay is idempotent. Revised source data and pending-to-posted linkage retain history and require renewed review. Source removals, upstream revision ordering and external write outcomes are not supported here.
- Use decimal strings with two fractional digits for demo USD. Reject floats, nonfinite numbers and invalid precision rather than silently round.
- Missing/invalid documents, unknown or ambiguous vendors/categories, inconsistent receipt totals/currency/vendor/date, period/account/currency mismatches, and potential duplicates block approval of the affected item.
- Broad-merchant purchases cannot be safely categorized from merchant name alone. No automatic business-purpose, deductibility, sales/use-tax, location, department or capitalization inference.
- Preparation, review acceptance, external posting, external reconciliation and final close are distinct states. A reviewed card proposal is not a completed accounting entry or close.
- A model may propose a treatment; it cannot approve or activate rules. Missing model access leaves ambiguity with a human. No use of Fable access or any subscription as an application connector.
- Reviewer findings and policy corrections must remain separate from producer evidence. A transaction-specific correction does not create a reusable mapping.
- A changed evidence population can create duplicate candidates for already reviewed items; invalidate their reviews rather than merely checking new rows.

## Fictional teaching cases and expected results

All names, amounts, dates, categories, currencies, accounts and document policies below are invented for testing. `DEMO_*` labels are placeholders, not Bird Bowl account names or numbers. The synthetic document policy requires one matching structured receipt for every ordinary charge, with no invented dollar threshold.

| ID | Synthetic input | Expected software result |
| --- | --- | --- |
| TX-001 | November 3; ACME PAPER DEMO; USD 42.50; matching receipt | Alias identifies fictional vendor; propose DEMO_OFFICE_SUPPLIES; awaiting independent review; no posting |
| TX-002 | November 4; METRO REPAIR DEMO; 180.00; no receipt | Vendor/category proposal retained; MISSING_RECEIPT blocks approval |
| TX-003 | November 5; UNKNOWN MARKET DEMO; 65.00; matching receipt | UNKNOWN_VENDOR and UNKNOWN_CATEGORY; no invented category |
| TX-004 / TX-005 | November 6; same fictional vendor, card, currency, amount 90.00; distinct source IDs | Both flagged POSSIBLE_DUPLICATE; neither discarded or approved |
| TX-006 | November 7; credit -42.50 | CREDIT_REQUIRES_REVIEW; no ordinary expense proposal; no sign reversal guessing |
| TX-007 | November 8; 10.00; pending | PENDING_TRANSACTION; excluded from posted population control totals |
| TX-008 | October 31 item in November fixture | UNASSIGNED_ACCOUNTING_PERIOD; retain/quarantine until October is configured |
| TX-009 | November 9; charge 80.00, receipt 79.99 | RECEIPT_AMOUNT_MISMATCH; no tolerance invented |
| TX-010 | November 10; 35.00; requires a split | SPLIT_REQUIRES_REVIEW; no allocation invented |
| TX-011 | November 11; EUR charge in USD fixture | CURRENCY_MISMATCH; no implicit FX conversion |
| TX-012 | November 12; CARD PAYMENT DEMO; 300.00 | NON_EXPENSE_REQUIRES_REVIEW; do not expense a card settlement |

A separate held-out fixture must vary descriptions, dates, repeated charges, document defects and source revisions without reusing the teaching answers. These tests establish software behavior, not validated accounting judgment. Please add independently authored expected outcomes.

## Open questions needing client evidence and human validation

1. What legal entity, books, edition/realm, card accounts, functional currencies and accounting periods are in scope? Is conversion complete? Who owns final review and close?
2. Which source is authoritative for posted transactions, card statements, receipts and ledger history? How are pending items, removals, disputes, reversals and feed/ledger duplicates represented? How is the complete population proved?
3. What is the actual chart of accounts and approved vendor logic? Which purchases require purpose, location, department, project, sales/use-tax or other dimensions?
4. What receipt/document policy, matching tolerance, missing-document resolution, retention and escalation rules apply? Can statements substitute for any evidence? What proof is needed for business purpose?
5. What approved treatment applies to repairs versus assets, prepaid expenses, subscriptions, inventory, employee/personal spend, meals, tips, fees, cash advances, refunds, reward credits, intercompany activity and payments?
6. Who may prepare, revise, resolve duplicates, approve exceptions, approve new mappings and authorize any later ledger write? What independence and authority limits apply to Theresa, Luis and others?
7. How are cutoff, transaction versus posting dates, late receipts, statement cycles, prior-period changes and closed periods handled?
8. What is the single posting route, match-to-existing-ledger behavior, and reconciliation process? Do not equate a public ledger API with native pending bank-feed actions.
9. What evidence is required to accept operating readiness, including Theresa's actual teach-back, unattended bounded execution, review time, avoidable interruptions, restore and technical support?

## High-risk edge cases

Different legitimate purchases with identical amount/date/vendor; merged or changed merchant descriptors; payment processors hiding the real supplier; multi-purpose retailers; the same document attached twice; altered or unrelated receipts; statement-only evidence; foreign exchange and fees; multiple cards or companies with similar account labels; pending authorizations changing amount on settlement; a receipt arriving after review; stale approval after a source correction; late duplicate intake affecting earlier approved work; retry after crash; credits without an original purchase; tax/tip-inclusive totals; partial refunds; multiple receipts or partial deliveries; card payments counted as both bank expense and card expense; imported descriptions that contain instructions or executable HTML; reviewing exports that omit blocked transactions; assuming a matched total proves completeness.

The first slice should conservatively hold these when it cannot establish treatment. Holding an item is not resolving the accounting question. Exception resolution and source removal may require later workflow extensions; please identify the minimal safe next steps.

## Decisions to critique

- Does the common workflow/tool/evidence/state model support the full accounting cycle without embedding card assumptions in the core? What entities and invariants must change now?
- Is the separation between shared controls and client-specific accounting framework, policies, accounts, systems, procedures and decisions sufficient? Propose a minimal safe onboarding/knowledge-approval lifecycle.
- Are standing mandates, bounded recurring occurrences, dependency holds and independent approvals sufficient for useful routine autonomy? Identify risks of stale recurring inputs and cross-period carryforward.

- Is exact alias-based vendor/category proposal safe enough when all mappings are explicitly fictional and every clean item still requires independent human review? What additional evidence should a real reusable rule require?
- Is approval blocking at the item level appropriate? Which source completeness defects should block the entire package or all review decisions?
- Is conservative duplicate flagging sufficient for preparation, with no automated suppression? Specify a reviewer disposition model and evidence needed to distinguish legitimate repeats, source replay and ledger duplicates.
- Is a single-receipt structured evidence contract useful for an initial demonstration? Define how to evolve it safely for splits, multiple receipts and authentic documents.
- What review independence, materiality, exception and rule-activation controls are essential before approved sample data, read-only connection and any write trial respectively?
- What belongs in shared invariants versus client policy? Identify any demo assumption accidentally presented as general accounting doctrine.
- Which accounting tests and expected outputs would most efficiently falsify this architecture?

## Specific deliverables requested from Fable

Please return Markdown plus machine-readable JSON where indicated, with explicit fact/assumption/question labels and source references. Do not include private reasoning transcripts.

1. **Review memo:** prioritized findings with severity, failure example, proposed correction and acceptance test; separate accounting defects from future improvements.
2. **Full-cycle capability/control matrix:** GL, AP, AR, banking, reconciliations, journals, close, reporting and analysis; implementation priority and workflow step, evidence, deterministic/model/human execution, shared invariant versus client policy, preparer/reviewer roles, blocking conditions and permitted resolution.
3. **Client discovery checklist:** questions ordered by what blocks the first approved-sample preparation workflow. Identify the minimum source packet Luis must provide.
4. **Proposed rule schema:** JSON examples for versioned, effective-dated vendor/category proposals, evidence requirements, decision scope (single item versus reusable rule), approver and supersession. Label these proposals; do not mark them approved.
5. **Independent full-cycle validation set:** at least 20 fictional cases across card activity, journals, reconciliation, AP/AR, close and reporting lineage with input JSON, expected accounting outcome or explicit deferred status, exception codes, approval eligibility and short rationale. Distinguish implemented-module tests from future-module specifications. Include duplicate, cutoff, payment, credit, document and source-revision cases. Keep this separate from the teaching fixture.
6. **Readiness gates:** criteria for synthetic acceptance, client-approved samples, read-only connection, controlled write capability and operating handoff; no automatic expansion from one gate to another.
7. **Modular roadmap and incorporation patch list:** exact changes recommended for engine, configuration, UI, audit and tests. Identify unresolved choices that must remain pending for Luis/client validation.

Send this file and, when available, `README.md`, `DECISIONS.md`, `accounting_agent/config/`, `accounting_agent/core.py`, `accounting_agent/modules.py`, `accounting_agent/service.py`, and the tests for code-specific review. Fable's response will be incorporated through explicit code/config revisions and tests; it will not activate accounting policies by itself.


## Implementation snapshot for the reviewer

The executable first slice now includes the common workflow/tool runner; SQLite source/artifact/decision/audit storage; scoped profile registration; manual and simulated recurring job creation; expiring worker leases, step checkpoints and bounded retries; current-version review; a browser work queue; and full JSON evidence export. Card preparation, proposed-journal validation and close document-readiness are executable. See `README.md`, `docs/CAPABILITY_CONTRACTS.md` and `PROGRESS.md` for actual tests and limitations.

All six areas have module contracts and catalog coverage. AP, AR, full banking/reconciliation, GL maintenance/posting, accrual/adjusting workflows, reporting and analysis remain deferred. No live/model adapter exists. Real client policy approval, effective-dated historical decision activation, full knowledge-package execution import, source removals, duplicate dispositions and split resolution remain future work. The independent role is a synthetic local test identity, not a verified human account. Fable should critique the general foundation and these extension boundaries as well as the three executable examples.


## Batch 1 implementation response

The independent review is preserved in review/FABLE_ARCHITECTURE_REVIEW.md. Batch 1 adds Unicode-safe vendor matching, explicit actor kind and hashed contributors, durable occurrences/re-dispatch/skips, accounting periods/locks/late-evidence holds, declared-input lineage and governing-artifact/decision controls. See docs/BATCH_1_REPORT.md and PROGRESS.md for executed results.

Mandates may be issued only by a human actor with the synthetic preparer role; independent approval, freshness and real standing authority are not implemented. Profiles still activate through demo registration. Envelopes now bind scope/period/version/contributor/input/dependency metadata, but entity/book, shared proposed entries and formal independently approved review policy remain Batch 2. package.manifest describes provenance and does not validate accounting readiness. The original ten-case regression fixture is derived from teaching data; the 60 Fable cases form the independent suite. No client facts or actual accounting readiness are established.
