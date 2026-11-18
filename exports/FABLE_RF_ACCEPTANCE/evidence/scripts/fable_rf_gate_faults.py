"""Fable fault injection for the RF gate validators (scripts/verify_re_acceptance_review.py).

usage: fable_rf_gate_faults.py <project-root> <probes-stdout> <family-stdout-dir>

The base inputs are REAL outputs of the unmodified scripts on the delivered source: the stdout of the 21
probes, and the stdout and --json results of the four search families (run one family per process and
joined here in the script's own family order, with the summary line the script prints for the whole run).
Every case changes one thing and says what a sound gate should do. Nothing in the project is written.
"""
import copy, itertools, json, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from scripts.verify_re_acceptance_review import FAMILIES, IDS, validate_orders, validate_probes  # noqa: E402
probes = Path(sys.argv[2]).read_text(); fam_dir = Path(sys.argv[3])
rows = []; lines = []
for name in FAMILIES:
    data = json.loads((fam_dir / ('re-step-search-%s.results.json' % name)).read_text()); rows += data['results']
    out = (fam_dir / ('re-step-search-%s.stdout.txt' % name)).read_text().split('\n\nSUMMARY')[0]
    lines += out.splitlines()
early = sum(1 for r in rows if r['approved_before_target_known_at_steps'])
DATA = {'runs': len(rows), 'double': sum(1 for r in rows if r['double_at_steps']), 'released': sum(1 for r in rows if r['released_at_steps']), 'results': rows}
OUT = '\n'.join(lines) + '\n\nSUMMARY runs=%d double=%d released_without_authority=%d audit_failures=%d approved_before_target_known=%d\n' % (
    len(rows), DATA['double'], DATA['released'], sum(1 for r in rows if not r['audit_ok']), early)
cases = []


def case(label, want, fn, *args):
    try:
        fn(*args); got = 'ACCEPTED'; msg = ''
    except Exception as exc:
        got = 'REJECTED'; msg = type(exc).__name__ + ': ' + str(exc)[:90]
    cases.append((label, want, got))
    print('M%02d %-108s want=%s got=%s %s %s' % (len(cases), label, want, got, 'ok ' if want == got else 'GAP', msg))


def row(pid):
    return re.search(r'(?m)^  %s +\S+ +\S+$' % re.escape(pid), probes.split('\nSUMMARY\n')[1]).group(0)


def sub(old, new, count=1):
    head, tail = probes.split('\nSUMMARY\n'); assert old in tail, old
    return head + '\nSUMMARY\n' + tail.replace(old, new, count)


# ---------------- probes
case('probes control: real output, exit 0', 'ACCEPTED', validate_probes, 0, probes)
case('probes: real output but exit 1', 'REJECTED', validate_probes, 1, probes)
for pid in ('C2a', 'C2d', 'C2f', 'C7a', 'C9h'):
    case('probes: %s reported WEAK (count line left as it is)' % pid, 'REJECTED', validate_probes, 0, sub(row(pid), row(pid).replace(' OK', ' WEAK')))
case('probes: C2d WEAK and the count line adjusted to 18 OK, 1 WEAK', 'REJECTED', validate_probes, 0, sub(row('C2d'), row('C2d').replace(' OK', ' WEAK')).replace('19 OK, 2 NOTE, 0 WEAK', '18 OK, 2 NOTE, 1 WEAK'))
case('probes: C2f reported ERROR', 'REJECTED', validate_probes, 0, sub(row('C2f'), row('C2f').replace(' OK', ' ERROR')))
case('probes: C9c NOTE becomes OK', 'REJECTED', validate_probes, 0, sub(row('C9c'), row('C9c').replace('NOTE', 'OK')))
case('probes: C9g NOTE becomes OK and the count line says 20 OK, 1 NOTE', 'REJECTED', validate_probes, 0, sub(row('C9g'), row('C9g').replace('NOTE', 'OK')).replace('19 OK, 2 NOTE', '20 OK, 1 NOTE'))
case('probes: C2a OK becomes NOTE', 'REJECTED', validate_probes, 0, sub(row('C2a'), row('C2a').replace(' OK', ' NOTE')))
case('probes: C9h OK becomes NOTE (the RE checkpoint verdict)', 'REJECTED', validate_probes, 0, sub(row('C9h'), row('C9h').replace(' OK', ' NOTE')))
case('probes: C7b row missing', 'REJECTED', validate_probes, 0, sub(row('C7b') + '\n', ''))
case('probes: C7b row missing and the count line says 20 probes: 18 OK', 'REJECTED', validate_probes, 0, sub(row('C7b') + '\n', '').replace('21 probes: 19 OK', '20 probes: 18 OK'))
case('probes: C7b row duplicated', 'REJECTED', validate_probes, 0, sub(row('C7b') + '\n', row('C7b') + '\n' + row('C7b') + '\n'))
case('probes: C7b replaced by a second C7a row', 'REJECTED', validate_probes, 0, sub(row('C7b'), row('C7a')))
case('probes: unknown probe C99 added', 'REJECTED', validate_probes, 0, sub(row('C9h') + '\n', row('C9h') + '\n' + row('C9h').replace('C9h', 'C99') + '\n'))
case('probes: C8a renamed C8z', 'REJECTED', validate_probes, 0, sub(row('C8a'), row('C8a').replace('C8a', 'C8z')))
case('probes: two rows in swapped order', 'REJECTED', validate_probes, 0, sub(row('C2a') + '\n' + row('C2b'), row('C2b') + '\n' + row('C2a')))
case('probes: count line says 20 OK', 'REJECTED', validate_probes, 0, sub('19 OK', '20 OK'))
case('probes: summary block printed twice', 'REJECTED', validate_probes, 0, probes + '\nSUMMARY\n' + probes.split('\nSUMMARY\n')[1])
case('probes: no summary block', 'REJECTED', validate_probes, 0, probes.split('\nSUMMARY\n')[0])
case('probes: a line after the count line', 'REJECTED', validate_probes, 0, probes + 'WEAK elsewhere\n')
case('probes: empty output', 'REJECTED', validate_probes, 0, '')

