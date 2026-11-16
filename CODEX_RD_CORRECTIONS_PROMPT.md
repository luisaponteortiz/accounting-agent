# Correct RD-01, RD-02 and PRV-11 to PRV-13, and return a new review bundle

Fable's independent review of your RC/PRV correction bundle is back. RC-01, RC-02 and RC-03 were accepted: every assertion in the three tickets held in an independent run, nothing regressed, and all earlier tests and archives are intact. PRV-01 to PRV-10 were accepted too. RB-01 as a whole was not. The requirement says "regardless of arrival order", and two delivery orders that no ticket named still leave one charge approved in locked November and again in open December. Those are RD-01 and RD-02, both P1, and they are the only things standing between this checkpoint and G0 technical criteria. Neither is a regression; both are in the V2 source as well. I am authorizing one correction pass for the two RD tickets and for PRV-11 to PRV-13. Batch 3, every deferred capability and all live actions stay closed.

## Where the review is

Everything is in the working project under `exports/FABLE_RC_ACCEPTANCE/`, and also in `exports/FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip` (SHA-256 `1c47259742cfed78a2dcd2059c8cdadb72787df208d9d9232ddd8946bcfcbc23`). Verify that hash before you start. The reviewed bundle was `9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454`.

Read these first, in this order:

1. `exports/FABLE_RC_ACCEPTANCE/FABLE_RC_CORRECTIONS.json`. This is the authority for the work: each ticket has the source lines, a minimal reproduction, expected and actual behaviour, the smallest correction, dependencies and exact acceptance assertions. The three register gaps are under `register_and_check_gaps`.
2. `exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md` for the reasoning.
3. `exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py` and `fable_rc_acceptance_output.txt`. Probes X01, X01d and X02 are the three failures. Q01, Q02, Q02i and Q03 restate the RC ticket assertions one by one and must keep passing.
4. `exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py` and `evidence/order-search-rc-source.txt`. This tries 120 delivery orders of one replacement chain. On your bundle 18 end in double approval.
5. `exports/FABLE_RC_ACCEPTANCE/evidence/fable-rc-register-faults.txt` and the script that produced it, `evidence/scripts/fable_rc_register_faults.py`. The four cases marked GAP are what PRV-12 and PRV-13 refer to.

Treat the folder and the response ZIP as immutable inputs, the same way you treated the earlier review files. Do not edit, rename or regenerate anything in them. Everything that was immutable in the last pass still is.

## What the two defects have in common

A replacement claim can exist in three forms: a link row, an "unresolved" event tied to one snapshot, or nothing but the stored packet. The quarantine decision reads only the first, and RC-03 taught it to read the second for the snapshot that is still current. RD-01 and RD-02 are the two cases left over:

- **RD-01.** A row already admitted to December is sent again, byte for byte unchanged, now saying it supersedes a row that has not arrived yet. Unchanged bytes return early from `source_revision`, before the line that records the unresolved claim, so the claim exists only in the stored packet. When the target arrives later and is held, the claimant is not. If a reviewer had already approved the claimant, that approval stands and December finalizes with no further decision.
- **RD-02.** A row with an unresolved claim gets a newer version that does not repeat the claim: an amount correction, or an unchanged re-send after the row was retired by its own replacement. The recorded claim points at the old snapshot and is never linked. A recorded link, by contrast, belongs to the row's identity and survives a revision. Fable notes that the "claimant snapshot is still the head" condition came from its own RC-03 correction text, so do not read this as a criticism of how you implemented it.

Do RD-01 first, then RD-02. They change the same function and share one lookup, so deliver them together.

## How to work

Reproduce before you change anything. On the unmodified source:

- `python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .` should give 12 OK, 3 WEAK (X01, X01d, X02), 1 NOTE (X08) and exit 1.
- `python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py .` should give 120 runs, 18 double and exit 1. It takes a few minutes.

Keep the raw output of both. Then write your own failing unit tests for each ticket, including the variants listed under `regression_tests`, and keep the before-and-after evidence.

