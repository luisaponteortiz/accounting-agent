# Record of the human G0 re-affirmation (D-039)

17 November 2026. The owner's words and what they cover are in D-039 at the end of `DECISIONS.md`.

The owner re-affirmed G0 for the source as it stands after the feed-contract changes of D-038. It is the same statement as D-036: the software controls behave as specified on fictional data. It opens no later gate.

No separate review examined the D-038 changes. The re-affirmation rests on the evidence in `docs/feed_decisions_uc21_uc23/`: Fable's review tests, the re-run suite and gates, and the earlier reviewers' unmodified probes. No register record was raised or re-based, and a later source change would fall outside it.

| File | Content |
| --- | --- |
| `record_g0_reaffirmation.py` | The assertion-checked script that made every edit, including the full D-039 text. |
| `before.sha256`, `after.sha256` | SHA-256 of the nine working documents before and after. Each before-hash equals the after-hash recorded for D-038. |
| `final-checks.txt` | `make check`, the documentation checker (39 decisions) and 53 documentation, register and protected-input methods in the working project after the edits. All pass. |
| `verify_preservation.py`, `preservation.json` | Read-only preservation check on the final state: all 1,198 protected inputs, 16 earlier archives, the RF and RE bundles and responses and all 298 returned RF response files unchanged; branch, HEAD and ten commits untouched; nothing staged. |

Only nine documents changed: `DECISIONS.md`, `docs/CONNECTION_READINESS.md`, `PROGRESS.md`, `AGENTS.md`, `README.md`, `START_HERE.md`, `FABLE_ACCOUNTING_HANDOFF.md`, `REVIEW_FREEZE.md` and `HANDOFF_RF_REGISTRATION_2026-11-17.md`. Every source, test, script and review file is identical to the state validated for D-038, so the full suite and gates were not re-run. The product register did not change. Nothing is committed.
