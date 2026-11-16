# Fable independent verification of RD-01, RD-02 and PRV-11 to PRV-13

16 November 2026. Reviewed: `FABLE_RD_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9` (matches the sidecar, the package check and the final-verification file). Baseline for the comparison: the RC/PRV bundle, SHA-256 `9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454`.

All data is fictional. Every database was temporary. I worked in disposable extracted copies; the submitted archive, its sidecars, the working project and every earlier review folder and archive were only read. Nothing was connected, posted, paid, sent or deployed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

Every conclusion below applies to that bundle hash and to synthetic local preparation controls only. None of it establishes client accounting policy, reconciliation completion, close or operating readiness.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RD-01** | **Accepted.** Every assertion in the ticket holds, for an eligible and for an already approved claimant, before and after the target arrives. |
| **RD-02** | **Accepted.** Every assertion holds: revision with and without the claim, retirement and re-send in both orders, restart, latest target, open target, cycle. |
| **PRV-11, PRV-12, PRV-13** | **Accepted.** One sentence added to the register promises more than the check does (PRV-15, P3). |
| **RB-01** as a whole | **Not accepted.** Two further kinds of delivery still leave one charge approved in locked November and in open December (RE-01 P1, RE-02 P2). Neither is a regression. |
| AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03 | **Remain Verification failed**, now for RE-01 and RE-02. The re-verification criteria the register names (X01, X01d, X02, all 120 orders) are met. |
| AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02, AAOS-CTL-09 | Remain Independently verified; their probes still pass at this checkpoint. |
| G0 technical criteria | **Not met.** Batch 3 stays closed. |

The correction pass did what it was asked to do. Both tickets are closed with a change the size of my worked reference (one helper, one added line, two short loops replaced) and without its SQLite JSON grouping; nothing regressed, all 192 earlier test methods are intact, and every archive and protected input is unchanged. What still fails is the requirement behind the tickets, which says "regardless of arrival order".

**This is the fourth review in a row with that shape, and I do not think a fifth correction pass on its own is the right next step.** The two remaining failures each need two unusual things at once. The requirement as written has no edge at which a reviewer can stop looking. The owner should decide whether to bound it by a stated feed contract; see "A choice for the owner" below.

## Reproduction of the original failures

On a clean extraction of the baseline, with the two scripts unmodified (`evidence/baseline/`):

- `fable_rc_acceptance_probes.py`: exit 1; 12 OK, X01, X01d and X02 WEAK, X08 NOTE.
- `fable_rc_order_search.py`: exit 1; 120 runs, 18 double, 18 finalized silently.

On a clean extraction of the new bundle: exit 0 with 15 OK and X08 NOTE; exit 0 with 120 runs and 0 double in all five families.

## What I verified for RD-01 and RD-02

Probes X01, X01d and X02 test the outcome after the target has arrived. The tickets and the review prompt assert more, so I wrote each assertion as its own check (probes Y01 to Y06 in `fable_rd_acceptance_probes.py`; output in `fable_rd_acceptance_output.txt`). All six fail on the RC source and pass on this one, so they do discriminate (`evidence/baseline-rc-source-rd-probes.txt`).

**RD-01, the first unchanged re-send with a claim on an unknown row (Y01, eligible and already approved).** The intake answers `changed: True` and adds exactly one source version, one binding and one SOURCE_SUPERSESSION_UNRESOLVED event; no link. Straight after the claim, before any new run, the earlier artifact is stale: an earlier approval no longer governs and December cannot be finalized on it. After re-preparing, the row carries both SOURCE_TRANSITION_REQUIRES_REVIEW and SOURCE_TRANSITION_UNRESOLVED and is not eligible; an approval attempt is refused; a `settlement_verified` disposition does not clear the unresolved blocker; December cannot be finalized without acknowledgement. When the target arrives, A1Y, A1X and both receipts are held under November, the links are A1→A1X and A1X→A1Y, and A1 still governs November. For the approved variant an approved-source event names the former December approval, ITEM_LEFT_POPULATION is recorded, and the approval decision is still in the history. No earlier snapshot, binding, move, link, decision, artifact, event or audit row changed at either step (each table compared as a byte-identical prefix), and the audit chain verifies.

