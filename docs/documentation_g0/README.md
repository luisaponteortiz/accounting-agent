# Evidence for the documentation-only pass (D-035)

17 November 2026. Owner assignment and developer record: D-035 in `DECISIONS.md`. Finding that led to it: [G0 criteria check](../G0_CRITERIA_CHECK_2026-11-17.md).

| File | Content |
| --- | --- |
| `before.sha256`, `after.sha256` | SHA-256 of the twelve working documents before and after the pass. |
| `six-documents.patch` | Exact diff of README.md, START_HERE.md, docs/ARCHITECTURE.md, docs/CAPABILITY_CONTRACTS.md, FABLE_ACCOUNTING_HANDOFF.md and REVIEW_FREEZE.md against the delivered RF bundle, to which each was byte-identical before the pass. |
| `register.patch` | Exact diff of docs/PRODUCT_REQUIREMENTS.md. Reversing its edits reproduces the pre-pass file hash in `before.sha256`. |
| `edit_core_documents.py`, `edit_handoff_freeze_register.py` | The assertion-checked replacement scripts that made those edits. |
| `make-test.stdout.txt`, `make-test.stderr.txt` | One complete unmodified `make test` on a disposable clone taken after the document and register edits: exit 0, 250 of 250 methods, 1,041.974 s. |
| `final-checks.txt` | `make check`, the 40 register tests and the decision-log test in the working project after D-035 was appended. |
| `preservation.json`, `verify_preservation.py` | Read-only preservation check on the final state. |

DECISIONS.md was only appended to (its RF-checkpoint bytes remain a prefix). PROGRESS.md, AGENTS.md, HANDOFF_RF_REGISTRATION_2026-11-17.md and docs/G0_CRITERIA_CHECK_2026-11-17.md received notes about this pass; for those four only the before and after hashes are recorded here, not a diff.

No application source, test, schema, probe, gate script, checker or derived result changed, and the gates were not re-run. Nothing is committed. This pass is developer-side work and is not an independent assessment of the sixth G0 criterion.
