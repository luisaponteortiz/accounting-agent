"""Fable additional fault injection for PRV-02..PRV-10 (register checker and make check).

usage: fable_rc_register_faults.py <disposable-project-copy>

Mutates text in memory, and files only inside the disposable copy given (each file is restored
after its case). 'want' is what a sound gate should do. Complements, and does not replace, the
unchanged exports/FABLE_RB_ACCEPTANCE/evidence/scripts/register_faults.py.
"""
import json, re, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from scripts.check_product_requirements import validate_register  # noqa: E402

REG = root / 'docs/PRODUCT_REQUIREMENTS.md'
RES = root / 'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
text = REG.read_text(); res_text = RES.read_text()
RB_REPORT = 'exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md'
V2 = '00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d'
REAL = '[independent review](../' + RB_REPORT + '), reviewed bundle SHA-256 ' + V2 + '; R01a; tests/test_platform.py'


def record(i, t):
    a = t.index('### ' + i + ' —'); b = t.find('\n### ', a + 5); return a, (b if b > 0 else len(t))


def setf(i, changes, t=None):
    t = t or text
    for name, value in (changes if isinstance(changes, list) else [changes]):
        a, b = record(i, t); m = re.search(r'^- \*\*' + re.escape(name) + r':\*\*\s*([^\n]*)', t[a:b], re.M)
        t = t[:a + m.start(1)] + (value(m.group(1)) if callable(value) else value) + t[a + m.end(1):]
    return t


cases = []


def case(label, want, mutated, results=None):
    if results is not None:
        RES.write_text(results)
    try:
        validate_register(mutated, root); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:120]
    finally:
        if results is not None:
            RES.write_text(res_text)
    cases.append((label, want, got, msg))


def results_with(fn):
    d = json.loads(res_text); fn(d['results']); return json.dumps(d, indent=2)


