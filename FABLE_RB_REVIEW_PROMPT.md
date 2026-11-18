Act as the independent senior accounting architect, accounting-controls reviewer and technical verifier for Accounting Agent OS.

Independently verify RB-01–RB-04 and the PR-01–PR-17 correction response in this bundle. Treat Codex’s descriptions, delivered logs and passing labels as claims, not acceptance evidence. Do not implement fixes during verification.

Accounting Agent OS is a universal six-function accounting platform. Bird Bowl is the first client implementation, not the product boundary. Client facts, policies, systems and authority remain isolated and unverified where stated. The current application is local, fictional preparation software; future shared requirements are not implemented capabilities.

READ FIRST AND VERIFY INTEGRITY

Read these original findings, which must remain unchanged:
- exports/FABLE_RA_ACCEPTANCE/FABLE_RA_CORRECTIONS.json
- exports/FABLE_RA_ACCEPTANCE/FABLE_RA_ACCEPTANCE_REPORT.md
- exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_CORRECTIONS.json
- exports/FABLE_PRODUCT_REQUIREMENTS/FABLE_PRODUCT_REQUIREMENTS_REVIEW.md

Then read FABLE_RB_CORRECTIONS_HANDOFF.md, docs/corrections_rb/RB_CORRECTIONS_REPORT.md, PR_DISPOSITION.md, execution-results.json, changed-files.json, both patches, docs/PRODUCT_REQUIREMENTS.md, AGENTS.md, DECISIONS.md and PROGRESS.md. Paths abbreviated after docs/corrections_rb/ refer to that directory.

Verify REVIEW_MANIFEST.json and actual source against the complete change inventory. The inventory baseline is the frozen combined submission: its nested RA source plus its separate documentation addendum. Verify the original inputs and preservation hashes. The frozen combined ZIP must remain at SHA-256 b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea; the returned review-response ZIP must remain at d38e0e27b30e46d2e4690b5366aa3fa237d5733e23783c64082c39ca4ff30f84.

This new outer ZIP is the runnable correction-response project. Run commands from its extracted root containing Makefile and accounting_agent/. Nested archives are historical evidence. Prompt-packaging changes are documented separately in docs/corrections_rb/prompt-bundle-addendum.json; they do not introduce new runtime changes or new test results.

REPRODUCE THE GATES

Use disposable synthetic databases. Run:

make test
make check
make batch2-gate
make reverification-gate
make acceptance-gate
make rb-gate
python3 scripts/check_product_requirements.py --json
python3 exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py .

Independently reproduce or correct the reported 174 passing tests: all 154 prior methods in 16 byte-identical original test files, plus 20 new methods. No skip or expected failure may conceal a corrected defect. The HTTP tests need temporary loopback access; an earlier sandbox bind failure is preserved, followed by a complete successful loopback-enabled run. Mark unavailable execution NOT_RUN; distinguish your runs from inspection and delivered logs.

Every one of the 14 latest independent probes must report OK, including R04c. None may remain NOTE, WEAK or ERROR. The script must be unmodified. Verify that normal tests and make rb-gate enforce those exact outcomes.

Individually report all 60 older cases: the claimed result is 29 PASS / 10 FIXED / 21 DEFERRED-OK, with zero unexpected outcomes. Deferred refusal is not implemented accounting functionality.

Retain C/RV/RA/Batch 2 controls, the seven accepted adaptations, strengthened RT14b and the five accepted statement setups. U4 remains the permitted NOTE only in its older acceptance gate. The older literal full commands still fail at disclosed setup incompatibilities; inspect those raw results and do not relabel them PASS. No new adaptation to the latest 14-probe script is claimed or permitted silently.

CHALLENGE THE ACCOUNTING CONTROLS

