"""Documentation-only pass (owner assignment 17 November 2026): README, START_HERE, architecture, capability contracts."""
import sys
from pathlib import Path
root=Path(sys.argv[1])
def once(t,old,new):
    assert t.count(old)==1,(old[:70],t.count(old));return t.replace(old,new)
def line_starting(t,start,new):
    lines=t.split('\n');hits=[i for i,l in enumerate(lines) if l.startswith(start)]
    assert len(hits)==1,(start[:50],len(hits));lines[hits[0]]=new;return '\n'.join(lines)
RF='c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd'
# ---------------- README
p=root/'README.md';t=p.read_text()
t=line_starting(t,'The current [RB correction handoff]',
 '**Current state (17 November 2026).** The independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 with no corrective ticket, and that review is registered: the register has seven Independently verified records and none Verification failed. Read the [current handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md), the [registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and the [G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md). **Human G0 has not been accepted**; it is the accounting owner\'s decision. The register has 88 retained records; proposed shared additions are documentation, not implemented features.')
t=line_starting(t,'The exact [RB/PR Fable verification prompt]',
 'The correction handoffs, review prompts and reports for the RA to RF passes remain in the repository as dated records of each checkpoint. [DECISIONS.md](DECISIONS.md) and [PROGRESS.md](PROGRESS.md) hold the full history; all delivered archives and reviewer inputs are immutable.')
t=once(t,'make acceptance-gate\n','make acceptance-gate\nmake rb-gate\nmake rc-gate\nmake rd-gate\nmake re-gate\nmake rf-gate\n')
t=once(t,'The current RA correction pass adds regression coverage and the independent acceptance gate; exact final counts and results are in docs/acceptance_ra/execution-results.json.',
 'The suite has 250 test methods; the latest complete results for the suite and all gates are in docs/registration_rf/commands/. The rb to rf gates run the independent reviewers\' unmodified probes and delivery-order searches; rf-gate takes about 50 minutes.')
t=once(t,'| Recurrence | Independently approved bounded mandates',
 '| Card-feed contract (D-026) | Provider order, replacement claims on late, older or conflicting messages, contested-target holds, and a recorded target selection under disposition and lock authority, for fictional card rows and their receipts | Journals, confirmation against a real provider (G2), and a web control for target selection |\n| Recurrence | Independently approved bounded mandates')
t=line_starting(t,'See [architecture](docs/ARCHITECTURE.md)',
 'See [architecture](docs/ARCHITECTURE.md), [capability contracts](docs/CAPABILITY_CONTRACTS.md), the [RF registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and the [current handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md). The original ss_agent_system_handoff/ package is preserved as reference; executive/marketing/sales work remains outside scope.')
t=once(t,'Fable accepted 14 of 17 RV corrections and all seven earlier probe adaptations, including strengthened RT14b, then identified RA-01–RA-08. This pass addresses those findings.',
 '**History of the RA pass, kept as written at that checkpoint.** Fable accepted 14 of 17 RV corrections and all seven earlier probe adaptations, including strengthened RT14b, then identified RA-01–RA-08. This pass addresses those findings.')
t=once(t,'Independent acceptance of these additions and G0 remain pending. No real operating readiness or Batch 3 authority is claimed.',
 'Independent acceptance of these additions and G0 remain pending. No real operating readiness or Batch 3 authority is claimed. (Since then the RA to RF reviews have returned; see the current state above.)')
p.write_text(t)
# ---------------- START_HERE
p=root/'START_HERE.md';t=p.read_text()
assert t.startswith('# RE/PRV correction checkpoint — independent verification pending')
t=('# Current state: RF review registered — 17 November 2026\n\n'
 'The independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 with no corrective ticket, and it is registered (D-033/D-034): no requirement is Verification failed. **Human G0 has not been accepted.** Start with [the current handoff](HANDOFF_RF_REGISTRATION_2026-11-17.md), [the registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and [the G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md). `make test` runs 250 methods. No further implementation is authorized; Batch 3 and all live actions remain closed.\n\n'
 'The sections below are earlier checkpoints, kept as written at the time. Their "pending" statements describe those dates, not today.\n\n')+t
p.write_text(t)
# ---------------- ARCHITECTURE
p=root/'docs/ARCHITECTURE.md';t=p.read_text()
t=line_starting(t,'Current corrective checkpoint: the returned RA review was not accepted;',
 'Current checkpoint (17 November 2026): the independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 at checkpoint '+RF+' with no corrective ticket, and that review is registered in the product register (D-033/D-034). Human G0 and Batch 3 remain closed. The sections from "RV correction details" onward record each correction pass in order and are written as of that pass; the RB to RF passes and the card-feed contract are described at the end. The product register separates product decisions from implementation/verification states; proposed shared requirements do not activate modules.')
t=once(t,'Capabilities declare rule kinds and date-governing source kinds as well as source/profile reads.',
 'Each of the three workflows starts with the shared capability `evidence.inventory`, which lists the scoped sources the workflow declares and blocks with NO_SOURCE_EVIDENCE when there are none, and ends with `package.manifest`, which records the input fingerprint and scope and states that nothing was posted or signed off. Neither proves a complete ledger or statement population. Capabilities declare rule kinds and date-governing source kinds as well as source/profile reads.')
