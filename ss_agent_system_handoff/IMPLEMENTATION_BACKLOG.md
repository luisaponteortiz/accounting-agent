# Implementation backlog

Version 1.4 — November 14, 2026

**Authority:** `BUILD_PLAN.md` is the authoritative product and implementation specification. Use this backlog to execute it in reviewable increments. Resolve any conflict in favor of the build plan and record the resolution in `DECISIONS.md`.

**Current boundary:** implement and validate M0–M5 locally with synthetic data. Produce reviewable code and deployment configuration. Connections, paid model usage, hosting activation, live records, and schedules begin only after the consolidated connection decision. Outbound communications remain human-sent throughout this roadmap.

**Company-first direction:** establish the initiative within the appropriate Supporting Strategies office/company arrangement with Danielle, using Luis, Sarai and Michael as the first pilot group. The actual legal entity, franchise authority and authorized company owners remain to be verified. Company control begins with the approved repository, accounts, access and operating records; it does not require immediate company-wide use. Synthetic local construction can proceed before those accounts are connected. This plan does not create accounts, transfer ownership, or transfer Luis's separate North Star framework.

`TESTING_AND_ROLLOUT.md` defines the local-test, company-staging, limited-production-pilot and wider-rollout gates. Staging is a deployment for testing; local testing precedes any deployment. Do not describe staging as already proven production use.

**Executive and autonomy direction:** promote the existing strategy lead to **Executive Director (CEO function)** while retaining role ID `strategy_lead`. It develops proposed vision and strategy, maintains company-approved direction, coordinates the seven directors, resolves operational tradeoffs and follows outcomes through completion. This is a functional agent mandate, not appointment as a legal corporate officer. `EXECUTIVE_AUTONOMY.md` defines the intended operating model: human involvement concentrates on meaningful approvals, exceptions and client communication, while authorized internal work proceeds without repeated prompting. That is an evaluated target, not a claim that every workflow is already autonomous.

## Execution rules

Complete dependencies before claiming a milestone. Maintain `PROGRESS.md` with completed task IDs, evidence, test results, known limitations, and the next task. Continue through ordinary implementation problems without requesting business credentials. If a required local tool is unavailable, document the actual blocker and complete independent work; do not report unrun checks as passed.

Use the default stack: FastAPI, Pydantic 2, SQLAlchemy, Alembic, React/TypeScript/Vite, PostgreSQL 17 at a compatible current patch verified during the build. One application image serves the web interface/API or runs the worker. Use PostgreSQL for the durable queue; introduce no Redis dependency initially. Keep source and artifact bytes in bounded PostgreSQL `BYTEA` storage for the pilot: 10 MiB per file and 100 MiB per organization are engineering defaults. Every retained version counts. A later `ObjectStoreAdapter` is optional. Ephemeral application files are temporary processing material, never the authoritative store.

All milestone demonstrations must state their capability level: **fixture-demonstrated**, **implemented-unconnected**, **live-verified**, **unsupported**, or **deferred**. A deterministic fixture demonstrates workflow behavior, not business judgment or actual financial results.

Track deployment environment (`local`, `staging`, `production`) separately from operating mode (`demo`, `evaluation`, `connected_pilot`). Enforce the approved combinations. A staging label does not authorize live data or paid calls; a provider-mode change does not promote a release to production. Each environment has distinct credentials, databases, storage and action permissions. Use separate environment usage ledgers and allocated ceilings whose sum cannot exceed the approved company pilot ceiling. Maintain an allocation register, provider controls and aggregate reporting; do not claim that isolated databases share atomic budget counters. Prefer one active paid environment during the initial pilot when practical.

### Commands the implementer must provide

These are requested command interfaces, **not commands that already exist in this handoff**. Implement and document equivalent commands if a suitable existing repository uses another convention.

