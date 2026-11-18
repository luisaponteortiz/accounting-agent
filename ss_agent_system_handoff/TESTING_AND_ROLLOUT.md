# Company Pilot Testing and Rollout

Version 1.4 — November 14, 2026

## 1. Operating decision

Build this as a company-controlled initiative from setup, with Luis, Sarai and Michael as the first pilot users. Luis will agree sponsorship, authority, resources and the release process with Danielle. Company control does not mean immediate access for the entire office, and it does not establish authority over the national Supporting Strategies organization.

The initial local application can be tested before any cloud deployment. It uses synthetic data and a deterministic model provider. Actual model judgment can then be evaluated locally with authorized company API access, before hosting if useful. A private company staging environment provides shared testing before production. Staging is itself a deployment, but its purpose and authority are limited to testing.

The current request updates the development plan only. It does not create accounts, deploy services, connect company data or incur costs.

Bird Bowl is the accounting pilot candidate only. Its possible client-hosted accounting module is a separate, restricted deployment; the company executive/director/business-development system remains under SS control. Verify Jeff's platform, current ledger, authority, administrative access, credentials and costs before any live step. Local synthetic accounting testing remains possible while those details are unknown. BIRD_BOWL_ACCOUNTING_PILOT.md and AT-58–AT-61 define the boundary, model-free deterministic path, portable knowledge and operating-readiness requirements.

## 2. Proposed company pilot charter

Confirm the following with Danielle before company setup or access; record unknowns rather than treating this table as an existing appointment or approval.

| Item | Proposed arrangement |
| --- | --- |
| Sponsoring organization | The actual franchise/operating company Danielle is authorized to sponsor; record the legal entity and any franchisor requirements. |
| Business sponsor | Danielle or the company's designated sponsor, subject to agreement. |
| Pilot and product lead | Luis. |
| Initial users | Luis, Sarai and Michael with individual permissions and selected clients. |
| Company administrators | Named company-controlled account owners with recovery continuity; Luis need not be the sole administrator. |
| Implementation repository and hosting | Company-controlled private repository and provider organization/workspace when established. |
| Model access | Company-authorized Console workspace and scoped credentials, with available Team credits used first within approved limits. |
| Legal review | Named company authority and qualified counsel path for triggered matters; source agreements and policies determine applicable obligations. |
| Release decision | A designated company approver accepts the tested release, cohort, workflows, client scope, operating budget and support owner. |
| Ownership and reuse | Record implementation ownership/licensing and rights to supplied materials. Company control does not by itself transfer North Star or unrelated pre-existing personal work. |
| Funding | Company control applies even if Luis contributes a bounded amount. Record contribution, period and reimbursement separately. |

Account planning can proceed after the plan while local development continues. Do not block synthetic local work on missing company credentials. Do not solve missing company authority by opening a personal production account and assuming a future transfer.

## 3. Keep three dimensions separate

**Environment** identifies where the application runs: local, staging or production. **Operating mode** identifies its data/model/effect configuration: demo, evaluation or connected_pilot. **Cohort and workflow scope** identifies who can use which clients and capabilities.

A company staging deployment may use synthetic fixtures or approved samples with a real model. A production deployment may initially admit only the pilot team and keep all external writes disabled. A label such as staging never grants access or makes real data non-sensitive.

| Stage | Where and with what | What it can establish |
| --- | --- | --- |
| Local demonstration, M0–M5 | Computer-based web app, PostgreSQL and worker, synthetic evidence, FixtureProvider, no external credentials. | Interface, state transitions, evidence links, policy enforcement, exports, calculations and recovery. |
| Local model evaluation, M6 | Same app with authorized company API credential and approved evaluation inputs; effects disabled. | Measured model reasoning, factual support, critique, latency and usage; no cloud hosting required. |
| Company staging, optional M6 | Authenticated company-hosted copy with separate database and credentials, synthetic or explicitly approved test samples. | Shared user testing, hosting behavior, identity, connector checks and recovery under intended infrastructure. |
| Limited operational pilot, M7 | Approved company environment, named users and selected real workflows, with a recorded production decision where operational use begins. | Actual review effort, usefulness, quality, costs and delivery outcomes over an agreed period. |
| Wider rollout, optional M8 | Approved release and added cohorts/clients/workflows after evidence supports expansion. | Broader operating results; accounting-write capabilities require their own separate decision. |

Real client deliverables used operationally need the applicable operational authority even when the group is called a pilot. Wider read-and-draft rollout does not depend on enabling accounting writes.

