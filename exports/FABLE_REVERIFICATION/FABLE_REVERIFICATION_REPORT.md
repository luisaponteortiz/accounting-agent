# Fable re-verification: C-01 to C-06 and Batch 2 (T-09 to T-19)

Independent review of `FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip`, 15 November 2026.
Review output only. It authorises no connection, posting, payment, model call, hosting, deployment or policy activation, and it opens no readiness gate. All data used is fictional.

Companion files: `FABLE_REVERIFICATION_RESULTS.json`, `FABLE_REVERIFICATION_CORRECTIONS.json`, `fable_reverification_probes.py`, `fable_reverification_output.txt`, and the raw logs in `evidence/`.

## 1. Decisions

| Subject | Decision | Basis |
| --- | --- | --- |
| Historical corrective checkpoint (frozen archive) | **PASS** | My original script, unmodified, on the frozen source: N01 to N07 all OK, every other required probe OK, exit 0. |
| C-01 to C-06 on current source | **FAIL (C-01 only)** | C-02, C-03, C-04, C-05 and C-06 hold. C-01 holds for the scenario I reported and fails its objective through a second route (RV-01). |
| Batch 2 (T-09 to T-19) | **FAIL, not yet accepted** | Six tickets meet their criteria. Five (T-09, T-12, T-15, T-18, T-19) each have a P1 defect. |
| G0 technical criteria | **FAIL, not yet met** | Four of six criteria are met. "All P0 and P1 defects fixed" and "Batch 2 complete" are not. |
| Human G0 acceptance, G1 to G4 | Not for this review | Human G0 acceptance should wait for the corrections below. Nothing here opens G1 to G4. |

Codex's reported numbers are accurate. I reproduced all of them: 111 tests passing, 41 original test methods retained, 60 cases at 29 PASS, 10 FIXED and 21 DEFERRED-OK, and the teaching month. The developer's gates pass because they do not test the eleven situations in which I found the controls give way.

I confirmed 17 defects: 6 at P1, 7 at P2 and 4 at P3. There is no P0. None is foundational, and none needs a design change. Each has a small, local correction, and each has a probe that fails today and will pass when it is fixed.

**Recommended next step:** one corrective pass (RV-01 to RV-13) on the current source, then re-verification. Batch 3 should not start before that.

## 2. What I ran

| Check | Result |
| --- | --- |
| Archive checksum and `REVIEW_MANIFEST.json` | Match. 152 of 152 files, none unlisted. |
| `python3 scripts/verify_corrective_checkpoint.py` | Exit 0. N01 to N07 OK. P07, P08, P12, P13, P15 and N17 deferred, and N08 and N09 weak, as expected at that checkpoint. |
| `make test` | Exit 0. 111 tests, no failure, no expected failure. |
| `make check` | Exit 0. |
| `make batch2-gate` and the three individual commands | Exit 0. Regenerated `final-validation.json` is byte-identical to the delivered one. |
| My own probes (`fable_reverification_probes.py`) | Exit 1. 35 probes: 21 held, 11 confirmed gaps, 3 notes. |
| Static checks on the change inventory, frozen inputs and retained tests | See section 7. |

Environment: Python 3.9.6, SQLite 3.51.0, macOS, no network. I kept one untouched extraction and one working copy. The developer's gates ran in the working copy. My probes ran against the untouched copy, and its manifest still verified afterwards.

Not run: a browser walkthrough of the demo UI. No accounting control depends on it. I read `http.py` and ran the delivered HTTP tests.

My probes use only service operations on temporary databases. They do not use the delivered helpers `prepare_profile`, `grant_fixture_authority` or `create_fixture_mandate`. Each probe proposes the profile as one person, approves it as another, and lists every grant. Each refusal is paired with a positive control, so a refusal is known to come from the control under test.

## 3. Corrective tickets on current source

