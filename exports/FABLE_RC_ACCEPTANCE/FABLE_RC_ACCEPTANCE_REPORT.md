# Fable independent verification of RC-01 to RC-03 and PRV-01 to PRV-10

16 November 2026. Reviewed: `FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454` (matches the sidecar and the package check).

All data is fictional. Every database was temporary. I worked in disposable extracted copies; the delivered archive, the working source and both earlier review folders were only read. Nothing was connected, posted, paid, sent or deployed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

Every conclusion below applies to that bundle hash and to synthetic local preparation controls only. None of it establishes client accounting policy, reconciliation completion, close or operating readiness.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RC-01** | **Accepted.** Every assertion in the ticket holds in both delivery orders. |
| **RC-02** | **Accepted.** Every assertion holds for the eligible and the already approved terminal source. |
| **RC-03** | **Accepted.** Every assertion holds, including a claimant that was already replaced. |
| **RB-01** as a whole | **Not accepted.** Two further delivery orders still leave one charge approved in locked November and in open December (RD-01, RD-02, both P1). Neither is a regression. |
| **PRV-01 to PRV-10** | **Accepted.** Two small residuals in the check (PRV-12, PRV-13, both P3). |
| AAOS-BNK-03, AAOS-CTL-04, AAOS-GOV-03 | **Remain Verification failed**, now for RD-01 and RD-02. |
| AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02, AAOS-CTL-09 | Remain Independently verified; their probes still pass at this checkpoint. |
| G0 technical criteria | **Not met.** Batch 3 stays closed. |

The correction pass did what it was asked to do, and did it cleanly: the three tickets are closed, nothing regressed, every earlier test and archive is intact, and the register check now enforces its own rules. What still fails is the requirement behind the tickets. It says "regardless of arrival order", and I found two orders that no ticket named.

## What I verified for RC-01 to RC-03

The developer's 18 unchanged probes test the outcome "not approved in two periods". The tickets assert more than that, so I wrote each assertion as its own check (probes Q01, Q02, Q02i, Q03 in `fable_rc_acceptance_probes.py`). The same probes fail on the V2 source and pass on this one, so they do discriminate (`evidence/baseline-v2-source-rc-probes.txt`).

**RC-01, withdrawal after the lock (Q01, both orders).** After B1 claims the withdrawn A1: December has no governing B1; B1 and its receipt are held under November; a blocked move row with had_approval exists for B1; the withdrawal of A1 is listed in `state.source_exceptions` under November; December cannot be finalized silently. After reopening November: A1 no longer governs November, December has exactly one item for the charge and it carries the transition blocker, the withdrawal leaves the exception list, and no version of A1 was dropped. After relocking, a revision of B1 stays in December.

**RC-02, late link on a middle source (Q02, both variants).** After B1 claims A1: neither C1 nor B1 governs December; C1, B1 and C1's receipt are held under November. Where C1 had been approved, an approved-source event names the approval, ITEM_LEFT_POPULATION is recorded, a blocked move row with had_approval exists for C1, and the approval decision is still in the history. After reopen only C1 governs December, it discloses the whole chain, and the earlier settlement acceptance has lapsed: C1 needs a new acceptance before it can be approved. The old decision is not rewritten. This is the `exceptions.py` change the developer disclosed; it behaves as described.

**The no-op rule (Q02i).** An intake that does not touch a chain added exactly its own two bindings and no move, link or chain event, for a held chain, a released and relocked chain, and an open-period chain. Replaying the batch added nothing.

**RC-03, claim resolved when the target arrives (Q03).** In the ticket's order, A1Y is held as soon as A1X arrives and A1Z is held when it arrives. With the claimant already replaced before its target arrives, and with all three delivered newest first and nothing re-sent, no chain member governs December and none can be approved; after reopen only A1Z is admitted and neither A1 nor A1X ever entered December. A target in an open period resolves to an ordinary supersession with no unresolved blocker, no quarantine and no blocked move. Two rows that each claim the other produce one link, not a cycle. A pending claim survives a restart (X09).

