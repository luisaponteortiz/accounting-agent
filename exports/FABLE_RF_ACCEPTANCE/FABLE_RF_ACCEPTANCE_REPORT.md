# Fable independent verification of RF-01 to RF-03 and PRV-16 under unchanged D-026 and D-029

16–17 November 2026. Reviewed: `FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd` (matches the sidecar, the package check and the final-verification file). Internal `REVIEW_MANIFEST.json` SHA-256 `07bac9cac34acd069c5e509d8fe832a397f768e8e640a9324903f3fe3ee715f0` (matches the external manifest and the package check); all 1,790 payload hashes verified, CRC clean, no unlisted file. Baseline for the comparison: the RE/PRV bundle, SHA-256 `4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae`. Authority: `CODEX_RF_CORRECTIONS_PROMPT.md`, SHA-256 `a4b2e870551f93931b5247d215a576218424765a64f79461171921594c32cc1a`; D-026 and D-029 unchanged; D-031 for one test method.

All data is fictional. Every database was temporary. I worked in disposable extracted copies; the submitted archive, its sidecars, the working project's existing files and every earlier review folder and archive were only read. The only thing added to the working project is this review folder and its response archive. Nothing was connected, posted, paid, sent or deployed, and nothing was committed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

Every conclusion below applies to that bundle hash and to synthetic local preparation controls only.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RF-01** (P1, clause 2) | **Accepted.** A claim-free older or conflicting message that is later re-sent with the row's first claim now applies the claim. I found no other path on which a first claim is recorded without being applied. |
| **RF-02** (P3, clause 9) | **Accepted.** Every person who recorded a target selection stays a contributor; none can approve or finalize; ordinary dispositions are unchanged. |
| **RF-03** (P3) | **Accepted.** The shortcut equals the full computation at every call I compared. The HTTP test file and its five-second deadline are untouched. The delivered setup finishes sooner than RD's under the same load in every pairing I measured. Five consecutive complete `make test` runs passed all 241 methods, the 11 HTTP methods included. |
| **PRV-16** | **Accepted.** Fourth authority pinned, latest verdict wins, seven rows in their original order, nothing protected changed. |
| **RE-01 / RB-01** | **Accepted.** RF-01 was its last failure. |
| The contract's promise (D-026) | **Met in every order tried.** No charge approved in locked November and again in open December, and nothing released from a hold without authority, in 3,120 stepwise delivery orders and every probe. |
| AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03 | **May be recorded Independently verified at this checkpoint, for this scope.** |
| AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02, AAOS-CTL-09 | Remain Independently verified; their probes still pass at this checkpoint. |
| Corrective tickets | **None.** Five new observations for the owner (UC-21 to UC-25), none of which breaks the contract. |
| G0 | Not granted by this report. It is the accounting owner's decision. Batch 3 and all live actions stay closed. |

The developer's reported results are accurate. I reproduced every one of them: 19 OK with C9c and C9g NOTE on my 21 unmodified probes, 480 orders with no double approval, release or audit failure, the 12 supplied probes, the adapted Y05, 336 and 120 orders, the retained RC, RB and RA scripts, all nine gate targets, 37/37, 44/44, 34/37 and 29/35 on the four original fault scripts, and 241 test methods. The pass also did the things that are easy to get wrong: the HTTP test and its deadline are byte-identical, the schema is untouched, only the one method named in D-031 was rewritten, the patch reproduces the delivered code exactly, and all 1,198 protected inputs keep their hashes.

## RF-01: the claim that was recorded and not applied

**What changed.** One line in `accounting_agent/feed_contract.py`, `card_source_revision`, in the branch for an older or conflicting message that matches a snapshot already on file: when the claim is the row's first, it now goes through the same first-claim path as every other first claim. The intake then answers `changed: True`, which is what makes the existing end-of-intake steps link waiting claims, re-evaluate live replacements and hold receipts.

**What I verified** (my own probes, new at this checkpoint, in `fable_rf_acceptance_probes.py`; C2d and C2f from the last review now report OK):

