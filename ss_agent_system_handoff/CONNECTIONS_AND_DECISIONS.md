# Decisions and Connection Readiness

Version 1.4 — November 14, 2026

BUILD_PLAN.md is authoritative. This register tells the implementer what is settled, what can be chosen during local development, and what waits for the later connection milestone.

## Confirmed direction

| Decision | Meaning for implementation |
| --- | --- |
| Full business development scope | Preserve Strategy, Marketing, Sales, Client Success, COO, Finance, People Development, Legal & Compliance, and independent review. |
| Executive direction | Expand the existing strategy_lead into the Executive Director (CEO function), responsible for vision proposals, approved direction, priorities, director tradeoffs, execution follow-through and outcomes. |
| Target human participation | Humans primarily handle meaningful approvals, exceptions and client communication; required accounting/legal judgment remains explicit. Actual autonomy must be demonstrated by workflow. |
| Standing internal authority | Approved, bounded mandates allow recurring/internal work without repeated prompts. Material strategy/scope changes and reserved actions still require their own human decision. |
| Company initiative from the outset | Luis will align sponsorship and authority with Danielle. Company systems and governance support the pilot; Luis, Sarai and Michael are the initial cohort. Wider rollout follows proof. |
| Legal & Compliance | Own contract/policy consistency, obligations and counsel preparation. Targeted review supports every function; it does not grant signing authority or replace qualified counsel. |
| COO is horizontal | Capacity, delivery, efficiency, quality and systems affect the entire team; bookkeeping and close execution sit within that workstream. |
| Discovery led by agents | Directors inspect evidence, identify gaps, develop alternatives and recommend priorities. Luis supplies judgment and business decisions. |
| Human strategy and communication approval | Agents can prepare complete work within an approved mandate. Outgoing communications remain human-sent. |
| Preserve current accounting logic | Import existing Claude instructions, checklists and examples as versioned procedures when supplied. Validate changes rather than replacing everything. |
| Pilot team | Luis, Sarai and Michael; Danielle holds the relevant company authority. Skills, availability and exact access remain to be established. |
| Revenue ambition | $750,000-$1 million, working interpretation: annual revenue of the managed portfolio. Definition, baseline and time horizon still need confirmation. |
| Technology direction | Codex or Claude Code builds; Claude supplies reasoning when needed; Render remains the intended SS host. Bird Bowl's accounting module may use its own verified host. |
| Bird Bowl scope | Selected candidate for accounting execution only under the COO. The broader executive/director/growth system stays within SS; no other client or company data is exposed to Bird Bowl. |
| Bird Bowl knowledge plan | Luis intends November–December 2026 work with Claude to produce approved portable procedures, skills, examples, decisions and corrections. Separate validation and Theresa's participation must establish workflow readiness; chats alone and calendar dates do not. |
| Accounting execution | Application-owned adapters call supported QuickBooks APIs directly. Deterministic rules can run without Claude; model assistance is optional and never replaces validation or required review. |
| Testing before deployment | The actual local application can be tested before hosting. The proposed sequence then permits a private company test deployment before a separately approved production release. |
| Connections after the plan | No connections during planning. Coordinate company setup with Danielle; the local synthetic build needs no live credentials. |
| Funding preference | Use available company Claude API credits first. Luis may cover an agreed limited amount of additional pilot expense. |
| Business boundaries | SS data and opportunities remain exclusively SS. Ledger Bridge is separate. North Star retains its distinct personal identity. |

## Selected engineering defaults

These choices let the coding agent proceed. They can be revised with a written architectural reason if an existing repository or a measured requirement warrants it.

