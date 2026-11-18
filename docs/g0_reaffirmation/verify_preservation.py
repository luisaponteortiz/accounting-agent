"""Read-only preservation check after recording the G0 re-affirmation (D-039); writes its findings to docs/g0_reaffirmation/."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve();E=ROOT/'docs/g0_reaffirmation'
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()
out={}
protected=json.loads((ROOT/'docs/corrections_rf/input-checksums.json').read_text())
bad=[n for n,h in protected.items() if not (ROOT/n).is_file() or sha(ROOT/n)!=h]
out['protected_inputs_of_the_rf_pass']={'count':len(protected),'unchanged':len(protected)-len(bad),'differences':bad}
archives=json.loads((ROOT/'docs/corrections_re/archive-integrity.json').read_text())
bad=[r['file'] for r in archives if sha(ROOT/r['file'])!=r['sha256']]
out['earlier_archives']={'count':len(archives),'unchanged':len(archives)-len(bad),'differences':bad}
fixed={'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip':'c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd',
       'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip':'343da96a13daecdbc5f8bd7c8d9c9ac265c7b1a9ebca97c478ac1be1a2583232',
       'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip':'4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae',
       'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip':'e0b0a49932ca4e4f7adf4c18f21202ea85b33219b08e3bc76038778c9178cf2a'}
out['rf_and_re_archives']={n:sha(ROOT/n)==h for n,h in fixed.items()}
# Every payload file of the delivered RF bundle against the working project.
changed=[];missing=[];members=0
with zipfile.ZipFile(ROOT/'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip') as z:
    for info in z.infolist():
        if info.is_dir():continue
        members+=1;p=ROOT/info.filename
        if not p.is_file():missing.append(info.filename);continue
        if hashlib.sha256(z.read(info)).hexdigest()!=sha(p):changed.append(info.filename)
out['delivered_rf_bundle_members_against_working_project']={'members':members,'identical':members-len(changed)-len(missing),'changed':sorted(changed),'not_in_working_project':sorted(missing)}
# Every file of the returned RF response against its working review-folder copy.
resp_changed=[];resp=0
with zipfile.ZipFile(ROOT/'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip') as z:
    names=[i for i in z.infolist() if not i.is_dir()]
    for info in names:
        resp+=1
        candidates=[ROOT/info.filename,ROOT/'exports'/info.filename,ROOT/'exports/FABLE_RF_ACCEPTANCE'/info.filename]
        data=hashlib.sha256(z.read(info)).hexdigest()
        if not any(c.is_file() and sha(c)==data for c in candidates):resp_changed.append(info.filename)
out['returned_rf_response_files_against_working_copies']={'files':resp,'identical':resp-len(resp_changed),'differences':resp_changed[:20]}
git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
out['git']={'branch':git('branch','--show-current'),'head':git('rev-parse','HEAD'),'commits':int(git('rev-list','--count','HEAD')),'staged':git('diff','--cached','--name-only').splitlines(),'tracked_modified':git('diff','--name-only').splitlines(),
            'history_identical_to_rf_preflight':subprocess.check_output(['git','log','--format=fuller'],cwd=ROOT)==(ROOT/'docs/corrections_rf/git-history-before.txt').read_bytes()}
sys.path.insert(0,str(ROOT))
from scripts.check_product_requirements import parse_register
with zipfile.ZipFile(ROOT/'exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip') as z:
    before=parse_register(z.read('docs/PRODUCT_REQUIREMENTS.md').decode());old_decisions=z.read('DECISIONS.md')
after=parse_register((ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text())
recorded=('AAOS-BNK-03','AAOS-CTL-04','AAOS-GOV-03')
out['register']={'ids_and_order_retained':list(before)==list(after),'records':len(after),
  'records_changed':sorted(k for k in before if before[k]!=after[k]),
  'fields_changed':{k:[f for f in before[k] if before[k][f]!=after[k][f]] for k in before if before[k]!=after[k]},
  'every_product_decision_and_acceptance_criterion_unchanged':all(before[k][f]==after[k][f] for k in before for f in ('Product decision','Acceptance criteria')),
  'implementation_states_changed':{k:[before[k]['Implementation state'],after[k]['Implementation state']] for k in before if before[k]['Implementation state']!=after[k]['Implementation state']},
  'four_earlier_verified_BB01_BB02_and_six_proposed_identical':all(before[k]==after[k] for k in ('AAOS-KNO-04','AAOS-CTL-01','AAOS-BNK-02','AAOS-CTL-09','AAOS-BB-01','AAOS-BB-02','AAOS-ONB-01','AAOS-ONB-02','AAOS-INT-07','AAOS-GL-06','AAOS-BNK-07','AAOS-RPT-03'))}
out['decision_log_rf_checkpoint_bytes_are_prefix']=(ROOT/'DECISIONS.md').read_bytes().startswith(old_decisions)
# New protected inventory: the earlier one plus the returned RF review and its delivery.
inventory=dict(protected)
extra=[p for p in sorted((ROOT/'exports/FABLE_RF_ACCEPTANCE').rglob('*')) if p.is_file()]
extra+=[ROOT/n for n in ('exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip','exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip.sha256','exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.REVIEW_MANIFEST.json','exports/FABLE_RF_AND_PRV_CORRECTIONS_PACKAGE_CHECK.json','exports/FABLE_RF_AND_PRV_CORRECTIONS_FINAL_VERIFICATION.json','exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip','exports/FABLE_RF_AND_PRV_CORRECTIONS_REVIEW_RESPONSE.zip.sha256','FABLE_RF_REVIEW_PROMPT.md','FABLE_RF_CORRECTIONS_HANDOFF.md','CODEX_RF_CORRECTIONS_PROMPT.md','HANDOFF_RF_CHECKPOINT_2026-11-17.md')]
added=0
for p in extra:
    n=str(p.relative_to(ROOT))
    if n not in inventory:inventory[n]=sha(p);added+=1
(E/'input-checksums.json').write_text(json.dumps(inventory,indent=1,sort_keys=True)+'\n')
out['new_protected_inventory']={'file':'docs/registration_rf/input-checksums.json','entries':len(inventory),'carried_from_rf_pass':len(protected),'added_for_the_returned_rf_review_and_delivery':added}
(E/'preservation.json').write_text(json.dumps(out,indent=1)+'\n')
print(json.dumps(out,indent=1))
