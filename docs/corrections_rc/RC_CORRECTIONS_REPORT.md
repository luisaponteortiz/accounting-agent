# RC/PRV developer correction report

16 November 2026. One authorized correction pass: RC-01, RC-02, RC-03, then PRV-01–PRV-10. All data and databases were fictional/local. No schema, stack, deferred/Proposed capability, live integration or operating authority changed. All results below were executed by Codex as developer validation; independent acceptance of this checkpoint is pending.

The three required preflight hashes matched before project edits. The unchanged probe script reproduced exit 1 with 13 OK / 3 WEAK / 2 NOTE (N01b/N01c/N01d failed). Final developer results: **192 tests OK; 16 OK / 2 expected NOTE in the exact 18-probe set; 14 retained probes OK; all required gates exit 0; reviewer cases 29 PASS / 10 FIXED / 21 DEFERRED-OK; all 37 register fault cases agree, zero gaps.** The ten specified GAP cases and shared-web injection are rejected.

## Corrections and coverage

| Ticket | Change | Files | Tests / probes / fault cases |
| --- | --- | --- | --- |
| RC-01 | Removed ancestor remains blocking only while its withdrawal is quarantined under a still-locked period; reopen admits that withdrawal. Expose it in state.source_exceptions. | accounting_agent/source_control.py; service.py | test_RC01_withdrawal_then_fresh_or_late_claim_and_relock; N01b, R01a, N01a; retained R01b/R01c/A01/X01 |
| RC-02 | Rebind live transaction chains shortest-first after changed intake, before receipts. Bind transition acceptance to exact resolved ancestry so expanded chains need fresh acceptance after reopen. | source_control.py; service.py; exceptions.py | test_RC02_middle_late_link_rechecks_eligible_and_approved_terminal; test_RC02_unchanged_chain_adds_no_bindings_moves_or_accounting_events; N01c, N01f, N01a/N01e/R01a–R01d |
| RC-03 | Resolve current-head pending claims when targets arrive, including removed claimants; refuse cycles; stop reporting linked claims unresolved. | source_control.py; service.py | test_RC03_pending_claim_resolves_before_or_after_claimant_is_replaced; test_RC03_open_target_clears_unresolved_without_quarantine; test_RC03_pending_cycle_is_not_linked; N01d/N01e/R01c/R01d |
| PRV-01 | Record seven actual independent conclusions; retain three failures and precise RC delivery orders; four prior-V2 verified scopes retain UC-10/UC-11. Update Current evidence and T-12/RA-01/RB-01 crosswalk. | docs/PRODUCT_REQUIREMENTS.md; INDEPENDENT_VERIFICATION_RESULTS.json | make check; register counts; seven report-backed entries; owner-wording-preservation.json |
| PRV-02 | Require existing tests/test_*.py or an exact probe ID declared in a probe script; ticket IDs and arbitrary tokens are insufficient. | scripts/check_product_requirements.py | test_PRV02_nonexistent_test_ticket_and_arbitrary_token_are_rejected; F21/F22/F23 rejected; real R01a positive |
| PRV-03 | Use independent-report conclusions, report hashes and bundle checkpoints; block promotion of failed verdicts and unbacked independent claims. | docs/INDEPENDENT_VERIFICATION_RESULTS.json; register checker | test_PRV03_failed_verdict_cannot_be_promoted; test_PRV03_self_asserted_independent_verification_is_rejected; F25/F26 rejected |
| PRV-04 | Neutralize both header and client panel; extend shared-source guard recursively through web assets, retaining demo/config/fixture exemptions. | accounting_agent/web/index.html; scripts/check.py; register checker | test_PRV04_shared_web_and_python_are_checked_but_fixtures_are_exempt; unchanged Fable make-check web/person injections rejected, exempt demo accepted |
| PRV-05 | Mark Proposed dependency references if ratified and retain shared instantiation citations. No product proposal is ratified. | docs/PRODUCT_REQUIREMENTS.md; register checker | test_PRV05_approved_cannot_depend_unconditionally_on_proposed; 77 Approved/9 Proposed/2 Rejected unchanged |
| PRV-06 | Enforce adjacent conditional phrases after each own dependency ID, for Deferred and Not started dependencies of implemented/tested states. GOV-02/ARC-01 depend conditionally on GOV-01; GOV-01 stays Not started. | register checker; docs/PRODUCT_REQUIREMENTS.md | test_PRV06_unstarted_or_deferred_dependency_needs_local_condition; F33b/F33c rejected, F33 accepted |
| PRV-07 | Start all EXC scope notes with Rejected scope. or Reserved action. and require agreement with the disposition table/product decision. | register checker; docs/PRODUCT_REQUIREMENTS.md | test_PRV07_scope_disposition_must_match_table; F35 rejected |
| PRV-08 | Clean dot-semicolon punctuation from the thirteen Dependencies fields and reject recurrence. | docs/PRODUCT_REQUIREMENTS.md; register checker | test_PRV08_stray_dependency_punctuation_is_rejected; make check |
| PRV-09 | Inventory every payload difference versus V2, including START_HERE and exports, with explicit self-artifact/manifest/envelope rules. Preserve original tests and pre-existing owner changes. | scripts/build_rc_review_bundle.py; changed-files.json; source-and-tests.patch | inventory preparation/preservation assertions; final manifest/CRC/hash and extracted-copy checks |
| PRV-10 | Read names/client-only choices from the client section; apply boundaries to all shared fields except Trace, retaining three allowed boundary records. Shared source guard uses the same list. | register checker; client terms in docs/PRODUCT_REQUIREMENTS.md | test_PRV10_every_shared_field_except_trace_uses_client_section_terms; F30/F31 rejected; dynamic added-term and Trace positives |

