# Fable independent verification of RE-01 to RE-03 and PRV-14/PRV-15 under D-026 and D-029

16 November 2026. Reviewed: `FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae` (matches the sidecar, the package check and the final-verification file). Internal `REVIEW_MANIFEST.json` SHA-256 `2a0a2e958bcf33070108edb054301732066ddabec16c46ff68120584337413eb` (matches the external manifest and the package check); all 1,337 payload hashes verified, no unlisted file. Baseline for the comparison: the RD/PRV bundle, SHA-256 `0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9`. Authority: `CODEX_RE_CORRECTIONS_PROMPT.md`, SHA-256 `da481f96bb1772c07f3af9600c6ff5ff244560727a1f1fa510779ea3966d559a`.

All data is fictional. Every database was temporary. I worked in disposable extracted copies; the submitted archive, its sidecars, the working project's existing files and every earlier review folder and archive were only read. The only thing added to the working project is this review folder. Nothing was connected, posted, paid, sent or deployed, and nothing was committed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

Every conclusion below applies to that bundle hash and to synthetic local preparation controls only.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RE-01** (clause 2) | **Not accepted.** A claim on an older message is applied the first time that message is delivered. If the same older message was already on file without the claim, the claim is recorded and never applied (RF-01, P1). With one more ordinary delivery this ends in the same charge approved in locked November and approved and finalized in open December. |
| **RE-02** (clause 7, with D-029) | **Accepted.** Every assertion holds in both claim orders, every target arrival order, with the first claim linked or waiting, and for third and later targets. The frozen-period boundary behaves as the owner decided. |
| **RE-03** (clauses 8 and 9) | **Accepted.** No provider message released a held row in any delivery I tried. Every refusal, both outcomes and the lock-authority condition hold. One neighbouring gap in review independence (RF-02, P3) and three observations for the owner. |
| `make test` | **Passes, but not dependably** (RF-03, P3): one of my three unmodified runs passed all 227; two stopped at the unchanged five-second HTTP setup deadline before the 11 HTTP methods ran. |
| **PRV-14, PRV-15** | **Accepted.** |
| The contract's promise (D-026) | **Not met**, because of RF-01. |
| AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03 | **Remain Verification failed**, now for RF-01. |
| AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02, AAOS-CTL-09 | Remain Independently verified; their probes still pass at this checkpoint. |
| G0 technical criteria | **Not met.** Batch 3 and all live actions stay closed. |

The developer's reported results are accurate. I reproduced them: 12 supplied probes OK, adapted Y05 OK, 336 orders with no double approval, the retained RC, RB and RA scripts, the eight gate targets, 37/37 and 44/44 fault cases, and 227 tests in one of three runs (see RF-03). The pass also did the things that are easy to get wrong: only the one authorized test method and Y05 part (a) were changed, all 205 earlier test methods are present, the schema is untouched, the patch reproduces the delivered source exactly, and all 16 earlier archives and 719 protected inputs keep their hashes.

What fails is one branch that none of the supplied probes or the developer's tests reaches. It is small (one missing line), it is inside the contract, and it defeats the contract's promise, so RB-01 cannot be accepted at this checkpoint.

## The failure: RF-01 (P1)

**In plain terms.** The card provider sends an older version of a December charge after a newer one. The system keeps the older message as evidence, as it should. Later the provider sends that same older message again, this time saying "this charge replaces P" (P being the replacement of A1, which is approved in locked November). The system writes the claim down and does nothing else with it. The December charge is never tied to November. If that charge is then itself replaced by another December row, that row can be approved and December can be finalized, while the original charge remains approved in November.

**Where.** `accounting_agent/feed_contract.py`, `card_source_revision`, lines 81–85. For an older or conflicting message that matches a snapshot already retained, the code calls `record_card_claim` and returns. Nine lines further down, the branch for a *new* retained message also calls `apply_first_card_claim` when the row had no claim. The `supersedes` field sits outside the row data, so a message with and without the claim has the same data hash and takes the first branch. Nothing applies the claim later, because `resolve_pending_supersessions` only visits rows that have a `SOURCE_SUPERSESSION_UNRESOLVED` event, and this path writes none.

