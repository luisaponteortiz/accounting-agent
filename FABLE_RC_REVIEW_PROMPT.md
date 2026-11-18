# Independently verify the RC/PRV correction checkpoint

Review FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip as a new checkpoint. This is a request for independent verification, not authorization to implement, accept human G0, open G1–G4 or Batch 3, implement deferred/Proposed scope, connect, spend, call paid models, send, post, pay, host or deploy. Use local fictional data and temporary databases only. Keep the delivered archive and all original review inputs immutable; use disposable extracted copies.

Verify the adjacent bundle SHA-256 and every payload hash in REVIEW_MANIFEST.json. Confirm that both returned response ZIPs retain SHA-256 0562869ad210b4b3b8653b4600bc7f3b863f283e8087029c6b19719497a5f399 and d4c5795dfce0ab9584c53c874efb4693e3473d3dadfa37a0d3b1be89bf03d826. The baseline V2 correction ZIP must retain 00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d; all older archives/sidecars and supplied reviewer inputs must be unchanged. Compare against docs/corrections_rc/input-checksums.json and the comprehensive inventory. The three historical Git commits were not rewritten; their hashes are recorded in docs/corrections_rc/git-history-final.txt. Git metadata is excluded from the bundle.

Read these authorities before judging the fix:

1. CODEX_RC_CORRECTIONS_PROMPT.md, exports/FABLE_RB_ACCEPTANCE/FABLE_RB_CORRECTIONS.json and FABLE_RB_ACCEPTANCE_REPORT.md.
2. The unchanged exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py and supplied output.
3. exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json, especially the seven conclusions and all ten current_gaps.
4. docs/corrections_rc/RC_CORRECTIONS_REPORT.md, raw logs/exit metadata, changed-files.json and source-and-tests.patch. Developer passing results are claims to reproduce, not independent acceptance.

Verify RC-01, RC-02 and RC-03 in that order, together against all exact ticket assertions and regression variants. In particular:

- RC-01: withdrawal after the lock, fresh and late links; replacement and receipt held under the locked origin; blocked move with had_approval; withdrawal visible in state.source_exceptions; only terminal replacement released on reopen; destination revisions remain in the destination after relock.
- RC-02: late middle link, terminal eligible and already approved; descendants and receipts re-evaluated; approval/event/move history retained; only terminal replacement on reopen. The new regression found an additional cause of its reopen assertion failing: earlier settlement_verified acceptance survived expanded ancestry. Inspect the existing-payload transition_refs binding and activation comparison in exceptions.py. A changed chain must lapse prior acceptance without rewriting the old decision. Unchanged chains must add no duplicate binding, move or accounting-event rows. No schema change was made.
- RC-03: unresolved claims link when targets arrive without claimant re-delivery, including a claimant already replaced; newest-first multi-link arrival; ordinary open-period resolution clears the unresolved blocker; pending claims must not close a cycle.

Run, unmodified:

```sh
python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
make rb-gate
make rc-gate
python3 scripts/check_product_requirements.py --json
python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
```

Require exit 0, exact 18 new probe IDs, sixteen OK and NOTE only for N02c and N04e. The earlier script must retain exactly fourteen OK. The normal tests and rc-gate must mechanically enforce the new contract. No API/probe adaptation was made. Require 29 PASS / 10 FIXED / 21 DEFERRED-OK in the reviewer gate and U4 as the sole NOTE identity in the older acceptance gate. Compare every V2 test method and require all earlier test files byte-identical except the explicitly assigned additive tests/test_product_requirements.py extension. Preserve all its earlier methods; no skip or expected-failure marker may hide a correction. The source patch and inventory name every difference.

Reproduce every PRV acceptance criterion independently:

- PRV-01: BNK-03, CTL-04, GOV-03 stay Verification failed for RC-01–03; criteria include all three delivery orders. Four verified records cite Fable's actual V2 checkpoint/report/probes with UC-10 and UC-11 limits. Only your new independent results may change the three failed verdicts. Do not equate developer passes with acceptance.
- PRV-02/03: nonexistent test paths, bare tickets and arbitrary tokens fail; a real declared probe is allowed. Inspect the seven immutable-report-backed JSON conclusions. Reject developer promotion of a failed verdict and self-asserted independent verification without a matching existing report entry/checkpoint.
- PRV-04/10: shared HTML contains client-neutral content, including the formerly hard-coded client panel. Client-specific terms come from the client section. Check all fields except Trace, retaining only GOV-01, ARC-04 and KNO-01 boundary exceptions; shared Python/web files also fail injected client names/person names. Demo/config/fixtures remain exempt.
- PRV-05/06/08: no unconditional Approved-to-Proposed dependency; tested states cannot depend unconditionally on Deferred/Not started; condition must follow its own requirement ID. All instantiation references remain. The six unratified shared requirements remain Proposed. No Dependencies field contains stray dot-semicolon punctuation.
- PRV-07: each EXC Scope note begins with its fixed disposition phrase and agrees with the table.
- PRV-09: every payload difference against V2 is listed or covered by an explicit manifest/envelope/self-artifact rule, including exports/ and START_HERE.md. Check hashes and source/tests patch reproducibility.

F21, F22, F23, F25, F26, F30, F31, F33b, F33c and F35 must be rejected. Check the entire 37-case fault output and all make-check mutations; the unchanged copy and exempt demo must pass. Do not edit the supplied fault script to accommodate a change. If a case mutates a now-different record and changes meaning, report it explicitly.

PR-11 was already confirmed by the user as product owner and accounting lead (D-016), then synchronized at the user's instruction (D-017). The pre-pass working register hash was a149f9008ca6c648df258a842f66d29c28ac66be4aed4f635090eb7fac3fb624. Preserve that confirmation: AAOS-BB-01/02 differ from that version only in Dependencies. Inspect pre-existing-owner-changes.patch and owner-wording-preservation.json. Do not request confirmation again or treat it as G0/G1/Batch 3 authority.

Keep UC-10/N02c and UC-11/N04e as policy observations; no fix is assigned. Retain U4's accepted visible non-restoration behavior, the earlier seven adaptations, strengthened RT14b and five statement setups. Preserve disclosed historical full-script incompatibilities; developer evidence marks whether the older literal full commands were run this pass. Synthetic controls establish no client accounting policy, reconciliation completion, close or human operating readiness.

Return a report, machine-readable verdicts, any corrective tickets and raw evidence. State exactly what you executed, exit codes/environment, what you inspected only and what is NOT_RUN. Name the exact bundle hash and scope for every independent conclusion. Do not modify the supplied source or independent-input folders while reviewing; propose further corrections separately.
