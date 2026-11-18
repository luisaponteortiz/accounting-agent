# Fable independent reverification

The exact prompt to send with this bundle is `FABLE_REVERIFICATION_PROMPT.md` at the project root. It requests independent verdicts, adversarial probes, all-case results, and prioritized implementable corrections.

Review C-01–C-06 first, then the assigned Batch 2 T-09–T-19 controls. This bundle contains actual source, regressions, execution logs, a diff against the delivered Batch 1 source, and the frozen corrective checkpoint. Do not treat passing fixture tests as actual accounting acceptance or authorize any live action.

## Reproduce the corrective checkpoint exactly

The frozen archive exports/FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip was created after C-01–C-06 passed and before any Batch 2 code was written. Run:

```sh
python3 scripts/verify_corrective_checkpoint.py
```

This extracts that archive to a temporary directory and runs the exact supplied unmodified exports/FABLE_BATCH_1_VERIFICATION/batch1_verification_probes.py against its code. Expected: N01–N07 OK and Corrective gate PASS. Its then-deferred Batch 2 cases remain deferred in that historical checkpoint. See docs/corrections/baseline-probes.txt, final-probes.txt and docs/batch2/checkpoint-rerun.txt. All four original supplied inputs are unchanged; docs/batch2/input-checksums.json records checksums.

## Verify current Batch 2 source

```sh
make test
make check
make batch2-gate
python3 review/run_fable_validation_cases.py . review/FABLE_VALIDATION_CASES.json --batch2-gate
python3 review/batch2_verification_probes.py .
python3 scripts/synthetic_month.py
```

Tests need temporary loopback-port access for the HTTP server. No model, connector or external service is needed. Each run creates temporary fictional databases; existing project accounting records are not modified.

Current setup intentionally differs from the pre-Batch-2 script: registration is proposed-only; grants and independent profile/mandate approval are explicit; statements are structured fictional specifications; ordered inputs state as_of; historical lock scenarios explicitly acknowledge unsettled work. The unmodified pre-Batch-2 script assumes immediately active policy/mandates and cannot represent those new contracts. It has not been edited to hide this incompatibility.

review/batch2_verification_probes.py is a maintained harness with those setup adaptations. The corrective adversarial assertions are retained. Additional implemented probes for ordering, journal substance, close outcomes, statement identity, receipts, lock preconditions, item contributors, revoke recovery and future policy are now gated. Review this adaptation independently; do not rely solely on our gate label. tests/test_corrective_gate.py includes it in ordinary tests. The four supplied files and original reviewer scripts are preserved separately.

The maintained 60-case suite now expects 29 PASS, 10 FIXED and 21 DEFERRED-OK. FV-CL04 is newly executable; its wrong-period document is both missing current-period evidence and a disclosed quarantine. FV-C13 expects a superseded pending authorization in immutable history/links, not the active population. FV-J05/J07 explicitly specify quarantine and lock-dispatch behavior. Receipt mismatches under absent policy now use policy-unset codes. The test-only statement adapter is clearly fictional and never runs in intake.

## Review priorities and requested return

1. Try to defeat locked-origin movement, locked decisions, identity kind, Unicode marks, rejection preservation and historical/item/configuration authorship. Include alternate source kinds, replays, recurring actors and resolved disputes.
2. Review policy/effective-date and standing-authority controls. Proposed decisions must remain inert; no synthetic fixture helper may be reachable through an HTTP auto-approval/grant path.
3. Validate disposition effects, shared-entry derivation, origin collision holds, statement population evidence and journal support/duplicate/no-effect rules. Check that an explicit external referral never clears its underlying blocker.
4. Verify finalized payload/hash stability, post-finalization event visibility, acknowledgement content, and period-specific close outcomes. Identify any route that can cleanly approve a held item or displace a prior rejection without accounting change.
5. Re-run the teaching-month walkthrough and two-client isolation check; distinguish preparation handover from an actual completed close. Human G0 acceptance remains pending.

Return a PASS/FAIL per C ticket and Batch 2 acceptance criterion, minimal reproducible probes for any failure, prioritized corrective tickets with exact acceptance assertions, and accounting questions that require client authority. Separate current defects from explicitly deferred Batch 3 work. Do not suggest activating AP/AR, live connections, posting, payments or deployment as part of this reverification.

Source comparison: docs/batch2/source-and-tests.patch and changed-files.json. These compare against exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip, not a nonexistent tracked Git baseline. The new archive contains complete runnable files and REVIEW_MANIFEST.json with verified SHA-256 hashes; it excludes runtime databases and credentials.