**Repeating the claim (Y02).** Two further deliveries of the same claim in new batch envelopes answer `changed: False`, and add no source snapshot, binding, move, link, decision, artifact or accounting event and change no head. Each adds one batch-envelope snapshot and one intake audit row. An exact replay of the packet answers `replay: True` and adds no snapshot of any kind.

*The distinction I was asked to inspect.* My RD-01 assertion said "adds no snapshot". The developer reads that as "no source snapshot" and keeps the ordinary immutable record of each distinct batch. I agree with that reading and have no disagreement with the contract in D-023: a new envelope is evidence that the provider sent the message, and dropping it would make the delivery untraceable. My wording was imprecise; the behaviour is right, and it is the same convention probe Q02i verified for RC-02.

**Finalized packages (Y06).** With November finalized and locked and December finalized with A1Y approved, the late claim rewrites and adds no package row; a POST_FINALIZATION_CHANGE event is recorded for the December package before the target arrives, and none for November at that point; the December approval stops governing; after the target arrives A1Y is held.

**RD-02, the claim belongs to the identity (Y03, Y04, Y05).**
- *Revision* (Y03): after an amount revision that omits the claim, the new version still carries both transition blockers; accepting the revised evidence does not release the hold; a new service instance on the same file still shows it; after the target arrives the link is on the current head of A1Y and A1Y is held. Same with the claim repeated (two unresolved events, as expected for two versions).
- *Retirement and re-send* (Y04), orders Yc Z Yp X and Z Yc Yp X: the claimant is retired by its own replacement, re-sent without the claim, and is retired again at once by its live terminal. Before the target arrives no chain member is eligible without a transition blocker. When the target arrives the link A1X→A1Y is made onto the removed head, A1Z and its receipt are held, and no chain member can be approved in December.
- *Most recent target* (Y05a): a claim re-declared on a different unknown row replaces the earlier one; the earlier target arriving creates no link; the later target is linked and the row is held.
- *Open target* (Y05b): a target that is an ordinary December row resolves to an ordinary supersession: target retired, claimant in December with the review blocker, no unresolved blocker, nothing held.
- *Cycle* (Y05c): two rows that each claim the other produce one link; the closing claim is refused with "Supersession cycle is not permitted".
- *Already linked identity and unrelated intake* (Y05d, Y05e): after a chain is resolved, two unrelated intakes add no link, move, chain event or chain binding; the same after November is reopened and relocked.
- *Withdrawn claimant* (E04) and *target changed twice* (E05): held in every variant.
- *Claim on a row in a locked period* (E01): the locked period's governing approval is undisturbed; the new version is listed as late activity.

Claims omitted from later versions persist, as D-023 records, pending the owner's feed-policy decision. That is the stronger control and I verified it as such; I did not treat it as decided policy.

**Retained assertions.** Q01, Q02, Q02i, Q03, N01d, N01e, N01f, R01c and R01d all report OK in the unmodified scripts.

**Wider orders.** I deepened two gate families from four deliveries to five (`fable_rd_order_search.py`: X+Yp+Yc+Yr+Z and X+Yp+Yc+Z+V, 120 orders each) and added two families with a withdrawn claimant. All 288 runs: no double approval.

No schema change was made: `storage.py` and `tests/schema_v1.sql` are byte-identical to the baseline. No API or probe adaptation was needed or made.

## Confirmed blockers

Both were found by trying deliveries no ticket named. Both give the same result on the RC source (`evidence/baseline-rc-source-rd-probes.txt`), so this pass did not introduce them. Both end the same way: A1 approved in locked November, a replacement approved in open December, December finalized without acknowledgement.

### RE-01 (P1): the claim is on a message the provider ordered before the governing version, delivered late

1. A1Y (3 Dec, 40.00) arrives with provider sequence 5 and no claim. It is admitted to December.
2. The provider's sequence 4 for A1Y arrives late: the same bytes, saying it supersedes A1. The intake answers `changed: False`.
3. A reviewer approves A1Y; December finalizes without acknowledgement.

