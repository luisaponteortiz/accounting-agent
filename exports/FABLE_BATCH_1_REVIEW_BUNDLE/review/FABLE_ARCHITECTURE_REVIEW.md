# Accounting Agent OS 0.1.0 — architecture and control review

Reviewer: Claude Fable, acting as independent accounting-systems reviewer. Date: November 14, 2026.
Subject: `FABLE_ACCOUNTING_REVIEW_BUNDLE.zip` (release 0.1.0, 39 files).
Companion files: `FABLE_IMPLEMENTATION_BACKLOG.json`, `FABLE_VALIDATION_CASES.json`, `run_fable_validation_cases.py`, `reviewer_probes.py`.

This is a review packet. It authorises nothing: no connection, posting, payment, model call, hosting or policy activation. Every example account, vendor, amount and policy in this packet is fictional.

---

## 1. What was inspected, executed and left unverified

**Inspected (read in full):** `FABLE_ACCOUNTING_HANDOFF.md`, `FABLE_REVIEW_PROMPT.md`, root `AGENTS.md`, `README.md`, `DECISIONS.md`, `PROGRESS.md`, everything in `docs/`, every file in `accounting_agent/` (Python, both client configs, all three fixtures, `web/app.js`, `web/index.html`), all three test files, `scripts/check.py`, `Makefile`, and `ss_agent_system_handoff/BIRD_BOWL_ACCOUNTING_PILOT.md` and `AGENTS.md`.

**Inspected in part:** `ss_agent_system_handoff/BUILD_PLAN.md` (§6E bookkeeping and close, §11 data model, §12 durable workflow) and `ACCEPTANCE_TESTS.md` (AT-58 to AT-61). The rest of those two files concerns the out-of-scope business-development system.

**Executed, on Python 3.9.6 / SQLite 3.51.0, with no network, model or ledger access:**

| Check | Result |
| --- | --- |
| SHA-256 of all 38 files listed in `FABLE_REVIEW_MANIFEST.json` | 38 of 38 match |
| `python3 -m unittest discover -s tests` | 41 tests passed in 8.8 s (matches the claim in `PROGRESS.md`) |
| `python3 scripts/check.py` | Passed |
| 16 reviewer probes against the unmodified code (`reviewer_probes.py`) | All 16 reproduced the behaviour described in the findings below |
| 60 reviewer validation cases (`run_fable_validation_cases.py`) | 28 pass, 10 fail as documented, 22 deferred capabilities correctly refused |

**Not verified:**

- The browser walkthrough in `PROGRESS.md` and `docs/VERIFICATION.md`. I did not start the demo server. The screenshot `docs/accounting-agent-os-demo.jpg` that those documents cite is not in the bundle.
- `IMPLEMENTATION_BACKLOG.md` and `EXECUTIVE_AUTONOMY.md`, which `docs/SOURCES.md` and the reference `AGENTS.md` cite, are not in the bundle.
- Anything about Bird Bowl. No client fact was supplied and none is assumed here.
- The standards references in §13 are cited from my own knowledge and were not re-fetched during this review.

Passing software tests show software behaviour. They do not show accounting correctness or operating readiness, and this review does not treat them as such.

---

## 2. Overall assessment

The foundation is worth keeping, and it is not yet a base on which a second month, a second workflow family or approved client samples can safely be added.

What is sound is the execution discipline: a small shared runner, pure handlers, immutable evidence and artifacts, exact decimal money, lease-and-checkpoint recovery, fail-closed capability registry, and honest status labels. The code does what the README says for the three demonstrated workflows on one month of fictional data.

What is not sound is the model of *state over time* and of *authority*. The system has one period, one client-wide notion of "current", and one kind of human authority (a role string). Each of those is acceptable in a one-month demo and each breaks as soon as real accounting rhythm appears: a second month, a period lock, a late receipt, a recurring run, a policy change. I could break the central review control, and the lock, with ordinary inputs and no code changes.

None of this requires a stack rewrite. Python, SQLite and synthetic identities are adequate for the next two batches of work. The changes are to the data model and to the service boundary.

### The five most important findings

1. **Independent review is not enforced (F-01, P0).** The check compares the reviewer only with the actor who enqueued the run. The person who registered the policy and supplied the journal and its support can approve it if a colleague presses run. "Human" is decided by whether the actor id starts with `worker`.
2. **An item has no single governing version (F-02, P0).** Recurring runs on unchanged inputs create additional "current" copies of the same journal. I approved one copy and rejected another; both stand, and the export carries both. One reviewer can also approve the same artifact repeatedly, and a second reviewer's rejection is overridden by a later approval.
3. **The period and invalidation model cannot survive a second month (F-04, F-05, P1).** The period is one field on the client profile. Locking it voids the approvals it should protect. Moving to December strands November as `OUTSIDE_PERIOD`. Any new source of any kind, and any change to any Python file, marks every approval for the client stale. There is no finalized state.
4. **There is no shared accounting-effect or exception model (F-09, F-10, P1).** A card proposal is a category string, not an entry; a journal is a free-standing upload with no origin. Exceptions are strings on an artifact with no way to resolve them, so seven of the twelve teaching transactions (both duplicates, the credit, the out-of-period item, the split, the foreign charge and the card payment) have no path to approval. AP, AR, reconciliation and reporting each need these two entities; adding them later means rewriting every module.
5. **Policy and standing authority are self-granted (F-06, F-07, P1).** The preparer registers the profile that constrains the preparer, marks it `approved_demo_only`, issues mandates and revokes them. There is no proposed-to-approved step, no effective dating, and no second person.

Two further points deserve attention before client samples: close readiness tests whether a file of a given type exists and ignores every open exception (F-11), and the statement completeness control is declared by the same party that supplies the population (F-12).

---

## 3. What should be retained

- **Pure handlers behind one runner** (`modules.py`, `service.py`). Handlers receive a scoped snapshot and return structured output; they cannot query the database, approve, or cause a side effect. This is the right seam for AP, AR and the rest.
- **Fail-closed capability registry.** Deferred capabilities have no handler and cannot be enqueued; write-effect capabilities are refused even if a handler were added (`service.py:159-162`).
- **Immutable snapshots, artifacts, decisions and audit** with database triggers, and versioned sources keyed by scope, kind and key.
- **Exact money as validated decimal strings**, with floats, exponents and extra precision rejected at intake.
- **Lease token plus input-fingerprint check at commit.** A stale or superseded worker cannot write. Crash recovery and concurrent workers are tested and behaved correctly under my probes.
- **Conservative defaults in card preparation.** Credits, payments, splits, pending items, foreign currency and duplicates are held and nothing is guessed. All 18 of my independent card cases that target current behaviour passed on first run, including the injection case.
- **Blocking at item level with package-level causes pushed onto affected items** (statement control mismatch holds every item on that card and no others).
- **Separate states for prepared, reviewed, posted, reconciled and closed**, and the consistent refusal to imply one from another.
- **Honest labelling.** `PROGRESS.md` and `VERIFICATION.md` separate what ran from what did not. Keep that standard; F-22 lists the few places where the documents are ahead of the code.
- **The unconfigured Bird Bowl template** with nulls for unknown facts.

---

## 4. Prioritized findings

Priorities: **P0** current critical control or correctness defect. **P1** foundation change needed before expanding execution or using approved client samples. **P2** next capability or reliability improvement. **P3** later enhancement.