| Asked | Result | Probe |
| --- | --- | --- |
| Known and unknown target; eligible and approved row | Linked and held with the receipt at once when the target is on file. For an unknown target: recorded as unresolved, blocked, approval refused, then linked and held when the target arrives, without a re-send. | G1a (20 variants: sequence and timestamp order, older and same-order conflicting, claim outside and inside the row data, the claim-free message delivered twice first) |
| Approval already given in the open period | Stops governing straight after the claim, before any new run. No decision is added. | G1a, G1h |
| Target is an open December row that is itself approved | Linked at once, the target retired, neither approval governs, the transition review is required before a new approval. | G1h |
| Live replacement approved before or after the claim | Target known: the replacement is held and its approval stops at once (C2f). Target unknown: the approval stops and the replacement is held with its receipt the moment the target arrives; December does not finalize. | C2f, G1c |
| Deferred automatic linking | Links when the target arrives, also after the claimant row and its receipt were revised without the claim. | G1a, G1e |
| Full locked-chain quarantine | Row, live replacements and their receipts are held; nothing has a December artifact. | G1a, G1c, G1d, G1e |
| Identical repeat | `changed: False`; no source version, binding, move, link, event, decision or head change, for the claim message and for the claim-free message. | G1a, G1b |
| Clause 7 still governs a second, different claim | A retained message re-sent with a different target is recorded as a conflict and not applied, with the first claim linked or waiting. A newer different claim after a first claim that came by this path leaves the first standing and the row held. | G1b, C2c |
| Removed head | The claimant was withdrawn by the feed before the claim arrived: the claim is recorded and linked; when the row comes back without the claim it is held at once. | G1d |
| Later omission (clause 6) | Later versions without the claim stay blocked or held. | G1e |
| Several retained versions; retained data that differs from the governing row | Applied once; the governing row is unchanged. | G1f |
| A message with no order value against an ordered row | Never replaces the governing row; the claim applies once (see UC-22 for its repeats). | G1g |

Run against the RE checkpoint source, 9 of these 15 probes report WEAK (`evidence/baseline-re-source-rf-probes.txt`), so they do discriminate.

**Other paths on which a claim could be recorded without being applied.** A card claim is recorded in exactly four places in `card_source_revision`. I went through each, and the order search below exercises all of them:

1. Same row, same order, and the row already has a claim: the message is either a repeat (nothing recorded) or a second, different claim (clause 7; recorded, not applied, by design).
2. Older or conflicting message already on file: this was RF-01; it now applies a first claim.
3. Older or conflicting message kept as a new version: applied a first claim before and still does.
4. Accepted new governing version: applies the claim unless it differs from the one the row has (clause 7).

A first claim for a target that is not on file always leaves the event that the end-of-intake step looks for, so it links when the target arrives, including when the claimant has been revised, withdrawn or replaced in between. The human selection route records and applies in one transaction. Claims carried inside the row data change the data hash, so such a message is never mistaken for one already on file; it takes path 3 or 4.

**The owner's invariant** (no card row with a first declared claim whose target is on file and no link) is checked after every delivery in every order of my extended search: 0 violations in 2,640 orders. On the RE checkpoint source the same check fires in 190 of the 720 baseline orders (six families).

## My order search, extended

`exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py`, unmodified, on the delivered source: 480 orders, 0 double, 0 released, 0 audit failures (`make rf-gate` and my own run with results kept per family).

`fable_rf_step_search.py` is new. It keeps the method (every permutation; after every step an honest operator prepares December, ties the statement, clears each blocker that has an ordinary disposition and asks an independent reviewer to approve every December row; November stays locked and nobody holds the lock grant) and adds twelve families that the first script does not contain. Each mixes the RF-01 pattern with one or two other things. It also checks more at every step: the owner's link invariant, and, in every second order, that an immediate repeat of each delivery is a no-op.