Cause: `source_revision` stores a version that is older in provider order and returns (lines 38–46) before the lines that link or record a claim (48–53). The only trace is the retained snapshot and its audit row. It makes no difference whether the claimed row exists (variant with A1X arriving afterwards: same result).

Control (E03c): the same two messages delivered in provider order are handled correctly; A1Y is held under November. In provider order this is "a later version omits the claim", which D-023 says does not withdraw it. So the outcome depends only on which message arrives first, which is the case provider ordering exists to make harmless. In the extended search every one of the 12 orders with the older message second is a double approval, and every one of the 12 with it first is held.

### RE-02 (P2): a later claim by a row that already has a link

1. A1Y arrives saying it supersedes B9, an ordinary December row. Linked at once.
2. A1Y is sent again saying it supersedes A1X, which has not arrived. A version and an unresolved event are recorded.
3. A1X arrives saying it supersedes A1, and is held under November.

A1Y shows only the review blocker for B9; after `settlement_verified` it is approved and December finalizes. With steps 2 and 3 swapped, A1Y is held under November.

Cause: `pending_claim` (line 116) returns nothing for an identity that has any link, so a claim declared after that link is recorded but never shown as a blocker and never resolved. When the target already exists, line 31 adds the link and the latest link governs. The same two messages therefore give different chains depending on which arrives first.

This follows my own RD-02 correction text ("for as long as the identity has no link"), and the sentence added to the AAOS-BNK-03 and AAOS-CTL-04 criteria in this pass describes it ("no … second pending-resolution link for an already linked identity is permitted"). The developer implemented what was specified; the gap is in the specification. I rate it P2 and not P1 because it needs one row to declare two different replacement targets, and what that means is itself undecided (UC-16).

One side effect is new in this pass. For such a row, repeating the claim is no longer a no-op: each repeat adds a source version, a binding, a blocked move row, an unresolved event and four audit rows (probe E02). On the RC source the same repeats added nothing. It fails in the safe direction, but it contradicts the RD-01 no-op assertion for this case.

### Tried in a temporary copy

I applied a correction for both to a temporary copy (`evidence/experimental-correction-re.patch`, `source_control.py` only: ten lines added, five replaced by seven). In that copy: my 13 probes all report OK; the RC probes still report 15 OK and X08 NOTE; the 120-order search has 0 double; the RB and RA scripts are unchanged at 16 OK / 2 NOTE and 14 OK; the extended search falls from 24 double to 10, all of them the UC-16 case below; `make test` and the gates I re-ran pass. Details and exit codes are in `evidence/experiment/` and under `experiment` in the results file. This is a worked reference, not a delivered fix, and no unit tests were written for it.

## A choice for the owner

RD-01 and RD-02 each needed one unusual delivery. RE-01 needs provider sequence numbers and out-of-order delivery and a claim present only on the older message. RE-02 needs one row with two targets. The failures are getting rarer, which is a good sign for the control, but each new dimension multiplies the space of deliveries and "regardless of arrival order" cannot be finished by listing orders.

- **Option A (recommended first).** Decide the feed contract for gate G2 now, at least: whether provider order metadata is used and whether delivery can be out of that order; whether one row can declare a replacement target more than once, and what the second claim means; whether a claim can arrive in a later message than its row. Then restate AAOS-BNK-03 and AAOS-CTL-04 as "regardless of arrival order within that contract", and have deliveries outside it refused at intake or held for a person. That is a small, testable control, and the requirement becomes verifiable.
- **Option B.** Keep the requirement open-ended and commission RE-01 and RE-02. That closes both orders, but I cannot promise a fifth review finds nothing.

The two can be combined. Neither is the developer's decision. If the provider contract guarantees that a claim always arrives with its row, in order, and once, then RC-03, RD-01, RD-02, RE-01 and RE-02 cannot occur at all.

## PRV-11 to PRV-13

