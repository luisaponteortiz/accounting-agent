"""Supplied RE probe/order gate; the whole-contract boundary is reported separately."""
import itertools
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
IDS=('Y01','Y02','Y03','Y04','Y06','E01','E02','E03','E03c','E04','E05','E06')
FAMILIES=(('X','Yp','Yc','Yr','Z'),('X','Yp','Yc','Z','V'),('X','B','Yb','Yc'),('X','Y5','Y4c','Z'),('X','Yc','Yt','Yp'),('X','Yc','Yt','Z'))

def validate_probes(code,stdout,ids=IDS):
    summary=stdout.split('\nSUMMARY\n')
    rows=re.findall(r'(?m)^\s*(\S+)\s+\S+\s+(OK|WEAK|ERROR|NOTE)\s*$',summary[-1])
    if code or len(summary)!=2 or len(rows)!=len(ids) or dict(rows)!={pid:'OK' for pid in ids}:raise ValueError('RE gate requires exactly the authorized probe IDs, all OK, exit 0')

def validate_orders(code,stdout,data):
    wanted={('+'.join(f),order) for f in FAMILIES for order in itertools.permutations(f)}
    rows=data.get('results',[])
    actual={(r['family'],tuple(r['order'])) for r in rows}
    if (code or re.findall(r'(?m)^SUMMARY runs=(\d+) double=(\d+) finalized_silently=(\d+)\s*$',stdout)!=[('336','0','0')]
        or data.get('runs')!=336 or data.get('double')!=0 or len(rows)!=336 or actual!=wanted
        or any(r['double'] or (r['november_A1_approved'] and r['december_approved']) for r in rows)):
        raise ValueError('RE gate requires every exact 336 order, all six families, zero double approval, exit 0')

def run(args):
    r=subprocess.run([sys.executable]+args,cwd=ROOT,capture_output=True,text=True)
    print(r.stdout,end='',flush=True);print(r.stderr,end='',file=sys.stderr,flush=True)
    return r

def main():
    from build_feed_contract_adapter import ADAPTED,adapted_text
    assert ADAPTED.read_text()==adapted_text(),'Only Y05(a) may differ from the independent script'
    r=run(['exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py',str(ROOT)]+list(IDS));validate_probes(r.returncode,r.stdout)
    r=run(['review/fable_rd_feed_contract_probes.py',str(ROOT),'Y05']);validate_probes(r.returncode,r.stdout,('Y05',))
    with tempfile.TemporaryDirectory(prefix='aaos-re-orders-') as tmp:
        path=Path(tmp)/'orders.json'
        r=run(['exports/FABLE_RD_ACCEPTANCE/fable_rd_order_search.py',str(ROOT),'--json',str(path)])
        validate_orders(r.returncode,r.stdout,json.loads(path.read_text()))
    print('PASS: supplied RE probe/336-order gate; whole D-026 compliance and independent RE acceptance are not established.')

if __name__=='__main__':main()
