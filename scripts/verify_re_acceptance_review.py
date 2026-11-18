"""RF gate: exact unmodified RE probes and all 480 stepwise delivery orders."""
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
IDS=('C2a','C2b','C2c','C2d','C2f','C2e','C7a','C7b','C7c','C7d','C8a','C8b','C8c','C9a','C9b','C9c','C9d','C9e','C9f','C9g','C9h')
NOTES={'C9c','C9g'}
FAMILIES={'older-claim+newer-claim':('P','B','Q7','Q6cP','Q8cB'),'older-resent-with-claim':('P','Q7','Q6','Q6cP','Z'),'two-claims+revision':('P','B','QcB','QcP','Qr'),'late-row-target':('L','B','QcL','QcB','Qr')}

def validate_probes(code,stdout):
    parts=stdout.split('\nSUMMARY\n')
    wanted={pid:'NOTE' if pid in NOTES else 'OK' for pid in IDS}
    if code or len(parts)!=2:raise ValueError('RF probes require exit 0 and one summary')
    lines=parts[1].strip().splitlines()
    rows=[re.fullmatch(r'\s*(\S+)\s+\S+\s+(OK|NOTE|WEAK|ERROR)\s*',line) for line in lines[:-2]]
    if (len(lines)!=23 or lines[-2].strip() or lines[-1]!='21 probes: 19 OK, 2 NOTE, 0 WEAK, 0 ERROR'
        or any(row is None for row in rows) or [r[1] for r in rows]!=list(IDS)
        or {r[1]:r[2] for r in rows}!=wanted):
        raise ValueError('RF probes require exactly 19 OK and only C9c/C9g NOTE, with all 21 identities')

def validate_orders(code,stdout,data):
    wanted=[(name,order) for name,family in FAMILIES.items() for order in itertools.permutations(family)]
    rows=data.get('results',[])
    if (code or data.get('runs')!=480 or data.get('double')!=0 or data.get('released')!=0
        or len(rows)!=480 or [(r.get('family'),tuple(r.get('order',[]))) for r in rows]!=wanted
        or any(r.get('double_at_steps')!=[] or r.get('released_at_steps')!=[] or r.get('audit_ok') is not True for r in rows)):
        raise ValueError('RF orders require all exact 480 orders, zero double/released/audit failures, exit 0')
    try:
        lines=['%-24s %-22s single no-release final_Q=%s held=%s' % (r['family'],' '.join(r['order']),r['final_Q_blockers'],[k.split(':')[-1] for k in r['final_held']]) for r in rows]
        early=sum(1 for r in rows if r['approved_before_target_known_at_steps'])
        expected='\n'.join(lines)+'\n\nSUMMARY runs=480 double=0 released_without_authority=0 audit_failures=0 approved_before_target_known=%d\n'%early
    except (KeyError,TypeError) as exc:raise ValueError('Incomplete RF order record') from exc
    if stdout!=expected:raise ValueError('RF order stdout or summary differs from the exact validated orders')

def run(args):
    r=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True)
    print(r.stdout,end='',flush=True);print(r.stderr,end='',file=sys.stderr,flush=True);return r

def main():
    r=run(['exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py',str(ROOT)]);validate_probes(r.returncode,r.stdout)
    with tempfile.TemporaryDirectory(prefix='aaos-rf-orders-') as tmp:
        path=Path(tmp)/'orders.json'
        r=run(['exports/FABLE_RE_ACCEPTANCE/fable_re_step_search.py',str(ROOT),'--json',str(path)])
        validate_orders(r.returncode,r.stdout,json.loads(path.read_text()))
    print('PASS: RF exact 21-probe/480-order developer gate; independent acceptance pending; no readiness authority.')

if __name__=='__main__':main()
