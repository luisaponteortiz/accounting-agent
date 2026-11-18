"""Run Fable's latest 14 probes unchanged; none may remain a NOTE or failure."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]


class RAReviewGate(unittest.TestCase):
    def test_all_14_unmodified_independent_probes_report_OK(self):
        result=subprocess.run([sys.executable,str(ROOT/'exports/FABLE_RA_ACCEPTANCE/fable_ra_acceptance_probes.py'),str(ROOT)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        rows=dict(re.findall(r'(?m)^(R\d+[a-z]?)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s',result.stdout))
        self.assertEqual(set(rows),{'R01a','R01b','R01c','R01d','R03a','R03b','R04a','R04b','R04c','R02a','R02b','R05','R07','R08'})
        self.assertEqual(set(rows.values()),{'OK'},result.stdout)

    def test_returned_inputs_and_submitted_archives_remain_unchanged(self):
        for name,expected in json.loads((ROOT/'docs/corrections_rb/input-checksums.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)

    def test_combined_frozen_submission_cannot_be_overwritten(self):
        path=ROOT/'exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_BUNDLE.zip'
        before=hashlib.sha256(path.read_bytes()).hexdigest()
        result=subprocess.run([sys.executable,str(ROOT/'scripts/build_review_bundle.py'),'FABLE_RA_AND_PRODUCT_REQUIREMENTS'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Frozen review submission cannot be overwritten',result.stderr)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
