"""Fable RE review: test inventory, Y05 confinement, skip scan, archive hashes. Read-only."""
import ast,hashlib,json,os,re,sys,difflib
from pathlib import Path
base,new,work=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])
def methods(root):
    out={}
    for f in sorted((root/'tests').glob('test_*.py')):
        src=f.read_text(); tree=ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node,ast.ClassDef):
                for item in node.body:
                    if isinstance(item,(ast.FunctionDef,)) and item.name.startswith('test'):
                        out[(f.name,node.name,item.name)]=ast.get_source_segment(src,item)
    return out
B,N=methods(base),methods(new)
print('baseline test methods',len(B),'| current test methods',len(N))
print('missing from current:',[k for k in B if k not in N])
changed=[k for k in B if k in N and B[k]!=N[k]]
print('baseline methods whose body changed:',changed)
added=[k for k in N if k not in B]
from collections import Counter
print('added methods by file:',dict(Counter(k[0] for k in added)))
# earlier test files: only appended?
for f in sorted((base/'tests').glob('*')):
    if f.is_file():
        a=f.read_bytes(); b=(new/'tests'/f.name).read_bytes()
        if a!=b:
            print('changed earlier test file:',f.name,'| pure append:',b.startswith(a) or b.startswith(a.rstrip(b'\n')))
# skips / expected failures
hits=[]
for f in sorted((new/'tests').glob('*.py')):
    for i,line in enumerate(f.read_text().splitlines(),1):
        if re.search(r'skip|expectedFailure|SkipTest',line):hits.append((f.name,i,line.strip()[:120]))
print('skip/expectedFailure mentions in tests:',hits)
# Y05 adaptation confinement
orig=(new/'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py').read_text().splitlines()
adap=(new/'review/fable_rd_feed_contract_probes.py').read_text().splitlines()
sm=difflib.SequenceMatcher(None,orig,adap,autojunk=False)
ops=[o for o in sm.get_opcodes() if o[0]!='equal']
print('Y05 adaptation: differing hunks',len(ops))
y05=[i for i,l in enumerate(orig) if "@probe('Y05'" in l][0]; nxt=[i for i,l in enumerate(orig) if l.startswith('@probe(') and i>y05][0]
for o in ops:
    print('  ',o[0],'orig lines',o[1]+1,'-',o[2],'| adapted lines',o[3]+1,'-',o[4],'| inside Y05 (orig lines %d-%d): %s'%(y05+1,nxt,y05<=o[1] and o[2]<=nxt))
    for l in orig[o[1]:o[2]]: print('     -',l[:230])
    for l in adap[o[3]:o[4]]: print('     +',l[:230])
# the immutable originals equal the working project's copies
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bad=[]
n=0
for dp,dn,fn in os.walk(work/'exports/FABLE_RD_ACCEPTANCE'):
    for f in fn:
        if f=='.DS_Store':continue
        p=Path(dp)/f; rel=p.relative_to(work); n+=1
        if not (new/rel).is_file() or sha(p)!=sha(new/rel):bad.append(str(rel))
print('FABLE_RD_ACCEPTANCE files in working project',n,'| differing or missing in bundle:',bad)
# archive integrity
ai=json.loads((new/'docs/corrections_re/archive-integrity.json').read_text())
print('archive-integrity keys:',list(ai.keys())[:8] if isinstance(ai,dict) else type(ai))
rows=ai.get('archives',ai) if isinstance(ai,dict) else ai
items=rows.items() if isinstance(rows,dict) else [(r.get('path') or r.get('name'),r.get('sha256')) for r in rows]
cnt=0;bad=[]
for name,h in items:
    if isinstance(h,dict):h=h.get('sha256')
    if not isinstance(h,str) or not re.fullmatch(r'[a-f0-9]{64}',h):continue
    cnt+=1
    for root,label in ((new,'bundle'),(work,'working')):
        p=root/name if (root/name).is_file() else root/'exports'/name
        if not p.is_file():bad.append((label,name,'missing'))
        elif sha(p)!=h:bad.append((label,name,'hash differs'))
print('prior archives listed',cnt,'| problems:',bad)
