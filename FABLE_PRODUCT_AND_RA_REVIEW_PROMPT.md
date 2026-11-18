Act as an independent senior accounting architect, accounting-controls reviewer and technical verifier for Accounting Agent OS.

Perform two separate reviews:
1. Independently verify the RA-01–RA-08 correction response and retained accounting controls.
2. Review the new permanent product requirements register for completeness, consistency and accurate implementation status.

Treat Codex’s reports and passing labels as claims requiring evidence. Do not implement fixes during this review.

PRODUCT SCOPE

Accounting Agent OS is a universal, reusable accounting execution platform covering:
- General Ledger
- Accounts Payable
- Accounts Receivable
- Banking & Reconciliation
- Month-End Close
- Financial Reporting & Analysis

Bird Bowl is the first client implementation, not the product boundary. Shared accounting controls and execution capabilities belong in the reusable core. Client-specific policies, frameworks, charts, systems, procedures, records, credentials and decisions belong in isolated client configurations.

The present application implements only bounded fictional preparation capabilities. Do not infer that full-cycle accounting, hosted autonomy, integrations or production readiness have been delivered.

MATERIALS AND PRESERVATION

The ZIP is the unchanged RA correction review checkpoint. The separately attached PRODUCT_REQUIREMENTS.md, AGENTS.md, DECISIONS.md and PROGRESS.md are a subsequent documentation addendum.

Keep the archive and its manifest assessment separate from that addendum. Do not treat the new documents as files originally packaged in the ZIP or modify the archive to make its manifest match them.

Preserve all original independent review inputs, scripts and historical archives. Write new probes and results to separate files. Use disposable synthetic databases only.

PART 1 — CORRECTIVE VERIFICATION

Follow FABLE_RA_REVIEW_PROMPT.md and FABLE_RA_CORRECTIONS_HANDOFF.md inside the bundle, including their detailed acceptance assertions and adversarial scenarios.

Verify corrections in the prescribed order:
RA-01, RA-03, RA-04, RA-02, RA-06, RA-05, RA-07, RA-08.

Also verify retained C-01–C-06, RV-01–RV-17 and Batch 2 controls, the seven previously accepted probe adaptations, and strengthened RT14b.

From the extracted project root, run:

make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .

Independently verify the reported 154 passing tests and the 60-case results:
29 PASS / 10 FIXED / 21 DEFERRED-OK.

The literal full original acceptance script is disclosed as still nonzero because four positive setups revise statements without the acceptance now required by RA-04. Independently judge the separate setup adaptations for A03, A05, A17, X09 and older RT18. Verify that they preserve the original accounting assertions, first prove the required holds/disclosure, and obtain legitimate non-supplier acceptance without manufacturing eligibility or adding authority.

Do not relabel the unmodified full command as passing. Only U4 is permitted to remain NOTE in the maintained RA gate.

Record your own commands, versions, stdout/stderr and exit codes. Mark anything you cannot execute NOT_RUN rather than accepting delivered logs as your own verification.

PART 2 — PRODUCT REQUIREMENTS REGISTER

Review all 76 requirement records and their crosswalk against the original specifications, implementation backlog, decisions, current source and Fable reviews.

Check that the register preserves:
- Morning Briefing: overnight completion, needs attention, waiting on others, continuing automatically, today’s priorities and estimated human review time; management-wide and client views with appropriate permissions.
- Hosted scheduled/event-driven execution without the user’s computer, with durable progress, retries, monitoring, exceptions and bounded standing authority.
- One reusable codebase, centralized Supporting Strategies deployment with isolated clients, and optional independent client deployment.
- Accounting knowledge, applicable frameworks, verified standards references, approved client policies, effective dates, charts, procedures, treatments, historical decisions and evidence.
- All six accounting functions.
- QBO, Bill.com, Google Workspace/Gmail, Google Drive, bank transactions/statements and permitted authorized bank-portal integrations.
- Independent review, segregation of duties, traceability, document completeness, approval controls, period locks, duplicate prevention, correction history, reconciliation validation and credential security.
- Bird Bowl’s planned November–December knowledge capture, independent validation, Theresa’s operating workflow, and relevant sales, deposit, payroll/tip and closing processes.
- Completion, accuracy, exceptions, interruptions, human effort, review-time estimates and model/infrastructure costs.
- Future missing-document requests, collection follow-ups and separately controlled drafting/sending permissions.

For every record, assess its stable ID, description, business purpose, priority, dependencies, status, acceptance criteria and target stage.

Identify:
- Missing or contradictory requirements.
- Bird Bowl assumptions improperly embedded in the shared core.
- Unsupported implemented/tested claims.
- Vague or untestable acceptance criteria.
- Incorrect dependencies or backlog mappings.
- Requirements silently lost, duplicated or inserted into an unauthorized batch.
- Client facts or policy choices that require human validation.
- Whether AGENTS.md provides sufficient ongoing maintenance instructions.

Do not classify an intentionally deferred capability as a current implementation defect merely because it is not built. Distinguish product approval from implementation authority, client-policy approval and operating readiness.

RETURN DELIVERABLES

Return the RA verification files specified in FABLE_RA_REVIEW_PROMPT.md.

Additionally return:
1. FABLE_PRODUCT_REQUIREMENTS_REVIEW.md — completeness assessment, universal-platform assessment, status accuracy, unresolved conflicts and recommended changes.
2. FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json — prioritized actionable findings, each with a stable finding ID, affected requirement IDs, evidence, proposed correction, dependencies and exact acceptance criteria.

Separate confirmed code defects, documentation defects, future enhancements and decisions requiring client/product authority. Give separate verdicts for RA acceptance, requirements-register acceptance and G0 technical criteria.

BOUNDARIES

No live connections, paid services/model calls, posting, payments, sending, deployment or production changes. Do not begin Batch 3, redesign the project concept or rewrite the technology stack without demonstrated necessity.

Independent technical acceptance does not itself grant human G0 acceptance, G1–G4 authority, Batch 3 authorization or permission to operate on client books.
