"""Sequential validation of the registered project on disposable clones; unmodified commands, complete logs."""
import hashlib,json,subprocess,sys,time,zipfile,os
from pathlib import Path
S=Path(sys.argv[1]);val=S/'val';logs=S/'val-logs'
def tree(root):
    out={}
    for d in ('accounting_agent','tests','scripts','review'):
        for p in sorted((root/d).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.sqlite3','.pyc'):out[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for n in ('Makefile','docs/PRODUCT_REQUIREMENTS.md','docs/INDEPENDENT_VERIFICATION_RESULTS.json','DECISIONS.md'):out[n]=hashlib.sha256((root/n).read_bytes()).hexdigest()
    return out
results=[]
def run(label,argv,cwd):
    start=time.time();started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    load=os.getloadavg()
    with open(logs/(label+'.stdout.txt'),'wb') as o,open(logs/(label+'.stderr.txt'),'wb') as e:
        code=subprocess.call(argv,cwd=cwd,stdout=o,stderr=e)
    results.append({'label':label,'argv':' '.join(argv),'exit_code':code,'elapsed_seconds':round(time.time()-start,3),'started_utc':started,'load_average_before':[round(x,2) for x in load]})
    (logs/'results.json').write_text(json.dumps(results,indent=1)+'\n')
before=tree(val);(logs/'tested-source-sha256.json').write_text(json.dumps(before,indent=1)+'\n')
run('make-test',['make','test'],val)
for target in ('check','batch2-gate','reverification-gate','acceptance-gate','rb-gate','rc-gate','rd-gate','re-gate','rf-gate'):
    run('make-'+target,['make',target],val)
after=tree(val)
(logs/'source-unchanged-after-run.json').write_text(json.dumps({'files':len(before),'unchanged':before==after,'differences':sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))},indent=1)+'\n')
py=sys.executable
run('register-faults-F-rb',[py,'exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py','.'],S/'vF')
run('register-faults-G-rc',[py,'exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py','.'],S/'vG')
run('register-faults-H-rd',[py,'exports/FABLE_RD_ACCEPTANCE/evidence/scripts/fable_rd_register_faults.py','.'],S/'vH')
run('register-faults-J-re',[py,'exports/FABLE_RE_ACCEPTANCE/evidence/scripts/fable_re_register_faults.py','.'],S/'vJ')
run('register-faults-K-rf',[py,'exports/FABLE_RF_ACCEPTANCE/evidence/scripts/fable_rf_register_faults.py','.'],S/'vK')
# Conflict reproduction: the two retained test files exactly as delivered at the RF checkpoint, against the registered project.
c=S/'vC'
with zipfile.ZipFile(c/'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip') as z:
    for n in ('tests/test_product_requirements.py','tests/test_product_requirements_rf.py'):(c/n).write_bytes(z.read(n))
run('conflict-unadapted-retained-register-tests',[py,'-m','unittest','tests.test_product_requirements','tests.test_product_requirements_rf','-v'],c)
(logs/'DONE').write_text('done\n')