| Ticket | Status | Evidence | Comment |
| --- | --- | --- | --- |
| C-01 locked-period move | **FAIL** | RN02 OK, RN02b WEAK | Re-dating is fixed, including replay, a recurring December run, release on reopen, and the receipt following its charge. Supersession under a new key reaches the same double approval (RV-01). |
| C-02 decisions under lock | PASS | RN01 | Approve, reject, revoke, resolve_approve and resolve_reject all return 409 PERIOD_LOCKED. So do dispositions and finalization. Reopen needs the lock grant and is audited. All decisions are accepted afterwards. |
| C-03 provenance outside content | PASS | RN03 | A colleague's identical run and a mandate run reuse the artifact. The rejection and the approval both survive. The colleague then cannot decide. |
| C-04 historical authorship | PASS | RN04, RN05 | Every version supplier stays barred. So do the author and approver of the chart and entity fields after a re-registration. Another item's receipt does not bar. One P2 residual for superseded rule versions (RV-10). |
| C-05 combining marks | PASS | RN06 | Thai, Devanagari and Hebrew pairs stay distinct. A different mark is held as unknown, an alias collision as ambiguous. Empty aliases are refused in profiles and rules. |
| C-06 actor kind | PASS | RN07 | No default. A service identity named like a human, with every grant issued to it, is refused for all eleven human operations. |

Two further defects found while testing C-01 affect locked periods: RV-03 and RV-04 in section 5.

### The maintained harness

`review/batch2_verification_probes.py` is a fair adaptation of my script. Its setup changes follow real contract changes, and its N01 to N07 assertions are the original ones. My independent versions agree with it on those seven.

It is not sufficient evidence on its own, for three reasons:

- Every mandate it creates goes through `create_fixture_mandate`, which supplies an empty freshness predicate. The harness therefore never tests the freshness control (RV-11).
- Profile approval happens inside a helper, with a fixed second actor. No maintained probe tests a withdrawn mapping, a superseded rule author or an untyped checklist.
- N18 is reported as a NOTE. That label is not evidence that an approver can see the normalised alias. The form is recorded only in an audit event (RV-14).

## 4. Batch 2 by ticket

Per-criterion results, 66 in total, are in `FABLE_REVERIFICATION_RESULTS.json`.

| Ticket | Status | What holds | What does not |
| --- | --- | --- | --- |
| T-09 policy lifecycle | **FAIL** | Proposed profiles and rules are inert. Proposer, ungranted human and service cannot approve. Effective dates and supersession follow the item date. A December rule and an unrelated close rule leave a November approval intact. Review policy uses the item date. No HTTP route reaches a grant or a policy approval. | A mapping withdrawn in a newly approved profile still applies (RV-05, P1). Rule author washing (RV-10, P2). Normalised alias not shown on the rule (RV-14, P3). |
| T-11 required facts | PASS | A client-sample profile with missing facts yields no eligible card or journal item. Demo waivers appear on the artifact and in the export. | |
| T-12 source lifecycle | **FAIL** | Older, conflicting, mixed-order and unordered deliveries never replace an ordered head. Replays change nothing. Evidence received before a period opens is adopted. A receipt follows its charge across a month boundary in either arrival order. | A removed source leaves a stale governing item (RV-03, P1). Later intake disturbs locked periods (RV-04, P1). Supersession of an approved source raises no event (RV-01). |
| T-10 mandates | PASS | Issuer cannot approve. An unapproved mandate dispatches nothing. A fixed period rule is honoured. With a stated requirement, an occurrence waits for fresh evidence and is woken by intake. A bound policy change suspends the mandate. | An empty freshness predicate is accepted (RV-11, P2). |
| T-13 statement control | PASS | A line swap with the same count and total is caught when line ids are supplied. Purchases and payments overstated by the same amount are caught. An opening-balance break blocks the account. A foreign row is listed as unreconciled. | No disclosure when line ids, the prior statement or independent provenance are absent (RV-13, P2). |
| T-14 dispositions | PASS | Closed vocabulary. Exact split only. Evidence required. A referral never clears its blocker. A rule proposed through a disposition stays inert. The dispositioner cannot review the item. Revocation re-blocks. An empty inventory blocks dependants. | Three P2 gaps in how a decision is bound to its facts (RV-07, RV-08, RV-09) and one P3 (RV-15). |
| T-15 proposed entry | **FAIL** | One entry per approved card item, traceable to its snapshot and marked not posted. Entry impact is reproducible. A journal citing a card source is held on both sides. | The hold disappears when the cited source gets any later version, and both are then approved (RV-02, P1). |
| T-16 journal controls | PASS | Tested one at a time: wrong-type support, support bound to another journal, support with no binding, duplicates with different memo and line order, no net effect, and dimension variants. Three separate unit tests exist. | |
| T-17 receipt policy | PASS | Unset policy gives named unset codes. A proposed rule changes nothing. With an approved one-day window and five-cent tolerance: one day matches, two days does not; five cents matches, six does not. | No way to carry or resolve a receipt exception without altering evidence (RV-12, P2). |
| T-18 finalization | **FAIL** | Preparer, same person in another role, and ungranted reviewer are refused. Carried items need an acknowledgement. Stale or disputed items block even with one. Package bytes are stable. A real source revision raises a visible event. A mistaken revoke can be recovered. | A false change event on locked periods (RV-04). A period with a removed source cannot be finalized (RV-03). Packages are not linked (RV-17, P3). |
| T-19 close readiness | **FAIL** | Typed requirements work: a label does not satisfy a typed reconciliation or tie-out. Unreviewed, held and quarantined work is reported. A queued close run waits for preparation, refreshes review status only, and is held if a close input changes. Final sign-off and external-step holds always remain. | The shipped checklist is untyped, so labels satisfy the reconciliation and tie-out lines (RV-06, P1). |

