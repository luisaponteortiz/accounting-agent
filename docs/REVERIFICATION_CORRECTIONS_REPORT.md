# RV-01–RV-17 implementation and verification report

> Historical checkpoint: Fable's independent acceptance review is now in exports/FABLE_RV_ACCEPTANCE/. Current source is the RA correction response in docs/RA_CORRECTIONS_REPORT.md. This report's gate counts and adaptation set describe the frozen RV submission; the current source comparisons are regenerated under their explicit archive baselines.

15 November 2026. Local fictional preparation only. **Developer verification passes with disclosed probe-setup adaptations; independent Fable acceptance and G0 remain pending.** No Batch 3 work, client connection, model invocation, accounting posting, payment, deployment or paid hosting was activated.

## Reproduced evidence and implementation boundary

The unchanged independent script reproduced the reported **21 OK, 11 WEAK, 3 NOTE**, exit 1, against the reviewed live source before modification. Its eleven failed IDs were RN02b, RN05b, RT09c, RT12b, RT12d, RT10b, RT14b, RT14c, RT14e, RT15 and RT19a. The existing 111 tests passed at that point. Raw logs are in `docs/reverification/baseline-independent-probes.txt`, `baseline-independent-exit.txt` and `baseline-tests.txt`.

The implementation order was RV-04, RV-03, RV-01, RV-02, RV-05, RV-06, then RV-07–RV-13 and RV-14–RV-17. The Python/SQLite/local HTTP stack is unchanged. All 22 new independent input files, the four previous verification inputs and three frozen review archives have preservation hashes in `docs/reverification/input-checksums.json`. None was edited or overwritten. The original reference handoff was left intact. All behavioral tests use temporary synthetic databases; the existing accounting database was not used as a test fixture or rewritten.

## Corrections and regression coverage

`tests/test_reverification_controls.py` adds 20 regression methods; `tests/test_reverification_gate.py` adds five acceptance/preservation methods, including two RT14b positive-setup fault tests. Assertions pair refusal paths with working independent approval paths. All 41 platform/HTTP methods from the Batch 1 baseline remain present and pass; the earlier initial accounting archive has 40, also all retained, as Fable's own static evidence reports. The reviewed Batch 2 checkpoint has 43, all retained as well. Changes to their fixtures are documented in DECISIONS.md, including explicit freshness and mandatory acceptance of revised support. No expected-failure marker is retained to demand an accounting defect stay broken.

| Ticket | Correction actually running | Acceptance evidence |
| --- | --- | --- |
| RV-04 | Binding an already admitted snapshot to the same period writes nothing; later-month intake no longer invents late receipts or post-finalization events. Genuine revised locked evidence remains quarantined. | RT12b/c, RN02; `test_RV04_locked_receipts_are_not_rebound_by_unrelated_intake` |
| RV-03 | Latest completed run membership defines governing items. Departures get ITEM_LEFT_POPULATION events, superseded exceptions/history and `removed_items` in state, outcomes and frozen packages. Empty projections also retain removal evidence. | RT12d, RN02; tombstone/finalization and removed-quarantine tests |
| RV-01 | Both envelope and data supersession resolve immutable source identity/links. Locked-origin replacements and their receipts stay quarantined; reopening releases routing and removes the old governing item. Superseded approved sources raise accounting events. | RN02b, RT12d, FV-C13; lock/reopen/history test. Unresolved predecessors remain explicit held transitions. |
| RV-02 | Journal/card origin ownership uses canonical source identity across revisions and supersession. An obsolete cited version adds ORIGIN_SOURCE_SUPERSEDED; citing the current version does not remove the ownership conflict. | RT15; historical/current-reference collision test; FV-J01–J10 unchanged |
| RV-05 | Independent profile approval appends effective retirement records for withdrawn profile-derived rules. Earlier dates retain their historical rule; deliberate reintroduction creates a usable rule again. | RT09a/b/c, FV-C01/C15; future-date withdrawal/reintroduction test |
| RV-06 | New profiles/rules require typed close entries. Demo reconciliation and tie-out requirements cannot be completed by labels. Legacy stored bare strings remain unsatisfied with UNTYPED_REQUIREMENT. | RT19a/b, FV-CL01/02/04; profile/rule refusal and legacy evaluation test |
| RV-07 | Dispositions enforce activity and account types: expense coding cannot name cash/liability, credits cannot disguise payments, and settlement/transfer require active asset accounts. Fee/interest choices are explicit. Referral remains nonclearing. | RT14e; invalid-treatment tests; valid credit/settlement paths in RT14a/RG0 |
| RV-08 | Distinct-purchases decisions bind the exact duplicate candidate identity/hash set independently of optional statement references. New candidates deactivate the decision. | RT14b with valid positive support; third-candidate regression |
| RV-09 | An excluded duplicate suppresses its proposed entry and supplies disposition/evidence/contributor lineage to the surviving item. Revocation restores both holds. Returning to an earlier input state creates a current projection and preserves any original rejection. | RT14c; exclusion/revocation, contributor denial and rejection-restoration regressions |
| RV-10 | Semantically retained aliases/categories and receipt policies keep relevant prior authors/approvers in item provenance. A materially different historical category alone does not bar an unrelated reviewer. | RN05b, RN04/05, RT09b; cosmetic-versus-different-category regression |
| RV-11 | Freshness must be nonempty, well-formed and limited to workflow source kinds. The sole explicit no-evidence form requires a nonempty reason and independent audited approval. Migration suspends legacy empty-freshness mandates. | RT10a/b; schema/reason/audit checks; dedup/cap/expiry/revocation tests use explicit authority |
| RV-12 | Changed receipt/document versions expose old/new refs, suppliers and changed fields, and add EVIDENCE_REVISED_REQUIRES_REVIEW. Acceptance requires a granted human who supplied none of the versions; final review is separate. Receipt mismatch/unset-policy referrals preserve the hold. | Revised-document and supplier-refusal regressions; RT12a/RG0 adapted positive setup; delivered teaching month retains original TX-009 support |
| RV-13 | Statement workpapers and items expose line identity, continuity and provenance assurance. Missing identities hold unless an applicable independently approved rule permits them. A configured prior period with no statement holds; quarantined revisions cannot displace its frozen statement. | RT13/RT13n, FV-C08/C09/C19; missing-ID/rule and frozen-prior regression |
| RV-14 | Rule records shown through state/export include normalized aliases, collision rule IDs, approval status and retirement-aware effective end. | RT09d; alias-preview regression |
| RV-15 | A disposition requires relevant support beyond its own row. Distinct purchases require receipt proof for every candidate, with supplier provenance propagated. | RT14d unchanged negative; supported RT14a positive; candidate-document regression |
| RV-16 | Change inventory and patch include Python, JSON, JavaScript, HTML and CSS. Both cumulative Batch 1 and this correction pass have explicit archive baselines. | Runtime inventory regression; original `evidence/static_checks.py` output in `docs/reverification/final-static-checks.txt` |
| RV-17 | Each new immutable preparation package names `supersedes_package_id`; state/export/UI identify governing versus historical packages without altering prior bytes. | RT18; package-chain/frozen-payload regression |

