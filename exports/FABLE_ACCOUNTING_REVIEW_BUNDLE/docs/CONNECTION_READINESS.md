# Connection and release readiness

**Status: local synthetic only. No request to connect is pending.** A successful demo grants no additional authority.

- [x] General accounting module contracts and executable common runner
- [x] Synthetic profiles, evidence, work state, exceptions and version-bound review
- [x] Automated unit/integration/HTTP tests and local backup/restore exercise
- [ ] Fable senior accounting architecture/control review incorporated and retested
- [ ] Luis/client validation of actual accounting system/migration, legal entity, accounts/currencies/periods, chart, procedures, source completeness and accounting policies
- [ ] Actual human preparer/reviewer/exception/close authority and client engagement/support responsibilities agreed
- [ ] Approved sample evidence with known reviewed results and independent validation cases
- [ ] Theresa's observed independent operation, teach-back, review/correction time, interruptions and escalation verified
- [ ] Hosting/platform capability/authority/costs agreed with Jeff and relevant owners
- [ ] Supported Python/service runtime, authenticated identity, scoped secret store, production persistence/migrations, logs, backups and restore tested
- [ ] Per-client connector capability inventory and provider documentation verified for the specific required operation
- [ ] Exact provider, purpose, account owner, data scope, read permissions, environment, cost ceiling and validation step authorized
- [ ] Real schedule/event delivery and evidence-freshness/period policies validated; no fixture authority promoted
- [ ] Live write capability separately designed, tested and authorized, including idempotency, unknown-outcome reconciliation and verification

Deferred adapters are **not implemented-unconnected connectors**. QBO, Desktop, bank/card feeds, Expensify, document providers and model APIs are all unconnected and no provider is selected. Do not copy company-wide credentials to a client deployment. A per-client future secret reference must resolve only within that client's authorized environment; raw keys never belong in profile JSON or exports.

The local HTTP server and synthetic role selector cannot be hosted. A hosted release requires a separate authenticated implementation and actual database/worker integration tests. No Render provisioning, infrastructure costs, subscription charges or accounting effects were incurred by this build.
