"""Package reviewable source/evidence, excluding runtime data and credentials."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
label=sys.argv[1]
bundle=root/'exports'/(label+'_REVIEW_BUNDLE.zip')
if bundle.with_suffix('.FROZEN.json').exists():raise SystemExit('Frozen review submission cannot be overwritten; choose a new bundle label.')
files=[root/n for n in ('AGENTS.md','README.md','PROGRESS.md','DECISIONS.md','REVIEW_FREEZE.md','FABLE_ACCOUNTING_HANDOFF.md','FABLE_REVIEW_PROMPT.md','FABLE_REVERIFICATION_PROMPT.md','FABLE_RV_CORRECTIONS_HANDOFF.md','FABLE_RA_CORRECTIONS_HANDOFF.md','FABLE_RA_REVIEW_PROMPT.md','Makefile') if (root/n).exists()]
for folder in ('accounting_agent','tests','scripts','review','docs','exports/FABLE_BATCH_1_VERIFICATION','exports/FABLE_REVERIFICATION','exports/FABLE_RV_ACCEPTANCE'):
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.sqlite3','.db'))
for checkpoint_name in ('FABLE_BATCH_1_REVIEW_BUNDLE.zip','FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip','FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip','FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip'):
    checkpoint=root/'exports'/checkpoint_name
    if checkpoint.exists() and label+'_REVIEW_BUNDLE.zip'!=checkpoint_name:
        files.append(checkpoint)
        if checkpoint.with_suffix('.FROZEN.json').exists():files.append(checkpoint.with_suffix('.FROZEN.json'))
files=sorted(set(files))
manifest={'label':label,'scope':'Local fictional accounting preparation only; no database, credentials, live records, posting or deployment authority.', 'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
    for p in files:archive.write(p,p.relative_to(root))
    archive.writestr('REVIEW_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
    for name,value in manifest['files'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==value
print(bundle)
print('Verified',len(files),'source/evidence files')
