"""Fable fault injection for PRV-12 and PRV-13 (register checker), RD checkpoint.

usage: fable_rd_register_faults.py <disposable-project-copy>

Mutates text in memory, and files only inside the disposable copy given (each file is restored
after its case). 'want' is what a sound gate should do. Complements, and does not replace, the
unchanged fable_rc_register_faults.py (G01..G44) and register_faults.py (F01..).
"""
import hashlib, json, re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
import scripts.check_product_requirements as cpr  # noqa: E402

REG = root / 'docs/PRODUCT_REQUIREMENTS.md'
RES = root / 'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
LATER = root / 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json'
EARLIER = root / 'exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json'
RC_REPORT = root / 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'
RB_REPORT = root / 'exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md'
text = REG.read_text(); res_text = RES.read_text()
V2 = '00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d'
RC = '9a85c78a40fd9b5f675b4d135274808056b34097ad907e38e962bf25b0762454'
REAL_RC = '[independent review](../exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md), reviewed bundle SHA-256 ' + RC + '; R01a; tests/test_platform.py'
PINS = dict(cpr.REVIEW_INPUT_HASHES)


def record(i, t):
    a = t.index('### ' + i + ' —'); b = t.find('\n### ', a + 5); return a, (b if b > 0 else len(t))


def setf(i, changes, t=None):
    t = t or text
    for name, value in (changes if isinstance(changes, list) else [changes]):
        a, b = record(i, t); m = re.search(r'^- \*\*' + re.escape(name) + r':\*\*\s*([^\n]*)', t[a:b], re.M)
        t = t[:a + m.start(1)] + (value(m.group(1)) if callable(value) else value) + t[a + m.end(1):]
    return t


cases = []


def case(label, want, mutated, results=None, files=None, repin=False):
    """files: {path: new bytes} written for the case and restored. repin: also move the checker's
    in-memory hash pins to the altered files, to test the derivation logic behind the pin."""
    saved = {}
    if results is not None:
        RES.write_text(results)
    for p, data in (files or {}).items():
        saved[p] = p.read_bytes(); p.write_bytes(data)
        if repin:
            cpr.REVIEW_INPUT_HASHES[str(p.relative_to(root))] = hashlib.sha256(data).hexdigest()
    try:
        cpr.validate_register(mutated, root); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:150]
    finally:
        if results is not None:
            RES.write_text(res_text)
        for p, data in saved.items():
            p.write_bytes(data)
        cpr.REVIEW_INPUT_HASHES.clear(); cpr.REVIEW_INPUT_HASHES.update(PINS)
    cases.append((label, want, got, msg))


def results_with(fn):
    d = json.loads(res_text); out = fn(d['results'])
    if out is not None:
        d['results'] = out
    return json.dumps(d, indent=2)


def later_with(fn):
    d = json.loads(LATER.read_text()); fn(d); return json.dumps(d, indent=1).encode()


def earlier_with(fn):
    d = json.loads(EARLIER.read_text()); fn(d); return json.dumps(d, indent=1).encode()


def idx(i):
    return [r['id'] for r in json.loads(res_text)['results']].index(i)


def set_later_state(d, i, state):
    for r in d['register_verdicts']:
        if r['id'] == i:
            r['state'] = state


