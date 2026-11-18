# Accounting Agent OS — independent verification of Batch 1

Reviewer: Claude Fable. Date: November 14, 2026.
Subject: `exports/FABLE_BATCH_1_REVIEW_BUNDLE/` (release `0.1.0-batch1`, 80 files).
Companion files: `FABLE_BATCH_1_1_CORRECTIONS.json`, `batch1_verification_probes.py`, `batch1_probe_output.txt`.

This is a verification of the Batch 1 corrections only. It authorises nothing beyond synthetic, local work. All data in the probes is fictional.

---

## 1. Verdict

**Codex's report is accurate, and Batch 1 did what the tickets asked.** Every count reproduces, every written acceptance criterion is met, and every failure scenario from my original review is fixed.

**The controls are not yet dependable.** New adversarial probes defeated four of the nine Batch 1 controls by routes the tickets did not cover. Two of those are serious: a transaction re-dated after a period lock can be approved in two periods, and approvals can still be revoked or granted inside a locked period. Six of the nine new weaknesses trace to gaps in my own ticket specifications, not to Codex's implementation.

**Recommendation: Batch 2 may proceed, on one condition.** Open it with six small corrective tickets (C-01 to C-06 in §6). They are contained changes with a probe that flips for each. Nothing found is foundational, so no further architecture review is needed.

---

## 2. What I ran

All on Python 3.9.6 / SQLite 3.51.0, against a copy of the bundle, with no network, model or ledger access.

| Check | Result |
| --- | --- |
| SHA-256 of all 79 files in `FABLE_BATCH_1_MANIFEST.json` | 79 of 79 match |
| `python3 -m unittest discover -s tests` | 72 run: 67 pass, 5 expected failures, 0 unexpected. Matches the report |
| `python3 scripts/check.py` | Passed |
| Maintained runner with `--batch1-gate` | PASS=28, FIXED=6, KNOWN-FAIL=4, DEFERRED-OK=22; gate PASS. Matches the report |
| Maintained probe suite (`review/reviewer_probes.py`) | 24 run: 19 pass, 5 expected failures |
| My original, unmodified probe script | 10 of 16 probes ran to completion; 6 stopped on intended contract changes (periods as records, run links, decision rules). See §3 note |
| All 16 original probes, adapted only for the period API | 11 OK, 5 unchanged and deferred to Batch 2 |
| 18 new adversarial probes | 9 found a weakness, 3 held, 5 recorded as notes, 1 deferred |
| Diff of the 41 original test methods | All 41 present. Changes are limited to 12 lines, all documented in `DECISIONS.md` |

Not verified: the browser walkthrough and its two screenshots. I did not start the server.

To reproduce everything in this report from the project root:

```bash
python3 exports/FABLE_BATCH_1_VERIFICATION/batch1_verification_probes.py .
```

(The path assumes the files are copied to that folder. The script takes the project root as its only argument. It ends with a corrective-gate line and exits non-zero while any of N01 to N07 is still WEAK, so today it reports `FAIL N01, N02, N03, N04, N05, N06, N07`.)

---

## 3. PASS or FAIL for each Batch 1 finding

**PASS** means the original defect is fixed and I could not defeat the control with new tests. **FAIL** means the control can still be defeated; evidence is in §4. "Original defect" is judged by my first-round probes and cases.

| Finding | Ticket | Original defect | Ticket criteria | Verdict | Why |
| --- | --- | --- | --- | --- | --- |
| F-01 Review independence | T-03 | Fixed (P01, P02, FV-R01) | Met | **FAIL** | An author regains review rights when a colleague makes a trivial revision (V-04, V-05). An actor created without a kind is treated as human (V-07) |
| F-02 One governing version, decision rules | T-07 | Fixed (P05, P14, FV-R03) | Met | **FAIL** | A rejection is displaced when the same content is re-prepared under another actor, and the copy can be approved (V-03) |
| F-03 Vendor normalisation | T-02 | Fixed (P06, FV-C15) | Met | **FAIL** | Scripts with combining vowel marks still collapse different words into one alias (V-06) |
| F-04 Periods and locks | T-05 | Fixed (P09, P10, FV-R04) | Met | **FAIL** | A re-dated source is approvable in two periods (V-01). Decisions are accepted in a locked period (V-02). Two evidence-binding defects (V-08, V-09) |
| F-05 Scoped invalidation (parts 1 and 2) | T-06 | Fixed (P11, P16) | Met | **PASS** | Verified with real file edits: `http.py`, `__main__.py`, `demo.py`, `service.py`, `storage.py` keep approvals; `modules.py` and `core.py` stale them |
| F-08 Occurrence lost when held | T-04 | Fixed (P03, FV-RC01) | Met | **PASS** | Held occurrences re-dispatch; skips are recorded; one completed run per occurrence holds under concurrency (N11, N12) |
| F-17 Unfit mandate stops all ticks | T-04 | Fixed (P04, FV-RC02) | Met | **PASS** | The unfit mandate is held with a reason; the other dispatches |
| F-21 Test suite | T-01 | Fixed | Met | **PASS** | Exact blocker sets; reviewer suite in `make test`. Four test-quality notes in §7 |
| F-22 Documentation | T-08 | Fixed | Met | **PASS** | Statements match the code. One overstatement: "protected reviews" under lock (see V-02) |

