# Six accounting capability areas and extension contracts

Current state (17 November 2026): the contracts below include the RB to RF corrections, and the independent RF review of them is registered; the accounting owner accepted human G0 on 17 November 2026 (D-036), and G1 to G4, Batch 3 and every deferred capability remain closed. The card-feed contract D-026 is summarized under Banking & Reconciliation and described in ARCHITECTURE.md.

The earlier RB correction response strengthened existing shared contracts only. A late/later-resolved supersession claim must inspect still-live locked ancestors before own destination admission. Replacement evidence includes re-pointed old keys as well as withdrawals. Relevant rule author history follows semantic coverage across general/item scopes and renamed keys. Statement continuity carries prior revision disclosure and depends on active own-period acceptance for every relying item; revocation invalidates that dependency. These additions do not implement reconciliation, new integrations or any deferred module. See corrections_rb/RB_CORRECTIONS_REPORT.md and PRODUCT_REQUIREMENTS.md for current evidence/state.

Design coverage is distinct from implementation. This file defines module seams for progressive execution under the shared runner. Entries marked deferred have no executable handler and cannot be invoked as successful tools.

## Common contract

Implemented envelopes bind organization/client/environment, entity/book, accounting period, workflow/capability/control versions, declared manifest, dependency hashes, fact waivers, applied rules and output. Immutable contributor lineage is separate from content identity. The common boundary enforces independent profile/rule/mandate approval, evidence-bound dispositions, review and preparation-package finalization. See ARCHITECTURE.md for exact lifecycle and limits.

Persistent records include scoped profile proposals/decisions, effective rules/decisions/retirements, authority grants, source snapshots/heads/ordering/links, period history/bindings/moves, runs/steps/leases, occurrences/mandates, artifacts/run links/contributors, decisions, exceptions/history, dispositions, accounting events, immutable packages and audit. The latest completed run defines governing item membership; removed items retain exception history and explicit package removal evidence. Packages name the prior version, with governing status derived without changing historical bytes. No new AP/AR or reconciled ledger domain is implied.

Supporting-evidence revisions are visible and held until a granted human who supplied none of their versions explicitly accepts them. Separate final review still applies. Dispositions bind the duplicate population and require support for each candidate; a valid duplicate exclusion carries provenance to the surviving item. Mandates require an explicit freshness predicate or independently approved reason for no evidence requirement. Statement artifacts disclose identity, continuity and provenance limits; typed close requirements cannot be satisfied by an untyped label.

Shared exact-money and entry validation is mechanical. Client policies still determine recognition, tax, materiality, accounts, tolerances, matching and procedures. Only explicit fictional entity/book/mappings are supplied. USD/two-decimal fixtures are not universal currency support. Every workflow starts with `evidence.inventory`, the scoped inventory of its declared sources, which is not proof of a complete population. `package.manifest` propagates package controls and records provenance; it cannot certify actual ledger completeness or final close.

## 1. General Ledger

- Domain entities: accounts and status/effective dates; transactions; proposed journal headers/lines; adjustments; accrual/reversal links; trial-balance snapshots; period locks and accounting decisions.
- Inputs: approved client chart, period/basis, business support, source ledger/trial balance and dimensions. Outputs: classification proposals, balanced journal workpapers, validation findings and account-maintenance requests.
- Controls: debits equal credits; no negative/both-sided/zero lines; active authorized accounts; no silent currency mixing; cutoff/lock checks; business rationale/evidence; independent exact-version review. A balanced journal can still be wrong accounting.
- Tools: `gl.journal_validate` executes synthetic mechanical validation; `gl.account_maintenance` and `gl.post` are deferred. Future adjustments, reversals and ledger reads get separate capabilities.
- Exceptions: unsupported account/dimension, unbalanced journal, missing support, closed period, ambiguous recognition, uncertain external outcome.
- Future live side effects: separately authorized application-owned ledger adapter; stable business operation ID, preflight duplicate/readback checks and outcome reconciliation. Never retry an unknown posting blindly.

## 2. Accounts Payable

- Domain entities: vendors; bills/credit memos; expense lines; purchase/receiving evidence; approval chains; due dates; payable balances; payment proposals and settlement references.
- Inputs: vendor master/version, invoices, receipt/purchase evidence where applicable, ledger/AP population, payment terms and actual client policies. Outputs: proposed bill/expense coding, duplicate/three-way-match exceptions, aging and payment proposal packets.
- Controls: vendor identity and change approval; invoice/source identity and number variants; duplicate checks across feeds/ledger; credit/refund handling; receipt/approval policy; subledger-control-account tie; currency/tax/dimensions; segregation of preparation, approval and payment execution.
- Initial tool `ap.bills_expenses_payments` is deferred; split bill preparation, aging, payment proposal and payment execution into separate tools when implemented. Payment execution remains a separately reserved capability.
- Exceptions: potential duplicate, invoice/receiving mismatch, changed bank instructions, missing evidence, unapproved supplier, disputed amounts, overpayment.
- Recurring dependency: current open-item population and approved evidence/policies; a recurring event cannot reuse stale payment authority.

## 3. Accounts Receivable

- Domain entities: customers, contracts/billing evidence, invoices/credit notes, receipts, allocations, unapplied cash, terms, aging buckets, disputes and collection status.
- Inputs: authorized billing terms, performed-service evidence, customer/AR populations and receipts. Outputs: invoice proposals, cash-application candidates, unapplied/mismatch exceptions and reproducible aging/collection workpapers.
- Controls: existence/cutoff/accuracy, invoice uniqueness, customer scope, credit approval, one receipt allocation budget, no many-to-one overapplication, ledger tie and client-defined aging policy. Preparing collection drafts never authorizes sending them.
- `ar.invoices_collections_application_aging` is deferred; later separate billing, receipt application, aging and collection-draft capabilities share the runner.
- Exceptions: disputed invoices, ambiguous customer/reference, short/overpayments, duplicate receipts, FX, unapplied cash and incorrect terms.