| ID | Pri | Classification | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-01 | P0 | Current defect | Review independence checks only the enqueuing actor; evidence and policy authors can approve; human/automation decided by id prefix | Probes P01, P02; case FV-R01 |
| F-02 | P0 | Current defect | No single governing version per item; conflicting and repeated decisions accepted | Probes P05, P14; case FV-R03 |
| F-03 | P0 | Current defect | Vendor normalisation discards all non-ASCII characters; unrelated descriptors match an alias and become approval-eligible | Probe P06; case FV-C15 |
| F-04 | P1 | Architectural gap | Period is one mutable profile field; locking or rolling it voids approvals and strands the prior period | Probes P09, P10; case FV-R04 |
| F-05 | P1 | Architectural gap | Client-wide and code-wide invalidation; no finalized state | Probes P11, P16 |
| F-06 | P1 | Architectural gap | Policy activates on registration by the preparer; no approval, effective dates or supersession | Code reading |
| F-07 | P1 | Architectural gap | Standing mandates are issued and revoked by the preparer and are unbound to period, policy version or evidence freshness | Code reading |
| F-08 | P1 | Current defect | A recurring occurrence is consumed when its run is held; missed occurrences are skipped without record | Probe P03; case FV-RC01 |
| F-09 | P1 | Architectural gap | No shared proposed-entry contract linking source item, entry, entity/book and period | Code reading |
| F-10 | P1 | Architectural gap | Exceptions are strings with no disposition path; dependency outcomes do not propagate | Code reading; 7 of 12 teaching items have no path to approval |
| F-11 | P1 | Architectural gap | Close readiness tests document-type presence only and ignores open exceptions and review status | Probe P12; cases FV-CL02, FV-CL04 |
| F-12 | P1 | Architectural gap | Completeness control is a self-declared count and signed total; excluded rows drop out silently; substitution passes | Probe P13; case FV-C19 |
| F-13 | P1 | Architectural gap, one current defect | No source ordering, removal or supersession semantics; a late older batch replaces newer data | Probe P07 |
| F-14 | P1 | Architectural gap | Null entity, framework and basis do not prevent approval-eligible output | Code reading |
| F-15 | P1 | Current defect | Journal validation accepts unrelated support, duplicate entries and entries with no ledger effect | Probe P08; cases FV-J08 to FV-J10 |
| F-16 | P1 | Architectural gap | Receipt-matching rules are hard-coded in the shared module as if they were shared doctrine | Probe P15 |
| F-17 | P1 | Current defect | One mandate that no longer fits the profile makes every recurring tick fail | Probe P04; case FV-RC02 |
| F-18 | P2 | Architectural gap | No failure classification, backoff or heartbeat; background worker stops permanently on any error; held is terminal | Code reading |
| F-19 | P2 | Architectural gap | Audit chain has no external anchor; export reads in two transactions; mutable run fields feed a control | Code reading |
| F-20 | P2 | Architectural gap | Two-decimal money and free-text currency are in the shared core | Code reading |
| F-21 | P2 | Current defect | Validation fixture is derived from teaching data and asserts blocker subsets, so unexpected blockers pass | Code reading |
| F-22 | P2 | Current defect | Several documentation statements are ahead of the code | Code reading |
| F-23 | P3 | Future enhancement | Demo transport gives every role token to any local caller; identity seam needed before any hosted use | Code reading |
| F-24 | P3 | Future enhancement | Whole-client fingerprint recomputed per job; state payload unbounded | Code reading |

Client-policy questions are listed separately in §8 because they are not defects.

---

## 5. Finding details

Line numbers refer to the bundle as delivered.

### F-01 — Review independence is not enforced · P0 · current defect

- **Where:** `service.py:325` (`actor.id == run["actor"] or actor.id.startswith("worker")`); `service.py:83-96` and `108-149` record the profile registrant and source supplier (`snapshots.actor`, `storage.py:18`) but review never reads them; `core.py:69-85` (`Actor` has a role string and no actor kind); `demo.py:9-10`.
- **Failure scenario (reproduced, P01):** `human-a` registers the profile and uploads journal J-001 with its support. `human-b` enqueues the run. `human-a`, holding the reviewer role, approves J-001. Accepted. Separately (P02), a reviewer-role actor named `automation-agent-7` is accepted, and one named `worker-of-the-month-jane` is refused.
- **Consequence:** The one control every other statement leans on ("every clean item still requires independent human review") is defeated by two people taking turns, or by one automated identity with the wrong name. In accounting terms: preparation and approval are not segregated for the person who created the evidence.
- **Smallest sufficient correction:**
  1. Add `kind` (`human` | `service`) to `Actor`, set only by trusted transport. Review requires `kind == "human"` and role `reviewer`. Delete the prefix test.
  2. At commit, store on the artifact envelope a `contributors` list: the run actor, the mandate issuer if any, the actor of every source snapshot in the artifact's evidence, and the actor who registered the profile version in force.
  3. Refuse approve and reject when the reviewer's id is in `contributors`.
- **Acceptance criteria:** FV-R01 returns 403. A reviewer who contributed nothing can still approve. A `service` actor with the reviewer role is refused regardless of id. The existing demo reviewer flow is unchanged.
- **Test:** FV-R01; convert probes P01 and P02 into `tests/test_platform.py`.
- **Dependencies / human decision:** None to implement. For Bird Bowl, Luis and the client must decide whether a person who approved a *policy* may review *transactions* prepared under it (see F-06 and the authority matrix in §7).

### F-02 — No single governing version per item · P0 · current defect

- **Where:** `service.py:163-170` (mandate runs skip the fingerprint de-duplication that manual runs get); `storage.py:43` (uniqueness is per step, not per item); `service.py:312-332` (no check for an earlier decision or a newer artifact); `service.py:404` (status is whatever the last decision row says); `web/app.js:14-18` (the UI shows only the latest run, the export shows all).
- **Failure scenario (reproduced, P05 and P14):** The documented demo flow is enough: prepare journals, issue the mandate, deliver two occurrences. J-001 now has three `current` artifacts. I approved one and rejected another; state reports `pending`, `approve` and `reject` for the same journal. On a single artifact, the sequence approve, approve, reject (second reviewer), approve leaves it `approve`.
- **Consequence:** A consumer of the export cannot say whether J-001 is reviewed. A rejection can be buried by re-approving, or sidestepped by approving the sibling copy.
- **Smallest sufficient correction:**
  1. Make the artifact content hash independent of the run: reference dependency *content hashes* in the envelope, not artifact row ids (`service.py:249`).
  2. At commit, if a current artifact with the same scope, workflow, item key and content hash exists, link the new run to it instead of inserting a copy.
  3. Define the governing artifact for (scope, workflow, item key) as the newest one from a completed run. Refuse approve and reject on any other.
  4. Add a decision state machine per artifact: `pending → approved | rejected`; `approved → revoked`; `rejected` and `revoked` are terminal for that version. Refuse a repeat of the current state. A contrary decision by another reviewer is recorded as a dispute and leaves the item `disputed`, not approved.
- **Acceptance criteria:** FV-R03 reports one governing artifact. A second approve returns 409. Reject after approve by another reviewer yields `disputed`. History remains append-only.
- **Test:** FV-R03; probes P05 and P14 as unit tests.
- **Dependencies:** Easier after F-05 (scoped manifests). No human decision.

### F-03 — Vendor normalisation collapses non-ASCII text · P0 · current defect

- **Where:** `core.py:60-61` (`[^A-Z0-9 ]` replaced by space); used for the alias match at `modules.py:130`, the duplicate key at `144-146` and the receipt vendor check at `162-163`. `service.py:67-68` accepts any non-empty alias.
- **Failure scenario (reproduced, P06):** A profile alias `東京文具` and a transaction descriptor `大阪修理` both normalise to the empty string. The transaction is matched to the Tokyo vendor, given its expense category, passes the receipt vendor check for the same reason, and is eligible for approval with no blockers.
- **Consequence:** The "no guess" invariant is violated with valid inputs. The trigger is narrow (an alias made only of non-ASCII or punctuation characters) but the result is a clean-looking wrong proposal. Partially non-ASCII names degrade in a safer direction (`PANADERÍA` becomes `PANADER A` and fails to match), which will matter for any client with Spanish-language vendors.
- **Smallest sufficient correction:** Normalise with Unicode NFKC and `casefold()`, keeping any character for which `str.isalnum()` is true. Reject at profile validation any alias whose normalised form is empty. In `card_prepare`, treat an empty normalised descriptor as `UNKNOWN_VENDOR` without a lookup, and fall back to the raw descriptor for the duplicate key. Do not fold accents by default; accent folding is a matching policy for the client to approve.
- **Acceptance criteria:** FV-C15 is held with `UNKNOWN_VENDOR` and `UNKNOWN_CATEGORY`, or the profile is refused. All existing alias tests still pass.
- **Test:** FV-C15; add a punctuation-only alias and an accented alias case.
- **Dependencies:** None.

