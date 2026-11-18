# RD/PRV correction report — 16 November 2026

RD-01, RD-02 and PRV-11–PRV-13 are implemented and developer-tested within the authorized local fictional scope. The unchanged RC probes report **15 OK / X08 NOTE**, with no WEAK/ERROR; the unchanged search reports **120 runs / zero double approvals**. `make test` passed **205 methods**, including all eleven HTTP methods, with no skips or expected failures. All 192 baseline methods and their bodies remain. All required gates pass. These results do not establish independent RD acceptance or human G0.

## Authority and baseline

Before any project edit, the prompt matched `4ae020a6d2111d4db33bd30d909f4968c60b89e8114ba044189f21d3e66c913f`, response ZIP matched `1c47259742cfed78a2dcd2059c8cdadb72787df208d9d9232ddd8946bcfcbc23`, and working register matched `d55063e25857b2a66606f8e2a255ccf68e427b330d6cba97bde79ad014a663f9`. See `preflight-hashes.txt` and `environment.json`. Branch `review/fable-rc-acceptance` retains exactly five commits, HEAD `5a12ab0`, with no rewrite or added commit (`git-history-before.txt`, `git-history-final.txt`).

The comparison checkpoint is the immutable RC/PRV ZIP at `9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454`. The 62 files in the RC review folder match the returned response ZIP byte for byte (`returned-response-integrity.json`). All 484 protected files and all 14 prior archives are unchanged. Existing archive sidecars match; three older historical archives have no `.zip.sha256` sidecar and are checked against their protected checkpoint hashes (`archive-integrity.json`). V2 remains `00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d`.

## Ticket disposition

| Ticket | Change and location | Coverage and developer result |
| --- | --- | --- |
| RD-01 | `accounting_agent/source_control.py`: an unchanged existing row declaring a new unknown-target claim forces a source version so the existing append-only unresolved event is recorded. Repeating the same unresolved claim does not force another version. | `tests/test_review_corrections_rd.py`: eligible and previously approved claimant, both blockers before target arrival, immutable approval decision/event references, two fresh-envelope repeats and exact packet replay. X01/X01d OK; X01b/X01c unchanged; all relevant search families have zero double. |
| RD-02 | The same module resolves the latest recorded claim by scoped kind/key to the current head, including removed heads. `service.py` uses that same lookup for the version in the population. Existing links and cycle refusal remain authoritative. | Five new source methods cover revision with/without repeated claim, restart, retirement/re-send in both Yc Z Yp X and Z Yc Yp X orders, latest target, and no second resolution of an already linked identity. X02/Q02i/Q03/N01d/N01e/N01f/R01c/R01d remain OK; all five order families pass. |
| PRV-11 | Register Current evidence, T-12/RA-01/RB-01, both arrival-order criteria, three failed scope/evidence fields, CTL-09 Q02 result, and all seven project results updated. AGENTS/DECISIONS/PROGRESS/readiness/freeze/start documents synchronized. | `make check` passes 88 records/27 tickets; preservation assertions retain all states/decisions, every BB-01/02 field and the three other verified records; results keep the seven-entry order. BNK-03/CTL-04/GOV-03 remain Verification failed for RD-01/RD-02. |
| PRV-12 | `scripts/check_product_requirements.py` derives conclusions from two pinned reviewer JSON files and pinned report hashes, applying the later RC verdict per ID. Project results must exactly match; omissions, additions, edits and stale metadata reject. Earlier accepted scope citations remain valid only while the latest verdict verifies that record. | Three new fault methods in `tests/test_product_requirements.py`: G16/G17/G18 combined promotion attempts, both authority-file hash changes, stale checkpoint metadata. All pass; unmodified Fable G16/G17/G18 reject, 44/44 agree. |
| PRV-13 | The checker parses the display name from the client section heading and requires it in the terms list. No client name is hard-coded. | New fault method tests name removal, heading/list mismatch and a different client name; G44 rejects. |