Five PASS, four FAIL. In all four FAIL rows the scenario I originally reported is fixed; the failure is a different route to the same control objective.

Note on my original probe script: run unmodified, probe P02 reports `automation-agent-7 -> approval accepted`. That is not a regression of the prefix check. The script builds the actor without a kind, and the new default is `human`. It is the evidence for V-07.

---

## 4. New defects

Priorities as before: **P0** current critical control or correctness defect; **P1** needed before execution expands or client samples are used; **P2** next reliability improvement. Each has a probe in `batch1_verification_probes.py`; the quoted lines are from `batch1_probe_output.txt`.

### V-01 — A source re-dated out of a locked period is approvable in both periods · P0

- **Where:** `service.py:168-180` (`bind_source` assigns each new version by its own date and looks only at the destination period); `service.py:182-189` (a locked period keeps its frozen view of the earlier version).
- **Reproduce (probe N02):** Approve TX-001 in November. Lock November. Open December. Intake a revision of TX-001 dated December 1 with its receipt and a December statement control. Prepare December.
- **Observed:**
  `November TX-001: approve amount 42.50 date 2026-11-03`
  `December TX-001: blockers [] | approval accepted | date 2026-12-01`
  `exceptions raised against November for the moved source: []`
- **Consequence:** One source transaction is approved and current in two periods with no exception raised anywhere. This is the ordinary case of a card feed revising a posting date after month end. In release 0.1.0 it could not happen, because any change staled everything; the period model introduced it.
- **Origin:** Sequencing gap in my plan. The "revision of an approved source raises an exception" rule was in Batch 2 ticket T-12, but Batch 1 periods made the gap reachable.
- **Fix:** C-01.

### V-02 — Review decisions are accepted in a locked period · P1

- **Where:** `service.py:465-499` (`review` never checks period status; frozen runs count as current at `303-305`).
- **Reproduce (probe N01):** Approve J-001. Lock November. A second reviewer revokes J-001; the first reviewer approves the still-pending TX-001.
- **Observed:** `under lock: {'approve pending TX-001': 'accepted', 'revoke approved J-001': 'accepted'} | J-001 now: revoke | TX-001 now: approve`
- **Consequence:** The lock stops new preparation and new evidence, and leaves the review state fully editable. An approval the lock was meant to protect can be withdrawn without reopening the period.
- **Origin:** Gap in my T-05 specification, which said only that locking is a status change.
- **Fix:** C-02.

### V-03 — A rejection is displaced by identical re-preparation under another actor · P1

- **Where:** `service.py:390-401`. The artifact hash includes `contributors`, so the same accounting content prepared by a run with a different enqueuer or mandate issuer is a new artifact. It becomes governing with no decisions.
- **Reproduce (probe N03):** Reviewer rejects J-001. A colleague issues a mandate and delivers one occurrence. A second reviewer approves the resulting copy.
- **Observed:**
  `new artifact created: True | identical accounting data: True | approval of the copy: accepted`
  `J-001 artifacts (id, governing, status, decisions): [(22, True, 'approve', ['approve']), (15, False, 'stale', ['reject'])]`
- **Consequence:** The item reads as approved. The rejection of byte-identical accounting data sits on a non-governing artifact marked stale, and no dispute was raised. The same mechanism silently resets an approval to pending when another actor triggers a recurring run.
- **Origin:** Conflict between two of my tickets. T-03 asked for contributors inside the hashed envelope; T-07 asked for identical inputs to give an identical hash. Both cannot hold when the enqueuer differs.
- **Fix:** C-03.