| Command | Required behavior |
| --- | --- |
| `make setup` | Install locked dependencies, validate local prerequisites, and create local configuration without secrets. |
| `make demo` | Start PostgreSQL, apply migrations safely, seed synthetic fixtures idempotently, and launch the web/API and worker. |
| `make test` | Run unit and PostgreSQL integration checks relevant to implemented milestones. |
| `make e2e` | Run browser acceptance scenarios against the functional application. |
| `make check` | Run formatting, linting, typing, schema validation, and build checks. |
| `make verify-no-egress` | Demonstrate that demo workflows complete with application outbound traffic denied. |
| `make export-demo` | Export the selected synthetic recommendation and drafts with evidence and demo labels. |
| `make reset-demo` | Explain the destructive scope, then reset only the designated local synthetic database. |
| `make stop` | Stop local services with a graceful worker checkpoint/shutdown. |

## M0 — Scaffold and contracts

**Dependencies:** none. **Outcome:** a coherent, bootable repository and explicit interfaces before business behavior is added.

### M0.1 Establish the application

Create or adapt the repository, lock dependency versions, configure formatting/types, and add the single Docker image and local Compose services. Use actual PostgreSQL for integration tests. Keep fixture-mode configuration explicit and deny application egress in its test configuration. Reading public documentation and installing development dependencies are separate from application runtime traffic.

### M0.2 Define contracts and configuration

Create typed schemas for evidence, findings, role definitions, delegation briefs, recommendations, artifacts, reviews, approval decisions, action intents, runs, jobs, capabilities, usage, and errors. Add legal issue/obligation records, legal review dispositions, environment configuration and release evidence. Add a versioned mission/vision/strategy register, standing-mandate records, outcome measures, and decision/exception records. Separate proposed direction from human-ratified active direction; record the approved version governing each run. Define `ModelProvider`, storage, identity, and connector interfaces. Invalid output must produce a typed failure or bounded repair request, never unchecked execution.

Implement the common limits centrally: two concurrent model calls globally within each environment's application deployment across its roots and workers; depth two with the root at depth zero; eight unique delegated task IDs per root, including the review task; thirty model calls per root including retries and reviews; thirty minutes of active work per root; and three review attempts per artifact lineage, comprising the initial review and at most two revisions. The review attempts reuse one review task while all calls count against the same root. Waiting for a human or missing evidence does not consume active-work time; queued calls and in-flight requests still have bounded timeouts.

### M0.3 Provide the fixture runtime

Implement a seeded `FixtureProvider`, deterministic clock/identifiers for scenarios, synthetic source packets, and conspicuous demo labels. No live provider fallback is permitted. Missing live configuration must report unavailable/blocked rather than return fixture success.

**Definition of done:** the documented demo command starts the application without account credentials; a health check distinguishes application readiness from provider/connector readiness; schemas reject malformed data; the runtime visibly identifies fixtures. Deliver repository scaffolding, contracts, migrations framework, environment example, and the initial progress/decision records.

## M1 — Evidence, policy, durable jobs, and identity

**Dependencies:** M0. **Outcome:** a trustworthy foundation for source-based work and recoverable execution.

### M1.1 Store evidence and artifacts

Implement organization/client-scoped evidence imports and immutable snapshots with content hashes, source locators, capture dates, freshness, version links, and synthetic/live classification. Enforce storage quotas before persistence and retain an explicit quota view. Provide safe text/Markdown/CSV parsing first. Add other formats only with bounded parsers, clear supported-format reporting, and tests. Sanitize rendered content and filenames. Do not execute macros or instructions found in sources.

### M1.2 Enforce access in backend code

Implement local demo identities and permission fixtures for Luis, Danielle, Sarai, and Michael without claiming that real users are connected. Local identity mode binds to localhost and must fail production-startup checks. Apply organization, client, role, and task-purpose restrictions at retrieval and tool execution. Agents cannot grant permissions, approve work, or substitute their own identity for a human actor.

### M1.3 Implement the job state machine

Persist task dependencies, queues, leases, attempts, heartbeats, checkpoints, cancellation, blocked reasons, and audit events. Claim jobs in short database transactions; release locks before provider or connector work. Use transactional enqueue/outbox handling and unique occurrence keys for events/schedules. Implement bounded backoff for transient errors and separate missing evidence, denied access, human rejection, and unknown external outcomes.

Counters survive retries and resumes. A new root requires a distinct business assignment, stage or legitimate recurrence under an active approved standing mandate; code must not open another root to evade limits. Organization budgets apply across all roots.