- Python/FastAPI backend, React/TypeScript interface, PostgreSQL, one application image with separate web and worker processes.
- Versioned role manifests, structured artifacts, an explicit orchestrator and trusted tool router.
- Deterministic FixtureProvider first; an unconnected Anthropic provider behind the same interface.
- PostgreSQL job queue and bounded PostgreSQL artifact storage for the first pilot.
- Local synthetic demo authentication; standard OIDC for hosted staging and production, including hosted synthetic demos.
- Local/staging/production environments are separate from demo/evaluation/connected-pilot modes. Credentials, databases, approvals, queues and enabled schedules do not cross environments automatically.
- Two concurrent model calls globally within each environment's application deployment; delegation depth two; eight unique delegated tasks, thirty calls and thirty active-work minutes per root; three critic review attempts per artifact lineage. Counters survive retries and resumptions. Separate environment budgets are allocated under one company ceiling.
- All connection, external-spend, live-write and schedule flags disabled until configured.
- One strategy-to-draft workflow first, with the other business views and the close demonstration following in the same local-build plan.
- One executive briefing and decision/exception inbox, supported by a versioned vision register, trusted standing-mandate checks and durable operating cycles. Live schedules remain off until authorized.

## Decisions deliberately deferred

| Item | Why it matters | Earliest gate |
| --- | --- | --- |
| Ratified vision, operating mandate and materiality thresholds | Lets the executive act independently within clear authority and know which decisions to escalate | Before delegated live recurring work |
| Executive cadence and exception-routing preferences | Defines when work wakes, how related issues are consolidated and who receives decisions | Before any live schedule or notification channel |
| Danielle's sponsorship, legal entity and delegated authority | Company-level scope does not establish national/franchisor authority or existing approval | Before company account setup and access |
| Company repository/account controllers and recovery access | Avoid later account transfer and dependence on Luis's personal credentials | At company setup |
| Approved agreements, policies and counsel contact | Establish actual obligations, review triggers and escalation paths | Before affected legal review or commitment |
| Implementation ownership and pre-existing asset reuse | Clarify company implementation rights without assuming a transfer of North Star | Before material IP integration or external commitment |
| Current revenue, goal definition and target period | A credible growth bridge needs a real baseline and timing | Discovery with real evidence |
| Human approval authority by action and client | Determines which authenticated person may approve what | Before connected pilot |
| Staff hours, skills and coverage | Prevents invented utilization and unrealistic delegation | Capacity analysis |
| Bird Bowl workflow, current ledger and procedure | Candidate is selected; actual QBO readiness, sources, rule set and reviewer remain to be verified | Before accounting read/draft pilot |
| Bird Bowl hosting and administration | Jeff's platform name, capabilities, authority, identity, secrets, persistence and costs are unknown | Before optional client-module deployment |
| Bird Bowl transaction intake and posting route | Compare actual complete checking activity with card-only feeds; assess direct bank, aggregator, Expensify or native QBO routes. Expensify would be considered only for bank transactions if purchased. Actual institutions/accounts, coverage and provider access are unverified; no vendor is selected. Require one posting route per transaction, source-to-ledger traceability, pending/posted handling and duplicate controls | Before the affected feed or posting capability |
| Bird Bowl operator and support agreement | Confirm Theresa's assigned authority, Jeff's technical responsibilities, accounting review/close ownership and any SS co-management scope/fees. Co-management is a proposed commercial opportunity, not a signed engagement | Before operating handoff or service commitment |
| Model selection and role configuration | Quality, latency and cost must be measured on relevant work | M6 |
| Actual Team credits and Console organization | Funding is shared; current balance and claim status are unknown | M6 |
| Personal spending ceiling and review date | Defines Luis's bounded contribution and the adoption decision | Before any personal expense |
| Authentication/identity provider | Connected access must use verified human identities | Before hosted access |
| Source retention and backups | Establishes approved handling and recovery for company records | Before real-data hosting |
| API scopes and account entitlements | A connection alone does not prove required capabilities | Per connector |
| Render plans and full recurring cost | Includes web, worker, database, storage and relevant workspace plan | Before deployment |

Unknowns should appear as unknowns. They do not prevent local construction with synthetic fixtures.

## Connection packet after M5