Batch 2 completion gate:

| Gate line | Status |
| --- | --- |
| Every fail-until-fix case reports FIXED | PASS, 10 of 10 |
| Full synthetic month driven to approved or dispositioned, finalized, locked | PASS, with the caveat in section 6 |
| Two synthetic clients in different periods with no cross-effects | PASS |
| G0 met and recorded | FAIL. `CONNECTION_READINESS.md` correctly shows human G0 acceptance as still open. |

## 5. Confirmed defects

Full detail for each is in `FABLE_REVERIFICATION_CORRECTIONS.json`: source lines, minimal reproduction, expected and actual behaviour, correction, acceptance assertions and regression tests.

### P1: fix before G0

**RV-01. A charge approved in a locked period can be approved again in another period through supersession.** (C-01, T-12; probe RN02b)
November item A1 is approved and locked. A new key A1X dated December arrives with `supersedes` pointing at A1. A1X enters December with no blocker and is approved. A1 stays approved in November. No event or source exception is recorded, and the head of A1 is marked removed inside the locked period. The system is told the two rows are the same charge and does nothing with that. Effect: the same expense and liability are proposed in two periods.

**RV-02. The double-recording hold disappears when the cited source is revised.** (T-15; probe RT15)
A journal cites card item A1, and both are correctly held. A1 then receives a new version that differs only in spacing. Ownership is matched on the snapshot id of the current version, so the journal's reference no longer matches anything. Both items lose the blocker and both are approved. Effect: a 40.00 expense is proposed twice after a routine feed revision.

**RV-03. An item whose source has left the period blocks finalization permanently.** (T-12, T-18, T-19; probes RT12d, RN02)
A pending authorisation is removed by the feed. Its old artifact is still reported as the governing item, with status stale and its old blockers. Finalization returns "Stale/disputed items cannot be finalized", and no service operation clears it. The same residue is left in the origin period when a moved source is released. The failure is in the safe direction, but any month with a removal, void, supersession or move can never be finalized.

**RV-04. Later intake disturbs every locked period.** (T-12, T-18; probe RT12b)
November is approved, finalized and locked. A December-only packet arrives. Both unchanged November receipts are then listed as LATE_ACTIVITY_IN_LOCKED_PERIOD, and POST_FINALIZATION_CHANGE is raised against the November package. Approvals and package bytes are intact. Cause: intake re-binds every receipt, and a binding into a locked period is always recorded as late. Effect: after the first intake of the next month, the quarantine list and the change-event trail for locked periods cannot be trusted.

**RV-05. A vendor mapping withdrawn from the approved profile keeps producing clean matches.** (T-09; probe RT09c)
Profile version 2 drops the Metro vendor and is approved. A Metro charge is still eligible with that vendor and category, while the profile shown in state lists only the other vendor. Cause: rules are created per vendor and nothing ends a rule whose vendor is no longer in the profile.

