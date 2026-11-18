"""Fable RF review: retained tests, protected files, register records, decision log, archives, reviewer folder, git. Read-only."""
import ast,hashlib,json,os,re,subprocess,sys,zipfile,difflib
from pathlib import Path
from collections import Counter
base,new,work=Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def methods(root):
    out={}
    for f in sorted((root/'tests').glob('test_*.py')):
        src=f.read_text(); tree=ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node,ast.ClassDef):
                for item in node.body:
                    if isinstance(item,ast.FunctionDef) and item.name.startswith('test'):
                        out[(f.name,node.name,item.name)]=ast.get_source_segment(src,item)
    return out
B,N=methods(base),methods(new)
print('RE checkpoint test methods',len(B),'| RF test methods',len(N))
print('missing from RF:',[k for k in B if k not in N])
changed=[k for k in B if k in N and B[k]!=N[k]]
print('retained methods whose text changed:',changed)
added=[k for k in N if k not in B]
print('added methods by file:',dict(Counter(k[0] for k in added)),'| total added',len(added))
for f in sorted((base/'tests').glob('*')):
    if f.is_file():
        a=f.read_bytes(); b=(new/'tests'/f.name).read_bytes()
        if a!=b:
            sm=difflib.SequenceMatcher(None,a.decode().splitlines(),b.decode().splitlines(),autojunk=False)
            ops=[o for o in sm.get_opcodes() if o[0]!='equal']
            print('changed earlier test file:',f.name,'| hunks:',[(o[0],o[1]+1,o[2],o[3]+1,o[4]) for o in ops])
# other setUp/helper code (non-test functions, module level) unchanged in earlier test files?
def nontest(root,name):
    src=(root/'tests'/name).read_text();tree=ast.parse(src);segs=[]
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            for item in node.body:
                if not(isinstance(item,ast.FunctionDef) and item.name.startswith('test')):segs.append(ast.get_source_segment(src,item))
        else:segs.append(ast.get_source_segment(src,node))
    return segs
diffs=[f.name for f in sorted((base/'tests').glob('test_*.py')) if nontest(base,f.name)!=nontest(new,f.name)]
print('earlier test files whose non-test code (imports, fixtures, setUp, helpers) changed:',diffs)
hits=[]
for f in sorted((new/'tests').glob('*.py')):
    for i,line in enumerate(f.read_text().splitlines(),1):
        if re.search(r'skip|expectedFailure|SkipTest',line):hits.append((f.name,i,line.strip()[:120]))
print('skip/expectedFailure mentions in RF tests:',hits)
# D-031 texts in the report equal the actual texts
k=('test_product_requirements.py','ProductRequirements','test_PRV14_third_authority_is_pinned_and_latest_verdict_controls')
rep=(new/'docs/corrections_rf/RF_CORRECTIONS_REPORT.md').read_text()
import textwrap
blocks=re.findall(r'```python\n(.*?)```',rep,re.S)
norm=lambda t:[l.strip() for l in t.strip().splitlines()]
print('report "before" equals RE method:',norm(blocks[0])==norm(B[k]),'| report "after" equals RF method:',norm(blocks[1])==norm(N[k]))
dd=re.findall(r'```diff\n(.*?)```',rep,re.S)[0]
real=list(difflib.unified_diff((base/'tests/test_product_requirements.py').read_text().splitlines(),(new/'tests/test_product_requirements.py').read_text().splitlines(),lineterm='',n=3))
print('report diff body equals my diff of the two files:',[l.rstrip() for l in dd.strip().splitlines()[2:]]==[l.rstrip() for l in real[2:]])
for name in ('authorized-method-before.py','authorized-method-after.py'):
    t=(new/'docs/corrections_rf'/name).read_text()
    print(name,'equals', 'RE method' if norm(t)==norm(B[k]) else 'RF method' if norm(t)==norm(N[k]) else 'NEITHER')
