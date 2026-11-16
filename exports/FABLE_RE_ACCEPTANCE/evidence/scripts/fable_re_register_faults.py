"""Fable fault injection for PRV-14 and PRV-15 (register checker), RE checkpoint.

usage: fable_re_register_faults.py <disposable-project-copy>

Targets the THIRD pinned reviewer authority (the RD review) and the seven-row order. Files are
changed only inside the disposable copy and restored after each case. 'want' is what a sound gate
should do under the owner's rule that the latest authority wins per record. With repin=True the
checker's in-memory hash pins follow the altered file, to test the derivation logic behind the pin.
"""
import hashlib, json, re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
import scripts.check_product_requirements as cpr  # noqa: E402

REG = root / 'docs/PRODUCT_REQUIREMENTS.md'
RES = root / 'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
RD = root / 'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json'
RD_REPORT = root / 'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md'
RC = root / 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json'
text = REG.read_text(); res_text = RES.read_text()
PINS = dict(cpr.REVIEW_INPUT_HASHES)
originals = {p: p.read_bytes() for p in (REG, RES, RD, RD_REPORT, RC)}
cases = []


def record(i, t):
    a = t.index('### ' + i + ' —'); b = t.find('\n### ', a + 5); return a, (b if b > 0 else len(t))


def setf(i, name, value, t=None):
    t = t or text
    a, b = record(i, t); m = re.search(r'^- \*\*' + re.escape(name) + r':\*\*\s*([^\n]*)', t[a:b], re.M)
    return t[:a + m.start(1)] + (value(m.group(1)) if callable(value) else value) + t[a + m.end(1):]


def case(label, want, mutated=None, results=None, files=None, repin=False):
    saved = {}
    if results is not None:
        RES.write_text(results)
    for p, data in (files or {}).items():
        saved[p] = p.read_bytes(); p.write_bytes(data)
        if repin:
            cpr.REVIEW_INPUT_HASHES[str(p.relative_to(root))] = hashlib.sha256(data).hexdigest()
    try:
        cpr.validate_register(mutated or text, root); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:140]
    finally:
        if results is not None:
            RES.write_text(res_text)
        for p, data in saved.items():
            p.write_bytes(data)
        cpr.REVIEW_INPUT_HASHES.clear(); cpr.REVIEW_INPUT_HASHES.update(PINS)
    cases.append((label, want, got))
    print('J%02d %-104s want=%s got=%s %s %s' % (len(cases), label, want, got, 'ok ' if want == got else 'GAP', msg))


def results(fn):
    d = json.loads(res_text); d['results'] = fn(d['results']); return json.dumps(d, indent=2) + '\n'


def rd(fn):
    d = json.loads(originals[RD]); fn(d); return (json.dumps(d, indent=1) + '\n').encode()


def rd_state(identifier, state):
    def change(d):
        for row in d['register_verdicts']:
            if row['id'] == identifier:
                row['state'] = state
    return change


def follow(identifier, state):
    return lambda rows: [dict(r, state=state) if r['id'] == identifier else r for r in rows]


case('control: delivered register, results and three pinned authorities', 'ACCEPTED')
# --- PRV-15: the seven-row order
case('results: first two rows swapped', 'REJECTED', results=results(lambda r: [r[1], r[0]] + r[2:]))
case('results: last two rows swapped', 'REJECTED', results=results(lambda r: r[:5] + [r[6], r[5]]))
case('results: all seven rows reversed', 'REJECTED', results=results(lambda r: r[::-1]))
case('results: rotated by one', 'REJECTED', results=results(lambda r: r[1:] + r[:1]))
case('results: sorted by record id', 'REJECTED', results=results(lambda r: sorted(r, key=lambda x: x['id'])))
case('results: failed records moved in front of verified ones', 'REJECTED', results=results(lambda r: r[4:] + r[:4]))
case('results: one row dropped', 'REJECTED', results=results(lambda r: r[:-1]))
case('results: one row duplicated in place of another', 'REJECTED', results=results(lambda r: r[:6] + [r[5]]))
# --- PRV-14: the third authority is pinned
case('RD results file: BNK-03 flipped to verified, pin unchanged', 'REJECTED', files={RD: rd(rd_state('AAOS-BNK-03', 'Independently verified'))})
case('RD results file: one byte of whitespace appended', 'REJECTED', files={RD: originals[RD] + b' '})
case('RD report: one byte appended', 'REJECTED', files={RD_REPORT: originals[RD_REPORT] + b'\n'})
case('RD results file removed', 'REJECTED', files={RD: b''})
# --- PRV-14: latest authority wins per record (pins follow the altered file)
case('RD says BNK-03 verified; results keep failed', 'REJECTED', files={RD: rd(rd_state('AAOS-BNK-03', 'Independently verified'))}, repin=True)
case('RD says BNK-03 verified; results follow; register still Verification failed (lags in the safe direction)', 'ACCEPTED', results=results(follow('AAOS-BNK-03', 'Independently verified')), files={RD: rd(rd_state('AAOS-BNK-03', 'Independently verified'))}, repin=True)
case('RD says KNO-04 failed; results keep verified', 'REJECTED', files={RD: rd(rd_state('AAOS-KNO-04', 'Verification failed'))}, repin=True)
case('RD says KNO-04 failed; results follow; register still Independently verified', 'REJECTED', results=results(follow('AAOS-KNO-04', 'Verification failed')), files={RD: rd(rd_state('AAOS-KNO-04', 'Verification failed'))}, repin=True)
case('RD says KNO-04 failed; results and register follow (downgrade by the latest authority)', 'ACCEPTED', mutated=setf('AAOS-KNO-04', 'Implementation state', 'Verification failed'), results=results(follow('AAOS-KNO-04', 'Verification failed')), files={RD: rd(rd_state('AAOS-KNO-04', 'Verification failed'))}, repin=True)


