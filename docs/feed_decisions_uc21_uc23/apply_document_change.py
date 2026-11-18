"""Record owner decision D-038 and bring the documents and the documentation checker into line with it."""
import sys,re
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root))
def once(t,old,new,n=1):
    assert t.count(old)==n,(old[:80],t.count(old));return t.replace(old,new)
def edit(name,pairs,prepend=None,append=None):
    p=root/name;t=p.read_text()
    for item in pairs:t=once(t,*item)
    if prepend:t=prepend+t
    if append:t=t.rstrip('\n')+'\n'+append
    p.write_text(t)
import scripts.check_documentation as cd
N=cd.test_method_count(root)
# checker: the new feed code must be described too
edit('scripts/check_documentation.py',[("SOURCE_(?:CLAIM|SUPERSESSION)[A-Z_]*|select_supersession_target","SOURCE_(?:CLAIM|SUPERSESSION|ORDER)[A-Z_]*|select_supersession_target")])
# stated suite size
edit('README.md',[('The suite has 262 test methods','The suite has %d test methods'%N)])
edit('START_HERE.md',[('`make test` runs 262 methods','`make test` runs %d methods'%N)])
# architecture
edit('docs/ARCHITECTURE.md',[
 ('An older or conflicting message is retained as a source version with an audit record and never replaces the governing row.',
  'An older or conflicting message is retained as a source version with an audit record and never replaces the governing row. One ordering scheme applies to a row (D-038): a message with no order value for a row governed by one, carrying different data, is kept once however often it repeats, never governs, and is flagged as SOURCE_ORDER_MIXED in the state, the export and the Source evidence view of the local page. The same data without an order value is an ordinary repeat and is not flagged.'),
 ('A later version that does not repeat a claim does not withdraw it.',
  'A later version that does not repeat a claim does not withdraw it. Under D-038 the same holds for an identical repeat, claim included, of a row or of its receipt that a live replacement has retired: no new version, no change, and the batch keeps its delivery record. A re-send with a newer order value, a re-send after the provider withdrew the replacement or the row itself, and a re-send that omits a claim the row has are recorded as before.'),
 ('As delivered, a selector is also a contributor of that card run\'s period-level artifacts (owner observation UC-23).',
  'A selector is also a contributor of that card run\'s period-level artifacts: the statement workpaper, the inventory and the package manifest. The owner accepted this stricter scope in D-038.'),
 ('Open questions for the owner are U4, UC-14, UC-17, UC-18 and UC-20 to UC-25 in the RF review\'s observations.',
  'The owner decided UC-21 to UC-23 in D-038; UC-24 is carried to upgrade notes and UC-25 needs no action. U4, UC-14, UC-17, UC-18 and UC-20 remain open.'),
 ('That is evidence for the orders tried on fictional data, not proof for every provider or client workflow.',
  'That is evidence for the orders tried on fictional data, not proof for every provider or client workflow. The D-038 changes were made after that review. They are covered by review tests Fable built (tests/test_feed_repeat_decisions.py) and by re-running the reviewers\' unmodified probes, searches and gates, not by a separate review.')])
edit('docs/CAPABILITY_CONTRACTS.md',[
 ('a locked-period hold is never released by a provider message.','a locked-period hold is never released by a provider message. Under D-038 an identical repeat of a row or receipt retired by a live replacement changes nothing, and a message with no order value for a row governed by one is kept once and flagged as a feed anomaly.')])
# readiness, AGENTS, Fable handoff, freeze
edit('docs/CONNECTION_READINESS.md',[('owner observations UC-21–UC-25 are open with U4, UC-14, UC-17, UC-18 and UC-20.','the owner decided UC-21 to UC-23 in D-038, and U4, UC-14, UC-17, UC-18 and UC-20 remain open.')])
edit('AGENTS.md',[
 ('Await the owner\'s decision on observations UC-21 to UC-25 and a new specific assignment','In D-038 the owner decided UC-21, UC-22 and UC-23: the feed code changed for UC-21 and UC-22 with review tests in tests/test_feed_repeat_decisions.py, and UC-23 is accepted as built. Those two changes were made after the G0 acceptance and after the RF checkpoint that the Independently verified records cite. Await a new specific assignment'),
 ('U4, UC-14, UC-17, UC-18 and UC-20 remain open; expected NOTE probes stay NOTE.','U4, UC-14, UC-17, UC-18 and UC-20 remain open; expected NOTE probes stay NOTE in the gates. In the RF review\'s own probe script, G1g and G5a now report OK because UC-21 and UC-22 are implemented.')])
