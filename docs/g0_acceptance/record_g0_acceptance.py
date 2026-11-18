"""Record the owner's human G0 acceptance (D-036) in the decision log and the living documents."""
import sys
from pathlib import Path
root=Path(sys.argv[1])
def once(t,old,new,n=1):
    assert t.count(old)==n,(old[:70],t.count(old));return t.replace(old,new)
def edit(name,pairs,prepend=None,append=None):
    p=root/name;t=p.read_text()
    for old,new in pairs:t=once(t,old,new)
    if prepend:t=prepend+t
    if append:t=t.rstrip('\n')+'\n'+append
    p.write_text(t)
G0='a statement that the software controls behave as specified on fictional data'
# DECISIONS
edit('DECISIONS.md',[],append='''

## D-036 — Owner decision: human G0 accepted; Fable designated architect and reviewer — 17 November 2026

The owner, who is the product owner and accounting lead (D-016), wrote:

> I accept G0, record it
>
> You are the architecture and the reviewer. Remove any limitations

**Human G0 (Synthetic acceptance) is accepted by the accounting owner as of 17 November 2026.**

- **What the owner had before deciding.** The independent RF review with no corrective ticket; its registration (D-033/D-034); the six-criterion check in docs/G0_CRITERIA_CHECK_2026-11-17.md, which found five criteria met on the evidence and "Documentation matches code" not met; the documentation-only pass that addressed it (D-035); and the stated limits of each. One listed documentation gap remains: the header counts inside review/FABLE_VALIDATION_CASES.json, a protected reviewer input, say 28/10/22 while its cases are 29/10/21.
- **What G0 is.** Section 9 of review/FABLE_ARCHITECTURE_REVIEW.md: it permits "A statement that the software controls behave as specified on fictional data" and does not permit "Any claim about accounting correctness, Bird Bowl, or readiness". This acceptance is that statement and nothing wider.
- **What it does not open.** No gate opens the next one. G1 still needs written answers to client questions 1 to 7 from the people with authority, client approval to use named sample records in a local unconnected environment, real identity, chart and rules entered as proposed and approved through the rule lifecycle, a held-out month, a named human reviewer who is not the preparer, and the owner's explicit G1 authorization. G2–G4, Batch 3, deferred and Proposed capabilities, real integrations, paid or model services, sending, posting, payment, hosting and deployment remain closed. D-016/D-017, every BB-01/BB-02 field and December 2026 as the held-out month are unchanged.
- **Architect and reviewer.** The owner designates Fable (Claude) as the project's architect and reviewer. On that basis the owner accepts the RF result registration (D-033/D-034) and the documentation pass (D-035), both carried out by a Fable session, without requiring a separate review. The living documents that listed the absence of a separate review as an open limitation now record this decision instead. The fact itself stays on record: the same Fable session registered its own review's verdicts and wrote the documentation it then checked.
- **How "Remove any limitations" was applied (the recorder's reading, not the owner's words).** It was applied to the open limitation above. It was not read as opening any later gate, authorizing implementation, changing D-026 or D-029, deciding UC-21 to UC-25, or deleting the recorded limits of what the evidence covers: fictional data only; journals excluded by D-026; principally two periods and one card account; the target-selection HTTP route not independently probed beyond developer tests; no real provider; no human operating readiness. Those describe what was tested and can change only through new assigned work and its review. If the owner intends more, a specific assignment naming the gate or the work is required.
- **Records changed with this decision.** docs/CONNECTION_READINESS.md (G0 checked), the current-evidence text, three crosswalk rows and one change-log row of docs/PRODUCT_REQUIREMENTS.md, PROGRESS.md, AGENTS.md, README.md, START_HERE.md, docs/ARCHITECTURE.md, docs/CAPABILITY_CONTRACTS.md, FABLE_ACCOUNTING_HANDOFF.md, REVIEW_FREEZE.md, HANDOFF_RF_REGISTRATION_2026-11-17.md and the criteria check. No requirement record, implementation state, acceptance criterion, product decision, source, test, schema, probe, gate script, checker or derived result changed. make check, the register tests and the decision-log test pass after the edits; the full suite and gates were not re-run because nothing they exercise changed since D-034/D-035. Ten commits at 5af9a6194bc39e2f303cc6b43b0b59094118b8e4 on review/fable-rc-acceptance are preserved; nothing staged, no commit added. Owner observations UC-21 to UC-25 remain open with U4, UC-14, UC-17, UC-18 and UC-20. No further implementation is authorized; await a new specific assignment.
''')
# CONNECTION_READINESS
edit('docs/CONNECTION_READINESS.md',[
 ('**Local fictional preparation only. Human G0 has not been accepted.**','**Local fictional preparation only. Human G0 was accepted by the accounting owner on 17 November 2026 (D-036); no later gate is open.**'),
 ('Human G0 is the next gate and remains the accounting owner\'s separate decision; owner observations','G0 is '+G0+', not a claim about accounting correctness, any client or readiness. G1 is the next gate and needs written client facts and the owner\'s explicit authorization; owner observations'),
 ('- [ ] Human G0 acceptance based on that independent verification','- [x] Human G0 acceptance based on that independent verification: accepted by the accounting owner on 17 November 2026 (D-036)')])
