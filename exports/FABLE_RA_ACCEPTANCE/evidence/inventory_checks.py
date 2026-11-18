"""Independent inventory checks. usage: inventory_checks.py <ra_checkpoint> <rv_baseline> <ra_run>"""
import ast, hashlib, json, re, sys, zipfile, io
from pathlib import Path
ra, base, run = map(Path, sys.argv[1:4])
sums = json.loads((ra/'docs/acceptance_ra/input-checksums.json').read_text())
bad = [n for n, h in sums.items() if hashlib.sha256((ra/n).read_bytes()).hexdigest() != h]
print('input-checksums.json entries:', len(sums), '| mismatches:', bad)
def tree(root):
    out = {}
    for sub in ('accounting_agent', 'tests', 'scripts', 'review', 'Makefile'):
        p = root/sub
        for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
            if f.is_file() and '__pycache__' not in f.parts: out[str(f.relative_to(root))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out
a, b = tree(base), tree(ra)
changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
print('source/test/script/review files differing from the frozen RV baseline:', len(changed)); print('  ', changed)
cf = json.loads((ra/'docs/acceptance_ra/changed-files.json').read_text())
flat = json.dumps(cf)
print('each differing file named in changed-files.json:', all(c in flat for c in changed), '| not named:', [c for c in changed if c not in flat])
def methods(root):
    out = set()
    for f in sorted((root/'tests').glob('test_*.py')):
        for n in ast.walk(ast.parse(f.read_text())):
            if isinstance(n, ast.ClassDef):
                for m in n.body:
                    if isinstance(m, ast.FunctionDef) and m.name.startswith('test'): out.add(f.name + '::' + n.name + '.' + m.name)
    return out
cur = methods(ra); old = methods(base)
print('test methods now:', len(cur), '| in frozen RV baseline:', len(old), '| baseline methods no longer present:', sorted(old - cur), '| new:', len(cur - old))
for f in ('tests/test_acceptance_corrections.py', 'tests/test_acceptance_gate.py'):
    print('  ', f, sum(1 for m in cur if m.startswith(Path(f).name)), 'methods')
for name in ('FABLE_BATCH_1_REVIEW_BUNDLE.zip', 'FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip', 'FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip'):
    z = zipfile.ZipFile(ra/'exports'/name); names = set()
    for n in z.namelist():
        if re.match(r'tests/test_(platform|http)\.py$', n):
            for node in ast.walk(ast.parse(z.read(n).decode())):
                if isinstance(node, ast.ClassDef):
                    for m in node.body:
                        if isinstance(m, ast.FunctionDef) and m.name.startswith('test'): names.add(Path(n).name + '::' + node.name + '.' + m.name)
    print('  ', name, 'platform/HTTP methods:', len(names), '| missing now:', sorted(names - cur))
src = ''.join(f.read_text() for f in (ra/'tests').glob('*.py'))
print('expectedFailure/skip markers in tests:', re.findall(r'expectedFailure|unittest\.skip|skipTest|skipIf|skipUnless', src))
v = json.loads((run/'docs/batch2/final-validation.json').read_text())
def cases(o):
    if isinstance(o, dict):
        if 'id' in o and isinstance(o.get('id'), str) and o['id'].startswith('FV-'): yield o
        for x in o.values(): yield from cases(x)
    elif isinstance(o, list):
        for x in o: yield from cases(x)
cs = list(cases(v)); import collections
key = next((k for k in ('verdict', 'status', 'result', 'outcome') if cs and k in cs[0]), None)
print('60-case report from my run: cases', len(cs), '| by', key, dict(collections.Counter(c.get(key) for c in cs)))
json.dump({c['id']: c.get(key) for c in cs}, open(Path(sys.argv[0]).parent/'my-60-case-results.json', 'w'), indent=1)