edit('FABLE_ACCOUNTING_HANDOFF.md',[
 ('`make test` passes 262 methods (250 at the D-034 validation, when all nine gate targets also passed; twelve documentation review tests were added under D-037).','`make test` passes %d methods (250 at the D-034 validation; twelve documentation review tests added under D-037 and eleven feed review tests under D-038). Under D-038 the owner decided UC-21 to UC-23: the feed code changed for UC-21 and UC-22 after the G0 acceptance and after the RF checkpoint, with the suite, all nine gates and the reviewers\' unmodified probes re-run.'%N),
 ('owner observations UC-21 to UC-25 are open with U4, UC-14, UC-17, UC-18 and UC-20.','U4, UC-14, UC-17, UC-18 and UC-20 remain open.')])
edit('REVIEW_FREEZE.md',[
 ('Working files changed since the RF bundle only under four owner decisions: D-036','Working files changed since the RF bundle only under five owner decisions: D-038 (application source for UC-21 and UC-22 in accounting_agent/feed_contract.py, source_control.py, service.py and web/app.js, with a new review test file), D-036'),
 ('No application source, schema, probe, gate script or HTTP test changed.','No schema, probe, gate script or HTTP test changed; application source changed only under D-038.')])
edit('PROGRESS.md',[],prepend='''# Feed-contract decisions UC-21 to UC-23 — 17 November 2026

Under owner decision D-038, after the independent RF review and after the accounting owner accepted human G0: an identical repeat of a card row or receipt that a live replacement has retired now changes nothing (UC-21); a message with no order value for a row governed by one is kept once and flagged as SOURCE_ORDER_MIXED in the state, export and local page (UC-22); and a target selector remaining a contributor of the run's period-level artifacts is accepted as built (UC-23). The suite has %d test methods, eleven of them new review tests in tests/test_feed_repeat_decisions.py. The reviewers' unmodified RE probes still report 19 OK with C9c/C9g NOTE; the RF review's own G1g and G5a probes now report OK. Every retained test method is unchanged: one RD-02 method pins a re-send that omits the row's claim, so that case keeps its earlier handling. Full results are in docs/feed_decisions_uc21_uc23/. G1–G4, Batch 3 and all live actions remain closed and no further implementation is authorized. The sections below are earlier checkpoints.

'''%N)
edit('HANDOFF_RF_REGISTRATION_2026-11-17.md',[
 ('| UC-21 | Whether clause 5 should cover an identical repeat of a retired open-period row. |','| UC-21 | Decided in D-038 and implemented: the identical repeat changes nothing. |'),
 ('| UC-22 | Whether a provider may mix ordered and unordered messages for one row, and how an unordered repeat is recognised. |','| UC-22 | Decided in D-038 and implemented: not permitted; the message is kept once and flagged. |'),
 ('| UC-23 | Accept that a selector also contributes to the card run\'s period-level artifacts, or narrow it to the row and its replacements. |','| UC-23 | Decided in D-038: accepted as built. |'),
 ('## Decisions waiting for the owner','''## Feed-contract decisions UC-21 to UC-23 (D-038)

The feed code changed after the G0 acceptance and after the RF checkpoint. `accounting_agent/feed_contract.py` and `source_control.py` implement UC-21 and UC-22; `service.py` and `web/app.js` expose the new anomaly list. Eleven review tests are in `tests/test_feed_repeat_decisions.py`, and the suite now has %d methods. The record, results and limits are in `docs/feed_decisions_uc21_uc23/`. The three Independently verified records still cite the RF checkpoint; these two changes are covered by Fable's review tests and re-run gates, not by a pinned review.

## Decisions waiting for the owner'''%N)])
# register: three scope notes, current-evidence text, change log
p=root/'docs/PRODUCT_REQUIREMENTS.md';t=p.read_text()
t=once(t,'Owner observations UC-21 to UC-25 are recorded and open with U4, UC-14, UC-17, UC-18 and UC-20; C9c/C9g remain NOTE.','After this checkpoint the owner decided UC-21 to UC-23 (D-038) and the working source changed for UC-21 and UC-22; that change is covered by review tests Fable built and by the re-run gates, not by this verification. UC-24 and UC-25 need no action; U4, UC-14, UC-17, UC-18 and UC-20 remain open; C9c/C9g remain NOTE.',3)
t=once(t,'are new owner observations from the RF review; none is a corrective ticket and none is decided here.','were owner observations from the RF review, none a corrective ticket. In D-038 the owner decided the first three: UC-21 and UC-22 are implemented (identical repeats of a row or receipt retired by a live replacement change nothing; an unordered message against an ordered row is kept once and flagged SOURCE_ORDER_MIXED) with review tests in tests/test_feed_repeat_decisions.py, and UC-23 is accepted as built. Those source changes follow the RF checkpoint and the G0 acceptance; the suite, all nine gates and the reviewers\' unmodified probes were re-run on them. UC-24 is carried to upgrade notes and UC-25 needs no action.')
last='| Owner decision D-037; docs/documentation_review/. |\n'
t=once(t,last,last+'\n| 2026-11-17 | Recorded the owner\'s decisions on UC-21, UC-22 and UC-23 and the resulting feed-contract source change in the scope notes of AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 and in the current-evidence text. No implementation state, acceptance criterion or product decision changed; the three records remain Independently verified for the RF checkpoint, which precedes the change. | Owner decision D-038; docs/feed_decisions_uc21_uc23/. |\n')
p.write_text(t)
# decision log
edit('DECISIONS.md',[],append='''

## D-038 — Owner decision: feed-contract observations UC-21, UC-22 and UC-23 — 17 November 2026

The owner asked for recommendations on each observation "for best accounting practices and accuracy". Three were given: extend clause 5 so the repeat changes nothing (UC-21); do not allow mixed ordering, and make it visible when it happens (UC-22); accept UC-23 as built. Asked "Should I record all three decisions and implement the UC-21 and UC-22 changes?", the owner answered:

> Yes, all three

D-026 and D-029 stay recorded as written. These decisions add to them.

- **UC-21, added to clause 5.** An identical repeat of a card row's message, claim included, or of its receipt, changes nothing when a live replacement has retired the row: no new source version, no binding, no generation step. A new batch still keeps its own delivery record. Not covered, and handled as before: a re-send with a newer order value, which is the provider reasserting the charge; a re-send after the provider withdrew the replacement or the row itself, which is the open restoration question (U4, UC-17); and a re-send that omits a claim the row has, which is a later omission under clause 6.
- **UC-22, added to clause 1.** One ordering scheme applies to a row. A message with no sequence number or timestamp, for a row governed by one and carrying different data, is a feed anomaly: it is kept as evidence once however often it repeats, never governs, and is flagged once per distinct content as SOURCE_ORDER_MIXED. The flag appears in the state and export (feed_anomalies and the accounting events) and in the Source evidence view of the local page. How a real provider behaves remains a G2 confirmation.
- **UC-23, clause 9.** A person who records a target selection is also a contributor of that card run's period-level artifacts: the statement workpaper, the inventory and the package manifest. Accepted as built. If real staffing at G1 makes this unworkable, narrowing it needs a recorded reason.
- **Implementation and review record.** accounting_agent/feed_contract.py and source_control.py carry the two changes; service.py adds feed_anomalies to the state; web/app.js lists them. No schema change. tests/test_feed_repeat_decisions.py has eleven review methods covering sequence, timestamp and arrival ordering, row-only and receipt-only repeats, chains of replacements, each boundary above, claims carried on the affected messages, and the visibility of the anomaly. Run against the source as it stood before the change, seven of the first ten methods fail or error; the eleventh was added afterwards with the narrowing below.
- **A retained test shaped the change.** The first implementation treated every unchanged re-send of a retired row as a repeat. The retained method test_RD02_retired_claimant_resent_unchanged_without_claim then failed: it requires a re-send that omits the row's waiting claim to be recorded. No retained method was adapted. The change was narrowed so that a repeat must carry the same claim as the row has, and a review test now pins that boundary. As a result one case of UC-21 is deliberately left as it was.
- **Reviewers' unmodified scripts.** The 21 RE probes report 19 OK with C9c and C9g NOTE, as before. The RF review's own 15 probes now report 14 OK and one NOTE: G1g and G5a, which recorded UC-22 and UC-21, changed from NOTE to OK, and G1c (UC-20) stays NOTE.
- **Limits.** The same data sent without an order value is treated as an ordinary repeat and is not flagged, so a provider that mixes ordering without changing data is not detected. The anomaly has no acknowledgement or disposition workflow; it stays listed. Ordering of receipts, statements and documents is not changed by this decision. The page line was checked by parsing the script and exercising that line in a JavaScript engine with stub page functions, not in a browser. Journals remain outside the contract.
- **Standing of earlier acceptances.** These source changes follow both the RF checkpoint, which the seven Independently verified records cite, and the owner's G0 acceptance (D-036). The three affected records keep their state for the RF checkpoint, with scope notes that say the source has since changed. Under D-037 the changes are Fable's own work with Fable's review tests; no pinned review result has been recorded for them, so no record is raised or re-based on them. Whether to re-affirm G0 for the changed source is the owner's decision. Validation results are in docs/feed_decisions_uc21_uc23/. G1–G4, Batch 3 and all live actions remain closed; no further implementation is authorized.
''')
print('suite size',N)
