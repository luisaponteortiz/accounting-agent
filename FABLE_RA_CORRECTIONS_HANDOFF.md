# Fable RA-01–RA-08 correction handoff

This is the response to exports/FABLE_RV_ACCEPTANCE/FABLE_RV_CORRECTIONS.json. Begin with docs/RA_CORRECTIONS_REPORT.md and FABLE_RA_REVIEW_PROMPT.md, then inspect actual source/tests and the unchanged independent acceptance inputs. The earlier RV submission remains frozen at SHA-256 247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75 and is included as the correction-diff baseline. Do not confuse it with this outer source.

Only RA-01–RA-08 are assigned; Batch 3 and live actions remain closed. All accounting data, identities and authority are fictional. Passing developer tests or accepting fixture setup does not constitute human G0 acceptance.

Run from the extracted project root:

```sh
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
```

The exact independent full command is also retained and its result disclosed:

```sh
python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .
```

RA-04 now holds revised statements. Four new positive fixtures (A03/A05/A17/X09), and older RT18, revise statements then assume immediate eligibility. A separate explicit-acceptance setup is returned under the API-change exception; no original verdict is changed and no original file is edited. Check docs/acceptance_ra/probe-adaptations.md and both exact patches. The original four failed IDs pass directly. The full original file still reports its four statement-setup incompatibilities; it is not claimed to exit zero.

All 24 acceptance controls run through the separate current setup (23 OK, allowed U4 NOTE); 20 unaffected originals execute directly. All 35 older controls run with 27 unaffected originals directly. The previously accepted seven adaptations and RT14b's explicit initial success/eligibility assertions remain intact. Judge the new acceptance steps independently.

The new bundle includes the 27 supplied acceptance files, earlier independent inputs, immutable historical ZIPs, new regression tests, full command output, original-script diagnostics, case-by-case 60-case results, source/test inventories and patches. Runtime databases and credentials are excluded. A packager guard prevents overwriting the frozen submission.
