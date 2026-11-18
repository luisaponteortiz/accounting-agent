"""Fable RF review: developer's change inventory against my own tree comparison; patch reproduction; working project vs bundle. Read-only."""
import json,os,hashlib,subprocess,shutil,sys,tempfile
from collections import Counter
R='/private/tmp/claude-501/rf'; P="/Users/luis/Documents/ChatGPT/Accounting Agent OS"
RE,RF=R+'/re_x',R+'/rf_x'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
d=json.load(open(R+'/ev/diff-vs-re-archive.json'))
added=d['added']
other=[a for a in added if not a.startswith('docs/corrections_rf/') and not a.startswith('exports/FABLE_RE_ACCEPTANCE/')]
print('my comparison RE archive -> RF archive: added',len(added),'changed',len(d['changed']),'removed',len(d['removed']))
print('added under docs/corrections_rf',sum(a.startswith('docs/corrections_rf/') for a in added),'| under exports/FABLE_RE_ACCEPTANCE',sum(a.startswith('exports/FABLE_RE_ACCEPTANCE/') for a in added),'| elsewhere',len(other))
c=json.load(open(RF+'/docs/corrections_rf/changed-files.json'))
f=c['files']; inv={x['file']:x for x in f}
mine=set(d['added'])|set(d['changed'])|set(d['removed'])
print('inventory entries',len(inv),'| my differences',len(mine))
print('in my diff, not in inventory:',sorted(mine-set(inv)))
print('in inventory, not in my diff:',sorted(set(inv)-mine))
print('inventory statuses',dict(Counter(x['status'] for x in f)),'| pre_existing_difference',dict(Counter(x['pre_existing_difference'] for x in f)),'| changed_in_this_pass',dict(Counter(x['changed_in_this_pass'] for x in f)))
bad=[]
for p,x in inv.items():
    fp=os.path.join(RF,p)
    if x.get('sha256') and (not os.path.isfile(fp) or sha(fp)!=x['sha256']): bad.append((p,'sha256'))
    bp=os.path.join(RE,p)
    if x.get('baseline_sha256') and (not os.path.isfile(bp) or sha(bp)!=x['baseline_sha256']): bad.append((p,'baseline'))
    if x['status']=='added' and os.path.exists(bp): bad.append((p,'status'))
    if x['status']=='modified' and not os.path.exists(bp): bad.append((p,'status'))
print('inventory hash/status mismatches:',bad)
print('pre-existing differences listed:',[p for p,x in inv.items() if x['pre_existing_difference']][:40])
# patch reproduction: apply to a copy of the RE code/test/gate files and compare with RF
tmp=tempfile.mkdtemp(prefix='rfpatch-',dir=R)
code=[]
for top in ('accounting_agent','tests','scripts','review','Makefile'):
    src=os.path.join(RE,top)
    if os.path.isdir(src): shutil.copytree(src,os.path.join(tmp,top))
    elif os.path.isfile(src): shutil.copy(src,os.path.join(tmp,top))
patch=RF+'/docs/corrections_rf/source-and-tests.patch'
print('patch sha256',sha(patch),'bytes',os.path.getsize(patch))
r=subprocess.run(['patch','-p1','-s','-i',patch],cwd=tmp,capture_output=True,text=True)
print('patch exit',r.returncode,(r.stdout+r.stderr).strip()[:600])
diff=[];n=0
for top in ('accounting_agent','tests','scripts','review','Makefile'):
    base=os.path.join(RF,top)
    walk=[(os.path.dirname(base),[],[top])] if os.path.isfile(base) else os.walk(base)
    for dp,dn,fn in walk:
        for name in fn:
            if name.endswith('.pyc') or name=='.DS_Store': continue
            p=os.path.join(dp,name); rel=os.path.relpath(p,RF); n+=1
            q=os.path.join(tmp,rel)
            if not os.path.isfile(q): diff.append(('missing after patch',rel))
            elif sha(p)!=sha(q): diff.append(('differs',rel))
extra=[]
for top in ('accounting_agent','tests','scripts','review'):
    for dp,dn,fn in os.walk(os.path.join(tmp,top)):
        for name in fn:
            if name.endswith(('.orig','.rej')): extra.append(os.path.relpath(os.path.join(dp,name),tmp)); continue
            rel=os.path.relpath(os.path.join(dp,name),tmp)
            if not os.path.isfile(os.path.join(RF,rel)): extra.append(rel)
print('RF code/test/script/review/Makefile files',n,'| not reproduced by patch:',diff,'| extra after patch:',extra)
shutil.rmtree(tmp)
# working project vs bundle
exc=('.git/',)
miss=[];dif=[];n=0
m=json.load(open(RF+'/REVIEW_MANIFEST.json'))['files']
for rel in list(m)+['REVIEW_MANIFEST.json']:
    wp=os.path.join(P,rel)
    if rel=='REVIEW_MANIFEST.json': continue
    n+=1
    if not os.path.isfile(wp): miss.append(rel)
    elif sha(wp)!=(m[rel] if isinstance(m[rel],str) else m[rel]['sha256']): dif.append(rel)
print('bundle payload files compared with working project',n,'| missing in working project:',miss[:20],'| differing:',dif[:20])
