# Accounting Agent OS handoff after the RF result registration

Prepared 17 November 2026 for continuation in the same project or a new chat. It follows `HANDOFF_RF_CHECKPOINT_2026-11-17.md`, which is left as written. A later handoff, `HANDOFF_G1_PREPARATION_2026-11-17.md`, lists what opening G1 requires.

The returned independent RF review is registered. **AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 are recorded Independently verified for the RF checkpoint and its synthetic scope. The register has seven Independently verified records and none Verification failed.** **The accounting owner accepted human G0 on 17 November 2026 (D-036) and re-affirmed it for the source as changed under D-038 (D-039).** G1 is the next gate and is not open. No further implementation is authorized.

## Project and checkpoint

- Workspace: `/Users/luis/Documents/ChatGPT/Accounting Agent OS`.
- Branch `review/fable-rc-acceptance`, HEAD `5af9a6194bc39e2f303cc6b43b0b59094118b8e4`, ten commits, unchanged. Nothing is staged and no commit was added. Do not commit, reset, clean or rewrite history unless the owner asks.
- The registration lives in working files only. It is not a new delivered bundle and no review archive was built for it.
- Reviewed RF bundle: `exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd`. Returned response: SHA-256 `343da96a13daecdbc5f8bd7c8d9c9ac265c7b1a9ebca97c478ac1be1a2583232`. Both, and every earlier archive, sidecar, manifest and reviewer input, are unchanged and immutable.

## Read these first

