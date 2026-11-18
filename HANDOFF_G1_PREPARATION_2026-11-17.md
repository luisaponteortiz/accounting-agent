# Accounting Agent OS handoff: G0 re-affirmed, and what opening G1 requires

Prepared 17 November 2026 at the owner's request, for continuation in the same project or a new chat. It follows `HANDOFF_RF_REGISTRATION_2026-11-17.md`, which stays as the record of the registration and the steps after it.

**Human G0 is accepted and was re-affirmed for the current source (D-036, D-039). G1 is the next gate and is not open.** None of the six things G1 needs beyond G0 is on record yet, and none of them is software work: they are written client facts, client approval, a held-out month, a named reviewer and the owner's authorization. No further implementation is authorized.

## Project and checkpoint

- Workspace: `/Users/luis/Documents/ChatGPT/Accounting Agent OS`.
- Branch `review/fable-rc-acceptance`, HEAD `5af9a6194bc39e2f303cc6b43b0b59094118b8e4`, ten commits, unchanged. Nothing is staged and no commit was added. Do not commit, reset, clean or rewrite history unless the owner asks.
- Everything done since the RF bundle lives in working files only. It is not a new delivered bundle.
- Reviewed RF bundle: `exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd`. It, the returned response and every earlier archive, sidecar, manifest, reviewer input and handoff are unchanged and immutable. The protected inventory is `docs/registration_rf/input-checksums.json` (1,506 entries).

## Read these first

1. Current [AGENTS.md](AGENTS.md).
2. D-033 to D-039 at the end of [DECISIONS.md](DECISIONS.md).
3. [Connection readiness](docs/CONNECTION_READINESS.md) and sections 8 and 9 of the [architecture review](review/FABLE_ARCHITECTURE_REVIEW.md), which hold the client questions and the gate table.
4. [Evidence for the feed-contract changes](docs/feed_decisions_uc21_uc23/README.md) and the [G0 re-affirmation record](docs/g0_reaffirmation/README.md).
5. [Earlier handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md), [product register](docs/PRODUCT_REQUIREMENTS.md) and [progress](PROGRESS.md).

## What was decided on 17 November 2026

| Decision | What it did |
| --- | --- |
| D-033, D-034 | Registered the independent RF review as the fifth pinned authority. AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 became Independently verified for the RF checkpoint. Six named retained test methods were adapted. |
| D-035 | Documentation-only pass that brought the entry, architecture and capability documents to the registered state. |
| D-036 | The owner accepted human G0 and designated Fable (Claude) as architect and reviewer: Fable creates the work and builds the review tests that check it. |
| D-037 | Documentation review checks added. The standing rule changed: a recorded review with review tests may establish Independently verified, and the reviewer may be Fable if the record says so. No record has been raised on that basis. |
| D-038 | Owner decisions on UC-21, UC-22 and UC-23. The feed code changed for UC-21 and UC-22, with twelve review tests. UC-23 was accepted as built. |
| D-039 | The owner re-affirmed G0 for the source as changed under D-038. |

## Where the software stands

| Item | State |
| --- | --- |
| Test suite | 274 methods, all passing in the one full validation run of the D-038 state |
| `make check` and the eight gate targets | all pass |
| Earlier reviewers' unmodified probe scripts | RE: 19 OK, 2 NOTE (C9c, C9g). RF: 14 OK, 1 NOTE (G1c) |
| Product register | 88 records; seven Independently verified, none Verification failed |
| Protected inputs and archives | all unchanged |
| Readiness gates | G0 accepted and re-affirmed; G1 to G4 closed |

Limits to carry forward:

- No separate review examined the D-038 source changes. They rest on Fable's review tests, the re-run suite and gates, and the earlier reviewers' unmodified probes. The seven verified records still cite the RF checkpoint, which precedes those changes.
- All evidence is on fictional data: principally two periods and one card account. Journals are outside the feed contract (D-026). No real provider behaviour is confirmed.
- UC-22 does not flag a message that mixes ordering without changing data, and the anomaly has no acknowledgement step. Two UC-21 cases were deliberately left as before. The local page line was checked in a JavaScript engine, not in a browser.
- The documentation checker covers the ten current-state documents it names. It does not cover this handoff.
- Each validation command ran once.

## What G1 is

G1 is "Approved client samples" in the gate table (section 9 of the architecture review).

| | |
| --- | --- |
| It permits | Local preparation on approved client samples, comparison with the client's own reviewed results, and recording the disagreements. |
| It does not permit | Connection to any system, or use of the sample output in the client's books. |
| What follows it | G2 (read-only integration) needs the accounting lead's acceptance of the G1 results on the held-out month, among other things. G1 does not open G2. |

## What is required to open G1

Seven conditions. The first is met; the other six are not on record anywhere in the project.

| # | Requirement | Who provides it | Status |
| --- | --- | --- | --- |
| 1 | Human G0 accepted | Accounting owner | **Met.** D-036, re-affirmed in D-039. |
| 2 | Client questions 1 to 7 answered in writing by the people with authority | The client's people with authority, and the accounting lead where the answer is the firm's | **Not on record.** |
| 3 | Client approval to use named sample records in a local, unconnected environment | The client | **Not on record.** |
| 4 | Real identity, chart and rules entered as proposed, then approved by a named human through the rule lifecycle | Preparer enters; a named human approves | **Not done.** No real client fact may be entered before requirements 2 and 3 and the owner's authorization. |
| 5 | A held-out month that was not used to build the rules | Accounting lead and client | **Designated, not yet available.** December 2026 (D-016). |
| 6 | A named human reviewer who is not the preparer | Accounting owner | **Not named.** |
| 7 | The owner's explicit G1 authorization, recorded as a decision | Accounting owner | **Not given.** |