Fable tried a combined correction in a throwaway copy and recorded it in `exports/FABLE_RC_ACCEPTANCE/evidence/experimental-correction-rd.patch`. In that copy the 16 new probes gave 15 OK and X08 NOTE, the order search gave 0 of 120, the 18 and 14 earlier probes were unchanged, all 192 tests passed and the four gates it ran exited 0. Use it as a worked reference, not as the answer. It was never reviewed as a fix, it has no unit tests of its own, and it groups claims with SQLite `json_extract`, which you may prefer to do in Python. If you find a cleaner design that meets the same assertions, prefer it and say why.

Four things are easy to get wrong, and the probes will catch most of them:

- Recording the claim must be idempotent. The first unchanged re-send with a claim creates one new version and one unresolved event. Sending the same claim again while it is still unresolved must add no snapshot, binding, move, link or event and must answer `changed: False`. Write a unit test for this; no supplied probe asserts it directly.
- The state between the claim and the arrival of its target. Once the claim is recorded, the claimant must show both transition blockers, and an earlier approval of it must stop governing, before the target ever arrives. Test the eligible and the already approved claimant. After the target arrives, X01d expects an approved-source event naming the December approval and ITEM_LEFT_POPULATION, with no approval decision deleted.
- The no-op rule from RC-02 still applies. An intake that does not touch a chain adds nothing for it. Probes Q02i and N01f check this, including after a release and relock.
- Resolving a claim by identity must not close a cycle and must not link a row whose identity already has a link. Probes Q03 and R01d must stay OK.

X08 is expected to stay NOTE. It is a feed-policy question (UC-14), not a defect, so do not "fix" it. The same goes for N02c and N04e.

The RC-02 re-evaluation step covers card transactions only. Leave it that way in this pass. If, while reading, you conclude that a journal can stand in a replacement chain across a lock in the same way, report it with the evidence and do not extend the fix.

No historical snapshot, decision, package or audit record may be rewritten. If you believe a schema change is needed, stop and explain before making it.

## What done looks like

- `fable_rc_acceptance_probes.py` runs unmodified and exits 0 with the exact 16 probe ids, 15 OK, NOTE for X08 only, no WEAK and no ERROR.
- `fable_rc_order_search.py` runs unmodified and exits 0 with 120 runs and 0 double.
- `fable_rb_acceptance_probes.py` still exits 0 with 16 OK and NOTE for N02c and N04e only. The 14-probe script still reports 14 OK. Both unmodified.
- `make test`, `make check`, `make batch2-gate`, `make reverification-gate`, `make acceptance-gate`, `make rb-gate` and `make rc-gate` all pass. Reviewer cases stay at 29 PASS / 10 FIXED / 21 DEFERRED-OK, and U4 remains the only NOTE in the older acceptance gate.
- Both new scripts are wired into `make test` and into a new gate target that enforces the exact contract above. If an API change makes a probe unrunnable, do not adapt it silently: return the adapted probe with a diff and an explanation for review.
- All 192 test methods of the reviewed checkpoint are still present. No earlier test file is modified except by adding methods. No skip or expected failure hides a corrected defect.
- Each PRV gap meets the acceptance criteria written for it in the corrections file.

## Register and project documents

Apply PRV-11 in the same change, because AGENTS.md requires the register to follow every independent result:

- AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 stay at Verification failed. Say that RC-01 to RC-03 were independently accepted at checkpoint `9a85c78a…2454`, cite RD-01 and RD-02 in their scope notes and evidence, and extend the two acceptance criteria with the two delivery orders in the wording the ticket gives. Your own passing tests do not raise these records; only the next independent review can.
- In AAOS-CTL-09, replace "RC transition-chain acceptance binding is developer-tested only" with the independent result: probe Q02 at checkpoint `9a85c78a…2454`. The other three verified records need no change.
- Update `docs/INDEPENDENT_VERIFICATION_RESULTS.json` from the `register_verdicts` list in `exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json`. Keep the seven entries in their current order; Fable's fault script addresses two of them by position.
- Keep the PR-11 confirmation as it stands. AAOS-BB-01 and AAOS-BB-02 were verified identical to my confirmed wording except for the Dependencies corrections you were assigned. Do not reword them, and change no implementation state or gate because of the confirmation.
- The working register's SHA-256 is `d55063e25857b2a66606f8e2a255ccf68e427b330d6cba97bde79ad014a663f9`, the same file as in your bundle. Verify it and build on it.
- Update the register's Current evidence section and the T-12, RA-01 and RB-01 crosswalk rows, record the contract changes in DECISIONS.md, update PROGRESS.md, and replace the current-authorization paragraph in AGENTS.md with this pass.