Test every assertion in your original RB tickets and add independently authored positive and negative cases:
- RB-01: late links on previously admitted and already approved destination sources; unresolved links resolved later; multiple depths and arrival orders; transaction/support quarantine and visible root history; removal of destination governing approval and corresponding events; blocked move evidence; no same-period move rows; authorized reopen admits only the terminal replacement; relock/restart/replay remain safe. One economic charge must never remain approved in both periods.
- RB-02: receipt and statement replacement by re-pointing the old key, in addition to same-key revision and withdrawal; disclosure of earlier/current identity, versions, fields and suppliers; both suppliers refused; granted non-supplier acceptance remains item-bound and separate from final review; later changes lapse acceptance. A genuine additional still-active document remains a multiple-support question.
- RB-03: equivalent vendor mappings and receipt policies under renamed keys and general-to-item scope changes retain relevant authors; unrelated clients, item scopes, descriptions, categories and policy values do not bar a legitimate independent reviewer.
- RB-04: disclose revised/replaced lookback statements to the relying period; continuity stays unverified with no or partial own-period acceptance; all relying items require active acceptance; revocation/new evidence invalidates dependent preparation/approval; acceptance actors remain relevant contributors. Preserve frozen locked-period lookback and do not silently authenticate a restated balance.

Re-drive both teaching-month routes, package immutability, period locks and second-client isolation. Verify actual accounting-entry impact and required holds, not merely successful API responses. These demonstrations are preparation, not posting, reconciliation completion or final close.

VERIFY THE PR CORRECTIONS

Review every PR-01–PR-17 disposition against its exact criteria. The register now claims 88 retained records, preserving all original 76 IDs. Check separate Product decision and Implementation state fields, scope/evidence notes, Needed for classifications, dependency direction/conditionality, backlog crosswalks, source traces and testable owner/gate parameters.

Seven affected records intentionally retain Verification failed pending your independent re-verification. Do not mistake that honest status for an unfixed code finding, or developer passes for independent acceptance. Any new verification conclusion must identify its source checkpoint and precise scope.

Fault-test the register checker for duplicate/lost IDs, missing fields, unknown/cyclic dependencies, missing backlog tickets, mixed/unsupported states, missing evidence and first-client conditions in shared criteria. Confirm make check invokes it and enforces the client-neutral shared-code notice. Confirm AGENTS.md has one current authorization, evidence/promotion/downgrade rules, conflict handling and isolated client-fact placement.

Verify proposed shared onboarding/offboarding, connector, operating-summary, deposit/settlement and consolidation records; named integrations must instantiate the shared contract. Client-specific system/intake questions belong in the client section. Exclusions versus reserved actions, outside-application procedure capture versus G1 processing, close-package elements/five states, task coverage and pending owner decisions must be explicit. Do not classify an intentionally deferred feature as a current defect or treat a documented proposal as approved implementation. State which PR findings are corrected, which remain deficient and which legitimately await product/client decisions.

RETURN NEW FILES

Return without overwriting supplied originals:
1. FABLE_RB_ACCEPTANCE_REPORT.md — separate verdicts for each RB ticket, retained controls, preservation and G0 technical criteria; lead with confirmed blockers.
2. FABLE_RB_ACCEPTANCE_RESULTS.json — every assertion/probe/case, command, environment, exit, evidence pointer and explicit NOT_RUN/DEFERRED result.
3. FABLE_RB_CORRECTIONS.json — confirmed reproducible defects with stable IDs, severity, affected requirement/source/function/line, minimal reproduction, expected/actual, accounting consequence, smallest correction, dependencies/order and exact regression assertions. Separate unverified concerns and deferred enhancements; use an empty confirmed list if none remain.
4. FABLE_PR_REVERIFICATION_REPORT.md and FABLE_PR_REVERIFICATION_CORRECTIONS.json — finding-by-finding PR verdicts, current gaps and remaining owner decisions, prioritized for incorporation.
5. fable_rb_acceptance_probes.py, fable_rb_acceptance_output.txt and evidence/ — independent service-only temporary-data probes and raw reproducible logs/scripts. Explain any test-only adaptation; preserve original control assertions.

No live connections, client-record uploads, paid services/model calls, sending, posting, payments, production changes or deployment. Do not begin Batch 3, redesign the product or rewrite the stack. Technical acceptance does not grant human G0, G1–G4, Batch 3 or operating authority. Return concrete independent acceptance or implementable corrective findings.