### Requirement 2: the seven questions

They are in section 8 of the architecture review. Each blocks a specific part of the work.

| # | Question | What a complete written answer covers |
| --- | --- | --- |
| 1 | Entity and books | Which legal entity and set of books are in scope; the accounting framework and basis; whether the Desktop-to-QBO conversion is complete; which system is the book of record for November and December 2026. |
| 2 | Authoritative sources | For each card account: the authoritative record of posted activity (statement, issuer export or feed), who extracts it, and whether it gives opening balance, closing balance and totals by activity type. |
| 3 | Chart and card mapping | The approved chart of accounts with types and active status; the liability account each card settles to; whether card spend goes straight to expense or through payables or a clearing account. |
| 4 | Cutoff date | Whether an item belongs to a period by transaction date, posting date or statement date, and how items are handled when a statement cycle crosses month end. |
| 5 | Document policy | Which purchases need a receipt; what counts as acceptable support; tolerated date and amount differences; whether a statement line may substitute; how missing documents are resolved. |
| 6 | Authority | Who may prepare, review, resolve each exception type, approve reusable rules, and lock or reopen a period. Theresa's and Luis's assigned limits, and whether anyone else is involved. |
| 7 | Minimum sample packet | One closed month for one card account: the statement, the full posted population, receipts as actually kept, the entries as actually booked, and the reviewer's corrections. Plus a second month held back for validation. |

"In writing" and "by the people with authority" both matter. An answer inferred from records, from memory or from a chat does not meet the requirement. Each answer should name who gave it and on what date.

### Requirement 3: client approval of samples

The approval should name the records (which card account, which months, which documents), state that they will be used only in a local environment that is not connected to any system, and come from someone at the client entitled to give it. It should be kept with the answers to the seven questions.

### Requirement 4: configuration as proposed, then approved

Nothing from the fictional demonstration carries over. The readiness document records that the client's legal entity, chart, accounting basis, systems, recognition and receipt policies, reviewer authority and source completeness are all unconfigured, and that demo waivers and grants never become client policy. At G1 the real identity, chart and rules go in as proposed items and take effect only when a named human approves them through the rule lifecycle. This step comes after the authorization, not before it.

### Requirement 5: the held-out month

- December 2026 is the held-out month and November 2026 is the teaching month (D-016). A different month needs a new recorded decision.
- December cases and their expected results must be kept apart from the teaching examples, so that the procedures can be tested against cases they were not built from.
- Question 7 asks for closed months. November 2026 has not ended, and December 2026 will not be closed and reviewed until January 2027 at the earliest. This is the preparer's observation, not an owner decision: on the designated months, G1 can be authorized and November work can begin before the held-out validation can.

### Requirement 6: the named reviewer

The gate table asks for a named human reviewer who is not the preparer. D-036 designates Fable as reviewer of Fable's own software work; that is a different role and does not fill this one. The owner is recorded as both product owner and accounting lead (D-016), so who prepares and who reviews the client samples needs to be decided and named. Question 6 asks for the same information from the client's side.

### Requirement 7: the authorization

A recorded owner decision, in the owner's words, that names at least: the client entity and books, the card account, the sample months, the records approved for use, the local unconnected environment, the preparer and the reviewer. No earlier gate, acceptance or decision implies it.

## What can proceed before G1

Under D-016, and with only the client access the team already has, the November 2026 accounting procedures may be documented outside the application. No client record may be loaded into or processed by the application until G1 is authorized. D-016 grants no new source access, upload, policy approval or authorization.

Collecting the written answers to questions 1 to 7, the client's sample approval and the reviewer's name are the owner's and the client's steps and need no software change.

## What may turn out to need an assignment

These are possibilities to check when the client's answers arrive, not findings and not authorized work.

- Whether the answers fit what the software already does. The verified scope is principally two periods and one card account, and journals are outside the feed contract. A cutoff rule, a clearing-account treatment or a document policy that the current controls do not express would need a specific assignment.
- UC-24: a database prepared at an earlier checkpoint shows open-period approvals as stale until re-prepared. It should be written into upgrade notes before any database holding client samples is kept across versions.
- U4, UC-14, UC-17, UC-18 and UC-20 remain open observations. C9c, C9g, X08, N02c and N04e stay NOTE. UC-9 remains reading only.

## What does not follow automatically

No G1 sample processing, Batch 3, Proposed or deferred capability, real integration, paid or model service, sending, posting, payment, hosting or deployment follows from G0, from its re-affirmation or from this handoff. A later change to application source falls outside the D-039 re-affirmation.

## Standing rules for whoever continues

- Stay on `review/fable-rc-acceptance`; preserve all ten commits; add no commit unless the owner asks.
- Every delivered archive, sidecar, manifest, reviewer input and earlier handoff is immutable.
- Do not edit `tests/test_http.py` or its five-second deadline. No schema change without stopping to explain.
- Do not adapt retained test methods, reviewer probes or fault scripts. D-031 and D-033 are not general exceptions. Report a conflict before changing anything.
- D-026 and D-029 stay recorded as written; D-038 adds to them.
- Deliver work with review tests that can fail, their results and what they do not cover (D-036, D-037).
- After changing a current-state document, the README gate list, the suite, the capability registry, the readiness checklist or the decision log, run `python3 scripts/check_documentation.py`.
- All data in the project is fictional until G1 is authorized.

For a new chat: read this handoff and the sources listed above, preserve the checkpoint and all current files, and obtain the owner's specific next assignment before changing code, tests, authority pins, register states or readiness gates.
