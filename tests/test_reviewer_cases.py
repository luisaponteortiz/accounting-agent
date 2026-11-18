"""The independent 60-case runner is part of the ordinary test gate."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReviewerCases(unittest.TestCase):
    def test_independent_validation_runner(self):
        result = subprocess.run([sys.executable, str(ROOT/'review/run_fable_validation_cases.py'), str(ROOT), str(ROOT/'review/FABLE_VALIDATION_CASES.json'), '--batch2-gate'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotRegex(result.stdout, r'(?m)^(FAIL|UNEXPECTED|DEFERRED-LEAK)\s')