### V-04 — The author of an entry regains review rights after a colleague's trivial revision · P1

- **Where:** `service.py:373-374`. Contributors are the suppliers of the latest version of each source only.
- **Reproduce (probe N04):** `human-a` supplies journal J-900. `human-b` re-supplies it with a full stop added to the memo and enqueues. `human-a`, as reviewer, approves.
- **Observed:** `contributors on artifact: ['human-b', 'worker-demo'] | human-a approving own entry: accepted`
- **Consequence:** The same two-person pattern as the original F-01, by a different route. It does not need collusion: a colleague fixing a typo is enough.
- **Origin:** Gap in my T-03 specification ("the actor of every source snapshot in the run's input manifest").
- **Fix:** C-04.

### V-05 — The author of the mapping rules regains review rights after a colleague re-registers the profile · P1

- **Where:** `service.py:373` (`profile_ref["actor"]` is the registrant of the latest profile version only).
- **Reproduce (probe N05):** `human-a` registers the profile with its vendor mappings. `human-b` registers version 2 changing only the notice text, then intakes and enqueues. `human-a` approves an item coded by `human-a`'s mapping.
- **Observed:** `contributors: ['human-b', 'worker-demo'] | human-a approving item coded by own mapping: accepted`
- **Consequence:** The implementation's own rule (the profile registrant is a contributor) holds or lapses depending on who last touched the profile.
- **Origin:** Gap in my T-03 specification ("the actor who registered the profile version in force").
- **Fix:** Interim in C-04. The full answer is rule-level proposer and approver in Batch 2 ticket T-09.

### V-06 — Different words in combining-mark scripts collapse to one alias · P0 (narrow trigger)

- **Where:** `core.py:62-63`. Characters are kept only when `str.isalnum()` is true. Combining vowel signs and points are not alphanumeric and are dropped.
- **Reproduce (probe N06):**
  `Thai 'กิน' vs 'กัน' -> 'ก น' vs 'ก น' equal=True`
  `Devanagari 'किताब' vs 'कुताब' -> 'क त ब' vs 'क त ब' equal=True`
  `end to end: vendor {'id': 'demo_thai', ...} | category DEMO_OFFICE_SUPPLIES | eligible True | blockers []`
- **Consequence:** The same class as F-03: a clean, approvable proposal for the wrong vendor. It affects Thai, Devanagari and other Indic scripts, and pointed Hebrew or Arabic. It does not affect English or Spanish names.
- **Origin:** My T-02 specification named `str.isalnum()`. Codex implemented it exactly.
- **Fix:** C-05.

### V-07 — An actor created without a kind is treated as human · P1

- **Where:** `core.py:78` (`kind: str = "human"`).
- **Reproduce (probe N07):** `default kind: human | review by actor with no kind supplied: accepted`
- **Consequence:** The human-versus-service control fails open. Any transport or script that omits the field produces a human. My own runner does this for its worker.
- **Origin:** Implementation choice.
- **Fix:** C-06.

### V-08 — Supporting evidence is assigned to a period by its own date · P1