**PRV-11, accepted.** By comparing every record field with the baseline (`evidence/register-diff.txt`, `evidence/inventory-and-states.txt`): exactly five of the 88 records changed. AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay Verification failed, state that RC-01 to RC-03 were accepted at 9a85c78a…2454, name RD-01 and RD-02 and give the exact re-verification criteria; both arrival-order criteria include the two RD deliveries. AAOS-CTL-09 cites the independent Q02 result. AAOS-GOV-02 describes the two new checks. No product decision and no implementation state changed. AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02 and every field of AAOS-BB-01 and AAOS-BB-02 are identical to the baseline. The six unratified records (ONB-01, ONB-02, INT-07, GL-06, BNK-07, RPT-03) are still Proposed and unchanged. The seven results keep their original order and match `register_verdicts`; T-12, RA-01, RB-01 and the Current evidence section agree with them.

**PRV-12, accepted.** The supplied fault script, unmodified, on a second disposable copy: 44 of 44 agree, G16, G17 and G18 rejected, no `make check` gap. My own 26 cases (`evidence/fable-rd-register-faults.txt`, H02 to H27): an edited scope, bundle hash or report reference; stale checkpoint metadata; an omitted failed row with and without promotion; a failed row rewritten as verified; an invented row; a duplicate; an extra key; a one-byte change to either reviewer file or either pinned report are all rejected. To test the derivation behind the pin I moved the pins in memory, never on disk: a later failed verdict governs even when the record still carries its earlier verified citation (H21, H23), and the register passes once it follows the later verdict (H22, H24). An earlier accepted citation is allowed only while the latest verdict verifies the record, and a hash from one checkpoint with the report of another is rejected (H25 to H27). Two of the 26 disagree, both the same point: see PRV-15.

**PRV-13, accepted.** G44 is rejected. My ten cases (H30 to H39) all agree: the display name removed from the list, the heading renamed without the list, a heading no name can be read from, and the name kept only inside a longer term are rejected; renaming the client consistently everywhere is accepted and the new name is then refused in a shared record, so the name is read from the client section and not hard-coded.

### New register and check items

- **PRV-14 (P2):** the register must record this review, and the check should read `register_verdicts` from `FABLE_RD_ACCEPTANCE_RESULTS.json` as a third pinned reviewer file.
- **PRV-15 (P3):** AAOS-GOV-02 now says the check will "preserve the current seven-row order". It does not look at the order: swapping two rows or reversing all seven is accepted (H13, H14). PRV-12 as I specified it did not ask for this, and the delivered file does keep the order. Enforce it or delete the clause.

## Gates, tests and preservation

Run unmodified on a clean extraction, in the order the prompt gives. Raw stdout, stderr and exit codes are in `evidence/commands/`.

