# Independent re-verification of Accounting Agent OS: RV-01–RV-17

Act as an independent senior accounting architect, accounting-controls reviewer, and technical verification engineer. Review the attached `FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip`. Independently decide whether the corrections satisfy your acceptance assertions and preserve C-01–C-06 and Batch 2 T-09–T-19. Treat Codex's reports and passing tests as claims to investigate.

Accounting Agent OS is a general reusable accounting execution platform across GL, AP, AR, banking/reconciliation, month-end close and reporting/analysis. Bird Bowl is its first client implementation. The executable scope remains fictional card/journal preparation and close readiness. Do not redefine the product around cards, activate deferred modules, or review executive/marketing/sales agents. Actual Bird Bowl policies, accounts, vendors, systems, records and reviewer authority remain unknown.

Use temporary fictional databases and explicit service operations. Synthetic profile/rule/mandate approvals needed for verification are permitted within those disposable fixtures. Do not connect client systems, call paid models/services, post entries, execute payments, deploy, incur costs, activate real client policy or grant real operating authority. Preserve original review inputs and archives. Do not implement application fixes during verification; put your new probes and outputs in separate files.

## 1. Establish the checkpoint

Extract the outer archive and run from its project root. Keep an untouched extraction. Historical nested ZIPs are not current source.

Read first:

- `exports/FABLE_REVERIFICATION/FABLE_REVERIFICATION_CORRECTIONS.json`, including order and exact assertions.
- Its companion report, results, original probes, raw output, and `evidence/` files. All 22 supplied files should be unchanged.
- `FABLE_RV_CORRECTIONS_HANDOFF.md` and `docs/REVERIFICATION_CORRECTIONS_REPORT.md`.
- `docs/reverification/probe-adaptations.md` and `docs/reverification/reverification-probe-adaptations.patch`.
- `docs/reverification/rt14b-positive-preconditions.patch`, the prior adapted script in `docs/reverification/before-rt14b-strengthening/`, and the strengthened-probe/fault-test logs in `docs/reverification/`.
- `PROGRESS.md`, `DECISIONS.md`, `docs/CONNECTION_READINESS.md`, `docs/ARCHITECTURE.md`, and `docs/CAPABILITY_CONTRACTS.md`.
- Original C-01–C-06 review inputs in `exports/FABLE_BATCH_1_VERIFICATION/` and T-09–T-19 acceptance criteria in `review/FABLE_IMPLEMENTATION_BACKLOG.json`.

Verify REVIEW_MANIFEST.json, preservation hashes in `docs/reverification/input-checksums.json`, and unchanged nested archives. The current correction diff/inventory in `docs/reverification/` uses the actual reviewed `FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip` as baseline. The corrected cumulative inventory in `docs/batch2/` uses the Batch 1 archive and must include changed JS/HTML/CSS. Independently compute missing/extra files and hashes; hash agreement is not evidence of correct controls.

Codex claims it reproduced the original 21 OK / 11 WEAK / 3 NOTE before source changes, implemented in order RV-04, RV-03, RV-01, RV-02, RV-05, RV-06, then RV-07–RV-17, and retained all 41 platform/HTTP methods from the Batch 1 baseline. Distinguish the initial archive's 40 and reviewed Batch 2 checkpoint's 43 methods, which must also remain retained. Inspect both baseline and final evidence and every deliberate fixture/assertion change. Do not infer chronology from a final archive alone.

## 2. Execute gates and scrutinize the compatibility exception

Run with Python 3.9+ and temporary loopback access for HTTP tests:

```sh
make test
make check
make batch2-gate
make reverification-gate
python3 scripts/synthetic_month.py
python3 scripts/verify_corrective_checkpoint.py
```

Expected developer results are 136 passing tests; 60 reviewer cases comprising 29 PASS, 10 FIXED and 21 DEFERRED-OK; 28 unchanged-setup original probes OK; and 35 OK through a separate setup adaptation. No NOTE, WEAK or ERROR is accepted by the adapted gate. Report all 60 IDs separately. DEFERRED-OK means the unavailable operation was refused, not that its future accounting behavior passed.

Also run the exact supplied full command:

```sh
python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .
```

