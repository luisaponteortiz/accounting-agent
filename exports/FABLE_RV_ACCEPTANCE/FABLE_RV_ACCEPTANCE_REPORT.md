# Fable acceptance review: RV-01 to RV-17

Independent review of `FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip`, 15 November 2026.
Review output only. It authorises no connection, posting, payment, model call, hosting, deployment or policy activation, and it opens no readiness gate. All data used is fictional.

Companion files: `FABLE_RV_ACCEPTANCE_RESULTS.json`, `FABLE_RV_CORRECTIONS.json`, `fable_rv_acceptance_probes.py`, `fable_rv_acceptance_output.txt`, and the raw logs and scripts in `evidence/`.

## 1. Confirmed blockers

One defect blocks acceptance.

**RA-01 (P1). A second supersession step releases a charge that is quarantined behind a locked period.**
November item A1 is approved and November is locked. A1X, dated December, supersedes A1 and is correctly quarantined. A1Y, also dated December, then supersedes A1X. A1Y is admitted to December and approved by an independent reviewer, while A1 stays approved in locked November. The quarantine entries for A1X disappear from the exception list. The same expense and liability are approved in two periods.
Cause: `bind_source` takes the origin period from the direct predecessor only, and only if that predecessor was ever admitted. A1X never was. Probe X01 reproduces it.

Three P2 defects should be fixed in the same pass:

| ID | Defect | Probe |
| --- | --- | --- |
| RA-02 | The RV-10 lineage follows only the optional `supersedes` link. A colleague who re-proposes the same rule without the link removes the first author from the lineage, and that author can then approve the items the rule codes. | A10 |
| RA-03 | The RV-12 hold applies per document key. Withdrawing a receipt and supplying a replacement under a new key gives a clean, approvable item with no revision disclosed. | X12k |
| RA-04 | A statement re-supplied to agree with the population is neither held nor disclosed as revised. Items that failed the statement control become approvable with no trace shown to the reviewer. | X12s |

## 2. Decisions

| Subject | Decision |
| --- | --- |
| RV-01 to RV-17 | **14 PASS, 3 FAIL** (RV-01, RV-10, RV-12). In all three, every assertion I wrote holds; the control is defeated by a route those assertions did not cover. |
| C-01 to C-06 on current source | **FAIL on C-01 only** (RA-01). C-02 to C-06 pass. |
| Batch 2 (T-09 to T-19) | **FAIL.** Ten of eleven tickets meet every criterion. T-12 has the one P1 defect. |
| Seven probe adaptations | **ACCEPTED, all seven** (section 4). |
| Strengthened RT14b | **PASS** under my own fault injection (section 4). |
| G0 technical criteria | **FAIL**, on the one open P1. Every other criterion is met. |
| Human G0 acceptance, G1 to G4 | Not for this review. All remain closed. |

This is a much stronger checkpoint than the last one. Eleven confirmed gaps and three notes from my previous probes are all closed. The previous six P1 defects are fixed, including under scenarios I built independently. What remains is one new P1 in the same area as RV-01, three P2 and four P3.

Codex's disclosures were accurate, including the ones against its own interest: the original full command still exits 1, and the original RT14b had become vacuous.

## 3. What I ran

| Check | Result |
| --- | --- |
| Archive checksum and `REVIEW_MANIFEST.json` | Match. 243 of 243 files, none unlisted. |
| My 22 files, four earlier inputs, three nested archives | All byte-identical to the originals. |
| `make test` | Exit 0. 136 tests, no failure, no expected failure, no skip. |
| `make check` | Exit 0. |
| `make batch2-gate` | Exit 0. 29 PASS, 10 FIXED, 21 DEFERRED-OK. Regenerated report identical to the delivered one. |
| `make reverification-gate` | Exit 0. 28 of my original probes OK run directly from my file; 35 OK through the adapted copy; frozen checkpoint passes. |
| `python3 scripts/synthetic_month.py` | Exit 0. Ten approvals, three held. |
| `python3 scripts/verify_corrective_checkpoint.py` | Exit 0. N01 to N07 OK on the frozen archive. This says nothing about current source. |
| My original full command, unmodified | Exit 1: 29 OK, 3 ERROR (RN02, RN03, RN07), 3 WEAK (RT12a, RT14a, RG0). Exactly as disclosed. |
| My new probes (`fable_rv_acceptance_probes.py`) | Exit 1. 24 probes: 16 held, 4 confirmed gaps, 4 notes. |
| RT14b fault injection, legacy-data upgrade, inventories, adapter structure | All pass (sections 4 and 6). |

Environment: Python 3.9.6, SQLite 3.51.0, macOS, no network. The delivered gates ran in a working copy. My probes ran against an untouched extraction, whose manifest still verified afterwards.

Not run: a browser walkthrough of the demo UI. Not verifiable from an archive: the order in which the corrections were made, and the baseline reproduction before changes. The delivered logs are consistent with both claims.

All 60 case IDs are listed individually in the results file. The 21 DEFERRED-OK cases mean the unavailable operation was refused with 403. They say nothing about how those capabilities will behave when built.