## 4. Banking & Reconciliation

- Domain entities: institution/account identity, source transaction lifecycle, statements, ledger populations, match allocations, transfers, timing items, reconciliations and verification evidence.
- Inputs: authoritative statement/complete transaction population, ledger extract and prior reconciliation, client mapping/matching rules and support. Outputs: intake inventory, proposed classifications/matches, transfer candidates, reconciliation workpapers and unresolved differences.
- Controls: stable source IDs; pending-to-posted revision/removal handling; one posting route; no reuse of a matched item; ambiguous matches hold; transfer counterpart/currency/period evidence; arithmetic plus source completeness; distinct prepared/posted/reconciled states. Equal totals do not prove completeness.
- `banking.card_prepare` executes the limited fictional card workflow. `banking.match_transfer_reconcile` is deferred. Human evidence-bound dispositions can resolve demonstrated credits, settlements, splits and duplicates into proposed entries. Foreign currency stays held; no FX policy is invented. Statement checks and source lifecycle execute; full reconciliation remains deferred.
- Card-feed contract (D-026, fictional card rows and receipts only): the highest provider order governs a row while older or conflicting messages are retained; a first replacement claim applies wherever it arrives and waits for an unknown target; a second claim naming a different target is recorded, not applied, and blocks the row with SOURCE_CLAIM_CONFLICT; a locked-period hold is never released by a provider message. Under D-038 an identical repeat of a row or receipt retired by a live, admitted replacement changes nothing, and a message with no order value for a row governed by one is kept once and flagged as a feed anomaly. The disposition choice `select_supersession_target` lets a person with disposition authority who supplied none of the claim messages state which declared target stands, with supporting evidence, and with lock authority where it releases a locked-period hold; it approves nothing and its author stays a contributor. Journals are excluded and real-provider behaviour is a G2 confirmation.
- Public API capability for pending feed UI actions and reconciled status must be verified separately from ledger operations before integration; no private endpoint workaround.

## 5. Month-End Close

- Domain entities: versioned close checklist/DAG, expected sources, account reconciliations, subledger ties, accruals, reversals, adjusting proposals, review/sign-off records and period-lock requests.
- Inputs: client close procedure, GL/AP/AR/banking outputs with actual source/review/external status, complete required statements and assigned authority. Outputs: available-work packet, missing prerequisites, proposed adjustments, close-readiness matrix and final human decision request.
- Controls: dependency versions and status; balance/evidence/source-completeness checks; independent review; actual posting/reconciliation verification; no calendar-triggered completion; no approval inherited from last period. Block only dependent tasks, while exposing package-level incompleteness.
- `close.readiness` executes typed workflow-outcome and period-bound evidence checks. It always preserves external-step and final-signoff holds. It does not yet verify that document contents establish accounting completion. `close.accruals_adjustments_signoff` is deferred.
- Recurrence: client-approved period calendar, current sources, effective procedure/authority and bounded occurrence; no automatic carryforward of an accrual or old sign-off.

## 6. Financial Reporting

- Domain entities: ledger/trial-balance snapshots, mapping/report definitions, statement lines, management dimensions, comparative/budget versions, calculations, variance explanations and review findings.
- Inputs: verified book and period, accounting basis, trial balance, source reconciliations, client report mappings and comparative/budget definitions. Outputs: source-tied statements, management workpapers, reproducible variances and evidence-labeled insights.
- Controls: statements tie to authoritative balances; balance sheet and movement/rollforward checks; P&L period/basis consistency; versioned comparative/mapping lineage; arithmetic/rounding policies; missing scope/dimensions explicit; distinguish calculated variance from proposed causal explanation; no invented forecast/business facts.
- `reporting.statements_management_variances_insights` is deferred; later separate statement assembly, management reports, variance calculations and model-assisted interpretation. Model commentary remains a proposal.
- Exceptions: incomplete/untied trial balance, changed chart/report mapping, missing comparatives, incompatible basis, unsupported consolidation/intercompany eliminations and ungrounded explanations.

## Onboarding/knowledge progression

1. Register an isolated client identity and actual authorized facts; the demo only accepts synthetic profiles without credentials.
2. Capture procedures, source versions, framework/basis, chart, systems, authority and decision scope. Proposed rules stay proposed.
3. Obtain accounting validation, version/effective period and approver for actual reusable policy. Transaction-specific corrections never silently broaden.
4. Validate modules against separate expected results and missing/ambiguous cases; preserve coverage gaps.
5. Authorize only tested workflows, inputs, recurring triggers, review boundaries and budgets. Add connector capabilities individually after validation.

Current onboarding and approved effective-dated knowledge run through the scoped Python service API with isolation tests. Full onboarding screens, real secrets/identity and live connectors remain deferred. Current JSON export preserves knowledge/evidence/decisions for inspection; trusted execution import of a complete operating knowledge package is not yet implemented.

## RA control amendments

Current source identity/period contracts resolve a complete supersession chain under lock and release terminal replacements only. Evidence-revision contracts include replaced receipt keys and revised/replaced statements; related source history and supplier independence remain bound to item acceptance and separate final review. Supporting references must be relevant documents, not arbitrary transaction rows. Approved rule identity history preserves relevant authorship without optional-link dependence. Mandate policy signatures use relevant effective windows independently of evidence arrival. Active duplicate/replay decisions must target a retained live item. These are shared-control corrections; no deferred accounting capability is activated.
