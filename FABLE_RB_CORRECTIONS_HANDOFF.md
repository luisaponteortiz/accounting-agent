# Independently verify the RB and product-register corrections

Start with [FABLE_RB_REVIEW_PROMPT.md](FABLE_RB_REVIEW_PROMPT.md), the exact current prompt included in the V2 review bundle. V2 adds that prompt and administrative packaging documentation to the already tested correction response; runtime source, tests, fixtures, reviewer scripts and gate assertions are unchanged. The prior correction archive and frozen submission remain preserved. The prompt-packaging addendum records this difference; new packaging checks are not new accounting-test or independent-acceptance claims.

This is a new correction response to exports/FABLE_RA_ACCEPTANCE/FABLE_RA_CORRECTIONS.json and exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json. The submitted combined bundle remains frozen at SHA-256 b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea; the returned response ZIP remains unchanged at d38e0e27b30e46d2e4690b5366aa3fa237d5733e23783c64082c39ca4ff30f84. Source/tests in this new outer project are the correction response; nested archives are immutable historical evidence, not the current executable source.

Read docs/corrections_rb/RB_CORRECTIONS_REPORT.md, PR_DISPOSITION.md, execution-results.json, changed-files.json and both source/documentation patches. Compare the actual code against the frozen combined checkpoint's source plus documentation addendum, not merely developer descriptions. Original independent inputs and all acceptance assertions remain unchanged.

Run from this new extracted project root, using disposable fictional data:

```sh
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
make rb-gate
python3 scripts/check_product_requirements.py --json
```

Also run the unchanged latest independent script directly:

```sh
python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
```

All 14 probes must report OK, including R04c; none is allowed to remain NOTE. Old acceptance U4 remains the previously allowed NOTE in its own retained gate. Historical full-original setup incompatibilities remain disclosed and are not relabeled passing. No new adaptation was made to the 14-probe script. The five prior statement setups were independently accepted in the returned review.

Challenge RB-01 late links and later-resolved chains, including an already approved destination, source/support quarantine, removal from governing population, accounting events, blocked move history, authorized reopen, terminal-only release, relock, restart and unchanged root history. RB-02 must cover re-pointed keys for receipts and statements in addition to withdrawals; both suppliers are refused, independent acceptance remains separate from final review and further changes lapse it. RB-03 must preserve semantic authors across item scope and renamed keys without barring unrelated scopes/aliases/categories/values. RB-04 must disclose prior-statement revisions, remain unverified with partial/no prior acceptance, verify only after all own-period relying items have active acceptance and re-block after revocation/new evidence. Frozen locked-period statement lookback remains unchanged.

Review the 88-record register and all PR-01–PR-17 dispositions. The original 76 IDs remain. Every record has one product decision and implementation state, a scope/evidence note and Needed for classification. Seven records retain Verification failed because developer repairs are not independent acceptance. The new shared lifecycle/connector/summary/deposit/consolidation details remain Proposed; exclusions/reservations and owner decisions are explicit. No future feature is claimed delivered. Fault-test the repeatable register gate and confirm client-specific facts do not constrain shared modules. Current AGENTS.md has one marked authorization paragraph.

Return independent verdicts separately for RB-01–RB-04, PR corrections/remaining product decisions, retained controls and G0 technical criteria. Include exact commands/versions/exits/raw evidence and new reproducible probes, with prioritized implementable tickets for confirmed failures. Distinguish code defects, documentation defects, unverified observations, intentionally deferred capabilities and client/product decisions. Do not modify supplied inputs or implement fixes during review. Passing tests or review does not grant human G0, G1–G4, Batch 3, client-data access, posting, payments, sending, paid services or deployment authority.
