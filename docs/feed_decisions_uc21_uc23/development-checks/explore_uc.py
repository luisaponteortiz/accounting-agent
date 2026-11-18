"""Observe current behaviour for UC-21 and UC-22 scenarios (read-only against the given project root)."""
import importlib.util,sys,io,contextlib,json
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
path=ROOT/'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
spec=importlib.util.spec_from_file_location('fx',path);p=importlib.util.module_from_spec(spec)
argv=sys.argv;sys.argv=[str(path),str(ROOT)]
with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(p)
sys.argv=argv
K=p.K
def quiet(fn,*a,**k):
    with contextlib.redirect_stdout(io.StringIO()):return fn(*a,**k)
def delta(before,after):return {k:len(after[k])-len(before[k]) for k in after if len(after[k])!=len(before[k])}
def retire(order):
    o=quiet(p.base)
    kw={} if order is None else {'as_of':order}
    qrows=[p.q(None,**kw),p.rc('Q','2026-12-03','40.00')]
    quiet(p.send,o,'q',qrows)
    zr=[p.sup('Z','2026-12-05','40.00','Q'),p.rc('Z','2026-12-05','40.00')]
    quiet(p.send,o,'z',zr+[p.stmt(zr,p.DEC,opening='100.00')]);quiet(p.prep,o)
    quiet(p.clear_and_approve,o,'Z')
    return o,qrows
print('ROW_TABLES',p.ROW_TABLES)
for order in (7,'2026-12-03T10:00:00+00:00',None):
    o,qrows=retire(order);b=p.rows_of(o);hd=p.head(o,'Q')
    r=quiet(p.send,o,'again',qrows);a=p.rows_of(o)
    print('UC21 order',order,'| Q head removed before',hd['removed'],'| result',r[1] if r[0]=='ok' else r,'| delta',delta(b,a),'| Q head after',p.head(o,'Q')['removed'],'| Z approved',p.approved(o,K('Z'),'2026-12'))
    b=p.rows_of(o);r=quiet(p.send,o,'again-receipt-only',[qrows[1]]);print('   receipt only:',r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)))
    b=p.rows_of(o);r=quiet(p.send,o,'again-row-only',[qrows[0]]);print('   row only:',r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)))
# withdrawn replacement
o,qrows=retire(7)
r=quiet(p.send,o,'z-gone',[dict(p.sup('Z','2026-12-05','40.00','Q'),tombstone=True,removal_reason='voided',as_of=9)] if False else [dict(p.tx('Z','2026-12-05','40.00'),tombstone=True,removal_reason='voided')])
print('withdraw Z:',r[1] if r[0]=='ok' else r,'| Z head',p.head(o,'Z'),'| Q head',p.head(o,'Q'))
b=p.rows_of(o);r=quiet(p.send,o,'q-after-z-gone',qrows);print('   identical Q after Z withdrawn:',r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)),'| Q head removed',p.head(o,'Q')['removed'])
# UC-22
for gov_order in (7,'2026-12-03T10:00:00+00:00'):
    o=quiet(p.base);quiet(p.send,o,'q7',p.q_rows(as_of=gov_order));quiet(p.prep,o);hd=p.head(o,'Q')
    for n in range(3):
        b=p.rows_of(o);r=quiet(p.send,o,'plain-%d'%n,[p.q(amount='41.00')]);print('UC22 gov',gov_order,'repeat',n,r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)),'head same',p.head(o,'Q')==hd)
    b=p.rows_of(o);r=quiet(p.send,o,'rc-plain',[p.rc('Q','2026-12-03','41.00')]);print('   receipt unordered diff:',r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)))
    b=p.rows_of(o);r=quiet(p.send,o,'rc-plain2',[p.rc('Q','2026-12-03','41.00')]);print('   receipt unordered diff again:',r[1] if r[0]=='ok' else r,delta(b,p.rows_of(o)))
print('state keys',sorted(o.state(p.PREP).keys()))
print('source_exceptions',[(e['source_key'],e['reason']) for e in o.state(p.PREP)['source_exceptions']])
