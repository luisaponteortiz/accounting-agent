"""Read-only comparison of the immutable RE review folder with its pinned ZIP."""
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a'
with zipfile.ZipFile(path) as z:
    names={n for n in z.namelist() if not n.endswith('/')}
    actual={p.relative_to(ROOT/'exports').as_posix() for p in (ROOT/'exports/FABLE_RE_ACCEPTANCE').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store'}
    assert names==actual,(names-actual,actual-names)
    assert z.testzip() is None
    assert all((ROOT/'exports'/n).read_bytes()==z.read(n) for n in names)
print(json.dumps({'response_zip_hash_verified':True,'CRC_verified':True,'review_folder_files':len(names),'every_review_folder_byte_matches_response_zip':True,'extra_or_missing_files':0},indent=2))