**RV-06. Under the shipped checklist, a document label satisfies the reconciliation and tie-out lines.** (T-19; probe RT19a)
The demo checklist is five plain strings. Five documents carrying only a label make all five lines report satisfied, including the bank reconciliation and the AP and AR tie-outs. The typed form of the same lines is correctly unsatisfied. The typed control exists; the delivered configuration does not use it, and untyped entries are still accepted. This is original finding F-11 surviving in the default setup.

### P2: fix in the same pass

| ID | Defect | Probe |
| --- | --- | --- |
| RV-07 | Disposition choices are not tied to the activity or account type. A card payment can be dispositioned as a standalone credit and approved as Dr card liability 300.00, Cr office supplies 300.00. | RT14e |
| RV-08 | A distinct-purchases decision about two charges stays in force when a third identical charge arrives. | RT14b |
| RV-09 | After one charge is excluded as a duplicate, the surviving charge stays held, and the only way to clear it is a false distinct-purchases statement. | RT14c |
| RV-10 | The author of a vendor mapping can review items it codes after a colleague re-proposes the rule with a cosmetic change. | RN05b |
| RV-11 | A mandate is accepted with an empty freshness predicate and then runs every slot on unchanged evidence. | RT10b |
| RV-12 | A receipt mismatch can only be cleared by re-supplying the receipt, and the reviewer is not told the evidence was revised. | RG0 |
| RV-13 | The statement workpaper does not say when line identity, opening continuity or independent provenance could not be checked. A substituted line then passes with no blocker. | RT13n |

### P3

| ID | Defect |
| --- | --- |
| RV-14 | The normalised alias is recorded in the audit event only, not on the rule the approver reads. Collisions are held after approval, which is safe. |
| RV-15 | A disposition may cite only the item's own source row as evidence. |
| RV-16 | `changed-files.json` and the patch omit `web/app.js` and `web/index.html`, both of which changed. The script inventories only `.py` and `.json`. |
| RV-17 | Several packages can be finalized for one period and workflow with no link between them. |

### Implementation order

RV-04, RV-03, RV-01, RV-02, RV-05, RV-06, then RV-07 to RV-13, then RV-14 to RV-17.
RV-04 comes first because it disturbs every multi-period test. RV-03 precedes RV-01 because the supersession fix needs a defined state for items that leave a period.

Completion gate for the pass: `python3 fable_reverification_probes.py <project-root>` exits 0, the existing gates still pass, and the probe file is added to `make test` unmodified.

## 6. Full month and G0

I drove the teaching month myself with explicit authority and five distinct people: preparer, policy approver, dispositioner, reviewer and finalizer, plus a period administrator.

| Check | Result |
| --- | --- |
| Approvals | 11: nine card items and two journals. Matches the claim. |
| Held items | TX-007 (pending) and TX-011 (foreign currency) each carry an external-referral disposition and remain blocked. Neither is ever eligible. |
| TX-008 | Quarantined in unconfigured October with its receipt. Both appear in the package's quarantined list. |
| Lineage | Reviewer and finalizer are outside the contributor list of every item. A dispositioner is barred from reviewing an item they decided (probe RT14a). |
| Entry impact, recomputed by hand | Office supplies +391.00, repairs +200.00, card liability −291.00, cash −300.00. Net zero. Matches. |
| Finalization and lock | Refused without acknowledgement. Two packages finalized. November locked. |
| Second client, December | Journal prepared and approved. First client's artifacts, package bytes and evidence history unchanged. Cross-client review and intake refused. Both audit chains verify. |

My judgment on the three treatments the prompt asked about:

- **TX-007 and TX-011** meet the criterion. A recorded referral that leaves the blocker in place is a disposition, and the package carries both items by name.
- **TX-008** meets the criterion. It is outside the period and is disclosed in the package content, not only in free text.
- **TX-009 does not meet it cleanly.** The receipt says 79.99 against a charge of 80.00. There is no disposition for a receipt exception, so the walkthrough has the preparer re-supply the receipt at 80.00. No blocker was weakened, but the evidence was changed to fit, and the approved artifact shows only a version number. That is RV-12. J-002 was also corrected by the preparer, which is ordinary: a journal is the preparer's own proposal.

