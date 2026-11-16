"""Independent PRV-01..PRV-10 checks on docs/PRODUCT_REQUIREMENTS.md using my own parser (read-only).
usage: prv_checks.py <rc-bundle-dir> <pre-pass-register.md> <v2-bundle-dir>
"""
import json, os, re, sys
from collections import Counter

root, pre_path, v2 = sys.argv[1:4]
REF = r'AAOS-[A-Z]+-\d{2}'


def parse(text):
    recs = {}
    heads = list(re.finditer(r'^### (AAOS-[A-Z]+-\d{2}) — ([^\n]+)', text, re.M))
    for i, m in enumerate(heads):
        body = text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)].split('\n## ', 1)[0]
        fields = {}
        for fm in re.finditer(r'^- \*\*([^*:]+):\*\*\s*([^\n]*)', body, re.M):
            fields.setdefault(fm.group(1), []).append(fm.group(2).strip())
        recs[m.group(1)] = {'id': m.group(1), 'title': m.group(2), 'f': fields}
    return recs


text = open(os.path.join(root, 'docs/PRODUCT_REQUIREMENTS.md')).read()
R = parse(text)
f = lambda i, k: R[i]['f'][k][0]
print('records', len(R))
bad = [i for i, r in R.items() if any(len(v) != 1 for v in r['f'].values()) or len(r['f']) < 12]
print('records with a missing or repeated field:', bad)
for k in ('Product decision', 'Implementation state', 'Priority', 'Needed for'):
    print(k, dict(sorted(Counter(f(i, k) for i in R).items())))

print('\n== PRV-01 ==')
for i in ('AAOS-BNK-03', 'AAOS-CTL-04', 'AAOS-GOV-03'):
    s, e, c = f(i, 'Scope note'), f(i, 'Evidence'), f(i, 'Acceptance criteria')
    print(i, '| state:', f(i, 'Implementation state'),
          '| RC-01..03 in scope note:', all(t in s for t in ('RC-01', 'RC-02', 'RC-03')) or 'RC-01–RC-03' in s or 'RC-01 to RC-03' in s,
          '| in evidence:', all(t in e for t in ('RC-01', 'RC-02', 'RC-03')) or 'RC-01–RC-03' in e or 'RC-01 to RC-03' in e)
    print('   scope note:', s[:600]); print('   evidence  :', e[:600]); print('   criteria  :', c[:900])
for i in ('AAOS-KNO-04', 'AAOS-CTL-01', 'AAOS-BNK-02', 'AAOS-CTL-09'):
    s, e = f(i, 'Scope note'), f(i, 'Evidence')
    print(i, '| state:', f(i, 'Implementation state'), '| report cited:', 'FABLE_RB_ACCEPTANCE_REPORT.md' in e, '| bundle hash cited:', '00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d' in e,
          '| UC-10 in scope:', 'UC-10' in s, '| UC-11 in scope:', 'UC-11' in s)
    print('   scope note:', s[:500]); print('   evidence  :', e[:700])
want_probes = {'AAOS-KNO-04': 'R02a R02b N03a N03b N03c'.split(), 'AAOS-CTL-01': 'R02a R02b N03a N03b N04a'.split(),
               'AAOS-BNK-02': 'R04a R04b R04c N02b N04a'.split(), 'AAOS-CTL-09': 'R03a R03b R04a R04b R04c N02a N02b'.split()}
for i, ps in want_probes.items():
    print(i, 'probes named in evidence:', {p: bool(re.search(r'(?<![\w-])' + p + r'(?![\w-])', f(i, 'Evidence'))) for p in ps})
m = re.search(r'^## Current evidence[^\n]*\n(.*?)(?=^## )', text, re.M | re.S)
cur = m.group(1) if m else ''
print('Current evidence section found:', bool(m), '| names RC-01..03:', all(t in cur for t in ('RC-01', 'RC-02', 'RC-03')) or 'RC-01–RC-03' in cur or 'RC-01 to RC-03' in cur)
print('   ', cur.strip()[:1500])
for t in ('T-12', 'RA-01', 'RB-01'):
    rows = re.findall(r'^\| ' + t + r' \|[^\n]*', text, re.M)
    print('crosswalk', t, ':', [r[:500] for r in rows])