Migrations 13–14 add rule retirement and suspend unsupported old authority without rewriting evidence, artifacts, decisions or packages. Source, audit and contributor history remain scoped and append-only. A new governing projection may reuse an identical immutable artifact, including its rejection; historical execution alone cannot become current merely because its fingerprint matches.

## Exact gate results

Environment: Python 3.9.6, SQLite 3.51.0. HTTP integration tests had temporary local loopback access. No network accounting service was used.

| Command | Exit | Observed result | Raw evidence |
| --- | --- | --- | --- |
| `make test` | 0 | **136 tests, OK**, including all original 41 methods | `docs/reverification/final-tests-release.txt` |
| `make check` | 0 | Python syntax, JSON/profile/registry and DOM checks pass; no external JS compiler/typechecker claim | `docs/reverification/final-check.txt` |
| `make batch2-gate` | 0 | **29 PASS, 10 FIXED, 21 DEFERRED-OK**; maintained Batch 2 probes and teaching month pass | `docs/reverification/final-batch2-release.txt`, `docs/batch2/final-validation.json` |
| `make reverification-gate` | 0 | **28 unchanged-setup probes OK** directly from the supplied script; **35 OK** through the setup-only adaptation; unmodified frozen corrective checkpoint passes | `docs/reverification/final-reverification-release.txt` |
| Original independent `evidence/static_checks.py` | 0 | No computed-but-unlisted files, missing patch entries or listed hash mismatches; all original test methods retained | `docs/reverification/final-static-checks.txt` |
| Original supplied full command on current code | 1 | API-setup incompatibilities: three ERROR and three WEAK; see below. This command is **not claimed to pass**. | `docs/reverification/current-original-probes.txt` |

All 60 reviewer case IDs and their raw outcomes are retained individually in `docs/batch2/final-validation.json`. The 21 DEFERRED-OK cases assert that unavailable AP/AR/reconciliation/reporting and other deferred operations are refused; they do not validate future accounting functionality. No assigned correction is reclassified as deferred.

The normal test gate also verifies preserved input/archive hashes, runs the 28 unchanged probes and all 35 control assertions, and checks new failure paths. `make reverification-gate` additionally runs the supplied old corrective script against its frozen checkpoint, where N01–N07 still report OK. Intermediate diagnostic failure logs are retained; `final-*-release.txt` identify the combined release results.

## Required probe-contract adaptations — awaiting Fable judgment