**Codex discloses that this still exits 1**, with RN02/RN03/RN07 ERROR and RT12a/RT14a/RG0 WEAK. It claims required RV-11/12/15 contracts invalidate seven old positive setups, including RT14b's otherwise vacuous positive path. Do not hide this result, assume the adaptation is acceptable, or change expectations merely to obtain PASS.

Inspect `scripts/build_reverification_adapter.py`, the exact patch, and `review/fable_reverification_probes.py`. Decide whether the corrections JSON's API-change exception is justified for each of these changes:

- RN02/RN03 replace forbidden empty freshness with an explicit reasoned no-evidence mandate, retaining their original independent human approval. RN07 makes the human preparer's proposal valid with that explicit reason, then deliberately requires service approval to fail with 403; this mandate is not independently approved in that setup. No grant or actor is added. RT10b's negative empty predicate must remain unchanged and fail intake.
- RT12a/RG0 must first assert the revised-evidence hold and history, then explicitly accept changed support through a granted non-supplier; final approval remains independent.
- Positive distinct-purchase setups in RT14a/RT14b/RG0 cite every candidate's support. Strengthened RT14b now asserts that both initial disposition calls succeed and D1 exists and is eligible before D3 is constructed or intaken. Its original final verdict remains unchanged. Two fault-injection regressions require it to abort if either initial call is refused or starting D1 is ineligible. Inspect those tests and the full seven-probe explanation in docs/reverification/probe-adaptations.md. RT14d's own-row-only evidence remains refused.

The generator claims all original verdict-return and gate expressions are AST-identical. Verify that and look for hidden helper changes, skipped tests, fabricated authority, ignored blockers or unconditional eligibility. The 28 unaffected probes must execute directly from the original file. Carry all invariants into your own independently constructed valid-positive/invalid-negative scenarios. If a reported OK is caused by an unrelated refusal, record failure or inadequate evidence.

Return a separate acceptance judgment for each of RN02, RN03, RN07, RT12a, RT14a, RT14b and RG0. For strengthened RT14b, inspect `tests/test_reverification_gate.py`, especially `test_RT14b_fails_when_either_initial_disposition_is_refused` and `test_RT14b_fails_when_initial_D1_is_ineligible`. Independently force a refusal of D1, a refusal of D2, and an ineligible initial D1 through test-only substitutions. Each must abort before D3 arrives, with AssertionError becoming ERROR/nonzero exit in the runner. Then demonstrate the valid path: both initial calls succeed, D1 is eligible, D3 arrives, and D1 becomes ineligible with POSSIBLE_DUPLICATE. Keep the original final verdict and original supplied script unchanged.

Record exact commands, exit codes, versions, stdout/stderr and environment restrictions. If a check cannot execute, report NOT_RUN; distinguish source inspection, delivered logs and your own runs. Without make, run unittest discovery and scripts/check.py, then each command declared in the Makefile gates. The historical corrective verifier must continue to run the unmodified script against its frozen archive; its N01–N07 passing does not establish current-source acceptance.

## 3. Verify every correction and surrounding invariant

Use the JSON's full assertions and dependencies. In particular challenge:

- RV-04: later-month intake causes no false late-receipt/package events; genuinely changed locked evidence still quarantines.
- RV-03/RV-01: tombstones, moves and envelope/data supersession remove old governing membership without deleting history. New-key supersession from locked origin stays quarantined with its support, preserves origin approval until reopen, records approved-source events, then releases routing with no dual governing approval. Removed items appear in immutable packages and exceptions become superseded.
- RV-02: one origin identity retains ownership across cosmetic versions and supersession; stale origin refs hold and current refs do not erase a double-entry conflict.
- RV-05/RV-06: withdrawn profile mappings retire only through independent approval and correct effective dating; historical mappings remain reproducible and reintroduction works. Typed reconciliation/tie-out requirements cannot be completed by document labels; legacy strings remain unsatisfied.
- RV-07: payments cannot become expense credits, expense coding cannot name cash/liability, and settlement/transfer/fee/interest choices obey activity and account types. External referral never grants eligibility.
- RV-08/RV-09: distinct decisions bind exact candidates even without statement evidence. Excluding one duplicate gives the survivor a truthful evidence-bound path, carries all relevant contributors, and revocation restores holds. Re-enqueue after reversal must produce a current projection while retaining the original rejection where content is identical.
- RV-10: cosmetic aliases/policies retain relevant historical rule authors; genuinely different historical categories do not create unrelated review bans. Preserve item-specific evidence independence and explicit human actor kind, Unicode combining marks and ambiguity controls.
- RV-11: malformed/empty freshness is refused; explicit no-evidence authority is independently approved and audited. Legacy empty authority suspends. Freshness recovery, occurrence/run separation, caps, expiry, policy dependency, restart and concurrency still work.
- RV-12: changed support discloses old/current refs, suppliers and fields and creates a hold. Suppliers cannot accept their revisions, nor can dispositioners perform final independent review. Bound acceptances become stale when support changes again. Receipt referrals preserve unresolved accounting impact.
- RV-13: statements disclose identity, continuity and provenance assurance. Missing IDs require an applicable independently approved exception; missing expected prior evidence holds; a quarantined prior statement cannot replace the admitted/frozen one. Manual statement provenance is not independent authentication.
- RV-14/RV-15: approvers see normalized aliases/collision IDs/effective retirement. Own-row evidence is insufficient; distinct decisions prove all candidates and propagate supplier provenance.
- RV-16/RV-17: runtime/test inventories are complete. New packages name predecessors; UI/export identify one governing version while historical hashes remain fixed. Acknowledgement cannot bypass stale/disputed/package controls or constitute final close.