Prepare one consolidated request with the exact purpose, provider, required capability, account owner, data scope, cost limit and validation step. Do not ask for every possible connector. Connect only what the selected first evaluation needs.

Company sponsorship and administrative planning can happen earlier without enabling runtime connections. TESTING_AND_ROLLOUT.md supplies a proposed company charter, local user test, private staging acceptance and release gates. Any production cohort is initially the named pilot team rather than everyone in the office.

### Claude

- Identify the company Console organization and its owner/admin.
- Verify whether Danielle has claimed the Team benefit, its current allowance, remaining balance and other consumers.
- Create a dedicated pilot workspace and scoped access/key under the agreed company arrangement.
- Configure run and monthly limits, permitted models, rate-table version and alerts.
- Store credentials in the approved environment/secret mechanism; never request raw secrets in ordinary chat or commit them.
- Execute a small authorized evaluation, record actual usage and failure handling, and keep external effects disabled.

The current product documentation treats Team credits as a pooled benefit claimed into one Console organization. A scoped workspace controls resource access and usage but still uses centralized billing. [S5][S6]

Local synthetic development needs no additional Claude subscription. The planned company application uses authorized API authentication under company control. Do not build a dependency on exporting a user's session tokens or moving a personally owned deployment into the company later.

### Company information and existing Claude assets

- Obtain only the selected files/exports and client procedures from an authorized person or approved connector.
- Preserve original instructions and checklist versions; identify their owner, effective period and unresolved contradictions.
- Normalize them into source records and candidate procedures. Ask for human validation before activating consequential accounting actions.
- Verify file mapping, client scope, date/period and completeness.
- Do not assume the application's model connection brings Claude Projects, chat memory, account credentials or connector permissions with it.
- For Bird Bowl's planned November–December work, capture approved reusable procedures and scoped corrections with original evidence. Keep raw chats/proposals separate, preserve a held-out validation set and record task coverage. December close waits for source availability; no date grants readiness or deployment authority.

### HubSpot

- Danielle provides the appropriate company access; no empty personal HubSpot account is required to build the local system.
- Verify the actual app/authentication type and allowed scopes against current HubSpot documentation.
- Begin with the records required for the chosen discovery: contacts, companies, deals, notes/activities, reasons, timestamps and communication restrictions where available.
- Handle absent custom fields honestly; use an explicit mapping and provenance record.
- Test pagination, incremental synchronization, merges/deletions, duplicate records, restricted contacts and stale history.
- Keep all analysis and derivative opportunities in the SS organization. No routing of declined leads to Ledger Bridge.
- Retain an authorized export path as a limited alternative when a live API connection is not yet available.

### Accounting systems

- Use Bird Bowl as the selected accounting pilot candidate and confirm one bounded documented process; selection does not establish live access or completed conversion.
- Confirm the external company/realm, accounts, currency, period, source completeness and human reviewer.
- Verify every required read/report/attachment capability independently.
- Build the read-and-draft workflow before any write.
- Respect the documented distinction between QBO ledger records, pending bank-feed actions and reconciled status. [S7][S8]
- Treat BILL, Sage and other provider access as unverified until actual entitlements and supported endpoints are checked.
- A missing API capability becomes an explicit manual or separately validated interface task. No undocumented private endpoint workaround.
- Keep Bird Bowl's deployment accounting-only. Confirm its platform with Jeff and verify the relevant client/company authority. Agree scoped credentials, administrators, model usage if needed, costs and maintenance; do not transfer shared SS credentials or company data by default.
- Classify steps as deterministic, model-assisted or human. Test the deterministic path with zero model calls; unresolved interpretation stays an exception unless approved model assistance is available. Preserve each workflow's review requirements.
- Resolve the transaction-intake choice against Bird Bowl's actual accounts and required activity, including whether a route covers full checking activity or only card transactions. Compare direct bank, aggregator, Expensify and native QBO options without assuming capability or choosing a vendor. Identify one posting route for each transaction; preserve source IDs and reconcile pending-to-posted changes, removals and duplicates. These are design requirements to verify, not sourced guarantees about any provider.

