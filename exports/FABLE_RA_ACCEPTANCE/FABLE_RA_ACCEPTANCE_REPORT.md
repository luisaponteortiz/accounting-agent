# Fable independent verification of RA-01 to RA-08

15 November 2026. Reviewed: `FABLE_RA_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `dec028b0…274e4f`, delivered inside `FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_BUNDLE.zip`, SHA-256 `b154db10…f61ea`.

All data is fictional. Every database was temporary. No source file was changed, and nothing was connected, posted, paid, sent or deployed. This report grants no human G0 acceptance, no G1–G4 authority and no Batch 3 authorization.

## Verdicts

| Subject | Verdict |
| --- | --- |
| **RA acceptance** | **Not accepted.** Five of eight corrections are accepted. RA-01 is not: one P1 regression (RB-01). RA-03 and RA-04 have one remaining route (RB-02, P2). |
| **G0 technical criteria** | **Not met.** One P1 and one P2 are open. |
| Retained C-01–C-06, RV-01–RV-17, Batch 2 | Retained in the delivered gates. The C-01 and RV-01 objective is breached by RB-01. |
| Five new setup adaptations | All five accepted (A03, A05, A17, X09, older RT18). |
| Seven earlier adaptations, strengthened RT14b | Retained unchanged. |

The requirements-register verdict is in `FABLE_PRODUCT_REQUIREMENTS_REVIEW.md`.

## Confirmed blockers

### RB-01 (P1, regression): one charge approved in two periods

A source that was admitted to an open period *before* it gained its supersession link is not quarantined when the link arrives.

Reproduction (probe R01b):

1. Approve A1 (3 Nov, 40.00). Lock November. December is open.
2. Intake B1 (2 Dec, 40.00) with receipt and December statement, with no supersession claim. It is admitted and eligible.
3. Re-send B1 with `supersedes = demo_card_001:A1`. Re-run December.
4. Disposition `SOURCE_TRANSITION_REQUIRES_REVIEW` as `settlement_verified`. Re-run. An independent reviewer approves B1.

Result in the RA source: B1 is approved in December, A1 stays approved in locked November, and December finalizes without acknowledgement. The move history records a move from December to December, not blocked.

Result in the frozen RV submission (`247c1cfd…`), same probe: B1 is quarantined under November with `SOURCE_MOVED_FROM_LOCKED_PERIOD` and leaves December. So the RA-01 correction removed a protection that existed. The comparison is in `evidence/baseline-frozen-rv-comparison.txt`.

A second route reaches the same result (probe R01c): A1Y arrives before the link A1X it replaces, is held as unresolved, A1X then arrives and is quarantined, and A1Y is re-sent so that its link resolves. A1Y is then approved in December and the quarantine entries for A1X disappear from `state.source_exceptions`. In the frozen submission this route was held only by the RA-06 defect.

Cause: `source_control.py` `source_origin` (lines 95–103) walks the chain starting with the source's own key and returns at the first key with any admitted binding. An earlier admission of the same key to December hides the locked ancestor. `service.py` `bind_source` (lines 219–226) then treats December as the origin, admits the source, and `apply_supersession` marks the approved ancestor removed while its period is locked.

Smallest correction: look at the ancestors first. If any ancestor's head is not removed and is either quarantined behind a locked period or admitted in a locked period, that period is the blocking origin. Only otherwise use the nearest admitted owner. This keeps the delivered relock regression, because after a valid release the ancestors' heads are removed.

### RB-02 (P2): re-pointing the old document avoids the revised-evidence hold

RA-03 and RA-04 detect a replacement under a new key only when the old key is *withdrawn*. If the old key is instead revised to name another transaction id (receipt) or another cycle (statement), nothing is detected.

- Probe R03b: receipt-A1 says 39.99 against a 40.00 charge. The preparer re-points receipt-A1 to a transaction id that does not exist and supplies receipt-A1-new at 40.00. The item is eligible, `evidence_revisions` is empty, and it is approved. No trace exists anywhere in state.
- Probe R04b: the statement says 90.00 against a 100.00 population. The preparer re-points the statement key to a January 2027 cycle and supplies a new key that ties. Both items are eligible, the workpaper has no `statement_revisions`, and the item is approved. The only trace is an unassigned-period exception for the old key.

Cause: `source_control.py` `evidence_revisions` line 81 requires `earlier['removed']`. Moving a receipt to another charge and attaching a new one is an ordinary clerical step, so this needs no intent.

Smallest correction: treat an earlier snapshot under another key as replaced when it has the same identity fields and its key's current head is either removed or no longer has those identity fields.

## Judgment per correction, in the prescribed order

| Ticket | Verdict | My evidence |
| --- | --- | --- |
| RA-01 | **Not accepted** | X01 and A01 pass unmodified. R01a passes: four-link chain, a receipt arriving before its transaction, a revision of a quarantined middle link, replay, reopen admitting only the last link, no intermediate ever admitted to December, relock followed by a destination revision, restart, audit chain. R01d passes: two- and three-step cycles and self-supersession refused atomically. **R01b and R01c fail (RB-01).** |
| RA-03 | Accepted for the specified routes; RB-02 open | X12k and A12 pass unmodified. R03a passes in both orders (withdraw with replacement; replacement before withdrawal): disclosed as replaced with both identities, versions, suppliers and changed fields; both suppliers refused; non-supplier accepts; acceptor and old supplier refused at final review; a further change lapses the acceptance; an additional still-active receipt stays a multiple-receipt issue. **R03b fails.** |
| RA-04 | Accepted for the specified routes; RB-02 and RB-04 open | X12s and A13 pass unmodified. R04a passes for same-key and withdraw-and-replace: every relying item held, workpaper discloses, direct approval refused, both suppliers refused, an acceptance that omits the statement refused, acceptance is item-bound (A1 accepted, A2 still held), acceptor refused at final review, a later change lapses it. **R04b fails. R04c is a NOTE (RB-04).** |
| RA-02 | Accepted | A10 passes unmodified. R02a passes: unlinked cosmetic vendor re-proposal and unlinked identical receipt policy keep the author barred; a different earlier category, an earlier rule that did not cover the description and a different earlier policy value do not; an independent reviewer approves. R02b (item-scoped or re-keyed identical rule) fails; this lies outside the RA-02 assertions and is recorded as RB-03 (P3). |
| RA-06 | Accepted | R01a: after reopen, `settlement_verified` citing the whole evidence list, including three predecessor snapshots, clears the blocker. The same call with a row of an unrelated November item added is refused. |
| RA-05 | Accepted | U1, RT10a and RT10b pass unmodified. R05 passes: a relevant vendor rule approved after the mandate suspends it; a close-checklist rule and a vendor rule effective next year do not; a second tick in the same occurrence does not dispatch twice. Period-boundary recurrence, caps, expiry and concurrency were not independently re-run (UC-8). |
| RA-07 | Accepted | A14 passes unmodified. R07 passes: own row, another item's row and another item's receipt are refused; the item's own receipt and its account statement are accepted. The journal-support path was checked by reading and by the delivered tests only (UC-9). |
| RA-08 | Accepted | R08 passes: the reverse exclusion is refused before re-preparation (as `source_replay`) and after it; a three-charge cycle is refused at the closing step and one charge keeps its entry; revocation restores both holds. X09 passes through the reviewed setup. U4 remains the permitted NOTE. |

## Lesser findings

- **RB-03 (P3).** The author of a general vendor mapping can approve a charge once a colleague re-proposes the identical mapping with item scope, or under a new rule key after the first rule's end date. `controls.py` `applied_rule_lineage` line 127 matches on exact key and exact item scope.
- **RB-04 (P3).** A prior-period statement restated while its period is open makes the next period's opening continuity report `verified`, with no disclosure in the next period. The prior period's items are correctly held.
- **UC-7.** `source_moves` records same-period rows for in-place revisions of a superseding source, and receipt rows in a blocked chain carry `had_approval` 0. No control effect.

Exact reproductions, corrections and regression assertions are in `FABLE_RA_CORRECTIONS.json`.

## Commands I ran

Python 3.9.6, SQLite 3.51.0, GNU Make 3.81, macOS (Darwin 25.5.0, x86_64). Run from a byte copy of the extracted checkpoint. Raw stdout, stderr and exit codes are in `evidence/`.

| Command | Exit | Result in my run |
| --- | --- | --- |
| `make test` | 0 | 154 methods OK in 379 s. No skip or expected-failure marker. |
| `make check` | 0 | Offline syntax, JSON, profile, registry and DOM checks. |
| `make batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK; corrective gate PASS. |
| `make reverification-gate` | 0 | 27 unmodified originals OK; all 35 reviewed-setup OK; frozen corrective checkpoint PASS. |
| `make acceptance-gate` | 0 | 20 unmodified originals: 19 OK and U4 NOTE. All 24 reviewed-setup: 23 OK and U4 NOTE. |
| `python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .` | **1** | 19 OK; A03, A05, X09 WEAK; A17 ERROR; U4 NOTE. As disclosed. Not a pass. |
| `python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .` | **1** | 28 OK; 4 WEAK; 3 ERROR. As disclosed. |
| `python3 fable_ra_acceptance_probes.py <root>` | **1** | 8 OK, 1 NOTE, 5 WEAK (R01b, R01c, R03b, R04b, R02b). |

