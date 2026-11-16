# Implement the feed contract (RE-01 to RE-03) and PRV-14, PRV-15, and return a new review bundle

Fable's independent review of your RD/PRV correction bundle is back. RD-01, RD-02 and PRV-11 to PRV-13 were accepted: every assertion held in an independent run, the 120-order search and two deeper five-delivery families have no double approval, nothing regressed, and all earlier tests, archives and protected inputs are intact. RB-01 as a whole was still not accepted. Two further kinds of delivery leave one charge approved in locked November and again in open December (RE-01, RE-02). Neither is a regression.

This was the fourth review in which every ticket passed and a neighbouring delivery failed, so I have stopped treating "regardless of arrival order" as open-ended. I have approved a feed contract, below. This pass implements that contract and nothing else. Batch 3, every deferred capability and all live actions stay closed.

## Where the review is

Everything is in the working project under `exports/FABLE_RD_ACCEPTANCE/`, and also in `exports/FABLE_RD_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip` (SHA-256 `97f062e5a1a36ffb995f149bd33c1cfe035453e1d6e837bbc7a9f9f636128b27`). Verify that hash before you start. The reviewed bundle was `0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9`.

Read these first, in this order:

1. This prompt. **Where it differs from the review's ticket file, this prompt governs**, because the contract was decided after the review. The differences are listed under "What the contract changes in the tickets".
2. `exports/FABLE_RD_ACCEPTANCE/FABLE_RD_CORRECTIONS.json`: source lines, minimal reproductions, expected and actual behaviour for RE-01 and RE-02, and the two register items under `register_and_check_gaps`.
3. `exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md` for the reasoning.
4. `exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py` and `fable_rd_acceptance_output.txt`. Y01 to Y06 restate the RD assertions; E03 and E06 are the two failures; E02 is the repeat that is no longer a no-op.
5. `exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py` and `evidence/order-search-extended-rd-source.txt`: 336 delivery orders, 24 of which end in double approval on your bundle.
6. `exports/FABLE_RD_ACCEPTANCE/evidence/fable-rd-register-faults.txt` and its script under `evidence/scripts/`. The two cases marked GAP are PRV-15.

Treat the folder and the response ZIP as immutable inputs. Do not edit, rename or regenerate anything in them. Everything that was immutable in the last pass still is.

## The feed contract I have approved

Record this section word for word in DECISIONS.md as D-026, an owner decision dated 16 November 2026. It decides the questions D-023 left open. Append it; do not rewrite D-023 or any earlier entry.

**Scope.** Card transaction rows and their receipts in the fictional local feed. Journals are excluded. Whether a real provider behaves this way remains a gate G2 confirmation.

**What it promises.** For every delivery order the contract allows, one charge is never approved in a locked period and again in an open one, and nothing leaves a locked-period hold without a person's authority. It does not promise identical intermediate records in every order.

1. **Provider order.** Where messages carry a sequence number or timestamp, the highest one governs the row. An older or conflicting message is kept as evidence and never replaces the governing row.
2. **Claim on a late, older or conflicting message.** The replacement claim is still recorded for the row. If the row has no claim yet, the claim applies as if it had arrived in order. If the row already has the same claim, it is a repeat (clause 5). If the row has a different claim, it is a second claim (clause 7).
3. **Claim after its row.** A provider may declare "this replaces X" in a later message than the row. The claim is recorded once, the row is blocked at once, and any earlier approval stops governing.
4. **Claim before its target.** The row stays blocked as unresolved until X arrives, then links automatically. If the chain reaches a locked period, the row and its receipt are held under that period.
5. **Identical repeat.** Repeating a claim the row already has changes nothing about the row. A new batch keeps its own delivery record; an exact replay of a batch adds nothing.
6. **Later omission.** A later version that does not repeat a claim does not withdraw it.
7. **Second claim naming a different target.** This applies whether or not the first claim has linked yet. The second claim is recorded but not applied. The row gets a blocker that only a recorded, authorized disposition can clear, and any approval stops governing. The row stays where it is: not moved into a hold, not moved out of one. The second target is not retired. Further different claims join the same open question.
8. **Release from a locked-period hold.** A provider message alone never releases a charge held under a locked period. Release requires an authorized reopen of that period, or a recorded, authorized disposition.
9. **Who may disposition.** A disposition under clause 7 or 8 is recorded by someone with disposition authority who did not supply either message, states which target stands, and cites evidence. If it releases a charge from a locked period, that person must also hold the lock authority.

**Left open, outside this contract.** Whether a removed replacement restores the original (U4), and whether replacing an already withdrawn charge needs the closed period reopened (UC-14).

Clauses 1, 3, 4, 5 and 6 are what you have already built and Fable has verified. Do not change them. Clauses 2, 7, 8 and 9 are the work.

## The three tickets

Do them in this order. Each later one builds on the one before.

