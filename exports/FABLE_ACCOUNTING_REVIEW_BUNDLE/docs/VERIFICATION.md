# Verification record — 0.1.0

Date: November 14, 2026 (client date). Environment: local. Mode/provider: demo/fixture. Source versions: fictional-demo-1, teaching-v1, separate validation cases V-01–V-10, late-receipt-v1. Actors: scoped synthetic preparer/reviewer/worker. Outbound effects: none. Application source hash can be reproduced from the review-bundle manifest; runtime input lineage is present in exported artifacts.

## Automated software acceptance: passed

Command: `python3 -m unittest discover -s tests -v`.

Actual result: **41 tests passed in 8.312 seconds**, including 8 black-box HTTP tests and 10 separate regression subcases. Expected result: deterministic outcomes, explicit holds, no unauthorized approval, no cross-client access, no duplicated committed artifacts/occurrences, durable recovery and no external effects. Evidence: `tests/test_platform.py`, `tests/test_http.py`, `tests/test_validation.py`, `accounting_agent/fixtures/validation.json`.

Covered behavior:

- Three workflow modules through the same runner and committed dependency outputs with hash lineage.
- Clean/missing/ambiguous/duplicate/pending/credit/payment/split/currency/cutoff card cases.
- Exact journal balancing and invalid account/line/period/currency/support rejection.
- Missing-close evidence, unverified external steps and pending final human sign-off.
- Replay idempotency; source revisions and late duplicate/evidence invalidation.
- Preparers denied approval; exact-hash decisions; independent reviewer; immutable histories; revocation.
- Two client profiles using the same engine; backend client/company/route/query-scope denial.
- Crash/expired lease recovery; stale worker rejection; concurrent workers; checkpoint rollback and bounded failures.
- Scoped mandate occurrence deduplication/caps; persisted simulated clock; expiry/revocation; independent work continuation; silence leaves review pending.
- Required unavailable model review remains blocked; hosted/connected/non-synthetic activation denied.
- Real HTTP server/worker results, session requirement, loopback-only binding, Host/Origin protection, safe static responses and invalid-request denial.
- Full inspection export, source/decision/audit preservation, package hash, changed-input export rejection, backup/restore integrity.
- Engine/review/export execute with application outbound socket/DNS calls denied in-process. No OS-level egress sandbox claim.

Command: `python3 scripts/check.py`.

Actual result: passed syntax, JSON/profile validation, DAG/tool-registration and DOM construction checks. No external typechecker/linter/JavaScript compiler was installed or claimed.

## Browser/developer acceptance: passed within synthetic scope

Actual functional app inspected using browser automation; 15 initial preparation items, 2 eligible and 13 held. Independent review saved without external posting. Missing-receipt arrival invalidated prior approvals; re-preparation produced 3 eligible and 12 held. Duplicate simulated events returned one recurring run; worker completed its checkpoints. Six accounting areas clearly display partial/deferred coverage. Final server release reloaded and receipt replay confirmed no input/approval changes.

Screenshot: `docs/accounting-agent-os-demo.jpg`. Retained synthetic database includes the walkthrough's source/review/audit history; exports contain full records. No screenshots of mockups were used as workflow proof.

## Other acceptance states

| Stage | Status | Reason |
| --- | --- | --- |
| Senior accounting design review / Fable | Pending | Handoff prepared; response not yet supplied |
| Actual Bird Bowl accounting validation | Not run | Approved chart/policies/procedures/sample results unavailable |
| Luis / Theresa human UAT and teach-back | Not run | Developer synthetic testing is separate |
| Real-model evaluation | Not run | No model API or paid calls authorized |
| Live connector validation | Not run | No client systems connected |
| Hosted staging UAT / production readiness | Not run | Hosting, authenticated identity, production persistence and authority unverified |
| Ledger writes / reconciliation verification / final close | Not run | Capabilities disabled/deferred |

Open findings/limitations are recorded in PROGRESS.md and docs/CONNECTION_READINESS.md. These results establish a working local foundation; they do not establish full-cycle accounting correctness or operating readiness.