| Family (steps) | Orders | Double | Released | Unlinked first claim | Repeat changed (of orders checked) | Repeat of a retired row | Approved while waiting (UC-20) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 8 revised (amount, date) | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; revised receipt for Q | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 7; Q seq 7 with another amount; the same claiming P; Z replacing Q | 120 | 0 | 0 | 0 | 0 of 60 | 21 | 40 |
| P; Q seq 7; Q seq 6; Q seq 6 with the claim inside the row data; Z replacing Q | 120 | 0 | 0 | 0 | 0 of 60 | 19 | 40 |
| the RF-01 family with timestamps instead of sequence numbers | 120 | 0 | 0 | 0 | 0 of 60 | 19 | 40 |
| P; Q claiming P; Z seq 7; Z seq 6; Z seq 6 claiming Q | 120 | 0 | 0 | 0 | 0 of 60 | 13 | 30 |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 5 claiming B (B on file) | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q seq 8 claiming B (B on file) | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; Q withdrawn (seq 8); Q re-sent (seq 9) | 720 | 0 | 0 | 0 | 0 of 360 | 0 | 0 |
| P; Q seq 7; Q seq 6 claiming P; Q seq 8 claiming B; a person with disposition authority only selects B | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 6; Q seq 6 claiming P; Q seq 8 claiming B; a person selects P | 120 | 0 | 0 | 0 | 0 of 60 | 0 | 0 |
| P; Q seq 7; Q seq 6; Q seq 6 claiming P; Z replacing Q; Z revised | 720 | 0 | 0 | 0 | 0 of 360 | 172 | 300 |
| **Total, delivered source** | **2,640** | **0** | **0** | **0** | **0 of 1320** | 244 | 450 |

Audit chain: verified at the end of every order (0 failures). The first script on the delivered source: 480 orders, 0 double, 0 released, 0 audit failures, 40 approved while waiting (UC-20).

"Double" means: A1 is approved in locked November while a December row is approved that reaches A1 through delivered claims whose targets are all on file; a row with two declared targets and no selection counts through either; after an accepted selection only the selected target counts. "Approved while waiting" is the case counted apart, as before (UC-20): a replacement of a waiting claimant is approved while the claimed target has not arrived. The search script's own flag for this looks for a missing locked row; in these families the late row is P, so that flag cannot fire, and I counted the case afterwards from the kept trail of every order (`evidence/uc20-from-trails.txt`, script `evidence/scripts/uc20_from_trails.py`): 450 orders. In every one the approval had stopped governing and the row was held at the step at which the target arrived, and the waiting claimant itself was never approved.

In the two selection families the person step is tried at every position. A selection of the open row by someone without the lock grant was refused whenever the row was held, and accepted only where no hold existed; no held row or receipt was admitted to December in any order.

Six of these families were also run on the RE checkpoint source: 720 orders, 60 with a double approval, 190 with an unlinked first claim, 0 released. So the search finds the defect it was built for.

"Repeat of a retired row" is observation UC-21 below; it is the same on the RE source and is not counted as a failure.

Two notes on how this was run. A first pass of six families ran with a stricter repeat criterion that counted UC-21 as a failure; its output is kept under `evidence/search-first-pass/` and is superseded. I began four of the families with six deliveries (720 orders each, with the open row B arriving at every position) and stopped them for time; they are delivered here with B on file before the permutation starts (120 orders each). B arriving late is covered by the first script's families and by probe C7a.

## RF-02: selectors stay contributors

**What changed.** The preparation context now carries the authors of every target selection recorded for a row or for any row it was ever linked to, and those people are written as contributors of the row's artifact. Nothing is rewritten; the latest selection still decides which target stands.