Implement backend-enforced standing mandates with authorized human issuer, organization/environment/client scope, permitted internal actions, purpose, trigger/recurrence, resource limits, material-change thresholds, active period, expiry and revocation. Recheck the current mandate and action preconditions before dispatch and after a wait. A model can propose a mandate or amendment but cannot activate it, extend its expiry or broaden its authority. An expired/revoked mandate holds only dependent work and creates the relevant decision item; other authorized work continues.

**Definition of done:** source versions survive restart; a simulated worker crash resumes from the correct checkpoint; duplicate event delivery does not duplicate the task; cross-client reads fail through the API and tool router; quota violations leave no partial source record; logs contain no secrets. Deliver durable repositories, policy service, queue/worker, identity adapter, and integration tests.

## M2 — Executive-led discovery, director coordination and independent review

**Dependencies:** M1. **Outcome:** the full business structure can investigate a sparse evidence packet and propose priorities.

### M2.1 Implement versioned role manifests

Represent the Executive Director (CEO function, role ID `strategy_lead`), Marketing, Sales, Client Success, COO, Finance, People Development, Legal & Compliance, and critic with their actual mandates, evidence needs, outputs, measures, and limits from `BUILD_PLAN.md`. The executive is the existing lead with a stronger mandate, not an additional layer with overlapping authority. COO remains horizontal across capacity and delivery; bookkeeping/close sits under operations. Legal & Compliance is a peer director with a horizontal advisory and obligations-management role. Role names do not create permanent processes or independent authority.

The executive can originate a proposed mission, vision and strategic options from sparse input and available evidence. Humans ratify the company's direction and material changes. Translate the active direction into outcome measures and proposed quarterly/monthly priorities, then coordinate approved initiatives, director dependencies and internal work. Evaluate tradeoffs against client fit, service quality, capacity, economics and the approved constraints rather than choosing solely by revenue or activity volume. A proposed improvement cannot silently change approved goals, permissions, budgets or a production policy.

Legal & Compliance identifies contract/proposal mismatches, policy and franchise-authority questions, data-use/vendor terms, workforce issues, approved AI/IP requirements, and notice/renewal obligations. It researches and drafts within approved sources, records jurisdiction and effective date for legal questions, and prepares specific questions for qualified counsel or authorized company decision-makers. It cannot sign, accept terms, waive rights, settle disputes, invent governing law, or convert its output into a final legal determination. The critic reviews the evidence and reasoning in Legal's output; Legal owns the issue/obligation workstream.

The seven director tasks plus one critic task use all eight delegated task IDs if a broad discovery invokes every role. Do not increase the limit or spawn a ninth specialist. Invoke only relevant roles, let the lead integrate their reports, or use a distinct approved later stage while preserving organization budgets. A stage cannot exist solely to reset an exhausted cap.

Directors may propose specialist roles and dispatch approved specialist templates within existing boundaries. Effective tools and data access are the intersection of organization, role, parent-task, and connector permissions. Permission expansion remains a human decision.

### M2.2 Build discovery orchestration

Ingest a synthetic business packet, assess evidence coverage by function, separate facts/assumptions/unknowns, identify contradictions, and ask only consequential missing questions. Produce a prioritized recommendation with alternatives, dependencies, capacity implications, economics, source references, and a named decision. Do not hard-code dormant timing prospects as the winning strategy or invent a revenue baseline.

Every delegation brief includes the objective, business/client scope, relevant source snapshots, prior decisions, required output schema, permitted tools, expected completion conditions, and remaining limits. Parallelize independent work; persist dependencies for subsequent synthesis.

### M2.3 Add the critic and bounded repair

The critic reads the brief, original sources, proposed artifact, and deterministic checks. It creates a separate review record and cannot edit producer artifacts. Validate its verdict/findings against a schema. Seed cases for unsupported claims, conflicting evidence, arithmetic errors, unrealistic capacity, and insufficient information.

Enforce the three-attempt review limit in code. Repairs consume the same root limits. Retain unresolved findings and escalate after exhaustion. A critic pass means reviewed, never authorized to execute externally.

