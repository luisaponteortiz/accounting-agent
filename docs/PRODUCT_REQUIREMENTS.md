# Accounting Agent OS — product requirements register

Established 15 November 2026. Current register: **88 retained requirements**, updated 16 November 2026. Owner: the product owner, with accounting validation by the assigned accounting lead. This is the authoritative register of product scope, requirements and their current disposition. It preserves the complete accounting product vision across development batches. It is not a replacement implementation backlog, an accounting-policy approval, or permission to connect, spend, send, deploy, pay or post.

**Accounting Agent OS is a universal, reusable accounting execution platform. Bird Bowl is its first client implementation, not its product boundary.** Shared code must accommodate additional clients through isolated configuration and progressively validated capabilities. No Bird Bowl policy, industry assumption, system choice, currency, jurisdiction or workflow becomes a universal default merely because it appears in a pilot. Universal architecture does not mean every accounting treatment or client is supported today.

## Authority, sources and maintenance

Apply the user's current instructions first, then the project scope and restrictions in [AGENTS.md](../AGENTS.md). Use this register for the product's required outcomes, [DECISIONS.md](../DECISIONS.md) for decision history, [PROGRESS.md](../PROGRESS.md) for the current checkpoint, and the existing Fable tickets for implementation order and exact control assertions. [CONNECTION_READINESS.md](CONNECTION_READINESS.md) controls readiness claims. A requirement's presence or product approval does not open an implementation or operating gate. Record a conflict instead of silently choosing a weaker control.

The following sources were consolidated. Earlier documents remain intact; a reference is not an assertion that its entire original business scope applies here.

| Reference | Source and use |
| --- | --- |
| U | User's accounting-only, general-platform directions, current requirements-register assignment and clarification that the platform must remain usable across clients. These supersede the broader executive/business-development system. |
| PILOT | [Bird Bowl accounting pilot v1.4](../ss_agent_system_handoff/BIRD_BOWL_ACCOUNTING_PILOT.md): known plans, portable knowledge, validation, operating handoff and unknown client facts. |
| LEGACY | Accounting and shared-control sections of [BUILD_PLAN.md](../ss_agent_system_handoff/BUILD_PLAN.md), [IMPLEMENTATION_BACKLOG.md](../ss_agent_system_handoff/IMPLEMENTATION_BACKLOG.md), [CONNECTIONS_AND_DECISIONS.md](../ss_agent_system_handoff/CONNECTIONS_AND_DECISIONS.md), [TESTING_AND_ROLLOUT.md](../ss_agent_system_handoff/TESTING_AND_ROLLOUT.md), [ACCEPTANCE_TESTS.md](../ss_agent_system_handoff/ACCEPTANCE_TESTS.md), and the reusable inbox/measurement concepts in [EXECUTIVE_AUTONOMY.md](../ss_agent_system_handoff/EXECUTIVE_AUTONOMY.md). Executive, marketing, sales and CRM agents are excluded. |
| ARCH | [Current architecture](ARCHITECTURE.md) and [six-area capability contracts](CAPABILITY_CONTRACTS.md). These distinguish executable handlers from module seams. |
| FABLE | [Architecture review](../review/FABLE_ARCHITECTURE_REVIEW.md), [implementation backlog](../review/FABLE_IMPLEMENTATION_BACKLOG.json) and [60 validation cases](../review/FABLE_VALIDATION_CASES.json). Original requirements, dependencies, gates and test assertions remain authoritative for their tickets. |
| CORRECTIONS | Independent [C corrections](../exports/FABLE_BATCH_1_VERIFICATION/FABLE_BATCH_1_1_CORRECTIONS.json), [RV corrections](../exports/FABLE_REVERIFICATION/FABLE_REVERIFICATION_CORRECTIONS.json), and latest [RA acceptance report](../exports/FABLE_RV_ACCEPTANCE/FABLE_RV_ACCEPTANCE_REPORT.md) / [RA corrections](../exports/FABLE_RV_ACCEPTANCE/FABLE_RV_CORRECTIONS.json). Review inputs are immutable. |
| EVIDENCE | [RA response report](RA_CORRECTIONS_REPORT.md), [execution results](acceptance_ra/execution-results.json), [probe adaptations](acceptance_ra/probe-adaptations.md), and [current Fable handoff](../FABLE_RA_CORRECTIONS_HANDOFF.md). These are developer evidence awaiting independent RA acceptance. |
| RETURNED REVIEW | [RA independent verdict/RB tickets](../exports/FABLE_RA_ACCEPTANCE/FABLE_RA_CORRECTIONS.json) and [product-register PR-01–PR-17 findings](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json), with their reports/probes/raw evidence preserved unchanged. These reject the RA checkpoint and condition register acceptance on corrections. Current developer response evidence is in corrections_rb/. |

Before implementation, check the relevant IDs, dependencies, client-fact prerequisites and current ticket gate. When a feature is added, changed, completed, deferred or rejected, update its record, acceptance criteria and evidence; cross-reference the assigned backlog ticket and update decisions/progress in the same change. An unassigned requirement stays unassigned until planning/authorization occurs. Preserve IDs permanently; add IDs rather than renumbering, and retain rejected or superseded records with the decision and reason. Do not rewrite independent review files or frozen bundles to synchronize them. Use the crosswalk below as the current overlay on those historical inputs.

## Product decisions, implementation states and planning metadata

Each requirement has exactly one Product decision and one Implementation state. A Scope note identifies the built subset, unbuilt scope and remaining limits; Evidence identifies named tests/probes and the reviewed checkpoint where applicable. Product decisions never grant implementation, policy, integration, spending or operating authority.

| Product decision | Meaning |
| --- | --- |
| Proposed | Candidate product/operating scope awaits the product owner or client authority. |
| Approved | Required product outcome is accepted; execution authority remains separate. |
| Rejected | Retained exclusion with reason and decision reference. |
| Superseded | Retained older requirement with its successor/decision. |

| Implementation state | Meaning |
| --- | --- |
| Not started | No implementation of the stated scope; intention is not delivery. |
| Deferred | Outside the assigned work; dependency/target stage names the prerequisite. |
| Implemented | Artifact/code exists; sufficient named validation has not been completed. |
| Developer-tested | Named developer tests cover the bounded scope, not independent acceptance or operating readiness. |
| Independently verified | An independent report names the exact checkpoint and verified scope; no broader gate is implied. |
| Verification failed | The latest independent verification failed an applicable criterion. Developer repairs are recorded in Scope note/Evidence but cannot erase this verdict before independent re-verification. |

Implemented and higher states require named scope/evidence. A failed independent probe downgrades every affected record in the same change. Only an independent reviewer can establish independent verification. Run `python3 scripts/check_product_requirements.py --json` or `make check` after edits; the script reproduces counts and checks required fields, unique IDs, valid states/evidence, dependencies/cycles, client boundaries and all backlog crosswalk rows.

Priority remains Must/Should/Could for outcome importance, separate from Fable severity. Needed for is a candidate planning classification: G0 controls, G1 approved samples, G2 hosted reads, G3 specified writes, G4 operating handoff, Second client, Platform maturity or Product decision. The product owner still decides ordering of unassigned work (PR-05); this field neither creates a new batch nor authorizes implementation. Conditional dependencies apply only to their named operation/real-authority gate, not to the fictional tested subset.

| Target stage | Meaning and boundary |
| --- | --- |
| Current / G0 | Preserve the existing corrective order and synthetic Batch 2 gate. No new functionality is authorized by this document. |
| Existing Batch 3 / T-nn | A ticket already present in Fable's backlog. **Batch 3 is closed pending a new assignment**, even where fictional-data implementation was previously considered feasible. |
| G1 / approved samples | After human G0 acceptance, written actual client facts and authority, explicit authorization for named local unconnected samples, proposed/approved configuration and an independently reviewed held-out month. No connection or use in the books. |
| G2 / hosted reads | Separate authorization naming provider, account, data scope, environment and cost ceiling; accepted G1 results, authenticated identity, isolated persistence/secrets and tested backup/restore. No writes or implicit schedule authority. |
| G3 / specified writes | Separately authorized, supported operations with exact approval, durable intent, idempotency, readback, unknown-outcome reconciliation and revocation. Does not include payments or final close. |
| G4 / operating handoff | Observed operator competence and unattended bounded execution, measured human effort, agreed support and an explicit human release for the demonstrated scope. |
| Future / unassigned | Preserved product requirement with no assigned implementation batch. The applicable G1–G4 and action-specific permissions still apply. |