- **RE-01 (P1), clause 2.** As written in the ticket file. A claim on a message that is older in provider order, or conflicting, and is therefore retained without governing, is still a claim of the row. Probe E03, control E03c.
- **RE-02 (P2), clause 7.** The ticket file proposes "the latest claim governs". I decided otherwise: a second, different claim is recorded and held for a person. This must give the same protection whichever of the two messages, or the two targets, arrives first, and whether the first claim is already linked or still waiting for its target. A first claim that is still waiting keeps working as it does today and links when its target arrives. Probes E06 and E02.
- **RE-03 (new, P2), clauses 8 and 9.** No provider message releases a row held under a locked period; today a later claim on an open row that is already on file does exactly that (UC-16 in the ticket file: 10 of the 24 orders of family X+B+Yb+Yc). Then build the one route a person has: a recorded disposition that names which declared target stands.

For RE-03, the disposition must behave as follows.

- It is refused without the disposition grant, refused for anyone who supplied a version of the row that carried either claim, refused unless it names one of the declared targets, and refused without evidence under the existing evidence rules.
- If recording it would take the row out of a hold under a locked period, it is also refused unless the same person holds the lock grant.
- If the first target stands, the blocker clears and nothing moves.
- If the second target stands, that link governs from then on with the ordinary consequences: held if its chain reaches a locked period, unresolved until the target arrives, otherwise in its own period with the usual transition review. Nothing is ever approved by the disposition itself.
- An authorized reopen releases a hold exactly as it does today. It does not clear the clause 7 blocker.
- Everything is append-only and the audit chain still verifies.

You choose the names of the blocker, the event and the disposition choice. Record them in DECISIONS.md and in your report.

## What the contract changes in the tickets

- **RE-02's proposed correction and its first acceptance assertion are superseded.** Under clause 7 the row is blocked where it sits; it is not moved under November by the contested claim. Do not use the `pending_claim` half of Fable's experimental patch. The `source_revision` half, for RE-01, is still a valid worked reference.
- **"Most recent target wins" is withdrawn.** It was delivered in RD-02 and verified, and clause 7 replaces it. Two things depend on it and only these two may change:
  - `tests/test_review_corrections_rd.py`, method `test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced`. Rewrite it to the contract and keep its second half, that unrelated intake leaves a linked chain untouched. Show the before and after in your report.
  - Probe Y05, part (a) only. Do not edit Fable's script. Return an adapted copy of Y05 with a diff confined to part (a), for review. Parts (b) to (e) must pass unchanged.
- **UC-16 is decided** by clause 8 and is no longer an open observation.
- **The completion gate in the ticket file is replaced** by "What done looks like" below.

If any other retained test, probe or fault case turns out to rely on re-targeting, do not adapt it. Report which one and why.

## How to work

Reproduce before you change anything. On the unmodified source:

- `python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py .` should give 10 OK, 1 NOTE (E02), 2 WEAK (E03, E06) and exit 1.
- `python3 exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py .` should give 336 runs, 24 double (12 in X+B+Yb+Yc, 12 in X+Y5+Y4c+Z) and exit 1. It takes several minutes.

Keep the raw output of both. Then write your own failing unit tests per clause, and keep the before-and-after evidence.

Six things are easy to get wrong:

- **Order of checks.** Cycle and self-supersession refusals come first and stay atomic refusals (R01d, Q03). Clause 7 applies only to a claim that would otherwise be accepted.
- **"Different" means a different target identity**, not a different version of the same target.
- **Idempotence.** The first declaration of a different target answers `changed: True` and is recorded once. Repeating either claim afterwards adds no source snapshot, binding, move, link or accounting event, also for a row that already has a link. E02 checks the linked case.
- **Not applied means not applied.** No link to the second target, no retirement of it, no move row for the claimant, and no change to where the claimant is bound.
- **The blocker is not clearable by existing dispositions.** `settlement_verified` and `revised_evidence_accepted` must leave it in place, approval must be refused, and the period must not finalize without acknowledgement. An earlier approval of the row stops governing as soon as the second claim is recorded.
- **Clause 2 and clause 7 meet.** A late older message whose claim differs from the one the row already has is a second claim, not a replacement of the first.

X08, N02c, N04e and U4 are expected to stay NOTE. Do not fix them.

The contract covers card transactions only. Leave journals as they are and do not extend the re-evaluation step. UC-9 stays a reading-only concern.

No historical snapshot, decision, package or audit record may be rewritten. **If you believe clause 9 needs a schema change, stop and explain before making it.** In that case deliver RE-01, RE-02 and the no-release half of RE-03, say plainly that a contested row then has no clearing route, and leave the disposition for my decision. That fails in the safe direction.

## What done looks like

