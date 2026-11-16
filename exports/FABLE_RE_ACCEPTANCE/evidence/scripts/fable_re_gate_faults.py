"""Fable fault injection for the RE gate (scripts/verify_rd_feed_review.py) and its wiring.

usage: fable_re_gate_faults.py <project-root> <rd-probes-stdout> <y05-stdout> <order-search-stdout> <order-search-json>

Feeds the gate's own validators the real outputs of this checkpoint, then altered copies. Nothing is
written to the project. 'want' is what a sound gate should do.
"""
import copy, json, re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root / 'scripts'))
import verify_rd_feed_review as gate  # noqa: E402

probes = Path(sys.argv[2]).read_text(); y05 = Path(sys.argv[3]).read_text()
orders_out = Path(sys.argv[4]).read_text(); data = json.loads(Path(sys.argv[5]).read_text())
cases = []


def case(label, want, fn):
    try:
        fn(); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:110]
    cases.append((want, got))
    print('K%02d %-92s want=%s got=%s %s %s' % (len(cases), label, want, got, 'ok ' if want == got else 'GAP', msg))


def line(pid, text=probes):
    return re.search(r'(?m)^\s*%s\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s*$' % re.escape(pid), text.split('\nSUMMARY\n')[-1]).group(0)


P = lambda text, code=0: (lambda: gate.validate_probes(code, text))
case('probes: the real 12-probe output, exit 0', 'ACCEPTED', P(probes))
case('probes: real output, exit 1', 'REJECTED', P(probes, 1))
for verdict in ('WEAK', 'NOTE', 'ERROR'):
    case('probes: E06 reported %s' % verdict, 'REJECTED', P(probes.replace(line('E06'), line('E06').replace('OK', verdict))))
case('probes: E03 line missing', 'REJECTED', P(probes.replace(line('E03') + '\n', '')))
case('probes: E05 line duplicated', 'REJECTED', P(probes.replace(line('E05'), line('E05') + '\n' + line('E05'))))
case('probes: E03 missing and E05 duplicated (count stays 12)', 'REJECTED', P(probes.replace(line('E03'), line('E05'))))
case('probes: unknown id Z99 in place of Y06', 'REJECTED', P(probes.replace(line('Y06'), line('Y06').replace('Y06', 'Z99'))))
case('probes: extra unassigned probe Y05 OK added', 'REJECTED', P(probes.replace(line('Y06'), line('Y06') + '\n' + line('Y06').replace('Y06', 'Y05'))))
case('probes: summary section absent', 'REJECTED', P(probes.split('\nSUMMARY\n')[0]))
case('probes: two summary sections', 'REJECTED', P(probes + '\nSUMMARY\n' + probes.split('\nSUMMARY\n')[-1]))
case('probes: empty output', 'REJECTED', P(''))
case('adapted Y05: real output', 'ACCEPTED', lambda: gate.validate_probes(0, y05, ('Y05',)))
case('adapted Y05: reported WEAK', 'REJECTED', lambda: gate.validate_probes(0, y05.replace(line('Y05', y05), line('Y05', y05).replace('OK', 'WEAK')), ('Y05',)))
case('adapted Y05: output of the 12-probe run offered instead', 'REJECTED', lambda: gate.validate_probes(0, probes, ('Y05',)))

O = lambda out=orders_out, d=data, code=0: (lambda: gate.validate_orders(code, out, d))


def alter(fn):
    d = copy.deepcopy(data); fn(d); return d


case('orders: the real 336-order result, exit 0', 'ACCEPTED', O())
case('orders: real result, exit 1', 'REJECTED', O(code=1))
case('orders: one order missing', 'REJECTED', O(d=alter(lambda d: d['results'].pop())))
case('orders: one order missing, runs lowered to 335', 'REJECTED', O(d=alter(lambda d: (d['results'].pop(), d.update(runs=335)))))
case('orders: one order duplicated in place of another (count stays 336)', 'REJECTED', O(d=alter(lambda d: d['results'].__setitem__(-1, copy.deepcopy(d['results'][0])))))
case('orders: one extra order appended', 'REJECTED', O(d=alter(lambda d: d['results'].append(copy.deepcopy(d['results'][0])))))
case('orders: one row marked double', 'REJECTED', O(d=alter(lambda d: d['results'][7].update(double=True))))
case('orders: one row approved in both periods but not marked double', 'REJECTED', O(d=alter(lambda d: d['results'][7].update(november_A1_approved=True, december_approved=True))))
case('orders: top-level double count 1', 'REJECTED', O(d=alter(lambda d: d.update(double=1))))
case('orders: a whole family replaced by a renamed one', 'REJECTED', O(d=alter(lambda d: [r.update(family='X+Yc+Yt+Q') for r in d['results'] if r['family'] == 'X+Yc+Yt+Z'])))
case('orders: summary line says double=1', 'REJECTED', O(out=orders_out.replace('double=0', 'double=1')))
case('orders: summary line says finalized_silently=1', 'REJECTED', O(out=orders_out.replace('finalized_silently=0', 'finalized_silently=1')))
case('orders: summary line absent', 'REJECTED', O(out=re.sub(r'(?m)^SUMMARY runs=.*$', '', orders_out)))
case('orders: summary line printed twice', 'REJECTED', O(out=orders_out + re.search(r'(?m)^SUMMARY runs=.*$', orders_out).group(0) + '\n'))
case('orders: summary says 335 runs', 'REJECTED', O(out=orders_out.replace('runs=336', 'runs=335')))

# wiring
make = (root / 'Makefile').read_text()
tests = (root / 'tests/test_re_review_gate.py').read_text()
case('wiring: make re-gate runs scripts/verify_rd_feed_review.py', 'ACCEPTED', lambda: (_ for _ in ()).throw(ValueError('not wired')) if not re.search(r'(?m)^re-gate:\n\t\$\(PYTHON\) scripts/verify_rd_feed_review\.py$', make) else None)
case('wiring: make test (unittest discover) contains a method that runs the gate main()', 'ACCEPTED', lambda: (_ for _ in ()).throw(ValueError('not wired')) if not ('verify_rd_feed_review' in tests and re.search(r'def test_all_authorized_probes_and_336_orders', tests)) else None)
agree = sum(1 for w, g in cases if w == g)
print('cases %d | agree %d | gaps %d' % (len(cases), agree, len(cases) - agree))
sys.exit(0 if agree == len(cases) else 1)
