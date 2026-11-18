"""Fable fault injection for PRV-16 (register checker), RF checkpoint.

usage: fable_rf_register_faults.py <disposable-project-copy>

Targets the FOURTH pinned reviewer authority (the RE review), the three older ones and the seven-row order. Files are
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
RC_REPORT = root / 'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_REPORT.md'
RB = root / 'exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json'
RB_REPORT = root / 'exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md'
RE = root / 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json'
RE_REPORT = root / 'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'
text = REG.read_text(); res_text = RES.read_text()
PINS = dict(cpr.REVIEW_INPUT_HASHES)
originals = {p: p.read_bytes() for p in (REG, RES, RD, RD_REPORT, RC, RC_REPORT, RB, RB_REPORT, RE, RE_REPORT)}
cases = []


def record(i, t):
    a = t.index('### ' + i + ' —'); b = t.find('\n### ', a + 5); return a, (b if b > 0 else len(t))


def setf(i, name, value, t=None):
    t = t or text
    a, b = record(i, t); m = re.search(r'^- \*\*' + re.escape(name) + r':\*\*\s*([^\n]*)', t[a:b], re.M)
    return t[:a + m.start(1)] + (value(m.group(1)) if callable(value) else value) + t[a + m.end(1):]


def case(label, want, mutated=None, results=None, files=None, repin=False, pins=None):
    saved = {}
    if pins is not None:
        cpr.REVIEW_INPUT_HASHES.clear(); cpr.REVIEW_INPUT_HASHES.update(pins)
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
    print('K%02d %-118s want=%s got=%s %s %s' % (len(cases), label, want, got, 'ok ' if want == got else 'GAP', msg))


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




def auth(path, fn):
    d = json.loads(originals[path]); fn(d); return (json.dumps(d, indent=1) + '\n').encode()


def state(identifier, value):
    def change(d):
        for row in d['register_verdicts']:
            if row['id'] == identifier:
                row['state'] = value
    return change


def rb_conclusion(identifier, value):
    def change(d):
        for row in d['verification_conclusions_for_the_seven_failed_records']['records']:
            if row['id'] == identifier:
                row['conclusion'] = value
    return change


def drop(identifier):
    def change(d):
        d['register_verdicts'] = [r for r in d['register_verdicts'] if r['id'] != identifier]
    return change


def follow(identifier, value):
    return lambda rows: [dict(r, state=value) if r['id'] == identifier else r for r in rows]


def cite(identifier, source):
    data = json.loads(originals[source]); rows_ = {r['id']: r for r in data['register_verdicts']}
    return lambda rows: [dict(r, state=rows_[r['id']]['state'], report_path=rows_[r['id']]['report_path'], bundle_sha256=rows_[r['id']]['bundle_sha256'], report_sha256=PINS[rows_[r['id']]['report_path']],
                              scope=data['scope_of_every_conclusion']) if r['id'] == identifier else r for r in rows]


V, F = 'Independently verified', 'Verification failed'
case('control: delivered register, results and four pinned authorities', 'ACCEPTED')
# --- the seven-row order
case('results: first two rows swapped', 'REJECTED', results=results(lambda r: [r[1], r[0]] + r[2:]))
case('results: last two rows swapped', 'REJECTED', results=results(lambda r: r[:5] + [r[6], r[5]]))
case('results: all seven rows reversed', 'REJECTED', results=results(lambda r: r[::-1]))
case('results: rotated by one', 'REJECTED', results=results(lambda r: r[1:] + r[:1]))
case('results: sorted by record id', 'REJECTED', results=results(lambda r: sorted(r, key=lambda x: x['id'])))
case('results: failed records moved in front of verified ones', 'REJECTED', results=results(lambda r: r[4:] + r[:4]))
case('results: one row dropped', 'REJECTED', results=results(lambda r: r[:-1]))
case('results: one row duplicated in place of another', 'REJECTED', results=results(lambda r: r[:6] + [r[5]]))
case('results: an eighth row appended (copy of the first)', 'REJECTED', results=results(lambda r: r + [r[0]]))
# --- every authority and report is pinned
case('RE results file: BNK-03 flipped to verified, pin unchanged', 'REJECTED', files={RE: auth(RE, state('AAOS-BNK-03', V))})
for label, path in (('RE results file', RE), ('RE report', RE_REPORT), ('RD results file', RD), ('RD report', RD_REPORT), ('RC results file', RC), ('RC report', RC_REPORT), ('RB conclusions file', RB), ('RB report', RB_REPORT)):
    case('%s: one byte appended' % label, 'REJECTED', files={path: originals[path] + b'\n'})
case('RE results file emptied', 'REJECTED', files={RE: b''})
case('RE report emptied', 'REJECTED', files={RE_REPORT: b''})
case('checker pins: the two RE entries removed (three-authority configuration) with the delivered results', 'REJECTED', pins={k: v for k, v in PINS.items() if 'FABLE_RE_ACCEPTANCE' not in k})
case('checker pins: RE entries moved in front of the RD entries (RD would become the latest)', 'REJECTED',
     pins=dict([kv for kv in PINS.items() if 'FABLE_RE_ACCEPTANCE' in kv[0]] + [kv for kv in PINS.items() if 'FABLE_RE_ACCEPTANCE' not in kv[0]]))
# --- the fourth authority controls per record (pins follow the altered file)
case('RE says BNK-03 verified; results keep failed', 'REJECTED', files={RE: auth(RE, state('AAOS-BNK-03', V))}, repin=True)
case('RE says BNK-03 verified; results follow; register still Verification failed (lags in the safe direction)', 'ACCEPTED', results=results(follow('AAOS-BNK-03', V)), files={RE: auth(RE, state('AAOS-BNK-03', V))}, repin=True)
case('RE says KNO-04 failed; results keep verified', 'REJECTED', files={RE: auth(RE, state('AAOS-KNO-04', F))}, repin=True)
case('RE says KNO-04 failed; results follow; register still Independently verified (promotion over a failed verdict)', 'REJECTED', results=results(follow('AAOS-KNO-04', F)), files={RE: auth(RE, state('AAOS-KNO-04', F))}, repin=True)
case('RE says KNO-04 failed; results and register follow (downgrade by the latest authority)', 'ACCEPTED', mutated=setf('AAOS-KNO-04', 'Implementation state', F), results=results(follow('AAOS-KNO-04', F)), files={RE: auth(RE, state('AAOS-KNO-04', F))}, repin=True)
# --- an older authority, altered and re-pinned, cannot override the fourth
for name, path in (('RD', RD), ('RC', RC)):
    case('OLDER authority (%s) says BNK-03 verified; RE still failed; results unchanged' % name, 'ACCEPTED', files={path: auth(path, state('AAOS-BNK-03', V))}, repin=True)
    case('OLDER authority (%s) says BNK-03 verified; results follow the older file' % name, 'REJECTED', results=results(follow('AAOS-BNK-03', V)), files={path: auth(path, state('AAOS-BNK-03', V))}, repin=True)
    case('OLDER authority (%s) says BNK-03 verified; results and register follow the older file' % name, 'REJECTED', mutated=setf('AAOS-BNK-03', 'Implementation state', V), results=results(follow('AAOS-BNK-03', V)), files={path: auth(path, state('AAOS-BNK-03', V))}, repin=True)
    case('OLDER authority (%s) says KNO-04 failed; RE verified; results unchanged' % name, 'ACCEPTED', files={path: auth(path, state('AAOS-KNO-04', F))}, repin=True)
    case('OLDER authority (%s) says KNO-04 failed; results and register follow the older file' % name, 'REJECTED', mutated=setf('AAOS-KNO-04', 'Implementation state', F), results=results(follow('AAOS-KNO-04', F)), files={path: auth(path, state('AAOS-KNO-04', F))}, repin=True)
# KNO-04 was verified by the oldest authority and the register cites that review as its verified checkpoint, so removing that verdict is refused outright
case('OLDEST authority (RB) says KNO-04 remains failed; results unchanged (the register cites that review as the verified checkpoint)', 'REJECTED', files={RB: auth(RB, rb_conclusion('AAOS-KNO-04', 'Remains Verification failed'))}, repin=True)
case('OLDEST authority (RB) says KNO-04 remains failed; results and register follow the oldest file', 'REJECTED', mutated=setf('AAOS-KNO-04', 'Implementation state', F), results=results(follow('AAOS-KNO-04', F)),
     files={RB: auth(RB, rb_conclusion('AAOS-KNO-04', 'Remains Verification failed'))}, repin=True)
case('OLDEST authority (RB): an unknown conclusion text', 'REJECTED', files={RB: auth(RB, rb_conclusion('AAOS-KNO-04', 'Probably fine'))}, repin=True)
# --- a record missing from the fourth authority falls back to the third, and the results must say so
case('RE verdict for GOV-03 deleted: the RD verdict becomes the latest; results still cite RE', 'REJECTED', files={RE: auth(RE, drop('AAOS-GOV-03'))}, repin=True)
case('RE verdict for GOV-03 deleted; the GOV-03 results row cites the RD review', 'ACCEPTED', results=results(cite('AAOS-GOV-03', RD)), files={RE: auth(RE, drop('AAOS-GOV-03'))}, repin=True)
# --- results rows must be the latest authority's row
case('results: BNK-03 row cites the RD report and bundle (stale authority)', 'REJECTED', results=results(cite('AAOS-BNK-03', RD)))
case('results: BNK-03 row cites the RC report and bundle (stale authority)', 'REJECTED', results=results(cite('AAOS-BNK-03', RC)))
case('results: GOV-03 state flipped to verified', 'REJECTED', results=results(follow('AAOS-GOV-03', V)))
case('results: KNO-04 state flipped to failed', 'REJECTED', results=results(follow('AAOS-KNO-04', F)))
case('results: CTL-04 bundle hash replaced by the RF bundle hash (not reviewed when delivered)', 'REJECTED', results=results(lambda rows: [dict(r, bundle_sha256='c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd') if r['id'] == 'AAOS-CTL-04' else r for r in rows]))
case('results: CTL-04 report hash altered', 'REJECTED', results=results(lambda rows: [dict(r, report_sha256='0' * 64) if r['id'] == 'AAOS-CTL-04' else r for r in rows]))
case('results: CTL-04 scope sentence altered', 'REJECTED', results=results(lambda rows: [dict(r, scope='Production ready.') if r['id'] == 'AAOS-CTL-04' else r for r in rows]))
# --- register states of the three failed records, and their citation
for identifier in ('AAOS-BNK-03', 'AAOS-CTL-04', 'AAOS-GOV-03'):
    for value in (V, 'Developer-tested', 'Implemented'):
        case('register: %s raised to %s' % (identifier, value), 'REJECTED', mutated=setf(identifier, 'Implementation state', value))
old_cite = lambda s: s.replace('FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md', 'FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_REPORT.md').replace('4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae', '0d188fa65a7fef24447ae0089b07c17395bdb052c680b4c9dba91f9a37647ea9')
assert old_cite(text) != text
case('register: AAOS-BNK-03 (failed) evidence cites the RD review and bundle instead of the RE review (known limit, unchanged from the RE checkpoint: the citation text of a failed record is not checked)', 'ACCEPTED', mutated=setf('AAOS-BNK-03', 'Evidence', old_cite))
wrong_hash = lambda s: re.sub(r'\b[a-f0-9]{64}\b', 'c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd', s)
case('register: AAOS-KNO-04 (verified) evidence cites a bundle hash that no review verified', 'REJECTED', mutated=setf('AAOS-KNO-04', 'Evidence', wrong_hash))
# --- owner ratification is a fact the checker cannot know (as G22 and J35); the six Proposed records are compared byte for byte instead
case('register: AAOS-ONB-01 changed from Proposed to Approved (known limit, same as G22; protected by byte comparison)', 'ACCEPTED', mutated=setf('AAOS-ONB-01', 'Product decision', 'Approved'))

agree = sum(1 for c in cases if c[1] == c[2])
print('cases %d | agree %d | gaps %d' % (len(cases), agree, len(cases) - agree))
restored = all(p.read_bytes() == data for p, data in originals.items()) and cpr.REVIEW_INPUT_HASHES == PINS and list(cpr.REVIEW_INPUT_HASHES) == list(PINS)
print('every file restored and every pin intact after the run:', restored)
sys.exit(0 if agree == len(cases) and restored else 1)
