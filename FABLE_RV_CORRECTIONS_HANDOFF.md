# RV-01–RV-17 correction checkpoint for Fable

> Historical RV handoff. The independent review has returned; start with FABLE_RA_CORRECTIONS_HANDOFF.md for the current response. This checkpoint's submitted archive remains frozen and byte-identical.

Start with docs/REVERIFICATION_CORRECTIONS_REPORT.md, then the unchanged exports/FABLE_REVERIFICATION/FABLE_REVERIFICATION_CORRECTIONS.json. This is the correction pass on the reviewed Accounting Agent OS source, not Batch 3 or a new accounting capability release. All records and identities remain fictional.

Please independently verify every RV acceptance assertion, retained C-01–C-06/Batch 2 control, source/input immutability and client isolation. Return remaining confirmed defects as prioritized reproducible tickets. No actual Bird Bowl policy, G0 acceptance, connection, posting, payment or deployment is authorized.

Commands from the extracted project root:

```sh
make test
make check
make batch2-gate
make reverification-gate
python3 review/fable_reverification_probes.py .
python3 scripts/synthetic_month.py
```

Read docs/reverification/probe-adaptations.md before judging the original all-probe command. The original 22 supplied files remain unchanged. RV-11/12/15 intentionally invalidate seven original positive setups; a separate compatibility copy preserves every original verdict/gate expression and updates only those setups with explicit authority and evidence. The exact delta is supplied. The unmodified compatible 28 probes run directly, and all 35 controls run through the current setup. The unmodified full command is also recorded, with its compatibility failures disclosed. Please judge this adaptation; it is not an automatic exemption from any control.

The full explanation now covers each of the seven adaptations and their unchanged assertions. Adapted RT14b explicitly asserts that both initial dispositions succeed and D1 is eligible before D3 arrives. Two fault-injection regressions verify that refusal of either initial decision or an ineligible starting D1 aborts the probe. The original RT14b and independent script remain unchanged. Please check the new assertions and the raw strengthened-probe/fault-test logs, as well as the unchanged final verdict.

The old reviewed archive, Batch 1 baseline and frozen corrective archive remain byte-identical inside the new bundle. docs/reverification/changed-files.json and source-and-tests.patch compare current source against the actual reviewed FABLE_CORRECTIONS_AND_BATCH_2 archive. The corrected cumulative Batch 1 inventory in docs/batch2/ includes JavaScript/HTML/CSS changes previously omitted. REVIEW_MANIFEST.json hashes every packaged file. Runtime databases and credentials are excluded.

Pay particular attention to supersession through new keys under lock, historical origin claims, population departures and revocation/re-enqueue, effective vendor retirement, evidence revisions and contributor lineage, duplicate candidate binding/exclusion, typed close requirements, and immutable package supersession. The new delivered teaching-month walkthrough refers TX-009 without changing its receipt; no accounting exception becomes clean merely by acknowledgement. All deferred capabilities and G1–G4 remain closed. Human G0 acceptance and independent re-verification remain pending.
