import json,hashlib,os,sys,zipfile
root,proj=sys.argv[1],sys.argv[2]
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
m=json.load(open(os.path.join(root,'REVIEW_MANIFEST.json')))
files=m['files']
actual=[]
for d,_,fs in os.walk(root):
    for f in fs:
        actual.append(os.path.relpath(os.path.join(d,f),root))
actual=set(actual)-{'REVIEW_MANIFEST.json'}
print('manifest entries',len(files),'actual files (excl manifest)',len(actual))
print('missing from disk',sorted(set(files)-actual))
print('not in manifest',sorted(actual-set(files)))
bad=[k for k,v in files.items() if k in actual and sha(os.path.join(root,k))!=(v if isinstance(v,str) else v.get('sha256'))]
print('hash mismatches',bad)
# unsafe paths
z=zipfile.ZipFile(os.path.join(proj,'exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_V2_REVIEW_BUNDLE.zip'))
print('unsafe zip names',[n for n in z.namelist() if n.startswith('/') or '..' in n.split('/')])
# preservation hashes
for name,exp in [('exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_BUNDLE.zip','b154db10b8cee32066f089f0f878e7d2d3a3f33ca44e7831318f66faccaf61ea'),('exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_RESPONSE.zip','d38e0e27b30e46d2e4690b5366aa3fa237d5733e23783c64082c39ca4ff30f84'),('exports/FABLE_RB_AND_REQUIREMENTS_CORRECTIONS_REVIEW_BUNDLE.zip','2b47c3f47d5a20461e5a78f67317c1707269d0b4d85998a3ddb795292f26014d')]:
    for base in (root,proj):
        p=os.path.join(base,name)
        if os.path.exists(p): print(name,'in',('bundle' if base==root else 'project'),'MATCH' if sha(p)==exp else 'MISMATCH '+sha(p))
        else: print(name,'in',('bundle' if base==root else 'project'),'ABSENT')
# originals vs returned response zip
rz=os.path.join(proj,'exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_RESPONSE.zip')
z=zipfile.ZipFile(rz)
names=[n for n in z.namelist() if not n.endswith('/')]
print('response zip files',len(names))
res={'same':0,'diff':[],'absent':[]}
for n in names:
    data=z.read(n); h=hashlib.sha256(data).hexdigest()
    # locate in bundle
    cands=[n, 'exports/'+n]
    hit=None
    for c in cands:
        if os.path.exists(os.path.join(root,c)): hit=c;break
    if not hit: res['absent'].append(n); continue
    if sha(os.path.join(root,hit))==h: res['same']+=1
    else: res['diff'].append(n)
print('originals vs response zip:',res)
ic=json.load(open(os.path.join(root,'docs/corrections_rb/input-checksums.json')))
print('input-checksums keys',list(ic.keys())[:10] if isinstance(ic,dict) else type(ic))
