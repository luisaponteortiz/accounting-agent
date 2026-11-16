import re, sys, json, difflib
def records(path):
    text = open(path).read()
    parts = re.split(r'(?m)^(?=### AAOS-[A-Z]+-\d{2} — )', text)
    out = {}
    for p in parts[1:]:
        m = re.match(r'### (AAOS-[A-Z]+-\d{2}) — ([^\n]+)\n', p)
        body = p[m.end():]
        body = re.split(r'(?m)^## ', body)[0]
        fields = {}
        for line in body.split('\n'):
            fm = re.match(r'- \*\*([^*]+?):?\*\*:?\s*(.*)', line) or re.match(r'\*\*([^*]+?):?\*\*:?\s*(.*)', line)
            if fm: fields[fm.group(1).strip()] = fm.group(2).strip()
        out[m.group(1)] = {'title': m.group(2), 'fields': fields, 'raw': p.split('\n## ')[0]}
    return text, out
bt, b = records(sys.argv[1]); nt, n = records(sys.argv[2])
print('records baseline', len(b), 'new', len(n), 'same ids/order', list(b) == list(n))
changed = [k for k in n if b.get(k, {}).get('raw') != n[k]['raw']]
print('changed records:', changed)
for k in changed:
    fb, fn = b[k]['fields'], n[k]['fields']
    print('\n==', k, '| fields parsed', len(fn), '| title same', b[k]['title'] == n[k]['title'])
    for f in fn:
        if fb.get(f) != fn[f]:
            print('  FIELD CHANGED:', f)
            print('    old:', (fb.get(f) or '')[:1500])
            print('    new:', fn[f][:1500])
    for f in fb:
        if f not in fn: print('  FIELD REMOVED:', f)
states = {}
for k, r in n.items():
    for f in ('Decision status', 'Verification status', 'Status'):
        if f in r['fields']: states.setdefault(f, {}).setdefault(r['fields'][f], []).append(k)
for f, d in states.items():
    print('\n', f, {s: len(v) for s, v in d.items()})
    for s, v in d.items():
        if len(v) < 12: print('   ', s, v)
print('\nsample field names:', list(n['AAOS-BNK-03']['fields']))
# non-record text diff
strip = lambda t, recs: re.sub(r'(?ms)^### AAOS-[A-Z]+-\d{2} — .*?(?=^### AAOS-|^## |\Z)', '', t)
bl, nl = strip(bt, b).split('\n'), strip(nt, n).split('\n')
print('\nNON-RECORD TEXT CHANGES:')
for l in difflib.unified_diff(bl, nl, lineterm='', n=0):
    if l.startswith(('+', '-')) and not l.startswith(('+++', '---')): print('  ', l[:1300])