### F-04 — The period is a profile field, and the lock destroys what it protects · P1 · architectural gap

- **Where:** `config/bird_bowl.demo.json:8`; `service.py:43-45`; `modules.py:81-89` (`period_issues`); `modules.py:106-110` (the statement control must cover exactly the profile period); `service.py:92-95` (any profile change bumps the client generation).
- **Failure scenarios (reproduced):** P09: approve J-001, then set `period.locked` to true. The approval becomes `stale`; on re-preparation J-001 is blocked by `PERIOD_LOCKED` and can never be approved again. P10: change the profile period to December. The approved November item becomes `stale` and re-prepares as `OUTSIDE_PERIOD` plus `STATEMENT_CONTROL_MISMATCH`. TX-008 (dated October 31) has nowhere to go in any configuration.
- **Consequence:** The system cannot hold two periods, cannot close one, and cannot route an item to the period it belongs to. This blocks the planned November capture and December validation before any accounting question arises.
- **Smallest sufficient correction:** Add a `periods` table (scope, period id, start, end, status `open | in_review | locked`, changed by, changed at, reason) with service operations `open_period`, `lock_period`, `reopen_period`, each audited and restricted to a human with the relevant authority. Bind every run to a period id. Assign each source to a period by its accounting date. Remove `period` from the profile. Locking is a status change, not a knowledge change, so it invalidates nothing. After a lock, new sources dated in that period are stored and raise `LATE_ACTIVITY_IN_LOCKED_PERIOD` against the period; they do not alter finalized work.
- **Acceptance criteria:** FV-R04 passes. Opening December leaves November statuses unchanged. An October-dated item in a November batch is prepared under October if open, or raises the late-activity exception if locked. A run cannot be enqueued for a locked period.
- **Test:** FV-R04, probes P09 and P10, plus a two-period scenario.
- **Dependencies / human decision:** Who may lock and reopen; which date governs cutoff (transaction, posting or statement date). Both are client decisions (§8, Q4 and Q9).

### F-05 — Everything invalidates everything, and nothing is ever final · P1 · architectural gap

- **Where:** `service.py:22` (hash of every `*.py` in the package, including `http.py`, `demo.py` and `__main__.py`); `service.py:102-106` (the manifest is every latest source of every kind for the client); `service.py:192-194`, `400-404`; `service.py:417-428` (export).
- **Failure scenarios (reproduced):** P16: approve journal J-001, then supply a card receipt for TX-002. The journal approval is exported as `stale`. P11: a simulated change to the code hash marks every run for the client non-current.
- **Consequence:** `ARCHITECTURE.md` records this as deliberate conservatism. In operation it is the opposite of conservative. Reviewed work is discarded daily, reviewers are trained to re-approve in bulk, and a routine deployment silently voids every open approval for every client. Nothing can be handed to a client as "the reviewed November package" because its status changes with the next upload.
- **Smallest sufficient correction:**
  1. Each capability declares what it reads: source kinds, profile sections, and look-back population. The run manifest is built from those inputs within the bound period. Currency is judged against that manifest.
  2. Replace the package-wide code hash with the capability version plus a hash of the files that implement handlers and invariants (`modules.py`, `core.py`). Transport and CLI changes do not affect accounting lineage.
  3. Add `finalize_package(period, workflow)`: an immutable record of the governing artifacts, their hashes, decisions and manifest at that moment. Later changes never rewrite a finalized package; they raise a `POST_FINALIZATION_CHANGE` exception that references it.
- **Acceptance criteria:** An unrelated receipt leaves a journal approval intact. Editing `http.py` changes no status; editing `modules.py` does. A finalized package exports identically before and after later intake.
- **Test:** Probes P11 and P16 as unit tests; a finalization round-trip test.
- **Dependencies:** F-04 for period scoping. No human decision for parts 1 and 2. Who may finalize is a client authority question.

### F-06 — Policy becomes active when the preparer registers it · P1 · architectural gap

- **Where:** `service.py:83-96` (`onboard` requires the preparer role); `service.py:37-40` (`approval_status` is a string the caller supplies); `service.py:79-81` (customers, dimensions and historical decisions must be empty); the profile is one document containing identity, chart, vendors, mappings, receipt policy, period and procedures.
- **Failure scenario:** The preparer registers version 2 with `receipt_required: false`, or remaps a vendor to a different account, and re-prepares. Items that were held are now clean. The reviewer sees item-level proposals carrying a profile hash, with nothing to show that policy changed, what changed, or that nobody approved it.
- **Consequence:** The party constrained by the policy edits the policy. The pilot document's requirement that "Luis validates accounting changes before they enter the approved playbook" has no representation. Transaction-specific corrections and reusable rules cannot be told apart because neither exists as a record.
- **Smallest sufficient correction:** Two steps.
  1. Now: profile versions are registered as `proposed`. A separate `approve_profile_version` operation, by a human who did not propose it, moves the client pointer. Runs use only the approved version.
  2. Next: move rules out of the monolith into individually versioned records (schema in §7) with status, effective dates, approver, evidence and supersession. Handlers receive only approved rules whose effective window covers the item's accounting date.
- **Acceptance criteria:** A proposed version is never used by a run. The proposer cannot approve. A rule effective March 1 is not applied to a February item. Re-preparing a prior period uses the rule in force for that date. A single-item correction changes nothing for the next item from the same vendor.
- **Test:** New tests for each criterion; AT-60 mechanics.
- **Dependencies / human decision:** Who approves Bird Bowl policy, and what evidence a reusable rule requires (§8, Q6).

### F-07 — Standing authority is self-issued and unbound · P1 · architectural gap

- **Where:** `service.py:334-346`, `348-353`, `355-383` (create, revoke and tick all require the preparer role); `storage.py:22-26` (a mandate stores workflows, window, interval, cap and issuer only).
- **Failure scenario:** Any holder of the preparer role issues a mandate for every workflow at a 60-second interval. The handoff calls mandates "human-issued", but the role is the same one the automation's operator holds, and nothing binds the mandate to the policy version, the period it should prepare, or the evidence it needs.
- **Consequence:** A mandate is standing authority. Granted by the party it authorises, and blind to policy change and evidence freshness, it will carry last month's assumptions into this month's run.
- **Smallest sufficient correction:** A mandate needs `approved_by` (human, not the issuer), the policy version set it was approved against, a `period_rule` (which period each occurrence prepares), a `freshness` predicate (required source kinds with an as-of on or after the occurrence start), and a mandatory expiry. A material policy change moves the mandate to `needs_reconfirmation`. An occurrence without fresh evidence is recorded as `awaiting_evidence` and does not run.
- **Acceptance criteria:** Issuer cannot approve. No dispatch without fresh inputs. Policy change suspends the mandate visibly.
- **Dependencies / human decision:** F-04, F-06, F-13. Who may approve a mandate for Bird Bowl.

### F-08 — A held run consumes its occurrence · P1 · current defect

- **Where:** `service.py:163-166` (an existing run for the occurrence is returned whatever its status); `service.py:213-216` (stale inputs put the run on hold); `service.py:369-381` (only the current occurrence is considered, and nothing records the ones in between). No code path moves a run from `held` back to `queued`.
- **Failure scenario (reproduced, P03):** Deliver an occurrence; before the worker claims it, a receipt arrives. The run is held as stale. Deliver the same occurrence again: the tick returns the held run id as if dispatched. Zero artifacts exist for the occurrence, and after the intake zero current journal artifacts exist for the client.
- **Consequence:** Evidence arriving is the ordinary reason recurring work is due. The scheduled preparation silently does not happen and the only trace is a run in `held`.
- **Smallest sufficient correction:** Separate occurrences from runs: an `occurrences` table (mandate, workflow, occurrence key, status, linked runs) holding the uniqueness constraint. A held run releases its occurrence for re-dispatch against current inputs. Each tick writes a `skipped_no_catch_up` row for every occurrence between the last and the current one.
- **Acceptance criteria:** FV-RC01 passes with still exactly one completed preparation per occurrence. Skipped occurrences appear in state and export.
- **Dependencies:** None. Implement with F-17.

