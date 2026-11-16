import sys, json, hashlib, os
new, base, proj = sys.argv[1], sys.argv[2], sys.argv[3]
def sha(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
def walk(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root)] = sha(p)
    return out
n = walk(new); b = walk(base)
m = json.load(open(os.path.join(new,'REVIEW_MANIFEST.json')))['files']
on_disk = set(n) - {'REVIEW_MANIFEST.json'}
print("manifest entries", len(m), "payload files", len(on_disk))
print("missing from disk", sorted(set(m)-on_disk)[:10])
print("not in manifest", sorted(on_disk-set(m))[:10])
print("hash mismatches", [k for k in m if k in n and n[k]!=m[k]][:10])
added = sorted(set(n)-set(b)); removed = sorted(set(b)-set(n)); changed = sorted(k for k in n if k in b and n[k]!=b[k])
print("vs baseline: added", len(added), "removed", len(removed), "changed", len(changed))
print("REMOVED:", removed)
print("CHANGED:"); [print("  ", c) for c in changed]
import collections
c = collections.Counter('/'.join(a.split('/')[:3]) for a in added)
print("ADDED by prefix:"); [print("  ", k, v) for k, v in sorted(c.items())]
json.dump({'added': added, 'removed': removed, 'changed': changed}, open(sys.argv[4], 'w'), indent=1)
# compare with working project
diff = []; missing = []
for k, h in n.items():
    if k == 'REVIEW_MANIFEST.json': continue
    p = os.path.join(proj, k)
    if not os.path.exists(p): missing.append(k)
    elif sha(p) != h: diff.append(k)
print("bundle vs working project: missing in project", missing[:20], "differing", diff[:40])