## 4. The seven probe adaptations

I checked the adapted copy three ways. The difference between my file and the copy is exactly the delivered patch. A structural comparison of all 35 probes shows every return statement and every verdict condition is identical, including the month, isolation and hand-calculation conditions in RG0. Six probe bodies and one helper changed, and one helper was added; nothing else.

| Probe | Judgment | Reason |
| --- | --- | --- |
| RN02 | Accepted | The only change is `{}` to the explicit no-evidence form that RV-11 itself provides. Issuer, independent approver and all conditions are unchanged. |
| RN03 | Accepted | Same single change. |
| RN07 | Accepted | Same single change, on a mandate deliberately left unapproved. The service approval is refused with 403 by the grant check, not because the mandate is invalid. The service-created mandate with `{}` is untouched and is refused by the human check, which runs first. |
| RT12a | Accepted | The newer delivery changes the receipt, so RV-12 requires a hold. The helper asserts the hold and the disclosed history first, then obtains acceptance from the existing dispositioner, who supplied neither version. No grant is added. |
| RT14a | Accepted | The helper adds candidate receipts only when a distinct-purchases call uses default evidence. The explicit empty-evidence negative is untouched and still refused. |
| RT14b | Accepted | Evidence now names the candidate receipt, still without the statement. The added assertions make the probe fail if its starting state is not reached. |
| RG0 | Accepted | Peer receipts are cited, and the corrected TX-009 receipt is accepted only after its hold and history are asserted. Counts and the hand calculation are unchanged. |

The API-change exception in my corrections file covers all seven: each change is forced by RV-11, RV-12 or RV-15, and none adds a grant, an actor or a bypass. RT10b's empty predicate and RT14d's own-row evidence are untouched and still refused.

**Strengthened RT14b.** My original RT14b prints OK on current source without ever making D1 eligible, so it had stopped testing anything. I injected three faults into the adapted copy through test-only substitutions of its helper functions:

| Fault | Runner verdict | Exit | Third charge constructed |
| --- | --- | --- | --- |
| Initial D1 disposition refused | ERROR | 1 | No |
| Initial D2 disposition refused | ERROR | 1 | No |
| D1 ineligible before the third charge | ERROR | 1 | No |
| No fault | OK | 0 | Yes: D1 eligible, then ineligible with POSSIBLE_DUPLICATE |

The two delivered fault tests do the same thing at the function level and pass.

## 5. RV-01 to RV-17

Each correction was tested twice: by my original probes through the delivered gate, and by a new scenario I built for this review. Per-assertion evidence is in the results file.

| ID | Status | Independent evidence |
| --- | --- | --- |
| RV-01 supersession under lock | **FAIL** | A01 holds for one step, by envelope and by data: quarantined with its receipt, origin approval kept, event raised, released on reopen with one governing item. X01 fails for two steps (RA-01). |
| RV-02 origin ownership | PASS | A02: the conflict survives a revision, a re-citation against the current version, and supersession under a new key. A stale reference is flagged. Withdrawing the journal clears the card item. |
| RV-03 departed items | PASS | A03: removed and voided rows have no governing item, their exceptions are superseded, history is kept, and the package lists them. |
| RV-04 locked periods undisturbed | PASS | A04: three December packets leave November with no exception, no event and no new binding row. A genuinely revised November receipt is still quarantined and raises an event. |
| RV-05 withdrawn mapping | PASS | A05: a proposed withdrawal changes nothing; the proposer cannot approve it; once approved it applies from its effective date; a November item still matches; reintroduction works from its own date. |
| RV-06 typed close evidence | PASS | A06: untyped entries refused in profiles and rules; labels do not satisfy reconciliation or tie-out lines. Legacy strings written by the previous version evaluate as unsatisfied (section 6). |
| RV-07 activity and account type | PASS | A07: 20 wrong treatments refused, each for the stated reason, including a purchase coded to cash and to the card liability. Settlement, credit, transfer, fee and interest paths produce the correct entries and are approved. A referred item is never approvable. |
| RV-08 candidate binding | PASS | A08 and the RT14b fault injection. |
| RV-09 surviving duplicate | PASS | A09: the survivor is eligible and cites the exclusion; the person who excluded cannot review it; revocation restores both holds and the earlier rejection, on a current projection. |
| RV-10 rule author lineage | **FAIL** | A10: holds with the link, and a different-category author is correctly not barred. Fails when the link is omitted (RA-02). |
| RV-11 freshness | PASS | A11: eight malformed predicates refused; the explicit no-evidence form needs independent approval and its reason is in the approval audit event. A legacy empty mandate is suspended on upgrade (section 6). |
| RV-12 revised evidence | **FAIL** | A12 holds for a revised receipt in every respect: disclosure, both suppliers refused, acceptance by a non-supplier, accepter barred from final review, acceptance lapsing on a further change, referral never clearing. X12k fails for a replacement key (RA-03). |
| RV-13 statement assurance | PASS | A13: line identity, continuity and provenance are disclosed; missing line ids need an approved exception; a missing prior statement holds; a quarantined late revision does not replace the frozen one. RA-04 is a separate gap. |
| RV-14 alias visibility | PASS | A14: the rule record shows normalised aliases, the colliding rule id, status and effective end. |
| RV-15 evidence beyond own row | PASS | A08, X15: own-row evidence refused; every candidate needs a receipt; the supplier of a cited candidate receipt is barred from review. |
| RV-16 inventories | PASS | Both inventories and both patches list every changed runtime and test file, including the two web files. |
| RV-17 package chain | PASS | A17: the second package names the first, one governs, the first is byte-identical, and acknowledgement does not clear stale work. |