# byte-identical protected files
for rel in ('tests/test_http.py','tests/schema_v1.sql','accounting_agent/storage.py','accounting_agent/http.py','review/fable_rd_feed_contract_probes.py','accounting_agent/source_control.py','accounting_agent/exceptions.py','accounting_agent/controls.py','accounting_agent/modules.py','accounting_agent/core.py','CODEX_RE_CORRECTIONS_PROMPT.md'):
    print('%-48s RE==RF: %s'%(rel,sha(base/rel)==sha(new/rel)))
print('deadline line in tests/test_http.py:',[l.strip() for l in (new/'tests/test_http.py').read_text().splitlines() if 'monotonic' in l or 'deadline' in l][:4])
# decisions log
a=(base/'DECISIONS.md').read_bytes();b=(new/'DECISIONS.md').read_bytes()
print('DECISIONS.md: RE text is an unchanged prefix:',b.startswith(a),'| RE sha',sha(base/'DECISIONS.md')[:12],'| appended bytes',len(b)-len(a))
tail=b[len(a):].decode()
print('appended headings:',re.findall(r'^#+ .*$',tail,re.M))
for d in ('D-016','D-017','D-026','D-029','D-030','D-031','D-032'):
    print(d,'entries opened in RE text:',len(re.findall(r'(?m)^(?:#+ |- \*\*)'+d+r'\b',a.decode())),'| in RF text:',len(re.findall(r'(?m)^(?:#+ |- \*\*)'+d+r'\b',b.decode())))
# register records
def records(root):
    t=(root/'docs/PRODUCT_REQUIREMENTS.md').read_text()
    parts=re.split(r'(?m)^(?=#+ AAOS-[A-Z]+-\d{2}\b)',t)
    out={};rest=[parts[0]]
    for part in parts[1:]:
        rid=re.match(r'#+ (AAOS-[A-Z]+-\d{2})',part).group(1)
        m=re.search(r'(?m)^#{1,2} (?!AAOS-)',part[5:])
        if m:rest.append(part[5+m.start():]);part=part[:5+m.start()]
        out[rid]=part
    return out,'\n'.join(rest)
RB_,restB=records(base);RN_,restN=records(new)
print('register records: RE',len(RB_),'RF',len(RN_),'| same ids in same order:',list(RB_)==list(RN_))
ch=[r for r in RB_ if RB_[r]!=RN_.get(r)]
print('records whose text changed:',ch)
def field(text,name):
    m=re.search(r'(?mi)^[-*| ]*\**'+re.escape(name)+r'\**\s*[:|]\s*(.*)$',text)
    return m.group(1).strip() if m else None
for r in ch:
    for name in ('Implementation state','Product decision'):
        print('  ',r,name,'| RE:',field(RB_[r],name),'| RF:',field(RN_[r],name))
    for name in ('Acceptance criteria',):
        sa=RB_[r];sb=RN_[r]
        ia=sa.find('Acceptance criteria');ib=sb.find('Acceptance criteria')
        print('  ',r,'has Acceptance criteria field:',ia>=0)
    sm=difflib.unified_diff(RB_[r].splitlines(),RN_[r].splitlines(),lineterm='',n=0)
    for line in list(sm)[2:]:
        if line.startswith(('+','-')):print('     ',line[:400])
print('text outside the 88 records (evidence section, crosswalk, change log) changed:',restB!=restN)
for line in list(difflib.unified_diff(restB.splitlines(),restN.splitlines(),lineterm='',n=0))[2:]:
    if line.startswith(('+','-')):print('     ',line[:330])
print('states:',dict(Counter(field(RN_[r],'Implementation state') for r in RN_)))
for r in ('AAOS-BB-01','AAOS-BB-02','AAOS-ONB-01','AAOS-ONB-02','AAOS-INT-07','AAOS-GL-06','AAOS-BNK-07','AAOS-RPT-03','AAOS-KNO-04','AAOS-CTL-01','AAOS-BNK-02','AAOS-CTL-09'):
    print('  ',r,'byte-identical:',RB_[r]==RN_[r],'| product decision:',field(RN_[r],'Product decision'),'| state:',field(RN_[r],'Implementation state'))