The executive may request revision or record an evidence-based disagreement, but cannot erase, downgrade or withhold a critic's material unresolved finding. Preserve the critic's direct path to the authorized human decision inbox and reserve enough run budget for review or a truthful partial handoff.

### M2.4 Implement bounded executive supervision

Use the durable worker to process approved schedule occurrences, new authorized evidence, completed tasks, unresolved dependencies and outcome changes. The executive checks the active vision/strategy and mandate, selects relevant directors, prepares/revises authorized work, reviews results, updates next steps and creates only consequential human decisions. This is event- or schedule-driven work with checkpoints and bounded calls, not an endless model conversation.

Demonstrate the loop using a controllable clock and synthetic events. Live schedules, business connectors, notifications and paid calls remain disabled. Deduplicate the business occurrence and consolidate repeated findings. An event carrying untrusted text cannot create authority. Exhausted calls, time or task limits cannot be reset by relabeling the same assignment as a new root; an actual later authorized recurrence has its own occurrence ID while sharing company budgets.

**Definition of done:** sparse input yields useful provisional analysis with visible gaps; the recommendation varies across contrasting fixtures; source citations resolve to exact snapshots; seeded errors trigger specific corrections; unresolved critical findings stay visible. A synthetic approved event can start and progress scoped internal work without another user prompt, and a material strategic change creates a reviewable human decision. Deliver executive/director manifests, mission/strategy and mandate records, discovery/supervision workflows, reviewer contracts, and deterministic scenario tests.

## M3 — Complete decision-to-draft browser workflow

**Dependencies:** M2. **Outcome:** Luis can use one working vertical slice end to end.

### M3.1 Build the core business interface

Implement Briefing, Evidence, Work, and Decisions views. Show what was learned, what is proposed, what has completed, and what needs a human decision. Provide original-source inspection and clear reviewer findings. Put model/call diagnostics in an administration panel. Use responsive layouts and accessible forms; avoid departmental chatbot screens that conceal shared work state.

Provide one consolidated decision/exception inbox rather than separate streams from each director. Each item includes the decision or exception, accountable human, severity/priority and basis, evidence, current best artifact, options, recommendation, affected work, and a deadline only when supported. Aggregate duplicate issues without hiding distinct recipients, risks or unresolved objections. Routine status belongs in a concise briefing. The interface must distinguish action required from informational progress and show what continues while an item waits.

### M3.2 Implement exact-scope approvals

Persist strategy approval separately from artifact/communication approval. A strategy approval specifies initiative, authorized internal preparation, budget, scope, and duration. Artifact review identifies the exact immutable version and content hash. Record the real actor identity in connected mode; use labeled demo identities now.

Changes to recipients, content, attachments, client, scope, amount, or other material approved fields invalidate the relevant approval. Revocation and supersession are enforced in backend code. Approval and its resulting internal task enqueue must commit atomically. Direct endpoint calls face the same controls as UI actions.

A valid standing mandate may authorize recurring internal research, preparation, review and task reprioritization within its exact scope. Do not request the same permission for every model call, revision or permitted internal step. New strategy, material scope/budget changes, affected final artifacts and reserved actions retain their required human decision. Silence, expiry of a decision deadline, or continued application use never counts as consent. Any batch approval must expose and bind the actual selected items and versions; it cannot grant hidden additional authority.

### M3.3 Complete preparation and export

After strategy approval, prepare the appropriate synthetic campaign, proposal narrative, client follow-up plan, or other complete deliverable. Run the required review, present the final work, and support revision/rejection/export. Emails and campaigns remain drafts for humans to send. Do not implement or register a send tool. A human-reported send is labeled as reported, without fabricated provider delivery confirmation.

**Definition of done:** a browser scenario completes discovery → recommendation → critic → human strategy approval → preparation → final review → export. Rejecting or changing an approval has the correct effect. Exported work includes relevant evidence, version, review status, and demo marking. Deliver functioning UI, approval service, export support, and end-to-end evidence.

## M4 — Broader business views and close preparation

Include the isolated Bird Bowl accounting profile described in BIRD_BOWL_ACCOUNTING_PILOT.md. Backend scope must exclude SS executive/director business workflows, CRM and other-client data from that client deployment. Test approved deterministic preparation through application-owned adapters with zero model calls and the required review policy; ambiguous items use authorized optional model assistance or a human exception. Do not connect Bird Bowl or assume its host/current ledger is ready during this milestone. AT-58 and AT-59 cover these requirements.

