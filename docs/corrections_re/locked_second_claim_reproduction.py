"""D-029: preserve frozen approval, block the incoming version until reopen."""
from pathlib import Path
import importlib.util,sys
root=Path(__file__).resolve().parents[2];path=root/'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py'
spec=importlib.util.spec_from_file_location('locked_claim_probe',path);p=importlib.util.module_from_spec(spec);sys.argv=[str(path),str(root)];spec.loader.exec_module(p);f=p.h
try:
    os_=f.approved_locked_november();key=f.CARD+':A1'
    for i,target in enumerate(('UNKNOWN0','UNKNOWN1')):
        result=os_.intake(f.PREP2,f.packet('locked-claim-'+str(i),[f.sup('A1','2026-11-03','40.00',target)]))
        assert result['changed']
        assert p.approved(os_,key,'2026-11')
        print('Claim',target,': frozen approval preserved')
    conflict=os_.export(f.PREP)['source_claim_conflicts'][key]
    assert conflict['conflicted'] and len(conflict['targets'])==2
    assert any(k==key and period=='2026-11' and code=='LATE_ACTIVITY_IN_LOCKED_PERIOD' for k,period,code in f.exceptions_of(os_))
    assert os_.verify_audit(f.PREP)
    print('Incoming version held; both claims recorded; audit valid')
    os_.reopen_period(f.PADMIN,'2026-11','D-029 fictional authorized reopen')
    f.run(os_,'card_preparation','2026-11',f.PREP2)
    current=f.gov(os_,key,'2026-11')
    assert current is not None and 'SOURCE_CLAIM_CONFLICT' in current['blockers']
    assert current['review_status']!='approve'
    assert os_.verify_audit(f.PREP)
    print('After reopen: contested blocker retained, no automatic approval; audit valid')
    print('PASS: owner D-029 clarification')
finally:f.TMP.cleanup()
