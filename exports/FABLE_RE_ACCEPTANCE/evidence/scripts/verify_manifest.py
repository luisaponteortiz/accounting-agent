import json,hashlib,os,sys
root=sys.argv[1]
m=json.load(open(os.path.join(root,'REVIEW_MANIFEST.json')))
print('label',m['label']); print('scope',m['scope']); print('hash_rule',m['hash_rule'])
files=m['files']
print(type(files), len(files))
items = files.items() if isinstance(files,dict) else [(f.get('path'),f) for f in files]
listed=set(); bad=[]
for p,v in items:
    listed.add(p)
    h = v if isinstance(v,str) else v.get('sha256')
    fp=os.path.join(root,p)
    if not os.path.isfile(fp): bad.append(('MISSING',p)); continue
    if hashlib.sha256(open(fp,'rb').read()).hexdigest()!=h: bad.append(('HASH',p))
actual=set()
for dp,dn,fn in os.walk(root):
    for f in fn:
        actual.add(os.path.relpath(os.path.join(dp,f),root))
extra=actual-listed-{'REVIEW_MANIFEST.json'}
print('listed',len(listed),'actual',len(actual),'bad',bad[:10],'extra',sorted(extra)[:10], 'unlisted_missing', sorted(listed-actual)[:5])
