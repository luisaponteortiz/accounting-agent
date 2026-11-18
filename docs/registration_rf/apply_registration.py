"""Owner-authorized RF result registration (D-033): pin the RF review as fifth authority,
regenerate the derived results, record three verdicts and synchronize the register text."""
import json,re,sys,hashlib
from pathlib import Path
root=Path(sys.argv[1]).resolve()
RJ='exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_RESULTS.json'
RR='exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md'
BUNDLE='c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd'
h=lambda p:hashlib.sha256((root/p).read_bytes()).hexdigest()
def once(t,old,new,n=1):
    assert t.count(old)==n,(old[:80],t.count(old));return t.replace(old,new)
# 1. checker pins
cp=root/'scripts/check_product_requirements.py';t=cp.read_text()
anchor="    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md':'55e1606bfbd3b96cacec064d0dc72c08ba5e4a3e6beae6afbd1bc0d6f5d22080',\n"
t=once(t,anchor,anchor+"    '%s':'%s',\n    '%s':'%s',\n"%(RJ,h(RJ),RR,h(RR)))
t=once(t,'"""Read the four pinned reviewer authorities in chronological order."""','"""Read the five pinned reviewer authorities in chronological order."""')
t=once(t,'# The shipped list always includes all four authorities and their reports.','# The shipped list always includes all five authorities and their reports.')
cp.write_text(t)
# 2. derived results
sys.path.insert(0,str(root))
import scripts.check_product_requirements as c
latest,_=c.reviewer_verdicts(root)
rp=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';d=json.loads(rp.read_text())
d['authority']=once(d['authority'],'four hash-pinned','five hash-pinned');d['results']=list(latest.values())
rp.write_text(json.dumps(d,indent=2)+'\n')
# 3. register records
reg=root/'docs/PRODUCT_REQUIREMENTS.md';text=reg.read_text()
def field(text,identifier,name,value):
    start=text.index('### '+identifier+' —');end=text.find('\n### ',start+5)
    body,n=re.subn(r'^- \*\*'+re.escape(name)+r':\*\*[^\n]*',lambda m:'- **'+name+':** '+value,text[start:end],count=1,flags=re.M)
    assert n==1;return text[:start]+body+text[end:]
common_scope=('Independent Fable RF review accepted RF-01, RF-02, RF-03 and PRV-16, and RE-01/RB-01, at checkpoint '+BUNDLE+' under unchanged D-026/D-029, with no corrective ticket. This record is Independently verified for that reviewed checkpoint and for synthetic local preparation controls only: fictional card rows and receipts, principally two periods and one card account; journals excluded; the target-selection HTTP route was not independently probed beyond the developer tests. %s Recorded by the owner-assigned registration of 17 November 2026 (D-033/D-034). Owner observations UC-21 to UC-25 are recorded and open with U4, UC-14, UC-17, UC-18 and UC-20; C9c/C9g remain NOTE. Real-provider behaviour remains a G2 confirmation. No client accounting policy, reconciliation completion, close, human G0, readiness or operating authority is verified.')
common_ev=('[independent review](../exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md) (exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 '+BUNDLE+'; %s Earlier [RE independent review](../exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md) at 4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae accepted RE-02/RE-03 and PRV-14/PRV-15 and recorded the RF-01 failure now repaired. Developer evidence: [tests/test_review_corrections_rf.py](../tests/test_review_corrections_rf.py), [tests/test_rf_review_gate.py](../tests/test_rf_review_gate.py), [tests/test_product_requirements_rf.py](../tests/test_product_requirements_rf.py), [tests/test_product_requirements_rf_registration.py](../tests/test_product_requirements_rf_registration.py), [RF developer report](corrections_rf/RF_CORRECTIONS_REPORT.md), [registration record](registration_rf/RF_REGISTRATION_REPORT.md).')
rows={'AAOS-BNK-03':('Reviewed criterion: one charge approved in two periods, for every delivery order within the feed contract of D-026.',
        'RF-01 accepted: C2d and C2f OK; 21 RE probes 19 OK with C9c and C9g NOTE; reviewer probes G1a–G1h OK (G1c and G1g NOTE); 480 original and 2,640 further stepwise orders with 0 double approvals, 0 releases and 0 unlinked first claims; 12 supplied RD probes and adapted Y05 OK; 336 and 120 supplied orders 0 double.'),
      'AAOS-CTL-04':('Reviewed criterion: a replacement chain never leaves the same expense approved in two periods.',
        'as AAOS-BNK-03, RF-01 accepted (C2d, C2f, G1a–G1h; 3,120 stepwise orders, 0 double, 0 released); clause 8 holds in every delivery tried; RF-02 accepted (C9h, G2a–G2f).'),
      'AAOS-GOV-03':('Reviewed criterion: known repaired defects must pass.',
        'RB-01 accepted at this checkpoint through RF-01 (C2d, C2f); all 227 earlier methods present, 226 unchanged and one rewritten under D-031; every retained gate passes; five consecutive complete make test runs pass 241 methods (RF-03).')}
