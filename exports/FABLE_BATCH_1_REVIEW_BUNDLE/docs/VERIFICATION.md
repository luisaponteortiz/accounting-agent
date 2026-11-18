# Verification record — Accounting Agent OS Batch 1

Environment/mode: local/demo. Data and actor identities: fictional. Runtime: Python 3.9.6 / SQLite 3.51.0. No third-party runtime installation, paid model, live connection, posting or deployment.

Before modification the original 41 tests passed and the supplied reviewer runner reproduced 28 PASS, 10 KNOWN-FAIL and 22 DEFERRED-OK. All 16 diagnostic probes were executed; original scripts and raw output remain available.

Final `make test`: **72 tests run, 67 passed and 5 expected failures** documenting unimplemented Batch 2 behavior. The original 41 test methods remain present and pass after intentional period/run-link adaptations recorded in DECISIONS.md. No unexpected failure/error/success. `make check` passes syntax, JSON/profile, DAG, DOM construction and documentation capability-ID checks. External lint/typechecker/JS compiler tools were not run.

The independent 60-case suite reports **28 PASS / 6 FIXED / 4 KNOWN-FAIL / 22 DEFERRED-OK**. The strict six-case Batch 1 gate passes. See docs/BATCH_1_REPORT.md and docs/batch1/final-validation.json for every case and its status. The original ten-case fixture is teaching-derived regression data, not independent validation.

Additional evidence covers scoped contributors, concurrent review/ticks/workers, governing reuse, dispute resolution, late evidence, multiple periods, lock/reopen, source quarantine, legacy immutable-byte preservation, foreign-key integrity and concurrent migration. The application-level socket-denial test remains passing; no OS firewall certification is claimed. Backup/restore and audit integrity remain tested; neither is a hosted retention/WORM guarantee.

Browser verification used a separate synthetic database on loopback port 8766: independent journal approval, December opened without staling November, November lock preserved approval, reopen succeeded, card receipt affected card work while journal approval stayed current, and selected-period re-preparation completed. The actual screen appears in docs/accounting-agent-os-demo.jpg; lock proof is docs/batch1/period-lock-preserves-approval.jpg. Both are included in the updated review bundle.

Fable's Batch 1 review is incorporated; its unresolved Batch 2/later findings are not declared fixed. Full synthetic G0, client accounting validation, Luis/Theresa human UAT, actual authority, real-model evaluation, connector validation, hosted UAT, live writes/reconciliation and final close remain unverified/deferred.
