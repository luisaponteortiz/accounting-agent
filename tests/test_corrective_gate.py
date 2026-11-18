import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class CorrectiveGate(unittest.TestCase):
    def test_independent_N01_through_N07(self):
        result=subprocess.run([sys.executable,str(ROOT/'review/batch2_verification_probes.py'),str(ROOT)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for n in range(1,8):self.assertRegex(result.stdout,r'(?m)^N%02d\s+OK\s'%n)
        self.assertNotIn('VERDICT: ERROR',result.stdout)
