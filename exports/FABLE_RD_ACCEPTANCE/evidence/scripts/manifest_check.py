import sys, json, hashlib, os
root, ext_manifest = sys.argv[1], sys.argv[2]
def sha(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
inner = os.path.join(root, 'REVIEW_MANIFEST.json')
print("inner manifest sha", sha(inner))
print("external manifest sha", sha(ext_manifest), "identical bytes", open(inner,'rb').read()==open(ext_manifest,'rb').read())
m = json.load(open(inner))
print("manifest keys", list(m.keys()) if isinstance(m, dict) else type(m))
for k,v in m.items():
    if not isinstance(v,(list,dict)): print("  ", k, "=", v)
    else: print("  ", k, type(v).__name__, len(v))
