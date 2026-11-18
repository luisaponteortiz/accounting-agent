"""Strict RC checkpoint gate and immutable independent-input checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.verify_rb_review import EXPECTED, validate_result

ROOT = Path(__file__).resolve().parents[1]


class RCReviewGate(unittest.TestCase):
    def test_all_18_unmodified_probes_meet_exact_contract(self):
        result = subprocess.run([sys.executable, str(ROOT/'scripts/verify_rb_review.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_gate_refuses_nonzero_missing_duplicate_or_changed_verdicts(self):
        good = '\n'.join('%s RB %s' % row for row in EXPECTED.items())+'\n'
        validate_result(0, good)
        for code, output in ((1, good), (0, good.replace('N01b RB OK\n', '')),
                             (0, good+'N01a RB OK\n'), (0, good.replace('N01b RB OK', 'N01b RB NOTE')),
                             (0, good.replace('N02c RB NOTE', 'N02c RB OK'))):
            with self.subTest(code=code, output=output), self.assertRaises(ValueError):
                validate_result(code, output)

    def test_supplied_inputs_and_prior_archives_are_byte_identical(self):
        for name, expected in json.loads((ROOT/'docs/corrections_rc/input-checksums.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