I also combined the tickets with each other (withdrawn root plus unresolved claim, withdrawn root plus late middle link, link and terminal in one batch, a four-deep chain, a second unrelated chain in the same period). All held (X03 to X07).

No schema change was made: `storage.py` and `tests/schema_v1.sql` are byte-identical to V2.

## Confirmed blockers

Both were found by trying deliveries the tickets did not list. Both exist in the V2 source as well, so this pass did not introduce them. Both end the same way: A1 approved in locked November, a replacement approved in open December, December finalized without acknowledgement.

### RD-01 (P1): the claim is declared on an unchanged row before its target arrives

1. A1Y (3 Dec, 40.00) arrives with no claim and is admitted to December.
2. The provider sends A1Y again, byte for byte the same, now saying it supersedes A1X. A1X has not arrived. The intake answers `changed: False`.
3. A1X arrives saying it supersedes A1, and is held under November.

The claim in step 2 is recorded nowhere except the stored packet: no event, no link, no blocker. A1Y stays eligible with an empty blocker list. If a reviewer had already approved A1Y, that approval simply stands and December finalizes with no further decision by anyone (probe X01d).

Cause: `source_revision` forces a new version for a claim only when the claimed row already exists (line 31). Otherwise unchanged bytes return early (lines 32–36), before the line that records the unresolved claim (47–48).

Controls: if the claim is repeated after A1X exists, or is carried inside the row so the bytes change, the control holds (X01b, X01c). So the outcome depends on whether a later message happens to change a byte.

### RD-02 (P1): the claimant gets a newer version while its claim is unresolved

1. A1Y arrives saying it supersedes A1X, which has not arrived. A1Y is admitted and held as unresolved. Correct.
2. A1Y is revised to 41.00, and the revision does not repeat the claim. Both transition blockers disappear from the new version.
3. A1X arrives saying it supersedes A1, and is held under November.

A1Y is never linked. Once the revised receipt is accepted, A1Y is approved.

Cause: the recorded claim is matched to one snapshot (`resolve_pending_supersessions` line 117; `context` lines 260–262). A recorded link, by contrast, belongs to the row's identity and survives a revision. The same thing happens when a row that was retired by its own replacement is re-sent unchanged, because that also creates a new version (orders `Yc Z Yp X` and `Z Yc Yp X` in the search).

The condition "claimant snapshot is still the head" comes from my own RC-03 correction text, and the code implements it as written. As with RC-01 last time, this is a gap in what I specified as much as in what was built.

### How far it reaches: a 120-order search

Finding one more order by hand three reviews in a row is not a good way to converge, so I tested the requirement directly. `fable_rc_order_search.py` takes six kinds of delivery for one replacement chain (the row with and without its claim, a revision, the next replacement, the withdrawal of the locked charge) and tries every ordering of five families of four: 120 runs, each in its own database, each ending with an honest operator supplying the matching statement, clearing every blocker that has a disposition and asking for independent approval.

| Source | Orders ending with one charge approved in both periods |
| --- | --- |
| V2 correction source (before this pass) | 37 of 120 |
| This bundle | 18 of 120 |
| This bundle with the trial correction below | 0 of 120 |

In this bundle the family that contains only the deliveries of RC-01 to RC-03 (X, Yc, Z, V) has 0 failures in 24 orders, which is independent evidence that those three corrections are complete for what they targeted. All 18 failures are RD-01 or RD-02. The search is bounded: a three-link chain on one account. It is evidence for those deliveries, not proof for every feed.

### Correction, tried in a temporary copy

I applied one combined change to a throwaway copy (`evidence/experimental-correction-rd.patch`; one helper of 8 lines, one added line, 6 lines replaced, no schema change):

- RD-01: when a claim is declared, its target does not exist, and no pending claim for that target is already recorded for the row, force a new version so the existing code records the claim. A repeated identical claim stays a no-op.
- RD-02: treat a pending claim as belonging to the row's identity, as links already do, both when resolving it and when showing it as unresolved.

In that copy: my 16 probes report 15 OK and X08 NOTE; the order search reports 0 of 120; the 18 and 14 earlier probes are unchanged; `make test` passes all 192 methods; `make acceptance-gate`, `reverification-gate`, `batch2-gate` and `rc-gate` exit 0 (`evidence/experiment/`). It has no unit tests of its own and was not reviewed as a fix. Use it as a worked reference.

