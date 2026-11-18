# RA-04 statement-acceptance setup changes

Fable accepted all seven earlier adaptations and strengthened RT14b in the frozen RV submission. Those changes remain intact. This correction pass adds **four new positive setups** (A03/A05/A17/X09) and **one older positive setup** (RT18), because RA-04 now holds changed statements until independently accepted. No supplied file is edited and no original verdict is changed.

## Why the unmodified full command remains nonzero

All four original defects now report OK directly from the supplied acceptance script: A10, X01, X12k and X12s. After RA-04, however, four other positive fixtures revise a statement and expect immediate eligibility without the newly mandatory decision:

| Probe | Revised statement in its positive setup | Unmodified result | Explicit added setup |
| --- | --- | --- | --- |
| A03 | Remove/void P1/V1 and replace the statement with the smaller population | WEAK: remaining items cannot be approved/finalized cleanly while revised support is unaccepted | Assert the statement revision hold/history, obtain acceptance for A1 and A2, re-prepare, then retain original approvals/finalization/removal assertions. |
| A05 | Add M3 and re-supply December's statement with the larger population | WEAK: M3 has the expected mapping but remains held for the statement revision | Accept that revised statement for M3, re-prepare December, then retain effective-date, retirement and vendor assertions. M2's unknown-vendor hold stays. |
| A17 | Add A3 and replace the statement after a frozen package | ERROR: immediate reviews are refused and clean finalization fails | Keep the original stale-finalization refusal first. Then assert/accept the statement revision for A1/A2/A3, re-prepare, and run the original reviews/package-supersession assertions. |
| X09 | Void retained D1 and replace the statement with D2 alone | WEAK: D2 regains an entry and loses duplicate exclusion, but its revised statement is unaccepted | Accept D2's statement revision before requiring eligibility. The second phase's circular-exclusion refusal and original verdict remain untouched. |
| Older RT18 | Change A2/receipt/statement, then use A1 as the valid starting point for dispute/revoke recovery | WEAK: A1 cannot enter the intended approval/dispute state while the statement is unaccepted | Retain stale-package refusal, assert/accept A1's revised statement, re-prepare, then run all original review/dispute/recovery and frozen-package assertions. Other held items remain carried by explicit acknowledgement. |

The new original full-file diagnostic is in current-original-acceptance-probes.txt. It is **not claimed to exit zero**. Returning to immediate eligibility would weaken the required statement control, so no runtime auto-acceptance, population-change exemption or implicit human authority was added.

## Exact changes and executable proof

`scripts/build_acceptance_adapter.py` generates the separate `review/fable_rv_acceptance_probes.py`. Its helper first asserts EVIDENCE_REVISED_REQUIRES_REVIEW and a disclosed statement revision, then obtains revised_evidence_accepted through the existing granted non-supplier DISP and re-prepares. No new person/grant is introduced. A17's stale-work negative remains before acceptance. Every original Return and Assign AST node in all 24 probes is identical. The exact delta is acceptance-probe-adaptations.patch.

`scripts/build_reverification_adapter.py` retains the previously accepted setup and adds only older RT18's explicit acceptance step. The original source remains exports/FABLE_REVERIFICATION/fable_reverification_probes.py. The original negative empty-freshness/insufficient-evidence cases and strengthened RT14b's initial success/eligibility assertions remain unchanged. Its original final verdicts are preserved; see older-RT18-adaptation.patch for the delta against the frozen reviewed copy and docs/reverification/reverification-probe-adaptations.patch for the complete original-to-current delta.

Normal tests run the supplied acceptance script **unmodified on its 20 unaffected probes**, plus all 24 through the explicit setup: 23 OK and the permitted U4 NOTE. The older gate runs 27 unaffected originals and all 35 current-setup probes. The unmodified full commands are also recorded separately with their setup failures. No NOTE other than U4 is accepted in the new maintained gate, and no original accounting finding is kept as an expected failure.

The independent API-change exception permits returning an adapted probe for review. It does not automatically accept these changes. Fable must judge the exact helper/setup deltas, legitimate starting states and unchanged verdicts. Expression identity alone does not prove that a fixture is sound. No G0 or real operating authority is inferred from the developer gate.
