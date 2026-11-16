# Correct RF-01 to RF-03, apply PRV-16, and return a new review bundle

Fable's independent review of your RE/PRV correction bundle is back. RE-02 (clause 7, with D-029), RE-03 (clauses 8 and 9), PRV-14 and PRV-15 were accepted: every assertion held in Fable's own probes, no held row was released without authority in any delivery order, and the frozen-period boundary behaves as I decided in D-029. Your reported results reproduced, all 205 earlier test methods, 16 archives and 719 protected inputs are intact, and the patch reproduces your source exactly.

RE-01 was not accepted. One branch records a claim without applying it, and with one more ordinary delivery the same charge ends approved in locked November and approved and finalized in open December (RF-01, P1). That breaks the promise of D-026, so RB-01 as a whole is still not accepted. Two smaller tickets came with it (RF-02 and RF-03, both P3).

This pass corrects those three tickets and nothing else. The feed contract does not change. Batch 3, every deferred capability and all live actions stay closed.

## Where the review is

Everything is in the working project under `exports/FABLE_RE_ACCEPTANCE/`, and also in `exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip` (SHA-256 `e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a`). Verify that hash before you start. The reviewed bundle was `4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae`.

Read these first, in this order:

1. This prompt. Where it differs from the review's ticket file, this prompt governs. The differences are listed under "My decisions on the tickets".
2. `exports/FABLE_RE_ACCEPTANCE/FABLE_RE_CORRECTIONS.json`: source lines, minimal reproductions, expected and actual behaviour and acceptance for RF-01, RF-02 and RF-03, and the observations.
3. `exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md` for the reasoning.
4. `exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py` and `fable_re_acceptance_output.txt`. C2d and C2f are the failure; C9h is RF-02; C9c and C9g are observations.
5. `exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py` and `evidence/step-search-older-resent-with-claim.stdout.txt`: 480 delivery orders with an approval attempt after every delivery, 40 of which end in a double approval on your bundle.
6. `exports/FABLE_RE_ACCEPTANCE/evidence/http-setup-timing.txt` and the four `make test` logs under `evidence/commands/` for RF-03.

Treat the folder and the response ZIP as immutable inputs. Do not edit, rename or regenerate anything in them. Everything that was immutable in the last pass still is.

## The contract stands

D-026 and D-029 are unchanged and are not to be rewritten, reworded or re-recorded. No clause is added. Record your implementation notes for this pass as a new entry appended to DECISIONS.md, and mark it as a developer record, not an owner decision.

## The three tickets

Do them in this order.

- **RF-01 (P1), clause 2.** As written in the ticket file. In `accounting_agent/feed_contract.py`, `card_source_revision`, an older or conflicting message that matches a snapshot already retained has its claim recorded and is then returned without the claim being applied. The `supersedes` field sits outside the row data, so the same older message with and without the claim has the same data hash and takes this branch. Probes C2d and C2f; search family `older-resent-with-claim`.
- **RF-02 (P3), clause 9.** After a second person records a confirming selection of the same target, the first selector, whose decision created the governing link, is no longer a contributor and can approve the row. Probe C9h.
- **RF-03 (P3).** `make test` passed in one of Fable's three unmodified runs. In the other two the five-second worker deadline in the class setup of the unchanged `tests/test_http.py` expired and its eleven methods did not run. In a diagnostic copy with only that deadline widened, the setup needed 4.84 seconds. The same setup needs about four seconds on your RD source.

## My decisions on the tickets

- **RF-01.** Fable's one-line patch (`evidence/experimental-correction-rf01.patch`) is a worked reference, not a required design. Whatever you choose must also satisfy the "also consider" note in the ticket: there must be no card row left with a declared first claim whose target is on file and no link. Add a test of that as an invariant across your own delivery matrices, not only for this one path.
- **RF-02 is to be fixed, not accepted as policy.** Every person who has recorded a target selection for a row, or for a row earlier in its chain, remains a contributor of that row and of its live replacements, whether a later selection confirmed theirs or replaced it. Earlier selection records stay as they are. Do not change the rule for ordinary dispositions.
- **RF-03: the deadline stays.** Do not edit `tests/test_http.py`. Bring the setup cost back to no more than your RD source needs when measured the same way (about four seconds on this machine; `evidence/scripts/http_setup_timing.py` is the measurement Fable used), and tell me the setup time inside the full suite. If you cannot do that without weakening a control, or five consecutive runs still do not pass, stop and explain; I will then decide whether to widen the deadline. That fails in the safe direction.
- **UC-17, UC-18 and UC-20 are not in this pass.** Leave the behaviour as it is: a de-selected first target stays retired, an exact batch replay leaves no supplier record, and a live replacement of a waiting claimant carries only the ordinary transition blocker. Record all three as open observations for my decision, alongside U4 and UC-14. Probes C9c and C9g are expected to stay NOTE.