# Register (text outside the requirement records)
p=root/'docs/PRODUCT_REQUIREMENTS.md';t=p.read_text()
t=once(t,'no corrective ticket; human G0 not granted; Batch 3 closed.**','no corrective ticket; human G0 accepted by the owner on 17 November 2026 (D-036); G1–G4 and Batch 3 closed.**')
t=once(t,'Independent verification of these controls is not human G0 acceptance and grants no G1–G4, Batch 3 or live authority.','Independent verification of these controls is not itself human G0 acceptance; the accounting owner gave that separately on 17 November 2026 (D-036). Neither grants G1–G4, Batch 3 or live authority.')
t=once(t,'UC-21–UC-25 open for the owner; no human G0 or readiness authority.','UC-21–UC-25 open for the owner; human G0 accepted separately by the owner (D-036); no readiness authority.',3)
last='| Owner assignment D-035; docs/G0_CRITERIA_CHECK_2026-11-17.md. |\n'
t=once(t,last,last+'\n| 2026-11-17 | Recorded the accounting owner\'s acceptance of human G0 in the current-evidence text and the T-12, RA-01 and RB-01 crosswalk rows. G0 is a statement that the software controls behave as specified on fictional data. No requirement record, state, criterion or product decision changed; G1–G4 and Batch 3 remain closed. | Owner decision D-036. |\n')
p.write_text(t)
# PROGRESS
edit('PROGRESS.md',[],prepend='''# Human G0 accepted — 17 November 2026

**The accounting owner accepted human G0 (Synthetic acceptance) on 17 November 2026; D-036 quotes the decision.** G0 is '''+G0+'''. It is not a claim about accounting correctness, any client or readiness. The owner had the independent RF review, its registration, the six-criterion check and the documentation pass before deciding. The owner also designated Fable (Claude) as the project's architect and reviewer and accepted the registration and the documentation pass without a separate review.

No later gate is open. G1 needs written client facts from the people with authority, client approval of named sample records, a held-out month, a named reviewer who is not the preparer, and the owner's explicit G1 authorization. G2–G4, Batch 3, deferred and Proposed capabilities and all live actions remain closed. Owner observations UC-21 to UC-25 are open with U4, UC-14, UC-17, UC-18 and UC-20. No further implementation is authorized. The sections below are earlier checkpoints, written before this decision.

''')
# AGENTS
edit('AGENTS.md',[('Human G0 is the accounting owner\'s separate decision and has not been given. Await the owner\'s decision on G0 and on observations UC-21 to UC-25, and a new specific assignment,',
 'The accounting owner accepted human G0 on 17 November 2026 (D-036): '+G0+', not a claim about accounting correctness, any client or readiness. The owner designates Fable (Claude) as the project\'s architect and reviewer and accepted the registration and the documentation pass without a separate review. G0 opens no later gate: G1 needs written client facts from the people with authority, client approval of named sample records, a held-out month, a named reviewer who is not the preparer, and the owner\'s explicit G1 authorization. Await the owner\'s decision on observations UC-21 to UC-25 and a new specific assignment')])