## Design and before/after evidence

The fix follows the experiment's narrow use of existing append-only links, bindings and events; a schema redesign offered no benefit for this assignment. The pending-claim lookup directly selects the current claimant head, including a removed head. The experiment was a worked reference, not accepted fix evidence. Two required additions are explicit: withdrawal disclosure in source_exceptions, and exact-chain transition-acceptance binding. No historical snapshot, decision, package or audit row is rewritten.

The six new RC methods were run against unmodified source first: seven subtest failures across the ticket variants, with idempotence and cycle positives retained (rc-unit-before.*). RC-01 then passed its fresh/late and relock regression. RC-02's first rebind fix held descendants, but its stronger reopen assertion still failed in both terminal-approval variants: prior settlement_verified acceptance suppressed the fresh transition hold (rc02-unit-after.* and rc-unit-after.*). The existing disposition payload now records transition_refs and activation compares it with the resolved chain. Changed ancestry, or a legacy decision without that binding, requires a new acceptance; the old decision remains immutable. All six methods pass in rc-unit-final.*, and the unchanged probes pass in rc-probes-after.*. This extra exceptions.py change is within RC-02's exact reopen assertion and is shown in the patch and D-019.

The restricted full run could not bind the HTTP server to 127.0.0.1 (also isolated in loopback-sandbox-probe.*). Its nonzero output is preserved. A complete rerun with temporary local-port access passed all 192 methods, including all eleven HTTP methods; no skip or expected failure hides a defect. Early inventory attempts also caught nonportable Finder metadata and two local synthetic backup databases in the new preservation list. Those are retained unchanged in the working tree and explicitly excluded from the portable input list/payload; no review file or prior archive was removed. All attempts remain in the raw evidence.

## Command evidence

Each command's combined stdout/stderr is in the linked .txt; adjacent JSON records exit code, working directory, elapsed time and environment where captured. Common environment: Python 3.9.6, SQLite 3.51.0, GNU Make 3.81, macOS 26.5.2 (x86_64). Gates ran in disposable copies because batch2-gate regenerates a historical report; the working historical evidence was preserved. tested-source-sha256.json confirms current runtime/test/gate sources match the complete-test copy.

