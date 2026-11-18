# G0 criteria check against current evidence

17 November 2026. Prepared at the owner's request after the RF result registration (D-033/D-034).

**Result: five of the six G0 criteria are met on the evidence. The sixth, "Documentation matches code", is not met as the documents stand.** The gap is documentation only; no code defect was found. A documentation-only pass has since been done under owner assignment D-035; see the addendum at the end.

This is a check by the Claude (Fable) session that performed the registration. It is not an independent review verdict, it changes no register state or gate, and it does not accept G0. Human G0 remains the accounting owner's decision.

## The criteria

Gate G0, "Synthetic acceptance", is defined in section 9 of [the architecture review](../review/FABLE_ARCHITECTURE_REVIEW.md). Its entry criteria are six sentences, not five as I said earlier. It permits "a statement that the software controls behave as specified on fictional data" and does not permit "any claim about accounting correctness, Bird Bowl, or readiness".

| # | Criterion | Result | Last explicit independent verdict |
| --- | --- | --- | --- |
| 1 | Batch 1 and Batch 2 complete | Met | FAIL at the RV acceptance review (one P1 under T-12); that P1 chain closed at the RF review |
| 2 | All P0 and P1 current defects fixed with tests | Met | "Not met" at RB, RD and RE; the RF review raised no ticket and gave no G0 line |
| 3 | Reviewer cases: zero unexpected, all fail-until-fix cases fixed | Met | PASS at the RV acceptance review; same counts reproduced at RB and RF |
| 4 | Full synthetic month approved or dispositioned, finalized and locked, with no database edits and no weakened blocker | Met | PASS at the RV acceptance review; gate reproduced at RB and RF |
| 5 | Two synthetic clients in different periods on one engine with no cross-effects | Met | PASS at the RV acceptance review; isolation reproduced at RB |
| 6 | Documentation matches code | **Not met** | PASS at the RV acceptance review; not assessed in the five reviews since |

"RV acceptance review" here means the review of the RV corrections in `exports/FABLE_RV_ACCEPTANCE/`, which raised RA-01 to RA-08 and was the last to give a six-row G0 table.

No review states that the G0 technical criteria are met. The last three that gave a G0 line said "Not met" because P1 defects were open. Criteria 1 and 2 are therefore met by inference from the ticket chain below, not by a stated verdict.

## 1. Batch 1 and Batch 2 complete

Met.

- **Batch 1 gate** (T-01 to T-08): FV-C15, FV-R01, FV-R03, FV-R04, FV-RC01 and FV-RC02 report FIXED with zero unexpected; the reviewer probes run as unit tests in `tests/test_reviewer_probes.py`, which passed in today's `make test`.
- **Batch 2 gate** (T-09 to T-19): FV-J08, FV-J09, FV-J10 and FV-CL02 report FIXED; the synthetic month reaches finalized and locked without database edits.
- **Ticket status.** The RV acceptance review found ten of eleven Batch 2 tickets meeting every criterion, with one P1 under T-12. That defect ran RA-01, RB-01, RC-01 to RC-03, RD-01/RD-02, RE-01 and RF-01, and the RF review accepted "RE-01 / RB-01".

## 2. All P0 and P1 defects fixed with tests

Met. Every P0 and P1 raised in the nine reviews ends in an accepted verdict.

| Raised in | P0 / P1 tickets | Where accepted |
| --- | --- | --- |
| Original backlog | T-02, T-03, T-07 (P0); T-04 to T-06, T-09 to T-19 (P1) | Batch gates; residual defects carried in the rows below |
| Batch 1 verification | C-01, C-05 (P0); C-02, C-03, C-04, C-06 (P1) | C-02 to C-06 PASS at the RV acceptance review; C-01 through RA-01 below |
| Re-verification | RV-01 to RV-06 (P1) | RV-02 to RV-06 PASS at the RV acceptance review; RV-01 through RA-01 below |
| RV acceptance review | RA-01 (P1) | Carried as RB-01 |
| RA review | RB-01 (P1) | Carried as RC-01 to RC-03, then RD-01/RD-02, RE-01, RF-01 |
| RB review | RC-01, RC-02, RC-03 (P1) | Accepted at the RC review |
| RC review | RD-01, RD-02 (P1) | Accepted at the RD review |
| RD review | RE-01 (P1) | Carried as RF-01 |
| RE review | RF-01 (P1) | Accepted at the RF review, with RE-01 / RB-01 |
| RF review | none | No corrective ticket |

