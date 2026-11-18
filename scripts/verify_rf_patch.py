"""Apply the RF source/test patch to a disposable immutable RE checkpoint."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile
from build_rf_review_bundle import ROOT,BASELINE,prepare,payload_files

def main():
    inventory=prepare();payload=payload_files()
    patch=ROOT/'docs/corrections_rf/source-and-tests.patch'
    names=[r['file'] for r in inventory['files'] if r['file'] in ('Makefile','review/fable_rd_feed_contract_probes.py') or r['file'].startswith(('accounting_agent/','tests/','scripts/'))]
    with tempfile.TemporaryDirectory(prefix='aaos-rf-patch-') as tmp:
        work=Path(tmp)
        with zipfile.ZipFile(ROOT/BASELINE) as z:z.extractall(work)
        for options in (['--dry-run'],[]):
            run=subprocess.run(['patch','-p1','--batch']+options+['-i',str(patch)],cwd=work,capture_output=True,text=True)
            print(run.stdout,end='');print(run.stderr,end='')
            assert run.returncode==0,run.returncode
        assert all((work/n).read_bytes()==payload[n] if n in payload else not (work/n).exists() for n in names)
    print(json.dumps({'patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'dry_run_exit':0,'apply_exit':0,'all_changed_code_test_gate_adapter_files_reproduced_exactly':True,'count':len(names),'files':names},indent=2))

if __name__=='__main__':main()
