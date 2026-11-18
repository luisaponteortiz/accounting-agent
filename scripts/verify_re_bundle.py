"""Verify the finalized RE archive in clean copies; write adjacent evidence once."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
LABEL='FABLE_RE_AND_PRV_CORRECTIONS'
BUNDLE=ROOT/'exports'/(LABEL+'_REVIEW_BUNDLE.zip')
OUT=ROOT/'exports'/(LABEL+'_FINAL_VERIFICATION')
RESULT=ROOT/'exports'/(LABEL+'_FINAL_VERIFICATION.json')


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    if OUT.exists() or RESULT.exists():raise SystemExit('Final verification evidence already exists; never overwrite it.')
    OUT.mkdir()
    bundle_hash=sha(BUNDLE.read_bytes())
    package=json.loads((ROOT/'exports'/(LABEL+'_PACKAGE_CHECK.json')).read_text())
    assert BUNDLE.with_suffix('.zip.sha256').read_text().split()[0]==bundle_hash==package['bundle_sha256']
    with zipfile.ZipFile(BUNDLE) as archive:
        assert archive.testzip() is None
        names=archive.namelist();assert len(names)==len(set(names))
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
        manifest_raw=archive.read('REVIEW_MANIFEST.json');manifest=json.loads(manifest_raw)
        assert sha(manifest_raw)==package['manifest_sha256']
        assert set(names)==set(manifest['files'])|{'REVIEW_MANIFEST.json'}
        assert all(sha(archive.read(n))==h for n,h in manifest['files'].items())
        with tempfile.TemporaryDirectory(prefix='aaos-re-final-') as tmp:
            copy=Path(tmp)/'project';archive.extractall(copy)
            protected=json.loads((copy/'docs/corrections_re/input-checksums.json').read_text())
            assert all(sha((copy/n).read_bytes())==h==sha((ROOT/n).read_bytes()) for n,h in protected.items())
            commands=[]
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
            for label,command in (
                ('make-check',['make','check']),
                ('rb-register-faults',[sys.executable,'exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py','.']),
                ('rc-register-faults',[sys.executable,'exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py',str(copy)]),
                ('gate-faults',[sys.executable,'-m','unittest',
                    'tests.test_re_review_gate.REReviewGate.test_rejects_nonzero_missing_duplicate_unknown_changed_or_extra_verdicts',
                    'tests.test_re_review_gate.REReviewGate.test_only_Y05_part_a_is_adapted',
                    'tests.test_re_review_gate.REReviewGate.test_all_protected_inputs_unchanged_and_contract_exact','-v']),
            ):
                tick=time.monotonic();start=datetime.datetime.now(datetime.timezone.utc).isoformat()
                with (OUT/(label+'.stdout.txt')).open('x') as stdout,(OUT/(label+'.stderr.txt')).open('x') as stderr:
                    run=subprocess.run(command,cwd=copy,stdout=stdout,stderr=stderr,env=env)
                row={'command':command,'cwd':str(copy),'started_utc':start,'elapsed_seconds':round(time.monotonic()-tick,3),'exit_code':run.returncode}
                (OUT/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n');commands.append(row)
                assert run.returncode==0,row
                text=(OUT/(label+'.stdout.txt')).read_text()
                if label=='rb-register-faults':assert 'cases 37 | agree 37 | gaps 0' in text and 'GAP' not in text
                if label=='rc-register-faults':
                    assert 'cases 44 | agree 44 | gaps 0' in text and 'make check gaps 0' in text and 'GAP' not in text
                    for case in ('G16','G17','G18','G44'):
                        line=next(line for line in text.splitlines() if line.startswith(case+' '))
                        assert 'got=REJECTED' in line,line
                print(label,run.returncode,flush=True)
            changed=[n for n,h in manifest['files'].items() if sha((copy/n).read_bytes())!=h]
            extra=[p.relative_to(copy).as_posix() for p in copy.rglob('*') if p.is_file() and p.relative_to(copy).as_posix() not in set(names)]
            assert not changed and not extra,(changed,extra)
    assert bundle_hash==sha(BUNDLE.read_bytes())
    before=(ROOT/'docs/corrections_re/git-history-before.txt').read_text()
    now=subprocess.check_output(['git','log','--format=fuller'],cwd=ROOT,text=True)
    assert before==now and subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=ROOT,text=True).strip()=='8'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='review/fable-rc-acceptance'
    result={'bundle':BUNDLE.name,'bundle_sha256':bundle_hash,'manifest_sha256':sha(manifest_raw),'payload_files':len(manifest['files']),
            'crc_and_every_payload_hash_verified':True,'protected_inputs_verified_in_working_and_bundle':len(protected),
            'extracted_payload_changes_after_commands':changed,'extra_files_after_commands':extra,'eight_commits_unchanged':True,
            'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'commands':commands,
            'raw_evidence_sha256':{p.name:sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file()},
            'contract_completion':'DEVELOPER_VALIDATED_INDEPENDENT_REVIEW_PENDING','owner_clarification':'D-029',
            'independent_acceptance':'PENDING','human_G0':'NOT_GRANTED','batch3':'CLOSED'}
    with RESULT.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','raw_evidence_sha256')},indent=2))


if __name__=='__main__':main()