for i,(crit,ev) in rows.items():
    text=field(text,i,'Implementation state','Independently verified')
    text=field(text,i,'Scope note',common_scope%crit)
    text=field(text,i,'Evidence',common_ev%ev)
old='Independent verdicts are derived from four hash-pinned reviewer machine-readable files'
text=once(text,old,old.replace('four','five'))
# 4. register status text, crosswalk and change log
text=once(text,'**88 retained requirements**, updated 16 November 2026.','**88 retained requirements**, updated 17 November 2026.')
start=text.index('**RE-02, RE-03, PRV-14 and PRV-15 independently accepted; RE-01/RB-01 not accepted; Batch 3 closed.**')
end=text.index('D-026/D-029 are unchanged. U4 and UC-14 remain open.')
new_status=('**RF-01, RF-02, RF-03 and PRV-16 independently accepted, with RE-01/RB-01; no corrective ticket; human G0 not granted; Batch 3 closed.** Fable\'s immutable [RF review](../exports/FABLE_RF_ACCEPTANCE/FABLE_RF_ACCEPTANCE_REPORT.md) at checkpoint SHA-256 '+BUNDLE+' accepted those bounded assertions under the unchanged owner contract D-026/D-029 and the single-method exception D-031. Its 21 unmodified RE probes report 19 OK with C9c/C9g NOTE; its 15 new probes report 12 OK and three NOTE; 3,120 stepwise delivery orders show zero double approvals, unauthorized releases or audit failures; five consecutive complete make test runs passed 241 methods with the unchanged five-second HTTP deadline. The earlier RE review at 4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae accepted RE-02, RE-03, PRV-14 and PRV-15. Every conclusion covers synthetic local preparation controls only, principally two periods and one card account. Journals remain outside the contract, the target-selection HTTP route was not independently probed beyond the developer tests, and real provider confirmation remains G2 work.\n\n'
 'AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 are recorded Independently verified for that reviewed checkpoint and scope by the owner-assigned registration of 17 November 2026 (D-033/D-034). Four previously verified scopes retain their bounded citations. [Independent results](INDEPENDENT_VERIFICATION_RESULTS.json) are derived from five pinned reviewer authorities, latest verdict winning per record in the original seven-row order. The [registration record](registration_rf/RF_REGISTRATION_REPORT.md) lists the six retained register-test methods adapted under D-033, the new five-authority tests and the older fault-script expectations that the fifth authority makes obsolete. Independent verification of these controls is not human G0 acceptance and grants no G1–G4, Batch 3 or live authority.\n\n')
text=text[:start]+new_status+text[end:]
text=once(text,'are open observations for the owner, outside this pass.','are open observations for the owner, outside this pass. UC-21 (an identical repeat of a retired open-period row adds source versions), UC-22 (unordered repeats against an ordered governing row add evidence), UC-23 (a selector also contributes to the card run\'s period-level artifacts), UC-24 (a database prepared at the RE checkpoint shows open-period approvals as stale until re-prepared) and UC-25 (failed-record citation text is not checked; the D-031 fixture derives its rows from the checker) are new owner observations from the RF review; none is a corrective ticket and none is decided here.')
old_tail='RE-02/RE-03 and PRV-14/15 accepted independently at 4890b297…98ae; RE-01/RB-01 stays unaccepted for RF-01 (C2d/C2f, 40/480 double). D-026/D-029 unchanged. RF-01–RF-03/PRV-16 developer repairs require independent 21-probe/480-order and retained-gate verification; no readiness authority.'
new_tail='RF-01–RF-03 and PRV-16, with RE-01/RB-01, accepted independently at c002b861…e7cd (21 RE probes 19 OK/C9c+C9g NOTE, 3,120 stepwise orders with zero double/released/audit failures, retained gates, five complete make test runs); RE-02/RE-03 and PRV-14/15 accepted earlier at 4890b297…98ae. D-026/D-029 unchanged. Recorded Independently verified for that checkpoint and synthetic scope only (D-033/D-034); UC-21–UC-25 open for the owner; no human G0 or readiness authority.'
text=once(text,old_tail,new_tail,3)
last='| 2026-11-16 | PRV-16 records RE-02/RE-03/PRV-14/15 acceptance and RF-01 continued failure, pins the fourth reviewer authority with latest-wins derivation and preserves seven-row order. Scope/evidence and crosswalk updated; every acceptance criterion, state, product decision and BB-01/02 field unchanged. | CODEX_RF_CORRECTIONS_PROMPT.md; immutable RE review; D-030; docs/corrections_rf/. |\n'
row='\n| 2026-11-17 | Registered the returned independent RF review: AAOS-BNK-03, AAOS-CTL-04 and AAOS-GOV-03 recorded Independently verified for checkpoint c002b861…e7cd and its synthetic scope; RF results and report pinned as the fifth reviewer authority with latest-wins derivation and the original seven-row order; AAOS-GOV-02 scope note, current-evidence text and crosswalk updated. Every acceptance criterion and product decision, the four earlier verified records, BB-01/02 and the six Proposed records unchanged. No G0, gate or operating change. | Owner assignment and clarification D-033; immutable RF review; D-034; docs/registration_rf/. |\n'
text=once(text,last,last+row)
reg.write_text(text)