## How to work

Reproduce before you change anything. On the unmodified source:

- `python3 exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py .` should give 21 probes: 16 OK, 3 NOTE (C9c, C9g, C9h), 2 WEAK (C2d, C2f), and exit 1.
- `python3 exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py .` should give 480 runs, 40 double, 0 released, 0 audit failures, and exit 1. All 40 are in the family `older-resent-with-claim`. It takes about twenty minutes; `--family NAME` runs one family.

Keep the raw output of both. Then write your own failing unit tests for each ticket, and keep the before-and-after evidence.

Five things are easy to get wrong:

- **Applied means the whole of clause 2 and clause 4.** For a known target the link is made and the row, its live replacements and their receipts are held if the chain reaches a locked period. For an unknown target the row waits as unresolved and links when the target arrives, without being re-sent.
- **An approval given earlier stops governing at once.** In C2f a replacement row was approved before the claim arrived. That approval must stop governing when the claim is recorded, not at the next preparation.
- **Idempotence is unchanged.** Repeating the claim-carrying older message afterwards answers `changed: False` and adds no source snapshot, binding, move, link or accounting event.
- **Clause 7 still applies first where it should.** If the row already has a different claim, the late claim is a second claim: recorded, not applied. C2c checks this and must stay OK.
- **Do not buy speed with a skipped check.** Any shortcut for RF-03 must give the same result as the full computation for every state, including rows with claims, links and selections. Show how you tested that.

X08, N02c, N04e, U4, C9c and C9g are expected to stay NOTE. Do not fix them.

The contract covers card transactions only. Leave journals as they are. UC-9 stays a reading-only concern.

No historical snapshot, decision, disposition, package or audit record may be rewritten. If you believe any ticket needs a schema change, stop and explain before making it.

No retained test, probe or fault case may be adapted in this pass. If one turns out to conflict with a correction, do not change it. Report which one and why.

## What done looks like

- `fable_re_acceptance_probes.py .`, unmodified, exits 0 with 21 probes: 19 OK, and C9c and C9g NOTE.
- `fable_re_step_search.py .`, unmodified, exits 0 with 480 runs, 0 double, 0 released and 0 audit failures.
- `fable_rd_acceptance_probes.py . Y01 Y02 Y03 Y04 Y06 E01 E02 E03 E03c E04 E05 E06` still exits 0 with 12 OK; your adapted Y05 still reports OK and is byte-identical to the one in your RE bundle; `fable_rd_order_search.py` still gives 336 runs and 0 double.
- The RC script still gives the exact 16 ids, 15 OK and X08 NOTE; the RC search still gives 120 runs and 0 double; the RB script still gives 16 OK with N02c and N04e NOTE; the RA script still gives 14 OK. All unmodified.
- `make check`, `make batch2-gate`, `make reverification-gate`, `make acceptance-gate`, `make rb-gate`, `make rc-gate`, `make rd-gate` and `make re-gate` all pass. Reviewer cases stay at 29 PASS / 10 FIXED / 21 DEFERRED-OK, and U4 remains the only NOTE in the older acceptance gate.
- `make test` passes in five consecutive complete runs on an otherwise idle machine. Keep all five logs, and report the HTTP class setup time measured inside the full suite.
- Fable's probe script is wired into `make test` and into a new gate target, `make rf-gate`, which also runs the 480-order search. Because the search takes about twenty minutes it belongs to the gate only. The gate enforces the exact contract above, and `make test` carries fault tests of its validators of the kind you wrote for `make re-gate`: non-zero exit; a missing, duplicated, unknown or extra probe; a changed verdict, including a NOTE that becomes OK or an OK that becomes NOTE; a missing, duplicated or extra order; a double or released order; an altered summary line.
- All 227 test methods of the reviewed checkpoint are still present and unchanged. No earlier test file is modified except by adding methods. No skip or expected failure hides a corrected defect.
- Your own unit tests cover, at least:
  - RF-01 with a known and an unknown target, for an eligible and an already approved row, with and without a live replacement, with the replacement approved before and after the claim, and with the claim-carrying message repeated;
  - the invariant named under my decision on RF-01;
  - RF-02 with a confirming selection and with a replacing selection, for the row, a revision of the row and a live replacement;
  - RF-03 as an equivalence test of any shortcut against the full computation.

