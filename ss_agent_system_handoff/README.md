# Supporting Strategies Agent System Implementation Handoff

Prepared for Luis on November 14, 2026. Version 1.4.

This package is a specification for Codex or Claude Code to implement. It covers the complete business development system for a company-sponsored Supporting Strategies pilot, with Luis, Sarai and Michael as its first users. It includes strategy, marketing, sales, client success, operations, finance, people development, Legal & Compliance, and accounting execution. The COO coordinates operational dependencies across these functions. The independent critic reviews work across the entire system. Luis will agree company sponsorship and authority with Danielle before company setup and connections.

The existing strategy lead now performs the Executive Director/CEO function: develop and steward the approved vision, coordinate the seven directors, keep authorized work moving, and bring humans complete approvals, exceptions and client communications. EXECUTIVE_AUTONOMY.md defines the authority, operating cycle and evidence needed to prove this target model.

## Start here

1. Put this package in an isolated project folder or an appropriate existing repository.
2. Give the coding agent START_PROMPT.txt.
3. Have it read BUILD_PLAN.md, AGENT_PLAYBOOKS.md, EXECUTIVE_AUTONOMY.md, IMPLEMENTATION_BACKLOG.md, ACCEPTANCE_TESTS.md, TESTING_AND_ROLLOUT.md, CONNECTIONS_AND_DECISIONS.md, and AGENTS.md before building.
4. The first implementation must run locally with deterministic synthetic fixtures and no external account connections. It must visibly distinguish simulated output from live model output.
5. Connect the selected model, company systems and hosting only after the offline implementation is demonstrated and the connection step is authorized. Bird Bowl is an accounting-only candidate with an optional separately verified host. Planning and local construction do not authorize deployment, spending, sending messages, or accounting writes.

## Package contents

| File | Purpose |
| --- | --- |
| BUILD_PLAN.md | Authoritative product and technical specification, boundaries, data contracts, workflow states, and architecture. |
| AGENT_PLAYBOOKS.md | Strategy lead, director, specialist, and critic mandates; diagnostic methods and output standards. |
| EXECUTIVE_AUTONOMY.md | CEO function, vision and strategy register, standing authority, proactive operation, consolidated decisions and autonomy measures. |
| BIRD_BOWL_ACCOUNTING_PILOT.md | Bird Bowl's accounting-only scope, November–December knowledge handoff, operating-readiness criteria, proposed support split and unresolved transaction intake. |
| IMPLEMENTATION_BACKLOG.md | Ordered implementation milestones, deliverables, dependencies, and completion gates. |
| ACCEPTANCE_TESTS.md | Concrete product, control, reliability, accounting, and evaluation scenarios. |
| CONNECTIONS_AND_DECISIONS.md | Confirmed decisions, provisional assumptions, deferred connections, and pilot adoption measures. |
| TESTING_AND_ROLLOUT.md | Company control from setup, local user testing, private staging, production release, rollback and wider rollout. |
| START_PROMPT.txt | The instruction Luis can give Codex or Claude Code with this package. |
| AGENTS.md | Repository-specific implementation instructions for the coding agent. |
| config/pilot_policy.example.yaml | Illustrative policy configuration. External costs, writes, schedules, and connections start disabled. |
| fixtures/business_scenarios.json | Fictional business cases for testing whether recommendations change with the evidence. |
| fixtures/close_scenario.json | Fictional accounting case with explicit expected reconciliations and exceptions. |
| fixtures/legal_scenario.json | Fictional contract/policy mismatch, obligations and authority tests; no claims about actual company agreements or law. |
| SOURCES.md | Primary product documentation and the scope of the claims it supports. |

## Authority and status

The user's current instructions and the project's applicable higher-priority instructions govern execution. BUILD_PLAN.md is the authoritative product specification within this handoff. Supporting files explain its implementation; resolve a conflict in favor of the narrower data access and action authority, record the discrepancy, and continue independent work. Ask Luis only for a material unresolved business decision or a genuinely blocked connection.

The $750,000-$1 million annual managed-portfolio revenue target is a working interpretation of Luis's goal. Current revenue, timeframe, staffing availability, margins, budgets, and account balances remain unknown. Synthetic examples are not estimates of the real business.

This is a Supporting Strategies implementation. Supporting Strategies client and prospect data, including unsuccessful HubSpot opportunities, remain exclusively within that operation. Ledger Bridge is a separate business context. Luis's Project North Star remains a distinct personal framework; this handoff does not determine intellectual-property ownership or transfer that framework.

No application has been built or deployed by delivering this package. No live account connection, model evaluation, client-book processing, or external communication has been performed.

## Version 1.4 changes

Added the planned November–December 2026 Bird Bowl knowledge capture, portable approved procedures and separate validation cases. Defined Theresa's independent operation, demonstrated unattended authorized work, interruption measures, and the proposed split between Jeff's technical support and Supporting Strategies accounting co-management. Co-management remains a commercial opportunity, not an agreed engagement. Added two acceptance cases, bringing the current total to 61. Transaction intake remains an unresolved design choice; actual checking/card coverage, one posting route and duplicate controls must be verified. Dates and successful tests do not activate connections, posting or deployment.

## Version 1.3 changes

Selected Bird Bowl as the accounting pilot candidate only; recorded optional hosting on its own platform without moving the SS business system. Added direct application-to-QuickBooks execution, deterministic accounting with optional model assistance, explicit review-policy preservation and two acceptance cases, bringing the total to 59.

## Version 1.2 changes

Expanded the existing strategy lead into the Executive Director/CEO function, preserving its role ID and the nine-role catalog. Added vision ratification, standing internal mandates, proactive bounded work, one decision/exception inbox and autonomy evaluation. The package now specifies 57 acceptance scenarios. Human client communication and existing company, accounting, Legal and release authority remain explicit.

## Version 1.1 changes

Added Legal & Compliance as a peer director, company control and sponsorship planning from inception, an explicit local-to-staging-to-production test path, human user acceptance and release gates, environment isolation and budget allocation, and legal review fixtures. Earlier role, critic, accounting and data boundaries remain in force.