**Reproduction** (probe C2f; every step is a public service operation):

1. A1 approved in November; November locked; December open.
2. P replaces A1 (December date). P is held under November. Correct.
3. Q, December, sequence 7, with its receipt.
4. Q, sequence 6, same data, no claim. Retained; `changed: False`. Correct.
5. Q, sequence 6, same data, `supersedes: P`. `changed: True`; `SOURCE_CLAIM_DECLARED` recorded. **No link, no unresolved event.**
6. Z replaces Q, with a receipt and a tying statement. Prepare December.
7. `settlement_verified` on Z; an independent reviewer approves Z; December finalizes without acknowledgement.

Result: A1 approved in locked November, Z approved and finalized in open December. Links are A1→P and Q→Z only. The same end state results when Z was approved before step 5: its approval keeps governing.

Without step 6 the state is safe but stuck (probe C2d, four variants): Q stays in December blocked as unresolved although its target is on file, it never links, and a target selection is refused because there is only one declared target.

**Why the supplied checks did not see it.** Probe E03 and family X+Y5+Y4c+Z deliver the older claim message once. The developer's clause 2 test delivers it once and then repeats it. Neither delivers the older message without the claim first.

**How wide.** My own order search (below) puts numbers on it. The same claim carried inside the row data (`supersedes_source_id`) is a different message and is applied correctly (C2f control).

**Worked reference.** `evidence/experimental-correction-rf01.patch` adds one line to the `if retained:` branch. On a disposable copy with that line: C2d and C2f report OK; my other 19 probes are unchanged; the 12 supplied probes, the adapted Y05, the RC probes, the developer's 16 feed-contract tests and the supplied 336-order search all still pass; my search reports no double approval (`evidence/experiment/`). It is a reference for the developer, not a delivered correction.

## What I verified, clause by clause

My probes are in `fable_re_acceptance_probes.py` (21 probes, 510 assertions; output in `fable_re_acceptance_output.txt`). They use their own identities and scenarios and only the fixture helpers of the earlier scripts. Run against the RD checkpoint source, 20 of the 21 fail or cannot reach their state and only the in-order control passes, so they do discriminate (`evidence/baseline-rd-source-re-probes.txt`).

| Clause | Verdict | Evidence |
| --- | --- | --- |
| 1 Provider order | Holds | C2a: in all 16 variants the governing head is the same snapshot, amount and order value after the late message; the late message is kept as one new source version. Supplied Y01, Y02. |
| 2 Claim on a late, older or conflicting message | **Fails in one branch (RF-01)** | Holds for the first delivery: C2a (sequence and timestamp order × known and unknown target × eligible and approved row × older and same-order conflicting), C2b control, C2c (a different older claim is a second claim, not applied), C2e (same end state as the in-order claim for an open target). Fails when the older message was already retained without the claim: C2d, C2f. |
| 3 Claim after its row | Holds | C2a, C7c: straight after the claim, before any new run, no approval governs. D-029 case below. Supplied Y01–Y04, E01. |
| 4 Claim before its target | Holds, except as a consequence of RF-01 | C2a unknown-target variants: blocked as unresolved, approval refused, then linked and held with the receipt when the target arrives. C7a, C9c. See observation UC-20. |
| 5 Identical repeat | Holds | C2a, C2c, C7b, C9d: every repeat answers `changed: False` and adds no source snapshot, binding, move, link, event, decision or head change. A new envelope keeps its batch record; an exact replay adds nothing (supplied E02, E04, E05; C9g). |
| 6 Later omission | Holds | C8a: the held row re-sent with no claim, revised, withdrawn and re-sent stays held. Supplied Y04, Y06. |
| 7 Second claim naming a different target | Holds | C7a (8 combinations), C7b, C7c, C7d. Details below. |
| 8 Release from a locked-period hold | Holds | C8a (14 kinds of provider message × 2 arrival orders), C8b, C8c, C9d; my search: no release in any order. |
| 9 Who may disposition | Holds; RF-02 (P3) | C9a–C9h. Details below. |

