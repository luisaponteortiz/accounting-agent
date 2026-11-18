# RF result registration record

17 November 2026. Owner assignment and clarification: D-033 ([quoted here](OWNER_CLARIFICATION.md)). Validation record: D-034.

The returned independent RF review is now registered. AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 are recorded **Independently verified for the reviewed RF checkpoint and its synthetic scope**. The RF results file and report are the fifth hash-pinned reviewer authority. No application source, schema, probe, gate script or HTTP test changed.

This is a developer-side registration of verdicts the independent review already issued. It was carried out by a Claude (Fable) session at the owner's assignment; Fable also performed the independent RF review. The three verdicts are derived mechanically from the pinned reviewer files, and the owner was told about the shared role before authorizing. **The registration change itself has not been independently reviewed.**

Human G0 is not granted by this record. All data is fictional and every database was temporary. Nothing was connected, posted, paid, sent, deployed or committed.

## What was registered

| Item | Value |
| --- | --- |
| Reviewed bundle | `exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd` |
| Fifth authority, results | `exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_RESULTS.json`, SHA-256 `fe543fe2b1930cc3e7d63315de298af331c6061ec4821288d94772773b778039` |
| Fifth authority, report | `exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md`, SHA-256 `90deaea5eb0efa9fbc3b7ff7d20505f9623012552578a5070b832ea516df2410` |
| Scope of every conclusion | Synthetic local preparation controls at the reviewed bundle hash only: fictional card rows and receipts, principally two periods and one card account. Journals excluded. The target-selection HTTP route was not independently probed beyond the developer tests. |

Register states before and after:

| Implementation state | RF checkpoint | Now |
| --- | --- | --- |
| Independently verified | 4 | 7 |
| Verification failed | 3 | 0 |
| Developer-tested | 20 | 20 |
| Deferred | 36 | 36 |
| Not started | 25 | 25 |

## Files changed

Compared with the delivered RF bundle, exactly nine of its 1,790 payload files differ in the working project ([preservation.json](preservation.json)). The complete diff is [registration.patch](registration.patch). [apply_registration.py](apply_registration.py) made the checker, results and register edits; [apply_test_adaptation.py](apply_test_adaptation.py) made the first version of the test edits, after which the fixture import was moved inside the three RF methods by hand so that nothing outside the six methods changes.

| File | Change |
| --- | --- |
| `scripts/check_product_requirements.py` | Two pins added (RF results and report); two comments say five authorities. No logic changed. |
| `docs/INDEPENDENT_VERIFICATION_RESULTS.json` | Seven rows re-derived from the five authorities, original order; each now cites the RF report and bundle. |
| `docs/PRODUCT_REQUIREMENTS.md` | Three records: Implementation state, Scope note and Evidence. AAOS-GOV-02: Scope note says five authorities. Current-evidence text, three crosswalk rows, one change-log row and the header date. |
| `tests/test_product_requirements.py` | Three methods adapted under D-033. Nothing outside those methods changed. |
| `tests/test_product_requirements_rf.py` | Three methods adapted under D-033. Nothing outside those methods changed. |
| `DECISIONS.md` | D-033 and D-034 appended; the RF-checkpoint bytes are an unchanged prefix. |
| `PROGRESS.md`, `docs/CONNECTION_READINESS.md`, `AGENTS.md` | Current checkpoint and authorization. G0 stays unaccepted. |

New files: `tests/rf_checkpoint_fixture.py`, `tests/test_product_requirements_rf_registration.py`, this folder, and `HANDOFF_RF_REGISTRATION_2026-11-17.md`.

Unchanged in the register: every acceptance criterion and product decision; all 88 IDs and their order; the four earlier verified records; AAOS-BB-01 and AAOS-BB-02; the six Proposed records (ONB-01, ONB-02, INT-07, GL-06, BNK-07, RPT-03).

## The six adapted methods

Before adaptation these six methods failed against the registered configuration; [the reproduction](commands/conflict-unadapted-retained-register-tests.stderr.txt) runs the two retained test files exactly as delivered and shows 8 failures in 31 tests. Complete texts: [before](adapted-methods-before.py), [after](adapted-methods-after.py), [diff](adapted-methods.diff). Method inventory: [retained-method-inventory.json](retained-method-inventory.json).