| Asked | Result | Probe |
| --- | --- | --- |
| Confirming and replacing selections | Three people select in turn (choose, confirm, replace). All three are contributors of the row, of its revision, of its live replacement and of the replacement of that replacement. Each is refused as reviewer and as finalizer. An independent reviewer approves and an independent finalizer finalizes. | G2a, C9h |
| Historical selections byte-identical | Each earlier record is unchanged after each later one and at the end. | G2a |
| Ancestry retargeted | The replacement is itself contested and a person selects a target other than the row it replaced: the earlier selector is still a contributor of the replacement. | G2f |
| A selector's own earlier approval | A person approves the row as an independent reviewer, a second claim arrives, and the same person then records the selection: the earlier approval does not come back, and that person cannot approve. | G2b |
| Ordinary disposition rules unchanged | The same scenario (one person clears the transition, a second person later clears a revised receipt and the transition again) gives identical contributors, blockers and review results on the RE and RF sources. | G2c |
| Scope isolation | A selection for one row adds no contributor to an unrelated row in the same period or to a row in another period. With the same row identities and the same person ids in a second client scope of one database, a selection in one scope changes nothing in the other. | G2d, G2e |

See UC-23 for one side effect in the safe direction.

## RF-03: speed without a skipped check

**What changed.** Inside `period_outcomes` in `accounting_agent/packages.py`, whether a run is current is computed once per run instead of once per artifact, and only when the caller is inside a database transaction. Outside a transaction every artifact is evaluated as before. `tests/test_http.py` is byte-identical to the RE and RD checkpoints, deadline included.

**Is it the same computation?** By reading: the remembered values live in a variable of one call; nothing survives the call, and the report code writes nothing, so inside one transaction two evaluations of the same run cannot differ. By test: `evidence/scripts/fable_rf_equivalence.py` wraps the report function, and at every call computes it both ways on the same connection and compares the complete results.

| Wrapped run (unchanged script) | Report calls inside a transaction | Outside | Differences | Currentness evaluations, delivered / full |
| --- | --- | --- | --- | --- |
| Demo data (the seed the HTTP tests use), single-threaded | 22 | 1 | 0 | 55 / 286 |
| My 15 new probes | 52 | 0 | 0 | 50 / 88 |
| My 21 RE probes | 65 | 0 | 0 | 63 / 120 |
| 13 RD probes (the original Y05 reports WEAK, as it has since D-026) | 57 | 0 | 0 | 54 / 100 |
| RC probes | 31 | 0 | 0 | 29 / 52 |
| RB probes | 15 | 0 | 0 | 15 / 26 |
| RA probes | 4 | 0 | 0 | 4 / 7 |
| Order search, family older-resent-with-claim (120 orders) | 120 | 0 | 0 | 120 / 240 |
| **Total** | **366** | **1** | **0** | 390 / 919 |

No difference at any call, in states that include claims, links, conflicts, selections, revisions, replacements, locked periods and finalized packages (the probes build all of them). The shortcut was exercised, not bypassed: in the demo data the delivered code evaluated currentness 55 times where the full computation needs 286. Outside a transaction nothing was reused.

**Timing.** The unchanged script from my last review (`evidence/scripts/http_setup_timing.py`, identical to `exports/FABLE_RE_ACCEPTANCE/evidence/scripts/http_setup_timing.py`), seconds until the background worker finished; the test's deadline is 5.0 (shell job-control lines left out here; the complete file is `evidence/http-setup-timing.txt`):