### Render

- Review the generated Blueprint and all resources and costs before provisioning.
- Verify business-controlled access for the appropriate people and choose a workspace plan that supports it.
- Create separate staging and production configuration under the company-controlled workspace when authorized; provision only the environment currently needed.
- Configure real authentication, secrets, health/readiness checks, one controlled migration step, worker shutdown, private database connectivity and backups.
- Verify environment boundaries for credentials, data, queues, webhooks, logs and budgets. A private URL or Render network isolation is not application authentication. [S11]
- Ensure artifact storage persists across web/worker restarts; exercise restore.
- Keep automatic deployment/sync inactive until approved; use a specific tested release for promotion. Review rollback and database migration compatibility. [S12]
- Deploy only at the authorized gate; the handoff does not provision services. Render documents both Blueprint configuration and payment-method changes. [S3][S9]

## Funding and company adoption

Start by using the available company API benefit within an approved pilot limit. Record gross API usage before credits as well as cash paid. Company credits are a finite shared resource even if no additional cash is charged.

Company administrative control applies from setup even if Luis contributes funds. If he pays any pilot expense, agree a bounded contribution and payment arrangement that cannot charge unrelated company activity. Funding does not silently change ownership, approval authority or access. An additional company-controlled billing organization should be considered only if actually needed; it does not automatically inherit Team credits linked elsewhere.

Where more than one environment can incur model costs, allocate each an explicit portion of the approved company budget and consolidate usage. A staging budget and a production budget must not each inherit the whole pilot allowance. Prefer one active paid evaluation environment initially.

Before incurring additional expense, document the pilot period, covered charges, maximum personal contribution, review date and company adoption criteria. Changing future billing is different from agreeing to reimburse past payments. Anthropic and Render provide payment-method management; actual account permissions must be verified. [S9][S10]

## Pilot scorecard

| Measure | Required interpretation |
| --- | --- |
| Quality | Material errors, evidence completeness, exception handling, human reviewer acceptance and reasons |
| Net human time | Baseline preparation/review/rework minus new supervision/review/correction/recurring maintenance; one-time build/training separate |
| Executive autonomy | Necessary and avoidable interventions per completed workflow, approval burden, exception age, missed issues and net leadership time; preserve quality and required judgment |
| Bird Bowl operating readiness | Defined task coverage on separate validation cases, Theresa's teach-back/independent operation, observed unattended authorized completion, avoidable interruptions, required reviews and support effort; no blanket human-accountant replacement claim |
| Delivery | Comparable work completed on time, elapsed cycle, unresolved exceptions and review bottlenecks |
| Unit operating cost | Labor/review/maintenance plus gross API/tool usage and allocated infrastructure, including failed/incomplete work |
| Business development | Qualified opportunities, proposal quality, preparation time, stage progression, later actual wins |
| Retention and expansion | Concerns resolved, commitments fulfilled, approved scope changes and observed retention/expansion over an appropriate period |
| Economics | Earned revenue and contribution, recurring run rate and project fees separately; no double counting of saved time |

Set practical thresholds with Luis and Danielle before live testing. The acceptance tests include proposed evaluation thresholds, not an approved company standard.

## Adoption decision

Present Danielle with the selected workflow, baseline, demonstrated results, exceptions, human effort, gross and cash operating cost, remaining limitations, proposed monthly budget and support owner.

The decision can be to continue and fund the company initiative, expand the approved rollout, revise the pilot, or stop. A successful narrow workflow does not automatically approve all departments, clients or write capabilities. Approval of a test deployment does not authorize production or office-wide release.

Sources referenced above are listed in SOURCES.md.

EXECUTIVE_AUTONOMY.md defines the CEO function, standing authority and the continuing operating cycle. The plan specifies these capabilities; no executive process or schedule is active yet.