- `fable_rd_acceptance_probes.py . Y01 Y02 Y03 Y04 Y06 E01 E02 E03 E03c E04 E05 E06`, unmodified, exits 0 with 12 OK. Your adapted Y05 reports OK.
- `fable_rd_order_search.py`, unmodified, exits 0 with 336 runs and 0 double in all six families.
- `fable_rc_acceptance_probes.py` still exits 0 with the exact 16 ids, 15 OK and X08 NOTE. `fable_rc_order_search.py` still exits 0 with 120 runs and 0 double. The RB script still gives 16 OK with N02c and N04e NOTE; the RA script still gives 14 OK. All unmodified.
- `make test`, `make check`, `make batch2-gate`, `make reverification-gate`, `make acceptance-gate`, `make rb-gate`, `make rc-gate` and `make rd-gate` all pass. Reviewer cases stay at 29 PASS / 10 FIXED / 21 DEFERRED-OK, and U4 remains the only NOTE in the older acceptance gate.
- Both RD scripts are wired into `make test` and into a new gate target that enforces the exact contract above, with fault tests of the kind you wrote for `make rd-gate`.
- All 205 test methods of the reviewed checkpoint are still present, with the single rewritten method named above. No other earlier test file is modified except by adding methods. No skip or expected failure hides a corrected defect.
- Your own unit tests cover, at least:
  - clause 2 with a known and an unknown target, for an eligible and an already approved row, and with the older message repeated;
  - clause 7 in both arrival orders, with the first claim linked and with it still waiting, and with a third target;
  - clause 8 in the November/December example with the December target already on file and with it arriving last;
  - clause 9: each refusal, each of the two outcomes, and release from a locked period with and without the lock grant.

## Register and project documents

Apply PRV-14 in the same change, with these amendments to the ticket file's wording:

- AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay at Verification failed. Say that RD-01 and RD-02 were independently accepted at checkpoint `0d188fa6…7ea9` and cite RE-01 to RE-03. Your own passing tests do not raise these records; only the next independent review can.
- Restate the two arrival-order criteria as holding "for every delivery order within the feed contract of D-026", and replace the sentence about a second pending-resolution link for an already linked identity with the rule of clause 7. Add clause 8 to AAOS-CTL-04.
- Add `exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json` (key `register_verdicts`) and `FABLE_RD_ACCEPTANCE_REPORT.md` to the pinned reviewer inputs as the third authority, the latest verdict winning per record, and update `docs/INDEPENDENT_VERIFICATION_RESULTS.json` from the three files. Keep the seven entries in their current order.
- The working register's SHA-256 is `bcbfdedfe5675ed72dac5c77cfbdd71acc58ed3c32cd856a94fbdc243a6ac997`, the same file as in your bundle. Verify it and build on it.
- Update the Current evidence section and the T-12, RA-01 and RB-01 crosswalk rows, update PROGRESS.md, and replace the current-authorization paragraph in AGENTS.md with this pass.
- Keep the PR-11 confirmation as it stands. Do not reword AAOS-BB-01 or AAOS-BB-02. I have still not ratified AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 or RPT-03; leave all six Proposed.

**PRV-15 (P3).** AAOS-GOV-02 says the seven-row order is preserved, and the check does not look at it (cases H13, H14). Enforce the order. If that is not simple, delete the clause and tell me why. Add a fault test either way, and confirm that `register_faults.py` still reports 37 agree and `fable_rc_register_faults.py` on a disposable copy still reports 44 agree.

## What to return

Build a new bundle under a new label. Never overwrite an earlier archive, sidecar or manifest. Every archive listed in `docs/corrections_rd/archive-integrity.json` must keep its hash, and so must your RD/PRV bundle (`0d188fa6…7ea9`) and the new review response (`97f062e5…8b27`). No existing commit may be rewritten. The working project is on branch `review/fable-rc-acceptance`; its head is the commit that adds this prompt and the review, on top of the five earlier commits ending at `5a12ab0`. Stay on it, and add no commit unless I ask.

Include:

- a correction report with one row per ticket and one row per contract clause: what changed, where, and which tests, probes or fault cases cover it;
- the adapted Y05 with its diff, and the before and after of the one rewritten test method;
- raw logs and exit codes for every command above, with environment and versions, plus the pre-correction reproduction of both RD scripts;
- a complete change inventory against your RD/PRV bundle, and a source-and-tests patch against it;
- a manifest with SHA-256 for every file, and the bundle's own SHA-256 in a sidecar;
- a short handoff and an exact prompt for Fable's next independent verification, which should ask Fable to write its own probes for clauses 2, 7, 8 and 9.

Report plainly. Say which results you ran yourself, mark anything you could not run as NOT_RUN with the reason, and do not describe developer passes as independent acceptance. If a clause turns out to be wrong, unreachable or in conflict with a control that is already verified, say so and show the evidence instead of working around it.

## Limits

Local, fictional data and temporary databases only. No live connections, client records, paid services or model calls, sending, posting, payments, hosting or deployment. Do not begin Batch 3, implement any Proposed register record, redesign the product or change the stack. The contract is my decision for the fictional local feed; it does not confirm how any real provider behaves. Passing tests do not grant human G0, G1–G4, Batch 3 or operating authority.