## PRV-01 to PRV-10

All ten meet their acceptance criteria. I checked each with my own parser (`evidence/prv-checks.txt`), ran the supplied fault script unmodified (37 of 37 agree, including the ten former GAP cases F21, F22, F23, F25, F26, F30, F31, F33b, F33c, F35, and all eleven `make check` mutations), and added 44 register cases and 10 `make check` cases of my own (`evidence/fable-rc-register-faults.txt`: 40 of 44 and 10 of 10 as wanted).

| Gap | Result |
| --- | --- |
| PRV-01 | The three records stay failed and cite RC-01 to RC-03; both criteria name the three delivery orders. The four raised records cite my RB report, `00a13d93…be001d` and their probes; UC-10 is in AAOS-CTL-09 and UC-11 in AAOS-BNK-02. Current evidence and the T-12, RA-01, RB-01 rows are updated. |
| PRV-02 | A missing test path, a bare ticket id, an undeclared probe-like token and a non-test file are rejected. An existing test file or a declared probe id is accepted. |
| PRV-03 | A failed record cannot be raised to any other state, or hidden as Not started. Self-asserted verification is rejected even with the real report and the real hash, unless the results file has a matching entry. The file lists the seven earlier conclusions correctly. **Residual (PRV-12):** the results file is an ordinary project file, so editing it together with the register is accepted (cases G16–G18). |
| PRV-04 | Both the header notice and the client panel are neutral. No first-client word is in any shared file under `accounting_agent/`. `make check` fails for the name in `index.html`, `style.css`, `app.js`, a new nested web file and a shared module; config, fixtures and `demo.py` stay exempt. |
| PRV-05 | All 18 dependencies of an Approved record on a Proposed one, in 13 records, say "if ratified" directly after their own id. Every instantiation reference is still there. The six unratified shared requirements and all nine Proposed decisions are unchanged; counts remain 77 Approved, 9 Proposed, 2 Rejected. |
| PRV-06 | The condition must follow the record's own id; "only" is no longer a condition. AAOS-GOV-02 and AAOS-ARC-01 depend conditionally on AAOS-GOV-01, which stays Not started. |
| PRV-07 | All five AAOS-EXC scope notes begin with their fixed phrase and agree with the table and the decision. Changing the prefix, the decision or the table row, or removing the row, is rejected. |
| PRV-08 | No Dependencies field contains `. ;` or `.;`, and both are rejected. |
| PRV-09 | 309 files differ from V2. 306 are listed with correct hashes and 3 are covered by a stated rule. The source-and-tests patch applies to the V2 tree and reproduces all 13 files byte for byte; no source, test or script change lies outside it. |
| PRV-10 | Terms are read from the client section and applied to every field and the title of shared records except Trace. A term I added to the list was enforced at once. Only AAOS-GOV-01, AAOS-ARC-04 and AAOS-KNO-01 name the first client. **Optional residual (PRV-13):** shortening the list goes unnoticed (case G44). |

PR-11 is preserved. AAOS-BB-01 and AAOS-BB-02 are identical to the pre-pass register (`a149f900…fb624`, which I confirmed is the committed version) in every field except Dependencies, where only the punctuation and "if ratified" changed. I have not asked for the confirmation again and it changes no state or gate.

## Integrity and preservation

- Bundle hash, sidecar and package check agree. All 740 manifest entries match the extracted files; the manifest's own hash matches the package check. No CRC error, no Git metadata, cache or database in the payload.
- Both response ZIPs keep `0562869a…5f399` and `d4c5795d…3d826`; the V2 correction ZIP keeps `00a13d93…be001d`. All 12 earlier archives match their sidecars. All 345 protected inputs are unchanged in the working project and in the bundle. Both review folders are identical to the first response ZIP.
- The three commits are unchanged and match `git-history-final.txt`.
- All 174 V2 test methods are present with unchanged bodies. 18 methods were added. The only earlier test file that changed is `tests/test_product_requirements.py`: nine methods added and one import line extended. No skip or expected-failure marker exists.
- The eleven commands changed no file in the copy they ran in.

