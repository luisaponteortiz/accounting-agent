"""Structural checks of docs/PRODUCT_REQUIREMENTS.md (read-only). usage: register_checks.py <register.md> <fable_backlog.json>"""
import collections, json, re, sys
text = open(sys.argv[1]).read()
blocks = re.split(r'(?m)^### ', text)[1:]
recs = {}
for b in blocks:
    m = re.match(r'(AAOS-[A-Z]+-\d+) — (.*)', b)
    if not m: continue
    rid = m.group(1); body = b.split('\n## ')[0]
    f = {'title': m.group(2)}
    for name in ('Description', 'Business purpose', 'Priority', 'Status', 'Dependencies', 'Acceptance criteria', 'Target stage', 'Trace'):
        mm = re.search(r'\*\*' + name + r':\*\*\s*(.*?)(?=\s*\*\*(?:Description|Business purpose|Priority|Status|Dependencies|Acceptance criteria|Target stage|Trace):\*\*|\n- \*\*|\n\n|\Z)', body, re.S)
        f[name] = mm.group(1).strip() if mm else None
    recs[rid] = f
print('records:', len(recs), '| duplicate ids:', [k for k, c in collections.Counter(re.findall(r'(?m)^### (AAOS-[A-Z]+-\d+)', text)).items() if c > 1])
missing = {r: [k for k, v in f.items() if not v] for r, f in recs.items()}
print('records with a missing field:', {r: m for r, m in missing.items() if m})
deps = {r: sorted(set(re.findall(r'AAOS-[A-Z]+-\d+', f['Dependencies'] or ''))) for r, f in recs.items()}
print('dependencies naming unknown ids:', {r: [d for d in ds if d not in recs] for r, ds in deps.items() if any(d not in recs for d in ds)})
print('self-dependencies:', [r for r, ds in deps.items() if r in ds])
# cycles
color = {}; cycles = []
def visit(n, path):
    color[n] = 1
    for d in deps.get(n, []):
        if d not in recs: continue
        if color.get(d) == 1: cycles.append(path[path.index(d):] + [d] if d in path else [n, d])
        elif color.get(d) is None: visit(d, path + [d])
    color[n] = 2
for r in recs:
    if color.get(r) is None: visit(r, [r])
print('dependency cycles:', cycles)
lead = lambda s: re.match(r'[A-Za-z /]+', s).group(0).strip().split(' ')[0]
status = {r: lead(f['Status']) for r, f in recs.items()}
print('leading status word:', dict(collections.Counter(status.values())))
print('priority:', dict(collections.Counter(lead(f['Priority']) for f in recs.values())), '| not Must:', [r for r, f in recs.items() if not f['Priority'].startswith('Must')])
print('compound statuses (a second status word appears):')
for r, f in recs.items():
    words = set(re.findall(r'\b(approved|implemented|tested|deferred|proposed)\b', f['Status'].lower()))
    if len(words) > 1: print('   ', r, sorted(words), '|', f['Status'][:110])
print('Tested records depending on Deferred/Approved-unbuilt records:')
for r, ds in deps.items():
    if status[r] == 'Tested':
        bad = [d + '(' + status[d] + ')' for d in ds if d in recs and status[d] in ('Deferred', 'Approved', 'Proposed')]
        if bad: print('   ', r, '->', bad)
stage = collections.Counter()
for f in recs.values():
    s = f['Target stage']
    stage['Current / G0' if s.startswith('Current') else 'Existing Batch 3' if s.startswith('Existing Batch 3') else 'Future / unassigned' if s.startswith('Future') else 'G1' if s.startswith('G1') else 'Before ...' if s.startswith('Before') else 'other'] += 1
print('target stage lead:', dict(stage))
print('client-specific names outside the BB section:')
for r, f in recs.items():
    if r.startswith('AAOS-BB'): continue
    for k in ('Description', 'Business purpose', 'Status', 'Dependencies', 'Acceptance criteria', 'Target stage'):
        hits = re.findall(r'Bird Bowl|Theresa|Jeff|Luis|Expensify|Render|Supporting Strategies|\bSS\b|Desktop', f[k] or '')
        if hits: print('   ', r, k, sorted(set(hits)))
# crosswalk
rows = dict(re.findall(r'(?m)^\| (T-\d\d) \| ([^|]+) \|', text))
print('crosswalk tickets:', len(rows), '| unknown ids in crosswalk:', {t: [i for i in re.findall(r'AAOS-[A-Z]+-\d+', v) if i not in recs] for t, v in rows.items() if any(i not in recs for i in re.findall(r'AAOS-[A-Z]+-\d+', v))})
cited = set(re.findall(r'AAOS-[A-Z]+-\d+', ' '.join(rows.values())))
print('requirements with no T-ticket in the crosswalk:', len(set(recs) - cited))
bl = json.load(open(sys.argv[2]))
def walk(o):
    if isinstance(o, dict):
        if isinstance(o.get('id'), str) and re.match(r'T-\d\d$', o['id']): yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)
tickets = {t['id']: t for t in walk(bl)}
print('tickets in Fable backlog:', len(tickets), '| missing from crosswalk:', sorted(set(tickets) - set(rows)), '| extra:', sorted(set(rows) - set(tickets)))
for tid in sorted(tickets):
    t = tickets[tid]
    print('   ', tid, '|', str(t.get('batch', t.get('phase', '')))[:8], '|', (t.get('title') or '')[:78], '| deps', t.get('depends_on', t.get('dependencies')), '| ->', rows.get(tid, '').strip())
json.dump({'records': recs, 'deps': deps, 'status_lead': status}, open('register_parsed.json', 'w'), indent=1)