print('\n== PRV-05 / PRV-06 / PRV-08 dependencies ==')
COND = re.compile(r'^\s*\(?\s*(if ratified|for (real|later|hosted|live)|before G[12]|where applicable|when authorized)\b', re.I)
prop_uncond, state_uncond, punct = [], [], []
for i in R:
    dep = f(i, 'Dependencies')
    if re.search(r'\.\s*;', dep):
        punct.append(i)
    for clause in dep.split(';'):
        refs = list(re.finditer(REF, clause))
        for n, r_ in enumerate(refs):
            d = r_.group(0); tail = clause[r_.end():refs[n + 1].start() if n + 1 < len(refs) else len(clause)]
            cond = bool(COND.match(tail))
            if f(i, 'Product decision') == 'Approved' and f(d, 'Product decision') == 'Proposed':
                print('  Approved %s -> Proposed %s | tail=%r | conditional=%s' % (i, d, tail.strip()[:60], cond))
                if not cond:
                    prop_uncond.append((i, d))
            if f(i, 'Implementation state') in ('Implemented', 'Developer-tested', 'Independently verified', 'Verification failed') and f(d, 'Implementation state') in ('Deferred', 'Not started'):
                print('  %s (%s) -> %s (%s) | tail=%r | conditional=%s' % (i, f(i, 'Implementation state'), d, f(d, 'Implementation state'), tail.strip()[:60], cond))
                if not cond:
                    state_uncond.append((i, d, f(i, 'Implementation state')))
print('Approved -> Proposed without condition:', prop_uncond)
print('tested/failed -> Deferred/Not started without condition:', state_uncond)
print('Dependencies fields with ". ;" or ".;":', punct)
print('six unratified shared requirements:', {i: f(i, 'Product decision') for i in ('AAOS-ONB-01', 'AAOS-ONB-02', 'AAOS-INT-07', 'AAOS-GL-06', 'AAOS-BNK-07', 'AAOS-RPT-03')})
print('Proposed:', sorted(i for i in R if f(i, 'Product decision') == 'Proposed'))
print('GOV-01 state:', f('AAOS-GOV-01', 'Implementation state'), '| GOV-02 deps:', f('AAOS-GOV-02', 'Dependencies'), '| ARC-01 deps:', f('AAOS-ARC-01', 'Dependencies'))
inst = {'AAOS-BB-0%d' % n: 'AAOS-ONB-01' for n in range(1, 9)}
inst.update({'AAOS-INT-0%d' % n: 'AAOS-INT-07' for n in range(1, 6)})
missing = [(i, d) for i, d in inst.items() if d not in ' '.join(R[i]['f'][k][0] for k in R[i]['f'])]
print('instantiation references missing (BB-01..08 -> ONB-01, INT-01..05 -> INT-07):', missing)
print('BB-04 cites GL-06:', 'AAOS-GL-06' in str(R['AAOS-BB-04']['f']), '| BB-05 cites BNK-07:', 'AAOS-BNK-07' in str(R['AAOS-BB-05']['f']))
# graph: unknown, self, cycle
graph = {i: re.findall(REF, f(i, 'Dependencies')) for i in R}
print('unknown refs:', sorted({d for ds in graph.values() for d in ds} - set(R)), '| self refs:', [i for i, ds in graph.items() if i in ds])
state = {}
def visit(n, stack):
    if state.get(n) == 2: return None
    if state.get(n) == 1: return stack + [n]
    state[n] = 1
    for d in graph.get(n, []):
        c = visit(d, stack + [n])
        if c: return c
    state[n] = 2
print('cycle:', next((c for c in (visit(i, []) for i in R) if c), None))