## Commands I ran

All in disposable copies, unmodified, in the order given. Raw output and exit codes are in `evidence/commands/`.

| Command | Exit | Result |
| --- | --- | --- |
| `python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .` | 0 | exact 18 ids; 16 OK; NOTE for N02c and N04e only |
| `python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .` | 0 | 14 OK |
| `make test` | 0 | 192 methods OK, including the eleven HTTP methods; no skip |
| `make check` | 0 | 88 records, 27 tickets |
| `make batch2-gate` | 0 | reviewer cases 29 PASS, 10 FIXED, 21 DEFERRED-OK |
| `make reverification-gate` | 0 | 27 and 35 OK; corrective gate PASS |
| `make acceptance-gate` | 0 | U4 is the only NOTE |
| `make rb-gate` | 0 | 14 OK |
| `make rc-gate` | 0 | exact contract enforced |
| `python3 scripts/check_product_requirements.py --json` | 0 | 77/9/2; 36 Deferred, 25 Not started, 20 Developer-tested, 4 Independently verified, 3 Verification failed |
| `python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .` | 0 | 37 agree, 0 gaps; 11 `make check` cases as wanted |

No fault case changed meaning because of the register edits. As a negative control, the rc-gate logic run against the V2 source exits 1 with 3 WEAK. The supplementary observations N08 and N09 in the retained corrective script still print WEAK, as they did in the last review and as the developer discloses; they are not part of any gate verdict.

Environment: Python 3.9.6, SQLite 3.51.0, GNU Make 3.81, macOS 26.5.2, x86_64. The HTTP tests bound 127.0.0.1 without any extra permission.

## Observations that need a decision, not a fix

- **UC-14 (new, X08).** After a withdrawal has been validly admitted and November relocked, a new December row that claims to replace the withdrawn charge is held under November although nothing of it remains there. It is safe, and another reopen releases it. Whether that should need a reopen is a feed question for G2.
- **UC-15 (new, by reading).** A settlement acceptance recorded before this checkpoint has no chain binding and lapses under this source. Safe, disclosed in D-019, and only fictional databases exist.
- **UC-9 (unchanged, not run).** The RC-02 re-evaluation covers card transactions only. Journals in a replacement chain across a lock were not exercised.
- UC-10 (N02c) and UC-11 (N04e) are unchanged policy observations. U4 is unchanged. UC-12 is closed by RC-01.
- **For the owner.** RC-03, RD-01 and RD-02 all require the provider to deliver a replacement, or its claim, before the row it replaces. If the feed contract for G2 guarantees that this cannot happen, all three are unreachable. Without that guarantee they are reachable, and the engine should hold.

## What was not run

- The full literal RV and reverification probe scripts with every id. Not assigned; the maintained subsets ran through the gates.
- Bespoke probes for UC-6, UC-8 and UC-9.
- An external linter, type checker or JavaScript compiler (not installed), and the web page in a browser (read as text only).
- Delivery orders beyond the 120 in the search: longer chains, several accounts, journals, receipts delivered apart from their charge.

## Files returned

In `exports/FABLE_RC_ACCEPTANCE/`:

- `FABLE_RC_ACCEPTANCE_REPORT.md` (this file)
- `FABLE_RC_ACCEPTANCE_RESULTS.json`: machine-readable verdicts, including `register_verdicts` for the seven records
- `FABLE_RC_CORRECTIONS.json`: tickets RD-01, RD-02, PRV-11, PRV-12, PRV-13, with source lines, reproductions, corrections and acceptance assertions
- `fable_rc_acceptance_probes.py` and `fable_rc_acceptance_output.txt`: 16 probes; exit 1 on this bundle with X01, X01d, X02 WEAK
- `fable_rc_order_search.py`: the 120-order search
- `evidence/`: raw output and exit codes for every command, my check scripts, the baseline comparisons, the trial patch and its logs

The register was not edited. AGENTS.md requires it to follow every independent result; that is ticket PRV-11 for the next pass.