case('G01 current register', 'ACCEPTED', text)
# PRV-02
case('G02 tested record whose only evidence is an existing test file', 'ACCEPTED', setf('AAOS-ARC-02', ('Evidence', 'tests/test_platform.py')))
case('G03 tested record whose only evidence is a declared probe id (R01a)', 'ACCEPTED', setf('AAOS-ARC-02', ('Evidence', 'probe R01a')))
case('G04 only evidence is a correction ticket (RC-01)', 'REJECTED', setf('AAOS-ARC-02', ('Evidence', 'RC-01 corrected')))
case('G05 only evidence is a probe-like token that no script declares (N99z)', 'REJECTED', setf('AAOS-ARC-02', ('Evidence', 'probe N99z')))
case('G06 only evidence is a real file that is not a test (scripts/check.py)', 'REJECTED', setf('AAOS-ARC-02', ('Evidence', 'scripts/check.py')))
case('G07 declared probe id glued inside another word (xR01ay)', 'REJECTED', setf('AAOS-ARC-02', ('Evidence', 'see xR01ay')))
# PRV-03
case('G08 failed record promoted to Independently verified with a real report, hash and probe', 'REJECTED', setf('AAOS-BNK-03', [('Implementation state', 'Independently verified'), ('Evidence', REAL)]))
case('G09 failed record promoted to Implemented', 'REJECTED', setf('AAOS-GOV-03', ('Implementation state', 'Implemented')))
case('G10 failed record hidden as Not started', 'REJECTED', setf('AAOS-CTL-04', ('Implementation state', 'Not started')))
case('G11 another record self-asserted with the real RB report and the real V2 hash, no result entry', 'REJECTED', setf('AAOS-ARC-02', [('Implementation state', 'Independently verified'), ('Evidence', REAL)]))
case('G12 verified record whose evidence drops the checkpoint hash', 'REJECTED', setf('AAOS-KNO-04', ('Evidence', lambda v: v.replace(V2, 'the V2 bundle'))))
case('G13 results file names a report that does not exist', 'REJECTED', text, results_with(lambda r: r[0].update(report_path='exports/NO_SUCH_REPORT.md')))
case('G14 results file carries a report hash that differs from the report', 'REJECTED', text, results_with(lambda r: r[0].update(report_sha256='ab' * 32)))
case('G15 results file names a report outside the project', 'REJECTED', text, results_with(lambda r: r[0].update(report_path='../outside.md')))
case('G16 results file entry removed for a failed record, record then promoted', 'REJECTED', setf('AAOS-BNK-03', ('Implementation state', 'Developer-tested')), results_with(lambda r: r.__delitem__(4)))
case('G17 developer edits the results file as well: failed BNK-03 rewritten as verified in both places', 'REJECTED', setf('AAOS-BNK-03', [('Implementation state', 'Independently verified'), ('Evidence', REAL)]), results_with(lambda r: r[4].update(state='Independently verified')))
case('G18 developer adds a results entry for a record the cited report never assessed (ARC-02)', 'REJECTED', setf('AAOS-ARC-02', [('Implementation state', 'Independently verified'), ('Evidence', REAL)]), results_with(lambda r: r.append(dict(r[0], id='AAOS-ARC-02'))))
# PRV-05
case('G19 Approved record with a bare Proposed dependency (INT-01 -> INT-07)', 'REJECTED', setf('AAOS-INT-01', ('Dependencies', lambda v: v.replace('AAOS-INT-07 if ratified', 'AAOS-INT-07'))))
case('G20 condition written before the id (if ratified AAOS-INT-07)', 'REJECTED', setf('AAOS-INT-01', ('Dependencies', lambda v: v.replace('AAOS-INT-07 if ratified', 'if ratified AAOS-INT-07'))))
case('G21 condition belongs to the next id in the clause (AAOS-INT-07, AAOS-KNO-03 if ratified)', 'REJECTED', setf('AAOS-INT-01', ('Dependencies', lambda v: v.replace('AAOS-INT-07 if ratified', 'AAOS-INT-07, AAOS-KNO-03 if ratified'))))
case('G22 a Proposed record made Approved by the developer keeps the check quiet (ONB-01)', 'ACCEPTED', setf('AAOS-ONB-01', ('Product decision', 'Approved')))
# PRV-06
case('G23 tested record with a bare Not started dependency (GOV-02 -> GOV-01)', 'REJECTED', setf('AAOS-GOV-02', ('Dependencies', 'AAOS-GOV-01')))
case('G24 the word only after the id is not a condition (AAOS-GOV-01 only)', 'REJECTED', setf('AAOS-GOV-02', ('Dependencies', 'AAOS-GOV-01 only')))
case('G25 verified record with a bare Deferred dependency (CTL-01 -> CTL-03)', 'REJECTED', setf('AAOS-CTL-01', ('Dependencies', lambda v: v.replace('AAOS-CTL-03 for real authority only', 'AAOS-CTL-03'))))
# PRV-07
case('G26 EXC-03 scope note prefix changed to Rejected scope.', 'REJECTED', setf('AAOS-EXC-03', ('Scope note', lambda v: v.replace('Reserved action.', 'Rejected scope.', 1))))
case('G27 EXC-01 scope note without the fixed prefix', 'REJECTED', setf('AAOS-EXC-01', ('Scope note', lambda v: v.replace('Rejected scope. ', '', 1))))
case('G28 EXC-01 decision changed to Approved while the note says Rejected scope', 'REJECTED', setf('AAOS-EXC-01', ('Product decision', 'Approved')))
case('G29 EXC-01 table row changed to Reserved', 'REJECTED', text.replace('| AAOS-EXC-01 | Rejected |', '| AAOS-EXC-01 | Reserved |', 1))
case('G30 EXC-04 table row removed', 'REJECTED', re.sub(r'^\| AAOS-EXC-04 \|.*\n', '', text, flags=re.M))
# PRV-08
case('G31 ". ;" in a Dependencies field', 'REJECTED', setf('AAOS-BNK-02', ('Dependencies', lambda v: v.replace(';', '. ;', 1))))
case('G32 ".;" in a Dependencies field', 'REJECTED', setf('AAOS-BNK-02', ('Dependencies', lambda v: v.replace(';', '.;', 1))))
# PRV-10
case('G33 first-client person (Jeff) in a shared Business purpose', 'REJECTED', setf('AAOS-ARC-01', ('Business purpose', 'So that Jeff can support it.')))
case('G34 first-client vendor in a shared Scope note', 'REJECTED', setf('AAOS-ARC-01', ('Scope note', 'Expensify export only.')))
case('G35 first-client name written BirdBowl in a shared Needed-for-adjacent field (Target stage)', 'REJECTED', setf('AAOS-ARC-01', ('Target stage', 'After BirdBowl pilot')))
case('G36 first-client name written bird_bowl in a shared Evidence field', 'REJECTED', setf('AAOS-ARC-01', ('Evidence', lambda v: v + ' bird_bowl sample')))
case('G37 first-client name in a shared record title', 'REJECTED', text.replace('### AAOS-ARC-01 — ', '### AAOS-ARC-01 — Bird Bowl ', 1))
case('G38 first-client person in a shared Trace field (Trace is exempt)', 'ACCEPTED', setf('AAOS-ARC-01', ('Trace', lambda v: v + '; Theresa interview notes')))
case('G39 first-client name in an allowed boundary record (GOV-01 Scope note)', 'ACCEPTED', setf('AAOS-GOV-01', ('Scope note', lambda v: v + ' Bird Bowl is the first client.')))
new_term = re.sub(r'^(- \*\*Client-specific terms:\*\*\s*[^\n]+)', r'\1; Marisol', text, count=1, flags=re.M)
new_term = setf('AAOS-BB-01', ('Scope note', lambda v: v + ' Marisol is a fictional added contact.'), new_term)
case('G40 a term newly added to the client section is accepted in the client section', 'ACCEPTED', new_term)
case('G41 ... and is then rejected in a shared record (list is read, not hard-coded)', 'REJECTED', setf('AAOS-ARC-01', ('Description', 'Marisol signs off.'), new_term))
case('G42 a term added to the client list that no client record uses', 'REJECTED', re.sub(r'^(- \*\*Client-specific terms:\*\*\s*[^\n]+)', r'\1; Zebulon', text, count=1, flags=re.M))
case('G43 the client-specific terms line removed', 'REJECTED', re.sub(r'^- \*\*Client-specific terms:\*\*[^\n]*\n', '', text, count=1, flags=re.M))
case('G44 the client name removed from the terms list while client records still use it', 'REJECTED', re.sub(r'^(- \*\*Client-specific terms:\*\*\s*)Bird Bowl; ', r'\1', text, count=1, flags=re.M))