P3 findings, none blocking:

| ID | Finding | Probe |
| --- | --- | --- |
| RA-05 | A mandate is suspended as "policy changed" when new evidence falls after the date of a rule that was already approved. This is the old concern UC-1, now reproduced. It fails safe. | U1 |
| RA-06 | A disposition that cites the predecessor snapshots listed in the artifact is accepted but never takes effect. | X01 |
| RA-07 | A transaction row from an unrelated item counts as supporting evidence. | A14 |
| RA-08 | Two charges can each be excluded as a duplicate of the other, leaving no entry for either. Both stay visibly held. | X09 |

Earlier concerns: UC-2 and UC-3 are verified fixed (A13, A04, A12). UC-4 is observed and visible, not a defect (U4). UC-5 is unchanged.

## 6. Preservation, legacy data and surrounding controls

- **Legacy data.** I wrote a temporary database with the previously reviewed version, holding an approved mandate with empty freshness and an untyped checklist, then opened it with the corrected version. The mandate is suspended with an audit event and dispatches nothing. All earlier artifacts and evidence are byte-identical. The audit chain verifies. All five legacy checklist strings evaluate as unsatisfied.
- **Test methods.** All 40 from the initial archive, 41 from the Batch 1 baseline and 43 from the reviewed Batch 2 checkpoint are present. None has fewer assertions.
- **Maintained cases.** Two changes since the last review: the base profile checklist is typed, and mandates in the runner state the no-evidence reason. No expected outcome changed.
- **C-02 to C-06, role and grant enforcement, close concurrency, deferred boundaries.** Covered by my original probes RN01, RN03 to RN07, RT19b and the 21 deferred cases, all passing through the delivered gate, plus M1 for client isolation.

## 7. Teaching month and G0

I drove the month by both permitted routes with explicit authority, and recomputed the entry impact by hand.

| | Referral route (delivered walkthrough) | Acceptance route (adapted RG0) |
| --- | --- | --- |
| TX-009 receipt | One version, 79.99, unchanged | Corrected to 80.00 by a second preparer; held; disclosed; accepted by a non-supplier |
| Approvals | 10 | 11 |
| Held with referral | TX-007, TX-009, TX-011 | TX-007, TX-011 |
| Office supplies | +311.00 | +391.00 |
| Repairs | +200.00 | +200.00 |
| Card liability | −211.00 | −291.00 |
| Cash | −300.00 | −300.00 |
| Net | 0.00 | 0.00 |

Both match the claims. In both: every held item is refused approval, finalization needs an acknowledgement, two packages are finalized, November is locked, October TX-008 and its receipt are quarantined and named in the package, and the package states it is a preparation handover and not a close. A referral is not an approval and is not counted as one.

The caveat from my last review is gone. The delivered walkthrough no longer changes TX-009's receipt.

Second-client isolation holds: first-client artifacts, package bytes and evidence history are unchanged, four cross-client attempts are refused, and both audit chains verify.

| G0 criterion | Status |
| --- | --- |
| Batch 1 and Batch 2 complete | FAIL: one P1 under T-12 |
| All P0 and P1 defects fixed with tests | FAIL: RA-01 |
| Reviewer cases: none unexpected, all fail-until-fix fixed | PASS |
| Full month to approved or dispositioned, finalized, locked | PASS |
| Two clients, different periods, no cross-effects | PASS |
| Documentation matches code | PASS |

## 8. Decisions that need client authority

None of these is assumed in the code or in this review:

1. Whether the person who approves policy may also review items prepared under it.
2. Document policy, including who may accept a corrected or replaced receipt.
3. Which document is the authoritative card statement, whether it has line identifiers, and who may supply or correct it.
4. Treatment of fees, interest, card payments and transfers.
5. The close checklist and who gives final sign-off.
6. Whether a recurring run may ever be authorised with no new evidence outside demonstrations.

## 9. Next boundary

1. Fix RA-01. Fix RA-02, RA-03 and RA-04 in the same pass; RA-05 to RA-08 can go with them. Order and acceptance assertions are in `FABLE_RV_CORRECTIONS.json`.
2. Add `fable_rv_acceptance_probes.py` to `make test` unmodified. The pass is complete when it exits 0 and the four existing gates still pass.
3. Return the source. If that holds, the software side of G0 is met and the human G0 decision can be taken.

Batch 3 stays closed until then. AP, AR, full reconciliation, reporting, live connections, posting, payments, final close and deployment remain out of scope.