## 4. Luis's local user acceptance session

Provide one documented startup command, fixture reset command and URL. A fresh operator should be able to start the interface without a cloud account. Label simulated outputs clearly and use the same persistence, approval, export and workflow code paths intended for later evaluation.

Have Luis perform these tasks himself and record observations, rather than accepting only developer screenshots:

| Task | Observable result |
| --- | --- |
| Open the timing-prospect case | Inspect a supported recommendation, excluded records and the sources behind the proposed audience. |
| Open the service/capacity case | See a different priority when client concerns and workload change the evidence. |
| Ask for a revision | A new artifact version appears; the previous version and review remain inspectable. |
| Approve the strategy | Scoped internal preparation proceeds while the final communication still needs its own human review. |
| Export a completed draft | Receive the exact reviewed content, recipient context and unresolved items, with no automatic sending. |
| Review the legal case | Identify proposal/agreement mismatches, unresolved authority and a proposed obligation date; inspect their actual fictional sources. |
| Work through the close case | Complete available bank preparation while the missing card statement remains visible; do not mark the close complete. |
| Interrupt and resume work | Persisted state returns without duplicate completed work or newly granted authority. |
| Pause work or revoke a decision | The affected pending action stops, with a truthful explanation and preserved history. |
| Test the executive operating cycle | A simulated event starts permitted work under a synthetic approved mandate without another chat prompt; a material strategy change returns as a complete decision package. |
| Review the executive inbox | Related issues are deduplicated, unresolved critic findings remain visible, and unanswered decisions stay pending while independent work continues. |

Record user, date, application version, scenario, expected behavior, observed result, defect and disposition. Unfamiliar wording or a confusing decision screen is a usability finding even if a software test passes. The acceptance tests specify failure cases; this session establishes that the intended people can use the product.

## 5. Live evaluation and company staging

After M5, connect only the selected model and minimum approved sources for the next evaluation. Use held-out cases and human-reviewed expected outcomes. Include factual, strategic, legal-policy and accounting errors that the critic must identify. Passing a scripted fixture does not establish model reliability.

For hosted testing, use real company identity, named access and server-enforced client permissions. Local demo accounts must fail startup in staging and production. Give staging its own database, storage, session secrets, provider keys/workspaces where available, callback URLs, queue, schedules and logs. Exported artifacts retain their environment and synthetic/live provenance.

Render documents environment-specific configuration and network controls; network isolation alone does not protect a public application endpoint. Verify both provider configuration and application authentication, along with repository rights that can modify a Blueprint. [S11]

Do not place production secrets in staging, clone real customer data by default, or enable every connector for convenience. Use synthetic evidence first, then approved minimal samples. Ordinary internal preparation can continue while a specific legal or access question is escalated.

### Bird Bowl knowledge capture and operating validation

Luis plans to work through November and December 2026 Bird Bowl accounting with Claude. Treat this as knowledge capture and validation for the accounting-only component, not an already completed agent training or deployment. November work should yield explicit procedures, checklists, skills, mappings, approved examples and a decision/correction register. Preserve sources, approval status, applicable scope and version history; separate raw chats and provisional suggestions from instructions the application may apply.

December work tests those instructions on new cases, with expected answers kept outside the worker's inputs. Record discrepancies, review changes before updating approved logic, and retain an independent validation set. Include relevant missing-data, duplicate and exception cases. Coverage must state what remains manual or untested. Complete the December close only when its required records and statements are available, potentially in January 2027; January 1 is not an automatic readiness or deployment date.

Use the following distinct evidence stages:

| Stage | Required evidence and limits |
| --- | --- |
| Local synthetic checks, M4/M5 | Load a portable approved package without the original chat; verify source/version selection, provisional-content exclusion, exception routing, durable progress and duplicate prevention. Exercise pending December records and the calendar boundary. These checks establish software behavior, not real accounting accuracy or operator readiness. |
| Authorized knowledge evaluation, M6 | Compare outputs on held-out cases with reviewed accounting results; record source completeness, discrepancies, corrections and coverage gaps. Passing teaching examples is insufficient. |
| Operator and unattended-work evaluation, M6/M7 | Theresa uses the guide and explains escalation rules back, completing her assigned workflow without Luis's step-by-step prompts. Separately observe the agent completing its authorized portion while Luis is away, with required review preserved and independent work continuing around a blocked item. Record actual participants and conditions; a developer simulation cannot substitute for these results. |

