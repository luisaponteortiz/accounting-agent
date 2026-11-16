"""Independent fault injection against scripts/check_product_requirements.py and `make check`.
Each case mutates a copy of the register text (never the file in the bundle) and reports whether
the checker rejects it. 'want' is what a sound gate should do."""
import re,sys,subprocess,shutil,os,tempfile
from pathlib import Path
root=Path(sys.argv[1]).resolve(); sys.path.insert(0,str(root))
from scripts.check_product_requirements import validate_register
text=(root/'docs/PRODUCT_REQUIREMENTS.md').read_text()
def record(i):
    a=text.index('### '+i+' —'); b=text.find('\n### ',a+5); return a,(b if b>0 else len(text))
def field(i,name):
    a,b=record(i); m=re.search(r'^- \*\*'+re.escape(name)+r':\*\*\s*([^\n]*)',text[a:b],re.M); return a+m.start(1),a+m.end(1)
def setf(i,name,value,t=None):
    s,e=field(i,name); t=t or text; return t[:s]+value+t[e:]
cases=[]
def case(label,want,mutated):
    try: validate_register(mutated,root); got='ACCEPTED'; msg=''
    except Exception as exc: got='REJECTED'; msg=type(exc).__name__+': '+str(exc)[:110]
    cases.append((label,want,got,msg))
a,b=record('AAOS-OBS-02')
case('F01 baseline register unchanged','ACCEPTED',text)
case('F02 duplicate ID (GOV-02 renamed GOV-01)','REJECTED',text.replace('### AAOS-GOV-02 —','### AAOS-GOV-01 —',1))
case('F03 lost ID (record OBS-02 deleted, references kept)','REJECTED',text[:a]+text[b:])
case('F04 lost ID with every reference removed too','REJECTED',(text[:a]+text[b:]).replace('AAOS-OBS-02','AAOS-OBS-01'))
case('F05 missing field (Needed for)','REJECTED',text.replace('- **Needed for:**','- **Needed:**',1))
case('F06 repeated field (two Priority lines)','REJECTED',text.replace('- **Priority:** Must','- **Priority:** Must\n- **Priority:** Could',1))
case('F07 empty field value','REJECTED',setf('AAOS-ARC-01','Trace',''))
case('F08 unknown dependency','REJECTED',setf('AAOS-ARC-01','Dependencies','AAOS-NOPE-01'))
case('F09 self dependency','REJECTED',setf('AAOS-ARC-01','Dependencies','AAOS-ARC-01'))
case('F10 two-record cycle (GOV-01 -> GOV-02 -> GOV-01)','REJECTED',setf('AAOS-GOV-01','Dependencies','AAOS-GOV-02'))
case('F11 three-record cycle (GOV-01 -> GOV-03 -> GOV-02 -> GOV-01)','REJECTED',setf('AAOS-GOV-01','Dependencies','AAOS-GOV-03'))
case('F12 backlog ticket row removed (T-12)','REJECTED',re.sub(r'^\| T-12 \|.*\n','',text,flags=re.M))
case('F13 backlog ticket row duplicated (T-12)','REJECTED',re.sub(r'^(\| T-12 \|.*\n)',r'\1\1',text,flags=re.M))
case('F14 backlog ticket row with no requirement reference','REJECTED',re.sub(r'^\| T-12 \| [^|]+\|',lambda m:'| T-12 | none |',text,flags=re.M))
case('F15 unsupported state (Tested)','REJECTED',setf('AAOS-ARC-02','Implementation state','Tested'))
case('F16 mixed state','REJECTED',setf('AAOS-ARC-02','Implementation state','Developer-tested; Deferred'))
case('F17 mixed product decision','REJECTED',setf('AAOS-ARC-02','Product decision','Approved / Proposed'))
case('F18 invalid Needed for','REJECTED',setf('AAOS-ARC-02','Needed for','Soon'))
case('F19 invalid priority','REJECTED',setf('AAOS-ARC-02','Priority','Critical'))
case('F20 Developer-tested with evidence "Claims only"','REJECTED',setf('AAOS-ARC-02','Evidence','Claims only'))
case('F21 Developer-tested citing a test file that does not exist (no link)','REJECTED',setf('AAOS-ARC-02','Evidence','tests/test_does_not_exist.py'))
case('F22 Developer-tested whose only evidence is a ticket id (PR-04)','REJECTED',setf('AAOS-ARC-02','Evidence','See PR-04'))
case('F23 Developer-tested whose only evidence is an arbitrary R-token (R2D2)','REJECTED',setf('AAOS-ARC-02','Evidence','R2D2 says so'))
case('F24 Independently verified without review or checkpoint','REJECTED',setf('AAOS-ARC-02','Implementation state','Independently verified'))
def setf2(i,changes):
    t=text
    for name,value in changes:
        a,b=record(i); m=re.search(r'^- \*\*'+re.escape(name)+r':\*\*\s*([^\n]*)',t[a:b],re.M); t=t[:a+m.start(1)]+value+t[a+m.end(1):]
    return t
