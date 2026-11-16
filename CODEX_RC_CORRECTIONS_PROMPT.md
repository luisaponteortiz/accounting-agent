# Correct RC-01 to RC-03 and PRV-01 to PRV-10, and return a new review bundle

Fable's independent review of your RB correction response is back. RB-02, RB-03 and RB-04 were accepted. RB-01 was not: the two reproductions in the original ticket now pass, but three other delivery orders still leave one charge approved in locked November and again in open December. Those are RC-01, RC-02 and RC-03, all P1, and they are the only things standing between this checkpoint and G0 technical criteria. The register corrections were accepted, with ten smaller gaps, PRV-01 to PRV-10. I am authorizing one correction pass for the three RC tickets and the ten PRV gaps. Batch 3, every deferred capability and all live actions stay closed.

## Where the review is

Everything is in the working project under `exports/`, and also in `exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_RESPONSE.zip` (SHA-256 `0562869ad210b4b3b8653b4600bc7f3b863f283e8087029c6b19719497a5f399`). Verify that hash before you start.

Read these first, in this order:

1. `exports/FABLE_RB_ACCEPTANCE/FABLE_RB_CORRECTIONS.json`. This is the authority for the work: each ticket has the source lines, a minimal reproduction, expected and actual behaviour, the smallest correction, dependencies and exact acceptance assertions.
2. `exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md` for the reasoning.
3. `exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py` and `fable_rb_acceptance_output.txt`. Probes N01b, N01c and N01d are the three failures.
4. `exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json`: the section on the seven failed records and all ten entries under `current_gaps`. Each gap has its evidence, a proposed correction and acceptance criteria.
5. `exports/FABLE_RB_ACCEPTANCE/evidence/register_fault_tests_output.txt` and the script that produced it, `evidence/scripts/register_faults.py`. The ten cases marked GAP are what PRV-02, 03, 06, 07 and 10 refer to.

Treat all of these as immutable inputs, the same way you treated the earlier review files. Do not edit, rename or regenerate anything in those two folders or the response ZIP.

## What the three defects have in common

The engine decides whether a source is held behind a locked period only at the moment that source is taken in, and only by looking at links that already exist. Each ticket is a case where the facts change afterwards and nobody asks again:

- **RC-01.** The locked charge is withdrawn by the feed after the lock. `source_origin` skips an ancestor whose head is removed, but this removal was itself quarantined and the charge is still approved in the locked population. Fable notes that the "head is not removed" condition came from its own RB-01 correction text, so do not read this as a criticism of how you implemented it.
- **RC-02.** A link is declared late on a middle source. That source is quarantined correctly, but its replacement, already admitted to December, is never re-evaluated. This one was held in the frozen combined submission by a side effect, so in outcome it is a regression.
- **RC-03.** A replacement arrives before the row it replaces. The claim is recorded only as an event, no link is written when the target later arrives, and a further replacement inherits a chain that stops short of the locked root.

Do them in the order RC-01, RC-02, RC-03. RC-03 relies on the re-evaluation step RC-02 introduces. All three touch the same two functions, so deliver them together.

## How to work

Reproduce before you change anything. Run `python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .` on the unmodified source and keep the raw output; you should see 13 OK, 3 WEAK, 2 NOTE and exit 1. Then write your own failing unit tests for each ticket, including the variants listed under `regression_tests`, and keep the before-and-after evidence.

Fable tried a combined correction in a throwaway copy and recorded it in `exports/FABLE_RB_ACCEPTANCE/evidence/experimental-correction.patch`. In that copy the 18 new probes, all retained gates and the 174 tests passed. Use it as a worked reference, not as the answer. It was never reviewed as a fix, it has no unit tests of its own, and it leaves out one part of RC-01: listing a withdrawal quarantined under a lock in `state.source_exceptions`. If you find a cleaner design that meets the same assertions, prefer it and say why.

Three things are easy to get wrong, and the probes will catch them:

- The reopen-then-relock path. After a valid release and relock, a later revision of the destination must stay in the destination. RC-01's reopen change exists to protect this; probes R01a and N01a check it.
- Re-evaluating chained sources on every intake must be a no-op for a source whose situation has not changed: no new binding rows, no move rows, no duplicate events. Probe N01f checks the open-period case.
- Resolving a pending claim must not close a supersession cycle. Probe R01d must stay OK.

No historical snapshot, decision, package or audit record may be rewritten. If you believe a schema change is needed, stop and explain before making it.

## What done looks like

- `fable_rb_acceptance_probes.py` runs unmodified and exits 0 with no WEAK and no ERROR. N02c and N04e are expected to stay NOTE; they are policy questions, not defects, so do not "fix" them.
- The earlier 14-probe script still reports 14 OK, unmodified.
- `make test`, `make check`, `make batch2-gate`, `make reverification-gate`, `make acceptance-gate` and `make rb-gate` all pass. Reviewer cases stay at 29 PASS / 10 FIXED / 21 DEFERRED-OK, and U4 remains the only NOTE in the older acceptance gate.
- The new probe script is wired into `make test` and into a gate target that requires exit 0, the exact 18 probe ids, OK for sixteen of them and NOTE for N02c and N04e only. If an API change makes a probe unrunnable, do not adapt it silently: return the adapted probe with a diff and an explanation for review.
- Every earlier test method is still present and no original test file is modified. No skip or expected failure hides a corrected defect.
- Each PRV gap meets the acceptance criteria written for it in the PR corrections file. `make check` passes on the corrected register and fails for fault cases F21, F22, F23, F25, F26, F30, F31, F33b, F33c and F35, and when the first client's name is added to a file under `accounting_agent/web/`.

