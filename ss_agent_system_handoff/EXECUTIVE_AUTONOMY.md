# Executive Direction and Autonomous Operation

Version 1.2 — November 14, 2026

## 1. Target operating model

Luis wants a system that develops the business, keeps authorized work moving and brings humans in primarily for approvals, meaningful exceptions and client communication. The application must reduce the management required to obtain useful results. It should discover needs and finish preparation without relying on a new chat prompt for every next step.

The Executive Director performs the CEO function and expands the existing strategy_lead role. It is one executive agent role, not a second lead layered onto the existing one. Seven peer directors remain: Marketing, Sales, Client Success, COO, Finance, People Development and Legal & Compliance. The independent critic can report material unresolved findings directly to the authorized humans.

Human/company governance ratifies vision and material choices. The executive develops proposals, stewards the ratified direction, manages the integrated operating plan and supervises execution. The COO coordinates delivery, capacity and process execution within that plan. A CEO title does not appoint an officer, create signing authority or establish competence.

This is a target to validate by workflow. Routine accounting review, professional judgment, final close sign-off and unresolved legal decisions remain assigned to the appropriate people under the existing policy. Required review is part of the human role; any remaining manual preparation must be measured rather than hidden.

## 2. Vision and strategy register

Maintain a durable, versioned record of:

- Purpose, desired client/service profile and value proposition.
- Company-approved values, service standards and non-negotiable constraints.
- Growth, profitability, quality, client experience, capacity and people-development objectives.
- Time horizons, current priorities, measures, owners, evidence, assumptions and unresolved choices.
- Proposed changes, the authorized human's decision, effective period and superseded versions.

The $750,000–$1 million portfolio ambition remains a provisional target interpretation requiring a baseline and timeframe. Do not turn it into permission to ignore margin, quality, staff capacity or client commitments.

When information is sparse, the executive should investigate the authorized evidence and propose a small number of coherent directions with tradeoffs. It should not ask Luis to invent the vision document or every department's strategy. Missing values and business constraints remain unknown until discovered or ratified. A proposed vision is distinguishable from the active company-approved version.

Translate ratified direction into quarterly objectives, nearer-term priorities and scoped work. These are configurable planning horizons rather than schedules activated by this document. Review outcomes and propose changes when evidence warrants them. A substantive change in target clients, service commitments, objectives, budget or risk tolerance needs its corresponding human decision.

## 3. Standing authority and reserved decisions

A standing operating mandate gives permission for a defined class of internal work. Its human approval is retained; each qualifying step does not require another click.

| Work | Executive behavior |
| --- | --- |
| Research, analysis, internal drafts, permitted revisions, evidence refresh and agent-task ordering within an active mandate | Proceed autonomously; record sources, authorization and results. |
| A new strategy or material change in scope, goals, resources or commitments | Prepare a complete decision package and request the relevant human decision. |
| Final client communications, contract execution and designated accounting decisions | Prepare reviewed work; retain the existing human action/approval process. |
| An unavailable capability, expired authority, denied access or prohibited action | Keep it blocked; report the specific dependency and continue independent authorized work. |

A mandate record includes ID/version, human approver, strategy version, organization/environment/client scope, allowed actions and predicates, triggers, budget/capacity bounds, review standard, effective date, expiry, revocation and escalation conditions. Unknown consequential limits do not mean unlimited authority. Demo mandates are explicitly synthetic and cannot cross into a live environment.

Trusted application code checks those fields before dispatch and before any consequential execution. The model can request work but cannot approve or broaden its own mandate. A mandate for internal preparation does not authorize a client message, CRM mutation, journal posting, changed staff obligation or larger spending ceiling. Later routine accounting rules remain a distinct M8 authority under BUILD_PLAN.md.

Version the mandate separately from the artifact it produces. A harmless internal draft revision does not require reapproving the whole operating mandate. An exact final communication or consequential action still binds to its current payload/version. Changes in evidence or scope revalidate affected preconditions; approval history remains inspectable.

## 4. Executive operating cycle

When an approved schedule, relevant event, source arrival or dependency resolution occurs:

1. Validate the trigger, active strategy, standing mandate, source freshness, allowed scope and remaining resources.
2. Examine material changes, completed work, outcomes, obligations, open exceptions and pending human decisions.
3. Select the work with the strongest supported business priority. Consult only the relevant directors and provide complete briefs.
4. Resolve competing recommendations against the approved goals and constraints. Distinguish an internal task-order choice from a material business decision needing approval.
5. Execute authorized internal work, assemble evidence, request independent critique and have the producer make bounded revisions.
6. Present a complete human decision or communication package only where needed. Record other completed work in the operating history.
7. Measure what happened, preserve state and the next wake condition, then stop until eligible work or a configured trigger exists.

Use durable jobs, occurrence IDs and checkpoints rather than a continuously running model conversation. A repeated event must update or reuse the existing work instead of creating duplicate initiatives. A new recurrence is not an excuse to reset counters for unfinished work or bypass an exhausted budget. Seven director tasks plus one critic use the current eight-task root allowance; the executive itself integrates their findings.

