"""Independent integrity check of the RC/PRV bundle (read-only).
usage: integrity.py <extracted-bundle> <working-project> <bundle-zip>
"""
import hashlib, json, os, sys, zipfile

bundle, project, zpath = sys.argv[1:4]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def walk(root):
    out = {}
    for d, dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root)] = p
    return out


print('== bundle zip ==')
print('sha256', sha(zpath))
with zipfile.ZipFile(zpath) as z:
    print('zip testzip (first bad member or None):', z.testzip())
    names = [i.filename for i in z.infolist() if not i.is_dir()]
    print('zip members (files):', len(names), 'duplicates:', len(names) - len(set(names)))
    bad = [n for n in names if n.startswith('/') or '..' in n.split('/')]
    print('unsafe member paths:', bad)

print('== manifest ==')
man = json.load(open(os.path.join(bundle, 'REVIEW_MANIFEST.json')))
files = man['files']
present = walk(bundle)
mismatch = [k for k, v in files.items() if k not in present or sha(present[k]) != v]
unlisted = sorted(set(present) - set(files))
print('manifest entries', len(files), 'payload files on disk', len(present))
print('mismatch or missing:', mismatch)
print('on disk but not in manifest:', unlisted)
print('manifest sha256', sha(os.path.join(bundle, 'REVIEW_MANIFEST.json')))

print('== git/caches in payload ==')
print([k for k in present if k.startswith('.git/') or '__pycache__' in k or k.endswith('.pyc') or k.endswith('.DS_Store') or k.endswith('.sqlite3')])

print('== named archives in working project ==')
want = {
    'exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_RESPONSE.zip': '0562869ad210b4b3b8653b4600bc7f3b863f283e8087029c6b19719497a5f399',
    'exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_RESPONSE_V2.zip': 'd4c5795dfce0ab9584c53c874efb4693e3473d3dadfa37a0d3b1be89bf03d826',
    'exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_BUNDLE.zip': '00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d',
}
for rel, h in want.items():
    for root, label in ((project, 'working'), (bundle, 'bundle')):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            print(label, rel, 'OK' if sha(p) == h else 'MISMATCH ' + sha(p))
        else:
            print(label, rel, 'ABSENT')

print('== input-checksums.json ==')
ic = json.load(open(os.path.join(bundle, 'docs/corrections_rc/input-checksums.json')))
print('top-level type', type(ic).__name__, (list(ic.keys())[:10] if isinstance(ic, dict) else len(ic)))
json.dump(ic, open(os.path.join(os.path.dirname(bundle), 'evidence', 'input-checksums.copy.json'), 'w'), indent=1)