print('working register sha',sha(work/'docs/PRODUCT_REQUIREMENTS.md'),'== bundle:',sha(work/'docs/PRODUCT_REQUIREMENTS.md')==sha(new/'docs/PRODUCT_REQUIREMENTS.md'))
# archives
ai=json.loads((new/'docs/corrections_re/archive-integrity.json').read_text())
rows=ai.get('archives',ai) if isinstance(ai,dict) else ai
items=rows.items() if isinstance(rows,dict) else [(r.get('file') or r.get('path') or r.get('name'),r.get('sha256')) for r in rows]
cnt=0;bad=[]
for name,hh in items:
    if isinstance(hh,dict):hh=hh.get('sha256')
    if not isinstance(hh,str) or not re.fullmatch(r'[a-f0-9]{64}',hh):continue
    cnt+=1
    for root,label in ((new,'bundle'),(work,'working')):
        pth=root/name if (root/name).is_file() else root/'exports'/name
        if not pth.is_file():bad.append((label,name,'missing'))
        elif sha(pth)!=hh:bad.append((label,name,'hash differs'))
print('prior archives listed in archive-integrity.json',cnt,'| problems:',bad)
print('archive-integrity.json RE==RF:',sha(base/'docs/corrections_re/archive-integrity.json')==sha(new/'docs/corrections_re/archive-integrity.json'))
for name,want in (('exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip','4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae'),('exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip','e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a')):
    print(name,'| bundle copy ok:',sha(new/name)==want,'| working copy ok:',sha(work/name)==want)
# sidecars and manifests of earlier archives: every exports/* file that existed in the RE bundle is unchanged
same=sum(1 for dp,dn,fn in os.walk(base/'exports') for f in fn if sha(Path(dp)/f)==sha(new/Path(dp).relative_to(base)/f));tot=sum(len(fn) for _,_,fn in os.walk(base/'exports'))
print('exports/ files of the RE bundle unchanged in the RF bundle:',same,'of',tot)
# reviewer folder: working == bundle == response zip
n=0;bad=[]
for dp,dn,fn in os.walk(work/'exports/FABLE_RE_ACCEPTANCE'):
    for f in fn:
        if f=='.DS_Store':continue
        pth=Path(dp)/f;rel=pth.relative_to(work);n+=1
        if not (new/rel).is_file() or sha(pth)!=sha(new/rel):bad.append(str(rel))
print('FABLE_RE_ACCEPTANCE files in working project',n,'| differing or missing in bundle:',bad)
z=zipfile.ZipFile(work/'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip');zb=[]
names=[i for i in z.infolist() if not i.is_dir()]
for i in names:
    cands=[new/i.filename,new/'exports'/i.filename,new/'exports/FABLE_RE_ACCEPTANCE'/i.filename]
    hit=[c for c in cands if c.is_file()]
    if not hit or hashlib.sha256(z.read(i)).hexdigest()!=sha(hit[0]):zb.append(i.filename)
print('response ZIP entries',len(names),'| not byte-identical in bundle:',zb[:5])
# all protected inputs as the developer lists them
for cand in ('docs/corrections_rf/protected-inputs.json','docs/corrections_rf/preservation.json'):
    print(cand,'exists:',(new/cand).is_file())
# git
def git(*a):return subprocess.run(['git','-C',str(work)]+list(a),capture_output=True,text=True).stdout.strip()
print('git branch:',git('branch','--show-current'),'| HEAD:',git('rev-parse','HEAD'),'| commits:',git('rev-list','--count','HEAD'))
print('git log:');print(git('log','--format=%H %s'))
print('tracked files modified in working tree:',git('diff','--name-only','HEAD').split())
print('staged:',git('diff','--cached','--name-only').split())
print('reflog entries since 2026-11-16 17:00:',git('reflog','--since=2026-11-16 17:00','--format=%h %gs'))