| Command / stage | Exit | Raw output |
| --- | --- | --- |
| environment: `python3 --version` | 0 | [environment.txt](environment.txt) |
| fable-register-faults: `python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .` | 0 | [fable-register-faults.txt](fable-register-faults.txt) |
| final-acceptance-gate: `make acceptance-gate` | 0 | [final-acceptance-gate.txt](final-acceptance-gate.txt) |
| final-authorization-doc-check: `make check` | 0 | [final-authorization-doc-check.txt](final-authorization-doc-check.txt) |
| final-batch2-gate: `make batch2-gate` | 0 | [final-batch2-gate.txt](final-batch2-gate.txt) |
| final-check: `make check` | 0 | [final-check.txt](final-check.txt) |
| final-current-check: `make check` | 0 | [final-current-check.txt](final-current-check.txt) |
| final-full-tests: `make test` | 0 | [final-full-tests.txt](final-full-tests.txt) |
| final-rb-gate: `make rb-gate` | 0 | [final-rb-gate.txt](final-rb-gate.txt) |
| final-rc-gate: `make rc-gate` | 0 | [final-rc-gate.txt](final-rc-gate.txt) |
| final-register-counts: `python3 scripts/check_product_requirements.py --json` | 0 | [final-register-counts.txt](final-register-counts.txt) |
| final-register-release-check: `make check` | 0 | [final-register-release-check.txt](final-register-release-check.txt) |
| final-reverification-gate: `make reverification-gate` | 0 | [final-reverification-gate.txt](final-reverification-gate.txt) |
| full-tests-sandbox: `make test` | 2 | [full-tests-sandbox.txt](full-tests-sandbox.txt) |
| inventory-final-preparation: `python3 scripts/build_rc_review_bundle.py --prepare` | 0 | [inventory-final-preparation.txt](inventory-final-preparation.txt) |
| inventory-prepare-after-metadata-fix: `python3 scripts/build_rc_review_bundle.py --prepare` | 1 | [inventory-prepare-after-metadata-fix.txt](inventory-prepare-after-metadata-fix.txt) |
| inventory-prepare-portable: `python3 scripts/build_rc_review_bundle.py --prepare` | 0 | [inventory-prepare-portable.txt](inventory-prepare-portable.txt) |
| inventory-prepare: `python3 scripts/build_rc_review_bundle.py --prepare` | 1 | [inventory-prepare.txt](inventory-prepare.txt) |
| loopback-sandbox-probe: `python3 -m unittest tests.test_http -v` | 1 | [loopback-sandbox-probe.txt](loopback-sandbox-probe.txt) |
| pre-correction-probes: `python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .` | 1 | [pre-correction-probes.txt](pre-correction-probes.txt) |
| prv-check-after: `make check` | 2 | [prv-check-after.txt](prv-check-after.txt) |
| prv-check-final: `make check` | 0 | [prv-check-final.txt](prv-check-final.txt) |
| prv-unit-after: `python3 -m unittest tests.test_product_requirements -v` | 0 | [prv-unit-after.txt](prv-unit-after.txt) |
| prv01-check: `make check` | 0 | [prv01-check.txt](prv01-check.txt) |
| rc-probes-after: `python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .` | 0 | [rc-probes-after.txt](rc-probes-after.txt) |
| rc-unit-after: `python3 -m unittest tests.test_review_corrections_rc -v` | 1 | [rc-unit-after.txt](rc-unit-after.txt) |
| rc-unit-before: `python3 -m unittest tests.test_review_corrections_rc -v` | 1 | [rc-unit-before.txt](rc-unit-before.txt) |
| rc-unit-final: `python3 -m unittest tests.test_review_corrections_rc -v` | 0 | [rc-unit-final.txt](rc-unit-final.txt) |
| rc01-unit-after: `python3 -m unittest tests.test_review_corrections_rc.ReviewCorrectionsRC.test_RC01_withdrawal_then_fresh_or_late_claim_and_relock -v` | 0 | [rc01-unit-after.txt](rc01-unit-after.txt) |
| rc02-unit-after: `python3 -m unittest tests.test_review_corrections_rc.ReviewCorrectionsRC.test_RC02_middle_late_link_rechecks_eligible_and_approved_terminal tests.test_review_corrections_rc.ReviewCorrectionsRC.test_RC02_unchanged_chain_adds_no_bindings_moves_or_accounting_events -v` | 1 | [rc02-unit-after.txt](rc02-unit-after.txt) |
| register-docs-final-check: `make check` | 0 | [register-docs-final-check.txt](register-docs-final-check.txt) |
| retained14-direct: `python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .` | 0 | [retained14-direct.txt](retained14-direct.txt) |
| source-patch-dry-run: `/usr/bin/patch --dry-run -p1 -i /Users/luis/Documents/ChatGPT/Accounting Agent OS/docs/corrections_rc/source-and-tests.patch` | 0 | [source-patch-dry-run.txt](source-patch-dry-run.txt) |

