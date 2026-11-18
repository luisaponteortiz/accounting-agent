Act as a senior accounting systems architect and independent technical reviewer. Review the attached Accounting Agent OS bundle and return prioritized, implementation-ready changes for Codex.

PROJECT SCOPE

We are building a general-purpose, reusable Accounting Agent OS supporting:

1. General Ledger: classification, journals, adjustments and account maintenance.
2. Accounts Payable: vendors, bills, expenses, payments and controls.
3. Accounts Receivable: customers, invoicing, collections, payment application and aging.
4. Banking & Reconciliation: intake, matching, transfers, reconciliations and exceptions.
5. Month-End Close: accruals, reconciliations, adjusting entries, procedures and reviews.
6. Financial Reporting: financial statements, management reports, variance analysis and accounting insights.

Bird Bowl is the first client implementation. Credit-card preparation is only an initial demonstration. Supporting Strategies executive, marketing, sales and other non-accounting agents are outside this project.

These scope instructions take precedence over the broader Supporting Strategies documents included as reference material.

YOUR OBJECTIVE

Determine whether the current foundation can grow into a dependable accounting staff/senior-accountant execution platform serving multiple isolated clients under appropriate human oversight.

Identify architectural changes needed now, concrete defects in the implementation, and the safest sequence for adding accounting capabilities. Give Codex specific changes it can implement and test—not just general recommendations or a replacement concept document.

READ AND INSPECT

Start with:
- FABLE_ACCOUNTING_HANDOFF.md
- Root AGENTS.md
- README.md
- docs/ARCHITECTURE.md
- docs/CAPABILITY_CONTRACTS.md
- DECISIONS.md
- PROGRESS.md
- docs/VERIFICATION.md
- docs/CONNECTION_READINESS.md

Then inspect:
- accounting_agent/core.py
- accounting_agent/service.py
- accounting_agent/storage.py
- accounting_agent/modules.py
- accounting_agent/http.py
- Client configurations, fixtures and tests
- ss_agent_system_handoff/BIRD_BOWL_ACCOUNTING_PILOT.md
- Relevant accounting requirements and acceptance tests in the reference package

Treat documented capabilities and reported test results as claims to assess against the code. Clearly distinguish what you inspected, what you executed, and what remains unverified. If your environment permits, run the existing tests locally without enabling external connections or installing paid services. If you cannot execute them, proceed with static review and state that limitation.

REVIEW PRIORITIES

Evaluate:

A. General accounting architecture
Does the shared workflow, capability, tool, state and evidence model support all six accounting areas without embedding card-specific assumptions in the core? Identify missing foundational entities or contracts that would force expensive redesign later.

B. Shared controls versus client knowledge
Assess separation of reusable controls from each client's accounting framework/basis, chart, dimensions, vendors/customers, policies, procedures, systems, credentials, historical decisions and authority matrix. Review proposed-to-approved policy activation, effective dates, supersession, and transaction-specific versus reusable corrections.

C. Accounting correctness and completeness
Assess source completeness, cutoff, period locks, exact monetary arithmetic, journal balancing, duplicate controls, credits, transfers, splits, accruals/reversals, subledger-to-GL ties, reconciliation evidence and financial-report lineage. Distinguish a mechanically valid result from correct accounting treatment.

D. Durable autonomous execution
Assess dependencies, checkpoints, leases, retries, idempotency, recurring mandates, occurrence deduplication, evidence freshness, expiry/revocation, stale inputs, exception escalation and crash recovery. Routine authorized work should proceed without repeated prompts; unresolved judgments must remain visible.

E. Review and authority
Assess independent review, approval scope, artifact/version binding, invalidation after changes, exception dispositions and separation of preparation, posting, reconciliation and final close. Model proposals must never grant authority or silently activate policy.

F. Client isolation and auditability
Review backend scope enforcement across retrieval, jobs, evidence, decisions and exports; audit integrity; recovery; and future per-client credential boundaries.

G. Incremental implementation
Recommend the next useful capabilities and the minimum controls needed before each. Distinguish an actual defect from an honestly deferred capability.

IMPORTANT BOUNDARIES

- All present transactions, accounts, mappings and demonstration policies are fictional.
- Do not invent Bird Bowl's actual policies, balances, chart, accounting basis, systems readiness or authorized reviewers.
- No live connections, posting, payments, paid model calls, hosting or deployment are authorized.
- Python/SQLite and synthetic local identities are deliberate prototype choices. Identify their limits and migration triggers; recommend an immediate stack rewrite only if a concrete current requirement justifies it.
- Do not treat passing software tests as accounting validation or production readiness.
- Where a recommendation depends on an accounting framework, jurisdiction or client policy, state that dependency. Cite authoritative sources for specific standards claims.
- Continue useful review despite missing client facts. Isolate the decisions requiring human validation.

RETURN THESE DELIVERABLES

1. FABLE_ARCHITECTURE_REVIEW.md

Include:
- Overall assessment and the five most important findings.
- What should be retained.
- A prioritized findings table.
- A six-area capability/control matrix.
- Proposed client-configuration and policy-approval improvements, with illustrative JSON where useful.
- Client questions ordered by what blocks the next implementation or validation step.
- Readiness gates for synthetic testing, approved client samples, read-only integration, separately authorized writes and operating handoff.

For each finding provide:
- Stable finding ID.
- Priority.
- Classification: current defect, architectural gap, client-policy question or future enhancement.
- File/symbol references supporting it.
- A concrete failure scenario and accounting/control consequence.
- The smallest sufficient correction.
- Acceptance criteria and a test that would detect the failure.
- Dependencies and any human decision needed.

Use priorities consistently:
P0: Current critical control or correctness defect.
P1: Foundation change needed before expanding execution or using approved client samples.
P2: Next capability or reliability improvement.
P3: Later enhancement.

Do not automatically classify every deferred feature as P0 or P1.

2. FABLE_IMPLEMENTATION_BACKLOG.json

Return an ordered backlog that Codex can implement. Each ticket should contain:
id, priority, title, finding_ids, rationale, affected_files_or_modules,
required_behavior, acceptance_criteria, tests, dependencies,
human_decision_required, and phase.

Organize the recommendations into three implementation batches. State the objective and completion gate for each batch. Identify which changes Codex can implement now using synthetic data and which must await client facts or authorization.

3. FABLE_VALIDATION_CASES.json

Provide at least 20 new fictional cases across the six accounting areas, emphasizing adversarial cases and boundaries.

Each case should contain:
id, accounting_area, target_workflow_or_capability, test_stage,
input, expected_outcome, expected_blockers, approval_eligibility,
and rationale.

Distinguish cases executable against current modules from specifications for future modules. For deferred modules, clearly separate the current expected “unavailable” behavior from the future accounting outcome. Do not reuse the teaching fixture's answers as independent validation.

DELIVERY STYLE

Be direct, specific and willing to challenge the implementation. Prefer actionable findings over broad praise or generic best practices. Avoid unnecessary complexity and unrelated agents.

Return the three named files if supported; otherwise provide clearly labeled Markdown and valid JSON blocks. Do not stop after an executive summary or merely ask discovery questions. Finish with the exact first implementation batch you recommend Codex undertake.