The 154 count is reproduced: 136 methods in the frozen RV submission, none missing, 18 new (13 in `test_acceptance_corrections.py`, 5 in `test_acceptance_gate.py`). All platform and HTTP methods of the three earlier checkpoints are still present. I counted 41, 41 and 43 in those archives; the prompt says 40, 41 and 43.

Integrity: both manifests match (26 and 324 files), no unsafe archive paths, all 57 recorded input hashes match, and the 15 source, test and script files that differ from the frozen RV submission are all named in `changed-files.json`. Limit: I compared the 27 independent input files with the hashes the developer recorded. I had no separately held copy to compare against.

## The new setup adaptations

I diffed the originals against the maintained copies myself. The acceptance diff equals the delivered patch, and both generator scripts reproduce the copies byte for byte.

| Probe | Judgment | Reason |
| --- | --- | --- |
| A03 | Accepted | Helper asserts the hold and a disclosed *statement* revision before asking the existing dispositioner, who supplied nothing, to accept for A1 and A2. Removal and package assertions unchanged. |
| A05 | Accepted | Acceptance for M3 only. M2 keeps its unknown-vendor hold. |
| A17 | Accepted | The stale-finalization refusal still runs first. |
| X09 | Accepted | Acceptance for D2 only. The circular-exclusion phase is untouched. |
| Older RT18 | Accepted | The stale-package refusal still runs first. Minor: the helper asserts a hold and a disclosed revision but not that the revision is a statement. |

