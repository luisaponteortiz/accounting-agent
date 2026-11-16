"""Independent preservation and inventory checks (read-only).
usage: preservation.py <rc-bundle-dir> <v2-bundle-dir> <run-copy>
"""
import ast, hashlib, json, os, re, sys

rc, v2, runc = sys.argv[1:4]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def methods(root):
    out = {}
    d = os.path.join(root, 'tests')
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.py'):
            continue
        tree = ast.parse(open(os.path.join(d, fn)).read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for b in node.body:
                    if isinstance(b, ast.FunctionDef) and b.name.startswith('test'):
                        out[(fn, node.name, b.name)] = ast.dump(b)
    return out


print('== test methods ==')
MV, MR = methods(v2), methods(rc)
print('V2 methods', len(MV), '| RC methods', len(MR), '| V2 methods missing in RC:', sorted(set(MV) - set(MR)))
print('V2 methods whose body changed:', sorted(k for k in MV if k in MR and MV[k] != MR[k]))
new = sorted(set(MR) - set(MV))
print('new methods', len(new))
for k in new:
    print('   ', k)
for fn in sorted(os.listdir(os.path.join(v2, 'tests'))):
    a, b = os.path.join(v2, 'tests', fn), os.path.join(rc, 'tests', fn)
    if os.path.isfile(a) and (not os.path.exists(b) or sha(a) != sha(b)):
        print('test file differs from V2:', fn)
print('test files only in RC:', sorted(set(os.listdir(os.path.join(rc, 'tests'))) - set(os.listdir(os.path.join(v2, 'tests')))))
markers = []
for fn in sorted(os.listdir(os.path.join(rc, 'tests'))):
    if fn.endswith('.py'):
        for n, line in enumerate(open(os.path.join(rc, 'tests', fn)), 1):
            if re.search(r'skip|expectedFailure|SkipTest', line):
                markers.append((fn, n, line.strip()[:120]))
print('skip / expectedFailure markers in tests:', markers)
# additive check for tests/test_product_requirements.py
a = open(os.path.join(v2, 'tests/test_product_requirements.py')).read().splitlines()
b = open(os.path.join(rc, 'tests/test_product_requirements.py')).read().splitlines()
import difflib
removed = [l for l in difflib.unified_diff(a, b, lineterm='', n=0) if l.startswith('-') and not l.startswith('---')]
print('lines removed from tests/test_product_requirements.py against V2:', len(removed))
for l in removed[:20]:
    print('    ', l[:200])

print('\n== change inventory (PRV-09) ==')
cf = json.load(open(os.path.join(rc, 'docs/corrections_rc/changed-files.json')))
for k in ('baseline', 'baseline_sha256', 'scope'):
    print(k, ':', json.dumps(cf[k])[:400])
print('coverage_rules:', json.dumps(cf['coverage_rules'], indent=1)[:2500])
print('self_artifacts_covered_by_manifest:', cf['self_artifacts_covered_by_manifest'])
print('output_envelope:', json.dumps(cf['output_envelope'])[:600])
print('original_tests:', json.dumps(cf['original_tests'])[:600])
files = cf['files']
print('files entries:', len(files), '| sample:', json.dumps(files[:2] if isinstance(files, list) else dict(list(files.items())[:2]))[:600])
diff = json.load(open(os.path.join(os.path.dirname(rc), 'evidence', 'diff-vs-v2.json')))
listed = {}
for e in (files if isinstance(files, list) else [dict(v, path=k) if isinstance(v, dict) else {'path': k, 'sha256': v} for k, v in files.items()]):
    listed[e.get('path') or e.get('file')] = e
differing = set(diff['added']) | set(diff['changed']) | set(diff['removed'])
selfa = set(cf['self_artifacts_covered_by_manifest'])
uncovered = sorted(p for p in differing if p not in listed and p not in selfa and p != 'REVIEW_MANIFEST.json')
print('differing files against V2:', len(differing), '| listed:', len(listed), '| differing but not listed, not self-artifact, not the manifest:', len(uncovered))
for p in uncovered[:40]:
    print('    ', p)
extra = sorted(p for p in listed if p not in differing)
print('listed but identical to V2 or absent from the bundle:', extra[:20])
bad = []
for p, e in listed.items():
    h = next((v for k, v in e.items() if isinstance(v, str) and re.fullmatch(r'[a-f0-9]{64}', v) and k not in ('baseline_sha256', 'before_sha256', 'v2_sha256', 'old_sha256')), None)
    fp = os.path.join(rc, p)
    if os.path.exists(fp) and h and sha(fp) != h:
        bad.append((p, e))
print('listed hashes that disagree with the bundle file:', bad[:5])
print('entry keys:', sorted({k for e in listed.values() for k in e}))

print('\n== files the eleven commands changed in the run copy ==')
ch = []
for d, dirs, fs in os.walk(runc):
    dirs[:] = [x for x in dirs if x != '__pycache__']
    for fn in fs:
        p = os.path.join(d, fn); rel = os.path.relpath(p, runc)
        q = os.path.join(rc, rel)
        if not os.path.exists(q):
            ch.append(('added', rel))
        elif sha(p) != sha(q):
            ch.append(('changed', rel))
print(len(ch)); [print('   ', c) for c in ch[:30]]