## Register and project documents

Apply PRV-16 in the same change:

- AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay at Verification failed. Say that RE-02, RE-03, PRV-14 and PRV-15 were independently accepted at checkpoint `4890b297…98ae` and cite RF-01. Your own passing tests do not raise these records; only the next independent review can.
- Do not change any acceptance criterion. The D-026 and D-029 wording in BNK-03 and CTL-04 stands as Fable verified it.
- Add `exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json` (key `register_verdicts`) and `FABLE_RE_ACCEPTANCE_REPORT.md` to the pinned reviewer inputs as the fourth authority, the latest verdict winning per record, and update `docs/INDEPENDENT_VERIFICATION_RESULTS.json` from the four files. Keep the seven entries in their current order.
- The working register's SHA-256 is `97876af92ef2d6e1daba18fd8a846a27d180613884f652bcc3211dfa8e28c34c` and DECISIONS.md is `cef283d295970010028b9cff76866073a3e79301ac1d30d9575b4ceb0b079626`, the same files as in your bundle. Verify both and build on them.
- Update the Current evidence section and the T-12, RA-01 and RB-01 crosswalk rows, update PROGRESS.md, and replace the current-authorization paragraph in AGENTS.md with this pass.
- Keep the PR-11 confirmation as it stands. Do not reword AAOS-BB-01 or AAOS-BB-02. I have still not ratified AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 or RPT-03; leave all six Proposed.
- Confirm that `register_faults.py` still reports 37 agree and `fable_rc_register_faults.py` on a disposable copy still reports 44 agree.
- Run `fable_rd_register_faults.py` and `exports/FABLE_RE_ACCEPTANCE/evidence/scripts/fable_re_register_faults.py` unmodified on a disposable copy and report the exact output. Both were written when an earlier review was the latest authority, so some of their cases will now disagree. Say which and why. Do not weaken latest-wins to satisfy them, and write your own fault tests for the fourth authority.

## What to return

Build a new bundle under a new label. Never overwrite an earlier archive, sidecar or manifest. Every archive listed in `docs/corrections_re/archive-integrity.json` must keep its hash, and so must your RE/PRV bundle (`4890b297…98ae`) and the new review response (`e0b0a499…cf2a`). No existing commit may be rewritten. The working project is on branch `review/fable-rc-acceptance`. Record its head and commit count before you start and leave both unchanged. Stay on the branch, and add no commit unless I ask.

Include:

- a correction report with one row per ticket: what changed, where, and which tests, probes or search results cover it;
- raw logs and exit codes for every command above, with environment and versions, plus the pre-correction reproduction of both Fable scripts and all five `make test` runs;
- a complete change inventory against your RE/PRV bundle, and a source-and-tests patch against it;
- a manifest with SHA-256 for every file, and the bundle's own SHA-256 in a sidecar;
- a short handoff and an exact prompt for Fable's next independent verification. It should ask Fable to look for any other path on which a claim is recorded without being applied, to extend the order search beyond these four families, and to re-run `make test` several times.

Report plainly. Say which results you ran yourself, mark anything you could not run as NOT_RUN with the reason, and do not describe developer passes as independent acceptance. If a ticket turns out to be wrong, unreachable or in conflict with a control that is already verified, say so and show the evidence instead of working around it.

## Limits

Local, fictional data and temporary databases only. No live connections, client records, paid services or model calls, sending, posting, payments, hosting or deployment. Do not begin Batch 3, implement any Proposed register record, redesign the product or change the stack. Passing tests do not grant human G0, G1–G4, Batch 3 or operating authority.
