"""Read-only checks of both change inventories, both patches, and retained test methods."""
import hashlib, io, json, os, re, sys, zipfile
root, initial, batch2 = sys.argv[1:4]
sha = lambda b: hashlib.sha256(b).hexdigest()
rd = lambda p: open(os.path.join(root, p), 'rb').read()
EXT = ('.py', '.json', '.js', '.html', '.css')
def scoped(n):
    return (n.startswith(('accounting_agent/', 'tests/', 'scripts/', 'review/')) and n.endswith(EXT) and '__pycache__' not in n and '/original/' not in n) or n == 'Makefile'
cur = {}
for d, _, fs in os.walk(root):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), root)
        if scoped(rel): cur[rel] = sha(open(os.path.join(d, f), 'rb').read())
def baseline(zip_rel):
    z = zipfile.ZipFile(io.BytesIO(rd(zip_rel))); names = [n for n in z.namelist() if not n.endswith('/')]
    pre = os.path.commonprefix(names); pre = pre[:pre.rfind('/') + 1] if '/' in pre else ''
    return {n[len(pre):]: sha(z.read(n)) for n in names}
def check(label, inv_rel, patch_rel, zip_rel):
    base = baseline(zip_rel); inv = json.loads(rd(inv_rel)); files = inv['files']
    listed = {e['file']: e for e in files}
    changed = sorted(n for n in cur if base.get(n) != cur[n]); removed = sorted(n for n in base if scoped(n) and n not in cur)
    bad_hash = [n for n, e in listed.items() if os.path.exists(os.path.join(root, n)) and e.get('sha256') and sha(rd(n)) != e['sha256']]
    bad_base = [n for n, e in listed.items() if e.get('baseline_sha256') and base.get(n) and base[n] != e['baseline_sha256']]
    patch = rd(patch_rel).decode('utf-8', 'replace'); pf = set(re.findall(r'(?m)^\+\+\+ (?:b/)?([^\t\n]+)', patch))
    web = [n for n in changed if n.endswith(('.js', '.html', '.css'))]
    print('%s: baseline %s' % (label, inv.get('baseline')))
    print('   runtime/test files changed (computed): %d | removed: %s | web assets among them: %s' % (len(changed), removed, web))
    print('   inventory entries: %d | computed changes not listed: %s | listed current-hash mismatches: %s | listed baseline-hash mismatches: %s' % (len(listed), sorted(set(changed) - set(listed)), bad_hash, bad_base))
    print('   patch files: %d | computed changes not in patch: %s' % (len(pf), sorted(n for n in changed if not any(p.endswith(n) for p in pf))))
check('1. correction pass', 'docs/reverification/changed-files.json', 'docs/reverification/source-and-tests.patch', 'exports/FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip')
check('2. cumulative since Batch 1', 'docs/batch2/changed-files.json', 'docs/batch2/source-and-tests.patch', 'exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip')
def methods(text):
    out = {}
    for m in re.finditer(r'(?ms)^    def (test_\w+)\(self.*?(?=^    def |\Z)', text):
        out[m.group(1)] = len(re.findall(r'self\.assert\w+|assert ', m.group(0)))
    return out
def zread(zip_rel, name):
    z = zipfile.ZipFile(io.BytesIO(rd(zip_rel))); n = [x for x in z.namelist() if x.endswith(name)][0]; return z.read(n).decode()
print('3. platform and HTTP test methods retained, by baseline')
for label, getter in (('initial 0.1.0 bundle', lambda f: open(os.path.join(initial, 'tests', f)).read()),
                      ('Batch 1 baseline archive', lambda f: zread('exports/FABLE_BATCH_1_REVIEW_BUNDLE.zip', 'tests/' + f)),
                      ('reviewed Batch 2 checkpoint', lambda f: open(os.path.join(batch2, 'tests', f)).read())):
    total = kept = 0; fewer = []
    for f in ('test_platform.py', 'test_http.py'):
        o, c = methods(getter(f)), methods(rd('tests/' + f).decode())
        total += len(o); kept += sum(1 for k in o if k in c); fewer += [(k, o[k], c[k]) for k in o if k in c and c[k] < o[k]]
    print('   %-28s methods %d | still present %d | with fewer assertions now: %s' % (label, total, kept, fewer))
alltests = sum(len(methods(rd('tests/' + f).decode())) for f in os.listdir(os.path.join(root, 'tests')) if f.startswith('test_') and f.endswith('.py'))
marks = sum(rd('tests/' + f).decode().count(m) for f in os.listdir(os.path.join(root, 'tests')) if f.endswith('.py') for m in ('expectedFailure', 'unittest.skip', '@skip', 'skipTest'))
print('   test methods defined now: %d | expected-failure or skip markers: %d' % (alltests, marks))