assert t.endswith('No accepted developer fixture establishes actual client policy, G0 acceptance, final close or production readiness.\n')
t+='''
## RB, RC and RD correction boundary

RB-01–RB-04 corrected late-link locked-origin routing, re-pointed support replacement, semantic author retention across scope/key changes and prior-statement revision continuity; the independent RB review accepted RB-02–RB-04. RC-01–RC-03 and RD-01/RD-02 then closed further arrival orders of the locked-origin control. A replacement claim persists by row identity: an unchanged row that first declares a claim on an unknown target gets a new source version and is blocked at once, any earlier open-period approval stops governing before the target arrives, a later version that omits the claim does not withdraw it, and the claim links when the target arrives without the claimant being re-sent. Cycle and self-supersession refusals stay atomic. Transition acceptance is bound to the exact resolved chain and lapses when that chain changes. The independent RC and RD reviews accepted these corrections.

## Card-feed contract and target selection (D-026)

The owner's feed contract D-026, with clarification D-029, governs fictional card transaction rows and their receipts. Journals are outside it, and whether a real provider behaves this way is a G2 confirmation. It is implemented in `accounting_agent/feed_contract.py` on the existing append-only accounting events, source links and dispositions; no schema changed. Its promise is that, for every delivery order the contract allows, one charge is never approved in a locked period and again in an open one, and nothing leaves a locked-period hold without a person's authority. It does not promise identical intermediate records in every order.

- **Provider order.** Where messages carry a sequence number or timestamp, the highest governs the row. An older or conflicting message is retained as a source version with an audit record and never replaces the governing row.
- **Replacement claims.** A message may declare that its row replaces another. The first claim for a row is recorded (SOURCE_CLAIM_DECLARED) and applied wherever it arrives: on the governing version, on a newly retained older or conflicting version, or on a re-send of a message already retained. If the target is on file, the rows are linked and approvals along the chain raise approved-source events. If it is not, the claim waits (SOURCE_SUPERSESSION_UNRESOLVED), the row is blocked, and it links when the target arrives.
- **Repeats and omissions.** Repeating a claim the row already has changes no source lifecycle record. A new batch keeps its own delivery record; an exact replay adds nothing.
- **Second claim naming a different target.** It is recorded (SOURCE_CLAIM_CONFLICT_RECORDED) and not applied. The row and its live replacements carry the SOURCE_CLAIM_CONFLICT blocker and any approval stops governing. The row is neither moved into a hold nor out of one, and the second target is not retired. Further different targets join the same open question.
- **Locked periods.** If a chain reaches a locked period, the row, its live replacements and their receipts are held under that period. A provider message alone never releases the hold. An approval already frozen in the row's own locked period is preserved and the incoming version is held until an authorized reopen; reopen does not clear a contested-claim blocker.
- **Target selection.** Only a recorded disposition clears the contested-claim blocker: choice `select_supersession_target` with payload `target_key`, through the ordinary disposition operation (service call or POST /api/dispositions) for a single card item in its accounting-date period. It requires the reviewer role with a disposition grant, a target among the row's declared targets, an open home period, current scoped supporting evidence related to the item, no cycle, and a person who supplied none of the row's claim messages. When the selection changes the standing target and would release a held charge from a locked period other than the new target's origin, the same person must also hold the lock grant. It records SOURCE_CLAIM_TARGET_SELECTED and approves nothing. Confirming the standing target moves nothing. A selection is not revoked through the ordinary revocation route; a new equally authorized selection replaces it, and new different claims reopen the question.
- **Review independence.** Every person who recorded a target selection for a row, or for any row it was ever linked to, stays a contributor of the row, its revisions and its live replacements, and so cannot review or finalize them. As delivered, a selector is also a contributor of that card run's period-level artifacts (owner observation UC-23).
- **Report cost.** Within one database transaction and one report calculation, a run's currentness is computed once; outside a transaction every artifact is evaluated afresh.

The local web page has no control for target selection. Open questions for the owner are U4, UC-14, UC-17, UC-18 and UC-20 to UC-25 in the RF review's observations. The independent RE review accepted RE-02 and RE-03; the independent RF review accepted the rest and verified the promise above in 3,120 stepwise delivery orders. That is evidence for the orders tried on fictional data, not proof for every provider or client workflow.
'''
p.write_text(t)
# ---------------- CAPABILITY_CONTRACTS
p=root/'docs/CAPABILITY_CONTRACTS.md';t=p.read_text()
t=once(t,'The RB correction response strengthens existing shared contracts only.',
 'Current state (17 November 2026): the contracts below include the RB to RF corrections, and the independent RF review of them is registered; human G0, Batch 3 and every deferred capability remain closed. The card-feed contract D-026 is summarized under Banking & Reconciliation and described in ARCHITECTURE.md.\n\nThe earlier RB correction response strengthened existing shared contracts only.')
t=once(t,'package.manifest propagates package controls and records provenance;','Every workflow starts with `evidence.inventory`, the scoped inventory of its declared sources, which is not proof of a complete population. `package.manifest` propagates package controls and records provenance;')
t=once(t,'- Public API capability for pending feed UI actions and reconciled status must be verified separately',
 '- Card-feed contract (D-026, fictional card rows and receipts only): the highest provider order governs a row while older or conflicting messages are retained; a first replacement claim applies wherever it arrives and waits for an unknown target; a second claim naming a different target is recorded, not applied, and blocks the row with SOURCE_CLAIM_CONFLICT; a locked-period hold is never released by a provider message. The disposition choice `select_supersession_target` lets a person with disposition authority who supplied none of the claim messages state which declared target stands, with supporting evidence, and with lock authority where it releases a locked-period hold; it approves nothing and its author stays a contributor. Journals are excluded and real-provider behaviour is a G2 confirmation.\n- Public API capability for pending feed UI actions and reconciled status must be verified separately')
p.write_text(t)
print('ok')