ids = [r['id'] for r in json.loads(res_text)['results']]
case('H01 current register and results', 'ACCEPTED', text)
# ---- PRV-12: results file against the two reviewer-authored files
case('H02 results: scope text of one row edited', 'REJECTED', text, results_with(lambda r: r[0].update(scope=r[0]['scope'] + ' And operating readiness.')))
case('H03 results: bundle hash of a failed row moved back to the V2 checkpoint', 'REJECTED', text, results_with(lambda r: r[idx('AAOS-BNK-03')].update(bundle_sha256=V2)))
case('H04 results: report path and hash of a verified row moved back to the RB report (stale metadata)', 'REJECTED', text, results_with(lambda r: r[0].update(report_path='exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md', report_sha256=PINS['exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md'], bundle_sha256=V2)))
case('H05 results: failed row GOV-03 omitted, register unchanged', 'REJECTED', text, results_with(lambda r: r.__delitem__(idx('AAOS-GOV-03'))))
case('H06 results: failed row CTL-04 omitted and CTL-04 promoted to Developer-tested', 'REJECTED', setf('AAOS-CTL-04', ('Implementation state', 'Developer-tested')), results_with(lambda r: r.__delitem__(idx('AAOS-CTL-04'))))
case('H07 results: failed CTL-04 rewritten as verified in results and register', 'REJECTED', setf('AAOS-CTL-04', [('Implementation state', 'Independently verified'), ('Evidence', REAL_RC)]), results_with(lambda r: r[idx('AAOS-CTL-04')].update(state='Independently verified')))
case('H08 register only: failed GOV-03 promoted to Independently verified citing the RC report', 'REJECTED', setf('AAOS-GOV-03', [('Implementation state', 'Independently verified'), ('Evidence', REAL_RC)]))
case('H09 results: invented row for a record no reviewer file names (ARC-01), register promoted', 'REJECTED', setf('AAOS-ARC-01', [('Implementation state', 'Independently verified'), ('Evidence', REAL_RC)]), results_with(lambda r: r.append(dict(r[0], id='AAOS-ARC-01'))))
case('H10 results: one row duplicated', 'REJECTED', text, results_with(lambda r: r.append(dict(r[0]))))
case('H11 results: an extra key added to a row', 'REJECTED', text, results_with(lambda r: r[0].update(note='developer pass')))
case('H12 results: verified row KNO-04 rewritten as failed (downgrade not in the reviewer files)', 'REJECTED', text, results_with(lambda r: r[idx('AAOS-KNO-04')].update(state='Verification failed')))
case('H13 results: two rows swapped (register says the seven-row order is preserved)', 'REJECTED', text, results_with(lambda r: [r[1], r[0]] + r[2:]))
case('H14 results: all seven rows reversed', 'REJECTED', text, results_with(lambda r: r[::-1]))
# ---- PRV-12: the protected reviewer files themselves
case('H15 later reviewer file altered: BNK-03 verdict flipped to verified (pin unchanged)', 'REJECTED', setf('AAOS-BNK-03', [('Implementation state', 'Independently verified'), ('Evidence', REAL_RC)]), results_with(lambda r: r[idx('AAOS-BNK-03')].update(state='Independently verified')), {LATER: later_with(lambda d: set_later_state(d, 'AAOS-BNK-03', 'Independently verified'))})
case('H16 later reviewer file altered by one byte of whitespace', 'REJECTED', text, None, {LATER: LATER.read_bytes() + b'\n'})
case('H17 earlier reviewer file altered: BNK-03 conclusion rewritten', 'REJECTED', text, None, {EARLIER: earlier_with(lambda d: [r.update(conclusion='May be recorded Independently verified') for r in d['verification_conclusions_for_the_seven_failed_records']['records'] if r['id'] == 'AAOS-BNK-03'])})
case('H18 pinned RC report altered by one byte', 'REJECTED', text, None, {RC_REPORT: RC_REPORT.read_bytes() + b'\n'})
case('H19 pinned RB report altered by one byte', 'REJECTED', text, None, {RB_REPORT: RB_REPORT.read_bytes() + b'\n'})
case('H20 later reviewer file removed from register_verdicts: GOV-03 row deleted there and in results', 'REJECTED', text, results_with(lambda r: r.__delitem__(idx('AAOS-GOV-03'))), {LATER: later_with(lambda d: d['register_verdicts'].__delitem__([r['id'] for r in d['register_verdicts']].index('AAOS-GOV-03')))})
# ---- PRV-12: derivation logic behind the pin (pins moved in memory to the altered file, never on disk)
case('H21 logic: later verdict for KNO-04 is failed; results follow it; register still says verified with its V2 citation', 'REJECTED', text, results_with(lambda r: r[idx('AAOS-KNO-04')].update(state='Verification failed')), {LATER: later_with(lambda d: set_later_state(d, 'AAOS-KNO-04', 'Verification failed'))}, repin=True)
case('H22 logic: same, and the register downgrades KNO-04 to Verification failed', 'ACCEPTED', setf('AAOS-KNO-04', ('Implementation state', 'Verification failed')), results_with(lambda r: r[idx('AAOS-KNO-04')].update(state='Verification failed')), {LATER: later_with(lambda d: set_later_state(d, 'AAOS-KNO-04', 'Verification failed'))}, repin=True)
case('H23 logic: later verdict for KNO-04 is failed but results keep the earlier verified row', 'REJECTED', text, None, {LATER: later_with(lambda d: set_later_state(d, 'AAOS-KNO-04', 'Verification failed'))}, repin=True)
case('H24 logic: later verdict verifies BNK-03; results and register follow with the RC citation', 'ACCEPTED', setf('AAOS-BNK-03', [('Implementation state', 'Independently verified'), ('Evidence', REAL_RC)]), results_with(lambda r: r[idx('AAOS-BNK-03')].update(state='Independently verified')), {LATER: later_with(lambda d: set_later_state(d, 'AAOS-BNK-03', 'Independently verified'))}, repin=True)
# ---- PRV-12: citations of verified records
case('H25 verified KNO-04 cites a bundle hash no reviewer checkpoint has', 'REJECTED', setf('AAOS-KNO-04', ('Evidence', lambda v: v.replace(V2, 'ab' * 32))))
case('H26 verified KNO-04 cites the later RC checkpoint and report instead of V2', 'ACCEPTED', setf('AAOS-KNO-04', ('Evidence', lambda v: v.replace(V2, RC).replace('FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md', 'FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'))))
case('H27 verified KNO-04 cites the V2 hash with the RC report (hash and report from different checkpoints)', 'REJECTED', setf('AAOS-KNO-04', ('Evidence', lambda v: v.replace('FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md', 'FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'))))
# ---- PRV-13: client display name
drop = lambda t: re.sub(r'^(- \*\*Client-specific terms:\*\*\s*)Bird Bowl; ', r'\1', t, count=1, flags=re.M)
case('H30 display name removed from the terms list', 'REJECTED', drop(text))
case('H31 section heading renamed without the list (Cedar Lane onboarding and validation)', 'REJECTED', text.replace('\n## Bird Bowl onboarding and validation', '\n## Cedar Lane onboarding and validation', 1))
case('H32 heading and list both renamed, client records still use the old name', 'REJECTED', drop(text.replace('\n## Bird Bowl onboarding and validation', '\n## Cedar Lane onboarding and validation', 1)).replace('- **Client-specific terms:** ', '- **Client-specific terms:** Cedar Lane; ', 1))
renamed = text.replace('Bird Bowl', 'Cedar Lane')
case('H33 the client renamed consistently everywhere in the register (name is read, not hard-coded)', 'ACCEPTED', renamed)
case('H34 ... and the new name then appears in a shared record', 'REJECTED', setf('AAOS-ARC-01', ('Description', 'Cedar Lane signs off.'), renamed))
case('H35 ... and the OLD name is then no longer client-specific in a shared record', 'ACCEPTED', setf('AAOS-ARC-01', ('Description', lambda v: v + ' Bird Bowl is a generic phrase here.'), renamed))
case('H36 heading wording changed so that no display name can be read (onboarding & validation)', 'REJECTED', text.replace('\n## Bird Bowl onboarding and validation', '\n## Bird Bowl onboarding & validation', 1))
case('H37 display name kept only inside a longer term (Bird Bowl LLC)', 'REJECTED', re.sub(r'^(- \*\*Client-specific terms:\*\*\s*)Bird Bowl; ', r'\1Bird Bowl LLC; ', text, count=1, flags=re.M))
case('H38 display name in the list in another letter case (bird bowl)', 'ACCEPTED', re.sub(r'^(- \*\*Client-specific terms:\*\*\s*)Bird Bowl; ', r'\1bird bowl; ', text, count=1, flags=re.M))
case('H39 display name moved to the end of the list', 'ACCEPTED', re.sub(r'^(- \*\*Client-specific terms:\*\*\s*)Bird Bowl; ([^\n]+)', r'\1\2; Bird Bowl', text, count=1, flags=re.M))

w = max(len(c[0]) for c in cases); gaps = 0
for label, want, got, msg in cases:
    ok = want == got; gaps += not ok
    print('%-*s want=%-8s got=%-8s %s %s' % (w, label, want, got, 'ok ' if ok else 'GAP', msg))
print('cases', len(cases), '| agree', len(cases) - gaps, '| gaps', gaps)
restored = REG.read_text() == text and RES.read_text() == res_text and all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in PINS.items())
print('every file restored and every pin intact after the run:', restored)
sys.exit(1 if gaps or not restored else 0)