Measure eligible tasks and completion, covered versus manual work, necessary and avoidable interventions, exceptions found or missed, quality, review/correction time and recurring maintenance. Agree thresholds before the observed period. The target is demonstrated recurring staff-level execution and selected senior-level preparation, with minimal avoidable interruption; it is not a claim that every human accountant responsibility has been replaced.

Before an operating handoff, confirm Theresa's day-to-day authority and the accounting-versus-technical escalation routes. Jeff's proposed role covers hosting and integration maintenance; Supporting Strategies' proposed co-management covers accounting logic, quality, close/exception oversight and improvements. Changes with accounting effects retain accounting review. These responsibilities and any commercial engagement remain to be agreed. AT-60/AT-61 evidence supplements, but does not replace, the existing access, release, posting and final-close gates. No live connection, accounting-policy change, deployment or expanded scope follows automatically from successful knowledge capture.

## 6. Cost and permission boundaries

Model-call concurrency is global within each environment's deployed application: two calls across its roots and workers by default. Root task, call and review counters persist as defined in BUILD_PLAN.md. Separate databases do not share those counters automatically.

Before operating multiple paid environments, record a company budget and allocate portions to each. The sum of environment allocations must not exceed the approved company ceiling. Track aggregate usage and provider-side limits; do not copy the full allowance to every environment or claim an exact invoice ceiling from estimates. One active paid pilot environment is preferred initially.

Each environment has independent capability flags. Staging approval never enables production, sending, signing, posting, payments or wider user access. Models cannot change these flags or grant human approval.

## 7. Release and promotion

Prepare one reviewable release packet containing:

- Exact code commit or image digest, dependencies, migrations, models, role/playbook/prompt versions and policy/configuration versions.
- Passed, failed and deferred software checks; live evaluation results; user acceptance findings; unresolved issues and affected capabilities.
- Approved users, clients, workflows, data sources, budget allocations, administrators and operating/support owner.
- Legal review dispositions for matters actually triggered by that release, without a blanket claim of legal compliance.
- Backup and tested restore evidence, monitoring and escalation routes, a pause procedure, and the rollback/forward-fix plan.

The authorized human approves a particular release and scope. Keep automatic deployments disabled until the company explicitly chooses a release policy. Render supports manual deployment and deployment of a selected commit. [S12]

Promote the tested application and intentionally validated configuration. Do not promote test credentials, synthetic identities, approval records, pending jobs, webhook deliveries, source data or enabled schedules as a side effect. Initialize production with approved identities and deliberately imported company data. Validate source-to-target mappings and versions where a migration is required. Rehearse migrations on a safe copy before the release.

After deployment, verify authentication, health, configuration, queue behavior and one approved read/draft workflow. Keep the rollout restricted to the pilot cohort until observed results support expansion.

## 8. Rollback and recovery

Preserve a known-good release and evaluate database compatibility before reverting code. A code rollback does not reverse a schema change, restore data or undo an external action. Prefer compatible migrations and a documented forward fix where reversal is unsafe.

If work must pause, stop new dispatch, preserve completed artifacts and record in-flight operations. Reconcile uncertain external outcomes using the provider's supported identifiers; never blindly repeat a possibly completed action. A database restore must not erase awareness of subsequent external effects or trigger duplicate jobs. Keep a reconciliation record if recovery spans such effects.

Test the process with synthetic faults before relying on it in the pilot. Review backup retention and recovery objectives with the company before storing live records.

## 9. Proving the company pilot

Before real operations, agree on an evaluation period and thresholds for the selected workflows. Compare quality, net human time, reviewer workload, timeliness, usefulness and total cost against the baseline. Count recurring supervision, corrections and maintenance. Keep one-time build/training separate.

Also measure necessary and avoidable interventions, executive/approval review time and exception quality. The CEO function and standing mandates must reduce management work without concealing failures or removing required judgment. EXECUTIVE_AUTONOMY.md and AT-50–AT-57 define that evaluation. Fixtures demonstrate mechanics; only observed live workflows can establish whether humans mainly handle approvals, exceptions and client communication.

Danielle's continuation or expansion decision should use the evidence, remaining limitations and support requirements. Possible outcomes are continue the current pilot, expand selected capabilities, revise and retest, or stop. Approval of one workflow does not approve every department or accounting action. The voluntary NIST Generative AI Profile provides background for governance, provenance and pre-deployment evaluation; it does not certify this system or establish binding company obligations. [S13]

Source links are in SOURCES.md. Acceptance cases AT-41 through AT-49 cover the added Legal, company-control and release requirements.
