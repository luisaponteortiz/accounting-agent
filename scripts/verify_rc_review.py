"""Enforce the unchanged RC acceptance contract and every bounded delivery order."""
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {pid: 'OK' for pid in (
    'Q01', 'Q02', 'Q02i', 'Q03', 'X01', 'X01b', 'X01c', 'X01d',
    'X02', 'X03', 'X04', 'X05', 'X06', 'X07', 'X09')}
EXPECTED['X08'] = 'NOTE'
FAMILIES = [('X', 'Yp', 'Yc', 'Z'), ('X', 'Yc', 'Z', 'V'), ('X', 'Yp', 'Yc', 'V'),
            ('X', 'Yc', 'Yr', 'Z'), ('X', 'Yp', 'Yc', 'Yr')]


def validate_probes(returncode, stdout):
    rows = re.findall(r'(?m)^(\S+)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s*$', stdout)
    if returncode != 0 or len(rows) != 16 or dict(rows) != EXPECTED:
        raise ValueError('RD gate requires exit 0, exact 16 ids, 15 OK and X08 NOTE only')


def validate_orders(returncode, stdout, data):
    wanted = {('+'.join(family), order) for family in FAMILIES for order in itertools.permutations(family)}
    rows = data.get('results', [])
    actual = {(row['family'], tuple(row['order'])) for row in rows}
    summaries = re.findall(r'(?m)^SUMMARY runs=(\d+) double=(\d+) finalized_silently=(\d+)\s*$', stdout)
    if (returncode != 0 or summaries != [('120', '0', '0')] or data.get('runs') != 120
            or data.get('double') != 0 or len(rows) != 120 or actual != wanted
            or any(row['double'] or (row['november_A1_approved'] and row['december_approved']) for row in rows)):
        raise ValueError('RD gate requires exit 0 and all exact 120 delivery orders with zero double approval')


def main():
    probe = subprocess.run([sys.executable, str(ROOT/'exports/FABLE_RC_ACCEPTANCE/fable_rc_acceptance_probes.py'), str(ROOT)], capture_output=True, text=True)
    print(probe.stdout, end=''); print(probe.stderr, end='', file=sys.stderr)
    validate_probes(probe.returncode, probe.stdout)
    with tempfile.TemporaryDirectory(prefix='aaos-rd-gate-') as tmp:
        path = Path(tmp)/'orders.json'
        orders = subprocess.run([sys.executable, str(ROOT/'exports/FABLE_RC_ACCEPTANCE/fable_rc_order_search.py'), str(ROOT), '--json', str(path)], capture_output=True, text=True)
        print(orders.stdout, end=''); print(orders.stderr, end='', file=sys.stderr)
        validate_orders(orders.returncode, orders.stdout, json.loads(path.read_text()))
    print('PASS: exact RC/RD probe and 120-order contracts (developer execution; independent RD acceptance pending).')


if __name__ == '__main__':
    main()
