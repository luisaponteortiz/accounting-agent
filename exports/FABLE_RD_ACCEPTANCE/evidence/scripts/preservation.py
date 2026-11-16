import sys, os, json, hashlib, zipfile, subprocess, re
S, P = sys.argv[1], sys.argv[2]
new, base, patched = S + '/newRef', S + '/baseRef', S + '/patchT'
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()
def tree(root, subs):
    out = {}
    for sub in subs:
        p = os.path.join(root, sub)
        if os.path.isfile(p): out[sub] = sha(p); continue
        for d, _, fs in os.walk(p):
            for f in fs:
                if f.endswith('.pyc'): continue
                q = os.path.join(d, f); out[os.path.relpath(q, root)] = sha(q)
    return out
print('== 1. patch applied to the baseline reproduces every source/test/script/Makefile byte')
subs = ['accounting_agent', 'tests', 'scripts', 'Makefile']
a, b = tree(patched, subs), tree(new, subs)
print('   files patched tree', len(a), '| new bundle', len(b), '| identical', a == b, '| differing', sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k)))
bb = tree(base, subs)
print('   source/test/script/Makefile files differing from baseline:', sorted(k for k in b if bb.get(k) != b[k]))
print('== 2. protected inputs (input-checksums.json)')
ic = json.load(open(new + '/docs/corrections_rd/input-checksums.json'))
for label, root in (('new bundle', new), ('working project', P)):
    bad = [k for k, h in ic.items() if not os.path.exists(os.path.join(root, k)) or sha(os.path.join(root, k)) != h]
    print('   %s: %d listed, %d mismatching %s' % (label, len(ic), len(bad), bad[:5]))
inb = [k for k in ic if os.path.exists(os.path.join(base, k))]
badb = [k for k in inb if sha(os.path.join(base, k)) != ic[k]]
print('   of these, present in the baseline bundle: %d, differing from baseline: %d %s' % (len(inb), len(badb), badb[:5]))
notin = [k for k in ic if k not in inb]
print('   not in the baseline bundle (later reviewer/owner inputs): %d, e.g. %s' % (len(notin), notin[:4]))
for must in ('exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py', 'exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py', 'exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py', 'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py', 'exports/FABLE_RC_ACCEPTANCE/evidence/scripts/fable_rc_register_faults.py', 'exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py', 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json', 'exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json', 'tests/schema_v1.sql', 'accounting_agent/storage.py'):
    print('   protected list contains %-78s %s' % (must, must in ic))
print('== 3. RC review folder against the returned response ZIP')
z = zipfile.ZipFile(P + '/exports/FABLE_RC_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip')
names = [n for n in z.namelist() if not n.endswith('/')]
def find(n, root):
    for cand in (n, 'exports/' + n, 'exports/FABLE_RC_ACCEPTANCE/' + n, 'exports/FABLE_RC_ACCEPTANCE/' + n.split('/', 1)[-1]):
        if os.path.isfile(os.path.join(root, cand)): return cand
for label, root in (('new bundle', new), ('working project', P)):
    same = diff = miss = 0
    for n in names:
        c = find(n, root)
        if not c: miss += 1; continue
        if hashlib.sha256(z.read(n)).hexdigest() == sha(os.path.join(root, c)): same += 1
        else: diff += 1
    print('   %s: response entries %d | identical %d | differing %d | not found %d' % (label, len(names), same, diff, miss))
onf = sum(len(fs) for _, _, fs in os.walk(P + '/exports/FABLE_RC_ACCEPTANCE'))
print('   files in working exports/FABLE_RC_ACCEPTANCE:', onf, '| (.DS_Store etc. included)')
print('== 4. earlier archives and sidecars in the working project')
ai = json.load(open(new + '/docs/corrections_rd/archive-integrity.json'))
for row in ai:
    p = os.path.join(P, row['file']); h = sha(p); side = p + '.sha256'
    sc = open(side).read().split()[0] if os.path.exists(side) else None
    print('   %-78s matches record %s | sidecar %s' % (row['file'], h == row['sha256'], 'none' if sc is None else sc == h))
allzip = sorted(f for f in os.listdir(P + '/exports') if f.endswith('.zip'))
print('   zip files in working exports: %d; not in the developer list: %s' % (len(allzip), [f for f in allzip if 'exports/' + f not in {r['file'] for r in ai}]))
print('   V2 hash:', sha(P + '/exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_BUNDLE.zip'))
print('== 5. earlier bundles carried inside the new bundle equal the working copies')
for f in allzip:
    q = os.path.join(new, 'exports', f)
    if os.path.exists(q): print('   %-70s identical %s' % (f, sha(q) == sha(os.path.join(P, 'exports', f))))
print('== 6. schema')
for f in ('accounting_agent/storage.py', 'tests/schema_v1.sql'):
    print('   %-32s identical to baseline %s' % (f, sha(os.path.join(new, f)) == sha(os.path.join(base, f))))
print('== 7. working project git state (read-only)')
def git(*a): return subprocess.run(['git', '-C', P] + list(a), capture_output=True, text=True).stdout.strip()
print('   branch', git('branch', '--show-current'), '| HEAD', git('rev-parse', '--short', 'HEAD'), '| commits on branch', git('rev-list', '--count', 'HEAD'))
print('   log:'); print('\n'.join('     ' + l for l in git('log', '--format=%h %ad %s', '--date=iso').split('\n')))
print('   recorded git-history-final.txt:'); print('\n'.join('     ' + l for l in open(new + '/docs/corrections_rd/git-history-final.txt').read().strip().split('\n')[:12]))
print('   reflog entries:', len(git('reflog').split('\n')), '| last:', git('reflog', '-1'))
print('   tracked files modified:', git('status', '--short', '--untracked-files=no').replace('\n', ' ; '))
print('   stash:', git('stash', 'list') or 'none', '| tags:', git('tag') or 'none')