### F-09 — No shared proposed-entry contract · P1 · architectural gap

- **Where:** `modules.py:169-175` (a card proposal is a vendor and a category); `modules.py:40-55`, `179-208` (a journal is an uploaded source with no origin); `service.py:263-267` (the artifact envelope carries scope, versions and fingerprint, and no legal entity, book or period). `CAPABILITY_CONTRACTS.md` states every workflow binds these; the code does not.
- **Failure scenario:** The reviewer approves TX-001 as office supplies. Nothing states the resulting entry: which account is credited, on which date, in which entity and book. Journal J-001 debits office supplies and credits the card liability for a purchase; whether it records the same purchase as a card item cannot be detected. When AP arrives, a bill for a card-paid purchase is a third representation of one event.
- **Consequence:** Without one representation of "the ledger effect this work proposes", there can be no subledger-to-GL tie, no detection of double recording across modules, no trial-balance impact preview, and no reporting lineage. Every later module will invent its own artifact shape and close will not be able to add them up.
- **Smallest sufficient correction:** Define a `proposed_entry` contract and one shared validator in `core.py`: entity, book, period, entry date, currency, lines (account, debit, credit, dimensions), entry type (`standard | accrual | reversal | reclass | settlement`), `reverses`, origin (capability, item key, source references), and external posting status (`not_posted`). `card_prepare` emits the proposal plus its derived entry; `journal_validate` uses the same validator. One source item may originate at most one live entry; a second raises `SOURCE_ALREADY_HAS_ENTRY`. Card accounts in the profile become objects carrying the liability account they settle to.
- **Acceptance criteria:** Each approved card item yields exactly one proposed entry traceable to its source. A journal citing an already-used source is held. The sum of proposed entries by account is reproducible from the export.
- **Dependencies / human decision:** F-04. Card liability mapping, entry-date policy, and whether card charges pass through AP or a clearing account are client facts (§8, Q3 and Q8).

### F-10 — Exceptions cannot be resolved, and outcomes do not flow between steps · P1 · architectural gap

- **Where:** `modules.py:68-70` (a blocker is a string in a list); `service.py:329-330` (approval is impossible while any blocker exists); no operation records a disposition. `modules.py:92-97` and `179-182` read `ctx["sources"]` and ignore `ctx["dependencies"]`, so the `NO_SOURCE_EVIDENCE` blocker from the inventory step affects nothing downstream. `modules.py:224-229`: `package.check` performs no check.
- **Failure scenario:** In the teaching month, suppose the two same-day 90.00 charges are both legitimate, the credit is a refund, one item is a card payment and one needs a split. All stay held permanently, because the only inputs the system accepts are a changed source or a changed profile. A human resolves them in a spreadsheet, and the system's export shows them unresolved forever.
- **Consequence:** The platform cannot complete a real month, which creates pressure to weaken blockers. `PROGRESS.md` lists dispositions as next work; I agree, and the point of this finding is that it is a foundation shared by all six areas, to be built once.
- **Smallest sufficient correction:** An `exceptions` table (scope, period, item key, code, status `open | dispositioned | superseded`) and an append-only `dispositions` table with a closed vocabulary per code, for example duplicate → `distinct_purchases | duplicate_of | source_replay`; credit → `refund_of | standalone_credit`; split → allocation lines; payment → `settlement_of_card_liability`. A disposition carries evidence references, reason, deciding human and scope (`single_item` by default, or `propose_rule`, which creates a *proposed* rule and nothing more). The disposition is an input to re-preparation; the new artifact cites it and then goes to independent review. Each step declares whether upstream blockers propagate; package-level codes propagate by default.
- **Acceptance criteria:** Two duplicate candidates with a `distinct_purchases` disposition and two distinct receipts become eligible, citing the disposition. A service actor cannot disposition. A disposition does not create an active rule. Revoking it re-blocks the item.
- **Dependencies / human decision:** F-01, F-02, F-06. Who may disposition each exception type, and whether the person who dispositions may also give final review (§7 authority matrix).

### F-11 — Close readiness tests whether files exist · P1 · architectural gap

- **Where:** `modules.py:211-221`; `modules.py:56-59` (a document is a type and free text, with no period and no reference to what it evidences); `config/bird_bowl.demo.json:25`.
- **Failure scenario (reproduced, P12):** Four placeholder documents whose content says "nothing reconciled; prior period" clear `MISSING_CLOSE_EVIDENCE`. Twelve open card and journal exceptions in the same client are not mentioned. A document uploaded once satisfies the requirement in every later period.
- **Consequence:** The standing holds (`FINAL_CLOSE_SIGNOFF_REQUIRED`, `EXTERNAL_STEPS_UNVERIFIED`) prevent a false "closed", which is good. But "readiness" currently means "five labels are present", and the handoff's own scenario ("reviewed journal preparation but a missing card statement") is not something the handler can evaluate, because it cannot see any other workflow.
- **Smallest sufficient correction:** Now: require a period on documents; have the service pass a `period_status` summary (open exceptions, eligible-but-unreviewed items, governing-artifact review states per workflow) into the handler; add `OPEN_PREPARATION_EXCEPTIONS` and `UNREVIEWED_PREPARATION` blockers. Later: replace the label list with typed checklist requirements (`workflow_outcome`, `reconciliation`, `tieout`, `document`) evaluated against artifacts.
- **Acceptance criteria:** FV-CL02 and FV-CL04 pass.
- **Dependencies:** F-02, F-04, F-10.

### F-12 — The completeness control is declared by the party it controls · P1 · architectural gap

- **Where:** `modules.py:99-113`; `fixtures/build_fixtures.py:42-43` (the control is computed from the same rows it then checks).
- **Observations:**
  1. The control is a count and one signed total supplied in the same intake as the transactions. It shows that two numbers typed by one party agree.
  2. Rows in another currency or dated outside the period are excluded from the comparison without being reported as a population difference (FV-C19: a CAD charge leaves a control of count 0, total 0.00 satisfied).
  3. Substitution passes (P13): one 65.00 item leaves the posted population, another 65.00 item enters, and every item is still clean.
  4. The fixture sums a 300.00 card payment in the same direction as purchases (840.00 total). On a statement, purchases and payments move the balance in opposite directions, so this control cannot be tied to a real statement as it stands.
  5. The control period must equal the calendar period exactly. Card statement cycles usually do not.
  6. There is no opening or closing balance, so periods cannot be chained.
- **Consequence:** The handoff already says a matched total does not prove completeness. The stronger point is that this control cannot fail for the errors that matter, and its presence may be read as assurance.
- **Smallest sufficient correction:** A `statement` source kind: account, statement id, cycle start and end, opening balance, closing balance, totals by activity type, line count, optional line ids, and provenance (system extract or manually keyed, and by whom). Checks: opening equals prior closing; opening plus activity equals closing; intake population by activity type ties to the statement totals; every excluded row is listed in an `unreconciled_population` section; line-level tie when line ids exist.
- **Acceptance criteria:** A foreign-currency row appears as an unreconciled population item. An opening-balance break blocks the account. Payments and purchases tie separately.
- **Dependencies / human decision:** F-13. Which document is the authoritative statement, and how statement cycles map to accounting periods (§8, Q2 and Q9).

### F-13 — Sources have no ordering, removal or supersession semantics · P1 · architectural gap with one current defect

- **Where:** `service.py:133-147` (identity is the batch id only); `storage.py:99-108` (the last write is the current version); `modules.py:128-129` (a `supersedes_source_id` produces a blocker and nothing else).
- **Failure scenario (reproduced, P07):** Batch 2 revises TX-001 to 45.00. Batch 1, delayed, then arrives with the original 42.50. Version 3 is 42.50 and is now current. Separately: a pending authorisation that the bank drops can never leave the population, and stays `PENDING_TRANSACTION` plus `MISSING_RECEIPT` forever.
- **Consequence:** Out-of-order delivery regresses data silently. Feed removals, which every card feed produces, cannot be represented.
- **Smallest sufficient correction:** Add `as_of` (source timestamp or feed sequence) to the source envelope. A version with an older `as_of` is stored as history and does not become current. Add a tombstone (reason `feed_removed | voided | superseded`). Resolve `supersedes` in the engine: the superseded row leaves the population with the link retained. Removal or revision of an item with a recorded approval raises an exception against that approval.
- **Acceptance criteria:** P07 leaves 45.00 current. A tombstoned pending row no longer produces blockers. FV-C13 continues to hold the settled row for review.
- **Dependencies:** None to implement synthetically. Real feed semantics are a client and provider fact.