I have not ratified AAOS-ONB-01, ONB-02, INT-07, GL-06, BNK-07 or RPT-03. Leave all six Proposed.

I have also not decided the feed question behind these tickets: whether a provider may deliver a replacement, or its claim, before the row it replaces, and whether a later version of a row that omits an earlier claim withdraws it. Until I do, implement the stronger control, which is that the claim is recorded and persists. Record that as the reason in DECISIONS.md and decide nothing on my behalf.

## PRV-12 and PRV-13

Do these after the RD tickets pass, so that a problem here cannot hold up the P1 work. Both are P3.

- **PRV-12.** `docs/INDEPENDENT_VERIFICATION_RESULTS.json` is an ordinary project file, so editing it together with the register passes the check. Fable's cases G16, G17 and G18 show three ways. Make the check read each verdict from the reviewer's own machine-readable files: `register_verdicts` in `exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json`, and the seven earlier conclusions in `exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json`, with the later review winning for a record named in both. Pin the hashes of those reviewer files in the protected-input list for this pass, and fail when the project's results file disagrees with them, omits one of their records, or adds a record they do not name.
- **PRV-13 (optional).** Removing the client's name from the Client-specific terms line goes unnoticed (case G44). Either require the list to contain the client's display name as it appears in the client section heading, or tell me why you would leave it.

Add your own fault tests to `tests/test_product_requirements.py` for each new rule, and check that the current register still passes after your edits. Then run both of Fable's scripts unmodified:

- `python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .` must still report 37 agree and 0 gaps.
- `python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py <disposable-copy>` should now reject G16, G17 and G18, and G44 if you do PRV-13. Point it at a clean extracted copy of your new bundle and never at the working folder: it writes into the copy it is given and restores each file afterwards.

Both scripts mutate specific records and specific phrases. If one of your register edits makes a case behave differently, report which case and why instead of editing the script.

## What to return

Build a new bundle under a new label. Never overwrite an earlier archive, sidecar or manifest. These must all keep their hashes: the frozen combined submission (`b154db10…f61ea`), the first review response (`d38e0e27…30f84`), the V2 correction bundle (`00a13d93…be001d`), the two V2 review responses (`0562869a…5f399` and `d4c5795d…3d826`), your RC/PRV bundle (`9a85c78a…2454`) and the new review response (`1c472597…bc23`). The three commits must not be rewritten. The working project is now on branch `review/fable-rc-acceptance`; stay on it, and add no commit unless I ask.

Include:

- a correction report with one row per ticket, RD and PRV alike: what changed, where, and which tests, probes or fault cases cover it;
- raw logs and exit codes for every command above, with environment and versions, plus the pre-correction reproduction of both new scripts;
- a complete change inventory against your RC/PRV bundle, and a source-and-tests patch against it;
- a manifest with SHA-256 for every file, and the bundle's own SHA-256 in a sidecar;
- a short handoff and an exact prompt for Fable's next independent verification.

Report plainly. Say which results you ran yourself, mark anything you could not run as NOT_RUN with the reason, and do not describe developer passes as independent acceptance. If an assertion in the tickets turns out to be wrong or unreachable, say so and show the evidence instead of working around it.

## Limits

Local, fictional data and temporary databases only. No live connections, client records, paid services or model calls, sending, posting, payments, hosting or deployment. Do not begin Batch 3, implement any Proposed register record, redesign the product or change the stack. Passing tests do not grant human G0, G1–G4, Batch 3 or operating authority.