Each correction pass has its own regression file under `tests/` (corrections, reverification controls, acceptance corrections, RB, RC, RD, feed contract, RF), and all 250 methods passed today.

Not in this criterion: P2 and P3 tickets (those in the verdict tables I read are accepted, some with a recorded residual; I did not trace each one) and the open observations U4, UC-14, UC-17, UC-18, UC-20 and UC-21 to UC-25. I did not trace every earlier UC item to its closure; the RF review lists the ones above as open.

## 3. Reviewer cases

Met. Today's `make batch2-gate` on the registered project: 29 PASS, 10 FIXED, 21 DEFERRED-OK, no FAIL, UNEXPECTED, KNOWN-FAIL or DEFERRED-LEAK line. The ten FIXED cases are exactly the ten fail-until-fix cases named in the Batch 1 and Batch 2 gates. The independent reviews reproduced the same counts at RB and RF.

The 21 DEFERRED-OK cases are future-module specifications (AP, AR, reconciliation, reporting). They pass because the capability correctly refuses, not because it works.

## 4. Full synthetic month

Met. `scripts/synthetic_month.py`, run today inside the gate, reports:

- 10 items independently approved (eight card items and two journals);
- 3 items carried with a recorded disposition and their blocker left in place (TX-007 pending, TX-009 receipt policy unset, TX-011 currency mismatch);
- two packages finalized, period status locked, proposed-entry impact balances;
- records changed through service operations only; audit integrity passes.

The script opens no database connection of its own. The RV acceptance review withdrew the earlier TX-009 caveat, so no blocker is weakened and no evidence is changed to fit.

## 5. Two clients, different periods

Met. The same script runs a second client in December on the same engine and asserts that the first client's state and package bytes are unchanged, that no first-client artifact is visible to the second, and that both audit chains verify. The RV acceptance review also recorded four refused cross-client attempts, and the RF review's probes G2d and G2e found no cross-scope contributor effect.

## 6. Documentation matches code