### F-14 — Unknown client facts do not stop eligible output · P1 · architectural gap

- **Where:** `config/bird_bowl.demo.json:6` (`legal_entity`, `accounting_framework`, `accounting_basis` are null); `service.py:36` requires the keys and not the values; `modules.py:179-208` validates journals regardless.
- **Failure scenario:** The real Bird Bowl profile arrives partly filled, with the basis still unknown. Journals balance, accounts exist, support is attached, and the entries go to review as clean. An accrual is mechanically valid under either basis and correct under only one.
- **Consequence:** "Unknowns stay null" is honoured in the data and has no effect on execution.
- **Smallest sufficient correction:** Each capability declares the client facts it requires. For any profile class other than `synthetic_demo`, a missing fact blocks every item with `CLIENT_FACT_MISSING:<fact>`. A synthetic profile may carry explicit, labelled waivers.
- **Acceptance criteria:** A `client_sample` profile with a null basis produces no eligible journal artifact. The demo runs only because of a visible waiver.
- **Dependencies:** F-06.

### F-15 — Journal validation is weaker than "mechanically valid" · P1 · current defect

- **Where:** `modules.py:179-208`.
- **Failure scenarios (reproduced, P08):** A journal supported only by the trial-balance placeholder is eligible. The same journal under a second key is eligible, with no duplicate signal. A journal that debits and credits the same account for the same amount is eligible.
- **Consequence:** A doubled accrual, or an entry backed by any document already on file, reaches the reviewer as clean. Card items have duplicate and evidence-binding controls; journals have neither.
- **Smallest sufficient correction:** Support must be a document of a type the journal workflow accepts and must reference the journal key (`JOURNAL_SUPPORT_NOT_BOUND`). Flag journals with identical date, lines and currency (`POSSIBLE_DUPLICATE_JOURNAL`). Hold entries whose lines net to zero per account and dimension (`NO_NET_LEDGER_EFFECT`). Later, with F-09: control-account restrictions, dimensions, reversal links.
- **Acceptance criteria:** FV-J08, FV-J09 and FV-J10 pass; FV-J01 to FV-J07 still pass.
- **Dependencies:** None for the three checks.

### F-16 — Receipt-matching rules are hard-coded as shared doctrine · P1 · architectural gap

- **Where:** `modules.py:152-168`; `service.py:46-49` (the only receipt policy is a boolean).
- **Failure scenario (reproduced, P15):** A purchase made on the 2nd posts on the 3rd. The receipt is dated the 2nd. `RECEIPT_DATE_MISMATCH`. The same will happen for most real card activity, because feeds usually carry the posting date.
- **Consequence:** Exact date equality, exact amount equality and one receipt per charge are demo choices sitting in the shared module. They are the kind of "demo assumption presented as general doctrine" the handoff asks about. Holding is the right default; the defect is that the reviewer cannot tell a policy breach from an unset policy.
- **Smallest sufficient correction:** Move these to an approved client rule (`receipt_matching`: date window, amount tolerance, multiple receipts, vendor match method). When a value is unset, keep exact matching and emit a code that says so (`RECEIPT_DATE_POLICY_UNSET`).
- **Dependencies / human decision:** F-06. Bird Bowl's document policy (§8, Q5).

### F-17 — One unfit mandate stops all recurring work · P1 · current defect

- **Where:** `service.py:365-381` calling `_enqueue` (`157-158`), inside one transaction.
- **Failure scenario (reproduced, P04):** Two mandates exist. A new profile version removes `journal_preparation` from the client's procedures. The next tick raises 403, creates no run for either mandate, and does not advance the clock.
- **Smallest sufficient correction:** Evaluate each mandate independently. On a control error, mark that mandate `held` with the reason, audit it, and continue.
- **Acceptance criteria:** FV-RC02 passes.

### F-18 — Retry, lease and worker lifecycle · P2 · architectural gap

- **Where:** `service.py:277-304` (every failure, including a deterministic control error from a handler, is retried immediately up to three times); `core.py:131-132` (30-second lease, no heartbeat); `http.py:30-37` (the worker loop exits on any exception and is never restarted); `service.py:214` (held is terminal).
- **Consequence:** Deterministic failures burn their attempts in milliseconds. A handler slower than 30 seconds can never commit. One transient database lock stops the demo worker until restart.
- **Correction:** Classify failures (`transient | deterministic | stale`). Retry only transient ones, with backoff stored as `not_before`. Add a lease heartbeat. Make the worker loop log and continue. Give `held` an explicit resume or supersede path.

### F-19 — Audit and export integrity · P2 · architectural gap

- **Where:** `storage.py:66-69` (triggers protect four tables and can be dropped by anyone with file access; `runs`, `steps`, `mandates` and `clients` are mutable, and `runs.actor` feeds the independence check); `storage.py:91-97` (per-scope hash chain with no external anchor, so truncating the tail is undetectable); `service.py:417-428` (state and history are read in two transactions, and `exported_at` is inside the package hash, so two exports of the same state never match).
- **Correction:** Read the export in one transaction. Hash content separately from export metadata. Include the audit chain head in every export and in every finalized package so that later truncation is detectable by comparison. Copy the independence inputs onto the immutable artifact (done by F-01).
- **Note:** `ARCHITECTURE.md` already states that this is not tamper-proof. External retention is a hosted-stage decision.

### F-20 — Money and currency contract · P2 · architectural gap

- **Where:** `core.py:47-51` (two decimals for every currency); `modules.py:15`, `43`, `87` (currency is free text compared by string equality, so `usd` is a mismatch against `USD`).
- **Correction:** Validate currency codes against ISO 4217 and take the minor unit from the code. Carry original amount, original currency, rate, rate source and rate date as explicit fields when a foreign charge is eventually handled.
- **Trigger:** The first non-USD or multi-currency account. Until then, the present contract is adequate and correctly labelled as a fixture contract.

### F-21 — The test suite cannot detect unexpected blockers · P2 · current defect

- **Where:** `tests/test_validation.py:20` (`issubset`); `fixtures/validation.json` (each case mutates one teaching source); `tests/test_platform.py:141-152` (independence is tested only for the same actor id).
- **Consequence:** A change that adds a spurious blocker to every item passes the suite. The "separate validation fixture" described in `PROGRESS.md` shares its data and expected answers with the teaching fixture.
- **Correction:** Assert exact blocker sets. Adopt the reviewer cases as an independent suite. Add negative authority tests.

### F-22 — Documentation ahead of the code · P2 · current defect

| Statement | Location | Actual |
| --- | --- | --- |
| "Every workflow binds … legal entity/book identity, period … preparer and review policy" | `docs/CAPABILITY_CONTRACTS.md`, common contract | The artifact envelope has none of these (`service.py:263-267`) |
| Mandates are "human-issued" | `FABLE_ACCOUNTING_HANDOFF.md`; `PROGRESS.md` | Issued by the preparer role; no actor kind exists |
| "Preparers and workers cannot approve" | `docs/ARCHITECTURE.md` | True for the same actor id and the `worker` prefix only (F-01) |
| "Separate validation fixture" | `PROGRESS.md` | Mutations of the teaching fixture (F-21) |
| `package.check` | `modules.py:224-229` | Performs no check |
| Screenshot `docs/accounting-agent-os-demo.jpg` | `PROGRESS.md`, `docs/VERIFICATION.md` | Not in the bundle |

### F-23 — Demo transport and identity seam · P3 · future enhancement

