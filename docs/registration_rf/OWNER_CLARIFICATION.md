# Owner assignment and clarification for the RF result registration

17 November 2026. Recorded in `DECISIONS.md` as D-033.

## Assignment

Given with the handoff `HANDOFF_RF_CHECKPOINT_2026-11-17.md`:

> Let's move this project forward and complete it

That handoff names the registration of the returned RF review as the next work and requires that conflicts with retained tests be identified and reported before any method is adapted.

## What was reported before any project file changed

The registration was tried in a disposable copy of the project. Pinning the RF results and report as the fifth authority and recording AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 as Independently verified made the checker and `make check` pass, and made six retained register-test methods fail. `commands/conflict-unadapted-retained-register-tests.stderr.txt` reproduces those failures against the final registered project with the two retained test files exactly as delivered at the RF checkpoint.

| File | Method | Why it conflicts |
| --- | --- | --- |
| `tests/test_product_requirements.py` | `test_PRV03_failed_verdict_cannot_be_promoted` | Uses AAOS-BNK-03 as a failed record; no failed record remains. |
| `tests/test_product_requirements.py` | `test_PRV12_omitted_changed_and_invented_results_cannot_promote_records` | Its "changed" case flips AAOS-BNK-03 to verified, which is now the true verdict. |
| `tests/test_product_requirements.py` | `test_PRV14_third_authority_is_pinned_and_latest_verdict_controls` | Its second half builds a three-authority fixture by omitting only the fourth pins; the fifth still overrides. |
| `tests/test_product_requirements_rf.py` | `test_fourth_authority_wins_and_all_older_authorities_cannot_override` | Asserts every latest verdict cites the RE report. |
| `tests/test_product_requirements_rf.py` | `test_fourth_changed_verdict_controls_even_with_matching_project_results` | Alters the RE file; the RF review now overrides it. |
| `tests/test_product_requirements_rf.py` | `test_fourth_stale_missing_extra_duplicate_changed_and_reordered_results_refused` | Its "changed" case flips AAOS-BNK-03 to verified, which is now the true verdict. |

## Question and answer

Question put to the owner:

> Authorize the RF registration, including adapting the six named retained test methods?

Owner's answer:

> Yes, authorize

## Conditions put to the owner with the question

- Only these six methods. Names stay and assertions are unchanged.
- Each adapted method runs on a historical fixture made of data only: the fifth (RF) pinned inputs are left out of the checker's pin table, and the register and derived-results bytes are those of the delivered RF checkpoint, read from the immutable RF bundle and checked against their recorded hashes. Nothing is stubbed, bypassed or special-cased.
- The other 235 of the 241 methods remain textually unchanged. No probe and no original fault case is edited.
- Separate new methods test the unmodified five-authority configuration.
- Latest-wins is not weakened. The shipped checker always reads all five authorities.
- The registration records the three verdicts for the RF checkpoint and scope only. Human G0, UC-21 to UC-25 and every later gate remain the owner's separate decisions.

The owner was also told, before answering, that more cases in the unchanged original fault scripts become obsolete, that the older bundle-preservation verifiers assert the three states are unchanged and would therefore fail, and that this session performs the developer-side registration of verdicts issued by the independent Fable review.

This is not a general test-edit exception. D-026, D-029 and D-031 are unchanged.
