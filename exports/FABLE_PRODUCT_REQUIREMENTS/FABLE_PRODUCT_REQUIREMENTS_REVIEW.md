# Fable review of the product requirements register

15 November 2026. Reviewed: `docs/PRODUCT_REQUIREMENTS.md` (SHA-256 `34623afc…c50e2`, 76 records) from the documentation addendum, with the addendum's `AGENTS.md`, `DECISIONS.md` and `PROGRESS.md`. Compared against the original specifications in `reference_material/`, Fable's 27-ticket backlog, the RA checkpoint source and my own RA verification in `FABLE_RA_ACCEPTANCE/`.

The addendum is assessed separately from the RA archive. It was not part of that archive's manifest and I did not overlay it. Product approval of a requirement is not implementation authority, client-policy approval or operating readiness, and this review changes none of those.

## Verdict

**Requirements-register acceptance: accepted with required corrections.** The register is complete against the ten requested areas, structurally sound and honest about what is not built. It should be adopted as the permanent register once three status corrections are made (PR-01 to PR-03). Its claim of "Tested" for the locked-period and replacement-evidence controls does not survive independent verification.

| Subject | Verdict |
| --- | --- |
| Completeness against the ten requested areas | Complete. Nothing requested is missing. |
| Universal-platform boundary | Mostly kept. Five shared records carry first-client conditions; four shared requirements a second client would need are absent. |
| Implementation status accuracy | Accurate for 71 of 76 records. Overstated for AAOS-BNK-03, AAOS-CTL-04, AAOS-CTL-09, AAOS-BNK-02 and AAOS-KNO-04. |
| Structure (IDs, fields, dependencies, crosswalk) | Sound. Four dependency entries need correction. |
| AGENTS.md maintenance instructions | Right in intent, not yet enforceable. |

Separate verdicts for RA acceptance (not accepted) and G0 technical criteria (not met) are in `FABLE_RA_ACCEPTANCE_REPORT.md`.

## What I checked mechanically

Script `evidence/register_checks.py`, output in `evidence/register_checks_output.txt`.

- 76 records, 76 unique IDs, all eight fields present in every record.
- Every dependency names an existing record. No self-dependency. No cycle.
- All 27 backlog tickets appear in the crosswalk and name existing records. Ticket dependencies were compared with record dependencies.
- Leading status word: 26 Approved, 26 Tested, 22 Deferred, 1 Implemented, 1 Proposed.
- Priority: 74 Must, 2 Should, 0 Could.
- Target stage: 29 current/G0, 28 future/unassigned, 8 existing Batch 3, 6 G1, 5 "before …".

PROGRESS.md reports the same structural checks. No script for them is in the repository, so they are not repeatable by the next agent (PR-17).

## Completeness against the requested areas

| Requested | Records | Preserved? |
| --- | --- | --- |
| Morning Briefing: six sections, management-wide and client views, permissions | AAOS-BRF-01, BRF-02, BRF-03, OBS-02 | Yes. All six sections are named and the permission tests are stated. Delivery channel is unstated. |
| Hosted scheduled and event-driven execution without the user's computer | AAOS-EXE-01 to EXE-06 | Yes. Durable progress, retries, monitoring, exceptions and bounded standing authority each have a record. |
| One codebase, central deployment with isolated clients, optional client deployment | AAOS-ARC-01 to ARC-05 | Yes. |
| Accounting knowledge, frameworks, verified references, policies, effective dates, charts, procedures, treatments, decisions, evidence | AAOS-KNO-01 to KNO-06 | Yes. |
| All six accounting functions | AAOS-GL-01–05, AP-01–02, AR-01–02, BNK-01–06, CLS-01–03, RPT-01–02 | Yes, with honest "executable today" and "deferred" columns. |
| QBO, Bill.com, Google Workspace/Gmail, Drive, bank activity, authorized portals | AAOS-INT-01 to INT-06 | Yes, as named vendors. No vendor-neutral connector record (PR-08). |
| Independent review, segregation of duties, traceability, document completeness, approvals, period locks, duplicates, correction history, reconciliation validation, credentials | AAOS-CTL-01 to CTL-13, KNO-05, BNK-04 | Yes. |
| Bird Bowl November–December capture, independent validation, Theresa's workflow, sales, deposit, payroll/tip, close | AAOS-BB-01 to BB-07 | Yes, as discovery. The execution they defer has no shared record (PR-09). The November month conflicts with the register's own gate (PR-11). |
| Completion, accuracy, exceptions, interruptions, human effort, review time, model and infrastructure cost | AAOS-OBS-01 to OBS-04 | Yes. |
| Future missing-document requests, collection follow-ups, separate drafting and sending permissions | AAOS-COM-01, COM-02 | Yes. Sending stays prohibited now. |