The experimental patch was a worked reference only. The delivered design decodes event payloads in Python; resolution uses a scoped identity join rather than SQLite `json_extract` grouping. One helper drives claim recording, display and resolution. No schema, API, probe, model or stack change was made. `storage.py` and `tests/schema_v1.sql` are byte-identical. Only `tests/test_product_requirements.py` changes among earlier test files, by appending methods; every original byte remains its prefix. New tests add five source methods, four strict-gate/preservation methods and four register fault methods: 192 + 13 = 205.

The owner has not decided early claim delivery or omission-as-withdrawal semantics. D-023 therefore records and retains the claim as the stronger control, without deciding feed policy. Distinct re-send batch envelopes retain their ordinary immutable batch snapshot/intake audit. The no-op assertion concerns the claimed source and its lifecycle: no added source snapshot, binding, move, link or accounting event, and changed False. Exact packet replay adds no snapshot of any kind. This preserves the intake evidence model and the RC-02 no-op convention demonstrated by Q02i.

## Reproduction and commands run

I ran these commands myself. Each label below has raw `.stdout.txt`, `.stderr.txt` and `.json` files containing the exact argv, cwd, UTC start, duration, exit code and environment. `execution-results.json` and `exit-codes.json` index every captured command, including intermediate failures. Environment: macOS 26.5.2 x86_64, Python 3.9.6, SQLite 3.51.0, GNU Make 3.81. The restricted sandbox refused a loopback bind (`loopback-check`, exit 1); the complete full suite ran with loopback access, without omitting HTTP tests.

| Command / label | Exit | Result |
| --- | --- | --- |
| Unmodified RC probes before source changes / `baseline-rc-probes` | 1 | Exact 16 ids: 12 OK, X01/X01d/X02 WEAK, X08 NOTE. |
| Unmodified order search before source changes / `baseline-order-search` | 1 | 120 runs, 18 double, 18 silently finalized. |
| Final new unit methods on clean baseline extraction / `rd-unit-before-final` | 1 | Five methods, six failing subcases for RD-01/RD-02; latest-target guard passes. No ERROR or unreachable production assertion. |
| Final new unit methods / `rd-unit-final` | 0 | All five pass. |
| `python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .` / `rd-rc-probes-after` | 0 | Exact 16 ids, 15 OK; only X08 NOTE. |
| `python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py .` / `rd-order-search-after` | 0 | 120 runs; zero double, all five families 0/24. |
| `python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .` / `final-rb-probes-direct` | 0 | Exact 18 ids; 16 OK; only N02c/N04e NOTE. |
| `python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .` / `final-ra-probes-direct` | 0 | 14 OK. |
| `make test` / `final-make-test` | 0 | 205 methods OK, all eleven HTTP tests; no skip/expected failure. Both new scripts run through the new gate test. |
| `make check` / `register-after-prv11-13` and `final-make-check` | 0 | 88 records, 27 tickets; source/syntax/profile/client boundaries pass. |
| `make batch2-gate` / `final-batch2-gate` | 0 | 29 PASS / 10 FIXED / 21 DEFERRED-OK, synthetic month and corrective gate pass. |
| `make reverification-gate` / `final-reverification-gate` | 0 | Retained original subset, maintained adapted suite and frozen corrective gate pass. |
| `make acceptance-gate` / `final-acceptance-gate` | 0 | U4 is the only NOTE identity. |
| `make rb-gate` / `final-rb-gate` | 0 | 14 unchanged probes and retained RA gate pass. |
| `make rc-gate` / `final-rc-gate` | 0 | Exact earlier 18-probe contract enforced. |
| `make rd-gate` / `final-rd-gate-current` | 0 | Exact 16 probes and every exact 120 order enforced, including missing/duplicate/unknown result and altered-note fault checks. |
| `python3 scripts/check_product_requirements.py --json` / `final-register-counts` | 0 | 77 Approved / 9 Proposed / 2 Rejected; 4 Independently verified / 3 Verification failed unchanged. |
| Unmodified earlier register fault script / `final-rb-register-faults` | 0 | 37 agree / zero gaps; eleven make-check setups retain their expected outcomes. |
| Unmodified new register fault script on clean candidate extraction / `final-rc-register-faults` | 0 | 44 agree / zero gaps; G16/G17/G18/G44 reject; make-check gaps zero. |
| Source/tests patch dry-run, apply and byte comparison / `source-patch-check` | 0 | All ten changed source/test/script/Makefile files reproduced exactly. |

