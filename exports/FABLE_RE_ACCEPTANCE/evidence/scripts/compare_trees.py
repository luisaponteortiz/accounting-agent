import hashlib,os,sys,json
a,b=sys.argv[1],sys.argv[2]
def tree(r):
    out={}
    for dp,dn,fn in os.walk(r):
        for f in fn:
            p=os.path.join(dp,f); out[os.path.relpath(p,r)]=hashlib.sha256(open(p,'rb').read()).hexdigest()
    return out
A,B=tree(a),tree(b)
added=sorted(set(B)-set(A)); removed=sorted(set(A)-set(B)); changed=sorted(k for k in set(A)&set(B) if A[k]!=B[k])
print('base files',len(A),'new files',len(B),'added',len(added),'removed',len(removed),'changed',len(changed))
print('REMOVED:',removed)
print('CHANGED:'); [print('  ',c) for c in changed]
na=[x for x in added if not x.startswith('docs/corrections_re/')]
print('ADDED outside docs/corrections_re:'); [print('  ',c) for c in na]
json.dump({'added':added,'removed':removed,'changed':changed},open(sys.argv[3],'w'),indent=1)
