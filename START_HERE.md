# Current state: RF review registered — 17 November 2026

The independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 with no corrective ticket, and it is registered (D-033/D-034): no requirement is Verification failed. **The accounting owner accepted human G0 on 17 November 2026 (D-036) and re-affirmed it for the source as changed under D-038 (D-039); no later gate is open.** Start with [the latest handoff, which lists what opening G1 requires](HANDOFF_G1_PREPARATION_2026-11-17.md), then [the registration handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md), [the registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and [the G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md). `make test` runs 274 methods. No further implementation is authorized; Batch 3 and all live actions remain closed.

The sections below are earlier checkpoints, kept as written at the time. Their "pending" statements describe those dates, not today.

# RE/PRV correction checkpoint — independent verification pending

This pass covers RE-01–RE-03 and PRV-14/15 under D-026 and owner clarification D-029. Start with [the handoff](FABLE_RE_CORRECTIONS_HANDOFF.md), [report](docs/corrections_re/RE_CORRECTIONS_REPORT.md), [owner clarification](docs/corrections_re/CONTRACT_CLARIFICATION.md) and [exact Fable prompt](FABLE_RE_REVIEW_PROMPT.md). Developer validation passes 227 tests and all named gates, with zero double approval in 336 extended and 120 retained orders. The owner's answer preserves frozen approval and blocks the incoming version until reopen; the dedicated check passes and reopen retains the contested blocker. No schema, branch or commit change; three requirements remain Verification failed pending independent RE verification. Batch 3, deferred/Proposed capabilities and live actions remain closed. Earlier checkpoints below are historical.

# RD/PRV review checkpoint — 16 November 2026

This pass is complete for developer review: RD-01/RD-02 and PRV-11–PRV-13 only. Start with [the handoff](FABLE_RD_CORRECTIONS_HANDOFF.md), [correction report](docs/corrections_rd/RD_CORRECTIONS_REPORT.md), and [exact Fable verification prompt](FABLE_RD_REVIEW_PROMPT.md). The new ZIP/checksum is under `exports/FABLE_RD_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip`. Developer validation passes 205 tests, all gates, zero double approval in 120 delivery orders, and 37/37 plus 44/44 register fault cases. Three requirement states remain Verification failed pending independent RD review. Five commits and every earlier archive/input remain unchanged. Batch 3, deferred/Proposed capabilities and live actions remain closed; await independent results and a new assignment. The sections below preserve prior checkpoints.

# RC/PRV review checkpoint

Extract FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip into a new disposable directory. This archive is a directly runnable project root. Keep its embedded historical ZIPs intact; do not overlay their contents onto this source.

1. Read FABLE_RC_CORRECTIONS_HANDOFF.md and FABLE_RC_REVIEW_PROMPT.md.
2. Read docs/corrections_rc/RC_CORRECTIONS_REPORT.md for the ticket matrix, developer results, intermediate failures and limits.
3. Verify REVIEW_MANIFEST.json and the adjacent archive checksum before running commands. docs/corrections_rc/input-checksums.json protects the supplied independent inputs, earlier archives and original reference/config/fixture material.
4. Inspect docs/corrections_rc/changed-files.json and source-and-tests.patch against the immutable V2 bundle. The inventory separates pre-existing differences, including D-016/D-017, from this pass.

The three RC-affected requirements remain Verification failed pending independent re-verification. N02c/UC-10 and N04e/UC-11 remain policy observations. Human G0, G1–G4, Batch 3, all deferred capabilities and all live actions remain closed.