## Status accuracy

I ran the checkpoint myself and wrote 14 further probes. Where a record says Tested, I compared its acceptance criteria with those results.

**Overstated (documentation defects):**

- **AAOS-BNK-03 and AAOS-CTL-04 (PR-01, P1).** Both say Tested for "full-chain locked-origin" controls. Their criteria say a replacement chain "never leaves the same expense approved in two periods". My probes R01b and R01c approve one charge in two periods. R01b is a regression: the frozen RV submission quarantined it.
- **AAOS-CTL-09 and AAOS-BNK-02 (PR-02, P2).** "Withdrawing/replacing a receipt or re-supplying a matching statement still creates visible holds" is true only when the old key is withdrawn. Re-pointing the old key avoids the hold (R03b, R04b). A restated prior statement is not disclosed to the next period (R04c).
- **AAOS-KNO-04 and the matching clause of AAOS-CTL-01 (PR-03, P3).** Author retention holds for the same rule key and item scope only (R02b).

**Confirmed by my runs:** AAOS-EXE-03 (RA-05), AAOS-CTL-05 (RA-08), AAOS-CTL-08 and AAOS-GL-02 (RA-06, RA-07), AAOS-CLS-02 and AAOS-ARC-02 (teaching month, two-client isolation), AAOS-EXE-07 (no-egress test), AAOS-OBS-04 (RT14b guard tests). The "Current evidence" section's 154 tests and 29/10/21 are reproduced.

**No unbuilt capability is described as built.** Every deferred function (AP, AR, reconciliation, close execution, reporting, integrations, hosting, briefing, communications) is stated as not implemented. I found no deferred capability reported as a defect and I report none as one.

**The status field itself (PR-04, P2).** One field carries both the product decision and the implementation state; 24 records put two status words in it; four equivalent unbuilt integrations carry different statuses; and there is no state for "independently verified", which is the distinction this project turns on.

## Universal-platform assessment

The opening statement, AAOS-GOV-01 and AGENTS.md set the right boundary, and the Bird Bowl section is properly separate. Three kinds of leakage remain.

**First-client conditions inside shared records (PR-07).**

- AAOS-AR-01: "Bird Bowl AR applicability is validated first". A shared capability waits on one client.
- AAOS-AP-01: "unknown Bird Bowl AP practices remain questions".
- AAOS-INT-05: names Expensify, a Bird Bowl candidate vendor.
- AAOS-INT-01: status cites the Desktop conversion. AAOS-KNO-06: target stage names Bird Bowl.

**Shared requirements a second client would need, which do not exist (decisions for product authority).**

- A reusable onboarding and offboarding process. It exists only as AAOS-BB-01 to BB-07 (PR-06).
- A vendor-neutral connector contract. The legacy packet already mentions Sage and other providers (PR-08).
- Execution of sales, deposit, payroll and tip accounting. Only Bird Bowl discovery records exist; consolidation is a Proposed item hidden inside AAOS-RPT-01 (PR-09).
- A list of scope exclusions with decisions: payroll processing, tax and information returns, legal review, payment execution (PR-10).

**In the shared source (code).**

- `service.py` line 827: `state()` returns "actual Bird Bowl accounting policies remain unconfigured" for every client, including the second client in the isolation probes (PR-15, P3 code defect; no accounting effect).
- `validate_profile` requires a `card_accounts` key and one currency for every client, and statements accept one sign convention. The register records the currency and sign limits but not `card_accounts` (PR-16, future enhancement).

## Unresolved conflicts

1. **November capture against gate G1 (PR-11).** AAOS-BB-01 targets G1. G1 needs human G0 acceptance and written client facts. On 15 November G0 is not accepted and RA remains open. The register does not say whether procedure capture as written documentation, outside the application, may proceed. This needs a decision now, because the month is passing.
2. **Register status against independent results (PR-01 to PR-03).** Resolved by correcting the records.
3. **Dependency direction (PR-12).** AAOS-EXE-02 depends on AAOS-EXE-03; the backlog has mandates (T-10) depending on occurrences (T-04).
4. **Priority (PR-05).** 74 of 76 records are Must, so the register cannot say what comes first after G0.

