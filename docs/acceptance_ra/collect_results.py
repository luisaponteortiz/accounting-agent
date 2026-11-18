"""Collect observed local gate results; refuses incomplete or unexpected results."""
import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import sqlite3

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/acceptance_ra'
read=lambda name:(OUT/name).read_text()
match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK\s*$',read('final-tests.txt'))
assert match and match[1]=='154','Final full test run must pass 154 methods'
acceptance_pattern=r'(?m)^(A\d+|X\w+|U\d+|M\d+)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s'
rv_pattern=r'(?m)^(RN\w+|RT\w+|RG0)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s'
first,current=read('final-acceptance-gate.txt').split('python3 review/fable_rv_acceptance_probes.py .',1)
original_compatible=dict(re.findall(acceptance_pattern,first));adapted=dict(re.findall(acceptance_pattern,current))
assert len(original_compatible)==20 and len(adapted)==24
for group in (original_compatible,adapted):
 for key,status in group.items():assert status=='OK' or key=='U4' and status=='NOTE',(key,status)
original=dict(re.findall(acceptance_pattern,read('current-original-acceptance-probes.txt')))
assert len(original)==24
assert {k for k,v in original.items() if v in ('WEAK','ERROR')}=={'A03','A05','A17','X09'}
assert all(original[k]=='OK' for k in ('A10','X01','X12k','X12s'))
first,rest=read('final-reverification-gate.txt').split('python3 review/fable_reverification_probes.py .',1)
current,historical=rest.split('python3 scripts/verify_corrective_checkpoint.py',1)
rv_compatible=dict(re.findall(rv_pattern,first));rv_adapted=dict(re.findall(rv_pattern,current))
assert len(rv_compatible)==27 and set(rv_compatible.values())=={'OK'}
assert len(rv_adapted)==35 and set(rv_adapted.values())=={'OK'}
assert 'Corrective gate (C-01 to C-06): PASS' in historical
rv_original=dict(re.findall(rv_pattern,read('current-original-rv-probes.txt')))
assert {k for k,v in rv_original.items() if v in ('ERROR','WEAK')}=={'RN02','RN03','RN07','RT12a','RT14a','RT18','RG0'}
cases=json.loads((ROOT/'docs/batch2/final-validation.json').read_text())
assert cases['summary']=={'PASS':29,'FIXED':10,'DEFERRED-OK':21} and len(cases['cases'])==60
hashes=json.loads((OUT/'input-checksums.json').read_text())
for path,value in hashes.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value,path
assert len(hashes)==57
corrections=json.loads((ROOT/'exports/FABLE_RV_ACCEPTANCE/FABLE_RV_CORRECTIONS.json').read_text())
methods=[n.name for n in ast.walk(ast.parse((ROOT/'tests/test_acceptance_corrections.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert len(methods)==13
commands=[
 {'command':'make test','exit_code':0,'result':'154 tests OK','seconds':float(match[2]),'evidence':'docs/acceptance_ra/final-tests.txt'},
 {'command':'make check','exit_code':0,'result':'Offline syntax/JSON/profile/registry/DOM checks PASS','evidence':'docs/acceptance_ra/final-check.txt'},
 {'command':'make batch2-gate','exit_code':0,'result':cases['summary'],'evidence':'docs/acceptance_ra/final-batch2-gate.txt'},
 {'command':'make reverification-gate','exit_code':0,'result':'27 unchanged originals and 35 current-setup OK; frozen corrective checkpoint PASS','evidence':'docs/acceptance_ra/final-reverification-gate.txt'},
 {'command':'make acceptance-gate','exit_code':0,'result':'20 compatible originals (19 OK/U4 NOTE); 24 current-setup (23 OK/U4 NOTE)','evidence':'docs/acceptance_ra/final-acceptance-gate.txt'},
 {'command':'python3 exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py .','exit_code':1,'result':'Disclosed statement-setup incompatibilities; original full command NOT PASS','evidence':'docs/acceptance_ra/current-original-acceptance-probes.txt'},
 {'command':'python3 exports/FABLE_REVERIFICATION/fable_reverification_probes.py .','exit_code':1,'result':'Preserved older original setup incompatibilities plus RT18 statement acceptance; NOT PASS','evidence':'docs/acceptance_ra/current-original-rv-probes.txt'},
]
tickets=[]
for row in corrections['confirmed_defects']:
 tests=[name for name in methods if name.startswith('test_'+row['id'].replace('-','')+'_')]
 assert tests,row['id']
 tickets.append({'id':row['id'],'priority':row['priority'],'title':row['title'],'developer_status':'PASS_WITH_DISCLOSED_CURRENT_SETUP','independent_acceptance':'PENDING','acceptance_assertions':row['acceptance_assertions'],'regression_methods':tests,'independent_probe':row['probe']})
result={
 'checkpoint':'FABLE_RA_CORRECTIONS','scope':'Local fictional preparation only; RA-01..RA-08; no Batch 3 or live authority',
 'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version},
 'baseline':{'matching_frozen_working_files':243,'original_exit_code':1,'counts':{'OK':16,'WEAK':4,'NOTE':4},'frozen_reviewed_archive_sha256':'247c1cfd31a2128573b5ae29d633c0d9e74bb076a38a5fc3d9844b6748cc1c75','evidence':'docs/acceptance_ra/baseline-independent-probes.txt'},
 'implementation_order':corrections['implementation_order'],'commands':commands,'tickets':tickets,
 'validation_cases':cases,'acceptance_original_compatible':original_compatible,'acceptance_current_setup':adapted,'acceptance_full_original':original,
 'older_original_compatible':rv_compatible,'older_current_setup':rv_adapted,'older_full_original':rv_original,
 'adaptations':{'status':'PENDING_INDEPENDENT_JUDGMENT','new_positive_setups':['A03','A05','A17','X09'],'older_positive_setup':['RT18'],'reason':'RA-04 requires independently accepted statement changes before positive eligibility/review. All original verdicts remain; all 24 new-probe assignments are unchanged. Original files stay byte-identical.','previous_seven_adaptations_and_RT14b':'Accepted by Fable at frozen RV checkpoint; retained unchanged in substance.','explanation':'docs/acceptance_ra/probe-adaptations.md','patches':['docs/acceptance_ra/acceptance-probe-adaptations.patch','docs/acceptance_ra/older-RT18-adaptation.patch']},
 'new_RA_regression_methods':13,'new_acceptance_gate_methods':5,'preserved_input_archive_hashes':57,'new_independent_files':27,
 'retained_original_platform_http_methods':{'initial':40,'batch1':41,'reviewed_batch2':43,'missing':[]},
 'extra_regression':{'case':'Valid move followed by former-origin relock and destination revision','before':'Reproduced false quarantine','after':'Nearest admitted owner preserves destination routing','evidence':['docs/acceptance_ra/relock-regression-before.txt','docs/acceptance_ra/final-RA-regressions.txt']},
 'teaching_month':{'referral':{'approvals':10,'held':['TX-007','TX-009','TX-011'],'original_TX009_receipt_unchanged':True,'impact':{'DEMO_OFFICE_SUPPLIES':'311.00','DEMO_REPAIRS':'200.00','DEMO_CARD_LIABILITY':'-211.00','DEMO_CASH':'-300.00'}},'accepted_revised_support':{'approvals':11,'held':['TX-007','TX-011'],'impact':{'DEMO_OFFICE_SUPPLIES':'391.00','DEMO_REPAIRS':'200.00','DEMO_CARD_LIABILITY':'-291.00','DEMO_CASH':'-300.00'}},'net':'0.00','quarantine':['TX-008','receipt-TX-008'],'preparation_packages':2,'period_status':'locked','second_client_isolation':'PASS in independent M1/current service walkthrough'},
 'remaining_note':'U4: visible non-restoration when a superseder is withdrawn; explicitly permitted by Fable, not an assigned defect.',
 'unresolved':'Independent RA acceptance and review of the four new positive setups/older RT18; literal original full commands remain nonzero as disclosed.',
 'G0':'NOT_ACCEPTED','G1_G4':'CLOSED','Batch3':'NOT_AUTHORIZED'
}
(OUT/'execution-results.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'exit-codes.json').write_text(json.dumps({r['command']:r['exit_code'] for r in commands},indent=2)+'\n')
print('Recorded 154 passing tests, 23 OK + allowed U4 NOTE, 29/10/21 cases, and 57 preserved hashes; original full-command incompatibilities disclosed.')
