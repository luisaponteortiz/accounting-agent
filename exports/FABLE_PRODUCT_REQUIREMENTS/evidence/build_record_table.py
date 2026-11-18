"""Build the 76-row per-record assessment table. usage: build_record_table.py <register_parsed.json> <out.md>"""
import json, sys
recs = json.load(open(sys.argv[1]))['records']
N = {  # id: (field(s) needing change, note)
 'AAOS-GOV-02': ('Acceptance criteria', 'Add a repeatable register check (PR-17).'),
 'AAOS-GOV-03': ('Status', 'Update after this review: RA not accepted (PR-01).'),
 'AAOS-ARC-03': ('Acceptance criteria', 'Concurrent-client criterion has no test (PR-14).'),
 'AAOS-ARC-04': ('Trace', 'Add AT-58 (PR-13).'),
 'AAOS-EXE-02': ('Dependencies', 'Direction with EXE-03 is reversed against T-04/T-10 (PR-12).'),
 'AAOS-EXE-03': ('Dependencies', 'Add EXE-02 and BNK-03; mark CTL-03 as for real authority (PR-12). Status agrees with my RA-05 result.'),
 'AAOS-EXE-05': ('Acceptance criteria', 'Stalled-work monitor has no time bound (PR-14).'),
 'AAOS-EXE-07': ('Dependencies, Trace', 'CTL-12 dependency needs the conditional marker (PR-12); add AT-59 (PR-13).'),
 'AAOS-KNO-01': ('Acceptance criteria', 'Names no artifact for the invariant/judgment distinction (PR-14).'),
 'AAOS-KNO-03': ('Description', 'Record the card_accounts schema limit (PR-16).'),
 'AAOS-KNO-04': ('Status, Acceptance criteria', 'Author retention holds for same key and scope only (PR-03).'),
 'AAOS-KNO-06': ('Description, Target stage', 'Add workflow inventory (PR-13); target stage names one client (PR-07).'),
 'AAOS-GL-03': ('Acceptance criteria', 'Materiality has no source (PR-14).'),
 'AAOS-AP-01': ('Acceptance criteria, Target stage', 'First-client condition in a shared record (PR-07).'),
 'AAOS-AR-01': ('Acceptance criteria, Target stage', 'Shared AR waits on one client (PR-07).'),
 'AAOS-BNK-02': ('Status, Acceptance criteria, Dependencies', 'Re-pointed statement and lookback restatement open (PR-02); add CTL-04 (PR-12).'),
 'AAOS-BNK-03': ('Status, Acceptance criteria', 'Criterion fails: RB-01 (PR-01).'),
 'AAOS-BNK-04': ('Trace', 'Add AT-24, AT-25 (PR-13).'),
 'AAOS-BNK-05': ('Description', 'Decide whether deposit and merchant-settlement matching belongs here (PR-09).'),
 'AAOS-CLS-02': ('Acceptance criteria', 'Add minimum package contents where they apply (PR-13).'),
 'AAOS-CLS-03': ('Acceptance criteria', 'Add package contents and the five separate states (PR-13).'),
 'AAOS-RPT-01': ('Status', 'Holds a Proposed consolidation requirement inside a Deferred record (PR-09).'),
 'AAOS-INT-01': ('Status', 'Cites the first client\'s Desktop conversion (PR-07); connector contract (PR-08).'),
 'AAOS-INT-02': ('Status', 'Approved while INT-01 is Deferred for the same state (PR-04); PR-08.'),
 'AAOS-INT-03': ('Status', 'As INT-02 (PR-04, PR-08).'),
 'AAOS-INT-04': ('Status', 'As INT-02 (PR-04, PR-08).'),
 'AAOS-INT-05': ('Status, Acceptance criteria', 'Names Expensify (PR-07); status as INT-02 (PR-04).'),
 'AAOS-INT-06': ('Trace', 'Add AT-29, AT-40 (PR-13).'),
 'AAOS-CTL-01': ('Acceptance criteria, Dependencies', 'Author-retention clause too broad (PR-03); CTL-03 marker (PR-12).'),
 'AAOS-CTL-04': ('Status, Acceptance criteria, Dependencies', 'Criterion fails: RB-01 (PR-01); CTL-03 marker (PR-12).'),
 'AAOS-CTL-09': ('Status, Acceptance criteria', 'Re-pointed documents avoid the hold: RB-02 (PR-02).'),
 'AAOS-CTL-12': ('Status', '"Comprehensive threat validation" has no list (PR-14).'),
 'AAOS-CTL-13': ('Acceptance criteria', 'No recovery-point or recovery-time parameter (PR-14).'),
 'AAOS-BB-01': ('Target stage', 'November capture cannot start under G1 as written (PR-11); instance of shared onboarding (PR-06).'),
 'AAOS-BB-02': ('Target stage', 'Follows PR-11.'),
 'AAOS-BB-03': ('—', 'Sound. Instance of shared onboarding (PR-06).'),
 'AAOS-BB-04': ('Target stage', 'No shared record for the execution it defers (PR-09).'),
 'AAOS-BB-05': ('Target stage', 'As BB-04 (PR-09).'),
 'AAOS-BRF-01': ('Acceptance criteria', 'Delivery channel and its permission unstated (minor note).'),
 'AAOS-BRF-03': ('Status, Acceptance criteria', 'Two statuses in one field (PR-04); "genuine urgency" has no rule source (PR-14).'),
 'AAOS-OBS-01': ('Acceptance criteria', 'Require that agreed thresholds are recorded (PR-14).'),
}
VER = {'AAOS-EXE-03': 'RA-05', 'AAOS-CTL-05': 'RA-08', 'AAOS-CTL-08': 'RA-06/RA-07', 'AAOS-GL-02': 'RA-07', 'AAOS-CLS-02': 'M1/M2', 'AAOS-ARC-02': 'M1 isolation', 'AAOS-EXE-07': 'make test no-egress', 'AAOS-OBS-04': 'RT14b guards'}
rows = ['| ID | Title | Fields to change | Assessment |', '| --- | --- | --- | --- |']
for rid, f in recs.items():
    fields, note = N.get(rid, ('—', 'Sound as written.'))
    if rid in VER and rid not in ('AAOS-EXE-03',): note += ' Status agrees with my run (%s).' % VER[rid]
    rows.append('| %s | %s | %s | %s |' % (rid, f['title'], fields, note))
open(sys.argv[2], 'w').write('\n'.join(rows) + '\n')
print(len(rows) - 2, 'rows;', sum(1 for r in recs if r in N and N[r][0] != '—'), 'need a change')