**Dependencies:** M3. **Outcome:** the pilot supports the complete intended business scope beyond the first slice.

### M4.1 Clients, opportunities, retention, and expansion

Add synthetic prospect histories, documented non-conversion reasons, current-client relationship plans, concern follow-up, and expansion signals. Preserve human account ownership. Client Success owns relationship coordination; Sales develops commercial expansion proposals; operations validates delivery capacity. Keep Supporting Strategies data and derived opportunities within its scope. No routing to Ledger Bridge.

### M4.2 Finance, capacity, and people development

Implement deterministic decimal calculations, explicit input assumptions, scenario comparisons, and a revenue bridge distinguishing annual earned revenue, recurring run rate, and project work. Model capacity and billing method rather than assuming automation always increases revenue. Display missing availability/budget data explicitly.

Represent training, coverage, and delegation proposals for Sarai and Michael without inventing skill assessments. Track net time saved after review, correction, training, and monitoring. Treat the revenue aspiration as a target that still requires a verified baseline and horizon.

### M4.3 Bookkeeping and close fixture

Build one fully synthetic client close using a versioned checklist: input readiness, deterministic totals, proposed reconciliations/adjustments, unresolved exceptions, review evidence, and a close package. Preserve the workflow logic that supplied client playbooks will later provide. Do not mark a client period finally closed merely because automated checks pass. Missing-information messages remain human-sent drafts.

Implement portable accounting knowledge import/export using existing evidence/artifact contracts: workflow coverage, approved procedures/skills/examples, decision and correction scope, source references, approval/version/supersession, and a separate validation-case set. Demonstrate AT-60 with fictional inputs. Raw chats and unapproved suggestions cannot activate accounting logic. Record the planned November–December 2026 Bird Bowl capture/validation period as planning metadata, not a schedule or completed work.

### M4.4 Legal issues, obligations and targeted review

Build a scoped issue/obligation register and a review packet linking the relevant agreement, proposal, company policy, source version, affected action, owner, due date, and disposition. Test with fictional policy and contract extracts; do not assert real Supporting Strategies requirements from them. Detect a proposal promise absent from the approved scope, a missing franchise-authority decision, and an unapproved data-use purpose. Mark absent facts and legal sources as unknown rather than inventing them.

Apply review triggers to the affected commitment, data use or action. Let unrelated authorized analysis continue. Routine drafts within an approved template/policy do not require an invented all-department legal clearance. A legal review disposition is separate from business approval, critic status, signature authority and deployment authority.

**Definition of done:** business views share the same sources, tasks, controls, and approvals; staffing and economic assumptions are inspectable; the close package exposes seeded imbalances and missing data; legal issues identify supported concerns and the specific decision needed. Deliver the additional views, calculation functions, scenario fixtures, obligations/review records, and relevant acceptance tests.

## M5 — Reliability, unconnected adapters, and connection readiness

**Dependencies:** M4. **Outcome:** a reviewable local product with an honest readiness package, no activated services.

### M5.1 Implement adapters without activating them

Implement the Anthropic provider behind the established contract, using current official SDK/schema/model documentation and locked tested versions. Verify request building, response validation, usage handling, errors, and refusals with recorded synthetic/stub responses. Label it **implemented-unconnected** until an authorized live evaluation succeeds.

Provide contract stubs and capability inventories for HubSpot, approved file sources, and candidate accounting systems. For each operation, distinguish implemented, verified, unsupported, and deferred behavior. Never infer that an available browser feature has an API equivalent. No accounting/CRM write or communication-send capability is enabled.

### M5.2 Complete cost and reliability controls

Implement atomic estimated-cost reservation and reconciliation, shared root/organization budgets, pause/cancel behavior, and retained usage records. Unset live cost budgets block starting live work. Simulated cost is labeled simulated. Bound concurrent/in-flight work and document possible differences between estimates and provider billing.

