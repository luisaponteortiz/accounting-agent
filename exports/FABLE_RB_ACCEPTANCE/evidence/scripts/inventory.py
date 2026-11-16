"""Independent change inventory: frozen combined baseline (nested RA source overlaid with the
documentation addendum, plus reference material) versus the current bundle; compared with
docs/corrections_rb/changed-files.json. Also test-method retention by AST."""
import ast,hashlib,json,os,sys
cur,ra,addendum,combined,response_zip=sys.argv[1:6]
def sha(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()
def tree(root):
    out={}
    for d,_,fs in os.walk(root):
        for f in fs:
            p=os.path.join(d,f); out[os.path.relpath(p,root)]=sha(p)
    return out
base=tree(ra); base.update(tree(addendum))          # addendum overlays the RA source
base.update(tree(os.path.join(combined,'reference_material')))   # reference package sits at the project root
for f in ('START_HERE.md','FABLE_PRODUCT_AND_RA_REVIEW_PROMPT.md'):
    base[f]=sha(os.path.join(combined,f))
base.pop('REVIEW_MANIFEST.json',None)
import zipfile
rz=zipfile.ZipFile(response_zip)
returned={('exports/'+n if not n.startswith('exports/') else n):hashlib.sha256(rz.read(n)).hexdigest() for n in rz.namelist() if not n.endswith('/')}
now=tree(cur); now.pop('REVIEW_MANIFEST.json',None)
added=sorted(set(now)-set(base)); removed=sorted(set(base)-set(now)); modified=sorted(k for k in set(now)&set(base) if now[k]!=base[k])
print('baseline files',len(base),'| current files',len(now),'| added',len(added),'| removed',len(removed),'| modified',len(modified),'| unchanged',len(set(now)&set(base))-len(modified))
inv=json.load(open(os.path.join(cur,'docs/corrections_rb/changed-files.json')))
listed={c['path']:c for c in inv['changes']}
excluded=set(inv['excluded_generated_files'])
mine=set(added)|set(modified)|set(removed)
ret_ok=sorted(k for k in returned if now.get(k)==returned[k]); ret_bad=sorted(k for k in returned if now.get(k)!=returned[k])
print('returned review files present and byte-identical:',len(ret_ok),'| differing or absent:',ret_bad)
mine-=set(ret_ok)
print('removed relative to baseline:',removed)
print('in my diff, not in inventory and not excluded:',sorted(mine-set(listed)-excluded))
print('in inventory, not in my diff:',sorted(set(listed)-mine))
bad=[p for p,c in listed.items() if (c.get('after_sha256') and now.get(p)!=c['after_sha256']) or (c.get('before_sha256') and base.get(p)!=c['before_sha256'])]
print('inventory hash disagreements:',bad)
code=[p for p in sorted(mine) if p.startswith(('accounting_agent/','tests/','scripts/','review/','Makefile')) or p=='Makefile']
print('source/test/script/review changes (mine):',code)
print('source_or_test_changes (inventory):',inv['source_or_test_changes'])
print('fixtures/config/reference changed:',[p for p in sorted(mine) if p.startswith(('accounting_agent/config','accounting_agent/fixtures','ss_agent_system_handoff/','review/'))])
print('independent inputs changed (exports/FABLE_*):',[p for p in sorted(mine) if p.startswith('exports/FABLE_') and p in base])
def methods(root):
    out={}
    tdir=os.path.join(root,'tests')
    for f in sorted(os.listdir(tdir)):
        if not f.startswith('test_') or not f.endswith('.py'): continue
        t=ast.parse(open(os.path.join(tdir,f)).read())
        for n in t.body:
            if isinstance(n,ast.ClassDef):
                for m in n.body:
                    if isinstance(m,ast.FunctionDef) and m.name.startswith('test'):
                        out[(f,n.name,m.name)]=[d.attr if isinstance(d,ast.Attribute) else getattr(d,'id',getattr(getattr(d,'func',None),'attr',None)) for d in m.decorator_list]
    return out
b,c=methods(ra),methods(cur)
print('test methods baseline',len(b),'| current',len(c),'| removed',sorted(set(b)-set(c)),'| new',len(set(c)-set(b)))
byfile={}
for k in set(c)-set(b): byfile[k[0]]=byfile.get(k[0],0)+1
print('new methods by file:',byfile)
orig=[f for f in sorted(os.listdir(os.path.join(ra,'tests'))) if f.endswith('.py')]
print('original test files',len(orig),'| byte-identical now',sum(1 for f in orig if base['tests/'+f]==now.get('tests/'+f)),'| differing',[f for f in orig if base['tests/'+f]!=now.get('tests/'+f)])
print('skip/expectedFailure decorators in current tests:',{k:v for k,v in c.items() if any(d and ('skip' in d or 'expectedFailure' in d) for d in v)})
import re
txt=''.join(open(os.path.join(cur,'tests',f)).read() for f in os.listdir(os.path.join(cur,'tests')) if f.endswith('.py'))
print('skipTest/SkipTest/expectedFailure textual occurrences:',len(re.findall(r'skipTest|SkipTest|expectedFailure|unittest\.skip',txt)))