These summarize, and do not relax, [Fable's readiness gates §9](../review/FABLE_ARCHITECTURE_REVIEW.md). Gates require recorded human decisions; dates, test passes and an approved product vision do not open the next gate automatically.

## Current evidence and corrective priority

**RD-01/RD-02 and PRV-11–PRV-13 independently accepted; RB-01 not accepted; Batch 3 closed.** Fable's immutable RD review at checkpoint SHA-256 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9 accepted the assigned RD/PRV assertions, all 120 earlier orders and two deeper five-delivery families. E03/E06 still failed for RE-01/RE-02; 24 of 336 extended orders ended in double approval under the then-undecided second-claim semantics. The owner subsequently approved the fictional local card-feed contract in D-026. RE-01 to RE-03 address its clauses 2, 7, 8 and 9; latest-target-wins is withdrawn. The owner clarified the frozen-period boundary in D-029: preserve an approval already frozen inside its own period and block the incoming version until authorized reopen; the contested-claim blocker remains after reopen. Journals remain outside this contract, and real provider confirmation remains G2 work.

AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 remain Verification failed until independent verification of the new checkpoint under D-026, including the 12 unmodified RD probes, the sole Y05(a) adaptation, all 336 orders and retained gates. Four verified scopes retain their existing bounded citations. [Independent results](INDEPENDENT_VERIFICATION_RESULTS.json) are derived from three pinned reviewer authorities, latest per-record verdict winning, with the original seven-row order enforced. [Current developer report](corrections_re/RE_CORRECTIONS_REPORT.md) records the before/after evidence, clause-by-clause coverage, exact commands and execution limits. Developer passes do not raise failed states or grant human G0/G1–G4, Batch 3 or live authority.

D-026 is recorded word for word as the owner's decision and supersedes the open questions of D-023 only within its stated fictional card-feed scope. U4 and UC-14 remain open; N02c/UC-10, N04e/UC-11 and journal UC-9 remain unchanged. No real client fact, provider behavior or accounting treatment is inferred. D-016/D-017 and every BB-01/BB-02 field are unchanged. ONB-01, ONB-02, INT-07, GL-06, BNK-07 and RPT-03 remain Proposed. Earlier archives, sidecars, original review inputs, adaptations and failed-command evidence remain immutable.

## Product scope and governance

### AAOS-GOV-01 — General accounting product scope

- **Description:** Support the full accounting cycle through one reusable platform: GL, AP, AR, banking/reconciliation, close, reporting/analysis. Keep non-accounting executive and business-development agents outside this project.
- **Business purpose:** Build accounting staff/senior preparation and execution capacity reusable for clients beyond Bird Bowl.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; the six-area design exists, full-cycle execution does not.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G0 controls
- **Dependencies:** None.
- **Acceptance criteria:** Each area has domain/control/extension contracts and truthful capability status; no card-only or Bird Bowl-only dependency prevents another client profile; deferred handlers cannot return fabricated success.
- **Target stage:** Current architecture; capability implementation progresses through the existing backlog and later assigned stages.
- **Trace:** U; ARCH; D-001/D-003.

### AAOS-GOV-02 — Permanent traceable requirements

- **Description:** Maintain this register with stable IDs, all required fields, source/backlog traceability and retained change/rejection history.
- **Business purpose:** Prevent future requirements from disappearing between batches without displacing the active implementation plan.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** The permanent register and executable checks enforce actual evidence, report-backed independent verdicts, adjacent conditional dependencies, disposition consistency and client boundaries; this is documentation governance, not operational accounting acceptance. Independent verdicts are derived from three hash-pinned reviewer machine-readable files, with later conclusions taking precedence; client display-name removal is rejected. The checker enforces the original seven-result row order, including swaps and reversal.
- **Evidence:** [tests/test_product_requirements.py](../tests/test_product_requirements.py); [register checker](../scripts/check_product_requirements.py), PR-04/PR-17.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-GOV-01 for later full-cycle execution only
- **Acceptance criteria:** All ten requested product areas and all T-01–T-27 tickets have a trace; agents must consult/update the register; decisions and progress name the current gate; rejected requirements retain an explanation. Run the repository checker after edits; reject duplicate IDs, missing fields, unknown/cyclic dependencies, invalid states/evidence and missing ticket crosswalks. Only independent review can establish verification; a failed independent probe downgrades affected records in the same change. Require real test/probe references and matching report/hash-backed independent results; reject unconditional tested dependencies on Deferred/Not started records, unconditional Approved-to-Proposed dependencies, stray dependency punctuation and scope-table/prefix conflicts. Read client-specific terms from the client section; scan every shared field except Trace and all shared application/web files. Reject omitted, edited or invented independent-result rows against the pinned reviewer authorities and preserve the current seven-row order. Require the client display name from the client section heading in its Client-specific terms list.
- **Target stage:** Current; ongoing maintenance in each relevant change.
- **Trace:** U; AGENTS.md; DECISIONS.md; PROGRESS.md.

### AAOS-GOV-03 — Evidence-based release and preserved review gates

- **Description:** Keep developer tests, independent review, client sample validation, connected operation and human operating readiness separate; preserve original review evidence and frozen releases.
- **Business purpose:** Make trustworthy claims and prevent a feature or documentation change from widening authority.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Verification failed
- **Scope note:** Independent Fable RD review accepted RD-01/RD-02 and PRV-11–PRV-13 at checkpoint 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; RB-01 remains not accepted for RE-01/RE-02 (E03/E06). The owner subsequently approved D-026, superseding latest-target-wins and adding RE-03 no-release/authorized-selection controls. This record stays Verification failed for RE-01 to RE-03 until independent verification of the D-026 clauses, the 12 unmodified RD probes, the explicitly adapted Y05(a), all 336 orders and retained gates on the new checkpoint. D-029 resolves the frozen-period question: preserve the already frozen approval and block the incoming version until authorized reopen; then the contested-claim blocker still requires an authorized disposition. The clarification and developer probe are recorded in docs/corrections_re/CONTRACT_CLARIFICATION.md. Developer repairs confer no readiness or operating authority.
- **Evidence:** [independent review](../exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; Y01–Y06, X01/X01d/X02 and 120 orders accepted RD-01/RD-02; E03/E06 WEAK and 24/336 double in the independent run. RE-03 is the subsequent owner contract assignment (D-026), not an independently reviewed correction. [tests/test_feed_contract.py](../tests/test_feed_contract.py), the unchanged RD probes/search, [Y05(a) adaptation](../docs/corrections_re/Y05-contract.patch) and corrections_re/ are developer repair evidence only. Independent RE-01/RE-02/RE-03 acceptance pending.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-GOV-02; AAOS-CTL-10.
- **Acceptance criteria:** Existing original methods/regressions and exact assertions remain; known repaired defects must pass; unavailable capabilities remain explicitly deferred; original/adapted probe differences and nonzero original commands remain disclosed; no bundle overwrite or automatic G1/Batch 3 transition.
- **Target stage:** Current / G0; renewed at every subsequent gate.
- **Trace:** FABLE; CORRECTIONS; EVIDENCE; REVIEW_FREEZE.md.

## Reusable architecture and client boundaries


### AAOS-ARC-01 — Shared execution and modular capabilities

- **Description:** Share deterministic accounting controls, tools, workflow DAGs and execution contracts while keeping client accounting knowledge/configuration separate.
- **Business purpose:** Add or validate a module/client without duplicating the core or redesigning the platform.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for the local runner and registered card/journal/readiness workflows; full module coverage deferred.
- **Evidence:** [tests/test_platform.py](../tests/test_platform.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-GOV-01 for later full-cycle execution only
- **Acceptance criteria:** Handlers use declared scoped inputs and committed dependency outputs; handler/model proposals cannot directly approve, query arbitrary client data or perform external effects; unimplemented modules return unavailable.
- **Target stage:** Current foundation; extend only in assigned capability tickets.
- **Trace:** ARCH; FABLE T-06/T-15; D-002/D-003.

### AAOS-ARC-02 — Isolated client workspaces

- **Description:** Scope identities, records, policies, credentials, memory, jobs, evidence, approvals, retrieval and exports by organization/client/environment, with entity/book where accounting requires it.
- **Business purpose:** Reuse one codebase without exposing or mixing client information or authority.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for synthetic backend scoping; real-client storage and authentication remain deferred.
- **Evidence:** [tests/test_platform.py](../tests/test_platform.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** Second client
- **Dependencies:** AAOS-ARC-01.
- **Acceptance criteria:** Two clients in different periods have no cross-effects; denied object IDs/search/export/job references fail server-side; real-client storage uses validated per-client databases or a server store with enforced isolation/per-client credentials rather than assuming a scope column suffices.
- **Target stage:** Current synthetic controls; production isolation before real client records/G1 and hosted G2.
- **Trace:** U; ARCH; FABLE §11/T-27; PILOT. AT-58 in the original acceptance specifications (reference, not a claim of implementation).

### AAOS-ARC-03 — Central Supporting Strategies deployment

- **Description:** Support one centrally operated Accounting Agent OS deployment with isolated client workspaces and authorized firm management views.
- **Business purpose:** Operate multiple accounting clients without separate code forks or importing the unrelated SS agent system.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved product architecture; no hosted deployment implemented.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-02; AAOS-CTL-12; AAOS-CTL-13; AAOS-EXE-04.
- **Acceptance criteria:** A second client onboards using scoped configuration on the same release; administrators and managers have explicit access; workload, storage, cost and authorization boundaries survive concurrent clients; deployment has a named company authority/owner. Before G2, the platform owner records a concurrent-client workload test: at least two fictional client scopes execute simultaneously while cross-client reads, jobs, decisions and exports are denied and retained evidence remains isolated. Actual load/capacity targets require owner approval before production reliance.
- **Target stage:** Future / unassigned; hosting/readiness work before G2, separately authorized.
- **Trace:** U; LEGACY connection/release controls; FABLE §11.

### AAOS-ARC-04 — Optional independent client deployment

- **Description:** Allow a Bird Bowl or other client deployment from the same accounting codebase, containing only its authorized accounting modules/data and its own scoped configuration.
- **Business purpose:** Accommodate a client's hosting/support arrangement without creating a client-specific product fork or central-system dependency.
- **Priority:** Should
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved option; actual Bird Bowl host and support arrangement unselected.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Second client
- **Dependencies:** AAOS-ARC-01; AAOS-ARC-02; AAOS-ONB-01 if ratified for later client onboarding; AAOS-CTL-12; AAOS-CTL-13
- **Acceptance criteria:** Accounting can operate without an SS backlink; no SS executive/CRM/other-client data or shared credentials are preloaded; any later backlink names its purpose, exact data scope and authority.
- **Target stage:** Future / unassigned; separate hosting authorization and G2/G4 controls.
- **Trace:** U; PILOT deployment boundary; LEGACY §6E. AT-58 in the original acceptance specifications (reference, not a claim of implementation).

### AAOS-ARC-05 — Environment and release separation

- **Description:** Separate local, evaluation/sample, staging and production records, secrets, queues, budgets, grants, evidence and approvals; promote code/configuration through reviewed releases.
- **Business purpose:** Prevent demo identities, fixture policy or test authority from becoming operational permission.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred for hosted environments; local-only restrictions exist.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-02; AAOS-CTL-12.
- **Acceptance criteria:** Hosted startup rejects demo identity/insecure configuration; promotion does not copy live credentials, sample approval flags or enabled schedules; reviewed migrations and rollback preserve evidence/decisions/jobs and identify compatibility limits.
- **Target stage:** Before approved samples as applicable and any hosted G2 environment.
- **Trace:** LEGACY environments/release/rollback; FABLE §11/T-27; D-004/D-006.

## Autonomous accounting execution


### AAOS-EXE-01 — Durable progress and resumable work

- **Description:** Persist tasks, steps, dependencies, memory/checkpoints, current outcomes and historical evidence across application/worker restarts.
- **Business purpose:** Complete work across days without restarting from chat context or losing blocked work.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested in local synthetic SQLite workflows.
- **Evidence:** [tests/test_platform.py](../tests/test_platform.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-ARC-01; AAOS-ARC-02.
- **Acceptance criteria:** A restart resumes committed work without duplicate artifacts/effects; a blocker pauses dependent work while unrelated authorized work continues; run/step/exception status explains the next required action.
- **Target stage:** Current / G0; production recovery separately validated.
- **Trace:** ARCH; FABLE T-04/T-14; LEGACY durable workflow.

### AAOS-EXE-02 — Recurring occurrences and event wake-up

- **Description:** Separate each business occurrence from its execution attempts; support calendar/scheduled and evidence/dependency events with deduplication.
- **Business purpose:** Retry or resume legitimate routine work without double-processing or requiring a new user prompt.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested with a persisted simulated clock/events; no real scheduler active.
- **Evidence:** [tests/test_corrections.py](../tests/test_corrections.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-EXE-01; AAOS-CTL-04
- **Acceptance criteria:** One completed execution per occurrence; held work can redispatch after its prerequisites change; unfit mandates do not stop other clients/work; missed slots and catch-up policy are explicit; retries do not reset unfinished-work limits.
- **Target stage:** Current simulation; live triggers only after separate schedule/event authorization and hosted readiness.
- **Trace:** FABLE T-04/T-10; ARCH; LEGACY recurrence controls.

### AAOS-EXE-03 — Bounded standing authority

- **Description:** Use independently approved mandates naming workflow, client/environment, period selection, policy windows, fresh-evidence predicates, limits, expiry, review requirements and revocation.
- **Business purpose:** Permit routine authorized work autonomously while preserving consequential human decisions.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for synthetic mandates; real authority and grant lifecycle unconfigured.
- **Evidence:** [tests/test_acceptance_corrections.py](../tests/test_acceptance_corrections.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-EXE-01; AAOS-EXE-02; AAOS-BNK-03; AAOS-KNO-04; AAOS-CTL-01; AAOS-CTL-04; AAOS-CTL-03 for real authority only
- **Acceptance criteria:** Proposed/model-authored mandates confer no authority; stale/missing required evidence waits; a no-evidence exception needs an independent explicit reason; relevant policy change suspends for reconfirmation, unrelated/future changes do not; source arrival alone does not falsely change approved policy; expiry/revocation prevents further authorized dispatch.
- **Target stage:** Current / G0 controls; validated real mandates and separately authorized triggers before unattended operation/G4.
- **Trace:** T-10; RV-11; RA-05; EVIDENCE; PILOT.

### AAOS-EXE-04 — Hosted unattended operation

- **Description:** Run authorized scheduled/event-driven accounting work on persistent hosted infrastructure without the user's computer or active chat session.
- **Business purpose:** Make overnight work and continuing accounting execution dependable.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved product outcome; hosted runtime, schedules and monitoring are not implemented/activated.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-01; AAOS-EXE-02; AAOS-EXE-03; AAOS-EXE-05; AAOS-ARC-05; AAOS-CTL-02; AAOS-CTL-13; AAOS-OBS-03.
- **Acceptance criteria:** A witnessed run completes its authorized portion while the user's computer is off; work/evidence survive host restart; unavailable inputs/services produce durable exceptions; health, failure notification, backup/restore and stop controls operate within the agreed authority/cost ceiling.
- **Target stage:** Future / unassigned; authorized hosted G2 setup, separate schedule authority, observed G4 handoff.
- **Trace:** U; PILOT readiness; LEGACY hosting/durable work; FABLE T-24/T-27.

### AAOS-EXE-05 — Production retries, leases and monitoring

- **Description:** Classify transient failures versus deterministic accounting holds, persist bounded backoff, heartbeat/fence worker leases and keep the worker alive with observable health/errors.
- **Business purpose:** Avoid duplicate or silently abandoned work after faults and outages.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; local checkpoints/leases exist, production lifecycle guarantees do not.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-EXE-01; AAOS-EXE-02.
- **Acceptance criteria:** Transient retries retain counts/next wake; deterministic failures do not loop; a lease loser cannot commit; a failed job does not kill independent work; stalled work has a deterministic monitor and assigned escalation; recovery tests preserve one valid business result. The operating owner records heartbeat interval, lease expiry, retry limit and stalled-job alert deadline before G2; a controlled stopped-worker test must alert within that configured deadline and reject a stale worker commit. Missing parameters block live enablement.
- **Target stage:** Existing Batch 3 / T-24, not authorized; hosted validation before G2/G4.
- **Trace:** FABLE F-18/T-24; LEGACY failure/recovery tests.

### AAOS-EXE-06 — Pause, cancellation and operational controls

- **Description:** Provide distinct controls for pausing new work, stopping a run, disabling triggers/connectors and revoking authority/approvals, with durable reasons and truthful in-flight status.
- **Business purpose:** Let operators contain a failure or policy change without losing completed evidence or suggesting irreversible actions were undone.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; current local controls cover only parts of this operational set.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-03; AAOS-CTL-03; AAOS-INT-06.
- **Acceptance criteria:** Each control is independently tested; pending versus dispatched/unknown outcomes remain visible; cancellation cannot claim reversal of a completed external effect; independent unaffected authorized work may continue.
- **Target stage:** Future / unassigned; relevant controls required before hosted/live actions.
- **Trace:** LEGACY stop controls/uncertain outcomes; FABLE T-24; ARCH limits.

### AAOS-EXE-07 — Deterministic execution and optional model proposals

- **Description:** Declare each step deterministic, model-assisted or human. Keep math, rules, authority and supported connector execution in application-owned code; model output remains untrusted proposals.
- **Business purpose:** Support valid zero-model workflows and avoid making accounting execution depend on a subscription or model conversation.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for the current zero-model/no-egress path; model adapters and model evaluation deferred.
- **Evidence:** [tests/test_platform.py](../tests/test_platform.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-ARC-01; AAOS-KNO-04; AAOS-CTL-01; AAOS-CTL-12 for real data/credentials only
- **Acceptance criteria:** Deterministic approved paths run with outbound calls denied; missing model access cannot cause guessing or bypass a required model review; model requests pass trusted scope/schema/evidence/authority checks; model/critic output never becomes human approval.
- **Target stage:** Current deterministic foundation; any model integration requires later explicit scope/cost authorization.
- **Trace:** PILOT application/model roles; LEGACY §6E/10; ARCH; T-09/T-10. AT-59 in the original acceptance specifications (reference, not a claim of implementation).

## Accounting Knowledge & Policy Layer


### AAOS-KNO-01 — Applicable framework and reusable accounting knowledge

- **Description:** Represent applicable framework, basis, jurisdiction/entity/book and reusable accounting principles separately from client-specific treatments and workflows.
- **Business purpose:** Ground work in the right accounting context without declaring one client's treatment universal.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; framework/basis fact gates exist, a complete accounting knowledge service does not.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ARC-01; AAOS-ARC-02; AAOS-KNO-03.
- **Acceptance criteria:** Each applicable treatment identifies the governing client context; missing/conflicting framework/basis is held; reusable invariants are distinguished from professional judgment/client policy; no framework, threshold or tax conclusion is silently assigned to Bird Bowl or a new client. The accounting lead approves a versioned knowledge-classification artifact before G1 that tags each instruction as reusable invariant, client policy, proposed interpretation or reserved professional judgment, with source/effective context; an unclassified consequential treatment cannot activate.
- **Target stage:** Future / unassigned knowledge capability; actual facts required at G1.
- **Trace:** U; FABLE §7/8; ARCH; FABLE_ACCOUNTING_HANDOFF.md.

### AAOS-KNO-02 — Verified standards references

- **Description:** Maintain authoritative reference identity, edition/effective dates, applicable passage, verification date, reviewer and supporting evidence for standards-dependent treatments.
- **Business purpose:** Make accounting reasoning reviewable and prevent a model's remembered citation from becoming policy.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; no operational standards-reference verification service implemented.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-KNO-01; AAOS-KNO-04; AAOS-CTL-10.
- **Acceptance criteria:** The accounting lead verifies references against authoritative material and applicability before reliance; expired/conflicting/unverified references are visible and cannot silently activate a rule; reference changes trigger review of dependent treatments; access/licensing restrictions are respected.
- **Target stage:** Future / unassigned; before relying on standards-driven live treatment.
- **Trace:** U; FABLE §13 (review citations were not re-fetched); docs/SOURCES.md.

### AAOS-KNO-03 — Client facts, chart and operating profile

- **Description:** Store separate client identity, legal entities/books, chart/types/status, dimensions, vendors/customers, systems, procedures, contacts, policies and credential references with provenance and unknown fields.
- **Business purpose:** Onboard any client without rebuilding shared code or filling missing facts with plausible assumptions.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for scoped proposed profiles/required-fact gates and fictional chart/entity/book; full master-data onboarding deferred. Current schema requires a card_accounts key and one currency per profile; it does not yet provide a typed general account-role list. Remove that limit only with a later assigned banking capability, not this correction pass (PR-16).
- **Evidence:** [tests/test_batch2_controls.py](../tests/test_batch2_controls.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ARC-02.
- **Acceptance criteria:** Capability prerequisites identify required facts; actual client-sample work cannot waive missing facts into eligibility; synthetic waivers are explanatory/exported and cannot migrate to real profiles; chart/mapping/system facts require authorized validation.
- **Target stage:** Current fact gates; actual profile at G1, master-data/integration extensions later assigned.
- **Trace:** T-11; D-004; ARCH; PILOT; FABLE questions 1–7/10/12–16.

### AAOS-KNO-04 — Independently approved effective policies

- **Description:** Propose, independently approve, supersede/retire and load client policies, treatment rules, vendor mappings, receipt rules and procedure versions by effective window and relevant scope.
- **Business purpose:** Convert validated knowledge into controlled reusable execution without allowing a preparer/model to activate its own advice.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Independently verified
- **Scope note:** Independent Fable RB review verified the synthetic local preparation controls exercised by the named probes at the V2 checkpoint; no client policy, connected operation, reconciliation completion, close or operating readiness is verified.
- **Evidence:** [independent review](../exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d; R02a, R02b, N03a, N03b, N03c; retained A10, RN04, RN05, RN05b.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-CTL-01; AAOS-CTL-04.
- **Acceptance criteria:** Unapproved rules cannot code approvable work; aliases/normalization/collisions are visible before approval; withdrawn mappings stop applying in their effective scope; prior relevant authors/approvers remain contributors even after cosmetic or unlinked re-proposal; item-date and workflow relevance select the applicable versions. Relevant equivalent-rule authorship survives general-to-item scope changes and new rule keys; unrelated descriptions, categories, item scopes, policy values and clients do not bar an independent reviewer.
- **Target stage:** Current / G0; real policies separately validated/approved at G1.
- **Trace:** T-09/T-17; RV-05/RV-10/RV-14; RA-02; EVIDENCE.

### AAOS-KNO-05 — Decisions and scoped correction history

- **Description:** Preserve item-specific decisions, rationale, source support, approver, effective version, correction scope and superseded guidance separately from reusable approved rules.
- **Business purpose:** Learn from interventions without silently generalizing a one-off accounting judgment.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for local immutable decisions/dispositions and proposed-rule separation; complete client playbook capture not validated.
- **Evidence:** [tests/test_batch2_controls.py](../tests/test_batch2_controls.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-04; AAOS-CTL-06; AAOS-CTL-10.
- **Acceptance criteria:** Every correction states single-item versus reusable scope; history survives rejection/revocation/supersession; a proposed reusable rule does not resolve an exception or authorize itself; repeat work uses only the approved applicable guidance.
- **Target stage:** Current controls; client knowledge capture/validation at G1/G4.
- **Trace:** PILOT November/handoff; T-14; ARCH; CORRECTIONS.

### AAOS-KNO-06 — Portable operating knowledge and coverage

- **Description:** Export a maintained knowledge package with workflow inventory and task-coverage plan, approved procedures, checklists, mappings, examples, decisions, support scripts/templates, operator/support guides and separate validation cases/coverage gaps.
- **Business purpose:** Make knowledge durable across models, hosts, staff and client deployment choices.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; inspection JSON exports exist, trusted execution import/complete portable operating package does not.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04; AAOS-KNO-05; AAOS-CTL-10; AAOS-OBS-04.
- **Acceptance criteria:** A recipient can trace each procedure/example to approved evidence/version; teaching answers are separated from held-out cases; untested annual/unusual work has a human route; import cannot grant authority or cross client/environment boundaries; chats alone never count as validated training. The workflow inventory distinguishes staff-level and selected senior preparation tasks, automated coverage, work remaining manual, operator/reviewer ownership and source evidence required per task.
- **Target stage:** Future / unassigned portability work; per-client G1 validation and G4 handoff.
- **Trace:** PILOT portable handoff; LEGACY AT-60/AT-61; ARCH onboarding progression.

## Six accounting functions

| Accounting function | Current executable scope | Scope still deferred |
| --- | --- | --- |
| General Ledger | Fictional shared proposed entries and mechanical journal validation | General classification/adjustments, account maintenance, trial balances and ledger execution |
| Accounts Payable | No AP subledger handler; the card demonstration is not AP completion | Vendors/bills, payable aging, control-account ties and payment proposals/execution |
| Accounts Receivable | No AR handler | Customers/invoices, cash application, aging and collections |
| Banking & Reconciliation | Fictional card preparation, statement population checks and ordered source lifecycle | Full bank/card reconciliation, transfer pairing and cross-period matching |
| Month-End Close | Typed local readiness and immutable preparation-package finalization | Accounting completion validation, full close execution and separate human final sign-off |
| Financial Reporting & Analysis | Contracts only | Source-tied statements, management reports, variance analysis and insights |


### AAOS-GL-01 — Shared proposed-entry contract

- **Description:** Represent proposed accounting effects with entity/book, origin, period/date, currency, accounts, debit/credit lines, dimensions, rationale, rule/evidence references and review/external status.
- **Business purpose:** Let every module produce inspectable accounting effects through common validation rather than unrelated output formats.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for synthetic card/journal proposed entries; no live ledger state or posting.
- **Evidence:** [tests/test_batch2.py](../tests/test_batch2.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-KNO-03; AAOS-CTL-04; AAOS-CTL-05.
- **Acceptance criteria:** Entries balance exactly, use configured active accounts and identity, cannot reuse an economic source as another governing entry, and distinguish proposed/reviewed from externally posted; unsupported dimensions/currency remain held.
- **Target stage:** Current / G0; broader module use only as implemented/validated.
- **Trace:** T-15; RV-02/RV-07; ARCH; FABLE six-area matrix.

### AAOS-GL-02 — Journal mechanical validation

- **Description:** Validate journal line shape/balance, entity/book/period, account status, bound supporting documents, duplicate origins and nonzero economic effect.
- **Business purpose:** Catch mechanical errors before an independent accounting review.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for fictional journal preparation; mechanical validity does not establish correct recognition or tax treatment.
- **Evidence:** [tests/test_validation.py](../tests/test_validation.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-GL-01; AAOS-CTL-08; AAOS-CTL-01.
- **Acceptance criteria:** Reject negative/both-sided/zero lines, unbalanced or net-no-effect entries, unsupported accounts/dimensions, duplicate/source-revision claims and unrelated/unbound documents; a balanced but unsupported journal is ineligible; journal review never posts it.
- **Target stage:** Current / G0.
- **Trace:** T-16; FV-J08–FV-J10; RV-02; RA-07; ARCH.

### AAOS-GL-03 — Classification, adjustments and account maintenance

- **Description:** Progressively support general transaction classification, accruals, adjustments, reversals, account-maintenance proposals and authorized ledger execution under client-specific treatment rules.
- **Business purpose:** Cover routine GL staff/senior work beyond the card demonstration.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred beyond demonstrated card coding/journal checks; no general adjustment/account-maintenance/posting handler.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-GL-01; AAOS-GL-04; AAOS-KNO-01; AAOS-KNO-04; AAOS-INT-06.
- **Acceptance criteria:** Each added treatment has approved source/rationale/recognition/cutoff/dimension requirements and held-out expected results; reversals reference the originating accrual/period; material/unusual changes retain human judgment; any write has its own G3 gate. The accounting lead records materiality/unusual-treatment predicates in approved client rules before enabling that treatment; unset thresholds require human review rather than an inferred numeric default. Boundary and missing-policy tests demonstrate the route.
- **Target stage:** Future / unassigned, capability by capability; never implied complete by GL validation.
- **Trace:** U; ARCH GL/close contracts; FABLE questions 8–10; LEGACY accounting controls.

### AAOS-GL-04 — Trial-balance intake and rollforwards

- **Description:** Intake source-tied trial balances by entity/book/as-of/basis and validate balances, chart coverage and rollforwards; label projected balances separately from actual books.
- **Business purpose:** Supply dependable GL, subledger tie-out and reporting foundations.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; a checklist document label is not a validated trial balance.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-GL-01; AAOS-KNO-03; AAOS-CTL-10.
- **Acceptance criteria:** Balanced totals, known active accounts, date/basis/source provenance and movement ties are checked; reviewed unposted adjustments affect only an explicitly projected trial balance; missing/untied balances block dependent reports and control-account conclusions.
- **Target stage:** Existing Batch 3 / T-22, not authorized; real reporting waits for client facts and relevant gates.
- **Trace:** T-22; FV-RP01/FV-RP02; RA deferred enhancement DE-5; ARCH.

### AAOS-GL-05 — Exact money and currency contract

- **Description:** Use exact decimal arithmetic, validated currencies/minor units and explicit original/functional-currency support and FX evidence when implemented.
- **Business purpose:** Prevent rounding, sign, precision or currency mixing from creating incorrect accounting effects.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred for general currency support; tested decimal-string/two-decimal USD fixtures do not meet the universal contract.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04.
- **Acceptance criteria:** Reject floats/nonfinite/invalid precision and unsupported codes; distinguish currency-specific minor units; FX stays held without an approved method/rate/source/date; fixture sign conventions never become universal bank/provider conventions.
- **Target stage:** Existing Batch 3 / T-26, not authorized; broader FX treatments later assigned/validated.
- **Trace:** T-26; ARCH money limits; FABLE F-20; PILOT unknown policies.

### AAOS-GL-06 — Summary-source journal preparation

- **Description:** Prepare proposed summary journals from approved operating sources such as daily sales, payroll registers and tip summaries, with source totals, approved treatment and review.
- **Business purpose:** Provide shared accounting execution for operating summaries discovered during any client onboarding.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-KNO-04; AAOS-GL-01; AAOS-GL-05; AAOS-CTL-01; AAOS-CTL-08
- **Acceptance criteria:** Per-client source layouts and approved gross/net, liability/expense/tax/tip/clearing mappings govern a balanced journal and source-to-line tie-out. Test omissions, reversals, duplicate imports, changed totals, cutoff and missing treatment. Payroll execution, tax calculation/filing and payments remain separately reserved; preparing a journal does not perform them.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-09; future accounting preparation proposal; no client payroll/sales policy inferred.

### AAOS-AP-01 — Vendor, bill and expense preparation

- **Description:** Support scoped vendors, bills/credit memos/expenses, invoice/receiving evidence, terms, coding, approval and subledger-to-GL controls.
- **Business purpose:** Prepare complete and nonduplicative liabilities and payable workpapers.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; card expense preparation is not an implemented AP subledger.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-GL-01; AAOS-GL-04; AAOS-CTL-05; AAOS-CTL-08; AAOS-KNO-04.
- **Acceptance criteria:** Detect vendor/invoice-number variants and duplicates across routes/ledger; validate receiving/receipt requirements and credits under approved policy; version vendor changes; tie AP control balances to the verified ledger. Applicability, approval chain, receiving and terms are validated for each client before enabling the capability in its workspace.
- **Target stage:** Existing Batch 3 / T-23 synthetic specification first, not authorized; per-client AP facts and a new assignment are required before expanding beyond that specification.
- **Trace:** T-23; FV-AP01–FV-AP05; ARCH AP contract; FABLE §8/10.

### AAOS-AP-02 — Payable scheduling and payment controls

- **Description:** Support payable aging/due-date work and payment proposals with bank-instruction change verification and distinct preparation, approval and payment authority.
- **Business purpose:** Improve payable operations while protecting against fraudulent or duplicate disbursement.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; no payments or payment execution enabled.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-AP-01; AAOS-CTL-01; AAOS-CTL-03; AAOS-INT-06.
- **Acceptance criteria:** Current liability population/terms and independently verified bank changes govern proposals; amounts/recipients are explicit; payment execution is a separate reserved capability with its own approval/design/tests/authorization and is not granted by ordinary G3 writes or T-23.
- **Target stage:** Future / unassigned; payment capability explicitly outside current authorization.
- **Trace:** U; ARCH AP contract; FABLE T-23; LEGACY reserved actions.

### AAOS-AR-01 — Customer billing and invoice controls

- **Description:** Maintain scoped customers, authorized contracts/terms, service/sales evidence, invoices, credits and billing approvals.
- **Business purpose:** Prepare accurate, complete and timely receivables without inventing billable activity.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; no executable AR capability.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04; AAOS-GL-01; AAOS-GL-04; AAOS-CTL-08.
- **Acceptance criteria:** Verify existence/cutoff/accuracy and invoice uniqueness, customer and credit authority, source-to-ledger lineage and subledger control tie. Validate AR applicability and billing procedures for each client before enabling that workspace. Invoice execution requires its separately supported/approved operation.
- **Target stage:** Future / unassigned; per-client applicability and accounting facts precede AR implementation beyond design.
- **Trace:** U; ARCH AR contract; FABLE §8/10.

### AAOS-AR-02 — Cash application, aging and collection work

- **Description:** Match customer receipts, manage unapplied cash/disputes and produce reproducible aging and collection recommendations under approved terms.
- **Business purpose:** Keep balances/collections accurate and avoid double or excessive payment application.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-AR-01; AAOS-BNK-05; AAOS-GL-05.
- **Acceptance criteria:** Allocation cannot exceed receipt or invoice balances; ambiguous/short/overpayments and FX remain exceptions; aging has an explicit as-of date/policy and ties to the ledger; collection drafts never imply sending authority.
- **Target stage:** Future / unassigned; client fact and capability gates apply.
- **Trace:** U; ARCH AR contract; FABLE later-capability questions.

### AAOS-BNK-01 — Card preparation demonstration

- **Description:** Demonstrate intake, vendor identification, proposed coding, duplicate detection, supporting-document checks, exceptions/dispositions and independent review through the reusable engine.
- **Business purpose:** Validate shared accounting execution controls on a small executable workflow.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for fictional card data; not the entire product and not a live bank feed/ledger.
- **Evidence:** [tests/test_reviewer_cases.py](../tests/test_reviewer_cases.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-04; AAOS-GL-01; AAOS-CTL-01; AAOS-CTL-05; AAOS-CTL-08; AAOS-BNK-02; AAOS-BNK-03.
- **Acceptance criteria:** Unknown/ambiguous vendors never receive clean approvable coding; pending, unsupported currency, missing/changed evidence and material unsupported treatments stay held; demonstrated dispositions are evidence-bound and re-preparation still needs review; approval does not post an expense.
- **Target stage:** Current / G0; approved client samples only under G1.
- **Trace:** T-02/T-13/T-14/T-15/T-17; CORRECTIONS; EVIDENCE.

### AAOS-BNK-02 — Statement-based population completeness

- **Description:** Validate posted transaction populations against independently supplied statement balances/activity/counts/line IDs and available continuity/provenance.
- **Business purpose:** Detect omissions and substitutions that internally generated totals cannot reveal.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Independently verified
- **Scope note:** Independent Fable RB review verified the synthetic local preparation controls exercised by the named probes at the V2 checkpoint; no client policy, connected operation, reconciliation completion, close or operating readiness is verified. UC-11: a restated prior statement with zero card activity has no item-bound acceptance route; the next period stays unverified.
- **Evidence:** [independent review](../exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d; R04a, R04b, R04c, N02b, N04a, N04b, N04c, N04d.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-BNK-03; AAOS-CTL-08; AAOS-CTL-09; AAOS-CTL-04
- **Acceptance criteria:** Check opening/activity/closing arithmetic and identity/population ties; disclose missing line identity, continuity or provenance checks; do not manufacture a statement from the population; corrected/replaced statements remain held until valid acceptance. A revision of the lookback statement is disclosed to every period relying on it, with continuity unverified until its own-period revision acceptances are active. Re-pointing the old key to another cycle cannot bypass replacement disclosure/acceptance.
- **Target stage:** Current / G0; provider/account authority and real statement validation at G1/G2.
- **Trace:** T-13; RV-13; RA-04; EVIDENCE.

### AAOS-BNK-03 — Ordered source lifecycle and one economic item

- **Description:** Retain source IDs/versions, ordering, pending-to-posted links, removals, supersession, quarantines and current heads without rewriting raw history.
- **Business purpose:** Avoid double counting or losing charges when providers revise, replace, remove or redeliver data.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Verification failed
- **Scope note:** Independent Fable RD review accepted RD-01/RD-02 and PRV-11–PRV-13 at checkpoint 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; RB-01 remains not accepted for RE-01/RE-02 (E03/E06). The owner subsequently approved D-026, superseding latest-target-wins and adding RE-03 no-release/authorized-selection controls. This record stays Verification failed for RE-01 to RE-03 until independent verification of the D-026 clauses, the 12 unmodified RD probes, the explicitly adapted Y05(a), all 336 orders and retained gates on the new checkpoint. D-029 resolves the frozen-period question: preserve the already frozen approval and block the incoming version until authorized reopen; then the contested-claim blocker still requires an authorized disposition. The clarification and developer probe are recorded in docs/corrections_re/CONTRACT_CLARIFICATION.md. Developer repairs confer no readiness or operating authority.
- **Evidence:** [independent review](../exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; Y01–Y06, X01/X01d/X02 and 120 orders accepted RD-01/RD-02; E03/E06 WEAK and 24/336 double in the independent run. RE-03 is the subsequent owner contract assignment (D-026), not an independently reviewed correction. [tests/test_feed_contract.py](../tests/test_feed_contract.py), the unchanged RD probes/search, [Y05(a) adaptation](../docs/corrections_re/Y05-contract.patch) and corrections_re/ are developer repair evidence only. Independent RE-01/RE-02/RE-03 acceptance pending.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-CTL-04; AAOS-CTL-05; AAOS-CTL-10.
- **Acceptance criteria:** Older/conflicting events do not overwrite newer heads; supersession chains cannot release a locked-origin charge into a second approved period; cycles refuse atomically; authorized reopen admits only the terminal replacement and retires predecessors/support with traceable history; removing a superseder does not silently restore an ancestor without an approved feed policy. These controls must hold for every delivery order within the feed contract of D-026, including a link declared on a source already admitted to another period and an unresolved link resolved later; no same-period source-move rows are created. This includes an ancestor withdrawn after the lock, a link declared on a source whose replacement is already admitted, and an unresolved claim whose target arrives without the claimant being re-sent. Any prior transition acceptance lapses when the resolved chain changes; reopening admits only the terminal source with a fresh transition hold. This also holds including a claim declared by re-sending an unchanged row before its target arrives, and a claimant revised or re-sent without its claim while the claim is unresolved. Recording a newly declared claim immediately adds both transition blockers and ends any earlier open-period governing approval before its target arrives; D-029 preserves an approval already frozen in its own period while blocking the incoming version until authorized reopen; repeating that unresolved claim is a source-lifecycle no-op. Claims persist by identity; self-supersession and cycle refusals stay atomic. A second different target is recorded without applying it or moving the claimant, whether the first claim is linked or pending; further different targets join the open question. Only a recorded authorized non-supplier disposition naming a declared target with supporting evidence may resolve that question; identical repeats add no source lifecycle rows. The highest provider order governs row data while a claim on an older or conflicting retained message is still recorded.
- **Target stage:** Current / G0; actual pending/removal/restoration semantics verified at G2.
- **Trace:** T-12; C-01; RV-01/RV-02/RV-03/RV-04; RA-01; U4/UC-4.

### AAOS-BNK-04 — Reconciliation workpapers

- **Description:** Prepare bank/card reconciliations from authoritative statements, ledger populations, prior reconciliations, proposed adjustments and reconciling items.
- **Business purpose:** Establish reproducible evidence that balances and populations reconcile, rather than treating equal totals as sufficient.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; current completeness checks are not full reconciliation.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-BNK-02; AAOS-GL-01; AAOS-CLS-02; AAOS-KNO-04.
- **Acceptance criteria:** Show opening/activity/closing, source/ledger completeness, reviewed/unreviewed/held entries, timing items and differences; separate actual from projected balances; unposted adjustments cannot confer externally reconciled status even at zero projected difference.
- **Target stage:** Existing Batch 3 / T-20 for card workpaper, not authorized; broader banking reconciliation later assigned.
- **Trace:** T-20; FV-BK01/FV-BK05; ARCH; LEGACY fictional close controls. AT-24, AT-25 in the original acceptance specifications (reference, not a claim of implementation).

### AAOS-BNK-05 — Matching, transfers and settlements

- **Description:** Match economic counterpart legs across bank/card/ledger feeds with one-use allocations, transfer/transit/settlement evidence and client-approved date/currency/account rules.
- **Business purpose:** Avoid expensing card settlements or recording the same economic event through multiple routes/periods.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred beyond demonstrated single-item settlement dispositions; cross-period ledger/source duplicate matching not complete.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-BNK-04; AAOS-GL-01; AAOS-CTL-05; AAOS-KNO-04.
- **Acceptance criteria:** Enforce opposite amount/direction and verified identities; ambiguous counterparts and in-transit period-end items stay held; matched legs cannot be reused; duplicate economic origin checks span relevant periods/routes; no date tolerance is invented.
- **Target stage:** Existing Batch 3 / T-21, not authorized; broader matching after validated workpapers/policies.
- **Trace:** T-21; FV-BK02–FV-BK04; RV/RA deferred enhancement DE-3; ARCH. AT-24, AT-25 in the original acceptance specifications (reference, not a claim of implementation).

### AAOS-BNK-06 — Statement cycles and receipt aggregation

- **Description:** Accommodate approved non-calendar statement cycles/cutoff and multiple/partial document allocation policies without weakening accounting-period or completeness controls.
- **Business purpose:** Extend beyond the demo's calendar-cycle/exact whole-charge receipt assumptions.
- **Priority:** Should
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; current statements must match periods, and allowed multiple receipts are each compared with the whole charge.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-BNK-02; AAOS-CTL-04; AAOS-CTL-08; AAOS-KNO-04.
- **Acceptance criteria:** Explicit client cutoff/date and allocation rules govern membership; allocations sum correctly without double-use; partial/aggregate support is distinguishable from a mismatch; held-out cross-month cases and missing-policy holds are tested before support is claimed.
- **Target stage:** Future / unassigned, after client policy validation; not silently added to current corrections.
- **Trace:** FABLE questions 4/5/9; RV/RA deferred enhancements DE-2/DE-4.

### AAOS-BNK-07 — Deposit and merchant-settlement matching

- **Description:** Match sales/receipt summaries, merchant settlements, fees/withholdings and bank deposits under approved client procedures with timing and one-use allocation controls.
- **Business purpose:** Reconcile gross operating activity to net cash without netting away unsupported revenue or liabilities.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-BNK-05; AAOS-GL-01; AAOS-KNO-04; AAOS-CTL-08
- **Acceptance criteria:** A per-client workpaper ties source sales/receipts to settlement and deposit identities, gross/fees/withholdings/net amounts and timing; exact allocations prevent re-use and duplicate posting; missing/ambiguous/partial/late settlements remain exceptions; no treatment or tolerance is inferred from a bank description.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-09; shared future execution for deposit/settlement discovery, not a card-feed-only function.

### AAOS-CLS-01 — Typed close-readiness outcomes

- **Description:** Evaluate versioned close prerequisites against actual workflow outcomes and period/account-bound evidence, exposing stale/disputed/held/unreviewed/external work.
- **Business purpose:** Make close status reflect accounting completion evidence instead of filenames or elapsed dates.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for typed local readiness and preserved external/final-signoff holds; full accounting completion validation deferred.
- **Evidence:** [tests/test_reverification_controls.py](../tests/test_reverification_controls.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-EXE-01; AAOS-CTL-04; AAOS-CTL-06; AAOS-CLS-02.
- **Acceptance criteria:** A document label cannot satisfy a typed reconciliation/tie-out; deferred capabilities stay unsatisfied; original untyped requirements are not silently upgraded; trial-balance/statement document placeholders must be replaced with validated workflow/tie-out requirements when those capabilities exist.
- **Target stage:** Current / G0; strengthen checklist bindings as existing T-20/T-22 and later modules are authorized.
- **Trace:** T-19; RV-06; RA DE-5; ARCH.

### AAOS-CLS-02 — Immutable preparation-package finalization

- **Description:** Finalize a versioned reviewed preparation package with governing content/hashes, decisions, contributor lineage, dispositions, controls, acknowledged unresolved items and audit reference.
- **Business purpose:** Hand over a stable accounting review record without erasing later changes or pretending the books are closed.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Developer tests cover immutable synthetic handover, supersession links and post-finalization change reporting. The complete seven-element accounting-close package and external accounting-completion validation remain future scope; no real close is certified.
- **Evidence:** [tests/test_synthetic_month.py](../tests/test_synthetic_month.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-CTL-06; AAOS-CTL-07; AAOS-CTL-10; AAOS-CTL-01.
- **Acceptance criteria:** Refuse disputed/stale/unacknowledged blocked work; carried items/removals are explicit; retain immutable earlier package bytes with prior-version links; later changes raise a visible change event; finalization does not post, reconcile or confer final-close sign-off. The preparation package contains, where applicable, these seven elements: Client/entity/book identity and accounting-system company ID; expected source inventory/completeness; relevant reconciliations/supporting schedules; proposed adjustments with lines/rationale/support/disposition; exceptions and blocked external steps; draft client questions; checklist/review completion with a separate final-close status. Unavailable elements are named as missing/manual; a placeholder does not prove their accounting completion.
- **Target stage:** Current / G0; client preparation handoff under G1/G4 as authorized.
- **Trace:** T-18; RV-03/RV-17; EVIDENCE; ARCH.

### AAOS-CLS-03 — Full month-end close execution

- **Description:** Execute the client close DAG: reconciliations, subledger ties, accruals/reversals, adjustments, reviews, verified external steps, period lock and separately assigned final human sign-off.
- **Business purpose:** Deliver a complete, evidenced close within actual client procedures and authority.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; close readiness and preparation finalization are only foundations.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-GL-03; AAOS-GL-04; AAOS-BNK-04; AAOS-CLS-01; AAOS-KNO-04; AAOS-AP-01 and AAOS-AR-01 where applicable to the client's books.
- **Acceptance criteria:** Approved checklist names applicable/missing/manual tasks and accountable reviewers; balances and required reconciliation/posting results are verified rather than inferred from prepared work; late/annual/unusual items route explicitly; calendar changes never complete the close; human final sign-off remains distinct. The complete close package has seven elements: Client/entity/book identity and accounting-system company ID; expected source inventory/completeness; relevant reconciliations/supporting schedules; proposed adjustments with lines/rationale/support/disposition; exceptions and blocked external steps; draft client questions; checklist/review completion with a separate final-close status. Track five distinct states with separate evidence: workpaper prepared; proposed adjustment reviewed; external posting verified; accounting-system reconciliation completed; final human close sign-off. None implies another.
- **Target stage:** Future / unassigned, progressively validated per client and capability; G4 only for demonstrated scope.
- **Trace:** U; ARCH close contract; PILOT December close; FABLE question 13; LEGACY §6E.

### AAOS-RPT-01 — Financial statements and management reports

- **Description:** Produce source-tied statements and management reports by approved entity/book/basis/period, report mapping and comparative definitions.
- **Business purpose:** Turn validated accounting records into dependable financial information.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No statement-generation handler. Consolidation/intercompany scope is tracked separately as proposed AAOS-RPT-03, not hidden inside this deferred requirement.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-GL-04; AAOS-CLS-01; AAOS-KNO-04; AAOS-GL-05.
- **Acceptance criteria:** Reports tie to the authoritative trial balance, satisfy balance/movement/rollforward checks, preserve mapping/comparative/rounding provenance and disclose missing scope/dimensions; projected adjustments never appear as actual results; unsupported consolidation/eliminations stay unavailable.
- **Target stage:** Future / unassigned; Fable question 14, T-22 and accepted accounting inputs precede reporting implementation.
- **Trace:** U; ARCH reporting contract; FABLE FV-RP01/FV-RP02/question 14; original Fable handoff.

### AAOS-RPT-02 — Variance analysis and accounting insights

- **Description:** Calculate reproducible variances and prepare evidence-linked explanations/insights under reviewed management definitions.
- **Business purpose:** Support senior-accountant analysis without turning plausible model narratives into financial facts.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-RPT-01; AAOS-EXE-07; AAOS-KNO-04.
- **Acceptance criteria:** Period/basis/denominator and comparative versions are explicit; distinguish measured variance, hypothesis and approved explanation; missing comparatives/causal evidence are disclosed; human review precedes reliance on material interpretations; no invented forecast or business facts.
- **Target stage:** Future / unassigned; after verified reporting inputs and client definitions.
- **Trace:** U; ARCH reporting contract; FABLE question 14.

### AAOS-RPT-03 — Consolidation and intercompany reporting

- **Description:** If ratified and applicable, support group/entity ownership, intercompany balances, eliminations and consolidated reporting under approved accounting policies.
- **Business purpose:** Track the proposed extension separately rather than hiding it inside a deferred statements requirement.
- **Priority:** Could
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-RPT-01; AAOS-GL-04; AAOS-GL-05; AAOS-KNO-04
- **Acceptance criteria:** Before enablement, the accounting authority approves group perimeter, ownership/effective dates, reporting basis/currency, intercompany counterpart identities and elimination rules. Separate-versus-consolidated balances and elimination workpapers tie to source books; unsupported scope, FX or missing counterpart balances remain held. No client is presumed to need consolidation.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-09; original Fable handoff cross-cycle question; proposed, not accepted client scope.

## Document and system integrations


### AAOS-INT-01 — QuickBooks Online integration

- **Description:** Add application-owned adapters for individually verified authorized QBO reads, reports, records and attachments, with later separately authorized writes.
- **Business purpose:** Connect preparation to the actual book of record without confusing ledger APIs with bank-feed UI actions.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No live ledger connector, external company identity or per-client migration/book-of-record readiness is confirmed; provider capabilities and authority must be verified for each workspace.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-KNO-03; AAOS-CTL-02; AAOS-CTL-12; AAOS-INT-06 for later writes only; AAOS-INT-07 if ratified
- **Acceptance criteria:** Confirm ledger edition/conversion and realm; verify each operation against current official documentation/entitlements in an isolated environment; unsupported pending-feed/reconciled-status operations remain unavailable/manual; supported reads never imply write authority or a private-endpoint workaround.
- **Target stage:** Future / unassigned; G2 named reads, G3 each specified write.
- **Trace:** U; PILOT first test/intake; LEGACY accounting integration constraints; FABLE question 15.

### AAOS-INT-02 — Bill.com integration

- **Description:** Support authorized BILL/Bill.com document, vendor, bill and status flows through individually verified provider capabilities.
- **Business purpose:** Incorporate client payable workflows without duplicating liabilities or bypassing approval/payment controls.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No adapter or live access implemented; per-client capabilities/entitlements and scope/cost authorization remain unverified. Named vendors are instances of the proposed shared connector contract.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-AP-01 for accounting preparation; AAOS-CTL-12; AAOS-KNO-03; AAOS-INT-06 for later writes only; AAOS-INT-07 if ratified
- **Acceptance criteria:** Verify named read/attachment/status operations and provider-to-ledger identities; identify the one accounting/posting route; preserve vendor/bank changes and audit provenance; any write/payment requires its distinct authority and capability, never assumed from read access.
- **Target stage:** Future / unassigned; G2 reads and separately authorized later operations.
- **Trace:** U; LEGACY accounting systems connection packet; ARCH AP contract.

### AAOS-INT-03 — Google Workspace and Gmail

- **Description:** Intake authorized accounting messages/attachments and relevant Workspace records through scoped access with source, thread, document and permission lineage.
- **Business purpose:** Recover accounting evidence and waiting-on-others context without exposing unrelated client/company mail.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No adapter or live access implemented; per-client capabilities/entitlements and scope/cost authorization remain unverified. Named vendors are instances of the proposed shared connector contract.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-12; AAOS-CTL-08; AAOS-COM-02 for any later sending only; AAOS-INT-07 if ratified
- **Acceptance criteria:** Named mailbox/folder/document permissions and retention govern reads; replayed attachments remain identifiable; instructions in email cannot change authority or destinations; reading a thread never grants sending permission.
- **Target stage:** Future / unassigned; G2 named reads, separate communication permissions for any sending.
- **Trace:** U; LEGACY trusted-tool/data-protection controls; ARCH evidence contracts.

### AAOS-INT-04 — Google Drive and document repository

- **Description:** Retrieve and organize authorized accounting documents and approved operating knowledge with file/version identity, access provenance and stable evidence references.
- **Business purpose:** Keep receipts, statements, workpapers and procedures retrievable without depending on chat attachments or local folders.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No adapter or live access implemented; per-client capabilities/entitlements and scope/cost authorization remain unverified. Named vendors are instances of the proposed shared connector contract.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-KNO-06; AAOS-CTL-08; AAOS-CTL-09; AAOS-CTL-12; AAOS-CTL-13; AAOS-INT-07 if ratified
- **Acceptance criteria:** Scope folders/files per client and environment; detect revisions/removals/access loss without rewriting earlier evidence; copied/moved documents retain provenance; repository access does not approve accounting treatment; document writes/deletions need separate permission.
- **Target stage:** Future / unassigned; G2 authorized retrieval before reliance.
- **Trace:** U; PILOT portable knowledge; LEGACY evidence/storage/retention.

### AAOS-INT-05 — Bank activity, statements and authorized portals

- **Description:** Support complete bank/card activity and statement intake from approved exports, direct/aggregator/provider routes or specifically authorized portal integration where permitted.
- **Business purpose:** Obtain the right source population without assuming card-only coverage or unsupported banking capabilities.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** No adapter or live access implemented; per-client capabilities/entitlements and scope/cost authorization remain unverified. Named vendors are instances of the proposed shared connector contract.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-BNK-02; AAOS-BNK-03; AAOS-CTL-12; AAOS-INT-06 for later writes only; AAOS-INT-07 if ratified
- **Acceptance criteria:** Verify complete checking versus card-only coverage and account types for each client; compare permitted direct, aggregator, application-native and export routes without presuming provider selection. Designate one posting route per transaction, document pending/removal/sign semantics and approved clearing treatment. Portal use needs permitted access and validated controls; no authentication/provider restriction bypass.
- **Target stage:** Future / unassigned; G1 authorized local exports, G2 separately authorized reads/portals.
- **Trace:** U; PILOT unresolved transaction-intake choice; LEGACY connection packet; FABLE questions 2/4/15.

### AAOS-INT-06 — Safe external execution and unknown outcomes

- **Description:** Gate each external effect with supported capability, current scope/approval/preconditions, durable business intent/operation ID, provider idempotency where available and verified outcome.
- **Business purpose:** Prevent duplicate accounting effects and false completion after a crash, timeout or permission change.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; no external write paths exist.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G3 specified writes
- **Dependencies:** AAOS-CTL-01; AAOS-CTL-03; AAOS-CTL-04; AAOS-CTL-05; AAOS-EXE-05.
- **Acceptance criteria:** Recheck exact payload and authority immediately before dispatch; a possibly completed write becomes outcome_unknown until readback/reconciliation or human resolution; no blind resubmission or claim that queue leases alone guarantee exactly-once provider effects; revoke/denial/changed-input/fault tests pass per operation.
- **Target stage:** Future / unassigned; G3 named writes only; payment, sending and final close remain separately reserved.
- **Trace:** FABLE G3; ARCH live effects; LEGACY §12/AT external-write controls. AT-29, AT-40 in the original acceptance specifications (reference, not a claim of implementation).

### AAOS-INT-07 — Vendor-neutral connector contract

- **Description:** Define a shared contract for scoped read/event/document adapters and separately authorized effects, selected by each client profile.
- **Business purpose:** Support another ledger, mail repository or bank source without changing core accounting requirements or claiming unsupported operations.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Second client
- **Dependencies:** AAOS-KNO-03; AAOS-CTL-10; AAOS-CTL-12; AAOS-EXE-01
- **Acceptance criteria:** Each connector declares verified supported read/report/attachment/event operations and explicit unsupported operations, authentication/secret references, entity/account scopes, raw/source identity and provenance, ordering/pending/removal semantics, pagination/rate/freshness limits and failure behavior. The client profile selects adapters. Describe and test two fictional adapters of the same kind behind the unchanged contract; each actual read or effect still needs capability verification and separate access/authority.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-08; existing application-owned adapters and universal-platform direction; proposed contract details await ratification.

## Accounting safety, quality and security


### AAOS-CTL-01 — Genuine independent review and segregation of duties

- **Description:** Require a separately authorized human independent of all relevant preparation/configuration/evidence roles for exact-version review and distinct controlled decisions.
- **Business purpose:** Prevent self-review or laundering authorship through reruns, cosmetic configuration changes or replacement evidence.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Independently verified
- **Scope note:** Independent Fable RB review verified the synthetic local preparation controls exercised by the named probes at the V2 checkpoint; no client policy, connected operation, reconciliation completion, close or operating readiness is verified.
- **Evidence:** [independent review](../exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d; R02a, R02b, N03a, N03b, N04a.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-06; AAOS-CTL-03 for real authority only
- **Acceptance criteria:** Include relevant enqueuer, worker, mandate issuer, historical evidence suppliers, rule/profile authors/approvers and disposition actors; identity names do not imply kind; cosmetic/unlinked equivalent rules retain relevant authors; revised-evidence acceptance excludes old/current suppliers and remains separate from final review; unrelated contributors do not create false barriers. Equivalent approved semantic rules retain relevant authors across renamed keys and general-to-item coverage changes; prior-statement acceptance actors are contributors when their acceptance is consumed for continuity.
- **Target stage:** Current / G0 controls; validated actual roles/grants before G1.
- **Trace:** T-03; C-03/C-04/C-06; RV-10/RV-12; RA-02/RA-03/RA-04; EVIDENCE.

### AAOS-CTL-02 — Authenticated identity and bounded access

- **Description:** Replace demo role selection with verified identity, membership, kind and scoped capabilities; use bounded/paged filtered backend reads and exports.
- **Business purpose:** Make multi-user/client operation secure and usable beyond fixture volumes.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; current loopback role selector is a test harness, not authentication.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-KNO-04.
- **Acceptance criteria:** A verified provider maps identities to server-side grants; hosted/second-user access rejects demo auth and unauthorized object/client references; cached views/manifests remain current on relevant generations; no giant unfiltered response leaks or substitutes for authorization.
- **Target stage:** Existing Batch 3 / T-27, not authorized; required before actual sample identity or non-loopback use as applicable.
- **Trace:** T-27; FABLE §11; LEGACY identity; ARCH limits.

### AAOS-CTL-03 — Authority-grant lifecycle

- **Description:** Define who may grant, change and revoke each scoped preparation/policy/review/disposition/finalization/period/operating authority, including administrator independence and emergency suspension.
- **Business purpose:** Prevent self-issued, obsolete or overbroad human/service permissions from becoming real accounting authority.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred for actual grants; synthetic fixtures have no full grant-revocation/admin-independence lifecycle.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ARC-02; AAOS-KNO-03.
- **Acceptance criteria:** Approved role matrix, independent grant administration, expiry/revocation and audit records exist; revoked grants stop future decisions/dispatch without rewriting history; no model can grant itself authority; real client configuration cannot rely on fixture grants.
- **Target stage:** Before G1 actual identities/authority; implementation unassigned, UC-5 remains open for that gate.
- **Trace:** RA UC-5; FABLE question 6/§7; LEGACY approval policy; CONNECTION_READINESS.md.

### AAOS-CTL-04 — Durable periods, cutoff and locks

- **Description:** Maintain accounting periods and independent open/lock/reopen history; bind source/run/entry/decision membership to approved period/cutoff rules.
- **Business purpose:** Prevent decisions or duplicate approvals across locked periods while retaining late evidence.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Verification failed
- **Scope note:** Independent Fable RD review accepted RD-01/RD-02 and PRV-11–PRV-13 at checkpoint 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; RB-01 remains not accepted for RE-01/RE-02 (E03/E06). The owner subsequently approved D-026, superseding latest-target-wins and adding RE-03 no-release/authorized-selection controls. This record stays Verification failed for RE-01 to RE-03 until independent verification of the D-026 clauses, the 12 unmodified RD probes, the explicitly adapted Y05(a), all 336 orders and retained gates on the new checkpoint. D-029 resolves the frozen-period question: preserve the already frozen approval and block the incoming version until authorized reopen; then the contested-claim blocker still requires an authorized disposition. The clarification and developer probe are recorded in docs/corrections_re/CONTRACT_CLARIFICATION.md. Developer repairs confer no readiness or operating authority.
- **Evidence:** [independent review](../exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9; Y01–Y06, X01/X01d/X02 and 120 orders accepted RD-01/RD-02; E03/E06 WEAK and 24/336 double in the independent run. RE-03 is the subsequent owner contract assignment (D-026), not an independently reviewed correction. [tests/test_feed_contract.py](../tests/test_feed_contract.py), the unchanged RD probes/search, [Y05(a) adaptation](../docs/corrections_re/Y05-contract.patch) and corrections_re/ are developer repair evidence only. Independent RE-01/RE-02/RE-03 acceptance pending.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-03 before G1 real authority only
- **Acceptance criteria:** Every review transition, including revoke/resolution, refuses a locked period; lock preserves approved/finalized evidence; late/unassigned/moved sources quarantine; independent audited reopen precedes admission; a replacement chain never leaves the same expense approved in two periods; destination revisions after a valid release use the nearest admitted owner. The prohibition holds for every delivery order within the feed contract of D-026, including a link declared after destination admission/approval and an unresolved link resolved later; affected destination approval ceases governing and an approved-source event names it. This includes an ancestor withdrawn after the lock, a link declared on a source whose replacement is already admitted, and an unresolved claim whose target arrives without the claimant being re-sent. Any prior transition acceptance lapses when the resolved chain changes; reopening admits only the terminal source with a fresh transition hold. This also holds including a claim declared by re-sending an unchanged row before its target arrives, and a claimant revised or re-sent without its claim while the claim is unresolved. Recording a newly declared claim immediately adds both transition blockers and ends any earlier open-period governing approval before its target arrives; D-029 preserves an approval already frozen in its own period while blocking the incoming version until authorized reopen; repeating that unresolved claim is a source-lifecycle no-op. Claims persist by identity; self-supersession and cycle refusals stay atomic. A second different target is recorded without applying it or moving the claimant, whether the first claim is linked or pending; further different targets join the open question. Only a recorded authorized non-supplier disposition naming a declared target with supporting evidence may resolve that question; identical repeats add no source lifecycle rows. The highest provider order governs row data while a claim on an older or conflicting retained message is still recorded. Provider messages alone never release a locked-period hold. Release requires an authorized reopen or an authorized target disposition by the same person holding both disposition and lock authority; reopen does not clear a contested-claim blocker. Selecting a target never approves the item.
- **Target stage:** Current / G0; actual cutoff/cycle and reopen policy at G1 before client use.
- **Trace:** T-05; C-01/C-02; RV-01/RV-04; RA-01 and relock regression; FABLE questions 4/9.

### AAOS-CTL-05 — Vendor identity and duplicate prevention

- **Description:** Preserve raw descriptors while using Unicode-safe normalized candidate identity and economic-source/duplicate controls across intake, preparation, entries and dispositions.
- **Business purpose:** Avoid false vendor matches, repeated expenses and removal of legitimate repeated purchases.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for current Unicode/ambiguity, idempotent replay and same-period economic-source/disposition controls; full cross-period matching deferred to AAOS-BNK-05.
- **Evidence:** [tests/test_acceptance_corrections.py](../tests/test_acceptance_corrections.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-KNO-04.
- **Acceptance criteria:** NFKC/casefold retains letters/numbers/combining marks; empty aliases cannot match; ambiguity withholds clean coding; duplicate candidates stay visible, not auto-deleted; new candidate/evidence changes lapse dependent dispositions; duplicate/replay targets must remain live and cannot mutually exclude all entries, including before re-preparation.
- **Target stage:** Current / G0; cross-route/period expansion under existing T-21 and future validated modules.
- **Trace:** T-02; C-05; RV-02/RV-08/RV-09; RA-08; EVIDENCE.

### AAOS-CTL-06 — Governing artifacts and decision integrity

- **Description:** Maintain one governing preparation per workflow/period/item with immutable prior artifacts, linked runs/contributors and append-only approval/rejection/dispute/revocation/resolution history.
- **Business purpose:** Prevent reruns or altered provenance from displacing a valid rejection or creating multiple competing approved preparations.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for synthetic governing membership, reuse and decision state machine.
- **Evidence:** [tests/test_corrections.py](../tests/test_corrections.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-EXE-01; AAOS-CTL-10.
- **Acceptance criteria:** Identical content retains decisions while accumulating contributors; noncurrent artifacts cannot receive decisions; conflicts are disputed rather than last-write-wins; independent resolution is explicit; removed/moved items leave current membership but retain auditable history; package supersession is explicit.
- **Target stage:** Current / G0; exact-version review preserved in later modules.
- **Trace:** T-07; C-03; RV-03/RV-17; EVIDENCE.

### AAOS-CTL-07 — Relevant dependency invalidation

- **Description:** Record declared source/policy/code dependencies and invalidate only affected work/authority, preserving unrelated client/workflow/period approvals.
- **Business purpose:** Keep accounting controls sound while reducing avoidable repeat reviews and interruptions.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested at workflow/period population granularity; per-item invalidation optimization deferred.
- **Evidence:** [tests/test_batch2_controls.py](../tests/test_batch2_controls.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-ARC-01; AAOS-KNO-04; AAOS-CTL-06.
- **Acceptance criteria:** Relevant changed content/policy expires affected approval/disposition; unrelated workflow/client/period or UI/transport edits do not; finalized bytes remain stable; relevant semantic policy windows govern mandates independently of evidence arrival; finer invalidation must preserve duplicate/population dependencies.
- **Target stage:** Current / G0; per-item efficiency improvement future / unassigned (DE-1).
- **Trace:** T-06; T-10; RA-05; RV/RA DE-1; ARCH. This supersedes D-005's original blanket-invalidation wording for current behavior.

### AAOS-CTL-08 — Source traceability and document completeness

- **Description:** Bind each item/treatment to relevant authenticatable source/document identity, version/hash, supplier, time, account/period and approved completeness/matching policy.
- **Business purpose:** Ensure accounting preparation has inspectable support rather than arbitrary files or matching labels.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for structured fictional support and explicit unset matching policy; OCR/authenticity/general document extraction unimplemented.
- **Evidence:** [tests/test_acceptance_corrections.py](../tests/test_acceptance_corrections.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04; AAOS-CTL-10.
- **Acceptance criteria:** Missing/irrelevant/unsupported documents block affected work; a transaction row cannot be supporting evidence; cards use related receipts/account-cycle statements and journals named bound support; duplicate decisions cite each candidate's relevant evidence; no amount/date tolerance or statement substitution is invented when policy is unset.
- **Target stage:** Current / G0; real evidence acceptance and document policy at G1, adapters at G2.
- **Trace:** T-16/T-17; RV-15; RA-06/RA-07; FABLE question 5; ARCH.

### AAOS-CTL-09 — Revised or replacement evidence acceptance

- **Description:** Detect changes to receipts/statements across versions and replacement keys; disclose earlier/current support, changed fields and suppliers and require bound non-supplier acceptance before renewed review.
- **Business purpose:** Prevent corrected documents from making previously unsupported work silently approvable.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Independently verified
- **Scope note:** Independent Fable RB review verified the synthetic local preparation controls exercised by the named probes at the V2 checkpoint; no client policy, connected operation, reconciliation completion, close or operating readiness is verified. UC-10: a contradicting receipt supplied after the one relied on, then moved away or withdrawn, leaves no disclosure; that document-policy question is outside the verified RB-02 scope (N02c NOTE). RC transition-chain acceptance binding was independently verified by probe Q02 at checkpoint 9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454. RD-01/RD-02 keep AAOS-BNK-03/AAOS-CTL-04 failed; this result grants no wider readiness.
- **Evidence:** [independent review](../exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d; R03a, R03b, R04a, R04b, R04c, N02a, N02b, N04a, N04b, N04c, N04d; N02c NOTE. [independent review](../exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454; Q02 independently verifies exact-chain transition acceptance binding.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-CTL-01; AAOS-CTL-08; AAOS-BNK-03.
- **Acceptance criteria:** Withdrawing/replacing a receipt or re-supplying a matching statement still creates visible holds; acceptance excludes all old/current suppliers, is item/evidence-bound and lapses on later changes; a new still-active extra receipt remains a multiple-document issue; accepted revisions still require separate final review; predecessor evidence accepted at submission can actually activate on re-preparation. Detect replacement by any route, including an old document key moved to another item or cycle; disclose prior-period lookback restatement and keep its dependent continuity unverified until active own-period acceptance covers every relying item. Revocation or changed evidence re-blocks it.
- **Target stage:** Current RA / G0; actual correction acceptance policy at G1.
- **Trace:** RV-12; RA-03/RA-04/RA-06; EVIDENCE and disclosed A03/A05/A17/X09/RT18 setups.

### AAOS-CTL-10 — Persistent audit and inspectable evidence

- **Description:** Preserve scoped source snapshots, immutable historical artifacts/decisions/contributors/exceptions, lineage, reasons and audit events through corrections, migrations and exports.
- **Business purpose:** Reconstruct what happened, why and under whose authority without rewriting accounting history.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for local append-only history, package bytes, restart/migrations and inspection; administrator-proof external retention not implemented.
- **Evidence:** [tests/test_periods.py](../tests/test_periods.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G0 controls
- **Dependencies:** AAOS-ARC-02; AAOS-EXE-01.
- **Acceptance criteria:** Reproduce an output from its source/policy/dependency versions; retain original independent review evidence and package hashes; current versus historical status is explicit; DB hash chains are described as inspection aids, not proof against an administrator or truncation without an external anchor.
- **Target stage:** Current / G0; external reliance additionally requires AAOS-CTL-11/13.
- **Trace:** T-07/T-18/T-25; CORRECTIONS; ARCH; LEGACY data protection.

### AAOS-CTL-11 — Consistent exports and external audit anchoring

- **Description:** Export one decision-consistent scoped snapshot with stable content hash/metadata separation; verify audit head/length against a separately retained anchor and support bounded/paged inspection.
- **Business purpose:** Prevent evidence exports from mixing states or overstating tamper/truncation protection.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred; current full live export uses two transactions with an input guard, not an atomic decision-consistent snapshot.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-CLS-02; AAOS-CTL-10.
- **Acceptance criteria:** Concurrent input/decision changes cannot produce mixed approval state; stable content hash excludes volatile export metadata; altered or truncated audit fails comparison with an external anchor; history is complete through pagination; actual external retention/WORM policy is selected before relying on that guarantee.
- **Target stage:** Existing Batch 3 / T-25, not authorized; external audit/retention infrastructure separately agreed before operational reliance.
- **Trace:** T-25; FABLE F-19/§11; ARCH limits; RA remaining limitations.

### AAOS-CTL-12 — Credentials, privacy and untrusted content

- **Description:** Use scoped secret references, least-privilege access, redaction and validated document/display handling; treat imported text/model output as data, never authority.
- **Business purpose:** Protect client credentials and financial information and resist prompt injection, unsafe uploads and cross-client disclosure.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred for real secret/credential lifecycle and comprehensive threat validation; local DOM/no-egress/scope checks cover only demo boundaries.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-CTL-02.
- **Acceptance criteria:** No secrets in prompts/source/fixtures/normal logs/exports; rotate/revoke scoped credentials; verify file types/size and sanitize rendering; do not execute imported scripts/macros; imported instructions cannot expand tools/scope/destinations; client data cannot enter public telemetry; no shared firm credential copy to a client host by default. Before G2, the security/operating owner approves and executes a threat-test matrix covering cross-scope retrieval/export, secret leakage/redaction, imported prompt instructions, executable/oversized uploads, unsafe rendering, authentication/session failures, credential rotation/revocation and unauthorized data egress; unresolved failures block connection.
- **Target stage:** Before actual records/credentials and any hosted G2 connection; implementation scope later assigned.
- **Trace:** U; LEGACY §14; PILOT deployment; ARCH local boundaries.

### AAOS-CTL-13 — Backup, restore, retention and supported infrastructure

- **Description:** Provide encrypted scoped evidence/state backups, restore drills, retention/deletion rules, private persistent artifact storage and supported runtime/database operation under agreed administration.
- **Business purpose:** Preserve client records and recover decisions, unfinished work and evidence after host or operator failure.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Deferred for operational infrastructure; local backup/migration tests do not establish production recovery.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G2 hosted reads
- **Dependencies:** AAOS-ARC-02; AAOS-ARC-05; AAOS-CTL-12; AAOS-EXE-01.
- **Acceptance criteria:** Restore evidence, decisions, packages, grants and pending work into the correct environment without replaying effects; document retention/recovery targets and deletion authority; validate storage/worker concurrency and schema migrations; choose supported runtime before hosting; justify any store/stack migration against Fable's triggers rather than rewriting speculatively. Before real evidence/G2, the client data owner and operating owner record retention duration, deletion authority, recovery-point objective (RPO) and recovery-time objective (RTO). A timed restore drill measures achieved data loss and recovery time against those approved values; unset/failed targets block operational reliance.
- **Target stage:** Before real evidence reliance and hosted G2; recovery verified again for G4.
- **Trace:** FABLE §11; LEGACY release/rollback/storage; PILOT Jeff/support; D-002.

## Shared client lifecycle

These client-neutral proposals preserve the reusable onboarding/offboarding scope. They add no enabled workflow or client authority. Each client implementation supplies its own facts, dates, operators, evidence and decisions. Product ratification and implementation ordering remain open.

### AAOS-ONB-01 — Client onboarding and capability validation

- **Description:** Provide a reusable onboarding process per client, entity/book and capability: authorized knowledge capture, independent held-out validation, operator teach-back, bounded unattended/close readiness and an agreed support/host/authority model.
- **Business purpose:** Onboard another client through configuration and validation without copying first-client assumptions.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Second client
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-06; AAOS-OBS-04; AAOS-CTL-03; AAOS-CTL-13
- **Acceptance criteria:** An onboarding dossier identifies scope, authoritative systems/sources, approved facts/policies, proposed versus approved knowledge, independent validation inputs/results, coverage/manual tasks, named operator/reviewer authority, observed teach-back, unattended evidence, support/data ownership and release decision. No client is enabled solely by cloning a profile. Each capability returns to its relevant G1–G4 gate; client-specific records instantiate this shared requirement.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-06; existing universal-client instructions; PILOT portable handoff/readiness pattern generalized without client facts.

### AAOS-ONB-02 — Client offboarding, data return and deletion

- **Description:** Define secure offboarding with authority revocation, cessation/reconciliation of pending work, scoped data return and agreed retention/deletion.
- **Business purpose:** Return client records without losing accounting evidence or leaving access/standing authority active.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** New proposed shared requirement; no capability is implemented or enabled by recording it.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Second client
- **Dependencies:** AAOS-ONB-01; AAOS-KNO-06; AAOS-CTL-03; AAOS-CTL-11; AAOS-CTL-12; AAOS-CTL-13
- **Acceptance criteria:** A signed-off plan specifies machine-readable JSON/CSV plus original support documents, hash manifest and a human-readable index; identifies pending/unknown external outcomes and their owner; revokes scoped credentials/grants/mandates; records recipients/secure delivery, retention/legal-hold constraints, deletion authority and evidence of permitted deletion/backup expiry. Test that another client is unaffected. Format/transport/retention terms require the client data owner before offboarding.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-06; proposed offboarding extension, not an inferred client retention or engagement policy.

## Bird Bowl onboarding and validation

- **Client-specific terms:** Bird Bowl; Theresa; Jeff; Luis; Expensify; Desktop

These names and client-only system choices are drawn from the client records below. Shared named QBO integration scope remains in AAOS-INT-01. The checker reads this list for register and shared-code boundaries.


### AAOS-BB-01 — November knowledge capture

- **Description:** Capture the planned November 2026 workflow inputs, sequence, accounts/calculations, outputs, review points, exceptions and Luis's interventions into proposed durable procedures/decisions.
- **Business purpose:** Preserve actual client accounting knowledge instead of relying on chat memory or invented mappings.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved pilot plan; real capture/processing is not evidenced as completed. The product owner and accounting lead confirmed in writing on 16 November 2026 that procedure documentation outside the application may proceed before G1 (D-016).
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04; AAOS-KNO-05; AAOS-GOV-03; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement)
- **Acceptance criteria:** Separate proven client logic, model suggestions, temporary choices and unresolved facts; each intervention names correction scope/evidence/rationale/version; accounting lead validates before reusable approval; real records only after G1 authorization. Distinguish external written procedure capture from application processing in the capture log. This clarification and its confirmation (D-016) grant no new source access, client-data upload, accounting-policy approval or real workflow execution; completion of capture is recorded only when evidenced.
- **Target stage:** Confirmed by the product owner and accounting lead (D-016): before G1 the team may document the November 2026 accounting procedures outside the application, using only the client access it already has; no client records are loaded into this application. Loading or processing client records in the application requires human G0 acceptance and explicit G1 authorization. November 2026 is the confirmed capture period, not evidence that capture occurred.
- **Trace:** PILOT November capture; LEGACY AT-60; U; PR-11; D-012; D-016.

### AAOS-BB-02 — Independent December validation and gaps

- **Description:** Validate approved procedures on new December 2026 cases and independently reviewed expected outcomes, separated from teaching examples.
- **Business purpose:** Determine whether the process generalizes before operating handoff.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved plan; independent real-client validation not performed. December 2026 is designated as the held-out month by the product owner and accounting lead (D-016).
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-BB-01; AAOS-KNO-06; AAOS-OBS-04; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement)
- **Acceptance criteria:** Include relevant missing evidence, duplicates, changed descriptions, splits, revisions and exceptions without supplying teaching answers; record disagreements and approved revisions; retain annual/unusual/untested coverage gaps with human routes; no synthetic success substitutes for this result. November cases are used to write and refine the procedures; December cases and their expected results are kept separate from the teaching examples so that an independent reviewer can test the procedures against them (D-016).
- **Target stage:** G1 held-out application validation follows approved capture by a separate accounting period. December 2026 is the designated held-out month for independent validation (D-016); a different month needs a new recorded decision. Processing December records in the application still requires human G0 acceptance and explicit G1 authorization. G2/G4 require their separate decisions.
- **Trace:** PILOT December validation; FABLE G1/G2; LEGACY AT-60/AT-61; PR-11; D-012; D-016.

### AAOS-BB-03 — Theresa's ordinary workflow and escalation

- **Description:** Capture Theresa's actual tasks, sequence, information needs, preparation/review limits and escalation routes; provide and test an operator guide.
- **Business purpose:** Enable daily operation without Luis prompting each step while retaining appropriate judgment and support.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved goal; Theresa's actual role/authority and observed workflow are unverified.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-BB-02; AAOS-KNO-06; AAOS-CTL-03; AAOS-BB-07 if ratified; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement)
- **Acceptance criteria:** Theresa performs the assigned workflow from input to review using the guide, explains when/how to escalate and identifies unclear context; record actual assistance/time; a fixture named Theresa or an API test cannot count as her teach-back or approval.
- **Target stage:** G1 discovery/validation; observed G4 operating handoff.
- **Trace:** U; PILOT Theresa/readiness; LEGACY AT-61; FABLE G4/question 17.

### AAOS-BB-04 — Sales and deposit process capture

- **Description:** Discover and document Bird Bowl's relevant sales evidence, sales-to-ledger workflow, cash/card receipts, deposits/settlements, timing differences and related review/closing dependencies.
- **Business purpose:** Onboard actual operating flows that a card-only demonstration cannot cover.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved discovery requirement; actual systems, totals, allocation/fee/tax treatment and procedures unknown.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-BB-01; AAOS-BNK-05; AAOS-KNO-04; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement) ; AAOS-GL-06 if ratified and AAOS-BNK-07 if ratified for any later authorized execution
- **Acceptance criteria:** Identify sources, responsible people, reconciliation boundaries and one posting route; independently validate observed procedures and known reviewed examples; exceptions/timing/fees/refunds remain questions until supported; store any approved treatment only in the client workspace, with no invented Bird Bowl financial facts.
- **Target stage:** G1 authorized knowledge capture; execution capabilities future / unassigned after prerequisites are validated.
- **Trace:** U's explicit onboarding scope; PILOT procedure-capture method; ARCH banking/GL contracts. Existing pilot does not supply the actual sales/deposit procedure.

### AAOS-BB-05 — Payroll and tip process capture

- **Description:** Discover the relevant payroll/tip inputs, liability/expense/clearing treatment, allocations, source-to-ledger reconciliation, review and close interfaces under actual authorized procedures.
- **Business purpose:** Preserve these onboarding needs without guessing payroll policies or expanding into unauthorized payroll execution.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved discovery requirement; providers, calculations, tax/tip rules, amounts and authority unknown.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-KNO-03; AAOS-KNO-04; AAOS-BB-01; AAOS-CTL-08; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement) ; AAOS-GL-06 if ratified for any later authorized accounting preparation
- **Acceptance criteria:** Accounting lead validates source completeness, reconciliation and approved examples; procedure names preparer/reviewer and manual responsibilities; missing legal/payroll/tip treatment remains a question for qualified validation; no payroll run, payment or filing capability is activated by knowledge capture.
- **Target stage:** G1 authorized discovery; any accounting preparation module later assigned separately; payroll execution outside this task.
- **Trace:** U; PILOT capture/validation controls; FABLE question 8 mentions meals/tips but provides no actual payroll policy.

### AAOS-BB-06 — Actual close and unattended readiness

- **Description:** Capture Bird Bowl's real close checklist/calendar and demonstrate the agent's bounded unattended portion plus required human review and final sign-off responsibilities.
- **Business purpose:** Establish dependable operation through accounting results and observed effort rather than a calendar promise or job-title claim.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved goal; actual close/operating readiness not demonstrated.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-BB-02; AAOS-BB-03; AAOS-CLS-03; AAOS-EXE-04; AAOS-OBS-01; AAOS-BB-07 if ratified; AAOS-ONB-01 if ratified (first client instance of the shared onboarding requirement)
- **Acceptance criteria:** December close waits for necessary records, possibly January 2027; no automatic January 1 deployment; measure complete supported work, required/missed exceptions, independence of blocked tasks and all recurring human work; human release identifies exactly which validated workflows may operate.
- **Target stage:** G1 close discovery; G4 demonstrated workflow scope after applicable capability gates.
- **Trace:** U; PILOT readiness; LEGACY AT-61; FABLE questions 13/17/G4.

### AAOS-BB-07 — Hosting, support, ownership and engagement agreement

- **Description:** Resolve proposed roles for Theresa (operations), Jeff (technical support), SS/Luis (accounting oversight), and the relevant client/company owners, including host, administrators, credentials, data/asset rights, billing and maintenance scope.
- **Business purpose:** Avoid turning a proposed support model into assumed authority, an engagement or an ownership transfer.
- **Priority:** Must
- **Product decision:** Proposed
- **Implementation state:** Not started
- **Scope note:** Proposed operating arrangement; responsibilities/commercial terms have not been agreed.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-KNO-03; AAOS-CTL-03; AAOS-CTL-12; AAOS-OBS-03. Deployment-option selection is part of this agreement, not a prerequisite to designing those options; AAOS-ONB-01 (first client instance of the shared onboarding requirement)
- **Acceptance criteria:** Named parties agree accounting versus technical escalation, authority, platform/runtime/jobs/storage, backup/recovery, changes requiring accounting review, optional model payer and support/co-management terms; authorized company/entity and any asset reuse/licensing boundaries are recorded; no inherited credentials or cost commitments.
- **Target stage:** Before any authorized hosting/G2 and operating handoff/G4; discussion can precede implementation.
- **Trace:** PILOT proposed responsibilities/deployment; LEGACY company authority/funding/asset boundaries; FABLE question 16.

### AAOS-BB-08 — AP/AR applicability, ledger edition and transaction-intake route

- **Description:** Resolve the first client’s actual AP/AR use, book-of-record edition/migration and authoritative bank/card intake/posting route.
- **Business purpose:** Keep these unresolved pilot facts in its client implementation instead of making shared accounting capabilities wait for one client.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** All actual AP/AR/ledger/intake facts remain unknown. This is the first client instance of shared onboarding, not a shared-core condition.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-ONB-01 if ratified; AAOS-KNO-03; AAOS-KNO-04
- **Acceptance criteria:** Authorized client/accounting owners confirm whether AP/AR are relevant and supply approval/receiving/terms/reporting facts; confirm Desktop-to-QBO conversion and the actual book of record per period. Compare permitted direct bank, aggregator, native QBO and, only if purchased/authorized, Expensify as a bank-transaction candidate; verify complete checking versus card coverage and one posting route, source identity and any approved clearing treatment. No vendor, access, purchase, mapping or completed conversion is presumed.
- **Target stage:** G1 written client facts; provider capabilities/access verified separately at G2. No connector/purchase/posting authorization.
- **Trace:** PR-07; PILOT first test/unresolved intake; Fable questions 1–7/12/15; AAOS-INT-01/05 are named integration requirements.

## Morning Briefing and human work management


### AAOS-BRF-01 — Actionable Morning Briefing

- **Description:** Present completed overnight, needs attention, waiting on others, continuing automatically, today's priorities and estimated human review time, with evidence/current-state links and an explicit reporting window.
- **Business purpose:** Let a human understand progress and make necessary accounting decisions quickly without prompting each task.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved product requirement; no implemented Morning Briefing.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-01; AAOS-EXE-02; AAOS-EXE-03; AAOS-OBS-01; AAOS-OBS-02; AAOS-BRF-03.
- **Acceptance criteria:** All six sections appear, including honest empty/unavailable states; reporting cutoff/timezone and stale/failed-run coverage are visible; each status/priority is tied to work/evidence/deadline/authority rather than invented completion; estimates state assumptions; no digest hides critical exceptions or treats silence as consent. Default delivery is in-application. Reporting cutoff and timezone are approved client-profile values; email or other outbound delivery is a send governed separately by AAOS-COM-02.
- **Target stage:** Future / unassigned; local briefing may later precede hosting, but true overnight completion requires authorized AAOS-EXE-04 operation.
- **Trace:** U; accounting-app adaptation of LEGACY briefing/inbox concepts. No Executive Director agent dependency.

### AAOS-BRF-02 — Management-wide and individual-client views

- **Description:** Provide authorized firm-management aggregation and scoped individual-client Morning Briefings/work views from the same accounting platform.
- **Business purpose:** Manage a portfolio efficiently while showing each client/operator only permitted records and responsibilities.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; management-wide briefing and real permissions not implemented.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-BRF-01; AAOS-ARC-02; AAOS-ARC-03; AAOS-CTL-02.
- **Acceptance criteria:** Aggregates/drill-downs include only granted clients; unauthorized counts, names, totals and export references do not leak; client views cannot reach other-client/company data; a standalone client deploy needs no central connection; tests cover permitted and denied management/client access.
- **Target stage:** Future / unassigned; hosted views require authenticated identity/isolation before G2.
- **Trace:** U; PILOT backend deployment boundary; LEGACY consolidated inbox/access principles.

### AAOS-BRF-03 — Review, exception and waiting inbox

- **Description:** Consolidate decisions/exceptions by cause with owner, age, evidence, recommendation, exact decision scope, allowed responses, waiting party and work that can continue.
- **Business purpose:** Reduce unnecessary interruptions without concealing blockers or bundling unrelated permissions.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved full inbox; local item review/exception UI and evidence-bound dispositions are tested subsets.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-01; AAOS-CTL-01; AAOS-CTL-06; AAOS-CTL-08; AAOS-CTL-09.
- **Acceptance criteria:** Group repeat alerts while retaining per-item approve/reject/defer/revise controls; genuine urgency/deadlines and escalation policy govern interruption; no external notification is claimed without verified channel evidence; unresolved items remain visible and independent work continues; no response grants authority. Before G4, the client/accounting owner records urgency predicates, response deadlines, timezone and escalation recipients in the approved workflow policy. Simulated deadline cases prove routing, deduplication and no-response holds; only separately authorized channels may send alerts.
- **Target stage:** Current local review subset; complete operational inbox future / unassigned, notification permission separate.
- **Trace:** U; T-14; LEGACY inbox/exception concepts; PILOT workflow readiness.

## Operating measurements and validation


### AAOS-OBS-01 — Work, accuracy, exceptions and human effort

- **Description:** Measure task coverage/completion, accounting accuracy, defects/missed exceptions/false positives, required versus unnecessary interruptions and human preparation/review/correction/training/maintenance time.
- **Business purpose:** Determine whether the system releases dependable capacity rather than merely increasing task counts or hiding errors.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; test/gate logs exist, a real operating scorecard and baseline do not.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-01; AAOS-CTL-10; AAOS-OBS-04.
- **Acceptance criteria:** Metrics identify sample, denominator, period, source and uncertainty; held/deferred tasks are not counted completed; all recurring human effort is included in net time released; saved capacity is not automatically cash payroll savings or revenue; thresholds are agreed before a real pilot, not invented here. Before G1 evaluation, the accounting/product owners record the baseline, denominators and acceptance thresholds for accuracy, missed exceptions, false alarms, interruptions and human time in a scorecard. Before G4 they review measured results against those values; unknown thresholds never become a success claim.
- **Target stage:** Future / unassigned instrumentation; baseline before G1/G2 and measured evidence before G4.
- **Trace:** U; PILOT readiness/effort; LEGACY autonomy/economics/scorecard.

### AAOS-OBS-02 — Estimated human review time

- **Description:** Estimate review time per item/package/briefing using observed comparable work and current complexity/exception state; record actual time separately to calibrate estimates.
- **Business purpose:** Plan daily attention and review capacity honestly.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; estimator/time-capture capability not implemented.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-OBS-01; AAOS-EXE-01.
- **Acceptance criteria:** Display estimate/as-of/method/confidence or unknown when no basis exists; totals do not double-count grouped work; track actual/estimated variance and necessary review even on routine work; synthetic estimates never become observed client time.
- **Target stage:** Future / unassigned, needed for the complete AAOS-BRF-01.
- **Trace:** U; LEGACY review-capacity/measurement principles; PILOT human effort.

### AAOS-OBS-03 — Model, infrastructure and human cost controls

- **Description:** Measure gross model usage, cash cost after credits, infrastructure/vendor costs and human effort; enforce approved per-run/environment/client/company allocations, concurrency and bounded work limits before paid use.
- **Business purpose:** Make autonomous operation economically accountable and prevent retries or multiple environments from bypassing spending limits.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved; no paid calls/services activated and no production budget enforcement proven.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** G4 operating handoff
- **Dependencies:** AAOS-EXE-03; AAOS-EXE-05; AAOS-CTL-10; AAOS-ARC-05.
- **Acceptance criteria:** Missing live budgets block spend; reserve estimates before calls and reconcile actual usage; retries/resumptions share limits and cannot reset counters; environment allocations fit the company ceiling; distinguish credits from owned budgets and estimates from invoices; proposed legacy numeric limits require explicit adoption, not silent client policy.
- **Target stage:** Future / unassigned; configured/tested before any authorized model/hosting/vendor expense.
- **Trace:** U; LEGACY §13/pilot economics; PILOT separate model/hosting costs; FABLE G2.

### AAOS-OBS-04 — Independent validation and realistic evaluation

- **Description:** Maintain teaching/regression/adversarial/held-out accounting cases, exact blocker expectations and operational fault tests; evaluate any model assistance separately from deterministic fixtures.
- **Business purpose:** Detect plausible but incorrect accounting and avoid treating a demonstration as independent business proof.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Developer-tested
- **Scope note:** Tested for current synthetic regression/reviewer/control suites; real-client/model/operational evaluation deferred.
- **Evidence:** [tests/test_acceptance_gate.py](../tests/test_acceptance_gate.py); [recorded developer evidence](acceptance_ra/execution-results.json). Scope is limited to the tests, not full-cycle or operating readiness.
- **Needed for:** G1 approved samples
- **Dependencies:** AAOS-GOV-03; AAOS-KNO-05; AAOS-CTL-10.
- **Acceptance criteria:** Positive paths prove their preconditions and exact eligible/blocker outcomes; missing initial decisions/eligibility fail before testing a later event (strengthened RT14b); new defects have regression cases; maintain original probe bytes and reviewed deltas; model evaluations measure missed issues, uncertainty, latency/cost and independent expected results without manufacturing participant UAT.
- **Target stage:** Current / G0; held-out G1, integration/fault G2/G3 and observed operating G4 evidence separately.
- **Trace:** T-01; CORRECTIONS; EVIDENCE; LEGACY AT-60/61 and live-evaluation distinctions.

## Future accounting communications


### AAOS-COM-01 — Missing-document and collection drafts

- **Description:** Prepare complete scoped requests for missing accounting documents and AR collection follow-ups with the underlying item/customer, evidence, recipients, attachments and unresolved questions.
- **Business purpose:** Help resolve blocked accounting work without making humans reconstruct the request.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved future capability; no automated communication workflow implemented or authorized to send.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-BRF-03; AAOS-CTL-08; AAOS-ARC-02; AAOS-KNO-03.
- **Acceptance criteria:** Source facts/customer balances and missing documents are verified; choose only authorized recipients with no cross-client attachment leakage; unsupported claims stay questions; a reviewed/exported draft is labeled draft, not delivered; collection-specific drafts wait for validated AAOS-AR-02 balances/terms.
- **Target stage:** Future / unassigned; draft-only stage can be assigned before sending, with approved sample/data access.
- **Trace:** U; LEGACY accounting package draft questions/human-sent communications; ARCH AR contract.

### AAOS-COM-02 — Controlled drafting and sending permissions

- **Description:** Model read, draft, approve and send permissions separately by client/channel/recipient/purpose, with exact content/attachment approval, bounded standing authority where expressly approved and auditable delivery state.
- **Business purpose:** Enable future communication assistance without sending unapproved financial information or treating draft approval as a general communications mandate.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Not started
- **Scope note:** Approved product direction; sending remains deferred and prohibited in the current build.
- **Evidence:** Not implemented; source specifications in Trace and target/dependency gates define future validation.
- **Needed for:** Platform maturity
- **Dependencies:** AAOS-COM-01; AAOS-CTL-01; AAOS-CTL-02; AAOS-CTL-03; AAOS-CTL-12; AAOS-INT-06.
- **Acceptance criteria:** Human-sent/exported drafts stay the default until a separate sending capability, policy and authorization are approved; exact sender/recipients/body/attachments and current scope are checked; denied/revoked/changed payload blocks send; uncertain delivery is reconciled without blind retry; human-reported sending is distinguished from provider-verified delivery; silence grants nothing.
- **Target stage:** Future / unassigned, separate action-specific authorization beyond ordinary accounting G3 writes; no automatic-send permission from this register.
- **Trace:** U's future communication scope; LEGACY human-sent boundary/uncertain outcomes; FABLE reserved actions.

## Scope exclusions and reserved actions

Rejected means outside this accounting product by existing scope decisions. Reserved means currently unavailable/prohibited without a separately assigned capability and action-specific authority; it is not a permanent product rejection. Unsettled long-term scope remains Proposed. No new payroll, tax, payment or legal capability is assigned here.

| Stable ID | Scope disposition | Reason | Decision reference |
| --- | --- | --- | --- |
| AAOS-EXC-01 | Rejected | Executive, marketing, sales, CRM and other business-development agents belong outside this accounting project. | User accounting-only scope; D-001. |
| AAOS-EXC-02 | Rejected | A separate legal/compliance agent is not this accounting platform; qualified human advice remains available as needed. | User non-accounting-agent exclusion; D-001. |
| AAOS-EXC-03 | Reserved | Payroll runs and payroll filings are not authorized by accounting-summary preparation; long-term product scope remains undecided. | Existing reserved-action boundary; D-012; PR-10. |
| AAOS-EXC-04 | Reserved | Tax returns, sales-tax filings and information returns/1099 preparation have no assigned capability or approved engagement scope. | D-012; PR-10; product/client decision pending. |
| AAOS-EXC-05 | Reserved | Payment execution is a future separately gated capability, not authorized by bill preparation or ordinary G3 writes. | AAOS-AP-02; Fable G3; D-012. |

### AAOS-EXC-01 — Non-accounting executive and business-development agents

- **Description:** Retain the explicit rejection of executive, marketing, sales, CRM and other non-accounting agents in this project.
- **Business purpose:** Prevent the broader source handoff from displacing accounting execution.
- **Priority:** Must
- **Product decision:** Rejected
- **Implementation state:** Not started
- **Scope note:** Rejected scope. Rejected scope, not a missing accounting capability.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Product decision
- **Dependencies:** None.
- **Acceptance criteria:** No such agents, CRM datasets or business-development workflows are activated by accounting implementation; reference-package preservation does not import its broader scope.
- **Target stage:** Excluded from this product; any different scope needs a new user decision.
- **Trace:** Explicit user scope supersedes broader handoff; D-001; PR-10.

### AAOS-EXC-02 — Separate legal and compliance agent

- **Description:** Retain exclusion of a separate legal/compliance agent while preserving required human accounting/legal judgments.
- **Business purpose:** Avoid expanding the accounting project into legal advice or contract/signing authority.
- **Priority:** Must
- **Product decision:** Rejected
- **Implementation state:** Not started
- **Scope note:** Rejected scope. Rejected non-accounting agent scope.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Product decision
- **Dependencies:** None.
- **Acceptance criteria:** No agent signs agreements, accepts terms, waives rights or assumes legal authority; questions requiring qualified legal/compliance judgment remain human referrals.
- **Target stage:** Excluded agent; human validation remains separate.
- **Trace:** D-001; explicit user scope; original legal-agent section is historical reference only; PR-10.

### AAOS-EXC-03 — Payroll execution and payroll filings reserved

- **Description:** Record payroll runs and statutory payroll filings as reserved, distinct from accounting journals prepared from approved payroll/tip reports.
- **Business purpose:** Avoid treating knowledge capture or proposed journals as permission to run payroll or file.
- **Priority:** Must
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** Reserved action. Reserved execution boundary; long-term product inclusion remains Proposed and no capability exists.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Product decision
- **Dependencies:** AAOS-GL-06; AAOS-CTL-03; AAOS-INT-06
- **Acceptance criteria:** No payroll run, filing or disbursement is executable from this foundation; any future proposal needs a product scope decision, qualified client authority, supported integration, reviewed controls and a separate implementation/action assignment. Retain the unresolved long-term scope instead of inventing a permanent exclusion.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-10; existing no-payroll-execution boundary; D-012.

### AAOS-EXC-04 — Tax and information-return preparation or filing reserved

- **Description:** Track tax returns, sales-tax filings and information-return/1099 preparation/filing as unassigned scope requiring separate product/engagement decisions.
- **Business purpose:** Prevent silence from becoming either forgotten work or assumed professional/filing authority.
- **Priority:** Should
- **Product decision:** Proposed
- **Implementation state:** Deferred
- **Scope note:** Reserved action. Reserved and unimplemented; whether it belongs in future product scope remains Proposed.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Product decision
- **Dependencies:** AAOS-KNO-01; AAOS-CTL-03; AAOS-CTL-08
- **Acceptance criteria:** The product owner and qualified client/accounting authority decide inclusion, jurisdiction, engagement and review/filing limits before any implementation; no return preparation, tax conclusion or filing is represented as delivered. Accounting source capture does not grant tax-service authority.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** PR-10; D-012; no client tax facts or scope have been supplied.

### AAOS-EXC-05 — Payment execution reserved

- **Description:** Preserve the separate approval/design/authority gate for executing payments, beyond payable workpapers and proposals.
- **Business purpose:** Prevent duplicate, unauthorized or misdirected disbursement.
- **Priority:** Must
- **Product decision:** Approved
- **Implementation state:** Deferred
- **Scope note:** Reserved action. Approved reserved-action control; payment execution itself remains Deferred and unimplemented.
- **Evidence:** Not implemented. [product-register review](../exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md); relevant original specifications and current authority remain prerequisites.
- **Needed for:** Product decision
- **Dependencies:** AAOS-AP-02; AAOS-CTL-03; AAOS-INT-06
- **Acceptance criteria:** Ordinary preparation, recurring mandates, G3 ledger-write approval and this register cannot execute payments; a later explicit payment capability needs verified recipients/bank changes, independent approvals, idempotency/unknown-outcome recovery and client-specific written authority.
- **Target stage:** Future / unassigned; no implementation or operating authority.
- **Trace:** User no-payment boundary; Fable G3; AAOS-AP-02; D-012; PR-10.

## Synchronization with the implementation backlog

This is a requirements crosswalk, not new ticket sequencing. The original JSON remains unchanged. Batch 1 and Batch 2 entries describe bounded local implementation, not full accounting-cycle completion or independent RA acceptance. Corrective tickets extend/reopen the affected underlying controls; they are not replaced by a new feature plan.

| Ticket | Requirement IDs | Current disposition |
| --- | --- | --- |
| T-01 | AAOS-GOV-03, AAOS-OBS-04 | Adopted exact reviewer assertions; preserved originals and disclosed adaptations. |
| T-02 | AAOS-CTL-05, AAOS-BNK-01 | Tested local Unicode/ambiguity handling; C-05 preserves combining marks. |
| T-03 | AAOS-CTL-01, AAOS-CTL-02 | Tested synthetic independence; real authentication remains T-27. |
| T-04 | AAOS-EXE-01, AAOS-EXE-02 | Tested occurrence/run separation and independent held work. |
| T-05 | AAOS-CTL-04 | Tested durable periods and later corrective lock/move controls. |
| T-06 | AAOS-ARC-01, AAOS-CTL-07 | Tested workflow/period manifest relevance; finer invalidation deferred. |
| T-07 | AAOS-CTL-06, AAOS-CTL-10 | Tested governing item/decision history and contributor links. |
| T-08 | AAOS-GOV-02, AAOS-GOV-03 | Truthful capability documentation; maintained with this register. |
| T-09 | AAOS-KNO-04, AAOS-CTL-01 | Tested synthetic rule/profile lifecycle; RA-02 accepted for original scope; RB-03 fails new scope/key coverage until re-verification. |
| T-10 | AAOS-EXE-03 | Tested synthetic period/freshness/policy authority; RA-05 independently accepted within its tested scope; broader real operation remains gated. |
| T-11 | AAOS-KNO-03 | Tested required facts and explicit demo-only waivers. |
| T-12 | AAOS-BNK-03, AAOS-CTL-04 | RD-01/RD-02 accepted independently at 0d188fa6…7ea9; RB-01 remains unaccepted for RE-01/RE-02. Owner D-026 now bounds the feed contract; RE-01–RE-03 developer corrections follow D-029 for frozen approvals and require independent contract-clause, 12-probe/adapted-Y05 and 336-order verification. |
| T-13 | AAOS-BNK-02 | Tested fictional statement/population controls; non-calendar cycles deferred. |
| T-14 | AAOS-BRF-03, AAOS-CTL-08, AAOS-CTL-09, AAOS-CTL-05 | Tested scoped exceptions/dispositions; RA-06/07/08 accepted; RB-02/RB-04 replacement/continuity routes await independent re-verification. |
| T-15 | AAOS-GL-01 | Tested synthetic shared proposed entries; actual ledger execution absent. |
| T-16 | AAOS-GL-02 | Tested bound-support/duplicate/no-effect journal checks. |
| T-17 | AAOS-KNO-04, AAOS-CTL-08, AAOS-BNK-06 | Tested explicit/unset receipt policy; aggregate receipt support deferred. |
| T-18 | AAOS-CLS-02 | Tested immutable preparation-package finalization; not final close. |
| T-19 | AAOS-CLS-01 | Tested typed workflow readiness; deferred external outcomes remain held. |
| T-20 | AAOS-BNK-04 | Deferred existing Batch 3 card reconciliation workpaper. |
| T-21 | AAOS-BNK-05, AAOS-CTL-05 | Deferred existing Batch 3 settlement/transfer/cross-period controls. |
| T-22 | AAOS-GL-04, AAOS-RPT-01 | Deferred existing Batch 3 trial-balance foundation; not full reporting. |
| T-23 | AAOS-AP-01, AAOS-AP-02 | Deferred synthetic AP specification first; no payment execution, client facts/new assignment required for expansion. |
| T-24 | AAOS-EXE-05 | Deferred production retry/worker lifecycle. |
| T-25 | AAOS-CTL-11 | Deferred atomic exports/audit anchoring. |
| T-26 | AAOS-GL-05 | Deferred general currency/minor units. |
| T-27 | AAOS-CTL-02, AAOS-ARC-02 | Deferred authenticated identity/bounded access; not production-ready today. |

Existing order is **T-01–T-08**, then **T-09, T-11, T-12, T-10, T-13, T-14, T-15, T-16, T-17, T-18, T-19**. The earlier RA order was **RA-01, RA-03, RA-04, RA-02, RA-06, RA-05, RA-07, RA-08**. The prior RB correction order was **RB-01, RB-02, RB-03, RB-04**. Current authorized order is **RE-01, RE-02, RE-03**, with **PRV-14–PRV-15** in the same pass, followed by independent re-verification. Batch 3's existing **T-20–T-27** order/dependencies remain on record but are not authorized to start. No new proposed requirements above are inserted into a batch.

| Review layer | Required control trace and acceptance state |
| --- | --- |
| C-01–C-06 | AAOS-CTL-01/04/05/06, AAOS-BNK-03. Later reviews reopened the locked-origin control; RA-01 failed at late-link arrival paths (RB-01); the response now requires independent re-verification. Preserve every original method and new failure-path regression. |
| RV-01–RV-17 | AAOS-CTL-01/05/06/08/09/10, AAOS-KNO-04, AAOS-BNK-02/03, AAOS-EXE-03, AAOS-CLS-01/02, AAOS-GOV-03. Fable accepted 14; RV-01/10/12 had new routes requiring RA-01/02/03/04. Seven earlier adaptations and strengthened RT14b accepted; do not claim all 17 were independently accepted. |
| RA-01 | AAOS-BNK-03, AAOS-CTL-04: RD-01/RD-02 accepted at 0d188fa6…7ea9; RE-01/RE-02 remain independently failed. Owner D-026 supersedes retargeting semantics and adds RE-03 authorized no-release/selection controls; D-029 preserves frozen approvals while blocking incoming versions until reopen; independent verification of the new checkpoint, including all 336 orders and this clarified boundary, remains required. |
| RA-03, RA-04 | AAOS-CTL-09, AAOS-BNK-02: replacement receipt keys and revised/replaced statements held/disclosed/independently accepted. |
| RA-02 | AAOS-KNO-04, AAOS-CTL-01: relevant approved semantic rule authors survive absent optional links. |
| RA-06, RA-05 | AAOS-CTL-08/09, AAOS-EXE-03: the same predecessor references activate dispositions; relevant policy windows do not depend on current source arrival. |
| RA-07, RA-08 | AAOS-CTL-08/05: related supporting documents only; a duplicate exclusion must retain a live survivor. |
| RA completion | Five RA corrections accepted; RB-01–RB-04 require correction and independent re-verification. Developer tests alone do not restore acceptance. Preserve `make test`, `make check`, `make batch2-gate`, `make reverification-gate`, `make acceptance-gate`, original review bytes and disclosed setup differences. Only U4 is a permitted NOTE in the maintained RA gate. |
| RB-01 | AAOS-BNK-03, AAOS-CTL-04: RD-01/RD-02 accepted at 0d188fa6…7ea9; RE-01/RE-02 remain independently failed. Owner D-026 supersedes retargeting semantics and adds RE-03 authorized no-release/selection controls; D-029 preserves frozen approvals while blocking incoming versions until reopen; independent verification of the new checkpoint, including all 336 orders and this clarified boundary, remains required. |
| RB-02 | AAOS-CTL-09, AAOS-BNK-02: replaced support includes re-pointed old keys, not only withdrawals; old/current suppliers remain independent of acceptance. |
| RB-03 | AAOS-KNO-04, AAOS-CTL-01: semantic rule history follows coverage across general/item scope and new keys; unrelated values/descriptions/scopes do not bar review. |
| RB-04 | AAOS-BNK-02, AAOS-CTL-09: disclose prior-statement revisions; continuity depends on active own-period acceptance for all relying items; revocation invalidates dependents. |
| PR-01–PR-17 | Split product/implementation states and evidence, correct universality/dependencies/traces, add explicit proposed shared scope/reserved decisions and repeatable fault-tested checks; PR-15 removes the client name from shared state. Proposed requirements do not authorize implementation. |

### Retained future concerns, without new implementation authority

- **DE-1:** Per-item rather than workflow/period invalidation — AAOS-CTL-07. Conservative current invalidation is not an accounting defect.
- **DE-2 / DE-4:** Receipt aggregation and non-calendar statement cycles — AAOS-BNK-06. Client policy is required.
- **DE-3:** Cross-period economic duplicate detection — AAOS-BNK-05 / AAOS-CTL-05; current RA-01 locked-chain protection does not prove comprehensive cross-period matching.
- **DE-5:** Replace trial-balance/statement document checklist placeholders with validated outcomes as those capabilities exist — AAOS-GL-04 / AAOS-CLS-01.
- **UC-4 / U4:** Removing a superseder does not restore the predecessor automatically; both removals remain visible. Restoration semantics require provider/client validation at G2 — AAOS-BNK-03. This was an allowed NOTE, not an assigned defect.
- **UC-5:** Real authority grant revocation/admin independence — AAOS-CTL-03, required before G1.
- **UC-6:** Duplicate payment-row disposition vocabulary may need work; Fable observed this by reading, not an executed defect. Preserve it under AAOS-BNK-05 / AAOS-CTL-05 for reproduction and assignment; do not label fixed or expand current work.
- **UC-7:** New same-period move rows are prevented by RB-01; historical rows remain immutable. Receipt move rows can still show had_approval=0 even when the supported root charge had approval; this remains a disclosed metadata limitation, not a changed accounting outcome.
- **UC-8 / UC-9:** Cross-period mandate policy signature behavior and independent journal-support disposition probing remain observations with the independent review's stated execution limits. Existing developer regressions are not relabeled independent verification.

## Requirements beyond the user's summary and unresolved decisions

Additional specificity found in the source specifications is retained above: zero-model application-owned execution and mandatory-review failure behavior (AAOS-EXE-07); portable approved knowledge and separate held-out/annual-gap coverage (AAOS-KNO-06/AAOS-OBS-04); complete checking coverage, one posting route and uncertain provider outcomes (AAOS-INT-05/06); actual operator teach-back and January source availability (AAOS-BB-02/03/06); production identity/grant lifecycle, environment separation and recoverable retention (AAOS-ARC-05/AAOS-CTL-02/03/12/13); general currency and actual versus projected balances (AAOS-GL-04/05/AAOS-BNK-04); atomic exports/external audit anchors (AAOS-CTL-11); and pause/cancel, economic baselines and cross-environment cost allocations (AAOS-EXE-06/AAOS-OBS-01/03). Source proposals for consolidation/intercompany support remain uncommitted extensions within AAOS-RPT-01 until their need is established.

| Apparent conflict | Current resolution; no clarification needed to continue this documentation task |
| --- | --- |
| Original handoff says its broader BUILD_PLAN is authoritative and includes executive/growth roles. | User's accounting-only general-platform instructions supersede that scope. The original package stays untouched; reusable accounting controls are retained. |
| Original stack/default milestone plan differs from the working Python/SQLite/static application. | D-002 and Fable's explicit retain-stack recommendation govern the present build. Hosting/isolation/concurrency/support requirements trigger justified migration decisions later; no speculative rewrite now. |
| Early D-005 says every input/config change invalidates approvals; later T-06 requires relevance. | Historical wording is retained; T-06 and later corrections govern current behavior. AAOS-CTL-07 records the bounded current granularity. |
| Historical gates required known Batch 2 defects to remain failing. | Later explicit corrective/Batch 2 instructions supersede those checkpoint expectations. Current repaired cases must pass; preserved originals document the history. |
| Broader handoff keeps communications human-sent; current product request preserves future controlled sending. | Current build remains human-sent/no-send. AAOS-COM-02 preserves the later product direction behind a new capability/policy/action-specific authorization, without widening existing G3 permission. |
| Bird Bowl independent hosting versus centralized Supporting Strategies deployment. | Both are supported product options from one codebase. Neither means a provider is selected or that a client must depend on the central app. |

The following decisions genuinely remain open. They do not block maintaining the register or the existing corrective verification work. Do not infer answers from fictional fixtures.

| Decision requiring validation/clarification | Who/when; affected IDs |
| --- | --- |
| Bird Bowl legal entity/book, applicable framework/basis/jurisdiction, actual chart/dimensions and current Desktop/QBO conversion/book of record. | Authorized client/accounting lead in writing before G1; AAOS-KNO-01/03, AAOS-GL-01/04, AAOS-INT-01. Same discovery applies to every future client. |
| Actual sales, deposit, payroll/tip and close procedures, supporting sources and known reviewed outcomes; whether AP/AR exist in the ledger. | Luis/Theresa and the accounting authority, authorized knowledge capture/G1; AAOS-BB-01–06, AAOS-AP-01, AAOS-AR-01, AAOS-CLS-03. No actual procedures for these processes are supplied by the pilot specification. |
| Which statement is authoritative, source coverage, line identity, cutoff/cycles, late corrections, receipt tolerance/aggregation/substitution and approved treatments for credits, fees, transfers, assets/prepaids/personal/FX spend. | Client/accounting lead before the relevant G1 workflow; AAOS-KNO-04, AAOS-BNK-02/05/06, AAOS-CTL-04/08/09. |
| Named preparers, policy approvers, independent item reviewers, disposition/finalization/lock/reopen administrators and Theresa's limits. A small team may ask policy approvers also to review their own rule's output; current controls bar that. | Client/product owner and independent accounting review before G1; AAOS-CTL-01/03. No exception is assumed or implemented; any proposed alternative needs an explicit documented control decision. |
| Central deployment operator/company authority versus optional Bird Bowl host; Jeff's platform/support scope, data ownership/licensing, secret administrators, billing/model payer and any SS accounting co-management engagement. | Relevant company/client authorities and proposed support owners before G2/G4; AAOS-ARC-03/04, AAOS-BB-07. Render is a reference proposal for SS, not a purchased/chosen client platform. |
| Provider-specific read/report/attachment/portal/write capabilities, bank/intake vendor, one posting route and source-removal/restoration semantics. | Verify current official provider documentation and account entitlements before a named G2/G3 authorization; AAOS-INT-01–06, AAOS-BNK-03/05. No unsupported bank-feed UI operation is presumed available. |
| Actual cadence/timezone, evidence freshness/no-evidence exceptions, escalation/review SLA, management permissions, cost ceilings/concurrency, materiality thresholds and review-time estimation basis. | Product/client/accounting owners before real recurring work or paid use; AAOS-EXE-02/03/04, AAOS-BRF-01/02/03, AAOS-OBS-01/02/03. Earlier numeric engineering proposals are not automatically ratified accounting-client limits. |
| Whether and under what distinct policy an agent may send requests/collections, to whom, with which review/standing limits. | Product/client authority after a separately assigned capability/control design; AAOS-COM-01/02. Current permission remains no sending. |
| Whether Fable accepts this RE/PRV response; whether the accounting owner accepts G0. RB-02–04 and all five additional statement setups were accepted at their named checkpoints. | Independent reviewer then human gate owner, current priority; AAOS-GOV-03. Until recorded, Batch 3 and later readiness gates remain closed. |

## Register change record

| Date | Change | Authority/evidence |
| --- | --- | --- |
| 2026-11-15 | Established 76 stable requirements, source/backlog/correction crosswalks and open decisions; made universal multi-client scope explicit. No feature implementation or gate change. | Current user assignment/clarification; existing sources above; linked decisions/progress record the documentation checks. |
| 2026-11-15 | Saved the exact combined Fable prompt and packaged current documentation separately from the unchanged RA checkpoint for independent review. Requirement statuses, implementation order and gates unchanged. | User's packaging request; D-008; FABLE_PRODUCT_AND_RA_REVIEW_PROMPT.md; adjacent new-bundle checksum/verification report. |


| 2026-11-16 | Applied PR-01–PR-17: independent-failure states, split decision/implementation fields, scope/evidence/needed-for metadata, shared proposed lifecycle/connectors/operating-source requirements, explicit reserved scope, client-specific fact relocation, dependency/trace/parameter corrections and executable checks. Original 76 IDs retained; 12 new IDs documented without feature implementation or Batch 3 authority. | Returned independent reviews; user correction assignment; D-010–D-012; docs/corrections_rb/. |
| 2026-11-16 | Recorded the PR-11 confirmation in AAOS-BB-01 and AAOS-BB-02: procedure documentation outside the application may proceed before G1 with existing client access; client records enter the application only after human G0 acceptance and explicit G1 authorization; December 2026 is the designated held-out validation month, with December cases and expected results kept separate from November teaching examples. Scope note, acceptance criteria, target stage and trace of those two records only; no product decision, implementation state, gate or other record changed. | User's written confirmation as product owner and accounting lead; D-016; D-017 (edited by Fable at the user's instruction as a limited exception to the V2 working-file freeze). |

| 2026-11-16 | RC/PRV authorized correction pass: PRV-01 records seven independent conclusions; PRV-02/03/04/05/06/07/08/10 enforce evidence, state, boundaries and dependencies; PRV-09 supplies complete inventory. D-016/D-017 wording retained. No new product decision or operating gate. | User correction assignment; immutable RB/PR reports; D-018–D-020; docs/corrections_rc/. |

| 2026-11-16 | PRV-11 records RC-01–03 acceptance at 9a85c78a…2454 and continued RD-01/RD-02 failure; extends both arrival-order criteria and records Q02 acceptance binding. PRV-12 anchors all seven current verdicts to pinned reviewer files; PRV-13 guards the client display name. All product decisions/states and AAOS-BB-01/02 wording are unchanged. | CODEX_RD_CORRECTIONS_PROMPT.md; immutable RC review; D-022–D-024; docs/corrections_rd/. |

| 2026-11-16 | PRV-14 records RD acceptance and RE failures, incorporates owner feed contract D-026, adds the third pinned reviewer authority and updates exact RE re-verification scope; PRV-15 enforces the existing seven-row order. No state/product decision or BB-01/02 field changes. | CODEX_RE_CORRECTIONS_PROMPT.md; immutable RD review; D-026/D-027; docs/corrections_re/. |