`http.py:21` and `106-108`: `/api/session` returns the preparer and reviewer tokens to any caller that can reach loopback. This is a declared demo harness and the service refuses non-local environments, so it is not a present defect. Before any hosted use, the service needs an identity interface that supplies verified human identity, actor kind and client membership, and the demo selector must be removed from the deployable package.

### F-24 — Recomputation and payload size · P3 · future enhancement

`service.py:98-106` is called for every candidate job in `claim` and for every run in `state`, each time reading and hashing every source for the client. `state` returns every artifact ever produced. Acceptable at fixture size. F-05's scoped manifests remove most of the cost.

---

## 6. Six-area capability and control matrix

"Executes today" is what I ran. "Shared foundation" names the findings that must be closed first. Execution kind: D deterministic, M model-assisted proposal, H human.

| Area | Executes today | Shared foundation needed first | Minimum controls before the first capability | First capability to add | Kind | Client policy it depends on |
| --- | --- | --- | --- | --- | --- | --- |
| **General Ledger** | Mechanical journal validation: balance, line shape, active account, period, currency, a support key exists | F-09 proposed entry; F-04 periods; F-14 fact gates; F-15 | Entry bound to entity, book and period; support bound to the entry; duplicate and no-effect checks; reversal linkage; control-account restriction | Proposed entries derived from approved card items, then accrual and reversal preparation | D for validation; H for recognition; M may propose | Framework and basis; chart with types and control accounts; dimensions; who may propose and approve entries |
| **Accounts Payable** | Nothing. Deferred and correctly refused | F-09; F-10 dispositions; F-06 rules; F-13 source lifecycle | Vendor identity and change approval; invoice-number normalisation for duplicate candidates across feeds; subledger-to-control tie; payment proposal separated from payment execution; bank-detail change hold | Bill preparation with duplicate control and AP control tie-out. Payments stay reserved | D; H for exceptions; M may read documents | Approval chain; whether receiving is matched; terms; cutoff and accrual policy; 1099 or tax treatment if applicable |
| **Accounts Receivable** | Nothing. Deferred and correctly refused | F-09; F-10; F-06 | Customer scope; invoice uniqueness; application budget (never exceed receipt or open balance); unapplied cash explicit; subledger-to-control tie | Cash-application candidates and aging workpaper. Only if Bird Bowl has receivables | D; H for ambiguity | Revenue recognition policy; aging definition; credit and write-off authority |
| **Banking and Reconciliation** | Card intake, alias category proposal, duplicate candidates, structured receipt checks, count-and-total control | F-12 statement; F-13 lifecycle; F-10 dispositions; F-16 | Opening-to-closing balance chain; activity tied by type; one-use matching; ambiguous matches held; transfer and settlement pairing; reconciled state distinct from prepared | Card statement reconciliation workpaper, then card-payment settlement pairing with the bank side | D; H for matches and timing items | Authoritative statement source; cycle-to-period mapping; one posting route; duplicate window |
| **Month-End Close** | Document-type presence checklist with permanent sign-off and external holds | F-11; F-04; F-02; F-10; F-05 finalization | Checklist items typed and evaluated from artifacts; dependency on review state and open exceptions; accrual reversal check; nothing inherited from the prior period; lock as an authorised status change | Close readiness v2 over real workflow outcomes, then period package finalization and lock | D to assemble; H to sign off | Close calendar and checklist; who signs off and locks; reopen rules; materiality for carried exceptions |
| **Financial Reporting** | Nothing. Deferred and correctly refused | F-09; trial-balance snapshot source; F-04; F-06 for mappings | Trial balance balances and ties to the ledger extract; every account mapped; rollforward ties; comparatives on one mapping version; calculation separated from explanation | Trial-balance snapshot intake with tie checks, then statement assembly from an approved mapping | D for assembly and variance arithmetic; M for commentary as proposal; H to accept | Report definitions; basis; comparative and budget versions; rounding presentation |

Cross-cutting entities that all six areas share and that do not exist yet: accounting period, legal entity and book, proposed entry, exception and disposition, policy rule, authority grant, statement, occurrence, finalized package.

Recommended order of capability work, each behind the same contracts: (1) exception dispositions for card preparation; (2) card statement reconciliation; (3) proposed entries from approved card items and trial-balance snapshot intake; (4) settlement and transfer pairing, then bank reconciliation; (5) close readiness v2 and period finalization; (6) AP bill preparation; (7) AR, if relevant to the client; (8) statement assembly and variance. The order follows shared entities: each step reuses what the previous one introduced.

---

## 7. Client configuration and policy approval

### 7.1 Split the profile

Today one JSON document holds identity, period, chart, vendors, mappings, policy and procedures, and any change to it invalidates everything. Split it into records with different owners and lifecycles:

| Record | Changes | Approved by | Effect of change |
| --- | --- | --- | --- |
| Client identity (entity, books, framework, basis, base currency, system identifiers) | Rarely | Client authority and engagement lead | Blocks affected capabilities until re-approved |
| Chart of accounts (id, type, subtype, control flag, active window) | Occasionally | Policy approver | Affects items dated in the changed window |
| Periods | Monthly | Close authority | Status change only; invalidates nothing |
| Policy rules (mappings, document policy, matching, cutoff, thresholds) | As learned | Policy approver, never the proposer | Applies to items dated in the rule's effective window |
| Authority grants | On staffing change | Client authority | Affects who may act from the effective date |
| Procedures and checklists | Occasionally | Policy approver | New version applies to periods opened after approval |
| Credentials reference | Hosted stage only | Technical owner and client authority | Never in profile JSON or exports |

### 7.2 Illustrative schemas

All of the following are **proposed and fictional**. None is approved policy for any client. Field values are examples of shape only.

**Client identity with explicit unknowns and required-fact gates**

```json
{
  "record": "client_identity",
  "status": "proposed",
  "profile_class": "client_sample",
  "organization_id": "demo_org",
  "client_id": "example_client",
  "legal_entities": [
    {"entity_id": "ENT-EXAMPLE-1", "name": null, "books": [{"book_id": "BOOK-1", "base_currency": null, "ledger_system": null, "ledger_company_id": null}]}
  ],
  "accounting_framework": null,
  "accounting_basis": null,
  "fact_waivers": [],
  "approved_by": null,
  "approved_at": null
}
```

A capability declares what it needs, and the service refuses to produce eligible output without it:

```json
{
  "capability": "gl.journal_validate",
  "requires_client_facts": ["legal_entities[].books[].base_currency", "accounting_framework", "accounting_basis", "chart.approved_version"],
  "reads": {"source_kinds": ["journal", "document"], "profile_sections": ["chart", "periods"], "look_back": "bound_period"}
}
```

**Accounting period**

```json
{
  "record": "period",
  "period_id": "2027-02",
  "book_id": "BOOK-1",
  "start": "2027-02-01",
  "end": "2027-02-28",
  "status": "open",
  "status_history": [{"status": "open", "by": "human:example-close-authority", "at": "2027-02-01T09:00:00+00:00", "reason": "Period opened"}]
}
```

**Policy rule: reusable vendor mapping, proposed**

```json
{
  "record": "policy_rule",
  "rule_id": "RULE-EX-0007",
  "rule_type": "vendor_account_mapping",
  "status": "proposed",
  "scope": "reusable",
  "payload": {
    "vendor_id": "example_vendor",
    "match": {"method": "exact_alias", "aliases": ["EXAMPLE VENDOR 001"]},
    "proposes": {"account_id": "EX_SUPPLIES", "dimensions": {}},
    "conditions": {"activity": "purchase", "amount_max": null, "requires_business_purpose_note": false}
  },
  "effective_from": "2027-02-01",
  "effective_to": null,
  "supersedes": null,
  "origin": {"kind": "review_correction", "decision_id": 412, "item_key": "ex_card:TX-88"},
  "evidence_required_for_approval": ["three_or_more_reviewed_examples", "vendor_nature_confirmed_by_client"],
  "evidence_refs": [],
  "proposed_by": "human:example-preparer",
  "proposed_at": "2027-02-14T15:20:00+00:00",
  "approved_by": null,
  "approved_at": null
}
```

Rules for the lifecycle:

- Status moves `proposed → approved | rejected`, and `approved → superseded` only by a later approved rule that names it in `supersedes`.
- `approved_by` must be a human with the policy-approver grant and must differ from `proposed_by`.
- A model may create a `proposed` rule. It can never set any other status.
- A handler receives only approved rules whose effective window contains the item's accounting date. Re-preparing January uses January's rules.
- Supersession never rewrites history: the old rule keeps applying to dates before the new rule's `effective_from`.

**Transaction-specific correction that does not become a rule**

```json
{
  "record": "disposition",
  "exception_code": "POSSIBLE_DUPLICATE",
  "item_keys": ["ex_card:TX-104", "ex_card:TX-105"],
  "disposition": "distinct_purchases",
  "scope": "single_item",
  "evidence_refs": [{"snapshot_id": 881, "hash": "…"}, {"snapshot_id": 882, "hash": "…"}],
  "reason": "Two separate orders on the same day; two receipts with different order numbers.",
  "decided_by": "human:example-reviewer",
  "decided_at": "2027-02-16T10:05:00+00:00",
  "propose_rule": null
}
```

**Document and matching policy with explicit unset values**

```json
{
  "record": "policy_rule",
  "rule_type": "receipt_matching",
  "status": "proposed",
  "payload": {
    "receipt_required": {"default": true, "exceptions": []},
    "date_window_days": null,
    "amount_tolerance": null,
    "allow_multiple_receipts": false,
    "statement_may_substitute": false
  },
  "note": "null means not decided: the module matches exactly and reports the policy as unset."
}
```

**Authority matrix**

```json
{
  "record": "authority_grants",
  "status": "proposed",
  "grants": [
    {"actor": "human:example-operator", "may": ["intake", "prepare", "disposition:MISSING_RECEIPT"], "from": "2027-02-01", "to": null},
    {"actor": "human:example-accountant", "may": ["review", "disposition:*", "propose_rule"], "from": "2027-02-01", "to": null},
    {"actor": "human:example-lead", "may": ["approve_rule", "approve_mandate", "finalize_package", "lock_period", "reopen_period"], "from": "2027-02-01", "to": null},
    {"actor": "service:worker", "may": ["execute_prepare"], "from": "2027-02-01", "to": null}
  ],
  "separation_rules": [
    "review: reviewer must not be a contributor to the artifact",
    "approve_rule: approver must not be the proposer",
    "approve_mandate: approver must not be the issuer",
    "service actors may hold execute_prepare only"
  ]
}
```

**Standing mandate bound to authority, policy and evidence**

```json
{
  "record": "mandate",
  "status": "proposed",
  "workflows": ["card_preparation"],
  "period_rule": "current_open_period",
  "trigger": {"kind": "event", "on": "statement_intake"},
  "freshness": {"requires": [{"source_kind": "statement", "as_of": "on_or_after_occurrence_start"}]},
  "policy_versions_bound": ["RULE-EX-0007@1"],
  "limits": {"max_occurrences": 12, "expires": "2027-12-31T00:00:00+00:00"},
  "issued_by": "human:example-accountant",
  "approved_by": null,
  "on_policy_change": "needs_reconfirmation"
}
```

---

## 8. Client questions, ordered by what they block

Nothing below is assumed. Each question names the step it blocks.

**Blocks any approved-sample preparation (gate G1)**

1. **Entity and books.** Which legal entity and which set of books are in scope? What accounting framework and basis do they use? Is the Desktop-to-QBO conversion complete, and which system is the book of record for November and December 2026? *Blocks: F-14 gates, every journal.*
2. **Authoritative sources.** For each card account: what is the authoritative record of posted activity (statement PDF, issuer export, feed), who extracts it, and does it give opening balance, closing balance and totals by activity type? *Blocks: F-12 completeness.*
3. **Chart and card mapping.** The approved chart of accounts with types and active status; which ledger liability account each card settles to; whether card spend goes straight to expense or through AP or a clearing account. *Blocks: F-09 entries.*
4. **Cutoff date.** Is an item assigned to a period by transaction date, posting date or statement date? How are items handled when a statement cycle crosses month end? *Blocks: F-04 period assignment.*
5. **Document policy.** Which purchases require a receipt, what counts as acceptable support, what date and amount differences are tolerated, whether a statement line may substitute, and how missing documents are resolved. *Blocks: F-16.*
6. **Authority.** Who may prepare, who may review, who may resolve each exception type, who approves reusable rules, who may lock and reopen a period. What are Theresa's and Luis's assigned limits, and is anyone else involved? *Blocks: F-01 contributors rule, F-06, F-10, §7 matrix.*
7. **Minimum sample packet.** One closed month for one card account: the statement, the full posted population, receipts as actually kept, the entries as actually booked, and the reviewer's corrections. Plus a second month held back for validation. *Blocks: G1 itself.*

**Blocks specific treatments within the first workflow**

8. **Treatments needing a rule.** Refunds and partial refunds; card payments; fees and interest; rewards credits; repairs versus capital items and any capitalisation threshold; prepaid and annual subscriptions; inventory purchases; personal or employee spend; meals and tips; mixed-purpose purchases; foreign charges. For each: the treatment, the evidence, and whether it is one-off judgement or a reusable rule.
9. **Statement cycles and prior-period items.** How late receipts, prior-period changes and items found after close are handled; whether closed periods are ever reopened.
10. **Dimensions.** Whether location, department, class, project or tax codes are required on entries, and on which accounts.
11. **Duplicate window.** Whether same vendor and amount on adjacent days, or across two cards, should be raised as a candidate.

**Blocks later capabilities**

12. **AP and AR relevance.** Does Bird Bowl carry payables and receivables in the ledger? If so: approval chain, receiving practice, terms, aging definition.
13. **Close.** The current close checklist and calendar, required reconciliations, and who signs off.
14. **Reporting.** Which statements and management reports are produced, on which mapping, with which comparatives.

**Blocks read-only integration and beyond (gates G2 to G4)**

15. **Systems.** Ledger edition and realm, intake route for bank and card activity, the single posting route, and how pending items, removals and reconciled status are represented. The build plan's note on QBO API limits must be re-verified against current provider documentation at that time.
16. **Hosting and support.** Platform, identity, secrets, backups, administrators and cost owner (Jeff and the client), and the accounting co-management arrangement.
17. **Operating evidence.** What Theresa's teach-back and unattended-run evidence must show before handoff.

---

## 9. Readiness gates

No gate opens the next one automatically. Each requires its own recorded human decision.

| Gate | Entry criteria | What it permits | What it does not permit |
| --- | --- | --- | --- |
| **G0 Synthetic acceptance** | Batch 1 and Batch 2 complete. All P0 and P1 current defects fixed with tests. Reviewer cases: zero unexpected, all fail-until-fix cases fixed. A full synthetic month can be driven to "every item approved or dispositioned, package finalized, period locked" with no database edits and no weakened blocker. Two synthetic clients in different periods on one engine with no cross-effects. Documentation matches code. | A statement that the software controls behave as specified on fictional data | Any claim about accounting correctness, Bird Bowl, or readiness |
| **G1 Approved client samples** | G0. Questions 1 to 7 answered in writing by the people with authority. Client approval to use named sample records in a local, unconnected environment. Real identity, chart and rules entered as *proposed* and approved by a named human through the rule lifecycle. A held-out month not used to build rules. Named human reviewer who is not the preparer. | Local preparation on approved samples; comparison with the client's known reviewed results; recording disagreements | Connection to any system; use of sample output in the client's books |
| **G2 Read-only integration** | G1 results accepted by the accounting lead on the held-out month, with exceptions correctly routed and no suppressed exception. Hosting, authenticated identity, per-client secret reference, production persistence, backup and restore tested. Provider capability verified against current documentation for each read operation. Written authorisation naming provider, account, data scope, environment and cost ceiling. | Reading named data from named systems into the client's isolated environment | Any write; any schedule beyond what is separately authorised |
| **G3 Separately authorised writes** | G2 stable over representative cycles. For each write operation: durable intent before dispatch, stable operation id, provider idempotency where available, read-back verification, unknown-outcome reconciliation, and a tested revocation path. Human approval bound to the exact payload. Written authorisation per operation type. | The specific write operations authorised, under approval | Any other write; payments; final close |
| **G4 Operating handoff** | Theresa completes her assigned workflow from the guide without step-by-step help and explains escalation. Observed unattended runs within mandate, with exceptions raised and none missed. Measured review, correction and maintenance effort. Support split agreed with Jeff and, if purchased, the accounting co-management scope. Human release decision. | Operation of the demonstrated workflow scope | Wider scope, new clients or new capabilities without returning to the relevant gate |

