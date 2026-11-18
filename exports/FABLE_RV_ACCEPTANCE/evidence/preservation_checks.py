"""Read-only preservation and adapter checks for the RV correction bundle."""
import ast, hashlib, io, json, os, sys, zipfile
root, my22, prev_outer, prev_extract = sys.argv[1:5]
sha = lambda b: hashlib.sha256(b).hexdigest()
rd = lambda *p: open(os.path.join(*p), 'rb').read()

print('1. the 22 supplied re-verification files')
same = diff = 0
for d, _, fs in os.walk(my22):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), my22)
        tgt = os.path.join(root, 'exports/FABLE_REVERIFICATION', rel)
        if os.path.exists(tgt) and sha(rd(tgt)) == sha(rd(my22, rel)): same += 1
        else: diff += 1; print('   DIFFERENT OR MISSING:', rel)
extra = [os.path.relpath(os.path.join(d, f), os.path.join(root, 'exports/FABLE_REVERIFICATION')) for d, _, fs in os.walk(os.path.join(root, 'exports/FABLE_REVERIFICATION')) for f in fs]
print('   identical to reviewer originals: %d | different or missing: %d | files in bundle folder: %d' % (same, diff, len(extra)))

print('2. nested archives')
print('   previous outer bundle nested == delivered previous bundle:', sha(rd(root, 'exports/FABLE_CORRECTIONS_AND_BATCH_2_REVIEW_BUNDLE.zip')) == sha(rd(prev_outer)))
for z in ('FABLE_BATCH_1_REVIEW_BUNDLE.zip', 'FABLE_CORRECTIVE_C01_C06_REVIEW_BUNDLE.zip'):
    print('   %s unchanged from the previous extraction: %s' % (z, sha(rd(root, 'exports', z)) == sha(rd(prev_extract, 'exports', z))))
for f in ('FABLE_BATCH_1_1_CORRECTIONS.json', 'FABLE_BATCH_1_VERIFICATION.md', 'batch1_probe_output.txt', 'batch1_verification_probes.py'):
    print('   Batch 1 verification input %s unchanged: %s' % (f, sha(rd(root, 'exports/FABLE_BATCH_1_VERIFICATION', f)) == sha(rd(prev_extract, 'exports/FABLE_BATCH_1_VERIFICATION', f))))
for f in ('FABLE_ARCHITECTURE_REVIEW.md', 'FABLE_IMPLEMENTATION_BACKLOG.json', 'original/reviewer_probes.py', 'original/run_fable_validation_cases.py'):
    print('   review/%s unchanged: %s' % (f, sha(rd(root, 'review', f)) == sha(rd(prev_extract, 'review', f))))
print('   review/FABLE_VALIDATION_CASES.json unchanged from the previous bundle:', sha(rd(root, 'review/FABLE_VALIDATION_CASES.json')) == sha(rd(prev_extract, 'review/FABLE_VALIDATION_CASES.json')))
chk = json.loads(rd(root, 'docs/reverification/input-checksums.json'))
bad = []
def walk(o, pre=''):
    if isinstance(o, dict):
        if 'sha256' in o and isinstance(o['sha256'], str):
            yield pre, o['sha256']
        for k, v in o.items():
            if isinstance(v, (dict, list)): yield from walk(v, (pre + '/' + k) if pre else k)
            elif isinstance(v, str) and len(v) == 64 and k != 'sha256': yield (pre + '/' + k) if pre else k, v
    elif isinstance(o, list):
        for v in o: yield from walk(v, pre)
n = 0
for name, h in walk(chk):
    cands = [name, name.split('/', 1)[-1], 'exports/FABLE_REVERIFICATION/' + name.split('/')[-1], 'exports/' + name.split('/')[-1], 'exports/FABLE_BATCH_1_VERIFICATION/' + name.split('/')[-1]]
    found = [c for c in cands if os.path.isfile(os.path.join(root, c))]
    n += 1
    if not any(sha(rd(root, c)) == h for c in found): bad.append(name)
print('   input-checksums.json entries: %d | not matching any current file: %s' % (n, bad[:8]))

print('3. adapter: original versus review/fable_reverification_probes.py, per probe')
def probes(path):
    tree = ast.parse(open(path).read()); out = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.decorator_list and getattr(node.decorator_list[0], 'func', None) is not None and getattr(node.decorator_list[0].func, 'id', '') == 'probe':
            pid = node.decorator_list[0].args[0].value
            rets = [ast.dump(n) for n in ast.walk(node) if isinstance(n, ast.Return)]
            oks = [ast.dump(n.value) for n in ast.walk(node) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ('ok', 'held_while_locked', 'follows', 'month', 'isolated', 'independent', 'hand', 'base', 'label_completes', 'excluded_ok', 'both', 'bad', 'held') for t in n.targets)]
            out[pid] = (ast.dump(node), rets, oks)
    helpers = {n.name: ast.dump(n) for n in tree.body if isinstance(n, ast.FunctionDef) and not n.decorator_list}
    top = [ast.dump(n) for n in tree.body if not isinstance(n, ast.FunctionDef)]
    return out, helpers, top
o, oh, ot = probes(os.path.join(root, 'exports/FABLE_REVERIFICATION/fable_reverification_probes.py'))
a, ah, at = probes(os.path.join(root, 'review/fable_reverification_probes.py'))
changed = sorted(k for k in o if o[k][0] != a.get(k, (None,))[0])
print('   probes: original %d, adapted %d | bodies changed: %s' % (len(o), len(a), changed))
print('   return statements identical in every probe:', all(o[k][1] == a[k][1] for k in o), '| verdict-condition assignments identical:', all(o[k][2] == a[k][2] for k in o))
print('   helper functions changed:', sorted(k for k in oh if oh[k] != ah.get(k)), '| added:', sorted(set(ah) - set(oh)), '| removed:', sorted(set(oh) - set(ah)))
print('   module-level statements changed:', sum(1 for x, y in zip(ot, at) if x != y), '| count', len(ot), len(at))
