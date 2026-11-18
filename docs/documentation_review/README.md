# Evidence for the documentation review tests and the verification-rule change (D-037)

17 November 2026. The owner's two instructions and the record of the work are in D-037 at the end of `DECISIONS.md`.

## Results

| Check | Result |
| --- | --- |
| Complete `make test`, unmodified, on a disposable clone byte-identical to the final working project | exit 0; 262 of 262 methods in 1,087.671 s; all 11 HTTP methods and all 12 documentation review methods pass |
| `make check` in the working project | passes |
| `python3 scripts/check_documentation.py` | PASS; facts in `check-result.json` |
| Documentation review, register and decision-log tests in the working project (53 methods) | pass |
| Preservation | all 1,198 protected inputs, 16 earlier archives, the RF and RE bundles and responses and all 298 returned RF response files unchanged; branch, HEAD and ten commits untouched; nothing staged |

The gates were not re-run: no application source, probe or gate script changed.

## Files

| File | Content |
| --- | --- |
| `review-tests.txt` | Verbose output of the twelve review methods. Each asserts that a check passes on the project and refuses faults injected into copies of the document texts. |
| `check-result.json` | The facts the checker established on the final state. |
| `make-test.stdout.txt`, `make-test.stderr.txt` | The complete suite run. |
| `final-checks.txt` | The checks run in the working project. |
| `apply_rule_change.py` | The assertion-checked script that changed the rule wording in AGENTS.md and the register, added the register change-log and T-08 text, and adjusted one registration test. |
| `adapted-registration-method-before.py`, `-after.py`, `.diff` | The one earlier test method changed: it now expects the single AAOS-GOV-02 sentence to differ from the RF checkpoint and asserts that nothing else in that criterion does. The before-text equals the method as recorded in `docs/registration_rf/registration.patch`. |
| `before.sha256`, `after.sha256` | SHA-256 of the existing files before and after this step, and of the two new files. |
| `preservation.json` | Read-only preservation check on the final state. Its general flag for "every acceptance criterion unchanged" is false by design; the fields beside it name the one criterion that changed (AAOS-GOV-02) and show that no product decision did. |

## Limits

The checks are fixed patterns over the current-state sections of ten documents. A stale statement worded differently would pass, and history sections, dated reports and earlier handoffs are outside them. The register checker does not yet enforce the statement the changed rule requires of a self-reviewed record. Nothing is committed.
