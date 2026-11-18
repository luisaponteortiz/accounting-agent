import hashlib, json, os, sys
root = sys.argv[1]
m = json.load(open(os.path.join(root, "REVIEW_MANIFEST.json")))
print("manifest keys:", [k for k in m if k != "files"])
for k in m:
    if k != "files":
        v = m[k]
        print(" ", k, "=", (v if not isinstance(v, (list, dict)) else (type(v).__name__, len(v))))
files = m.get("files")
listed = {}
if isinstance(files, dict):
    listed = files
elif isinstance(files, list):
    for f in files:
        listed[f.get("path")] = f
bad = 0
for path, meta in sorted(listed.items()):
    full = os.path.join(root, path)
    if not os.path.exists(full):
        print("MISSING", path); bad += 1; continue
    h = hashlib.sha256(open(full, "rb").read()).hexdigest()
    exp = meta if isinstance(meta, str) else (meta.get("sha256") or meta.get("hash"))
    if h != exp:
        print("MISMATCH", path, h, exp); bad += 1
actual = set()
for d, _, fs in os.walk(root):
    for f in fs:
        actual.add(os.path.relpath(os.path.join(d, f), root))
extra = sorted(actual - set(listed) - {"REVIEW_MANIFEST.json"})
print("listed:", len(listed), "actual (excl manifest):", len(actual - {"REVIEW_MANIFEST.json"}), "bad:", bad, "unlisted:", extra)
