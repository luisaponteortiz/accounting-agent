"""Run the independent RD inputs unchanged and fault-test the gate contract."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.verify_rc_review import EXPECTED, FAMILIES, validate_probes, validate_orders

ROOT = Path(__file__).resolve().parents[1]


class RDReviewGate(unittest.TestCase):
    def test_unmodified_16_probes_and_120_orders_meet_exact_contracts(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/verify_rc_review.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_gate_rejects_probe_error_missing_duplicate_unknown_and_changed_note(self):
        good = '\n'.join('%s RC %s' % row for row in EXPECTED.items())+'\n'
        validate_probes(0, good)
        for code, output in ((1, good), (0, good.replace('X01 RC OK\n', '')),
                             (0, good+'X01 RC OK\n'), (0, good.replace('X01 RC OK', 'X99 RC OK')),
                             (0, good.replace('X08 RC NOTE', 'X08 RC OK')),
                             (0, good.replace('X01 RC OK', 'X01 RC ERROR'))):
            with self.subTest(code=code, output=output), self.assertRaises(ValueError):
                validate_probes(code, output)

    def test_gate_rejects_missing_duplicate_or_double_order_and_false_summary(self):
        data = {'runs': 120, 'double': 0, 'results': [
            {'family': '+'.join(f), 'order': list(o), 'double': False,
             'november_A1_approved': True, 'december_approved': []}
            for f in FAMILIES for o in itertools.permutations(f)]}
        good = 'SUMMARY runs=120 double=0 finalized_silently=0\n'
        validate_orders(0, good, data)
        missing = copy.deepcopy(data); missing['results'].pop()
        duplicate = copy.deepcopy(data); duplicate['results'][1] = duplicate['results'][0]
        double = copy.deepcopy(data); double['results'][0]['december_approved'] = ['A1Y']
        for code, output, mutated in ((1, good, data), (0, good, missing), (0, good, duplicate),
                                      (0, good, double), (0, good.replace('double=0', 'double=1'), data)):
            with self.subTest(code=code, output=output), self.assertRaises(ValueError):
                validate_orders(code, output, mutated)

    def test_all_protected_inputs_remain_byte_identical(self):
        for name, expected in json.loads((ROOT/'docs/corrections_rd/input-checksums.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