def rc_state(identifier, state):
    d = json.loads(originals[RC])
    for row in d['register_verdicts']:
        if row['id'] == identifier:
            row['state'] = state
    return (json.dumps(d, indent=1) + '\n').encode()


case('OLDER authority (RC) says BNK-03 verified; RD still failed; results unchanged (older cannot override)', 'ACCEPTED', files={RC: rc_state('AAOS-BNK-03', 'Independently verified')}, repin=True)
case('OLDER authority (RC) says BNK-03 verified; results follow the older file', 'REJECTED', results=results(follow('AAOS-BNK-03', 'Independently verified')), files={RC: rc_state('AAOS-BNK-03', 'Independently verified')}, repin=True)
case('OLDER authority (RC) says KNO-04 failed; RD verified; results unchanged', 'ACCEPTED', files={RC: rc_state('AAOS-KNO-04', 'Verification failed')}, repin=True)


def drop(identifier):
    def change(d):
        d['register_verdicts'] = [r for r in d['register_verdicts'] if r['id'] != identifier]
    return change


case('RD verdict for GOV-03 deleted: the RC verdict becomes the latest; results still cite RD', 'REJECTED', files={RD: rd(drop('AAOS-GOV-03'))}, repin=True)
# --- results rows must be the latest authority's row
rc_rows = {r['id']: r for r in json.loads(originals[RC])['register_verdicts']}
case('results: BNK-03 row cites the RC report and bundle (stale authority)', 'REJECTED', results=results(lambda rows: [dict(r, report_path=rc_rows[r['id']]['report_path'], bundle_sha256=rc_rows[r['id']]['bundle_sha256'], report_sha256=PINS[rc_rows[r['id']]['report_path']]) if r['id'] == 'AAOS-BNK-03' else r for r in rows]))
case('results: GOV-03 state flipped to verified', 'REJECTED', results=results(follow('AAOS-GOV-03', 'Independently verified')))
case('results: CTL-04 bundle hash replaced by the RE bundle hash (not yet reviewed when delivered)', 'REJECTED', results=results(lambda rows: [dict(r, bundle_sha256='4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae') if r['id'] == 'AAOS-CTL-04' else r for r in rows]))
# --- register states of the three failed records
for identifier in ('AAOS-BNK-03', 'AAOS-CTL-04', 'AAOS-GOV-03'):
    for state in ('Independently verified', 'Developer-tested', 'Implemented'):
        case('register: %s raised to %s' % (identifier, state), 'REJECTED', mutated=setf(identifier, 'Implementation state', state))
# --- owner ratification is a fact the checker cannot know (as G22); the six Proposed records are compared byte for byte instead
case('register: AAOS-ONB-01 changed from Proposed to Approved (known limit, same as G22; protected by byte comparison)', 'ACCEPTED', mutated=setf('AAOS-ONB-01', 'Product decision', 'Approved'))

agree = sum(1 for c in cases if c[1] == c[2])
print('cases %d | agree %d | gaps %d' % (len(cases), agree, len(cases) - agree))
restored = all(p.read_bytes() == data for p, data in originals.items()) and cpr.REVIEW_INPUT_HASHES == PINS
print('every file restored and every pin intact after the run:', restored)
sys.exit(0 if agree == len(cases) and restored else 1)
