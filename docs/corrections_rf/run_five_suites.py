"""Five sequential exact make test runs with observation-only HTTP timing."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/corrections_rf'

def main():
    expected=json.loads((OUT/'final-validation-source-sha256.json').read_text())
    def unchanged():
        assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in expected.items()),'Code changed during consecutive-suite validation'
    unchanged()
    target=Path('/tmp/aaos-rf-timing/sitecustomize.py')
    assert target.read_bytes()==(OUT/'http_setup_sitecustomize.py').read_bytes()
    env=dict(os.environ,PYTHONPATH=str(target.parent)+os.pathsep+str(ROOT))
    suite_count=sum(1 for p in (ROOT/'tests').glob('test_*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'))
    results=[]
    for i in range(1,6):
        label='consecutive-make-test-%d'%i
        assert not (OUT/(label+'.json')).exists(),'Never overwrite a completed suite log'
        print('Starting '+label,flush=True)
        # This orchestrator runs no other validation while the suite is active.
        load=os.getloadavg();start=time.time()
        run=subprocess.run([sys.executable,str(OUT/'run.py'),label,'make','test'],cwd=ROOT,env=env)
        stderr=(OUT/(label+'.stderr.txt')).read_text()
        timing=[json.loads(line.split(' ',1)[1]) for line in stderr.splitlines() if line.startswith('RF_HTTP_SETUP ')]
        counts=re.findall(r'(?m)^Ran (\d+) tests in ([\d.]+)s$',stderr)
        http=re.findall(r'(?m)^test_\S+ \(test_http.HTTPCase\) \.\.\. ok$',stderr)
        record={'label':label,'exit_code':run.returncode,'expected_methods':suite_count,'reported_counts':counts,'HTTP_methods_executed':len(http),'HTTP_setup':timing,'start_load_average':load,'elapsed_seconds':round(time.time()-start,3)}
        results.append(record);(OUT/'five-suite-results.json').write_text(json.dumps(results,indent=2)+'\n')
        unchanged()
        assert run.returncode==0 and stderr.rstrip().endswith('OK'),record
        assert not re.search(r'\.\.\. (skipped|expected failure|unexpected success)',stderr),record
        assert len(counts)==1 and int(counts[0][0])==suite_count,record
        assert len(http)==11 and len(timing)==1 and not timing[0]['setup_failed'] and timing[0]['worker_wait_seconds']<5,record
        print('Completed '+label+' '+json.dumps(record),flush=True)
    print('PASS: five consecutive complete make test runs; no omitted methods, unchanged code, eleven HTTP methods each.',flush=True)

if __name__=='__main__':main()
