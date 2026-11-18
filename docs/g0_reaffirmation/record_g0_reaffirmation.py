"""Record the owner's re-affirmation of human G0 for the source as changed under D-038 (D-039). Documents only; every replacement is asserted to match exactly once."""
import sys
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
def edit(name,pairs):
    path=ROOT/name;text=path.read_text()
    for old,new in pairs:
        assert text.count(old)==1,(name,text.count(old),old[:70])
        text=text.replace(old,new)
    path.write_text(text)

D039='''
## D-039 — Owner decision: human G0 re-affirmed for the source as changed under D-038 — 17 November 2026

After the validation of the D-038 changes finished and its results and limits were reported, the owner was asked "Do you re-affirm G0 for the source as it now stands?" and answered:

> Yes, re-affirm G0

**Human G0 (Synthetic acceptance) is re-affirmed by the accounting owner on 17 November 2026 for the working source as it stands after D-038.**

- **What is re-affirmed.** The same statement as D-036 and nothing wider: the software controls behave as specified on fictional data. It is not a claim about accounting correctness, any client or readiness. The state it covers is the working project as validated for D-038: the 107 source, test, script, review and document files whose hashes are in docs/feed_decisions_uc21_uc23/validation/tested-source-sha256.json, uncommitted, on the ten commits at 5af9a6194bc39e2f303cc6b43b0b59094118b8e4.
- **What the owner had before deciding.** One complete, unmodified validation of that state on a disposable clone: make test with 274 of 274 methods; make check and the eight gate targets, all passing; the RE review's unmodified probes at 19 OK with C9c and C9g NOTE; the RF review's unmodified probes at 14 OK with G1c NOTE; the documentation checker; and the preservation check. The owner was also told that the first full run had failed on the RB review's unmodified probe N01e, that the change was narrowed instead of the probe, that two cases of UC-21 are deliberately left as before, and the limits listed in D-038.
- **How its basis differs from D-036.** The acceptance in D-036 followed an independent review of the RF checkpoint. No separate review has examined the D-038 changes. For those changes this re-affirmation rests on Fable's own review tests, the re-run suite and gates, and the earlier reviewers' unmodified probes, as the working model of D-036 and D-037 allows. The seven Independently verified records still cite the RF checkpoint; no record is raised or re-based by this decision, and no review result is pinned for it.
- **What it does not open.** No gate opens the next one. G1 still needs written answers to client questions 1 to 7 from the people with authority, client approval to use named sample records in a local unconnected environment, real identity, chart and rules entered as proposed and approved through the rule lifecycle, a held-out month, a named human reviewer who is not the preparer, and the owner's explicit G1 authorization. G2–G4, Batch 3, deferred and Proposed capabilities, real integrations, paid or model services, sending, posting, payment, hosting and deployment remain closed. A later change to application source would again fall outside this re-affirmation.
- **Records changed with this decision.** Documents only: docs/CONNECTION_READINESS.md, PROGRESS.md, AGENTS.md, README.md, START_HERE.md, FABLE_ACCOUNTING_HANDOFF.md, REVIEW_FREEZE.md and HANDOFF_RF_REGISTRATION_2026-11-17.md. No requirement record, register text, source, test, schema, probe, gate script, checker or derived result changed. Earlier decisions stay as written, including the sentence in D-038 that left this question to the owner. The record and its checks are in docs/g0_reaffirmation/. Ten commits on review/fable-rc-acceptance are preserved; nothing staged, no commit added. U4, UC-14, UC-17, UC-18 and UC-20 remain open. No further implementation is authorized.
'''
path=ROOT/'DECISIONS.md';text=path.read_text()
assert '## D-039' not in text and text.endswith('no further implementation is authorized.\n')
path.write_text(text+D039)