The six conflicts the register itself lists (lines 912–919) are resolved consistently with DECISIONS.md, and its nine open decisions (lines 923–933) are correctly left open. I add one to them: PR-11.

## Lost, duplicated or inserted requirements

- **Lost:** none of the requested areas. Three legacy accounting items survive only by implication: the minimum close package contents, the five separate close states, and the staff/senior task-coverage plan (PR-13). Legacy tests AT-24, AT-25, AT-29, AT-40, AT-58 and AT-59 are not cited by ID.
- **Duplicated:** none that matters. AAOS-CTL-05 and AAOS-BNK-05 share cross-period duplicate detection and say so.
- **Inserted into an unauthorized batch:** none. No new requirement is placed ahead of the corrections or into Batch 3, and the register says so at line 885.

## Vague or untestable acceptance criteria

Most criteria are specific and checkable. Eight are not (PR-14): AAOS-ARC-03 (concurrent clients), EXE-05 (stalled-work monitor), KNO-01, GL-03 (materiality), CTL-12, CTL-13 (recovery targets), BRF-03 (urgency), OBS-01 (thresholds). Where the value is a client or product decision, the criterion should read "value set by the named owner before the named gate".

## Client facts and policy choices needing human validation

The register's open-decision table is complete for these and invents nothing. In addition:

- Whether the feed can deliver a replacement row before declaring what it replaces (bears on RB-01).
- Who may re-attach a receipt to another charge, and how a correction to a closed statement cycle is carried forward (RB-02, RB-04).
- Whether a policy author may review items coded by an identical later rule (RB-03).

## Is AGENTS.md sufficient?

It requires reading the register before implementation, updating it with every feature change, preserving IDs and retaining rejections. That is the right set of duties. It is not yet sufficient (PR-17) because:

1. Nothing says who may raise a status or what a failed independent probe must do to a record. That gap produced PR-01 to PR-03.
2. No repeatable check exists. The reported documentation checks have no script.
3. The rule "record a conflict instead of choosing a weaker control" is in the register, not in AGENTS.md.
4. Nothing says where a second client's facts go.
5. Past authorizations (Batch 1, Batch 2, RA) accumulate with no marked current-authority paragraph.

## Recommended changes, in order

1. Correct the five overstated statuses and their criteria (PR-01, PR-02, PR-03) and update "Current evidence" with this review's outcome.
2. Decide the November capture question (PR-11).
3. Split the status field and add the independent-verification state (PR-04); add the enforcement rules and a register check to AGENTS.md and `make check` (PR-17).
4. Move first-client conditions out of shared records (PR-07).
5. Product owner decides the four shared additions and the ordering field (PR-05, PR-06, PR-08, PR-09, PR-10).
6. Fix dependencies, traces and untestable criteria (PR-12, PR-13, PR-14).
7. With the next authorized code change: client-neutral notice text (PR-15).

Each finding has evidence, a proposed correction, dependencies and exact acceptance criteria in `FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json`.

## Record-by-record assessment

Each record's ID, description, business purpose, priority, dependencies, status, acceptance criteria and target stage were read. "Sound as written" means I would change none of them. IDs are stable and unique throughout. Priority is not listed per row because the same remark applies to all (PR-05), and the status-field remark applies to all (PR-04).

