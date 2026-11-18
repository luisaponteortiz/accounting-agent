"""Independent RA review inputs stay unchanged and all controls execute."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
ALL=('A04','A03','A01','A02','A05','A06','A07','A08','A09','A10','A11','A12','A13','A14','A17','X01','X09','X12k','X12s','X15','U1','U4','M1','M2')
ADAPTED={'A03','A05','A17','X09'}

class AcceptanceGate(unittest.TestCase):
    def execute(self,path,ids=()):
        result=subprocess.run([sys.executable,str(ROOT/path),str(ROOT),*ids],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        rows=dict(re.findall(r'(?m)^(A\d+|X\w+|U\d+|M\d+)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s',result.stdout))
        self.assertEqual(set(rows),set(ids or ALL),result.stdout)
        for identifier,status in rows.items():self.assertIn(status,('OK','NOTE') if identifier=='U4' else ('OK',),result.stdout)

    def test_independent_review_inputs_and_four_frozen_archives_unchanged(self):
        for name,expected in json.loads((ROOT/'docs/acceptance_ra/input-checksums.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)

    def test_packager_refuses_to_overwrite_frozen_submission(self):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/build_review_bundle.py'),'FABLE_REVERIFICATION_CORRECTIONS'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Frozen review submission cannot be overwritten',result.stderr)
        expected=json.loads((ROOT/'docs/acceptance_ra/input-checksums.json').read_text())['exports/FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip']
        self.assertEqual(hashlib.sha256((ROOT/'exports/FABLE_REVERIFICATION_CORRECTIONS_REVIEW_BUNDLE.zip').read_bytes()).hexdigest(),expected)

    def test_unmodified_compatible_independent_acceptance_probes(self):
        self.execute('exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py',[key for key in ALL if key not in ADAPTED])

    def test_all_24_independent_assertions_with_explicit_statement_acceptance(self):
        self.execute('review/fable_rv_acceptance_probes.py')

    def test_original_acceptance_verdicts_and_assignments_are_preserved(self):
        def criteria(path):
            result={}
            for fn in ast.walk(ast.parse((ROOT/path).read_text())):
                if not isinstance(fn,ast.FunctionDef):continue
                identifiers=[d.args[0].value for d in fn.decorator_list if isinstance(d,ast.Call) and getattr(d.func,'id',None)=='probe']
                if identifiers:result[identifiers[0]]=[ast.dump(n,include_attributes=False) for n in ast.walk(fn) if isinstance(n,(ast.Return,ast.Assign))]
            return result
        self.assertEqual(criteria('exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py'),criteria('review/fable_rv_acceptance_probes.py'))
