"""Documentation-only pass, part 2: Fable handoff, review freeze, stale register lines."""
import sys
from pathlib import Path
root=Path(sys.argv[1])
def once(t,old,new,n=1):
    assert t.count(old)==n,(old[:70],t.count(old));return t.replace(old,new)
# ARCHITECTURE: the omission clause promised by the bullet title
p=root/'docs/ARCHITECTURE.md';t=p.read_text()
t=once(t,'- **Repeats and omissions.** Repeating a claim the row already has changes no source lifecycle record.','- **Repeats and omissions.** Repeating a claim the row already has changes no source lifecycle record. A later version that does not repeat a claim does not withdraw it.')
p.write_text(t)
# FABLE_ACCOUNTING_HANDOFF
p=root/'FABLE_ACCOUNTING_HANDOFF.md';t=p.read_text()
assert t.startswith('# Current RF/PRV developer checkpoint — 16 November 2026')
t=once(t,'# Current RF/PRV developer checkpoint — 16 November 2026','# Earlier RF/PRV developer checkpoint — 16 November 2026')
t=once(t,'# Current RC/PRV review handoff — 16 November 2026','# Earlier RC/PRV review handoff — 16 November 2026')
t=once(t,'> Current correction response: Fable\'s reviews are preserved','> Earlier RB correction response: Fable\'s reviews are preserved')
t=('# Current state: RF review returned and registered — 17 November 2026\n\n'
 'Fable\'s independent RF review accepted RF-01–RF-03, PRV-16 and RE-01/RB-01 at checkpoint c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd with no corrective ticket. Under owner decision D-033 that review is registered: its results and report are the fifth pinned reviewer authority, AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 are recorded Independently verified for that checkpoint and synthetic scope, and no requirement is Verification failed. `make test` passes 250 methods and all nine gate targets pass (D-034). A documentation-only pass under D-035 then brought the entry, architecture and capability documents to this state and described the D-026 card-feed contract in them.\n\n'
 'Read [HANDOFF_RF_REGISTRATION_2026-11-17.md](HANDOFF_RF_REGISTRATION_2026-11-17.md), [the registration record](docs/registration_rf/RF_REGISTRATION_REPORT.md) and [the G0 criteria check](docs/G0_CRITERIA_CHECK_2026-11-17.md). The registration and the documentation pass were done by a Claude (Fable) session at the owner\'s assignment and have not themselves been independently reviewed. **Human G0 has not been accepted**; owner observations UC-21 to UC-25 are open with U4, UC-14, UC-17, UC-18 and UC-20. No further implementation is authorized. Journals, real-provider confirmation, G1 sample processing, Batch 3, deferred/Proposed capabilities and all live actions remain closed.\n\n'
 'The sections below are earlier checkpoints and the original handoff, kept as written at the time.\n\n')+t
p.write_text(t)
# REVIEW_FREEZE
p=root/'REVIEW_FREEZE.md';t=p.read_text()
assert t.startswith('# Current RF correction authority — 16 November 2026')
for old,new in (('# Current RF correction authority — 16 November 2026','# Earlier RF correction authority — 16 November 2026'),
                ('# Current RE correction authority — 16 November 2026','# Earlier RE correction authority — 16 November 2026'),
                ('# Current RD correction authority — 16 November 2026','# Earlier RD correction authority — 16 November 2026'),
                ('# Current correction authority — 16 November 2026','# Earlier RC correction authority — 16 November 2026'),
                ('## Current V2 submission frozen — 16 November 2026','## Earlier V2 submission frozen — 16 November 2026')):
    t=once(t,old,new)
t=('# Current boundary after the RF result registration — 17 November 2026\n\n'
 'No correction pass is authorized. The delivered RF bundle (c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd), its returned response (343da96a13daecdbc5f8bd7c8d9c9ac265c7b1a9ebca97c478ac1be1a2583232), every earlier archive, sidecar and manifest, all original reviewer inputs and every delivered handoff, prompt and report are immutable. docs/registration_rf/input-checksums.json lists 1,506 protected inputs, including the returned RF review.\n\n'
 'Working files changed since the RF bundle only under two owner decisions: D-033 (registration of the RF review: checker pins, derived results, three register records, six named register-test methods, decision/progress/readiness/AGENTS records) and D-035 (documentation only: README.md, START_HERE.md, docs/ARCHITECTURE.md, docs/CAPABILITY_CONTRACTS.md, FABLE_ACCOUNTING_HANDOFF.md, this file and stale status lines in the register). No application source, schema, probe, gate script or HTTP test changed. These working changes are not a new delivered bundle and nothing is committed. Human G0, G1–G4, Batch 3 and all live actions remain closed; a new specific owner assignment is required before any further change.\n\n'
 'The sections below are earlier authorities and freezes, kept as written at the time.\n\n')+t
p.write_text(t)
# Register: stale status lines outside the requirement records
p=root/'docs/PRODUCT_REQUIREMENTS.md';t=p.read_text()
t=once(t,'These are developer evidence awaiting independent RA acceptance. |','These were the developer evidence for the RA pass; the independent RA review has since returned (next row), and later reviews are summarized under Current evidence and corrective priority. |')
t=once(t,'These reject the RA checkpoint and condition register acceptance on corrections. Current developer response evidence is in corrections_rb/. |','These rejected the RA checkpoint and conditioned register acceptance on corrections. The RB response is in corrections_rb/; the later RC to RF passes and their independent reviews are summarized under Current evidence and corrective priority. |')
t=once(t,'RA-02 accepted for original scope; RB-03 fails new scope/key coverage until re-verification. |','RA-02 accepted for original scope; RB-03 (scope/key coverage) accepted at the independent RB review. |')
t=once(t,'RA-06/07/08 accepted; RB-02/RB-04 replacement/continuity routes await independent re-verification. |','RA-06/07/08 accepted; RB-02/RB-04 replacement/continuity routes accepted at the independent RB review. |')
t=once(t,'Current authorized order is **RE-01, RE-02, RE-03**, with **PRV-14–PRV-15** in the same pass, followed by independent re-verification.','The later correction orders were **RC-01–RC-03**, **RD-01–RD-02**, **RE-01–RE-03** and **RF-01–RF-03**, each with its PRV items and each independently reviewed; the RF review raised no ticket. No correction order is currently authorized.')
t=once(t,'RA-01 failed at late-link arrival paths (RB-01); the response now requires independent re-verification.','RA-01 failed at late-link arrival paths (RB-01); that chain was accepted at the independent RF review (see RA-01 and RB-01 below).')
t=once(t,'| RA completion | Five RA corrections accepted; RB-01–RB-04 require correction and independent re-verification. Developer tests alone do not restore acceptance.','| RA completion | Five RA corrections accepted at the RA review; RB-02–RB-04 accepted at the RB review; RB-01 accepted at the RF review after the RC, RD, RE and RF corrections. Developer tests alone do not establish acceptance.')
last='| Owner assignment and clarification D-033; immutable RF review; D-034; docs/registration_rf/. |\n'
row='\n| 2026-11-17 | Documentation-only correction of stale status wording outside the requirement records: the EVIDENCE and RETURNED REVIEW source rows, crosswalk rows T-09 and T-14, the correction-order sentence and the C-01–C-06 and RA completion rows now state the independent verdicts already recorded elsewhere in this register. No requirement record, state, criterion, product decision or gate changed. | Owner assignment D-035; docs/G0_CRITERIA_CHECK_2026-11-17.md. |\n'
t=once(t,last,last+row)
p.write_text(t)
print('ok')