---

## 10. Implementation batches

Detail, acceptance criteria and tests for each ticket are in `FABLE_IMPLEMENTATION_BACKLOG.json`.

| Batch | Objective | Tickets | Completion gate |
| --- | --- | --- | --- |
| **1. Control integrity and state over time** | Make the stated review control true, and make state survive a second period and a recurring run | T-01 to T-08 | All 41 existing tests pass or are deliberately changed with the reason in `DECISIONS.md`. FV-C15, FV-R01, FV-R03, FV-R04, FV-RC01 and FV-RC02 report FIXED. Zero UNEXPECTED. Probes P01 to P06, P09 to P11, P14 and P16 are passing unit tests. |
| **2. Accounting substance** | Policy approval, exceptions, proposed entries, source lifecycle, completeness, journal controls, finalization | T-09 to T-19 | FV-J08 to FV-J10 and FV-CL02 report FIXED. A full synthetic month reaches finalized and locked without database edits. Gate G0 criteria met. |
| **3. First new capabilities and reliability** | Card reconciliation, settlement pairing, trial-balance intake, AP bill preparation, runtime hardening | T-20 to T-27 | Each new capability passes its FV specifications and adversarial tests before its status changes. No connector exists. |

**Codex can implement now on synthetic data:** every ticket in Batches 1 and 2, and T-20 to T-22 and T-24 to T-27 in Batch 3.

**Must wait for client facts or authorisation:** entering any real identity, chart, mapping, threshold, tolerance or authority grant; T-23 (AP) beyond a synthetic specification until question 12 is answered; AR and reporting modules; anything under gates G1 to G4; every connector, schedule, model call and write.

---

## 11. Stack limits and migration triggers

The Python standard library, SQLite and static front end are adequate for Batches 1 to 3. I do not recommend a rewrite. The limits to plan for:

| Limit | Why it is acceptable now | Migration trigger |
| --- | --- | --- |
| SQLite, one writer at a time (`BEGIN IMMEDIATE`) | One process, fixture volumes | More than one worker process, or more than one real client on one deployment |
| Isolation by a `scope` column in one file | Synthetic data only | First real client data: use one database per client, or a server database with row-level security and per-client credentials |
| Python 3.9 | It is what the machine has | Any hosted use: 3.9 is past its end of life; move to a supported release first |
| `http.server` and a role selector | Loopback demo, refused elsewhere | Any second user or any non-loopback access: authenticated identity behind the F-23 interface |
| Local file backup | Synthetic data | Real evidence: encrypted backups, restore drills, retention policy |
| Hash chain inside the same database | Inspection aid | Any external reliance on the audit trail: anchor or retain it outside the operator's control |

The repository seam is clean enough (`storage.py` is 123 lines and handlers never touch it) that a later move is a contained task, provided the lease, transaction and isolation tests are re-run against the new store.

---

## 12. Answers to the handoff's "decisions to critique"

- **Does the common model support the full cycle without card assumptions in the core?** The runner does. The state model does not: single period, client-wide currency, no entry, no exception entity. `card_accounts` and the receipt policy boolean are card assumptions in the profile schema, and `core.money` carries a USD assumption.
- **Is the shared-versus-client separation sufficient?** The file split is right. The lifecycle is missing (F-06), and three client policies are in shared code (F-16).
- **Are mandates, occurrences, holds and approvals sufficient for routine autonomy?** Not yet. F-07, F-08 and F-17 mean recurring work is self-authorised and can silently not happen. Stale carry-forward is unguarded because nothing binds an occurrence to a period or to fresh evidence.
- **Is exact alias proposal safe when every item still gets human review?** Yes as a proposal mechanism, after F-03. A reusable rule for a real client should require several reviewed examples, confirmation of the vendor's nature, conditions on activity type and amount, an effective date and an approver who is not the proposer. Multi-purpose merchants should never map by name alone.
- **Is item-level blocking appropriate?** Yes. Package-level blocks should apply to: statement balance or population breaks (per account), an unbalanced or untied trial balance, an opening-balance break, and missing client facts.
- **Is duplicate flagging without suppression sufficient?** For preparation, yes. It needs the disposition model in §7.2 to be usable.
- **Is the single structured receipt useful?** As a first demonstration, yes. Evolve by: binding documents to items by reference; allowing several documents under an approved policy; adding allocation lines for splits as a disposition; and treating authenticity as unverified until a document source is connected.
- **Which demo assumptions look like doctrine?** Exact receipt date; one receipt per charge; calendar-month control period; payments summed with purchases; two-decimal money; `receipt_required` as a single boolean.
- **Which tests most efficiently falsify the architecture?** A second period (F-04), a recurring run with late evidence (F-08), a self-approval through a colleague (F-01), and a month that must be completed end to end (F-10). All four are in the reviewer cases.

---

## 13. Standards references

These are cited from my own knowledge to anchor vocabulary. They were not re-fetched for this review; confirm wording before relying on any of them. None is asserted to apply to Bird Bowl, whose framework and basis are unknown.

- **Segregation of duties as a control activity:** COSO, *Internal Control — Integrated Framework* (2013), Control Activities component, Principle 10. Basis for F-01, F-06 and F-07.
- **Assertion vocabulary (completeness, cutoff, accuracy, occurrence, classification):** AICPA AU-C Section 315. Used here to name control objectives, not to imply an audit.
- **Cash, tax and other non-GAAP bases as special purpose frameworks:** AICPA AU-C Section 800. Basis for treating "accounting basis" as a required client fact (F-14, FV-AP05).
- **Foreign currency transactions:** FASB ASC 830 under US GAAP; IAS 21 under IFRS. Relevant only when a foreign charge is handled (F-20).
- **Currency minor units:** ISO 4217 (for example, JPY has none and KWD has three).
- **Capitalisation of property and equipment:** FASB ASC 360 under US GAAP; for US tax, Treas. Reg. §1.263(a)-1(f) (de minimis safe harbor) and §1.263(a)-3. Relevant to question 8 only if those regimes apply.
- **Revenue and receivables:** FASB ASC 606 under US GAAP; IFRS 15. Relevant only if AR is in scope.

---

## 14. The first implementation batch for Codex

Implement Batch 1 in this order. Do not start Batch 2 until the Batch 1 gate is met.

1. **T-01 Adopt the reviewer suite and exact assertions.** Add `FABLE_VALIDATION_CASES.json` and its runner to the repository and to `make test`; change `issubset` to equality in `tests/test_validation.py`; add probes P01 to P16 as unit tests marked as expected failures.
2. **T-02 Fix vendor normalisation** (F-03).
3. **T-03 Enforce review independence** with actor kind and artifact contributors (F-01).
4. **T-04 Separate occurrences from runs**, re-dispatch held occurrences, record skips, isolate unfit mandates (F-08, F-17).
5. **T-05 Introduce accounting periods** as records with status, bind runs and sources to a period, remove the period from the profile (F-04).
6. **T-06 Scope the input manifest** to what each capability reads within its period, and narrow the code hash to handler and invariant files (F-05, parts 1 and 2).
7. **T-07 One governing artifact per item and a decision state machine** (F-02).
8. **T-08 Bring the documents into line with the code** (F-22), and record each deliberate contract change in `DECISIONS.md`.

**Gate:** existing tests pass or are deliberately changed with a recorded reason; reviewer runner shows FV-C15, FV-R01, FV-R03, FV-R04, FV-RC01 and FV-RC02 as FIXED with zero UNEXPECTED; the remaining four fail-until-fix cases (FV-J08, FV-J09, FV-J10, FV-CL02) are still reported as KNOWN-FAIL and belong to Batch 2.