```
== idle, before the five runs
2026-11-17T03:37:07Z
22:37  up 7 days,  9:11, 1 user, load averages: 16.30 8.46 19.60
rd_x seconds until the worker finished (test deadline is 5.0): ['10.06', '9.70', '12.18', '20.66', '7.78']
rf_x seconds until the worker finished (test deadline is 5.0): ['3.14', '3.47', '2.77', '3.28', '2.89']
re_x seconds until the worker finished (test deadline is 5.0): ['11.16', '19.24', '19.59', '11.06', '11.09']
== 8 busy processes, RD then RF then RD then RF (same load for both)
22:39  up 7 days,  9:14, 1 user, load averages: 26.22 16.99 21.29
rd_x seconds until the worker finished (test deadline is 5.0): ['15.79', '13.83', '11.25', '17.58']
rf_x seconds until the worker finished (test deadline is 5.0): ['3.99', '3.15', '3.16', '3.09']
rd_x seconds until the worker finished (test deadline is 5.0): ['8.10', '9.63', '10.51', '10.24']
rf_x seconds until the worker finished (test deadline is 5.0): ['2.79', '3.02', '3.17', '2.55']
22:42  up 7 days,  9:16, 1 user, load averages: 87.45 61.98 39.93
== 16 busy processes, RD then RF then RD then RF (same load for both)
22:42  up 7 days,  9:17, 1 user, load averages: 64.83 58.48 39.19
rd_x seconds until the worker finished (test deadline is 5.0): ['15.16', '18.96', '25.77', 'not within 60']
rf_x seconds until the worker finished (test deadline is 5.0): ['8.14', '3.84', '4.47', '4.26']
rd_x seconds until the worker finished (test deadline is 5.0): ['19.01', 'not within 60', '11.39', '10.63']
rf_x seconds until the worker finished (test deadline is 5.0): ['3.11', '2.77', '8.80', '2.76']
22:46  up 7 days,  9:21, 1 user, load averages: 32.82 43.77 37.76
== idle, after the five runs
2026-11-17T05:37:53Z
 0:37  up 7 days, 11:12, 1 user, load averages: 3.60 4.31 6.31
rd_x seconds until the worker finished (test deadline is 5.0): ['4.47', '4.05', '3.83', '3.98', '4.12']
rf_x seconds until the worker finished (test deadline is 5.0): ['2.06', '2.32', '2.20', '2.23', '2.21']
```

How to read this, with RD and RF always measured back to back under the same conditions:

| Condition | RD checkpoint (s) | Delivered RF (s) |
| --- | --- | --- |
| Quiet machine (last block, load average 3.6) | 3.83 to 4.47 | 2.06 to 2.32 |
| Machine still settling after the searches (first block, load average 16; headed "idle" in the raw file, but it was not) | 7.78 to 20.66 | 2.77 to 3.47 |
| 8 busy processes added | 8.10 to 17.58 | 2.55 to 3.99 |
| 16 busy processes added | 10.63 to 25.77, twice not within 60 | 2.76 to 8.80 (two of eight above 5.0) |

The delivered setup is faster than RD's in every pairing, about half the time on a quiet machine, so the cost is below the RD level and not merely back to it. The RE checkpoint, measured once in the first block, took 11.06 to 19.59 seconds where the delivered code took about 3. Inside the real suite the HTTP class setup took 2.36 to 3.39 seconds in the five consecutive runs (next table). With sixteen extra busy processes the delivered setup can still exceed five seconds; RD exceeded it in every loaded measurement, so this is the test's known sensitivity to machine load and not something this pass introduced.

**`make test`.** Unmodified, on clean disposable copies:

| Run | Exit | Methods passed | HTTP methods passed | HTTP class setup inside the suite (s) | Worker wait inside the suite (s) | Suite (s) | Load averages before |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 241 of 241 | 11 | 2.43 | 2.22 | 1531.639 | 24.70 39.84 36.64 |
| 2 | 0 | 241 of 241 | 11 | 2.67 | 2.49 | 1427.187 | 4.74 9.56 18.84 |
| 3 | 0 | 241 of 241 | 11 | 3.39 | 3.15 | 1624.468 | 26.73 25.69 22.16 |
| 4 | 0 | 241 of 241 | 11 | 2.36 | 2.20 | 1006.603 | 7.22 17.58 21.87 |
| 5 | 0 | 241 of 241 | 11 | 2.45 | 2.29 | 1015.042 | 4.21 5.41 10.20 |

The five consecutive runs were made one after another with no other job of this review running. The machine was not perfectly quiet throughout: its own background services (photo analysis and Spotlight indexing) and one unrelated process of the user's were active, and run 1 started while the load from the timing measurements was still decaying. The load averages before each run are in the table; runs 4 and 5 ran on a quiet machine. Extra load makes the five-second deadline harder to meet, not easier. The setup time inside the suite comes from an observation hook (`evidence/hook/sitecustomize.py`) that reads the clock around the unmodified class setup and changes nothing. One more run was made at the start, without the hook, while about twenty other jobs of this review were running (load average above 100): exit 0, 241 of 241 methods, 11 HTTP methods, 2601.023 seconds. A last run on the quiet machine without the hook: exit 0, 241 of 241 methods, 11 HTTP methods, 1018.939 seconds.

