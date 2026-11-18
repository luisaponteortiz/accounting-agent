"""Sequential validation of the D-038 state on disposable clones; unmodified commands, complete logs."""
import hashlib,json,subprocess,sys,time,os,shutil
from pathlib import Path
S=Path(sys.argv[1]);val=S/'ucval';logs=S/'ucval-logs'
def tree(root):
    out={}
    for d in ('accounting_agent','tests','scripts','review'):
        for p in sorted((root/d).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.sqlite3','.pyc'):out[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for n in ('Makefile','docs/PRODUCT_REQUIREMENTS.md','docs/INDEPENDENT_VERIFICATION_RESULTS.json','DECISIONS.md','README.md','START_HERE.md','AGENTS.md','PROGRESS.md','docs/ARCHITECTURE.md','docs/CAPABILITY_CONTRACTS.md','docs/CONNECTION_READINESS.md','FABLE_ACCOUNTING_HANDOFF.md','REVIEW_FREEZE.md','HANDOFF_RF_REGISTRATION_2026-11-17.md'):out[n]=hashlib.sha256((root/n).read_bytes()).hexdigest()
    return out
results=[]
def run(label,argv,cwd):
    start=time.time();started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());load=os.getloadavg()
    with open(logs/(label+'.stdout.txt'),'wb') as o,open(logs/(label+'.stderr.txt'),'wb') as e:
        code=subprocess.call(argv,cwd=cwd,stdout=o,stderr=e)
    results.append({'label':label,'argv':' '.join(argv),'exit_code':code,'elapsed_seconds':round(time.time()-start,3),'started_utc':started,'load_average_before':[round(x,2) for x in load]})
    (logs/'results.json').write_text(json.dumps(results,indent=1)+'\n')
before=tree(val);(logs/'tested-source-sha256.json').write_text(json.dumps(before,indent=1)+'\n')
run('make-test',['make','test'],val)
for target in ('check','batch2-gate','reverification-gate','acceptance-gate','rb-gate','rc-gate','rd-gate','re-gate','rf-gate'):
    run('make-'+target,['make',target],val)
py=sys.executable
run('re-review-probes-unmodified',[py,'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py','.'],val)
run('rf-review-probes-unmodified',[py,'exports/FABLE_RF_ACCEPTANCE/fable_rf_acceptance_probes.py','.'],val)
run('documentation-check',[py,'scripts/check_documentation.py','--json'],val)
after=tree(val)
(logs/'source-unchanged-after-run.json').write_text(json.dumps({'files':len(before),'unchanged':before==after,'differences':sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))},indent=1)+'\n')
run('baseline-review-tests-on-source-before-the-change',[py,'-m','unittest','tests.test_feed_repeat_decisions','-v'],S/'ucbase')
(logs/'DONE').write_text('done\n')
