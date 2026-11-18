"""Finish the current read-only searches/gates before five otherwise-idle suites."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/corrections_rf'
needed={'baseline-re-step-search':1,'current-rf-gate':0,'final-rf-gate':0,'final-re-gate':0,'final-rd-gate':0,'final-re-register-faults':1,'full-suite-before-retained-test-decision':2}
while True:
    pending=[]
    for label,expected in needed.items():
        p=OUT/(label+'.json')
        if not p.exists():pending.append(label);continue
        actual=json.loads(p.read_text())['exit_code'];assert actual==expected,(label,actual,expected)
    if not pending:break
    print('Waiting for existing validations: '+', '.join(pending),flush=True)
    time.sleep(30)
print('All other managed validation jobs finished. Starting five sequential suites.',flush=True)
print('Start load averages: '+str(os.getloadavg()),flush=True)
subprocess.run([sys.executable,str(OUT/'run_five_suites.py')],cwd=ROOT,check=True)