Keep live schedules disabled during the local build. Simulated clocks and events demonstrate the cycle offline. A configured schedule later needs an approved purpose, cadence, timezone, scope, budget and stop/review condition. Proposed cadences are a daily operating review, a weekly priority review and a periodic strategy review; actual frequency depends on observed change and the company's preference.

Deterministic monitoring should identify failed/stale jobs and missing heartbeats independently of model output. The initial application displays issues in its inbox and health view. Any future outbound internal notification channel requires its own approved recipients, content policy and delivery test; it must not expose an unrestricted messaging tool to agents or enable client sending.

## 5. Executive judgment across departments

Suppose a fictional Sales analysis finds suitable dormant prospects, Client Success identifies an unresolved client concern, and the COO finds insufficient review capacity. The executive should compare the competing priorities and prepare a coordinated response: service recovery, a proposed capacity remedy, and acquisition preparation timed to confirmed delivery readiness.

It can reorder authorized research and drafting, request the appropriate internal analyses and prepare the work. Reassigning actual employee responsibilities or promising a client start date follows the configured human authority. The executive should show why it recommends the sequence, which alternatives it considered and what evidence would change the decision.

This cross-functional integration is the CEO function. It includes vision, prioritization, tradeoffs, operating follow-through and learning from results. It must not substitute a generic growth recommendation when the evidence calls for retention, capacity or economic repair.

## 6. One human decision and exception inbox

Consolidate the team's output into one interface with separate views for decisions needed, exceptions, ready-to-send client work, completed work and current objectives. Humans can inspect department detail without having to manage separate chats.

Each decision or exception case contains:

- The business question or failure, why it matters, affected scope and current status.
- The best available artifact and original evidence, material unknowns and critic objections.
- A recommended response, alternatives and the exact authority requested.
- Relevant cost, capacity and client implications; a real deadline only when supported.
- The assigned human, allowed response choices and what work can continue meanwhile.

Deduplicate repeated alerts about the same cause. Group related routine decisions for efficient review while preserving each item's content, scope and approve/defer/reject control. Do not hide critical findings in a digest or combine unrelated permissions into a single opaque approval.

Use urgency based on consequence and genuine timing. Critical matters can surface immediately through approved channels; ordinary matters can wait in the next configured review. Without a configured external notification route, do not claim a human was notified outside the application.

No response means no new approval. Keep the affected action waiting, show its age and consequence, and follow the approved escalation policy. Continue other work already permitted. The executive may return a recommended answer with the question, but it must not manufacture a missing client fact or treat silence as consent.

## 7. Independent critique and improvements

Reserve resources for review. Give the critic original evidence, the current strategy/mandate, criteria and artifact. Preserve its findings and direct human visibility even when the executive disagrees. Disagreement can produce a supported revision or an explicit unresolved case; the executive cannot rewrite the review record or label a failed artifact passed.

The executive should propose improved role instructions, procedures, specialist templates and measures based on observed results. Approved reusable templates can be instantiated within scope. New persistent tools, broader permissions, budget increases, executable changes and altered consequential procedures follow the company's versioned change/release process. The system does not promote its own policy changes.

## 8. How to measure autonomy

Track results by workflow and comparable scope:

| Measure | Interpretation |
| --- | --- |
| Completed useful work | Reviewed output or supported task completion, not counts of messages or spawned agents. |
| Human intervention rate | Necessary decisions, useful exceptions, avoidable prompts and manual rescue per completed workflow. |
| Human time | Direction-setting, review, corrections, client communication and recurring maintenance, separately identified. |
| Approval burden | Number, age, reading effort and repeated requests for authority already granted. |
| Exception quality | Material issues detected, missed issues, false alarms, unresolved age and effects on delivery. |
| Outcome quality | Accuracy, client service, timeliness, capacity and economics alongside autonomy. |
| Cost | Gross model usage, cash cost after credits, infrastructure and human effort, including unsuccessful work. |

Low intervention is useful only if quality, required review and exception detection remain acceptable. The system must not suppress cases to improve its score. Agree practical thresholds before the live pilot; do not promise a percentage of autonomy or hours saved without evidence.

M0–M5 demonstrate the mechanics with fictional evidence and simulated triggers. M6 evaluates actual executive/director/critic reasoning on held-out cases. M7 observes limited real workflows with the required humans available. Expand delegated authority only for the action classes supported by those results. Report remaining manual steps directly.

## 9. Implementation links

Implement these requirements through the common evidence, task, authorization, review and UI services rather than a separate uncontrolled executive service. Current product and runtime details must still be verified at implementation. Anthropic's published agent patterns discuss delegated work, feedback from tools, review loops and stopping conditions; they do not establish the business competence of this particular implementation. [S14]

Acceptance cases AT-50 through AT-57 cover the executive role and autonomy requirements. BUILD_PLAN.md remains authoritative; AGENT_PLAYBOOKS.md supplies the executive and director instructions; TESTING_AND_ROLLOUT.md governs company testing and release.