RV-11 rejects `{}` freshness, RV-12 requires independent acceptance after changed support, and RV-15 requires evidence for all duplicate candidates. Seven original **positive** setups therefore require explicit current inputs: RN02, RN03, RN07, RT12a, RT14a, RT14b and RG0. No runtime compatibility bypass or implicit policy activation was added to preserve unsafe setup.

The original full command reports RN02/RN03/RN07 ERROR because they create empty-freshness mandates; RT12a/RG0 WEAK because they expect immediate eligibility after support revisions; RT14a WEAK because its distinct-purchase support omits peer receipts. RT14b otherwise prints OK vacuously after its initial positive dispositions are refused. The strengthened adaptation supplies valid support and now asserts success of both initial dispositions and D1 eligibility before D3 is constructed or intaken. Its original final verdict remains unchanged. Two added fault-injection tests require assertion failure when either initial decision is refused or D1 is ineligible. Raw targeted evidence is in docs/reverification/rt14b-strengthened-probe.txt and rt14b-fault-regressions.txt. The full seven-probe explanation and unchanged accounting-control conditions are in docs/reverification/probe-adaptations.md.

The separate `review/fable_reverification_probes.py` preserves **every original verdict-return and gate expression**. `scripts/build_reverification_adapter.py` checks their AST equivalence and supplies a patch in `docs/reverification/reverification-probe-adaptations.patch`. Positive mandates now state an audited reason for fixed-evidence authority; positive distinct-purchase decisions cite candidate receipts; positive support revisions must first show the hold/history, then be accepted through the granted non-supplier dispositioner. The original negative empty freshness and own-row-only evidence probes are untouched. Final approvals remain independent.

This uses the API-change exception explicitly allowed in the supplied corrections JSON. Read `docs/reverification/probe-adaptations.md` and judge the exact delta independently. **Passing the adapted gate is developer evidence, not independent acceptance of the adapter or the original full command.**

## Teaching month: original evidence retained

The delivered `scripts/synthetic_month.py` now leaves TX-009's 79.99 receipt unchanged and records external referral of its mismatch. It produces **ten preparation approvals and three held dispositions**: pending TX-007, receipt mismatch TX-009, and foreign-currency TX-011. October TX-008 and its receipt remain quarantined and named. Two immutable preparation handovers and the November lock acknowledge these carried issues without turning them into clean approvals or final close.

Independently asserted approved proposed-entry impact:

| Fictional account | Impact |
| --- | ---: |
| DEMO_OFFICE_SUPPLIES | +311.00 |
| DEMO_REPAIRS | +200.00 |
| DEMO_CARD_LIABILITY | −211.00 |
| DEMO_CASH | −300.00 |
| Net | 0.00 |

The adapted independent RG0 exercises the other permitted RV-12 route: it preserves original support history, explicitly accepts the corrected document, and retains the original eleven-approval and 391.00 office-supplies assertions. These are two disclosed routes, not interchangeable claims about one run. Both assert scoped second-client December isolation and audit integrity. They do not establish G0 acceptance or a complete accounting month.

## Changed files, handoff and unresolved boundary

`docs/reverification/changed-files.json` and `source-and-tests.patch` compare actual current source, tests, scripts, web assets and documentation against the reviewed `exports/FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip`. `docs/batch2/changed-files.json` and patch provide the corrected cumulative Batch 1 comparison. Core correction areas are `source_control.py`, `service.py`, `controls.py`, `exceptions.py`, `modules.py`, `packages.py`, `storage.py`, `demo.py`, the demo profile, and the web UI. Tests, maintained reviewer fixtures, synthetic-month script, gates and documentation reflect the explicit contracts above. Exact files/hashes are in the inventories and outer REVIEW_MANIFEST.json.

The new archive is `exports/FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip`; prior ZIPs are preserved and nested. It contains source/tests, both inventories, original independent evidence, new raw command results, a current exact prompt in FABLE_REVERIFICATION_PROMPT.md and FABLE_RV_CORRECTIONS_HANDOFF.md. Runtime databases, credentials and live client records are excluded.

All 17 assigned corrections have developer regression evidence. No confirmed assigned correction is knowingly left failing under the documented current setup. Independent re-verification, acceptance of the adapted positive setups, and human G0 acceptance remain unresolved. UC-2 (frozen prior-statement lookback) and UC-3 (approved supporting-document change events) gained regression coverage within this work. UC-1 (possible false mandate suspension as new evidence crosses a mid-period rule date), UC-4 (automatic restoration after a superseder is removed), and UC-5 (synthetic grant administration/revocation) remain unverified concerns; no fix or PASS is claimed for them.

No actual Bird Bowl accounting facts/policies were invented. Actual recognition, chart/mappings, fee/interest and FX treatment, receipt correction rules, reviewers and completeness require authorized client validation. AP, AR, full reconciliation, reporting, production identity/reliability, consistent live exports and external audit anchoring remain deferred. G1–G4 and all live/write actions remain closed. The next action is independent verification of this correction checkpoint, not Batch 3.