## Register and project documents

Apply PRV-01 in the same change, because AGENTS.md requires the register to follow every independent result:

- AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay at Verification failed. Cite RC-01 to RC-03 in their scope notes and evidence, and extend the two acceptance criteria with the three arrival orders. Your own passing tests do not raise these records; only the next independent review can.
- AAOS-KNO-04, AAOS-CTL-01, AAOS-BNK-02 and AAOS-CTL-09 may be recorded as Independently verified. Cite Fable's RB report, the reviewed bundle hash `00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d` and the probes named in the PR corrections file. Write UC-10 into the AAOS-CTL-09 scope note and UC-11 into AAOS-BNK-02.
- Carry D-016 into the register. I have confirmed PR-11 in writing as both product owner and accounting lead, and DECISIONS.md already records it as D-016; keep that entry as written. In AAOS-BB-01 and AAOS-BB-02, cite D-016, state that procedure capture outside the application before G1 is confirmed, and name December 2026 as the designated held-out month, with December cases and their expected results kept separate from the November teaching examples. Update the matching row of the open-decision table. This confirmation grants no source access, G0 acceptance or G1 authorization, so change no implementation state or gate because of it.
- Update the register's Current evidence section and the T-12, RA-01 and RB-01 crosswalk rows, record the contract changes in DECISIONS.md, update PROGRESS.md, and replace the current-authorization paragraph in AGENTS.md with this pass.

## PRV-02 to PRV-10

Do these after the RC tickets pass, so that a problem here cannot hold up the P1 work. They are all P3. The corrections file gives the detail; what follows is the intent and the boundaries.

The register check (`scripts/check_product_requirements.py`) currently lets through things AGENTS.md forbids. Tighten it so the rules are enforced by `make check`, not by good faith:

- **PRV-02.** Evidence for a tested state must name something real: a `tests/test_*.py` file that exists, or a probe id that appears in a probe script under `exports/` or `review/`. A ticket id alone is not evidence.
- **PRV-03.** Add a small machine-readable file of independent verification results (record id, state, report path, bundle hash), written only from independent reports. The check fails if a record listed there as failed carries a higher state, or if a record claims Independently verified without an entry whose report exists. Its first entries are the seven conclusions from this review, which is why PRV-01 comes first.
- **PRV-06.** Apply the unconditional-dependency rule to Not started as well as Deferred, and require the condition phrase to follow the record id, so that the word "only" elsewhere in a clause does not count. For AAOS-GOV-02 and AAOS-ARC-01, mark their dependency on AAOS-GOV-01 conditional. Do not raise AAOS-GOV-01's state to make the problem go away unless you can cite named tests for it.
- **PRV-07.** State the disposition of each AAOS-EXC record in a fixed phrase at the start of its scope note and have the check compare it with the scope table.
- **PRV-10.** Apply the client-boundary rule to every field of shared records except Trace, with the client-specific words taken from the client section, not a hard-coded list. AAOS-GOV-01, AAOS-ARC-04 and AAOS-KNO-01 remain the allowed boundary records.

Then the documentation and one code item:

- **PRV-04 (code).** `accounting_agent/web/index.html` line 12 still says "Bird Bowl — fictional sandbox" for every client. Make it client-neutral or fill it from the state the page already loads, and extend the `make check` guard to `accounting_agent/web/`. The demo and config files stay exempt.
- **PRV-05.** Thirteen Approved records list a Proposed record as a dependency because "is the first instance of" was written as "depends on". Record instantiation separately, or mark those dependencies "if ratified", and add a check that an Approved record does not depend unconditionally on a Proposed one. I have not ratified AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 or RPT-03, so leave all six Proposed and decide nothing on my behalf.
- **PRV-08.** Clean the stray punctuation in the thirteen Dependencies fields.
- **PRV-09.** Make the change inventory cover every file that differs from its baseline, including `START_HERE.md` and anything added under `exports/`, either by listing it or by a stated rule.

Add your own fault tests to `tests/test_product_requirements.py` for each new rule, and check that the current register still passes after your edits. Then run Fable's script unmodified: `python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .`. All ten GAP cases should now be rejected. The script copies the whole project tree to a temporary directory eleven times to test `make check`, so point it at a clean extracted copy of your new bundle if the working folder is large. Your register edits may make one of its other cases behave differently, because the script mutates specific records; if so, report which case and why instead of editing the script.

## What to return

Build a new bundle under a new label. Never overwrite an earlier archive, sidecar or manifest; the frozen combined submission (`b154db10…f61ea`), the first review response (`d38e0e27…30f84`), the V2 correction bundle (`00a13d93…be001d`) and the new review response (`0562869a…5f399`) must all keep their hashes. Include:

- a correction report with one row per ticket, RC and PRV alike: what changed, where, and which tests, probes or fault cases cover it;
- raw logs and exit codes for every command above, with environment and versions, plus the pre-correction reproduction;
- a complete change inventory against the V2 correction bundle, and a source-and-tests patch;
- a manifest with SHA-256 for every file, and the bundle's own SHA-256 in a sidecar;
- a short handoff and an exact prompt for Fable's next independent verification.

Report plainly. Say which results you ran yourself, mark anything you could not run as NOT_RUN with the reason, and do not describe developer passes as independent acceptance. If an assertion in the tickets turns out to be wrong or unreachable, say so and show the evidence instead of working around it.

## Limits

Local, fictional data and temporary databases only. No live connections, client records, paid services or model calls, sending, posting, payments, hosting or deployment. Do not begin Batch 3, implement any Proposed register record, redesign the product or change the stack. Passing tests do not grant human G0, G1–G4, Batch 3 or operating authority.
