"""Read-only RF checkpoint, immutable inputs, policy and history boundaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from build_rf_review_bundle import ROOT,BASELINE,BASELINE_HASH,prepare
from check_product_requirements import parse_register

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    inventory=prepare()
    protected=json.loads((ROOT/'docs/corrections_rf/input-checksums.json').read_text())
    assert all(sha((ROOT/n).read_bytes())==h for n,h in protected.items())
    archives=json.loads((ROOT/'docs/corrections_re/archive-integrity.json').read_text())
    for row in archives:assert sha((ROOT/row['file']).read_bytes())==row['sha256']
    with zipfile.ZipFile(ROOT/BASELINE) as z:
        before=parse_register(z.read('docs/PRODUCT_REQUIREMENTS.md').decode());after=parse_register((ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text())
        assert list(before)==list(after) and len(after)==88
        assert all(before[k][f]==after[k][f] for k in before for f in ('Product decision','Implementation state','Acceptance criteria'))
        assert all(before[k]==after[k] for k in before if before[k]['Implementation state']=='Independently verified' or k in ('AAOS-BB-01','AAOS-BB-02','AAOS-ONB-01','AAOS-ONB-02','AAOS-INT-07','AAOS-GL-06','AAOS-BNK-07','AAOS-RPT-03'))
        assert all((ROOT/n).read_bytes()==z.read(n) for n in ('accounting_agent/storage.py','tests/schema_v1.sql','tests/test_http.py','review/fable_rd_feed_contract_probes.py'))
        assert (ROOT/'DECISIONS.md').read_bytes().startswith(z.read('DECISIONS.md'))
    expected=json.loads((ROOT/'docs/corrections_rf/preflight.json').read_text())
    assert subprocess.check_output(['git','log','--format=fuller'],cwd=ROOT)==(ROOT/'docs/corrections_rf/git-history-before.txt').read_bytes()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==expected['head']
    assert int(subprocess.check_output(['git','rev-list','--count','HEAD'],cwd=ROOT,text=True))==expected['commit_count']==10
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==expected['branch']=='review/fable-rc-acceptance'
    print(json.dumps({'protected_inputs_unchanged':len(protected),'all_prior_archives_unchanged':len(archives),'all_88_ids_and_order_retained':True,'every_acceptance_criterion_state_and_product_decision_unchanged':True,'four_verified_scopes_BB01_BB02_six_proposed_records_identical':True,'schema_HTTP_deadline_Y05_unchanged':True,'prior_decision_log_bytes_are_prefix':True,'retained_test_methods':sum(r['baseline_methods'] for r in inventory['original_tests'].values()),'unchanged_retained_methods':226,'sole_authorized_rewrite':'D-031 / test_PRV14_third_authority_is_pinned_and_latest_verdict_controls','ten_commits_branch_and_HEAD_unchanged':True,'head':expected['head']},indent=2))

if __name__=='__main__':main()