Gate commands that generate old report files ran in `/tmp/aaos-rd-gates` so earlier working evidence was not regenerated. All runtime/source and register controls in those copies match the new pass. The stricter generic probe-id matcher was separately checked on current source (`rd-gate-fault-unit-final`, `final-rd-gate-current`). The new fault script ran only against `/tmp/aaos-rd-faults`, extracted from a newly generated validation candidate; its checker/register/application/tests match the final ones. The finalized archive is also checked directly by `scripts/verify_rd_bundle.py`: its adjacent `_FINAL_VERIFICATION.json` and log folder record exact clean-extraction checks, both unchanged fault scripts, and the new rd-gate. These adjacent outputs avoid a self-referential archive rebuild.

No supplied fault case changed its intended meaning; every previous accepted/rejected setup agrees. Initial new-test development exposed two harness mistakes: event payloads export as JSON strings, and a re-sent claimant can immediately be retired again by its live terminal. The final tests decode the string and assert the unresolved blocker for any claimant actually in the population, then require the current-head link and terminal quarantine. Earlier failing logs remain; the final corrected methods were rerun against a clean baseline and still reproduce six defect subcases. The optional stale-results test was added after verdict metadata advanced; it is covered by the final 24-method register run and full suite.

## Preservation, inventory and limits

`preservation.json`, `input-checksums.json`, the test inventory in `changed-files.json`, and `tested-source-sha256.json` anchor the preserved source and evidence. `changed-files.json` lists every payload difference against the RC/PRV bundle, including the pre-existing review/authorization files, with baseline/initial/current hashes. The inventory and patch cover themselves through the manifest rule. The ZIP/sidecar/external manifest/package check and adjacent final-extraction evidence are excluded from the payload as declared output-envelope artifacts. The internal manifest hashes every payload file except itself; its hash is in the external package check, and the ZIP hash is in its checksum sidecar. No earlier archive, sidecar or manifest was overwritten.

RC-01–03 and PRV-01–10 were independently accepted by Fable at 9a85c78a…2454; this report only adds developer repair evidence for RD/PRV. BNK-03, CTL-04 and GOV-03 remain Verification failed until independent X01/X01d/X02 and order-search success on the next checkpoint. CTL-09 now cites independent Q02; the other three verified records remain unchanged. D-016/D-017 and every BB-01/02 field are unchanged. ONB-01, ONB-02, INT-07, GL-06, BNK-07 and RPT-03 remain Proposed.

X08/UC-14, N02c/UC-10, N04e/UC-11 and U4 remain policy observations. The retained supplementary corrective script still prints N08/N09 WEAK as previously disclosed; those supplementary observations are not gate verdicts and were not changed.

**Reading only / NOT_RUN:** journal-chain UC-9 has not been executed as a bespoke probe. `journal-scope-reading.txt` records the public journal `supersedes` envelope, shared source revision path, transaction-only re-evaluation and absence of journal unresolved-transition blockers. This suggests a separately reproducible late-middle-link exposure; it is an inference from source, not a verified or corrected journal defect. The re-evaluation remains card transactions only. Bespoke UC-6/UC-8 checks, full literal older RV/reverification scripts with every historically incompatible setup, deliveries beyond the bounded 120 orders, browser rendering, and external linter/typechecker/JavaScript compilation were NOT_RUN: outside this assignment or not installed. Maintained older gate subsets/adaptations ran unchanged. No toolchain was added.

All data and databases used were temporary and fictional. No connection, model call, client-data loading, sending, posting, payment, hosting or deployment occurred. No human G0, G1–G4, Batch 3, deferred capability or operating authority is granted. After this delivery, await independent results and a new user assignment.