1. Current [AGENTS.md](AGENTS.md).
2. [Registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and the [owner's quoted authorization](docs/registration_rf/OWNER_CLARIFICATION.md).
3. D-033 and D-034 at the end of [DECISIONS.md](DECISIONS.md).
4. [Independent RF report](exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md) and its [observations](exports/FABLE_RF_ACCEPTANCE/FABLE_RF_CORRECTIONS.json).
5. [Product register](docs/PRODUCT_REQUIREMENTS.md), [progress](PROGRESS.md) and [connection readiness](docs/CONNECTION_READINESS.md).
6. [G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md), prepared afterwards at the owner's request: five of the six G0 criteria are met on the evidence; "Documentation matches code" was not, and a documentation-only pass under D-035 has since addressed it (see below). Neither is an independent verdict and neither changes a gate.

## What the registration did

| Item | Result |
| --- | --- |
| Checker | RF results and report pinned as the fifth authority. No logic changed. |
| Derived results | Seven rows, original order, each citing the RF report and bundle. |
| Register | Three records raised to Independently verified, with new Scope note and Evidence. AAOS-GOV-02 scope note says five authorities. Status text, three crosswalk rows and one change-log row updated. |
| Tests | Six retained methods adapted under D-033; 235 of 241 unchanged; nine methods added; 250 in total. |
| Documents | D-033 (owner, quoted) and D-034 (validation) appended; progress, readiness and AGENTS.md updated. |

Unchanged: every acceptance criterion and product decision, all 88 IDs, the four earlier verified records, D-016/D-017, every BB-01/BB-02 field, the six Proposed records, D-026, D-029 and D-031, application source, schema, probes, gate scripts and `tests/test_http.py`.

## Documentation pass after the registration (D-035)

The G0 criteria check found the entry, architecture and capability documents describing the RB or RE checkpoints, and the D-026 card-feed contract absent from them. The owner assigned a documentation-only pass, now complete:

| Document | Change |
| --- | --- |
| `README.md`, `START_HERE.md` | Current state stated first; gates `rb-gate` to `rf-gate` listed; older text labelled as history. |
| `docs/ARCHITECTURE.md` | Current checkpoint; shared `evidence.inventory` and `package.manifest` steps; new sections for the RB to RD corrections and for the card-feed contract and target selection. |
| `docs/CAPABILITY_CONTRACTS.md` | Current state; feed contract summarized under Banking & Reconciliation. |
| `FABLE_ACCOUNTING_HANDOFF.md`, `REVIEW_FREEZE.md` | New current section first; older "Current" headings relabelled "Earlier". |
| `docs/PRODUCT_REQUIREMENTS.md` | Seven stale status lines outside the requirement records, and one change-log row. No record, state, criterion or decision changed. |

No source, test, schema, probe or gate script changed. Left as they are: the header counts inside `review/FABLE_VALIDATION_CASES.json` (a protected reviewer input) and every dated report, prompt and handoff of earlier passes.

## Evidence and its limits

Validation ran once, unmodified, on disposable clones of the registered project:

- `make test`: exit 0, 250 of 250 methods, all eleven HTTP methods, no skips or expected failures.
- `make check` and the eight gate targets: all exit 0. RF gate: 19 OK with C9c/C9g NOTE; 480 orders with zero double approvals, releases or audit failures.
- Preservation: all 1,198 protected inputs, sixteen earlier archives and all 298 returned RF response files unchanged; exactly nine of the 1,790 delivered RF payload files differed in the working project at registration, and fifteen differ after the documentation pass (the six documents above are the additions).

Limits to carry forward:

- **The registration and the documentation pass were performed by a Claude (Fable) session, and Fable also performed the independent RF review.** The owner was told this before authorizing. On 17 November 2026 the owner designated Fable as the project's architect and reviewer and accepted both without a separate review (D-036).
- The verified scope is what the RF review exercised: fictional local preparation, principally two periods and one card account. Journals were excluded and the target-selection HTTP route was not independently probed beyond the developer tests. No real provider or human operating readiness is verified.
- The original fault scripts are unchanged and now report 36/37, 43/44, 35/37, 20/35 and 41/62. Each disagreeing case presumes the three records are failed or alters an authority the RF review overrides; the registration record lists every case. Do not edit them or weaken latest-wins.
- `scripts/verify_rf_preservation.py`, `verify_re_preservation.py` and the three `verify_*_bundle.py` tools belong to earlier checkpoints and now refuse. They are outside `make test` and every gate. Use `docs/registration_rf/verify_preservation.py` for this state.
- `make test` was run once, not five times. The five-run requirement belonged to RF-03.

## G0 accepted (D-036)

G0 is a statement that the software controls behave as specified on fictional data. It is not a claim about accounting correctness, any client or readiness, and it opens no later gate. G1 needs written answers to client questions 1 to 7 from the people with authority, client approval to use named sample records in a local unconnected environment, real identity, chart and rules entered as proposed and approved through the rule lifecycle, a held-out month, a named reviewer who is not the preparer, and the owner's explicit G1 authorization.

D-036 also records how the owner's words "Remove any limitations" were applied: to the open limitation that the registration and documentation pass had no separate review. They were not read as opening a gate or as deleting the recorded limits of what the evidence covers. The owner confirmed that reading, and explained the designation: "you create your work and you build the review tests to make sure it is correct". Fable therefore delivers its work with review tests.

## Documentation review tests and the verification rule (D-037)

`scripts/check_documentation.py` checks the current-state sections of ten documents against the code, the register, the readiness checklist and each other; `tests/test_documentation_review.py` has twelve methods that show each check refusing injected faults. The suite now has 262 test methods; the 250 quoted elsewhere in this handoff is the count at the registration. Run the checker after changing a current-state document, the README gate list, the suite, the capability registry, the readiness checklist or the decision log.

By the same decision the standing rule changed. A recorded review with review tests may establish Independently verified, and the reviewer may be Fable reviewing work Fable created, provided the record says so. Developer tests alone still cannot. No record has been raised on that basis, and the register checker does not yet enforce the required statement.

## Feed-contract decisions UC-21 to UC-23 (D-038)

The feed code changed after the G0 acceptance and after the RF checkpoint. `accounting_agent/feed_contract.py` and `source_control.py` implement UC-21 and UC-22; `service.py` and `web/app.js` expose the new anomaly list. Twelve review tests are in `tests/test_feed_repeat_decisions.py`, and the suite now has 274 methods. The record, results and limits are in `docs/feed_decisions_uc21_uc23/`. The three Independently verified records still cite the RF checkpoint; these two changes are covered by Fable's review tests and re-run gates, not by a pinned review.

## G0 re-affirmed for the changed source (D-039)

After the D-038 validation finished the owner re-affirmed G0 for the source as it now stands. It is the same statement as before: the software controls behave as specified on fictional data. No separate review examined the D-038 changes; the re-affirmation rests on Fable's review tests, the re-run suite and gates and the earlier reviewers' unmodified probes. No record was raised or re-based, no gate opened, and a later source change would fall outside it. The record is in `docs/g0_reaffirmation/`.

## Decisions waiting for the owner

| Item | What is needed |
| --- | --- |
| Human G0 | Accepted by the accounting owner on 17 November 2026 (D-036) and re-affirmed for the source as changed under D-038 (D-039). No action. |
| UC-21 | Decided in D-038 and implemented: the identical repeat changes nothing. |
| UC-22 | Decided in D-038 and implemented: not permitted; the message is kept once and flagged. |
| UC-23 | Decided in D-038: accepted as built. |
| UC-24 | No decision now. Carry into upgrade notes before any database is kept across versions. |
| UC-25 | No action required. |

U4, UC-14, UC-17, UC-18 and UC-20 remain open. C9c, C9g, X08, N02c and N04e stay NOTE. UC-9 remains reading only.

## What does not follow automatically

No G1 sample processing, Batch 3, Proposed or deferred capability, real integration, paid or model service, sending, posting, payment, hosting or deployment follows from this registration or from G0. Application processing of client records still requires human G0 and explicit G1 authorization with written client facts. December 2026 remains the held-out validation month, separate from November teaching cases.

D-033 is not a general test-edit exception, and D-031 remains limited to its one method. For a new chat: read this handoff and the registration record, preserve the checkpoint and all current files, and obtain the owner's specific next assignment before changing code, tests, authority pins, register states or readiness gates.
