"""Assemble FABLE_RB_ACCEPTANCE_RESULTS.json from my own raw logs. Nothing here is copied from
the developer's delivered logs."""
import json,os,re,sys
out_dir,ev=sys.argv[1],sys.argv[2]
def read(p): return open(p).read()
parsed=json.load(open(os.path.join(ev,'parsed-gate-results.json')))
exits={}
for line in read(os.path.join(ev,'exit-codes.txt')).splitlines():
    label,ex,sec,cmd=line.split('|',3); exits[label]={'command':cmd[4:],'exit':int(ex[5:]),'seconds':int(sec[8:]),'stdout':'evidence/%s.stdout.txt'%label,'stderr':'evidence/%s.stderr.txt'%label}
exp={}
ep=os.path.join(ev,'experiment','exit-codes.txt')
if os.path.exists(ep):
    for line in read(ep).splitlines():
        label,ex,sec,cmd=line.split('|',3); exp[label]={'command':re.sub(r'/\S*/scratchpad/out/','',cmd[4:]),'exit':int(ex[5:]),'seconds':int(sec[8:]),'stdout':'evidence/experiment/%s.stdout.txt'%label}
probe_out=read(os.path.join(out_dir,'fable_rb_acceptance_output.txt'))
titles=dict((m.group(1),(m.group(2),m.group(3))) for m in re.finditer(r'(?m)^(N\d\d[a-z]) \[([^\]]+)\] (.+)$',probe_out))
verdicts=dict(re.findall(r'(?m)^(N\d\d[a-z])\s+\S+\s+(OK|WEAK|NOTE|ERROR)\s*$',probe_out))
new=[{'id':k,'ticket':titles[k][0],'verdict':verdicts[k],'title':titles[k][1],'run':'executed by Fable','evidence':'fable_rb_acceptance_output.txt'} for k in titles]
exp_verdicts={}
p=os.path.join(ev,'experiment','exp-new-probes.stdout.txt')
if os.path.exists(p): exp_verdicts=dict(re.findall(r'(?m)^(N\d\d[a-z])\s+\S+\s+(OK|WEAK|NOTE|ERROR)\s*$',read(p)))
tests=read(os.path.join(ev,'make-test.stderr.txt'))
ran=re.search(r'Ran (\d+) tests in ([\d.]+)s',tests)
A=lambda ticket,text,result,evidence,note=None:dict(ticket=ticket,assertion=text,result=result,evidence=evidence,**({'note':note} if note else {}))
assertions=[
 A('RB-01','Probe R01b reports OK: late claim on an admitted source is quarantined, leaves December, blocked move with had_approval','PASS','R01b (unmodified), N01a'),
 A('RB-01','Probe R01c reports OK: unresolved link later resolved by re-sending is quarantined with the whole chain','PASS','R01c (unmodified), N01e'),
 A('RB-01','A destination approved before the claim stops governing and an accounting event names it','PASS','N01a'),
 A('RB-01','After reopen and re-preparation: November has no governing A1, December has exactly one governing item with SOURCE_TRANSITION_REQUIRES_REVIEW','PASS','N01a, N01e, R01a'),
 A('RB-01','R01a stays OK including relock; restart and replay are stable; root history kept','PASS','R01a (unmodified), N01a'),
 A('RB-01','No source_moves row with the same origin and destination period','PASS','N01a, N01f'),
 A('RB-01','A late link to a charge in an open period is an ordinary supersession','PASS','N01f'),
 A('RB-01','A charge superseded while its period was open, then locked before re-preparation, is not approved beside its replacement','PASS','N01g'),
 A('RB-01','One economic charge never remains approved in both periods: ancestor withdrawn after the lock, then late link','FAIL','N01b','RC-01'),
 A('RB-01','One economic charge never remains approved in both periods: late link on a middle source whose replacement is admitted or approved','FAIL','N01c','RC-02; held in the frozen combined submission'),
 A('RB-01','One economic charge never remains approved in both periods: unresolved claim never re-sent, claimant then replaced','FAIL','N01d','RC-03'),
 A('RB-02','Probe R03b reports OK: re-pointed receipt key is held and disclosed with version 1 and the amount change','PASS','R03b (unmodified), N02a'),
 A('RB-02','Probe R04b reports OK: re-pointed statement key holds both items; workpaper names version 1 and the totals change','PASS','R04b (unmodified), N02b'),
 A('RB-02','Re-pointing in a separate packet, before or after the replacement, and to an existing other charge, is detected','PASS','N02a, N02b'),
 A('RB-02','Both suppliers are refused (403); a granted non-supplier accepts; acceptance is item-bound; final review stays separate','PASS','N02a, N02b, R03a, R04a'),
 A('RB-02','A later change lapses the acceptance','PASS','N02a, N02b'),
 A('RB-02','A genuine additional still-active receipt remains a multiple-support question','PASS','N02a, R03a'),
 A('RB-02','R03a, R04a, X12k, X12s, A12, A13 unchanged','PASS','ra-probes-direct, make-acceptance-gate'),
 A('RB-02','A contradicting receipt supplied later and then moved away is disclosed','NOTE','N02c','UC-10; outside the RB-02 assertion; policy decision'),
 A('RB-03','Probe R02b reports OK: item-scoped and re-keyed identical rule keep the earlier author refused with 403','PASS','R02b (unmodified), N03a'),
 A('RB-03','Receipt policies behave the same; the earlier rule approver is also barred; a three-step chain keeps every author','PASS','N03a'),
 A('RB-03','Probe R02a unchanged; another item scope, description, category, policy value or client does not bar a reviewer','PASS','R02a (unmodified), N03b'),
 A('RB-03','An equal money value cannot be written differently to defeat exact comparison','PASS','N03c'),
 A('RB-04','Probe R04c reports OK: the December workpaper lists the November revision and continuity is not verified','PASS','R04c (unmodified), N04a'),
 A('RB-04','Continuity stays unverified with no and with partial own-period acceptance; verified only when every relying item is accepted','PASS','N04a'),
 A('RB-04','The acceptor and the supplier of the restated statement cannot review the December item; an independent reviewer can','PASS','N04a'),
 A('RB-04','Revocation re-blocks December and removes the approval; finalization is refused before re-preparation','PASS','N04a'),
 A('RB-04','New evidence after full acceptance lapses it and re-blocks an approved December item','PASS','N04b'),
 A('RB-04','A re-pointed or withdrawn-and-replaced prior statement is disclosed to December; a withdrawn one is reported missing','PASS','N04c'),
 A('RB-04','Probe A13 unchanged: a quarantined late revision of a locked prior statement is not used; an unaccepted restatement is not authenticated by a lock','PASS','make-acceptance-gate A13, N04d'),
 A('RB-04','A restated prior statement with no activity has an acceptance route','NOTE','N04e','UC-11; fails in the safe direction; disclosed by the developer'),
]
result={
 'title':'Fable independent verification results for RB-01 to RB-04 and retained controls',
 'authored':'2026-11-16',
 'notice':'Every result marked "executed by Fable" comes from my own run on a byte copy of the extracted bundle. Delivered developer logs were read as claims only. All data fictional; temporary databases; nothing connected, posted, paid, sent or deployed.',
 'bundle':{'file':'FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_BUNDLE.zip','sha256':'00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d','sha256_matches_supplied':True},
 'environment':{'versions':read(os.path.join(ev,'versions.txt')).strip().splitlines(),'working_directory':'byte copies of the extracted bundle in a temporary directory','loopback':'available; the HTTP tests bound 127.0.0.1 without a permission error'},
 'integrity':{
  'manifest':'448 entries, 448 files on disk, no missing, no unlisted, no hash mismatch, no unsafe archive path (evidence/integrity-manifest.txt)',
  'frozen_combined_zip_sha256':{'expected':'b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea','in_bundle':'MATCH','in_project_folder':'MATCH'},
  'returned_review_response_zip_sha256':{'expected':'d38e0e27b30e46d2e4690b5366aa3fa237d5733e23783c64082c39ca4ff30f84','in_bundle':'MATCH','in_project_folder':'MATCH'},
  'original_review_files':'all 39 files of the returned response ZIP are present in the bundle and byte-identical, including fable_ra_acceptance_probes.py',
  'change_inventory':'10 source/test/script changes, identical to changed-files.json; every listed hash agrees; nothing changed under fixtures, config, review/ or the reference package; 19 added files are outside the inventory (START_HERE.md and 18 archives and sidecars under exports/) - PRV-09 (evidence/inventory_checks_output.txt)',
  'limit':'The baseline for the inventory is the frozen combined ZIP held in the project folder, whose hash matches the value in the prompt.'},
 'commands':exits,
 'test_suite':{'run':'executed by Fable','methods_run':int(ran.group(1)) if ran else None,'seconds':float(ran.group(2)) if ran else None,'result':'OK','skips_or_expected_failures':0,
   'retention':'154 methods of the frozen RA source all present; 16 original files under tests/ byte-identical (15 test modules and __init__.py); 20 new methods: 11 in test_product_requirements.py, 6 in test_review_corrections_rb.py, 3 in test_ra_review_gate.py',
   'note':'Two test names contain the word "skipped"; no test is skipped.'},
 'latest_independent_probes_unmodified':{'run':'executed by Fable','direct':parsed['ra-probes-direct'],'through_make_rb_gate':parsed['make-rb-gate'],'enforced_by':'tests/test_ra_review_gate.py (in make test and make rb-gate): exit 0, the exact 14 ids, every verdict OK; script hash checked against input-checksums.json'},
 'validation_cases':{'run':'executed by Fable (make batch2-gate)','summary':{'PASS':29,'FIXED':10,'DEFERRED-OK':21,'unexpected':0},'note':'DEFERRED-OK means the capability correctly refuses; it is not implemented accounting functionality.','cases':parsed['validation_cases']},
 'acceptance_gate':{'run':'executed by Fable','unmodified_originals':parsed['make-acceptance-gate'][0],'reviewed_setups':parsed['make-acceptance-gate'][1],'permitted_note':'U4'},
 'reverification_gate':{'run':'executed by Fable','unmodified_originals':parsed['make-reverification-gate'][0],'reviewed_setups':parsed['make-reverification-gate'][1],'corrective_checkpoint':'PASS'},
 'older_literal_full_commands':{'run':'executed by Fable','status':'NOT A PASS; fail at the disclosed setup incompatibilities, identical to my previous review','acceptance':parsed['original-full-acceptance'][0],'reverification':parsed['original-full-reverification'][0]},
 'new_probes':{'script':'fable_rb_acceptance_probes.py','exit':1,'counts':{v:sum(1 for n in new if n['verdict']==v) for v in ('OK','WEAK','NOTE','ERROR')},'probes':new,
   'frozen_baseline_comparison':{'what':'N01a to N01d and N01g run against the nested RA source of the frozen combined submission (SHA-256 dec028b0...)','result':{'N01a':'WEAK (the RB-01 defect itself)','N01b':'WEAK','N01c':'OK (held by a side effect)','N01d':'WEAK','N01g':'OK'},'evidence':'evidence/baseline-frozen-ra-comparison.txt'}},
 'assertions':assertions,
 'teaching_month_and_isolation':{'run':'executed by Fable through unmodified probes M1 and M2 (make acceptance-gate) and scripts/synthetic_month.py (make batch2-gate)',
   'referral_route':{'DEMO_OFFICE_SUPPLIES':'311.00','DEMO_REPAIRS':'200.00','DEMO_CARD_LIABILITY':'-211.00','DEMO_CASH':'-300.00','nets_to_zero':True},
   'acceptance_route':{'DEMO_OFFICE_SUPPLIES':'391.00','DEMO_REPAIRS':'200.00','DEMO_CARD_LIABILITY':'-291.00','DEMO_CASH':'-300.00','nets_to_zero':True},
   'isolation':'PASS','audit_integrity':'PASS','package_immutability':'A17 OK in the reviewed-setup gate; RT18 OK','meaning':'preparation only; not posting, reconciliation completion or close'},
 'register_checks':{'run':'executed by Fable','own_parser':'evidence/register_checks_output.txt','fault_injection':'evidence/register_fault_tests_output.txt','fault_cases':37,'checker_agrees':27,'gaps':['F21','F22','F23','F25','F26','F30','F31','F33b','F33c','F35'],'make_check_on_mutated_copies':'non-zero exit for duplicate ID, missing field, unknown dependency, cycle, missing backlog ticket and a client name in a shared Python module; zero for the name in demo.py (exempt), in web/app.js and for a first-client person name (PRV-04, PRV-10)'},
 'experimental_copy':{'what':'RC-01 to RC-03 corrections applied to a temporary copy only; not a delivered fix','patch':'evidence/experimental-correction.patch','commands':exp,'new_probe_verdicts':exp_verdicts},
 'not_run':[
  {'id':'UC-6','result':'NOT_RUN','reason':'duplicated payment row vocabulary; by reading only'},
  {'id':'UC-8','result':'NOT_RUN','reason':'RA-05 across a period boundary; delivered tests only'},
  {'id':'UC-9','result':'NOT_RUN','reason':'RA-07 journal support path; delivered tests only'},
  {'id':'external linter / type checker','result':'NOT_RUN','reason':'none exists in the project; make check says so'},
  {'id':'make test in a restricted sandbox without loopback','result':'NOT_RUN','reason':'my environment allowed loopback; the developer\'s preserved bind failure was read, not reproduced'}],
 'deferred':'21 validation cases are DEFERRED-OK; AP, AR, reconciliation, close execution, reporting, integrations, hosting, briefing and communications are not implemented and are not counted as defects.'
}
json.dump(result,open(os.path.join(out_dir,'FABLE_RB_ACCEPTANCE_RESULTS.json'),'w'),indent=1)
print('written; assertions',len(assertions),'| new probes',len(new),'| experiment commands',len(exp))