edit('docs/CONNECTION_READINESS.md',[
 ('**Local fictional preparation only. Human G0 was accepted by the accounting owner on 17 November 2026 (D-036); no later gate is open.**',
  '**Local fictional preparation only. Human G0 was accepted by the accounting owner on 17 November 2026 (D-036) and re-affirmed the same day for the source as changed under D-038 (D-039); no later gate is open.**'),
 ('- [x] Human G0 acceptance based on that independent verification: accepted by the accounting owner on 17 November 2026 (D-036)',
  '- [x] Human G0 acceptance based on that independent verification: accepted by the accounting owner on 17 November 2026 (D-036). Re-affirmed the same day for the source as changed under D-038 (D-039); for those changes the basis is Fable\'s review tests, the re-run suite and gates and the earlier reviewers\' unmodified probes, not a separate review'),
])
edit('AGENTS.md',[
 ('Those two changes were made after the G0 acceptance and after the RF checkpoint that the Independently verified records cite.',
  'Those two changes were made after the G0 acceptance and after the RF checkpoint that the Independently verified records cite. In D-039 the owner re-affirmed G0 for the source as it stands after them, on the evidence of Fable\'s review tests, the re-run suite and gates and the reviewers\' unmodified probes; no separate review examined the changes, no record was raised or re-based, and a later source change falls outside the re-affirmation.'),
])
edit('README.md',[
 ('**The accounting owner accepted human G0 on 17 November 2026 (D-036)**: a statement',
  '**The accounting owner accepted human G0 on 17 November 2026 (D-036)** and re-affirmed it the same day for the feed-contract source changes of D-038 (D-039): a statement'),
])
edit('START_HERE.md',[
 ('**The accounting owner accepted human G0 on 17 November 2026 (D-036); no later gate is open.**',
  '**The accounting owner accepted human G0 on 17 November 2026 (D-036) and re-affirmed it for the source as changed under D-038 (D-039); no later gate is open.**'),
])
edit('FABLE_ACCOUNTING_HANDOFF.md',[
 ('**The accounting owner accepted human G0 on 17 November 2026 (D-036)**; no later gate is open;',
  '**The accounting owner accepted human G0 on 17 November 2026 (D-036)** and re-affirmed it for the source as changed under D-038 (D-039); no later gate is open;'),
])
edit('REVIEW_FREEZE.md',[
 ('Working files changed since the RF bundle only under five owner decisions: D-038 (',
  'Working files changed since the RF bundle only under six owner decisions: D-039 (the re-affirmation of human G0 for the source as changed under D-038, recorded in documents only), D-038 ('),
 ('Human G0 was accepted by the accounting owner on 17 November 2026 (D-036); G1–G4, Batch 3',
  'Human G0 was accepted by the accounting owner on 17 November 2026 (D-036) and re-affirmed for the changed source (D-039); G1–G4, Batch 3'),
])
edit('HANDOFF_RF_REGISTRATION_2026-11-17.md',[
 ('**The accounting owner accepted human G0 on 17 November 2026 (D-036).** G1 is the next gate',
  '**The accounting owner accepted human G0 on 17 November 2026 (D-036) and re-affirmed it for the source as changed under D-038 (D-039).** G1 is the next gate'),
 ('these two changes are covered by Fable\'s review tests and re-run gates, not by a pinned review.',
  'these two changes are covered by Fable\'s review tests and re-run gates, not by a pinned review.\n\n## G0 re-affirmed for the changed source (D-039)\n\nAfter the D-038 validation finished the owner re-affirmed G0 for the source as it now stands. It is the same statement as before: the software controls behave as specified on fictional data. No separate review examined the D-038 changes; the re-affirmation rests on Fable\'s review tests, the re-run suite and gates and the earlier reviewers\' unmodified probes. No record was raised or re-based, no gate opened, and a later source change would fall outside it. The record is in `docs/g0_reaffirmation/`.'),
 ('| Human G0 | Accepted by the accounting owner on 17 November 2026 (D-036). No action. |',
  '| Human G0 | Accepted by the accounting owner on 17 November 2026 (D-036) and re-affirmed for the source as changed under D-038 (D-039). No action. |'),
])
path=ROOT/'PROGRESS.md';text=path.read_text()
assert text.startswith('# Feed-contract decisions UC-21 to UC-23 — 17 November 2026\n')
path.write_text('''# Human G0 re-affirmed for the changed source — 17 November 2026

**The accounting owner re-affirmed human G0 on 17 November 2026 for the source as it stands after D-038; D-039 quotes the decision.** The owner accepted human G0 earlier the same day, after the independent RF review (D-036); the feed code then changed under D-038. Before re-affirming, the owner had the complete validation of that state first: 274 of 274 suite methods, make check and the eight gates passing, the reviewers' unmodified RE and RF probes, the preservation check, the failed first run and the limits. It is the same statement as D-036, that the software controls behave as specified on fictional data, and nothing wider. No separate review examined the D-038 changes: the re-affirmation rests on Fable's review tests, the re-run suite and gates and the earlier reviewers' unmodified probes. No register record was raised or re-based, and a later source change would fall outside it. The record is in docs/g0_reaffirmation/. G1–G4, Batch 3 and all live actions remain closed and no further implementation is authorized. The sections below are earlier checkpoints.

'''+text)
print('recorded')