| ID | Title | Fields to change | Assessment |
| --- | --- | --- | --- |
| AAOS-GOV-01 | General accounting product scope | — | Sound as written. |
| AAOS-GOV-02 | Permanent traceable requirements | Acceptance criteria | Add a repeatable register check (PR-17). |
| AAOS-GOV-03 | Evidence-based release and preserved review gates | Status | Update after this review: RA not accepted (PR-01). |
| AAOS-ARC-01 | Shared execution and modular capabilities | — | Sound as written. |
| AAOS-ARC-02 | Isolated client workspaces | — | Sound as written. Status agrees with my run (M1 isolation). |
| AAOS-ARC-03 | Central Supporting Strategies deployment | Acceptance criteria | Concurrent-client criterion has no test (PR-14). |
| AAOS-ARC-04 | Optional independent client deployment | Trace | Add AT-58 (PR-13). |
| AAOS-ARC-05 | Environment and release separation | — | Sound as written. |
| AAOS-EXE-01 | Durable progress and resumable work | — | Sound as written. |
| AAOS-EXE-02 | Recurring occurrences and event wake-up | Dependencies | Direction with EXE-03 is reversed against T-04/T-10 (PR-12). |
| AAOS-EXE-03 | Bounded standing authority | Dependencies | Add EXE-02 and BNK-03; mark CTL-03 as for real authority (PR-12). Status agrees with my RA-05 result. |
| AAOS-EXE-04 | Hosted unattended operation | — | Sound as written. |
| AAOS-EXE-05 | Production retries, leases and monitoring | Acceptance criteria | Stalled-work monitor has no time bound (PR-14). |
| AAOS-EXE-06 | Pause, cancellation and operational controls | — | Sound as written. |
| AAOS-EXE-07 | Deterministic execution and optional model proposals | Dependencies, Trace | CTL-12 dependency needs the conditional marker (PR-12); add AT-59 (PR-13). Status agrees with my run (make test no-egress). |
| AAOS-KNO-01 | Applicable framework and reusable accounting knowledge | Acceptance criteria | Names no artifact for the invariant/judgment distinction (PR-14). |
| AAOS-KNO-02 | Verified standards references | — | Sound as written. |
| AAOS-KNO-03 | Client facts, chart and operating profile | Description | Record the card_accounts schema limit (PR-16). |
| AAOS-KNO-04 | Independently approved effective policies | Status, Acceptance criteria | Author retention holds for same key and scope only (PR-03). |
| AAOS-KNO-05 | Decisions and scoped correction history | — | Sound as written. |
| AAOS-KNO-06 | Portable operating knowledge and coverage | Description, Target stage | Add workflow inventory (PR-13); target stage names one client (PR-07). |
| AAOS-GL-01 | Shared proposed-entry contract | — | Sound as written. |
| AAOS-GL-02 | Journal mechanical validation | — | Sound as written. Status agrees with my run (RA-07). |
| AAOS-GL-03 | Classification, adjustments and account maintenance | Acceptance criteria | Materiality has no source (PR-14). |
| AAOS-GL-04 | Trial-balance intake and rollforwards | — | Sound as written. |
| AAOS-GL-05 | Exact money and currency contract | — | Sound as written. |
| AAOS-AP-01 | Vendor, bill and expense preparation | Acceptance criteria, Target stage | First-client condition in a shared record (PR-07). |
| AAOS-AP-02 | Payable scheduling and payment controls | — | Sound as written. |
| AAOS-AR-01 | Customer billing and invoice controls | Acceptance criteria, Target stage | Shared AR waits on one client (PR-07). |
| AAOS-AR-02 | Cash application, aging and collection work | — | Sound as written. |
| AAOS-BNK-01 | Card preparation demonstration | — | Sound as written. |
| AAOS-BNK-02 | Statement-based population completeness | Status, Acceptance criteria, Dependencies | Re-pointed statement and lookback restatement open (PR-02); add CTL-04 (PR-12). |
| AAOS-BNK-03 | Ordered source lifecycle and one economic item | Status, Acceptance criteria | Criterion fails: RB-01 (PR-01). |
| AAOS-BNK-04 | Reconciliation workpapers | Trace | Add AT-24, AT-25 (PR-13). |
| AAOS-BNK-05 | Matching, transfers and settlements | Description | Decide whether deposit and merchant-settlement matching belongs here (PR-09). |
| AAOS-BNK-06 | Statement cycles and receipt aggregation | — | Sound as written. |
| AAOS-CLS-01 | Typed close-readiness outcomes | — | Sound as written. |
| AAOS-CLS-02 | Immutable preparation-package finalization | Acceptance criteria | Add minimum package contents where they apply (PR-13). Status agrees with my run (M1/M2). |
| AAOS-CLS-03 | Full month-end close execution | Acceptance criteria | Add package contents and the five separate states (PR-13). |
| AAOS-RPT-01 | Financial statements and management reports | Status | Holds a Proposed consolidation requirement inside a Deferred record (PR-09). |
| AAOS-RPT-02 | Variance analysis and accounting insights | — | Sound as written. |
| AAOS-INT-01 | QuickBooks Online integration | Status | Cites the first client's Desktop conversion (PR-07); connector contract (PR-08). |
| AAOS-INT-02 | Bill.com integration | Status | Approved while INT-01 is Deferred for the same state (PR-04); PR-08. |
| AAOS-INT-03 | Google Workspace and Gmail | Status | As INT-02 (PR-04, PR-08). |
| AAOS-INT-04 | Google Drive and document repository | Status | As INT-02 (PR-04, PR-08). |
| AAOS-INT-05 | Bank activity, statements and authorized portals | Status, Acceptance criteria | Names Expensify (PR-07); status as INT-02 (PR-04). |
| AAOS-INT-06 | Safe external execution and unknown outcomes | Trace | Add AT-29, AT-40 (PR-13). |
| AAOS-CTL-01 | Genuine independent review and segregation of duties | Acceptance criteria, Dependencies | Author-retention clause too broad (PR-03); CTL-03 marker (PR-12). |
| AAOS-CTL-02 | Authenticated identity and bounded access | — | Sound as written. |
| AAOS-CTL-03 | Authority-grant lifecycle | — | Sound as written. |
| AAOS-CTL-04 | Durable periods, cutoff and locks | Status, Acceptance criteria, Dependencies | Criterion fails: RB-01 (PR-01); CTL-03 marker (PR-12). |
| AAOS-CTL-05 | Vendor identity and duplicate prevention | — | Sound as written. Status agrees with my run (RA-08). |
| AAOS-CTL-06 | Governing artifacts and decision integrity | — | Sound as written. |
| AAOS-CTL-07 | Relevant dependency invalidation | — | Sound as written. |
| AAOS-CTL-08 | Source traceability and document completeness | — | Sound as written. Status agrees with my run (RA-06/RA-07). |
| AAOS-CTL-09 | Revised or replacement evidence acceptance | Status, Acceptance criteria | Re-pointed documents avoid the hold: RB-02 (PR-02). |
| AAOS-CTL-10 | Persistent audit and inspectable evidence | — | Sound as written. |
| AAOS-CTL-11 | Consistent exports and external audit anchoring | — | Sound as written. |
| AAOS-CTL-12 | Credentials, privacy and untrusted content | Status | "Comprehensive threat validation" has no list (PR-14). |
| AAOS-CTL-13 | Backup, restore, retention and supported infrastructure | Acceptance criteria | No recovery-point or recovery-time parameter (PR-14). |
| AAOS-BB-01 | November knowledge capture | Target stage | November capture cannot start under G1 as written (PR-11); instance of shared onboarding (PR-06). |
| AAOS-BB-02 | Independent December validation and gaps | Target stage | Follows PR-11. |
| AAOS-BB-03 | Theresa's ordinary workflow and escalation | — | Sound. Instance of shared onboarding (PR-06). |
| AAOS-BB-04 | Sales and deposit process capture | Target stage | No shared record for the execution it defers (PR-09). |
| AAOS-BB-05 | Payroll and tip process capture | Target stage | As BB-04 (PR-09). |
| AAOS-BB-06 | Actual close and unattended readiness | — | Sound as written. |
| AAOS-BB-07 | Hosting, support, ownership and engagement agreement | — | Sound as written. |
| AAOS-BRF-01 | Actionable Morning Briefing | Acceptance criteria | Delivery channel and its permission unstated (minor note). |
| AAOS-BRF-02 | Management-wide and individual-client views | — | Sound as written. |
| AAOS-BRF-03 | Review, exception and waiting inbox | Status, Acceptance criteria | Two statuses in one field (PR-04); "genuine urgency" has no rule source (PR-14). |
| AAOS-OBS-01 | Work, accuracy, exceptions and human effort | Acceptance criteria | Require that agreed thresholds are recorded (PR-14). |
| AAOS-OBS-02 | Estimated human review time | — | Sound as written. |
| AAOS-OBS-03 | Model, infrastructure and human cost controls | — | Sound as written. |
| AAOS-OBS-04 | Independent validation and realistic evaluation | — | Sound as written. Status agrees with my run (RT14b guards). |
| AAOS-COM-01 | Missing-document and collection drafts | — | Sound as written. |
| AAOS-COM-02 | Controlled drafting and sending permissions | — | Sound as written. |

40 of 76 records need at least one field changed; 36 are sound as written.

## Files returned

1. `FABLE_PRODUCT_REQUIREMENTS_REVIEW.md` (this file)
2. `FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json`: 17 findings (1 code defect, 10 documentation defects, 1 future enhancement, 5 decisions for product or client authority)
3. `evidence/`: the check script, its output, the parsed register and the table generator
