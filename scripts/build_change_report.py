"""Portable source diff against the actual delivered Batch 1 archive."""
import ast
import argparse
import difflib
import hashlib
import json
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',default='exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip')
parser.add_argument('--output-dir',default='docs/batch2')
args=parser.parse_args()
output=root/args.output_dir
output.mkdir(parents=True,exist_ok=True)
active=['AGENTS.md','README.md','PROGRESS.md','DECISIONS.md','REVIEW_FREEZE.md','Makefile','FABLE_ACCOUNTING_HANDOFF.md','FABLE_REVERIFICATION_PROMPT.md']
for folder in ('accounting_agent','tests','scripts','review'):
    active += [str(p.relative_to(root)) for p in (root/folder).rglob('*') if p.is_file() and p.suffix in ('.py','.json','.js','.html','.css') and '__pycache__' not in p.parts and 'original' not in p.parts]
active += [str(p.relative_to(root)) for p in (root/'docs').glob('*.md')]
active += [str(p.relative_to(root)) for p in root.glob('FABLE*.md')]
with zipfile.ZipFile(root/args.baseline) as baseline:
    members=set(baseline.namelist());patch=[];changes=[]
    for name in sorted(set(active)):
        p=root/name
        if not p.exists():continue
        old=baseline.read(name) if name in members else b'';new=p.read_bytes()
        if old==new:continue
        changes.append({'file':name,'status':'modified' if name in members else 'added','baseline_sha256':hashlib.sha256(old).hexdigest() if name in members else None,'sha256':hashlib.sha256(new).hexdigest()})
        patch.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+name if name in members else '/dev/null',tofile='b/'+name))
    retained={}
    for name in ('tests/test_platform.py','tests/test_http.py'):
        methods=lambda raw:{n.name for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
        before=methods(baseline.read(name));after=methods((root/name).read_text())
        assert before<=after
        retained[name]={'original_methods':len(before),'retained':sorted(before),'missing':sorted(before-after)}
(output/'source-and-tests.patch').write_text(''.join(patch))
(output/'changed-files.json').write_text(json.dumps({'baseline':args.baseline,'original_test_methods':retained,'files':changes},indent=2)+'\n')
print('Compared',len(changes),'changed files; preserved',sum(v['original_methods'] for v in retained.values()),'baseline platform/HTTP methods.')