| Command | Exit | Result |
| --- | --- | --- |
| `fable_rc_acceptance_probes.py .` | 0 | Exact 16 ids; 15 OK; X08 NOTE only |
| `fable_rc_order_search.py .` | 0 | 120 runs, 0 double, 0 finalized silently; 0 of 24 in each family |
| `fable_rb_acceptance_probes.py .` | 0 | Exact 18 ids; 16 OK; N02c and N04e NOTE only |
| `fable_ra_acceptance_probes.py .` | 0 | 14 OK |
| `make test` | 0 | 205 methods OK in 745 s, all eleven HTTP methods, no skip, no expected failure |
| `make check` | 0 | 88 records, 27 tickets; client boundaries pass |
| `make batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK |
| `make reverification-gate` | 0 | Pass; supplementary N08/N09 WEAK lines appear as disclosed and are not a gate verdict |
| `make acceptance-gate` | 0 | Pass; U4 is the only NOTE |
| `make rb-gate` | 0 | 14 unchanged probes OK; retained RA gate passes |
| `make rc-gate` | 0 | Exact 18-probe contract: 16 OK; N02c and N04e NOTE |
| `make rd-gate` | 0 | Exact 16 probes and exact 120 orders; 0 double |
| `check_product_requirements.py --json` | 0 | 77 Approved / 9 Proposed / 2 Rejected; 4 Independently verified / 3 Verification failed |
| `register_faults.py .` (earlier, unmodified) | 0 | 37 of 37 agree |
| `fable_rc_register_faults.py <second copy>` | 0 | 44 of 44 agree; G16, G17, G18, G44 rejected; `make check` gaps 0 |

**The gate is strict.** Both new scripts are reached by `make test` (through `tests/test_rd_review_gate.py`) and by `make rd-gate`. With the two application files reverted to the baseline, `make rd-gate` fails (`evidence/rd-gate-negative-control.txt`). I fed the gate's two validators the real outputs of my own run and then 21 altered copies (`evidence/fable-rd-gate-faults.txt`, 23 of 23 agree): a non-zero exit, a missing, duplicated, unknown or extra probe id, a WEAK or ERROR verdict, the X08 note altered, an OK altered to NOTE, a missing or duplicated order row, an order outside the five families, a double approval stated or hidden, and a false or missing summary are each rejected. The delivered fault tests cover the same ground and passed in my run.

**Tests.** 192 baseline methods, all present, every body byte-identical (compared by syntax tree, `evidence/test-inventory.txt`). 13 added: five in `test_review_corrections_rd.py`, four in `test_rd_review_gate.py`, four appended to `test_product_requirements.py`, whose earlier bytes are an exact prefix of the new file. No other earlier test file changed. No fault case I ran changed its meaning.

**Preservation** (`evidence/integrity.txt`, `evidence/preservation.txt`):
- All 936 manifest entries match; the manifest hash matches the package check; no entry is missing or unlisted; the archive has no unsafe path.
- The developer's inventory lists every one of the 207 payload differences from the baseline that are not its two declared self-artifacts or the manifest; every listed hash matches.
- The patch applies cleanly to the baseline and reproduces all 61 source, test, script and Makefile files byte for byte; exactly ten differ from the baseline.
- All 484 protected inputs match in the bundle and in the working project. The 415 that existed in the baseline are unchanged from it.
- All 14 earlier archives match their recorded hashes and, where one exists, their sidecar. V2 is `00a13d93…001d`.
- The RC review folder in the bundle and in the working project matches the returned response ZIP, 62 of 62 files.
- Working project, read-only: branch `review/fable-rc-acceptance`, HEAD `5a12ab0`, five commits, unchanged. Every bundle file is byte-identical to the working copy.
- My pristine extraction was re-hashed after all runs: unchanged, no extra file.

## What I did not run

- **UC-9, journals in replacement chains: reading only, NOT_RUN.** The new claim lookup is not limited to transactions, so a journal's claim is now recorded and linked by identity. The re-evaluation step still reads transaction heads only, and journal validation has no unresolved-transition blocker. I agree with the developer's note in `docs/corrections_rd/journal-scope-reading.txt` that a late middle link may leave a journal descendant unevaluated. Neither of us executed it. It is not part of RD.
- UC-6 and UC-8 bespoke probes; the full literal older RV and reverification scripts (their maintained subsets ran through the gates); deliveries beyond the 120 gate orders and my 336; browser rendering; an external linter, type checker or JavaScript compiler (none installed).
- I did not fix or re-open X08/UC-14, N02c/UC-10, N04e/UC-11 or U4. They report as before.

One new observation needs a decision and is not a defect finding: **UC-16.** A row held under locked November as part of A1's chain is released into December, with no reopen and no disposition, when the provider later says the same row replaces a different open row. The system applies "the latest claim replaces the earlier one" and keeps the earlier target held as the trace. If a second claim instead adds to the first, that is a double approval. It is the same on the RC source.

## Files

- `FABLE_RD_ACCEPTANCE_RESULTS.json`: machine-readable verdicts per ticket and per register record, every command and exit code, and what was run, read or not run.
- `FABLE_RD_CORRECTIONS.json`: tickets RE-01, RE-02, PRV-14, PRV-15, the owner's choice, and open concerns.
- `fable_rd_acceptance_probes.py`, `fable_rd_acceptance_output.txt`, `fable_rd_order_search.py`: the new probes, their output on this bundle, and the extended search.
- `evidence/`: raw logs, the baseline reproduction, fault outputs, the experimental patch and its logs, and the scripts that produced each file.

This folder, `exports/FABLE_RD_ACCEPTANCE/`, and the response ZIP with its checksum beside it are the only files I added to the project. No existing file was changed and nothing was committed.

I am returning these findings and waiting for the owner's next assignment. No developer pass and nothing in this report grants independent acceptance of RB-01, human G0, G1–G4, Batch 3 or live authority.