No test method is skipped or marked as an expected failure anywhere (the only matches for "skip" in the tests are two method names about skipped schedule slots).

## PRV-16

By comparing every record with the RE checkpoint (`evidence/preservation.txt`): 88 records, same ids in the same order, exactly four changed (AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03, and the scope note of AAOS-GOV-02), and in those only the Scope note and Evidence fields. No acceptance criterion, implementation state or product decision changed.

- BNK-03, CTL-04 and GOV-03 stay Verification failed, cite the RE review at `4890b297…98ae`, say that RE-02, RE-03, PRV-14 and PRV-15 were accepted there, and name RF-01 to RF-03 as developer evidence only.
- AAOS-BB-01 and AAOS-BB-02 are byte-identical; AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 and RPT-03 are byte-identical and Proposed; the four verified records are byte-identical.
- `docs/INDEPENDENT_VERIFICATION_RESULTS.json` has the seven rows in the original order, each taken from the RE review.
- `DECISIONS.md`: the RE-checkpoint text is an unchanged prefix, so D-016, D-017, D-026 and D-029 are as they were. Appended: D-030 and D-032 (developer records, marked as such) and D-031 (the owner's answer, quoted).
- `tests/schema_v1.sql` and `accounting_agent/storage.py` are byte-identical.

**Fault injection.** The four original scripts, unmodified, on disposable copies: 37 of 37, 44 of 44, 34 of 37 and 29 of 35, as the developer reports. I agree with the developer's reading of the nine disagreements. H22 to H24 were written when the RC review was the newest authority, and J14, J15, J16, J18, J22 and J25 when the RD review was the newest and the RE bundle unreviewed. Each one alters or follows an authority that a later review now overrides, so the checker is right to answer differently, and I would not weaken latest-wins to satisfy them.

My own cases for the fourth authority (`evidence/scripts/fable_rf_register_faults.py`, 62 cases, all agree): every reordering of the seven rows, a dropped, duplicated and extra row; one byte added to each of the eight pinned files; the RE files emptied; the checker's pins without the RE entries or in a different order; with the pin moved, the RE verdict controls each record in both directions; an altered and re-pinned RD, RC or RB file cannot override it, and results or a register that follow the older file are rejected; a record missing from the RE file falls back to the RD verdict only if the results row says so; stale report, bundle hash, report hash and scope in a results row; none of the three failed records can be raised in the register.

**The method rewritten under D-031.** Of the 227 methods of the RE checkpoint, 227 are present and 226 are textually identical; no earlier test file changed otherwise (imports, fixtures and helpers included). The before and after texts and the diff in the developer's report equal the real ones. The first half is unchanged and runs against the real four pins. The second half leaves the two RE entries out of the pinned-input data; the two assertions are unchanged and nothing is stubbed. One thing is new in its fixture, noted as UC-25(b). Five new methods test the real four-authority configuration.

## Gates, tests and preservation

- **RF gate.** `scripts/verify_re_acceptance_review.py` runs my 21 probes and the 480-order search and is wired into `make rf-gate`; the probes also run inside `make test`. My fault injection on its validators, fed the real outputs of this checkpoint (56 cases, all agree), rejects a non-zero exit, a WEAK, ERROR or changed verdict (a NOTE that becomes OK and an OK that becomes NOTE included), a missing, duplicated, unknown, renamed or reordered probe, a missing or doubled summary, a missing, duplicated, extra or reordered order, a renamed family, a double, a release, a failed or missing audit flag, every altered summary field and results edited after the run. Run against the RE checkpoint source, the gate exits 1.
- **RE gate.** My fault script from the last review, unchanged, with this checkpoint's real outputs: 33 of 33.
- **Tests.** 241 methods: 227 earlier, 14 added (6 corrections, 3 gate, 5 register).
- **Source.** Against the RE archive: no file removed; 15 changed, all expected (three source files, the checker, one test file, the Makefile, the register, the results file, six project documents and the manifest); 453 added. Applying `source-and-tests.patch` to the RE archive reproduces all 89 code, test, script, review and Makefile files exactly. `changed-files.json` lists every difference I found except its own two self-artifacts and the manifest, as it says.
- **Archives and inputs.** All 16 earlier archives keep their hashes in the bundle and in the working project; so do the RE bundle and the RE response. All 1,198 protected inputs match in both places; 1,011 of them are byte-identical to the RE bundle and 167 to the RE response archive. The working project equals the bundle for all 1,790 payload files.
- **History.** Branch `review/fable-rc-acceptance`, head `5af9a6194bc39e2f303cc6b43b0b59094118b8e4`, ten commits, nothing staged; the developer added no commit.

## Commands I ran

All on clean disposable copies, unmodified, with complete stdout, stderr and exit codes under `evidence/commands/`. macOS 26.5.2 x86_64, Python 3.9.6, SQLite 3.51.0, GNU Make 3.81.

| Command | Exit | Result |
| --- | --- | --- |
| My 21 RE probes, unmodified | 0 | 19 OK, NOTE: C9c, C9g |
| My 480-order search, unmodified (four processes, one per family) | 0/0/0/0 | 480 runs, 0 double, 0 released, 0 audit failures |
| 12 supplied RD probes | 0 | {'OK': 12} |
| Adapted Y05 (byte-identical to the RE bundle) | 0 | {'OK': 1} |
| Supplied 336-order search | 0 | SUMMARY runs=336 double=0 finalized_silently=0 |
| RC probes | 0 | {'OK': 15, 'NOTE': 1} |
| RC order search | 0 | SUMMARY runs=120 double=0 finalized_silently=0 |
| RB probes | 0 | {'OK': 16, 'NOTE': 2} |
| RA probes | 0 | Verdict counts: {'OK': 14} |
| Developer's D-029 reproduction | 0 | PASS |
| `make check` | 0 | passes |
| `make batch2-gate` | 0 | Summary: DEFERRED-OK=21, FIXED=10, PASS=29; synthetic month passes |
| `make reverification-gate` | 0 | passes |
| `make acceptance-gate` | 0 | Verdict counts: {'NOTE': 1, 'OK': 19}; Verdict counts: {'NOTE': 1, 'OK': 23}; U4 the only NOTE |
| `make rb-gate`, `rc-gate`, `rd-gate`, `re-gate` | 0, 0, 0, 0 | pass |
| `make rf-gate` | 0 | 21 probes as above; 480 orders, 0 double, 0 released, 0 audit failures |
| `make rf-gate` script on the RE checkpoint source | 1 | refused, as it must be |
| `register_faults.py` (F) | 0 | 37 of 37 agree |
| `fable_rc_register_faults.py` (G) on a copy | 0 | 44 of 44 agree |
| `fable_rd_register_faults.py` (H) on a copy | 1 | 34 of 37; H22-H24 obsolete as explained |
| `fable_re_register_faults.py` (J) on a copy | 1 | 29 of 35; J14, J15, J16, J18, J22, J25 obsolete as explained |
| My new probes (15) | 0 | G1c NOTE, G1g NOTE, G5a NOTE; the other 12 OK |
| My new probes on the RE checkpoint source | 1 | {'WEAK': 9, 'NOTE': 2, 'OK': 4} |
| `make test`, five consecutive runs | 0, 0, 0, 0, 0 | see RF-03 |

Most of these ran side by side on a heavily loaded machine, which is why some took longer than in the developer's logs. Only the HTTP timing and the consecutive `make test` runs were made with no other job of this review running.

## How to reproduce

Work only in an extracted copy of the bundle (`<copy>`); `<here>` is this folder. Python 3.9, no network.

```
python3 <here>/fable_rf_acceptance_probes.py <copy>                       # expected: 12 OK, G1c G1g G5a NOTE, exit 0
python3 <here>/fable_rf_step_search.py <copy> --family NAME --json out.json   # one family per process; --shard I/3 for the two 720-order families
python3 <here>/evidence/scripts/uc20_from_trails.py <dir with the results> rf-
python3 <copy>/exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py <copy> --family NAME --json out.json
python3 <here>/evidence/scripts/fable_rf_equivalence.py <copy> <probe or search script> [its arguments]
python3 <here>/evidence/scripts/fable_rf_register_faults.py <a second disposable copy>   # expected: cases 62, agree 62
python3 <here>/evidence/scripts/fable_rf_gate_faults.py <copy> <stdout of the 21 probes> <dir with the four family outputs>   # expected: cases 56, agree 56
python3 <here>/evidence/scripts/http_setup_timing.py <copy> 5             # and the same with an extracted RD bundle
cd <copy> && make test                                                    # five times in a row; 241 methods, OK
```

The baseline runs use a copy in which `accounting_agent/` is replaced by that folder from the RE bundle; on it the new probes report 9 WEAK and the search reports doubles and unlinked first claims. The exact command lines, start times and exit codes of every run are in `evidence/commands/*.json`, and `evidence/README.txt` describes each evidence file.

## Observations for the owner (no ticket)

- **UC-21 (new; same at the RE checkpoint).** If a row has been retired by its replacement in the open period, an identical repeat of that row's message is stored as a new version and answers `changed: True`; the row is retired again in the same intake. Nothing is approved twice or released. Clause 5 speaks of repeating a claim; you may want it to cover this.
- **UC-22 (new; same at the RE checkpoint).** A message with no sequence number or timestamp, for a row governed by one, is kept as evidence each time it is repeated if its data differs from the governing row. No accounting effect.
- **UC-23 (new).** A selector is also made a contributor of the period-level artifacts of that card run (statement workpaper, inventory, package manifest). Stricter than you decided, in the safe direction.
- **UC-24 (new).** The fingerprint gained an entry, so a database prepared by the RE checkpoint shows open-period approvals as stale when this checkpoint opens it, until the period is prepared and reviewed again. Locked periods are unaffected. Fail-safe; relevant only once a database is kept across versions.
- **UC-25 (new).** (a) The checker does not compare the citation text of a failed record with the latest review (unchanged; covered here by byte comparison). (b) The rewritten D-031 method takes its three-authority results rows from the checker instead of editing a row by hand; within your conditions, slightly less independent than before.
- **UC-20 (unchanged).** Verified again on the RF-01 path: the approval of a replacement given while the claimant waits stops governing the moment the target arrives.
- U4, UC-14, UC-17, UC-18, X08, N02c and N04e are unchanged and open; C9c and C9g stay NOTE. UC-9 remains reading only; journals were not exercised.

## What I did not do

I did not exercise the HTTP route for the target selection beyond the developer's own tests; my probes call the service operations the route passes through. I did not test journals (excluded by D-026), more than two periods or more than one card account. The equivalence check for RF-03 outside a transaction is single-threaded; with the worker running concurrently two computations cannot be compared at the same moment, so there I rely on the code, which evaluates every artifact afresh. I did not change the register: recording the three verdicts is a separate change for you to assign.

## Files in this folder

- `FABLE_RF_ACCEPTANCE_RESULTS.json`: per-ticket and per-clause verdicts, register verdicts, checkpoint hashes, search and command results.
- `FABLE_RF_CORRECTIONS.json`: no tickets; the observations.
- `fable_rf_acceptance_probes.py`, `fable_rf_acceptance_output.txt`: my new probes and their output on the delivered source (439 assertions).
- `fable_rf_step_search.py`: my extended order search.
- `evidence/`: command outputs and exit codes, search results per family, fault-injection scripts and outputs, the equivalence wrapper and its results, timing, tree and register comparisons, the baseline run.

Developer passes are not independent acceptance, and this review does not by itself promote any requirement or grant readiness. It authorizes no implementation and no live action.