# ---------------- orders
wanted = [(n, o) for n, f in FAMILIES.items() for o in itertools.permutations(f)]
case('orders control: real stdout and results, exit 0', 'ACCEPTED', validate_orders, 0, OUT, DATA)
case('orders: the joined real results are the exact 480 orders in the script order', 'ACCEPTED', lambda: None if [(r['family'], tuple(r['order'])) for r in rows] == wanted and len(rows) == 480 else (_ for _ in ()).throw(ValueError('not the 480')))
case('orders: exit 1', 'REJECTED', validate_orders, 1, OUT, DATA)


def mutate(fn, text=None):
    d = copy.deepcopy(DATA); fn(d); return 0, (OUT if text is None else text), d


case('orders: runs says 479', 'REJECTED', validate_orders, *mutate(lambda d: d.update(runs=479)))
case('orders: double says 1', 'REJECTED', validate_orders, *mutate(lambda d: d.update(double=1)))
case('orders: released says 1', 'REJECTED', validate_orders, *mutate(lambda d: d.update(released=1)))
case('orders: last order missing', 'REJECTED', validate_orders, *mutate(lambda d: d['results'].pop()))
case('orders: one order missing and runs says 479', 'REJECTED', validate_orders, *mutate(lambda d: (d['results'].pop(100), d.update(runs=479))))
case('orders: second order replaced by a copy of the first', 'REJECTED', validate_orders, *mutate(lambda d: d['results'].__setitem__(1, copy.deepcopy(d['results'][0]))))
case('orders: one extra order', 'REJECTED', validate_orders, *mutate(lambda d: d['results'].append(copy.deepcopy(d['results'][0]))))
case('orders: a family renamed', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][130].update(family='unknown')))
case('orders: two deliveries swapped inside one order', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][130].update(order=d['results'][130]['order'][::-1])))
case('orders: two orders swapped', 'REJECTED', validate_orders, *mutate(lambda d: d['results'].__setitem__(slice(0, 2), d['results'][1::-1])))
case('orders: one order has a double approval at step 3', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][150].update(double_at_steps=[3])))
case('orders: one order has a release at step 2', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][150].update(released_at_steps=[[2, ['Q']]])))
case('orders: one order has audit_ok False', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][150].update(audit_ok=False)))
case('orders: one order has no audit_ok field', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][150].pop('audit_ok')))
case('orders: one order has no double_at_steps field', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][150].pop('double_at_steps')))
case('orders: results clean, one stdout row says DOUBLE@[3]', 'REJECTED', validate_orders, 0, OUT.replace(' single ', ' DOUBLE@[3] ', 1), DATA)
case('orders: results clean, one stdout row says RELEASED', 'REJECTED', validate_orders, 0, OUT.replace(' no-release ', " RELEASED@[(2, ['Q'])] ", 1), DATA)
for field in ('runs=480', 'double=0', 'released_without_authority=0', 'audit_failures=0', 'approved_before_target_known=%d' % early):
    k, v = field.split('=')
    case('orders: summary line says %s=%d' % (k, int(v) + 1), 'REJECTED', validate_orders, 0, OUT.replace(field, '%s=%d' % (k, int(v) + 1)), DATA)
case('orders: one stdout row removed', 'REJECTED', validate_orders, 0, '\n'.join(OUT.splitlines()[1:]) + '\n', DATA)
case('orders: one stdout row repeated', 'REJECTED', validate_orders, 0, OUT.splitlines()[0] + '\n' + OUT, DATA)
case('orders: summary line missing', 'REJECTED', validate_orders, 0, OUT.split('\n\nSUMMARY')[0] + '\n', DATA)
case('orders: results changed after the run (final blockers of one order), stdout as printed', 'REJECTED', validate_orders, *mutate(lambda d: d['results'][7].update(final_Q_blockers=['EDITED'])))
case('orders: approved-before-target flag removed from one order in the results only', 'REJECTED' if early else 'ACCEPTED', validate_orders,
     *mutate(lambda d: next(r for r in d['results'] if r['approved_before_target_known_at_steps'] or not early).update(approved_before_target_known_at_steps=[])))
case('orders: empty results', 'REJECTED', validate_orders, 0, OUT, {})

agree = sum(1 for c in cases if c[1] == c[2])
print('cases %d | agree %d | gaps %d' % (len(cases), agree, len(cases) - agree))
print('real base: 21 probe rows; %d orders; early=%d' % (len(rows), early))
sys.exit(0 if agree == len(cases) else 1)
