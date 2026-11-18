"""Exact RE gate, authorized adaptation boundaries and immutable inputs."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest
from scripts.verify_rd_feed_review import IDS,FAMILIES,validate_probes,validate_orders
from scripts.build_feed_contract_adapter import ORIGINAL,ADAPTED,PART_A,PART_B,adapted_text
ROOT=Path(__file__).resolve().parents[1]

class REReviewGate(unittest.TestCase):
    def test_all_authorized_probes_and_336_orders(self):
        r=subprocess.run([sys.executable,str(ROOT/'scripts/verify_rd_feed_review.py')],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_rejects_nonzero_missing_duplicate_unknown_changed_or_extra_verdicts(self):
        good='\nSUMMARY\n'+''.join('  %s RE OK\n'%pid for pid in IDS)
        validate_probes(0,good)
        for code,text in ((1,good),(0,good.replace('  Y01 RE OK\n','')),(0,good+'  Y01 RE OK\n'),(0,good+'  Z99 RE OK\n'),(0,good.replace('E02 RE OK','E02 RE NOTE')),(0,good.replace('E03 RE OK','E03 RE WEAK')),(0,good.replace('Y01','Z99'))):
            with self.subTest(code=code,text=text),self.assertRaises(ValueError):validate_probes(code,text)
        data={'runs':336,'double':0,'results':[{'family':'+'.join(f),'order':list(order),'double':False,'november_A1_approved':True,'december_approved':[]} for f in FAMILIES for order in itertools.permutations(f)]}
        text='SUMMARY runs=336 double=0 finalized_silently=0\n';validate_orders(0,text,data)
        missing=copy.deepcopy(data);missing['results'].pop()
        duplicate=copy.deepcopy(data);duplicate['results'][1]=duplicate['results'][0]
        double=copy.deepcopy(data);double['results'][0]['december_approved']=['A1Y']
        for code,output,d in ((1,text,data),(0,text,missing),(0,text,duplicate),(0,text,double),(0,text.replace('double=0','double=1'),data)):
            with self.subTest(code=code),self.assertRaises(ValueError):validate_orders(code,output,d)
    def test_only_Y05_part_a_is_adapted(self):
        original=ORIGINAL.read_text();adapted=ADAPTED.read_text();self.assertEqual(adapted,adapted_text())
        a=original.index(PART_A,original.index("@probe('Y05'"));b=original.index(PART_B,a)
        self.assertTrue(adapted.startswith(original[:a]));self.assertTrue(adapted.endswith(original[b:]))
    def test_all_protected_inputs_unchanged_and_contract_exact(self):
        for n,h in json.loads((ROOT/'docs/corrections_re/input-checksums.json').read_text()).items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        contract='**Scope.**'+(ROOT/'CODEX_RE_CORRECTIONS_PROMPT.md').read_text().split('**Scope.**',1)[1].split('\n\nClauses 1,',1)[0]
        self.assertIn(contract,(ROOT/'DECISIONS.md').read_text())