Not met as the documents stand. The automated checks pass (`make check` confirms every capability ID named in the documents exists, and the register's links and evidence references resolve). The entry and architecture documents, however, describe checkpoints several passes old.

| Document | What it says now | What is true |
| --- | --- | --- |
| `README.md` | The RB correction handoff is current; independent re-verification is pending; "this pass" addresses RA-01 to RA-08; lists gates up to `acceptance-gate` | Five later passes are complete; the RF review is accepted and registered; `rb-gate` to `rf-gate` exist |
| `START_HERE.md` | Headed "RE/PRV correction checkpoint — independent verification pending", 227 tests | RE and RF are verified; 250 tests |
| `docs/ARCHITECTURE.md` | "Current corrective checkpoint" is the RB response | As above |
| `docs/CAPABILITY_CONTRACTS.md` | Opens with the RB correction response | As above |
| `FABLE_ACCOUNTING_HANDOFF.md`, `REVIEW_FREEZE.md` | Head sections describe the RF developer checkpoint and RF correction authority as current | The RF review has returned and is registered. I did not update these two in the registration; AGENTS.md asks that the Fable handoff be maintained, so this omission is mine. |
| `docs/PRODUCT_REQUIREMENTS.md` | EVIDENCE source row: "developer evidence awaiting independent RA acceptance". Crosswalk row T-14: RB-02/RB-04 "await independent re-verification" | RA acceptance was decided long ago; RB-02 and RB-04 were accepted at the RB review |

One gap in substance, not only status:

- **The D-026 feed contract is not described in any architecture or user-facing document.** Replacement claims on older or conflicting messages, the contested-claim blocker, the `select_supersession_target` disposition and its lock-authority condition, and the selector-as-contributor rule exist in `accounting_agent/feed_contract.py`, `exceptions.py` and `modules.py`. They are described in `DECISIONS.md` (D-026, D-027, D-029, D-030), the register's acceptance criteria and the correction reports, and nowhere in `README.md`, `docs/ARCHITECTURE.md` or `docs/CAPABILITY_CONTRACTS.md`.

Two smaller points:

- The registered capability `evidence.inventory` is not named in `README.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITY_CONTRACTS.md` or any other top-level file under `docs/`. `package.manifest` is named in the contracts document and a Batch 1 report, and not in the architecture document.
- The header counts inside `review/FABLE_VALIDATION_CASES.json` say 28 / 10 / 22 while the cases themselves are 29 / 10 / 21. The independent reviews accepted the maintained file and its adaptations; the header was not updated.

What I did not find: a document that claims a control the code lacks. The stale documents under-describe the current system; they do not over-claim. That is the test the documentation ticket T-08 set ("no document claims a control that a reviewer probe can defeat"), so a stricter or looser reading of this criterion is possible. I read "matches" as including "current", and on that reading it is not met.

This was a bounded check: the automated checks, the head sections and status statements of the documents above, a search for the feed-contract terms, and the capability registry against the contracts document. It was not a line-by-line audit of every document against the code.

## What would close criterion 6

A documentation-only pass, with no source, test, schema or gate change:

1. Bring `README.md`, `START_HERE.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITY_CONTRACTS.md`, `FABLE_ACCOUNTING_HANDOFF.md` and `REVIEW_FREEZE.md` to the registered state.
2. Add a short description of the D-026 feed contract and the target-selection disposition to the architecture and capability documents.
3. Correct the two stale lines in the register (EVIDENCE row and T-14 row) and record the change in its change log.
4. Run `make check` and the register tests.

This needs the owner's assignment; no further work is authorized now. Earlier delivered handoffs, prompts, reports and archives stay as written.

## Limits of this check

- Criteria 3, 4 and 5 rest on gates rerun today on a clone of the registered project (`docs/registration_rf/commands/`) and on the independent reviews named above.
- Criteria 1 and 2 rest on reading each review's ticket verdicts; I did not re-run any probe beyond the gates.
- Everything concerns fictional data and local preparation. Journals under the feed contract, more than two periods or one card account, the target-selection HTTP route beyond developer tests, and any real provider remain unverified.
- The registration change itself has not been independently reviewed.

## Addendum: documentation pass completed (D-035)

Later on 17 November 2026 the owner assigned the documentation-only pass described above, and it is done.

- `README.md`, `START_HERE.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITY_CONTRACTS.md`, `FABLE_ACCOUNTING_HANDOFF.md` and `REVIEW_FREEZE.md` now state the registered RF state first and label older text as history.
- `docs/ARCHITECTURE.md` and `docs/CAPABILITY_CONTRACTS.md` describe the D-026 card-feed contract and the `select_supersession_target` disposition, written from `accounting_agent/feed_contract.py`, D-026, D-027, D-029 and D-030. `evidence.inventory` and `package.manifest` are now named in the architecture document.
- Seven stale status lines in the register outside the requirement records were corrected, with a change-log row. The two I listed in the table above were the EVIDENCE row and T-14; reading the whole crosswalk found five more of the same kind (the RETURNED REVIEW row, T-09, the correction-order sentence, and the C-01–C-06 and RA completion rows).
- Not changed: the header counts inside `review/FABLE_VALIDATION_CASES.json`, which is a protected reviewer input, and every dated report, prompt and handoff of earlier passes.

On my reading, every gap this check listed for criterion 6 is now closed except that header count. That is a developer-side statement by the session that wrote the documents. It is not an independent assessment of criterion 6, it was not a line-by-line audit of every document against the code, and it does not accept G0.

## Addendum: G0 accepted by the owner (D-036)

With this check, its limits and the first addendum in front of them, the accounting owner accepted human G0 on 17 November 2026. D-036 quotes the decision. The owner also designated Fable (Claude) as the project's architect and reviewer and accepted the registration and the documentation pass without a separate review. The acceptance is the statement G0 permits, that the software controls behave as specified on fictional data, and it opens no later gate. The limits listed in this document still describe what the evidence covers.

## Addendum: the sixth criterion now has executable checks (D-037)

The owner asked for review tests for the documentation pass. `scripts/check_documentation.py` and `tests/test_documentation_review.py` now check the kinds of statement this document found stale: the stated test count, the gate list, the names of codes, routes and identifiers, capability status, G0 status, the latest registered review, pending or failed wording, register figures, links and decision references. Each check is shown to refuse injected faults. They are fixed patterns over the current-state sections, not a reading of every sentence, so they narrow the gap this check described without closing it for every possible wording.