No actor or grant is added, no blocker is weakened, and every original `return` and assignment is identical. The seven earlier adaptations and the RT14b guard assertions are present unchanged; both RT14b guard tests pass.

## Teaching month and isolation

Re-driven through the unmodified original probes M1 and M2.

- Referral route: TX-009 keeps its 79.99 receipt; ten approvals; TX-007, TX-009 and TX-011 held; supplies +311.00, repairs +200.00, card liability −211.00, cash −300.00; nets to zero.
- Acceptance route: the corrected receipt is held, disclosed and accepted by a non-supplier; eleven approvals; supplies +391.00, card liability −291.00, same repairs and cash; nets to zero.
- Both: October evidence stays quarantined, reviewer and finalizer are outside every lineage, finalization without acknowledgement is refused, packages are preparation-only.
- A second client running December cannot decide, send or finalize for the first; the first client's records are unchanged and both audit chains verify.

Neither route is an accounting close or human G0.

## What was not run

- UC-6 (duplicated payment row vocabulary): not executed.
- RA-05 across a period boundary, caps, expiry, concurrency: delivered tests only.
- RA-07 for journals: inspection and delivered tests only.
- No external linter or type checker exists in the project.

## Files returned

1. `FABLE_RA_ACCEPTANCE_REPORT.md` (this file)
2. `FABLE_RA_ACCEPTANCE_RESULTS.json`: every command, probe and case, raw and assessed
3. `FABLE_RA_CORRECTIONS.json`: RB-01 to RB-04, open concerns, decisions for client authority
4. `fable_ra_acceptance_probes.py`: 14 service-only probes; exit 1 on a verified failure. The helper section is copied unchanged from my earlier script; one line records the database path for the restart check.
5. `fable_ra_acceptance_output.txt` and `evidence/`: raw logs, the runner, the probe sources, the frozen-baseline comparison, adapter diffs and inventory checks
