"""Require the exact unchanged RB acceptance probe set and its two policy notes."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {pid: 'OK' for pid in (
    'N01a', 'N01b', 'N01c', 'N01d', 'N01e', 'N01f', 'N01g',
    'N02a', 'N02b', 'N03a', 'N03b', 'N03c', 'N04a', 'N04b', 'N04c', 'N04d')}
EXPECTED.update(N02c='NOTE', N04e='NOTE')


def validate_result(returncode, stdout):
    rows = re.findall(r'(?m)^(N\d+[a-z]?)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s*$', stdout)
    if returncode != 0 or len(rows) != 18 or dict(rows) != EXPECTED:
        raise ValueError('RB review gate requires exit 0, exact 18 ids, 16 OK and N02c/N04e NOTE only')


def main():
    result = subprocess.run([sys.executable, str(ROOT/'exports/FABLE_RB_ACCEPTANCE/fable_rb_acceptance_probes.py'), str(ROOT)], capture_output=True, text=True)
    print(result.stdout, end='')
    print(result.stderr, end='', file=sys.stderr)
    try:
        validate_result(result.returncode, result.stdout)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print('PASS: exact RB acceptance probe contract (developer execution; independent acceptance pending).')


if __name__ == '__main__':
    main()