Recheck scoped reads/jobs/exports, immutable accounting and audit records, locked decisions, role/grant enforcement, close concurrency, typed deferred boundaries, and all C/T acceptance criteria. Avoid accepting a system that merely denies every operation. Preserve actual working independent preparation approvals.

UC-2 and UC-3 have claimed coverage within these changes; verify it. UC-1, UC-4 and UC-5 remain unverified concerns, not fixes. Probe them if feasible and classify reproducible defects separately from unresolved concerns/deferred enhancements. Do not turn a newly confirmed in-scope bypass into an acceptable deferral.

## 4. Judge teaching-month and readiness evidence honestly

The delivered service-only walkthrough now preserves TX-009's original 79.99 receipt and refers its mismatch. Expected: ten approvals; three held dispositions (TX-007 pending, TX-009 mismatch, TX-011 FX); October TX-008 and receipt quarantined and named; two immutable preparation handovers; acknowledged November lock; second-client December isolation. Independently recompute approved impact: office supplies +311, repairs +200, card liability −211, cash −300, net zero.

The adapted RG0 follows the other RV-12 route, explicitly accepts revised support and retains its original eleven-approval / office-supplies 391 assertions. Verify both paths and their full histories. Do not confuse their results or count a referral as accounting approval. Decide separately whether the technical evidence satisfies the original G0 criteria; human G0 acceptance remains separate. G1–G4, live connections, posting, payments, final close and production readiness remain closed.

## 5. Return evidence Codex can implement from

Return together, without overwriting the supplied originals:

1. `FABLE_RV_ACCEPTANCE_REPORT.md`: separate PASS/FAIL/NOT_VERIFIED decisions for RV-01–RV-17, current C-01–C-06, Batch 2, each of the seven probe adaptations, strengthened RT14b and G0 technical criteria. Lead with confirmed blockers. Include per-assertion evidence, accounting consequences, execution limits and next authorized boundary.
2. `FABLE_RV_ACCEPTANCE_RESULTS.json`: every RV assertion, original failed ID, C/T criterion, all 60 case IDs, teaching-month/isolation checks, and G0. Preserve raw statuses alongside your judgment; include exact commands, exits and evidence links.
3. `FABLE_RV_CORRECTIONS.json`: prioritized confirmed defects with stable IDs, P0–P3, affected requirement, source/function/line, minimal reproduction, expected/actual behavior, consequence, smallest sufficient correction, dependencies/order, exact assertions/tests and any client-authority decision. Separate unverified concerns and deferred work. Return an empty confirmed-defect list if appropriate.
4. `fable_rv_acceptance_probes.py`: independent runnable probes taking the project root, explicit synthetic authority/evidence, no database edits to manufacture successful outcomes, nonzero exit on gate failure.
5. `fable_rv_acceptance_output.txt` and supporting evidence: raw commands, versions, exits, stdout/stderr, scripts and any justified test-only adaptations.

Return concrete acceptance or corrective findings. No project-concept redesign or feature expansion is requested. Passing developer tests alone is insufficient; so is claiming failure solely because a correctly refused deferred capability is unavailable.