case('F25 Independently verified, self-asserted: the words "independent review", any 64-hex string and a test path','REJECTED',setf2('AAOS-ARC-02',[('Implementation state','Independently verified'),('Evidence','independent review '+'ab'*32+' tests/test_platform.py')]))
case('F26 a Verification failed record promoted to Developer-tested by the developer (BNK-03)','REJECTED',setf('AAOS-BNK-03','Implementation state','Developer-tested'))
case('F27 first-client name in a shared acceptance criterion','REJECTED',setf('AAOS-ARC-01','Acceptance criteria','Bird Bowl-only policy applies.'))
case('F28 first-client name in a shared Target stage','REJECTED',setf('AAOS-ARC-01','Target stage','After Bird Bowl G1 validation'))
case('F29 first-client vendor (Expensify) in a shared criterion','REJECTED',setf('AAOS-INT-05','Acceptance criteria','Use Expensify.'))
case('F30 first-client person (Theresa) in a shared criterion','REJECTED',setf('AAOS-ARC-01','Acceptance criteria','Theresa approves every shared release.'))
case('F31 first-client name in a shared Description','REJECTED',setf('AAOS-ARC-01','Description','Built for Bird Bowl restaurants.'))
case('F32 tested record with an unconditional Deferred dependency (GL-02 -> CTL-13)','REJECTED',setf('AAOS-GL-02','Dependencies','AAOS-CTL-13'))
case('F33 tested record with a conditional Deferred dependency','ACCEPTED',setf('AAOS-GL-02','Dependencies','AAOS-CTL-13 for real data only'))
case('F33b tested record with an unconditional Not started dependency (GL-02 -> KNO-01)','REJECTED',setf('AAOS-GL-02','Dependencies','AAOS-KNO-01'))
case('F33c the word only anywhere in the clause counts as a condition (GL-02 -> CTL-13)','REJECTED',setf('AAOS-GL-02','Dependencies','AAOS-CTL-13, the only prerequisite'))
case('F34 broken evidence link','REJECTED',setf('AAOS-ARC-02','Evidence','[tests](../tests/test_missing.py) tests/test_platform.py'))
case('F35 scope table says Rejected while the record says Approved (EXC-05)','REJECTED',text.replace('| AAOS-EXC-05 | Reserved |','| AAOS-EXC-05 | Rejected |',1))
w=max(len(c[0]) for c in cases)
gaps=0
for label,want,got,msg in cases:
    ok=want==got; gaps+=not ok
    print('%-*s want=%-8s got=%-8s %s %s'%(w,label,want,got,'ok ' if ok else 'GAP',msg))
print('cases',len(cases),'| agree',len(cases)-gaps,'| gaps',gaps)
# make check on mutated copies of the project (temporary directories only)
def make_check(label,mutate):
    d=Path(tempfile.mkdtemp(prefix='fable-rb-check-'))/'p'
    shutil.copytree(root,d,ignore=shutil.ignore_patterns('*.sqlite3'))
    mutate(d)
    r=subprocess.run(['make','check'],cwd=d,capture_output=True,text=True)
    last=(r.stdout+r.stderr).strip().splitlines()[-1][:150] if (r.stdout+r.stderr).strip() else ''
    print('make check | %-62s exit=%d | %s'%(label,r.returncode,last)); shutil.rmtree(d.parent)
reg=lambda d:d/'docs/PRODUCT_REQUIREMENTS.md'
make_check('unchanged copy',lambda d:None)
make_check('duplicate ID',lambda d:reg(d).write_text(text.replace('### AAOS-GOV-02 —','### AAOS-GOV-01 —',1)))
make_check('missing field',lambda d:reg(d).write_text(text.replace('- **Needed for:**','- **Needed:**',1)))
make_check('unknown dependency',lambda d:reg(d).write_text(setf('AAOS-ARC-01','Dependencies','AAOS-NOPE-01')))
make_check('dependency cycle',lambda d:reg(d).write_text(setf('AAOS-GOV-01','Dependencies','AAOS-GOV-02')))
make_check('backlog ticket missing from the crosswalk',lambda d:reg(d).write_text(re.sub(r'^\| T-12 \|.*\n','',text,flags=re.M)))
def add(path,s):
    return lambda d:(d/path).write_text((d/path).read_text()+s)
make_check('client name literal added to accounting_agent/service.py',add('accounting_agent/service.py','\nNOTE="Bird Bowl default"\n'))
make_check('client name as identifier bird_bowl in accounting_agent/core.py',add('accounting_agent/core.py','\nbird_bowl_default=1\n'))
make_check('client name added to accounting_agent/demo.py (exempt)',add('accounting_agent/demo.py','\nNOTE="Bird Bowl demo"\n'))
make_check('client name added to accounting_agent/web/app.js',add('accounting_agent/web/app.js','\n// Bird Bowl only\n') if (root/'accounting_agent/web/app.js').exists() else (lambda d:None))
make_check('first-client person name (Theresa) added to service.py',add('accounting_agent/service.py','\nNOTE="Ask Theresa"\n'))