- **Where:** `service.py:169-170` (a receipt is bound by the receipt's date, independently of the transaction it supports).
- **Reproduce (probe N09):** A charge posts November 1; its receipt is dated October 31.
- **Observed:** `TX-001 blockers: ['MISSING_RECEIPT'] | receipt status: [('receipt-TX-001', 'UNASSIGNED_ACCOUNTING_PERIOD')] | evidence listed on artifact: ['demo_card_001:TX-001', 'demo-card-control']`
- **Consequence:** It fails closed, so nothing wrong is approved. But the reviewer is told the receipt is missing when it was supplied, and the artifact does not show it. This will occur at every month boundary.
- **Origin:** Implementation choice within an underspecified ticket.
- **Fix:** Add to Batch 2 ticket T-12 (§8).

### V-09 — Evidence received before its period is opened stays quarantined · P2

- **Where:** `service.py:126-129` (opening a period adopts only sources that carry a `date`); `storage.py:202-203` (re-supplying identical content creates no new version, so nothing is re-bound).
- **Reproduce (probe N08):** Intake the teaching packet, then open November, then re-supply the same packet.
- **Observed:** `still quarantined after the period opened: ['demo-card-control', ..., 'journal-support-001', 'trial-balance-placeholder']`, with `J-001 blockers: ['MISSING_JOURNAL_SUPPORT']` and `TX-001 blockers: ['STATEMENT_CONTROL_MISSING_OR_AMBIGUOUS']`.
- **Consequence:** Fails closed and is visible in `source_exceptions`. The only recovery is to change the content of the statement control or document.
- **Fix:** Add to Batch 2 ticket T-12 (§8).

### Notes, not defects

| Probe | Behaviour | Where it belongs |
| --- | --- | --- |
| N10 | A period can be locked with 12 governing items unreviewed, blocked or stale. Stale items in a locked period stay stale until reopen | Lock preconditions in T-18 |
| N14 | A person who supplies one receipt is barred from reviewing every item in that workflow and period. With two people this will block review quickly | Item-level lineage in T-14 |
| N15 | A revoked approval cannot be re-approved, and re-preparing unchanged inputs returns the same artifact. An overruled reviewer can re-open a resolved dispute, which then needs a fourth reviewer | T-07 follow-up in Batch 2 |
| N16 | A policy change that is later reverted restores the earlier approval without review. Defensible, since the approval binds exact inputs | Record in `DECISIONS.md` |
| N17 | Adding a December vendor rule stales approved November items if November is open, and after any reopen. Known and deferred (F-06 effective dating) | T-09 |
| N18 | Punctuation is discarded, so `A+ CLEANERS` equals `A CLEANERS` and `#1 PIZZA` equals `1 PIZZA` | Show the normalised form when an alias is approved (T-09) |

---

## 5. The five focus questions

1. **Independent review and separation of duties.** Enforced for the direct cases: the enqueuer, the worker, the mandate issuer, the current supplier of each input and the current profile registrant cannot review. Not yet dependable: authorship is tracked for the latest version only (V-04, V-05), and the human check fails open (V-07).
2. **Conflicting artifacts and approvals.** Prevented at any one moment: one governing artifact per item, repeats refused, contrary decisions become a dispute needing a third reviewer, and this holds under concurrency (N12). Not prevented over time: a rejection can be replaced by an approval of identical content (V-03).
3. **Periods, locks and historical approvals.** Opening a second period, locking, late evidence, lock-then-reopen and routing by date all behave correctly. Two gaps: a moved source is approvable twice (V-01), and the lock does not freeze decisions (V-02). Effective dating of policy is still missing, as planned (N17).
4. **Vendor matching.** The reported collapse is fixed, accents are preserved, and empty aliases are refused. A wrong, clean match is still possible for combining-mark scripts (V-06).
5. **Recurring execution, idempotency and invalidation.** Reliable in everything I tried: held occurrences recover, skips are recorded, an unfit mandate is isolated, a period boundary is handled, four concurrent ticks and drains produce one completed run per occurrence, and evidence, policy and source changes invalidate exactly the affected workflow and period (N11, N12, N13).

---

## 6. Required corrections before the rest of Batch 2

Six tickets. Detail, acceptance criteria and tests are in `FABLE_BATCH_1_1_CORRECTIONS.json`.

| Ticket | Fixes | Change | Probe that must flip |
| --- | --- | --- | --- |
| C-01 | V-01 | A new version of a source whose earlier version is admitted in a locked period is quarantined (`SOURCE_MOVED_FROM_LOCKED_PERIOD`) and enters no population until that period is reopened | N02 |
| C-02 | V-02 | `review` refuses every decision type while the artifact's period is locked | N01 |
| C-03 | V-03 | Record contributors outside the content hash, append-only, and take the union across linked runs. Identical inputs then reuse the artifact whoever enqueues | N03 |
| C-04 | V-04, V-05 | Contributors include the supplier of every version of each source in the manifest and the registrant of every profile version | N04, N05 |
| C-05 | V-06 | Keep Unicode letters, numbers and marks (categories L, N, M) when normalising | N06 |
| C-06 | V-07 | `Actor.kind` has no default; every call site sets it | N07 |

Order: C-05 and C-06 first (smallest), then C-02, C-04, C-03, C-01.

Do not start T-12 (source lifecycle), T-14 (dispositions) or T-18 (finalization) until C-01, C-02 and C-03 are in. Those three tickets build directly on source-period binding, lock semantics and artifact identity.

---

## 7. The 67 / 5 / 4 classification

Codex's classification is correct. None of the nine failing checks is a Batch 1 regression; each belongs to a Batch 2 finding.

The two sets overlap. They are not five plus four separate defects:

| Expected-failure test | Why it fails today | Finding | Matching known-fail case |
| --- | --- | --- | --- |
| `test_P07` | A late older batch becomes current (42.50 replaces 45.00) | F-13 | None |
| `test_P08` | A journal supported only by a trial-balance document is eligible | F-15 | FV-J10 |
| `test_P12` | Close readiness lacks `OPEN_PREPARATION_EXCEPTIONS` | F-11 | FV-CL02 |
| `test_P13` | Population substitution leaves TX-001 eligible | F-12 | None |
| `test_P15` | The profile rejects an unknown policy key | F-16 | None |
| (no unit test) | Duplicate journals are eligible | F-15 | FV-J08 |
| (no unit test) | A no-effect journal is eligible | F-15 | FV-J09 |

So there are seven distinct failing checks across five findings (F-11, F-12, F-13, F-15, F-16). Two unit tests overlap with two cases; three unit tests have no case; two cases have no unit test.

Four things to correct in the tests as Batch 2 opens:

1. **`test_P15` tests the wrong thing.** It fails only because the profile schema rejects a key named `receipt_date_tolerance_days`. It will pass as soon as that key is accepted, whatever the matching does, and the key conflicts with the rule-record design in T-17.
2. **`test_P08` covers one of the three defects in its name.** It asserts unbound support only. Split it into three tests.
3. **The Batch 1 gate is wired into `make test`.** `tests/test_reviewer_cases.py` passes `--batch1-gate`, which requires the four cases to remain KNOWN-FAIL. The first Batch 2 fix will therefore fail the suite. Replace it with a Batch 2 gate.
4. **Two of the 28 PASS results use a changed contract.** FV-J05 and FV-J07 pass through runner special cases keyed on the blocker name. I accept both contract changes (quarantine of a journal dated in an unopened period; refusal to dispatch in a locked period). The case file should state them, and the special cases should go.

One further observation: `exports/FABLE_REVIEW_RESPONSE/run_fable_validation_cases.py` and `reviewer_probes.py` in the project were replaced with short forwarders. This is recorded in `DECISIONS.md`, and my originals are preserved unchanged in `review/original/`.

---

## 8. Additions to Batch 2 acceptance criteria

| Ticket | Add |
| --- | --- |
| T-09 Policy lifecycle | Independence uses the proposer and approver of each rule applied to the item, replacing the interim in C-04 (probe N05 stays refused). A rule effective in a later period leaves approvals in earlier periods intact, whether those periods are open or reopened (probe N17 flips). Alias approval shows the normalised form (N18) |
| T-10 Mandates | Each occurrence prepares the period named by the mandate's period rule. Today a December occurrence prepares December by calendar date even when November has new evidence |
| T-12 Source lifecycle | Supporting evidence is assigned to the period of the item it references, and is listed on the artifact even when it does not match (probe N09 flips). Opening a period adopts every quarantined source that belongs to it, including statement controls and undated documents, and re-supplying identical content re-evaluates a quarantined binding (probe N08 flips). Quarantined sources appear in the period status passed to close readiness |
| T-14 Dispositions | Contributors are computed per item lineage, so supplying one receipt bars review of that item only (probe N14 flips), while every version supplier of that item's inputs remains barred (probe N04 stays refused) |
| T-16 Journal controls | Three separate unit tests for unbound support, duplicate journal and no-effect journal |
| T-17 Receipt policy | `test_P15` rewritten to assert matching behaviour under an approved rule and under an unset rule |
| T-18 Finalization | Locking or finalizing is refused, or needs a recorded acknowledgement, while any governing item is stale, disputed or unreviewed (probe N10). An invariant test: no source key has a current governing artifact in more than one period |
| T-07 follow-up | A defined recovery path for a mistaken revoke, and a bound on re-opening a resolved dispute (probe N15) |
| Test gate | Replace `--batch1-gate` with a Batch 2 gate requiring all ten original fail-until-fix cases FIXED. Add `batch1_verification_probes.py` to `make test` with every WEAK verdict treated as a failure |

---

## 9. Recommendation

**Proceed with Batch 2, starting with C-01 to C-06.**

- The Batch 1 work is sound and honestly reported. I found no regression and no misclassification.
- The remaining weaknesses are specific and small. None requires a redesign, and none calls for another broad review.
- When C-01 to C-06 are done, send me the bundle or the diff. Verification is one command: every probe N01 to N07 must report OK, and the earlier results must be unchanged.
