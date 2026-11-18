"""Keep Fable's immutable input and every current control in the normal gate."""
import hashlib
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
# These seven positive fixtures use contracts deliberately tightened by RV-11/12/15.
# Their ORIGINAL verdict expressions are retained in the reviewed compatibility copy.
CHANGED_SETUP={'RN02','RN03','RN07','RT12a','RT14a','RT14b','RT18','RG0'}
ALL=('RN01','RN02','RN02b','RN03','RN04','RN05','RN05b','RN06','RN07','RT09a','RT09b','RT09c','RT09d','RT11','RT12a','RT12b','RT12c','RT12d','RT10a','RT10b','RT13','RT13n','RT14a','RT14b','RT14c','RT14d','RT14e','RT14f','RT15','RT16','RT17','RT18','RT19a','RT19b','RG0')

class ReverificationGate(unittest.TestCase):
    def execute(self,path,ids=()):
        result=subprocess.run([sys.executable,str(ROOT/path),str(ROOT),*ids],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        statuses=dict(re.findall(r'(?m)^(RN\w+|RT\w+|RG0)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s',result.stdout))
        self.assertEqual(set(statuses),set(ids or ALL),result.stdout)
        self.assertTrue(all(v=='OK' for v in statuses.values()),result.stdout)

    def test_original_inputs_and_archives_unchanged(self):
        hashes=json.loads((ROOT/'docs/reverification/input-checksums.json').read_text())
        for name,expected in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),expected,name)

    def test_unmodified_independent_probes_with_unchanged_setup(self):
        self.execute('exports/FABLE_REVERIFICATION/fable_reverification_probes.py',[p for p in ALL if p not in CHANGED_SETUP])

    def test_all_independent_control_assertions_with_explicit_current_setup(self):
        self.execute('review/fable_reverification_probes.py')

    def rt14b_fixture(self):
        path=ROOT/'review/fable_reverification_probes.py'
        spec=importlib.util.spec_from_file_location('fable_rt14b_gate_fixture',path)
        module=importlib.util.module_from_spec(spec)
        with patch.object(sys,'argv',[str(path),str(ROOT)]):spec.loader.exec_module(module)
        self.addCleanup(module.TMP.cleanup)
        return module,next(fn for identifier,_,_,fn in module.PROBES if identifier=='RT14b')

    def test_RT14b_fails_when_either_initial_disposition_is_refused(self):
        fixture,probe=self.rt14b_fixture()
        original_dispose=fixture.dispose
        for key in ('D1','D2'):
            with self.subTest(refused_initial_item=key):
                def refuse_one(os_,item_key,*args,**kwargs):
                    if item_key==fixture.CARD+':'+key:return ('refused',400,'Deliberate positive-setup failure')
                    return original_dispose(os_,item_key,*args,**kwargs)
                with patch.object(fixture,'dispose',side_effect=refuse_one),redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(AssertionError,'Initial distinct-purchases disposition must succeed'):
                        probe()

    def test_RT14b_fails_when_initial_D1_is_ineligible(self):
        fixture,probe=self.rt14b_fixture()
        original_gov=fixture.gov
        def ineligible_d1(os_,item_key,*args,**kwargs):
            artifact=original_gov(os_,item_key,*args,**kwargs)
            if item_key==fixture.CARD+':D1' and artifact and artifact['eligible']:
                return dict(artifact,eligible=False)
            return artifact
        with patch.object(fixture,'gov',side_effect=ineligible_d1),redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(AssertionError,'D1 must be eligible before D3 arrives'):
                probe()
