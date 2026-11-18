"""Static evidence checks: change inventory, frozen inputs, retained tests. Reads only."""
import hashlib, io, json, os, re, sys, zipfile
root, original = sys.argv[1], sys.argv[2]
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: open(os.path.join(root, p), 'rb').read()

print('1. changed-files.json against the Batch 1 baseline archive')
inv = json.loads(read('docs/batch2/changed-files.json'))
print('   inventory keys:', sorted(inv) if isinstance(inv, dict) else type(inv).__name__)
base = zipfile.ZipFile(io.BytesIO(read('exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip')))
bnames = {n for n in base.namelist() if not n.endswith('/')}
prefix = os.path.commonprefix(sorted(bnames)) if bnames else ''
prefix = prefix[:prefix.rfind('/') + 1] if '/' in prefix else ''
bfiles = {n[len(prefix):]: sha(base.read(n)) for n in bnames}
scope = lambda n: n.startswith(('accounting_agent/', 'tests/', 'scripts/', 'review/')) or n in ('Makefile',)
cur = {}
for d, _, fs in os.walk(root):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), root)
        if scope(rel) and '__pycache__' not in rel:
            cur[rel] = sha(open(os.path.join(d, f), 'rb').read())
actual_changed = sorted(n for n in cur if bfiles.get(n) != cur[n])
actual_removed = sorted(n for n in bfiles if scope(n) and n not in cur)
listed = inv.get('files', inv) if isinstance(inv, dict) else inv
names = set()
mism = []
for e in (listed.values() if isinstance(listed, dict) and all(isinstance(v, dict) for v in listed.values()) else listed):
    if isinstance(e, dict):
        n = e.get('path') or e.get('file'); names.add(n)
        h = e.get('sha256') or e.get('after_sha256') or e.get('new_sha256') or e.get('current_sha256')
        if h and n in cur and cur[n] != h: mism.append(n)
    elif isinstance(e, str): names.add(e)
if isinstance(listed, dict) and not names: names = set(listed)
print('   source/test files that differ from baseline (computed):', len(actual_changed), '| removed:', actual_removed)
print('   listed in inventory:', len(names), '| computed-but-unlisted:', sorted(set(actual_changed) - names)[:12], '| listed hash mismatches:', mism)
patch = read('docs/batch2/source-and-tests.patch').decode('utf-8', 'replace')
pfiles = set(re.findall(r'^\+\+\+ (?:b/)?([^\t\n]+)', patch, re.M))
pfiles = {p.split('/', 1)[1] if p.split('/', 1)[0] not in ('accounting_agent', 'tests', 'scripts', 'review', 'Makefile') and '/' in p else p for p in pfiles}
print('   files in patch:', len(pfiles), '| computed changes missing from patch:', sorted(n for n in actual_changed if not any(p.endswith(n) for p in pfiles))[:12])

print('2. the four verification inputs: outer bundle, frozen corrective archive, recorded checksums')
chk = json.loads(read('docs/batch2/input-checksums.json'))
frozen = zipfile.ZipFile(io.BytesIO(read('exports/FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip')))
for name, meta in chk.items():
    outer = sha(read('exports/FABLE_BATCH_1_VERIFICATION/' + name))
    inner = [sha(frozen.read(n)) for n in frozen.namelist() if n.endswith('FABLE_BATCH_1_VERIFICATION/' + name)]
    mine = sha(open(os.path.join(original, name), 'rb').read())
    print('   %-34s recorded==outer:%s outer==frozen:%s outer==reviewer original:%s' % (name, meta['sha256'] == outer, inner == [outer], mine == outer))

print('3. frozen checkpoint contains no Batch 2 modules')
fz = [n for n in frozen.namelist() if 'accounting_agent/' in n and n.endswith('.py')]
print('   python modules in frozen archive:', sorted(os.path.basename(n) for n in fz))

print('4. original platform/HTTP test methods retained')
orig = sys.argv[3]
def methods(path):
    out = {}
    src = open(path).read()
    for m in re.finditer(r'^    def (test_\w+)\(self.*?(?=^    def |\Z)', src, re.M | re.S):
        body = m.group(0); out[m.group(1)] = (len(re.findall(r'self\.assert\w+|assert ', body)), sha(body.encode())[:8])
    return out
total = kept = changed = 0; weaker = []
for f in ('test_platform.py', 'test_http.py'):
    o, c = methods(os.path.join(orig, 'tests', f)), methods(os.path.join(root, 'tests', f))
    total += len(o); kept += sum(1 for k in o if k in c)
    for k in o:
        if k in c and o[k][1] != c[k][1]:
            changed += 1
            if c[k][0] < o[k][0]: weaker.append((f, k, o[k][0], c[k][0]))
    print('   %s: original methods %d, still present %d, current methods %d' % (f, len(o), sum(1 for k in o if k in c), len(c)))
print('   total original %d | retained %d | bodies changed %d | fewer assertions than original: %s' % (total, kept, changed, weaker))
tp = open(os.path.join(root, 'tests/test_reviewer_probes.py')).read()
print('5. expectedFailure markers left in tests:', sum(open(os.path.join(root, 'tests', f)).read().count('expectedFailure') for f in os.listdir(os.path.join(root, 'tests')) if f.endswith('.py')))
print('   probe tests for P08/P15:', re.findall(r'def (test_P(?:08|15)\w*)', tp))