# README, START_HERE, ARCHITECTURE, CAPABILITY_CONTRACTS, Fable handoff, freeze
edit('README.md',[('**Human G0 has not been accepted**; it is the accounting owner\'s decision.','**The accounting owner accepted human G0 on 17 November 2026 (D-036)**: '+G0+', not a claim about accounting correctness, any client or readiness. It does not start G1.')])
edit('START_HERE.md',[('**Human G0 has not been accepted.**','**The accounting owner accepted human G0 on 17 November 2026 (D-036); no later gate is open.**')])
edit('docs/ARCHITECTURE.md',[('Human G0 and Batch 3 remain closed.','The accounting owner accepted human G0 on 17 November 2026 (D-036); G1 to G4, Batch 3 and all live actions remain closed.')])
edit('docs/CAPABILITY_CONTRACTS.md',[('human G0, Batch 3 and every deferred capability remain closed.','the accounting owner accepted human G0 on 17 November 2026 (D-036), and G1 to G4, Batch 3 and every deferred capability remain closed.')])
edit('FABLE_ACCOUNTING_HANDOFF.md',[('were done by a Claude (Fable) session at the owner\'s assignment and have not themselves been independently reviewed. **Human G0 has not been accepted**;','were done by a Claude (Fable) session at the owner\'s assignment; the owner designates Fable as the project\'s architect and reviewer and accepted both without a separate review (D-036). **The accounting owner accepted human G0 on 17 November 2026 (D-036)**; no later gate is open;')])
edit('REVIEW_FREEZE.md',[('Human G0, G1–G4, Batch 3 and all live actions remain closed;','Human G0 was accepted by the accounting owner on 17 November 2026 (D-036); G1–G4, Batch 3 and all live actions remain closed;')])
# Handoff
edit('HANDOFF_RF_REGISTRATION_2026-11-17.md',[
 ('Human G0 has not been accepted; it is the accounting owner\'s decision and the next gate.','**The accounting owner accepted human G0 on 17 November 2026 (D-036).** G1 is the next gate and is not open.'),
 ('| Human G0 | Accept or withhold, as accounting owner. Nothing in the reviews or this registration grants it. |','| Human G0 | Accepted by the accounting owner on 17 November 2026 (D-036). No action. |'),
 ('- **Neither the registration change nor the documentation pass has been independently reviewed.** A Claude (Fable) session performed it at the owner\'s assignment, and Fable also performed the independent RF review. The owner was told this before authorizing.','- **The registration and the documentation pass were performed by a Claude (Fable) session, and Fable also performed the independent RF review.** The owner was told this before authorizing. On 17 November 2026 the owner designated Fable as the project\'s architect and reviewer and accepted both without a separate review (D-036).'),
 ('## Decisions waiting for the owner','''## G0 accepted (D-036)

G0 is '''+G0+'''. It is not a claim about accounting correctness, any client or readiness, and it opens no later gate. G1 needs written answers to client questions 1 to 7 from the people with authority, client approval to use named sample records in a local unconnected environment, real identity, chart and rules entered as proposed and approved through the rule lifecycle, a held-out month, a named reviewer who is not the preparer, and the owner's explicit G1 authorization.

D-036 also records how the owner's words "Remove any limitations" were applied: to the open limitation that the registration and documentation pass had no separate review. They were not read as opening a gate or as deleting the recorded limits of what the evidence covers. A wider meaning needs a specific assignment.

## Decisions waiting for the owner''')])
# Criteria check
edit('docs/G0_CRITERIA_CHECK_2026-11-17.md',[],append='''
## Addendum: G0 accepted by the owner (D-036)

With this check, its limits and the first addendum in front of them, the accounting owner accepted human G0 on 17 November 2026. D-036 quotes the decision. The owner also designated Fable (Claude) as the project's architect and reviewer and accepted the registration and the documentation pass without a separate review. The acceptance is the statement G0 permits, that the software controls behave as specified on fictional data, and it opens no later gate. The limits listed in this document still describe what the evidence covers.
''')
print('ok')