| Count | Result |
| --- | --- |
| Retained methods at the RF checkpoint | 241 |
| Present | 241 |
| Textually unchanged | 235 |
| Adapted under D-033 | 6 |
| Added | 9 |
| Total now | 250 |

How each was adapted:

- **Names and assertions are unchanged.** `test_PRV03` previously called the class helper `rejects`; it now spells out the same `assertRaisesRegex(ValueError, ...)` around `validate_register`, because the helper is fixed to the real project root.
- **Fixture.** `tests/rf_checkpoint_fixture.py` leaves the two RF pins out of the checker's pin table as data and supplies the register and results bytes of the RF checkpoint, read from the immutable RF bundle and checked against `8a91c6ff…680f` and `4371242d…d515`. It stubs and bypasses nothing.
- **`test_PRV14` (the D-031 method).** Its first half is unchanged and runs on the real five pins. Its second half now omits the fourth and fifth pins and validates the RF-checkpoint register text.
- **Three RF methods.** They run as before on the four-authority configuration they were written for, through the fixture.

## New methods on the real five-authority configuration

`tests/test_product_requirements_rf_registration.py`, nine methods:

| Method | What it shows |
| --- | --- |
| `test_shipped_configuration_reads_five_authorities_and_the_fifth_is_latest` | The pin table holds the five authorities in order; all seven latest verdicts cite the RF report and bundle; the three recorded records were failed at the fourth; the project results file equals the derivation. |
| `test_fifth_results_and_report_are_hash_pinned` | One added byte in either RF file is rejected. |
| `test_three_recorded_scopes_cite_the_fifth_checkpoint_and_nothing_else_moved` | Only the three records and AAOS-GOV-02 changed, in the fields listed above; citing only the RE review for a recorded record is rejected. |
| `test_fifth_failed_verdict_cannot_be_promoted_and_a_downgrade_is_accepted_when_results_and_register_follow` | With the RF file altered and re-pinned to fail AAOS-BNK-03, the verified register is rejected and a downgraded register is accepted. |
| `test_each_older_authority_altered_and_repinned_cannot_override_the_fifth` | Each of the four older files, altered and re-pinned, changes no verdict. |
| `test_results_and_register_that_follow_the_fourth_authority_are_rejected` | The RF-checkpoint results file, and each row taken from the previous authority, is rejected. |
| `test_record_absent_from_the_fifth_falls_back_to_the_fourth_verdict` | A record removed from the RF file takes the RE verdict, and the verified register is then rejected. |
| `test_seven_row_order_and_exact_rows_are_enforced_on_five_authorities` | Swapped, reversed, moved, missing, extra, duplicate, changed and stale rows are rejected. |
| `test_historical_fixture_bytes_are_hash_checked_and_leave_the_shipped_pins_alone` | The fixture rejects altered checkpoint bytes and restores the shipped pin table and its order. |

One behaviour these tests record without changing: with the registered results in place, a register that still shows the three records as Verification failed is accepted. The checker bars promotion over a failed verdict; it does not force a record up to a verified one.

## Validation

All commands ran unmodified on disposable clones of the registered project, one after another. Full index and raw output: [commands/COMMAND_RESULTS.md](commands/COMMAND_RESULTS.md).

| Command | Exit | Result |
| --- | --- | --- |
| `make test` | 0 | 250 of 250 methods OK in 1,017.714 s; all 11 HTTP methods OK; no skips or expected failures |
| `make check` | 0 | passes; 88 records, 27 tickets |
| `make batch2-gate` | 0 | passes |
| `make reverification-gate` | 0 | passes |
| `make acceptance-gate` | 0 | 19 OK / 1 NOTE and 23 OK / 1 NOTE; U4 the only NOTE |
| `make rb-gate` | 0 | 14 OK |
| `make rc-gate` | 0 | 16 OK; N02c and N04e NOTE |
| `make rd-gate` | 0 | 15 OK; X08 NOTE; 120 orders, 0 double |
| `make re-gate` | 0 | 336 orders, 0 double |
| `make rf-gate` | 0 | 19 OK; C9c and C9g NOTE; 480 orders, 0 double, 0 released, 0 audit failures |

