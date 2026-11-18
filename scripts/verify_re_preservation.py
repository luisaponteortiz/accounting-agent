"""Read-only checks of the RE pass's preserved checkpoint and authorized test edit."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from build_re_review_bundle import BASELINE,BASELINE_HASH,test_methods
from check_product_requirements import parse_register
ROOT=Path(__file__).resolve().parents[1]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    assert sha((ROOT/BASELINE).read_bytes())==BASELINE_HASH
    protected=json.loads((ROOT/'docs/corrections_re/input-checksums.json').read_text())
    assert all(sha((ROOT/n).read_bytes())==h for n,h in protected.items())
    with zipfile.ZipFile(ROOT/BASELINE) as z:
        before=parse_register(z.read('docs/PRODUCT_REQUIREMENTS.md').decode());after=parse_register((ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text())
        assert list(before)==list(after) and len(after)==88
        assert all(before[k][f]==after[k][f] for k in before for f in ('Product decision','Implementation state'))
        changed={k for k in before if before[k]!=after[k]}
        assert changed=={'AAOS-GOV-02','AAOS-GOV-03','AAOS-BNK-03','AAOS-CTL-04'},changed
        assert all(before[k]==after[k] for k in before if before[k]['Implementation state']=='Independently verified' or k in ('AAOS-BB-01','AAOS-BB-02'))
        proposed=('AAOS-ONB-01','AAOS-ONB-02','AAOS-INT-07','AAOS-GL-06','AAOS-BNK-07','AAOS-RPT-03')
        assert all(before[k]==after[k] and after[k]['Product decision']=='Proposed' for k in proposed)
        assert all((ROOT/n).read_bytes()==z.read(n) for n in ('accounting_agent/storage.py','tests/schema_v1.sql'))
        assert (ROOT/'DECISIONS.md').read_bytes().startswith(z.read('DECISIONS.md'))
        baseline_methods=0;current_methods=0
        for n in z.namelist():
            if not n.startswith('tests/') or not n.endswith('.py'):continue
            old=z.read(n);new=(ROOT/n).read_bytes();baseline_methods+=len(test_methods(old))
            assert test_methods(old)<=test_methods(new)
            if n=='tests/test_product_requirements.py':assert new.startswith(old)
            elif n=='tests/test_review_corrections_rd.py':
                def masked(raw):
                    tree=ast.parse(raw)
                    nodes=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='test_RD02_latest_pending_target_wins_and_existing_link_is_not_replaced']
                    assert len(nodes)==1
                    node=nodes[0];lines=raw.splitlines(True)
                    return b''.join(lines[:node.lineno-1])+b'<AUTHORIZED METHOD>\n'+b''.join(lines[node.end_lineno:])
                assert masked(old)==masked(new)
            else:assert old==new,n
        current_methods=sum(len(test_methods(p.read_bytes())) for p in (ROOT/'tests').glob('*.py'))
        assert baseline_methods==205
    history=subprocess.check_output(['git','log','--format=fuller'],cwd=ROOT)
    assert history==(ROOT/'docs/corrections_re/git-history-before.txt').read_bytes()
    assert subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=ROOT,text=True).strip()=='8'
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='review/fable-rc-acceptance'
    print(json.dumps({'protected_inputs_unchanged':len(protected),'all_88_ids_and_order_retained':True,'product_decisions_changed':0,'implementation_states_changed':0,'changed_register_records':sorted(changed),'owner_confirmed_BB01_BB02_all_fields_identical':True,'all_four_verified_records_identical':True,'six_named_unratified_records_still_proposed_and_identical':True,'schema_files_unchanged':True,'prior_decision_log_bytes_are_prefix':True,'baseline_methods_retained':baseline_methods,'current_test_methods':current_methods,'only_authorized_earlier_method_rewritten':True,'branch_and_eight_commits_unchanged':True,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},indent=2))

if __name__=='__main__':main()
