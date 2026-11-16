import importlib.util, sys
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve(); sys.argv=[sys.argv[0],str(ROOT)]
spec=importlib.util.spec_from_file_location('rep',Path(__file__).with_name('fable_re_acceptance_probes.py')); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
globals().update({k:getattr(m,k) for k in dir(m) if not k.startswith('__')})
os_=base()
send(os_,'q',[q('P'),rc('Q','2026-12-03','40.00')])       # in-order claim on an unknown target
z=sup('Z','2026-12-05','40.00','Q')
send(os_,'z',[z,rc('Z','2026-12-05','40.00'),stmt([z],DEC,opening='100.00')]); prep(os_)
print('Q claims unknown P; Z replaces Q. Z before any disposition:',brief(gov(os_,K('Z'),'2026-12')),'| Q:',brief(gov(os_,K('Q'),'2026-12')))
a=clear_and_approve(os_,'Z'); print('after settlement_verified + independent review: Z',brief(a))
print('finalize December:',attempt(os_.finalize_package,FIN,'2026-12','card_preparation','Fictional'))
send(os_,'p',p_rows())
print('P (replacing locked A1) arrives -> Z approved now:',approved(os_,K('Z'),'2026-12'),'| held:',sorted(held_under(os_)))
