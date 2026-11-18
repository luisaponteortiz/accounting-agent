# Independently verify RD-01/RD-02 and PRV-11–PRV-13

Review the new `exports/FABLE_RD_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`. Verify its SHA-256 against the adjacent `.zip.sha256` before extraction, and verify every entry of `REVIEW_MANIFEST.json` and its externally anchored hash in the adjacent `_PACKAGE_CHECK.json`. Treat the submitted ZIP, its sidecars, the working project and every earlier reviewer folder/archive as immutable. Use clean disposable extracted copies, fictional fixtures and temporary databases only. Nothing in this prompt authorizes implementation in the working project, a schema change, paid models/services, client records, sending, posting, payments, hosting, deployment, Batch 3 or a readiness release.

The reviewed baseline for the diff is `exports/FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`, SHA-256 `9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454`. The returned review response is `1c47259742cfed78a2dcd2059c8cdadb72787df208d9d9232ddd8946bcfcbc23`. The owner authorized exactly RD-01, RD-02 and PRV-11–PRV-13 in `CODEX_RD_CORRECTIONS_PROMPT.md` (SHA-256 `4ae020a6d2111d4db33bd30d909f4968c60b89e8114ba044189f21d3e66c913f`). No API/probe adaptation or schema change is claimed.

Read in this order:

1. `exports/FABLE_RC_ACCEPTANCE/FABLE_RC_CORRECTIONS.json`, its companion acceptance report and machine-readable results. These supply your original exact assertions, regression variants and register verdicts.
2. `docs/corrections_rd/RD_CORRECTIONS_REPORT.md`, `FABLE_RD_CORRECTIONS_HANDOFF.md`, D-022–D-025 in `DECISIONS.md`, and the changed register records.
3. `docs/corrections_rd/source-and-tests.patch`, `changed-files.json`, `preservation.json`, `input-checksums.json`, pre-correction raw logs and command exit-code records. The inventory covers every payload difference from the RC/PRV baseline, including pre-existing administrative/review additions; only declared self-artifacts/envelope files are covered by explicit manifest rules.

Reproduce both original failures on a separate clean extraction of the baseline: the unchanged `fable_rc_acceptance_probes.py` should exit 1 with 12 OK / X01, X01d, X02 WEAK / X08 NOTE; the unchanged `fable_rc_order_search.py` should exit 1 with 18 double approvals in 120 runs. Then independently evaluate the new source against each acceptance assertion:

- RD-01: first unchanged re-send with an unknown-target claim records exactly one new source version and unresolved event; both transition blockers appear before the target arrives, for eligible and previously approved claimants. Earlier approval stops governing before target arrival. When the target arrives, claimant and receipt are held under the locked ancestor, an approved-source event names the former December approval and ITEM_LEFT_POPULATION is recorded; the approval decision remains. Repeat the still-unresolved claim twice: changed False and no extra source snapshot/binding/move/link/accounting event. Distinct batch envelopes retain their ordinary immutable intake record; exact packet replay adds no snapshot of any kind. Inspect this distinction and report any disagreement with the contract.
- RD-02: the latest unresolved claim belongs to scoped source identity (kind/key), survives amount revision or retirement/re-send without the claim, and resolves to the current claimant head (removed or not). Check both orders Yc Z Yp X and Z Yc Yp X, the repeated-claim control, restart, most recent target selection, open target, cycle refusal, and an already linked identity. Claims omitted from later versions persist pending the owner's unresolved feed-policy decision.
- Keep Q01/Q02/Q02i/Q03, N01d/N01e/N01f, R01c/R01d and every prior gate assertion. Unrelated intake must add nothing to a chain, including after release/relock. No snapshot, decision, package or audit record may be rewritten.
- Do not fix X08/UC-14, N02c/UC-10, N04e/UC-11 or U4. The transaction-only re-evaluation remains unchanged; journal-chain UC-9 is reported by source reading and is NOT_RUN as a bespoke execution. Investigate independently if useful and return a separate finding; it is not permission to expand this pass.
- PRV-11: RC-01–03 accepted at 9a85c78a…2454, RB-01 still unaccepted for RD-01/RD-02. BNK-03, CTL-04 and GOV-03 remain Verification failed with exact re-verification criteria. Both arrival-order criteria include the two RD deliveries. CTL-09 cites Q02 independent acceptance binding; the other three verified records and every field of BB-01/BB-02 remain unchanged. Seven project results keep their original order and match `register_verdicts`; T-12, RA-01, RB-01 and Current evidence agree.
- PRV-12: independently verify hash pins and derivation from the two reviewer-authored machine-readable files, earlier seven conclusions then RC `register_verdicts`, later winning per record. Alter project result metadata/state, omit a failed record and promote it, invent a record, or alter either protected reviewer file: the check must fail. Earlier authoritative accepted citations for unchanged verified scopes are allowed only while the latest verdict still verifies them; a later failed verdict always governs.
- PRV-13: removing the client display name from the terms list or changing the heading without the list must fail. Names are read from the client section, not hard-coded. Run G44 unchanged.

Run these commands unmodified on the new extraction, keeping raw stdout/stderr and exit codes:

```sh
python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py .
python3 exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py .
python3 exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py .
python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .
make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
make rb-gate
make rc-gate
make rd-gate
python3 scripts/check_product_requirements.py --json
python3 exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py .
```

Use a second clean extracted copy for the following mutating script, never the working project:

```sh
python3 exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py <disposable-copy>
```

Require exact 16 RC ids with 15 OK / X08 NOTE only, exact 120 orders with zero double approval, earlier exact 18 ids with 16 OK / N02c and N04e NOTE only, and 14 earlier OK. Both new scripts must be reached by `make test` and strict `make rd-gate`; fault-test missing/duplicate/unknown ids, altered notes, missing/duplicate order rows and double approvals. All 192 baseline test methods and their bodies must remain; the only earlier test file changed must be additive methods in `tests/test_product_requirements.py`. Expect 205 methods total, no skips/expected failures. Reviewer cases stay 29 PASS / 10 FIXED / 21 DEFERRED-OK; U4 alone remains NOTE in the older acceptance gate. Historical supplementary N08/N09 output is disclosed and is not a gate verdict. Require 37/37 and 44/44 register fault agreement, with G16/G17/G18/G44 rejected. Report any case whose meaning changed; do not change a supplied fault script.

Verify all earlier archive/sidecar hashes, both review folders, the frozen V2 hash `00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d`, all 484 protected inputs, no schema change, exact owner wording, all six named unratified records still Proposed, and the complete inventory/patch. Check that the patch applies to the baseline and reproduces every source/test/script/Makefile byte. In the working project, read-only, confirm branch `review/fable-rc-acceptance` and five unchanged commits with HEAD `5a12ab0`; no new commit is authorized. The adjacent `_FINAL_VERIFICATION.json` and `_FINAL_VERIFICATION/` logs report checks against the finalized archive outside its own manifest to avoid recursion.

Return an independent report, machine-readable per-ticket and per-register verdicts, exact probes/fault outputs, and any new minimal reproductions. State which assertions you ran, which were reading-only, and NOT_RUN reasons. Identify the precise reviewed bundle hash and scope for every conclusion. Do not treat developer passes as independent acceptance or grant human G0, G1–G4, Batch 3 or live authority. Return findings and await the owner's next assignment.