`make test` was run once. The five-consecutive-run requirement belonged to RF-03, whose source is unchanged here. The 94 tested source, test, script, review, Makefile, register, results and decision-log files had identical hashes before and after the run. They match the working project, except that D-034 was appended to `DECISIONS.md` after the run; [final-checks.txt](final-checks.txt) records `make check`, the register tests and the decision-log test re-run in the working project after that last edit.

## Original fault scripts

All five scripts are unchanged. More of their cases are now obsolete, because each either presumes the three records are failed or alters an authority that the RF review now overrides. This is the same reading the independent RF review gave to H22–H24 and the six J cases at the RF checkpoint.

| Script | At RF checkpoint | Now | Exit now |
| --- | --- | --- | --- |
| F: `FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py` | 37 of 37 | 36 of 37 | 0 |
| G: `FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py` | 44 of 44 | 43 of 44 | 1 |
| H: `FABLE_RD_ACCEPTANCE/evidence/scripts/fable_rd_register_faults.py` | 34 of 37 | 35 of 37 | 1 |
| J: `FABLE_RE_ACCEPTANCE/evidence/scripts/fable_re_register_faults.py` | 29 of 35 | 20 of 35 | 1 |
| K: `FABLE_RF_ACCEPTANCE/evidence/scripts/fable_rf_register_faults.py` | 62 of 62 | 41 of 62 | 1 |

Every disagreeing case, by reason:

| Reason | Cases |
| --- | --- |
| The case raises or flips a record that it presumes is failed. The record is now verified, so the "fault" is the true state or a permitted lower state. | F26; G09; J14, J20, J24, J26–J34; K24, K30, K31, K35, K36, K46, K51–K59 |
| The case alters or deletes a verdict in an authority that the RF review now overrides for that record. | H22, H23; J16, J18, J22; K26, K28, K42, K43 |
| The case swaps in the RF bundle hash as an unreviewed hash. It is now the reviewed hash. | K48 |
| The case removes the RE pins and expects different results. The RF review covers all seven records, so the derivation is unchanged. The first new method above asserts the exact five-entry pin list instead. | K22 |

H24, J15 and J25, which disagreed at the RF checkpoint, now agree. That is a side effect of the same change and not a repair.

Do not edit these scripts or weaken latest-wins to make the obsolete cases agree. The nine new methods test the five-authority equivalents.

## Older verifiers that now refuse

`scripts/verify_rf_preservation.py` and `scripts/verify_re_preservation.py` assert that every Implementation state equals the RE checkpoint, so both now fail on the three recorded states (observed in the disposable trial copy). `scripts/verify_rf_bundle.py`, `verify_re_bundle.py` and `verify_rd_bundle.py` require 37 of 37 and 44 of 44 from the F and G scripts and would also fail; those three were not run. They are delivery-time tools for their own checkpoints, are not part of `make test` or any Makefile gate, and are left unchanged. [verify_preservation.py](verify_preservation.py) is the equivalent read-only check for this registration.

## Preservation

From [preservation.json](preservation.json), re-run on the final state:

- All 1,198 protected inputs of the RF pass are unchanged.
- All 16 earlier archives, and the RF and RE bundles and responses, keep their hashes.
- All 298 files of the returned RF response match their working copies.
- Branch `review/fable-rc-acceptance`, HEAD `5af9a6194bc39e2f303cc6b43b0b59094118b8e4`, ten commits, history identical to the RF preflight, nothing staged, no commit added.
- `tests/test_http.py`, the schema and every probe are unchanged (they are among the 1,781 identical bundle members).
- [input-checksums.json](input-checksums.json) is the new protected inventory: the 1,198 earlier inputs plus 308 for the returned RF review and its delivery, 1,506 in total.

## Open after this registration

- **Human G0.** The accounting owner's separate decision. Not granted.
- **Owner observations.** UC-21, UC-22 and UC-23 ask for a decision; UC-24 and UC-25 need none now. U4, UC-14, UC-17, UC-18 and UC-20 remain open. C9c, C9g, X08, N02c and N04e stay NOTE. UC-9 remains reading only.
- **Not verified by anyone.** Journals, more than two periods or one card account, the target-selection HTTP route beyond developer tests, any real provider, and human operating readiness.
- **Closed.** G1 sample processing, Batch 3, deferred and Proposed capabilities, and every live action.