w = max(len(c[0]) for c in cases); gaps = 0
for label, want, got, msg in cases:
    ok = want == got; gaps += not ok
    print('%-*s want=%-8s got=%-8s %s %s' % (w, label, want, got, 'ok ' if ok else 'GAP', msg))
print('cases', len(cases), '| agree', len(cases) - gaps, '| gaps', gaps)


# make check on the disposable copy; every file is restored after its case
def make_check(label, want, path, extra, create=False):
    p = root / path
    before = None if create else p.read_bytes()
    if create:
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(extra)
    else:
        p.write_bytes(before + extra.encode())
    r = subprocess.run(['make', 'check'], cwd=root, capture_output=True, text=True)
    if create:
        p.unlink()
        if p.parent != root / 'accounting_agent/web' and not any(p.parent.iterdir()):
            p.parent.rmdir()
    else:
        p.write_bytes(before)
    got = 'PASS' if r.returncode == 0 else 'FAIL'
    out = (r.stdout + r.stderr).strip().splitlines()
    detail = next((l for l in reversed(out) if 'Client' in l or 'FAIL' in l or 'Error' in l), out[-1] if out else '')[:130]
    print('make check | %-70s want=%s got=%s %s | %s' % (label, want, got, 'ok ' if want == got else 'GAP', detail))
    return want != got


g = 0
r = subprocess.run(['make', 'check'], cwd=root, capture_output=True, text=True)
print('make check | %-70s want=PASS got=%s' % ('unchanged disposable copy', 'PASS' if r.returncode == 0 else 'FAIL'))
g += make_check('client name appended to accounting_agent/web/index.html', 'FAIL', 'accounting_agent/web/index.html', '\n<!-- Bird Bowl -->\n')
g += make_check('client name appended to accounting_agent/web/style.css', 'FAIL', 'accounting_agent/web/style.css', '\n/* Bird Bowl */\n')
g += make_check('client person (Theresa) appended to accounting_agent/web/app.js', 'FAIL', 'accounting_agent/web/app.js', '\n// ask Theresa\n')
g += make_check('client vendor (Expensify) appended to accounting_agent/modules.py', 'FAIL', 'accounting_agent/modules.py', '\nNOTE="Expensify"\n')
g += make_check('client name in a new nested file accounting_agent/web/sub/x.js', 'FAIL', 'accounting_agent/web/sub/x.js', '// birdbowl\n', create=True)
g += make_check('client name in a new file accounting_agent/config/x.json (exempt)', 'PASS', 'accounting_agent/config/x.json', '{"n":"Bird Bowl"}\n', create=True)
g += make_check('client name in a new file accounting_agent/fixtures/x.json (exempt)', 'PASS', 'accounting_agent/fixtures/x.json', '{"n":"Bird Bowl"}\n', create=True)
g += make_check('client name appended to accounting_agent/demo.py (exempt)', 'PASS', 'accounting_agent/demo.py', '\nNOTE="Bird Bowl demo"\n')
g += make_check('neutral text appended to accounting_agent/web/app.js', 'PASS', 'accounting_agent/web/app.js', '\n// accounting client\n')
print('make check gaps', g)
sys.exit(1 if gaps or g else 0)
