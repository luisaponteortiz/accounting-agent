"""The normal suite runs the probes; the long search belongs only to rf-gate."""
import copy
import itertools
import json
from pathlib import Path
import subprocess
import sys
import unittest
from scripts.verify_re_acceptance_review import IDS,NOTES,FAMILIES,validate_probes,validate_orders
ROOT=Path(__file__).resolve().parents[1]

class RFReviewGate(unittest.TestCase):
    def test_all_21_unmodified_RE_probes(self):
        r=subprocess.run([sys.executable,str(ROOT/'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'),str(ROOT)],capture_output=True,text=True)
        validate_probes(r.returncode,r.stdout)
    def test_probe_validator_refuses_all_contract_faults(self):
        good='\nSUMMARY\n'+''.join('  %s clause %s\n'%(pid,'NOTE' if pid in NOTES else 'OK') for pid in IDS)+'\n21 probes: 19 OK, 2 NOTE, 0 WEAK, 0 ERROR\n'
        validate_probes(0,good)
        faults=[(1,good),(0,good.replace('  C2a clause OK\n','')),(0,good.replace('  C2b clause OK','  C2a clause OK')),(0,good+'  C99 clause OK\n'),(0,good.replace('C2a','C99')),(0,good.replace('C9c clause NOTE','C9c clause OK')),(0,good.replace('C2a clause OK','C2a clause NOTE')),(0,good.replace('C2d clause OK','C2d clause WEAK')),(0,good.replace('19 OK','20 OK')),(0,good.replace('\nSUMMARY\n','\nSUMMARY\n\nSUMMARY\n'))]
        for code,stdout in faults:
            with self.subTest(code=code,stdout=stdout),self.assertRaises(ValueError):validate_probes(code,stdout)
    def test_order_validator_refuses_all_contract_faults(self):
        rows=[{'family':name,'order':list(order),'double_at_steps':[],'released_at_steps':[],'audit_ok':True,'final_Q_blockers':None,'final_held':[],'approved_before_target_known_at_steps':[]} for name,f in FAMILIES.items() for order in itertools.permutations(f)]
        data={'runs':480,'double':0,'released':0,'results':rows}
        good=''.join('%-24s %-22s single no-release final_Q=None held=[]\n'%(r['family'],' '.join(r['order'])) for r in rows)+'\nSUMMARY runs=480 double=0 released_without_authority=0 audit_failures=0 approved_before_target_known=0\n'
        validate_orders(0,good,data)
        mutations=[]
        for mode in ('missing','duplicate','extra','unknown','double','released','audit','runs','summary-double','summary-release'):
            d=copy.deepcopy(data);text=good
            if mode=='missing':d['results'].pop()
            elif mode=='duplicate':d['results'][1]=d['results'][0]
            elif mode=='extra':d['results'].append(d['results'][0])
            elif mode=='unknown':d['results'][0]['family']='unknown'
            elif mode=='double':d['results'][0]['double_at_steps']=[2]
            elif mode=='released':d['results'][0]['released_at_steps']=[[2,['Q']]]
            elif mode=='audit':d['results'][0]['audit_ok']=False
            elif mode=='runs':d['runs']=479
            elif mode=='summary-double':text=text.replace('double=0','double=1')
            elif mode=='summary-release':text=text.replace('released_without_authority=0','released_without_authority=1')
            mutations.append((0,text,d))
        mutations.extend([(1,good,data),(0,good.replace('runs=480','runs=479'),data),(0,good+good.splitlines()[0]+'\n',data),(0,'\n'.join(good.splitlines()[1:])+'\n',data)])
        for code,stdout,d in mutations:
            with self.subTest(code=code),self.assertRaises(ValueError):validate_orders(code,stdout,d)
