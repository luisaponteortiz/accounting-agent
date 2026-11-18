# Six accounting capability areas and extension contracts

Design coverage is distinct from implementation. This file defines module seams for progressive execution under the shared runner. Entries marked deferred have no executable handler and cannot be invoked as successful tools.

## Common contract

Every workflow binds organization/client/environment, legal entity/book identity, period, currency, workflow/capability/shared-control versions, approved client-knowledge version, evidence manifest, preparer and review policy. A handler receives only scoped snapshot data and prior declared dependencies; it returns structured artifact data, evidence references, blocking exception codes and review eligibility. Trusted orchestration controls persistence and authority. No handler approves itself or executes an external side effect.

Core persistent records: client profile versions; source snapshots (immutable source key, version, content/hash); runs/steps (dependencies, leases, attempts/checkpoints); artifacts; decisions; mandates/occurrences; audit. The current implementation has these records. Future normalized domain entities below enter as evidence plus typed module contracts before dedicated storage is introduced. A design entity below is not an already-created database table.

Shared validation covers exact money, scoped identity, declared period/currency/account checks, no ambiguity guessing, deterministic reproducible calculations, input lineage and current-version independent review. Client choices cover accounting framework/basis, materiality, tolerances, recognition, tax, accounts/dimensions, receipt policy, matching/aging/report definitions, procedures, authority and effective dates. USD/two-decimal fixture formatting is a supported demo contract, not a universal currency rule.

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
- `banking.card_prepare` executes the limited fictional card workflow. `banking.match_transfer_reconcile` is deferred. Card payments/credits/splits/FX/transitions remain exceptions; no lifecycle resolution is claimed.
- Public API capability for pending feed UI actions and reconciled status must be verified separately from ledger operations before integration; no private endpoint workaround.

## 5. Month-End Close

- Domain entities: versioned close checklist/DAG, expected sources, account reconciliations, subledger ties, accruals, reversals, adjusting proposals, review/sign-off records and period-lock requests.
- Inputs: client close procedure, GL/AP/AR/banking outputs with actual source/review/external status, complete required statements and assigned authority. Outputs: available-work packet, missing prerequisites, proposed adjustments, close-readiness matrix and final human decision request.
- Controls: dependency versions and status; balance/evidence/source-completeness checks; independent review; actual posting/reconciliation verification; no calendar-triggered completion; no approval inherited from last period. Block only dependent tasks, while exposing package-level incompleteness.
- `close.readiness` executes document-presence/missing-evidence checks only. It always preserves external-step and final-signoff holds. It does not yet verify that document contents establish accounting completion. `close.accruals_adjustments_signoff` is deferred.
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

Current onboarding is a Python service API with isolation tests; onboarding screens, client policy-approval lifecycle, effective-dated historical-rule activation, real secrets/identity and live connectors are deferred. Current JSON export preserves knowledge/evidence/decisions for inspection; trusted execution import of a complete operating knowledge package is not yet implemented.