Exercise worker restart, duplicate delivery, malformed output, revoked approval, changed evidence, model refusal, unavailable connection, exceeded limits, source instruction injection, and unknown external-write outcomes using test adapters. Restore a local backup and confirm the evidence/artifact/approval/job relationships survive.

### M5.3 Prepare deployment and operations documents

Produce reviewable company staging and production configurations for web, worker, and PostgreSQL, with required secret inputs, health checks, one controlled migration step, graceful worker shutdown, and authenticated access. Do not deploy them or configure automatic deployments. Use distinct resource names and secret references; demonstrate rejection of production credentials in local/staging configuration and of local demo identity in hosted environments. Document backup/restore, export, routine maintenance, capability enabling, credential rotation, budget review, release promotion and rollback.

Prepare a user acceptance walkthrough that Luis and, when available, Sarai and Michael can perform against the actual local application. Include inspection of evidence, approval/rejection/revision, a missing-source close, recovery, exports and a legal issue packet. Keep operator actions and observed results separate from developer assertions. Record release/version, environment, evidence and unresolved findings.

Include a simulated autonomous operating period: an active mandate, several legitimate events, permitted internal progress, a new strategic proposal, a bounded exception and the consolidated decision inbox. Record both necessary human decisions and unnecessary interruptions. Verify that a nonresponse leaves the affected item pending while unrelated permitted work progresses. Do not enable a real schedule or deliver a real notification for this demonstration.

Provide the Bird Bowl operator/readiness template and synthetic AT-61 demonstration: assigned preparation/review authority, teach-back, operation without Luis's prompts, unattended authorized steps, interruptions, review/correction time, and accounting-versus-technical escalation. Jeff's technical and SS's potential accounting co-management responsibilities remain proposed. Do not count a simulated Theresa identity as her actual participation or claim live readiness.

Promote an approved code revision, migrations and versioned configuration through the release process. Do not automatically promote source data, secret values, draft histories, approval decisions, production access or action-enabling flags. A production configuration must receive its own authority, credentials, seed/reference-data decisions and readiness checks.

**Definition of done:** relevant tests and browser flows pass; the demo succeeds with application egress denied; hosted startup rejects demo authentication; artifacts persist without ephemeral storage; readiness reporting separates local results from live unknowns. A human can test the functioning application locally before deployment. Deliver source, locked dependencies, tests, operating guide, cost/limits report, isolated environment configurations, UAT records/template, and a demonstration walkthrough.

### Consolidated connection request after M5

Present one actionable package containing: completed milestone evidence; remaining limitations; confirmed or proposed company repository/account owners and identity setup; the Claude Console workspace and budget needed; the first narrowly scoped read-only data connection or approved import; proposed staging/production resources and separate/aggregate estimated costs; and the exact connection/deployment actions requiring authorization. Include the appropriate company entity and franchise-authority questions without assuming Danielle controls the national franchisor. Ask for missing inputs together. Do not repeatedly interrupt M0–M5 for credentials or claim that this request itself authorizes activation.

## M6 — Authorized Claude evaluation and company staging

**Dependencies:** M5 and explicit connection-stage authorization. **Outcome:** measured live capability for a bounded sample, with optional authenticated company staging for shared testing.

Configure the approved Claude API credentials, human identity, company/client scope, and spending controls. Evaluate actual reasoning against human-reviewed samples, including the critic's detection of errors. Record quality, missed issues, revisions, latency, and gross/cash cost. A fixture pass is not a substitute for this evaluation.

Evaluate the executive on held-out work that requires prioritization, coordination and follow-through within a ratified mission and standing mandate. Record human interventions by reason and workflow, valid exceptions, missed issues, unnecessary approval requests and net leadership/reviewer time. Preserving critical findings is required even when it increases intervention counts. Low interruption volume alone is not evidence of competent autonomy.

Enable only the authorized read connection or sample import. Verify actual scopes, pagination, incremental updates, duplicate/merged records, freshness, and relevant contact restrictions. Compare imported records with the source. Complete a live discovery-to-draft scenario with human review. The first authorized model evaluation can run locally with approved identity, samples and spend controls. Hosting is not required for that evaluation.