G0 criteria:

| Criterion | Status |
| --- | --- |
| Batch 1 and Batch 2 complete | FAIL |
| All P0 and P1 defects fixed with tests | FAIL: RV-01 to RV-06 |
| Reviewer cases: none unexpected, all fail-until-fix fixed | PASS |
| Full month to approved or dispositioned, finalized, locked | PASS, with the TX-009 caveat |
| Two clients, different periods, no cross-effects | PASS |
| Documentation matches code | FAIL, minor: RV-16, and the typed close-evidence description against the untyped shipped checklist |

## 7. Evidence integrity and adaptations

- **Change inventory.** All 46 listed hashes are correct. Two changed files are missing from both the inventory and the patch (RV-16).
- **Verification inputs.** My four files are byte-identical in the outer bundle, in the frozen archive and against my originals.
- **Frozen archive.** It contains none of the Batch 2 modules. That is consistent with the claim that C-01 to C-06 passed before Batch 2 began. File times agree. An archive cannot prove the order of work.
- **Original tests.** All 41 platform and HTTP method names of the Batch 1 baseline (32 and 9) are present. Against the first 0.1.0 bundle, all 40 platform and HTTP methods are present, 14 bodies changed, and none has fewer assertions than the original. No expected-failure marker remains.
- **Test corrections I asked for.** Done: `test_P15` now asserts behaviour, `test_P08` is three tests, the Batch 1 gate is replaced, and the period contracts are stated in FV-J05 and FV-J07.

Changes to the 60 cases, each of which I accept:

| Case | Change | Judgment |
| --- | --- | --- |
| FV-C13 | Superseded pending row is in history, not in the open population | Requested by T-12 |
| FV-C17, FV-C18 | Policy-unset codes | Requested by T-17; items still held |
| FV-J05, FV-J07 | Quarantine and lock-dispatch contracts stated | Outcome unchanged: no eligible entry |
| FV-CL04 | Now executable; adds disclosure of the quarantined document | Stronger than before |
| Statement adapter | Converts my count-and-total controls into structured statements | Acceptable. It runs only in the test runner and fixture builder, never in intake. It preserves a wrong declared count or total. It takes line ids from the intake population, so the 60 cases cannot detect a line-identity defect. My probes RT13 and RT13n cover that. |

The 21 deferred cases are all still refused with 403.

## 8. Limits and open questions

Not verified by execution, listed in the corrections file as UC-1 to UC-5: possible false suspension of a mandate when evidence dated after a mid-period rule arrives; use of a quarantined prior statement for continuity; no event when a receipt of an approved item is revised; no restore when a superseding source is removed; no revocation of synthetic grants.

One observation that is not a defect: each item's envelope carries the run-wide fingerprint and rule list. A same-period rule that affects one item therefore sends every item of that workflow back for review. That is conservative and can be narrowed later.

Decisions that need client authority before real samples, none of which I have assumed:

1. Whether the person who approves policy may also review items prepared under it. The code bars them, following my earlier specification. A small client may not have a third person.
2. Document policy: date window, amount tolerance, multiple receipts, and who may accept a corrected receipt.
3. Which document is the authoritative card statement, whether it has line identifiers, and how cycles map to periods.
4. Treatment of fees, interest, card payments and transfers, and the accounts each disposition may use.
5. The close checklist, the evidence each line requires, and who gives final sign-off.
6. Who may disposition, finalize and lock, and what evidence must be new before a recurring run.

## 9. Recommendation

1. Do not start Batch 3 and do not record G0.
2. Implement RV-01 to RV-06, then RV-07 to RV-13, in the order given. RV-14 to RV-17 can go in the same pass.
3. Add `fable_reverification_probes.py` to `make test` unmodified. If an API change makes a probe unrunnable, return the change and the adapted probe for review.
4. Return the source for re-verification. If the probe file exits 0 and the existing gates still pass, the software side of G0 is met and the human G0 decision can be taken.

Scope stays as it is: AP, AR, full reconciliation, reporting, live connections, posting, payments and deployment remain out.
