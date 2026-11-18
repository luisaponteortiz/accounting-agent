"""Refuse a completed RF checkpoint unless every required developer result exists."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/corrections_rf'
required=['delivery-preservation','delivery-source-and-tests-patch','delivery-make-check','final-make-check','final-batch2-gate','final-reverification-gate','final-acceptance-gate','final-rb-gate','final-rc-gate','final-rd-gate','final-re-gate','final-rf-gate','authorized-register-tests-final','retained-older-and-conflicting-matrix','final-rf-regression-and-validator-tests','final-protection-inventory-complete','patch-after-owner-clarification','response-folder-integrity','final-fourth-authority-all-three-older-faults-corrected','five-consecutive-suite-orchestration']
for label in required:
    row=json.loads((OUT/(label+'.json')).read_text());assert row['exit_code']==0,(label,row)
for label in ('baseline-re-probes','baseline-re-step-search','final-regressions-on-unmodified-RE-source'):
    row=json.loads((OUT/(label+'.json')).read_text());assert row['exit_code']==1,(label,row)
assert '21 probes: 16 OK, 3 NOTE, 2 WEAK, 0 ERROR' in (OUT/'baseline-re-probes.stdout.txt').read_text()
baseline=json.loads((OUT/'baseline-re-step-results.json').read_text())
assert baseline['runs']==480 and baseline['double']==40 and baseline['released']==0
assert all(not r['double_at_steps'] or r['family']=='older-resent-with-claim' for r in baseline['results'])
assert all(r['audit_ok'] for r in baseline['results'])
assert re.search(r'SUMMARY runs=480 double=0 released_without_authority=0 audit_failures=0 approved_before_target_known=\d+', (OUT/'final-rf-gate.stdout.txt').read_text())
five=json.loads((OUT/'five-suite-results.json').read_text());assert len(five)==5
assert all(r['exit_code']==0 and r['expected_methods']==241 and r['reported_counts'][0][0]=='241' and r['HTTP_methods_executed']==11 and len(r['HTTP_setup'])==1 and not r['HTTP_setup'][0]['setup_failed'] and r['HTTP_setup'][0]['worker_wait_seconds']<5 for r in five)
for label,want,summary in [('final-rb-register-faults',0,'cases 37 | agree 37 | gaps 0'),('final-rc-register-faults',0,'cases 44 | agree 44 | gaps 0'),('final-rd-register-faults',1,'cases 37 | agree 34 | gaps 3'),('final-re-register-faults',1,'cases 35 | agree 29 | gaps 6')]:
    assert json.loads((OUT/(label+'.json')).read_text())['exit_code']==want
    assert summary in (OUT/(label+'.stdout.txt')).read_text()
expected=json.loads((OUT/'final-validation-source-sha256.json').read_text());assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in expected.items())
value={'status':'DEVELOPER_VALIDATED_INDEPENDENT_REVIEW_PENDING','source_files_unchanged_during_final_validation':len(expected),'retained_methods':227,'retained_methods_unchanged':226,'sole_authorized_rewrite':'D-031 / test_PRV14_third_authority_is_pinned_and_latest_verdict_controls','current_methods':241,'consecutive_complete_runs':5,'HTTP_methods_per_run':11,'HTTP_setup':[{k:v for k,v in r['HTTP_setup'][0].items()} for r in five],'required_zero_exit_commands':required,'baseline_RE_probes':{'OK':16,'NOTE':3,'WEAK':2,'exit':1},'baseline_orders':{'runs':480,'double':40,'released':0,'audit_failures':0,'exit':1},'corrected_RE_probes':{'OK':19,'NOTE':['C9c','C9g'],'exit':0},'corrected_orders':{'runs':480,'double':0,'released':0,'audit_failures':0,'exit':0},'required_validation_NOT_RUN':[],'NOT_RUN':[{'scope':'optional diagnostic','command':'ps process inventory','reason':'Sandbox denied /bin/ps; file-based progress records were used. No required validation depends on it.'}],'independent_acceptance':'PENDING','three_affected_requirement_states':'Verification failed','human_G0':'NOT_GRANTED','G1_G4':'CLOSED','Batch_3':'CLOSED','live_actions':'CLOSED'}
(OUT/'completion.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
