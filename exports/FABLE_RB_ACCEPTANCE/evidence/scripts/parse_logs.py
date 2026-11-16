"""Parse my own gate logs into structured results (used to build FABLE_RB_ACCEPTANCE_RESULTS.json)."""
import re,json,sys,os
E=sys.argv[1]
def read(n): return open(os.path.join(E,n)).read()
out={}
# 60 validation cases
cases=re.findall(r'(?m)^(PASS|FIXED|DEFERRED-OK|FAIL\S*|UNEXPECTED\S*|ERROR\S*)[ \t]+(FV-\S+)[ \t]*(.*)$',read('make-batch2-gate.stdout.txt'))
out['validation_cases']=[{'id':c[1],'result':c[0],'detail':c[2].strip()} for c in cases]
def summaries(name):
    t=read(name); blocks=[]
    for part in re.split(r'(?m)^={50,}\s*$',t)[1:]:
        rows=re.findall(r'(?m)^([A-Z][A-Za-z0-9]{1,6})[ \t]+(\S+)[ \t]+(OK|WEAK|NOTE|ERROR)[ \t]+(.*)$',part)
        if not rows: continue
        gate=re.search(r'(?m)^(.*gate: (?:PASS|FAIL).*)$',part); counts=re.search(r'(?m)^Verdict counts: (.*)$',part)
        blocks.append({'rows':[{'id':r[0],'ticket':r[1],'verdict':r[2],'title':r[3][:160]} for r in rows],'gate_line':gate.group(1).strip() if gate else None,'counts_line':counts.group(1) if counts else None})
    return blocks
for n in ('ra-probes-direct','make-rb-gate','make-acceptance-gate','make-reverification-gate','original-full-acceptance','original-full-reverification'):
    out[n]=summaries(n+'.stdout.txt')
json.dump(out,open(os.path.join(E,'parsed-gate-results.json'),'w'),indent=1)
from collections import Counter
print('cases',Counter(c['result'] for c in out['validation_cases']),len(out['validation_cases']))
for n,b in out.items():
    if n=='validation_cases': continue
    for i,blk in enumerate(b):
        c=Counter(r['verdict'] for r in blk['rows'])
        print(n,'block',i,dict(c),'| not OK:',[(r['id'],r['verdict']) for r in blk['rows'] if r['verdict']!='OK'],'|',blk['gate_line'])
