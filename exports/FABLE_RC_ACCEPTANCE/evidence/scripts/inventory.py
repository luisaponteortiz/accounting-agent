"""Independent inventory check (read-only).
usage: inventory.py <rc-bundle-dir> <v2-bundle-dir> <working-project>
"""
import hashlib, json, os, sys

rc, v2, project = sys.argv[1:4]


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
            out[os.path.relpath(p, root)] = sha(p)
    return out


R, V = walk(rc), walk(v2)
print('rc files', len(R), 'v2 files', len(V))

print('== protected inputs (input-checksums.json) ==')
ic = json.load(open(os.path.join(rc, 'docs/corrections_rc/input-checksums.json')))
bad_w, bad_b, absent_w, absent_b = [], [], [], []
for rel, h in ic.items():
    pw = os.path.join(project, rel)
    if not os.path.exists(pw):
        absent_w.append(rel)
    elif sha(pw) != h:
        bad_w.append(rel)
    if rel not in R:
        absent_b.append(rel)
    elif R[rel] != h:
        bad_b.append(rel)
print('entries', len(ic))
print('working: mismatched', bad_w, 'absent', absent_w)
print('bundle : mismatched', bad_b, 'absent', len(absent_b), absent_b[:20])
tops = {}
for rel in ic:
    k = '/'.join(rel.split('/')[:2])
    tops[k] = tops.get(k, 0) + 1
print('protected by area:', json.dumps(tops, indent=0)[:3000])

print('== difference against V2 ==')
added = sorted(set(R) - set(V))
removed = sorted(set(V) - set(R))
changed = sorted(k for k in R if k in V and R[k] != V[k])
print('added', len(added), 'removed', len(removed), 'changed', len(changed))
print('removed:', removed)
print('changed:', changed)

cf = json.load(open(os.path.join(rc, 'docs/corrections_rc/changed-files.json')))
print('changed-files.json keys:', list(cf.keys()) if isinstance(cf, dict) else type(cf))
json.dump({'added': added, 'removed': removed, 'changed': changed}, open(os.path.join(os.path.dirname(rc), 'evidence', 'diff-vs-v2.json'), 'w'), indent=1)