If Bird Bowl is in the authorized evaluation scope, use approved November–December knowledge artifacts and separate new cases; measure task coverage, corrections and missed exceptions. Verify the actual transaction-intake account coverage and duplicate/pending-to-posted handling before relying on it. An Expensify, bank, aggregator or native-QBO route remains a candidate until verified. Missing December-close records leave that work pending.

If shared remote testing is approved, deploy only the company staging environment with access limited to designated participants, independent credentials/data and draft-only actions. Staging is hosted testing and incurs its own approved costs; a staging URL or login does not make the release production-ready. Luis, Sarai and Michael perform their assigned UAT scenarios. Danielle or her authorized delegate confirms company access and the next gate. Record tasks actually performed, findings and corrections; do not fabricate approvals for absent participants.

**Definition of done:** the chosen operations are individually marked live-verified with supporting evidence; unresolved limitations have explicit handling; human approvers accept the evaluation/UAT results and pilot scope. Any staging deployment is identified separately from production. No communication sending or ledger mutations occur.

## M7 — Limited company pilot and production decision

**Dependencies:** accepted M6 results and agreed pilot duration, company control, budget, participants, and scope. Production activation requires its own recorded release decision; testing success alone cannot activate it.

Run only approved workflows and schedules. Measure completion quality, exception handling, net time saved, review burden, gross API usage, hosting, and cash paid. Compare against a documented baseline and agreed success criteria. Maintain existing human client ownership and final accounting judgment.

For Bird Bowl, require observed Theresa operation within assigned authority and authorized agent work completed while Luis is away, with useful exceptions and all required reviews. Record the agreed support owners and any co-management engagement separately. Readiness evidence and a release decision govern the handoff; January 1 or completion of a capture period cannot activate deployment.

Use the approved executive mandate to keep internal work moving between human sessions. Deliver complete approval/exception packets and client-ready drafts. Compare the measured human workload with the intended approvals/exceptions/client-communication model, while retaining any required accounting review, sign-off and operational oversight. Narrow or revise an underperforming mandate; do not broaden authority to make the interruption metric look better. Changes to mission or material strategy return to the appropriate human.

Use Luis, Sarai and Michael as the limited initial group within the company arrangement. If actual business work begins in a company staging environment, record that data-use and operational scope explicitly; the word staging does not reduce its obligations. Before a limited production pilot, verify production identity, approved client/data scope, budgets, operating ownership, backup/restore, compatible migrations, release evidence and rollback readiness. Record the permitted users and capabilities. Broader office use remains a later decision.

At the review date, prepare a decision packet recommending continuation, broader rollout, revision, extension with a new ceiling, or stop. Show capacity and revenue implications as evidence-supported scenarios. Company systems remain company-controlled throughout; continuation funding and reimbursement of any agreed personal pilot contribution are separate decisions. Do not design a personal-to-company ownership transfer as the default adoption step.

**Definition of done:** a human decision is recorded with evidence and an operating owner. Do not turn a successful technical demo into an assumed company adoption or automatic budget increase.

## M8 — Optional wider rollout and authorized accounting execution

**Dependencies:** accepted M7 results plus explicit approval of the particular expansion. New users, clients, workflows and any accounting write each require the applicable scope, capacity and authority. This milestone is optional; wider read/draft use does not depend on adding accounting writes.

For wider office rollout, use staged groups with named owners, training/support, capacity checks, budget allocation and feedback. Reconfirm applicable company/franchise authority and review any new data-use or contractual scope. Preserve tenant/client controls and the ability to pause only the affected capability. Do not grant every company user access to every client or activate every director workflow automatically.

Implement only verified, individually authorized routine writes with deterministic preconditions, evidence, audit records, idempotency, and reconciliation of unknown outcomes. Test first in an appropriate sandbox or approved nonproduction context. Human review remains required for unusual or material adjustments and final close. A standing authorization must define its allowed cases and stopping conditions in enforceable policy.

**Definition of done:** every expanded group/workflow has a recorded scope, operating owner, budget and acceptance evidence. Every enabled write additionally has a verified provider capability, narrow policy, successful controlled evaluation and recovery procedure. Unsupported actions stay unsupported or human-executed. This milestone does not enable outbound communication sending, payments, publishing, CRM mutations, or unrestricted autonomous accounting.