print('\n== PRV-07 ==')
for i in sorted(k for k in R if k.startswith('AAOS-EXC-')):
    row = re.findall(r'^\| ' + i + r' \| ([^|]+) \|', text, re.M)
    print(i, '| decision:', f(i, 'Product decision'), '| table:', row, '| scope note starts:', f(i, 'Scope note')[:40])

print('\n== PRV-10 / PRV-04 client boundary ==')
tl = re.findall(r'^- \*\*Client-specific terms:\*\*\s*([^\n]+)', text, re.M)
print('Client-specific terms lines:', tl)
terms = [t.strip() for t in tl[0].split(';')] if tl else []
mine = ['Bird Bowl', 'bird_bowl', 'birdbowl', 'Theresa', 'Jeff', 'Expensify', 'Toast', 'QuickBooks', 'Restaurant365', 'R365', 'Ramp', 'Brex', 'Gusto', 'SS accounting']
hits = []
for i, r in R.items():
    if i.startswith('AAOS-BB-'):
        continue
    for k, v in list(r['f'].items()) + [('title', [r['title']])]:
        if k == 'Trace':
            continue
        for t in set(terms + mine):
            if re.search(r'(?<![A-Za-z0-9])' + re.escape(t) + r'(?![A-Za-z0-9])', v[0], re.I):
                hits.append((i, k, t))
print('client words found in shared records outside Trace:', hits)
print('words of my own list that are NOT in the register terms list:', [t for t in mine if t.lower() not in [x.lower() for x in terms]])
src_hits = []
for d, dirs, files in os.walk(os.path.join(root, 'accounting_agent')):
    rel = os.path.relpath(d, os.path.join(root, 'accounting_agent'))
    if rel.split(os.sep)[0] in ('config', 'fixtures') or '__pycache__' in rel:
        continue
    for fn in files:
        if rel == '.' and fn == 'demo.py':
            continue
        try:
            body = open(os.path.join(d, fn), encoding='utf-8').read()
        except Exception:
            continue
        for t in set(terms + mine):
            for mm in re.finditer(r'(?<![A-Za-z0-9])' + re.escape(t).replace(r'\ ', r'[\W_]*') + r'(?![A-Za-z0-9])', body, re.I):
                src_hits.append((os.path.join(rel, fn), t, body[max(0, mm.start() - 40):mm.end() + 40].replace('\n', ' ')))
print('client words in shared accounting_agent files (outside config, fixtures, demo.py):', len(src_hits))
for h_ in src_hits[:20]:
    print('   ', h_)

print('\n== PR-11 owner wording (D-016/D-017) ==')
P = parse(open(pre_path).read())
for i in ('AAOS-BB-01', 'AAOS-BB-02'):
    diff = [k for k in R[i]['f'] if R[i]['f'][k] != P[i]['f'].get(k)]
    print(i, '| title same:', R[i]['title'] == P[i]['title'], '| fields that differ from the pre-pass register:', diff)
    for k in diff:
        print('    pre :', P[i]['f'][k][0]); print('    now :', R[i]['f'][k][0])
changed = sorted(i for i in R if i in P and (R[i]['f'] != P[i]['f'] or R[i]['title'] != P[i]['title']))
print('records changed against the pre-pass register:', len(changed)); print('  ', changed)
print('records added/removed:', sorted(set(R) - set(P)), sorted(set(P) - set(R)))
states = [(i, P[i]['f']['Implementation state'][0], f(i, 'Implementation state')) for i in R if i in P and P[i]['f']['Implementation state'][0] != f(i, 'Implementation state')]
decs = [(i, P[i]['f']['Product decision'][0], f(i, 'Product decision')) for i in R if i in P and P[i]['f']['Product decision'][0] != f(i, 'Product decision')]
print('implementation state changes:', states); print('product decision changes:', decs)
json.dump({i: {k: v[0] for k, v in r['f'].items()} for i, r in R.items()}, open(os.path.join(os.path.dirname(root), 'evidence', 'register-parsed.json'), 'w'), indent=1)