No supplied probe was adapted. The new rc-gate and normal test suite require exit 0, exactly eighteen IDs, sixteen OK and only N02c/N04e NOTE. The older acceptance gate retains U4 as its sole NOTE identity. Historical supplementary observations in retained corrective scripts remain visible; passing gate labels do not relabel those observations.

## Preservation and inventory

Both review folders contain 58 files identical to each response ZIP. All twelve pre-existing ZIPs retain their initial hashes, including b154db10…f61ea, d38e0e27…30f84, 00a13d93…be001d, 0562869a…5f399 and d4c5795d…3d826. Original sidecars, original reviewer inputs, review/, fixtures/config and ss_agent_system_handoff/ remain unchanged. The three commits on review/fable-rb-acceptance retain their hashes. No Git commit was added, rewritten or staged by this pass.

All 174 V2 test methods remain. Every earlier test file is byte-identical except the explicitly requested additive extension of tests/test_product_requirements.py (eleven earlier methods retained, nine added). Six new RC methods and three strict-gate/preservation methods bring the total to 192. The sixteen test files of the original RA baseline remain untouched. No new skip/expected-failure marker was introduced.

changed-files.json covers every delivered payload difference against V2, including START_HERE.md and exports/. Its two self-artifacts are covered by REVIEW_MANIFEST.json; the manifest's own hash is in the adjacent package-check JSON, and the archive is hashed by its checksum sidecar. Runtime databases/data, OS metadata and Git/caches are explicitly excluded. source-and-tests.patch is generated against the immutable V2 source. pre-existing-owner-changes.patch and initial-files.json separate prior changes from this pass. AAOS-BB-01/02 preserve D-016/D-017 wording in every field except assigned Dependencies corrections; confirmation does not change state or a gate.

## Independent verdicts and remaining boundaries

AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 remain **Verification failed**, naming RC-01–03 and requiring independent re-verification of this checkpoint. The four prior-V2 verified records are raised solely from Fable's actual returned report/probes and checkpoint hash, not these developer tests. UC-10/N02c remains the later contradicting receipt policy observation; UC-11/N04e remains the zero-activity prior-statement acceptance limitation. U4, receipt had_approval metadata, synthetic grant lifecycle and other previously deferred matters remain disclosed; no unrelated fix or policy decision is assigned.

The six unratified shared requirements ONB-01/02, INT-07, GL-06, BNK-07 and RPT-03 remain Proposed; all nine Proposed decisions and all deferred capability states remain. Human G0 acceptance, G1–G4, Batch 3, actual client processing, live connections, paid models/services, sending, posting, payments, hosting and deployment remain closed.

## NOT_RUN this pass

- **NOT_RUN:** Full literal exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py . (all IDs). Not assigned for this pass; historical incompatibilities and nonzero logs are preserved. The maintained original-compatible subset and all reviewed setups ran via acceptance-gate and make test.
- **NOT_RUN:** Full literal exports/FABLE_REVERIFICATION/fable_reverification_probes.py . (all IDs). Not assigned for this pass; preserved historical nonzero results are not relabeled. Maintained original-compatible and reviewed setups ran via reverification-gate and make test.
- **NOT_RUN:** Additional bespoke UC-6, UC-8 and UC-9 independent probes. Outside RC/PRV assignment; existing developer regression coverage does not establish independent verification.
- **NOT_RUN:** External linter, type checker and JavaScript compiler. Not installed; no unrelated toolchain added. Offline repository syntax/registry/DOM checks ran.
- **NOT_RUN:** Next Fable independent verification. Awaiting independent reviewer of this new bundle; developer executions do not provide independent acceptance.

Use FABLE_RC_REVIEW_PROMPT.md for the exact next independent assignment. The adjacent archive checksum identifies the new checkpoint; passing developer results do not supply independent acceptance.
