"""Independent structural checks on docs/PRODUCT_REQUIREMENTS.md, using my own parser.
Usage: python3 register_checks.py <project-root> <frozen-addendum-register.md>"""
import sys,re,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from register_parse import parse
from collections import Counter
root,orig_path=sys.argv[1],sys.argv[2]
os.chdir(root)
text=open('docs/PRODUCT_REQUIREMENTS.md').read()
recs=parse(text); by={r['id']:r for r in recs}
f=lambda i,k:by[i]['fields'][k][0]
REF=r'AAOS-[A-Z]+-\d{2}'
FIELDS=['Description','Business purpose','Priority','Product decision','Implementation state','Scope note','Evidence','Needed for','Dependencies','Acceptance criteria','Target stage','Trace']
print('records',len(recs),'| unique ids',len(by))
print('records without exactly the 12 fields once each:',[r['id'] for r in recs if sorted(r['fields'])!=sorted(FIELDS) or any(len(v)!=1 for v in r['fields'].values())])
for k in ('Product decision','Implementation state','Needed for','Priority'):
    print(k,dict(Counter(r['fields'][k][0] for r in recs)))
print('Verification failed:',[r['id'] for r in recs if f(r['id'],'Implementation state')=='Verification failed'])
print('Proposed:',[r['id'] for r in recs if f(r['id'],'Product decision')=='Proposed'])
print('Rejected:',[r['id'] for r in recs if f(r['id'],'Product decision')=='Rejected'])
print('INT-01..05 states:',[f('AAOS-INT-0%d'%n,'Implementation state') for n in range(1,6)])
orig=parse(open(orig_path).read())
print('original ids',len(orig),'| retained',len({r['id'] for r in orig}&set(by)),'| new',sorted(set(by)-{r['id'] for r in orig}))
print('titles changed for original ids:',[(r['id'],r['title'],by[r['id']]['title']) for r in orig if by[r['id']]['title']!=r['title']])
n=0
for r in recs:
    if f(r['id'],'Implementation state') in ('Developer-tested','Verification failed','Implemented','Independently verified'):
        n+=1
        paths=re.findall(r'tests/test_\w+\.py',f(r['id'],'Evidence'))
        missing=[p for p in set(paths) if not os.path.exists(p)]
        if not paths or missing: print('evidence problem',r['id'],'| test paths:',sorted(set(paths)),'| missing:',missing)
print('records in a tested or failed state, each citing at least one existing test file:',n)
st=lambda i:f(i,'Implementation state')
print('--- tested or failed records with a Deferred or Not started dependency')
for r in recs:
    if st(r['id']) in ('Developer-tested','Independently verified','Verification failed'):
        for clause in f(r['id'],'Dependencies').split(';'):
            for d in re.findall(REF,clause):
                if st(d) in ('Deferred','Not started'):
                    print('%-12s %-20s -> %-12s %-12s | clause: %s'%(r['id'],st(r['id']),d,st(d),clause.strip()[:70]))
print('--- Approved records that depend on Proposed records')
for r in recs:
    if f(r['id'],'Product decision')=='Approved':
        deps=[d for d in re.findall(REF,f(r['id'],'Dependencies')) if f(d,'Product decision')=='Proposed']
        if deps: print(r['id'],'->',deps)
mal=[r['id'] for r in recs if re.search(r'\.\s*;|;\s*$|\.;',f(r['id'],'Dependencies'))]
print('dependency fields with stray punctuation:',len(mal),mal)
rows=re.findall(r'^\| (T-\d{2}) \| ([^|]+)\|',text,re.M)
print('crosswalk tickets',len(rows),'| unique',len({k for k,_ in rows}),'| refs all exist:',all(set(re.findall(REF,v))<=set(by) for _,v in rows))
g={r['id']:re.findall(REF,f(r['id'],'Dependencies')) for r in recs}
print('unknown deps:',sorted({d for v in g.values() for d in v}-set(by)),'| self deps:',[k for k,v in g.items() if k in v])
state={}
def visit(n,stack):
    if state.get(n)==1: return [stack+[n]]
    if state.get(n)==2: return []
    state[n]=1; out=[]
    for d in g[n]: out+=visit(d,stack+[n])
    state[n]=2; return out
print('cycles:',[c for n in g for c in visit(n,[])])
print('EXE-02 deps:',g['AAOS-EXE-02'],'| EXE-03 deps:',g['AAOS-EXE-03'],'| BNK-02 deps:',g['AAOS-BNK-02'])
for at in ('AT-24','AT-25','AT-29','AT-40','AT-58','AT-59'):
    print(at,'in Trace of',[r['id'] for r in recs if at in f(r['id'],'Trace')])
print('--- first-client words in shared records (any field)')
for r in recs:
    if r['id'].startswith('AAOS-BB-'): continue
    for k,v in r['fields'].items():
        for m in re.finditer(r'bird[\W_]*bowl|expensify|desktop|theresa',v[0],re.I):
            print(r['id'],k,'...'+v[0][max(0,m.start()-50):m.end()+40]+'...')