### Clause 7

For both claim orders (open row first, locked chain first), with the first target on file or not, and the second target on file before or after its claim (C7a):

- the second declaration answers `changed: True` and is recorded once as `SOURCE_CLAIM_CONFLICT_RECORDED`;
- no link, no move row, and the claimant's effective binding (period, admitted, reason) is what it was;
- the second target is not retired, then or later, and never linked;
- the first claim keeps working: where it names the locked chain the row is held under November when that target arrives; where it names the open row the row stays in December and is not moved into a hold;
- the row carries `SOURCE_CLAIM_CONFLICT`, is not eligible, and approval is refused;
- `settlement_verified` and `revised_evidence_accepted`, on either blocker code, leave the conflict in place;
- December does not finalize without acknowledgement;
- earlier history is an unchanged prefix and the audit chain verifies.

Third and fourth targets join the same question in order, and each repeat of any of the four is a no-op (C7b). An approval already given in open December stops governing straight after the second claim, before any new run, and no approval decision is added. A live replacement of the contested row carries the blocker, and an approval of that replacement given earlier stops governing at once (C7c).

**D-029, the frozen home period (C7d, and the developer's reproduction, exit 0).** A1 is approved inside November and November is locked. Two incoming versions of A1 then claim two different unknown rows. The November approval is preserved: same artifact, still approved. The incoming version is held as late activity. One declaration and one conflict are recorded; no approval decision is added; the audit chain verifies. A target selection is refused with `PERIOD_LOCKED`, also for a person holding both the disposition and the lock grant. Straight after an authorized reopen the old approval no longer governs. After preparation A1 carries the contested blocker, is not eligible, approval is refused, and no approval was created. A selection is then accepted and clears only the conflict. This is the behaviour the owner chose.

### Clause 8

Q is a December charge that replaces P, which replaces A1; Q and its receipt are held under locked November. With the open row B on file first and with B arriving last, none of these releases Q or its receipt (C8a): a second claim naming B; repeats of either claim; the row re-sent with no claim; an amount revision; a date revision inside December; a date revision into November and back; a revised receipt; a second receipt under a new key (held too); a third claim; a new statement; withdrawal by the feed; re-send after the withdrawal. Half of these were sent with an explicit December period hint on the batch. B is never retired or linked.

Messages for other rows in the chain do not release it either (C8b): P re-claimed to an open row (P becomes contested and stays held), a new replacement of Q (held as well), P voided.

An authorized reopen releases the hold and leaves the contested blocker; approval is still refused.

### Clause 9

**Refusals (C9a).** Each of these is refused and leaves no disposition, event, link, binding or move row: a reviewer without the disposition grant; the lock grant alone; the supplier of the first claim message; the supplier of the second; a third person who re-sent the second claim in a new envelope; an undeclared target; an unknown target; no evidence; a superseded receipt version; a reference that does not exist; the current receipt with a wrong hash; only the receipt of another charge; the wrong period; a rule-scope disposition. An independent person with the disposition grant and the current receipt is then accepted.

**First target stands (C9b).** One disposition and one `SOURCE_CLAIM_TARGET_SELECTED` event; no link, binding, move, snapshot, head or decision changes; the blocker clears and the ordinary transition review remains; nothing is approved. The selector is refused as reviewer; an independent reviewer can then approve. The selection cannot be revoked through the ordinary route.

**Second target stands (C9c).** Known open row: its link governs, the row stays in December with the transition review, the old link is kept as evidence. Unknown row: unresolved until it arrives, then linked and held with the receipt. Row whose chain reaches locked November: accepted without the lock grant (it moves into a hold, not out of one), held with the receipt. Nothing approved in any of the three. Selecting a target that is itself late activity in the locked period quarantines the claimant and its receipt (C8c).

**Release from a hold (C9d).** With Q held under November and contested, selecting the open target is refused for the disposition grant alone, disposition plus review, the lock grant alone, and finalize plus lock; nothing is recorded. Confirming the standing locked target needs no lock grant and moves nothing. A person holding both grants is accepted: Q and its receipt go to December with the transition review, nothing is approved, the former link is kept as evidence, that person cannot approve Q, and P stays held. Repeating the de-selected claim afterwards changes nothing; a new distinct target reopens the question.

**Locked home, tested apart from the release case (C9f, C7d).** With the row's own period locked the selection is refused with `PERIOD_LOCKED` for both kinds of actor; after reopen the conflict is still open and the selection is accepted.

**Contributor (C9e).** After a revision of the row the selection stands, the selector is listed as a contributor and is refused as reviewer. The selector is also refused on the live replacement of the row; an independent reviewer is accepted.

**RF-02 (P3, C9h).** If a second person records a confirming selection of the same target, only that person remains a contributor. The first selector, whose decision created the governing link, can then approve the row. It needs two people with disposition authority, approves nothing twice and keeps both records, and it mirrors the existing rule for ordinary dispositions. I ticketed it because the prompt asks that the selector never approve a dependent artifact; the owner may equally record it as accepted policy.

## My own order search

`fable_re_step_search.py` delivers every permutation of four families of five deliveries that the supplied search does not contain. Unlike the supplied search it attempts an approval after *every* delivery, not only at the end: prepare, tie the statement, clear every blocker that has an ordinary disposition, ask an independent reviewer. No person records a selection and November stays locked.

| Family (five deliveries) | Orders | Double approval | Released without authority |
| --- | --- | --- | --- |
| P, B, Q seq 7, Q seq 6 claiming P, Q seq 8 claiming B | 120 | 0 | 0 |
| P, Q seq 7, Q seq 6, Q seq 6 claiming P, Z replacing Q | 120 | **40** | 0 |
| P, B, Q claiming B, Q claiming P, Q revised | 120 | 0 | 0 |
| L (late November row), B, Q claiming L, Q claiming B, Q revised | 120 | 0 | 0 |
| **Total, delivered source** | **480** | **40** | **0** |
| Total with the one-line reference for RF-01 | 480 | 0 | 0 |

The 40 are exactly the orders in which the claim-carrying older message arrives after both the newer version and its own claim-free copy. In all 40 the double approval is still there after the last delivery. In the other 80 orders of that family, and in all 360 orders of the other three, nothing is approved twice at any step, no held row or receipt leaves its hold, and the audit chain verifies.

"Double" here means: at some step A1 is approved in locked November while Q or its replacement is approved in December, Q has declared that it replaces P or L, and that target is on file. In 40 orders of the second family the replacement Z is approved at a step where the target has not arrived yet; that is counted apart and is observation UC-20, not a failure.

## PRV-14 and PRV-15

By comparing every record with the RD checkpoint (`evidence/register-diff.txt`): 88 records, none added or removed, exactly four changed (AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03, and the scope note of AAOS-GOV-02 for PRV-15).

- BNK-03, CTL-04 and GOV-03 stay Verification failed; they cite the RD review at `0d188fa6…7ea9`, state that RD-01 and RD-02 were accepted there, and name RE-01 to RE-03 as developer evidence only.
- Both arrival-order criteria now read "for every delivery order within the feed contract of D-026". The sentence about a second pending-resolution link is gone and the clause 7 rule stands in its place. CTL-04 carries clause 8. D-029 is reflected in both.
- Current evidence and the T-12, RA-01 and RB-01 rows are updated.
- AAOS-BB-01 and AAOS-BB-02 are byte-identical; the three PR-11 lines are identical; AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 and RPT-03 are byte-identical and Proposed.
- `docs/INDEPENDENT_VERIFICATION_RESULTS.json` has the seven rows in the original order, each taken from the RD review.
- D-026 appears word for word in `DECISIONS.md`, once; the RD-checkpoint text of that file is an unchanged prefix.

My fault injection (`fable_re_register_faults.py`, 35 cases, all agree): every reordering of the seven rows is rejected (two swaps, reversal, rotation, sorting, regrouping), as are a dropped and a duplicated row; the RD results file and RD report are pinned (verdict flip, one byte, removal); with the pin moved, the latest authority wins per record in both directions, an older file cannot override it, a stale citation is rejected, and none of the three failed records can be raised in the register.

The unchanged RD diagnostic reports 34 of 37, as the developer says. H13 and H14 now reject. H22 to H24 expect the RC review to be the newest authority; with the RD review pinned as the third they are obsolete, and cases J14 to J23 show the rule working correctly. I agree with the developer's reading and would not weaken latest-wins.

## Gate, tests and preservation

- **RE gate.** `scripts/verify_rd_feed_review.py` runs the 12 supplied probes, the adapted Y05 and the 336-order search, and is wired into `make re-gate` and into `make test`. My fault injection on its validators (`fable_re_gate_faults.py`, 33 cases, all agree) rejects a non-zero exit, a WEAK, NOTE or ERROR verdict, a missing, duplicated, unknown or extra probe, a missing or doubled summary, a missing, duplicated or extra order, a double row, a row approved in both periods without the flag, a renamed family and every altered summary line.
- **Y05.** The adapted copy differs from my script in four hunks, all inside part (a) (original lines 280–289 of Y05's 277–348). Parts (b) to (e) and the rest of the file are identical.
- **Tests.** 205 earlier methods, all present. One method body changed: `test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced`, with its unrelated-intake half retained. `test_product_requirements.py` is a pure append (two methods). 22 methods added: 16 feed contract, 4 RE gate, 2 register. No skip or expected failure anywhere.
- **Source.** Against the RD archive: no file removed; 17 changed, all expected; `accounting_agent/storage.py` and `tests/schema_v1.sql` unchanged; the non-card path of `source_revision` is unchanged, so journals are as they were. Applying `source-and-tests.patch` to the RD archive reproduces all 81 runtime, test, script and review files exactly. `changed-files.json` lists every difference I found.
- **Archives and inputs.** All 16 earlier archives keep their hashes in the bundle and in the working project; so do the RD bundle, the RD response and the prompt. All 719 protected inputs match in both places. My RD review folder in the bundle is identical to the one in the working project (95 files).
- **History.** Branch `review/fable-rc-acceptance`, head `542688b57ece08ea55082d68b713ccf6433fd8ce`, eight commits. The working project's source, tests, scripts and register equal the bundle.

## Commands I ran

All on clean disposable copies, unmodified, with complete stdout, stderr and exit codes under `evidence/commands/`. macOS 26.5.2 x86_64, Python 3.9.6, SQLite 3.51.0, GNU Make 3.81.

| Command | Exit | Result |
| --- | --- | --- |
| 12 supplied RD probes | 0 | 12 OK |
| Adapted Y05 | 0 | OK |
| Supplied 336-order search | 0 | 336 runs, 0 double, 0 finalized silently; six families |
| RC probes | 0 | 16 ids: 15 OK, X08 NOTE |
| RC order search | 0 | 120 runs, 0 double |
| RB probes | 0 | 18 ids: 16 OK, N02c and N04e NOTE |
| RA probes | 0 | 14 OK |
| Developer's D-029 reproduction | 0 | PASS |
| `make test`, three unmodified runs | 2, 2, 0 | Runs 1 and 2: 216 methods OK, then one class-setup error in the unchanged `tests/test_http.py`; its 11 methods did not run. Run 3: 227 OK. No method failed an assertion in any run. See below. |
| `make check` | 0 | 88 records, 27 tickets |
| `make batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK; synthetic month passes |
| `make reverification-gate` | 0 | passes |
| `make acceptance-gate` | 0 | U4 the only NOTE |
| `make rb-gate`, `rc-gate`, `rd-gate` | 0 | pass |
| `make re-gate` | 0 | 12 OK; adapted Y05 OK; 336 orders, 0 double |
| `register_faults.py` (F) | 0 | 37 of 37 agree |
| `fable_rc_register_faults.py` (G) on a copy | 0 | 44 of 44 agree; no `make check` gap |
| `fable_rd_register_faults.py` (H) on a copy | 1 | 34 of 37; H22–H24 obsolete as explained |

### `make test` is timing-marginal (RF-03, P3)

`tests/test_http.py` is unchanged from the RD checkpoint. Its class setup gives the background worker five seconds to prepare the demo data. In my first full run (made while other jobs were running) and in my second (made alone) that deadline expired, so the suite ended with 216 methods OK and one setup error, exit 2. My third run, also alone, passed all 227. The developer's report describes the same two failures before their passing run, on the same kind of machine.

It is a question of margin, not of a failing control:

- the 11 HTTP methods pass on their own (3 runs of 3) and together with the feed-contract tests (3 of 3);
- in a labelled diagnostic copy where only that deadline is widened, the full suite passes 227 and the setup needs 4.84 seconds;
- timed outside the suite, the same setup needs about 3.8 to 5.2 seconds on the RD source and about 4.5 to 6.5 on this one (`evidence/http-setup-timing.txt`). The new claim checks cost roughly one second there. In one of ten timings on this source, taken under load, the worker stopped and the setup never finished; I could not reproduce or attribute it, and `accounting_agent/http.py` is unchanged.

So "227 tests pass" is true of a run, and not dependable as a gate. I ticketed it at P3 because nothing accounting-related fails, but a gate that passes one run in three will hide a real failure sooner or later. The developer may not edit that test; either the setup cost comes down well below the deadline, or the owner allows the deadline to be widened.

## Observations for the owner (no ticket)

- **UC-17 (C9c).** When a person selects the second target, the first target that the automatic first claim had already retired stays retired. It has no December artifact and is listed under removed items. Whether it should come back is the same kind of question as U4.
- **UC-18 (C9g).** An exact replay of a claim batch by another person leaves no record of that person, by clause 5, so that person is not treated as a supplier and may record the selection. A re-send in a new envelope is recorded and refused.
- **UC-20.** While a claimant waits for its target, a live row that replaces the claimant carries only the ordinary transition blocker; after `settlement_verified` it can be approved and December finalized. When the target arrives the approval stops governing and the row is held. It is the same on the RD checkpoint, so it is not a regression, and it does not break the contract's promise. Clause 4 speaks of "the row"; the owner may want it to cover the replacement too.
- U4, UC-14, X08, N02c and N04e are unchanged and open. UC-9 remains reading only; journals were not exercised.

## What I did not do

I did not exercise the HTTP route for the new disposition beyond the developer's own tests; my probes call the service operations the route passes through. I did not test journals (excluded by D-026). I did not test more than two periods or more than one card account.

## Files in this folder

- `FABLE_RE_ACCEPTANCE_RESULTS.json`: per-ticket and per-clause verdicts, register verdicts, checkpoint hashes, command results.
- `FABLE_RE_CORRECTIONS.json`: RF-01 and RF-02 with source lines, reproductions, expected and actual behaviour, acceptance; the observations.
- `fable_re_acceptance_probes.py`, `fable_re_acceptance_output.txt`: my probes and their output on the delivered source.
- `fable_re_step_search.py`: my order search.
- `evidence/`: command outputs and exit codes, search results, fault-injection scripts and outputs, register and tree comparisons, the baseline comparison, the experimental patch and its results.

Developer passes are not independent acceptance, and this review does not promote any requirement or grant readiness. It authorizes no implementation and no live action.
