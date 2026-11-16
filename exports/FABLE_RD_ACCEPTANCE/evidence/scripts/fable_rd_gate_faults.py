"""Fable fault cases for the make rd-gate contract (scripts/verify_rc_review.py), RD checkpoint.

usage: fable_rd_gate_faults.py <project-copy> <real-probe-stdout> <real-order-search-stdout> <real-order-search-json>

Feeds the gate's two validators the real outputs of my own run, then altered copies in memory.
Nothing is written. 'want' is what a sound gate should do.
"""
import copy, json, re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from scripts.verify_rc_review import validate_probes, validate_orders  # noqa: E402

probes = Path(sys.argv[2]).read_text(); orders_out = Path(sys.argv[3]).read_text(); data = json.loads(Path(sys.argv[4]).read_text())
cases = []


def case(label, want, fn, *args):
    try:
        fn(*args); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:90]
    cases.append((label, want, got, msg))


def alt(fn):
    d = copy.deepcopy(data); fn(d); return d


line = lambda pid: re.search(r'(?m)^%s\s+\S+\s+\S+\s*$' % re.escape(pid), probes).group(0)
case('P01 real probe output of my run, exit 0', 'ACCEPTED', validate_probes, 0, probes)
case('P02 real output, exit 1', 'REJECTED', validate_probes, 1, probes)
case('P03 summary row X02 missing', 'REJECTED', validate_probes, 0, probes.replace(line('X02') + '\n', ''))
case('P04 summary row X02 duplicated', 'REJECTED', validate_probes, 0, probes.replace(line('X02'), line('X02') + '\n' + line('X02')))
case('P05 unknown id X99 in place of X02', 'REJECTED', validate_probes, 0, probes.replace(line('X02'), line('X02').replace('X02', 'X99')))
case('P06 an extra unknown id X99 added', 'REJECTED', validate_probes, 0, probes.replace(line('X02'), line('X02') + '\n' + line('X02').replace('X02', 'X99')))
case('P07 X01 reported WEAK', 'REJECTED', validate_probes, 0, probes.replace(line('X01'), re.sub(r'OK\s*$', 'WEAK', line('X01'))))
case('P08 X01d reported ERROR', 'REJECTED', validate_probes, 0, probes.replace(line('X01d'), re.sub(r'OK\s*$', 'ERROR', line('X01d'))))
case('P09 the X08 NOTE altered to OK', 'REJECTED', validate_probes, 0, probes.replace(line('X08'), re.sub(r'NOTE\s*$', 'OK', line('X08'))))
case('P10 an OK probe (Q03) altered to NOTE', 'REJECTED', validate_probes, 0, probes.replace(line('Q03'), re.sub(r'OK\s*$', 'NOTE', line('Q03'))))
case('P11 empty output', 'REJECTED', validate_probes, 0, '')
case('O01 real order-search output and JSON of my run, exit 0', 'ACCEPTED', validate_orders, 0, orders_out, data)
case('O02 real output, exit 1', 'REJECTED', validate_orders, 1, orders_out, data)
case('O03 one order row missing', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'].pop()))
case('O04 one order row missing but runs still says 120', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'].pop(7)))
case('O05 one order duplicated in place of another', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'].__setitem__(1, d['results'][0])))
case('O06 one order row has double=True', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'][5].update(double=True)))
case('O07 a double approval hidden behind double=False (A1 approved and a December approval listed)', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'][5].update(november_A1_approved=True, december_approved=['A1Y'])))
case('O08 top-level double count set to 1', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d.update(double=1)))
case('O09 summary line says double=1', 'REJECTED', validate_orders, 0, orders_out.replace('double=0', 'double=1'), data)
case('O10 summary line missing', 'REJECTED', validate_orders, 0, re.sub(r'(?m)^SUMMARY runs=.*$', '', orders_out), data)
case('O11 an order from an unknown family in place of a real one', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'][0].update(family='X+Yp+Yc+Q')))
case('O12 one order row given a permutation that is not of its family', 'REJECTED', validate_orders, 0, orders_out, alt(lambda d: d['results'][0].update(order=['X', 'X', 'Yc', 'Z'])))

w = max(len(c[0]) for c in cases); gaps = 0
for label, want, got, msg in cases:
    ok = want == got; gaps += not ok
    print('%-*s want=%-8s got=%-8s %s %s' % (w, label, want, got, 'ok ' if ok else 'GAP', msg))
print('cases', len(cases), '| agree', len(cases) - gaps, '| gaps', gaps)
sys.exit(1 if gaps else 0)
