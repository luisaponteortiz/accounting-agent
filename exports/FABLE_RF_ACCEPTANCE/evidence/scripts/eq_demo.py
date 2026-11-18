"""Demo data (the same seed the HTTP tests use), single-threaded: report computation inside and outside a transaction.
Run under fable_rf_equivalence.py, which compares every call with the full computation."""
import sys, tempfile
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from accounting_agent.demo import SCOPE, actor, seed
from accounting_agent.service import AccountingOS
with tempfile.TemporaryDirectory() as t:
    os_ = AccountingOS(Path(t) / 'eq.sqlite3', [SCOPE]); seed(os_); os_.drain(actor('worker'))
    st = os_.state(actor())
    periods = sorted({r['period_id'] for r in st['runs'] if r['period_id']})
    print('demo runs:', [(r['workflow'], r['period_id'], r['status']) for r in st['runs']])
    for period in periods:
        db = os_.store.connect()
        try:
            a = os_.period_outcomes(db, actor(), period)          # autocommit reader
            print('autocommit period', period, 'items', len(a['items']), 'in_transaction', db.in_transaction)
        finally:
            db.close()
        with os_.store.transaction() as db:
            b = os_.period_outcomes(db, actor(), period)          # inside a transaction
            print('transaction period', period, 'items', len(b['items']), 'in_transaction', db.in_transaction)
        print('same result inside and outside a transaction:', a == b)
    for _ in range(3):
        os_.state(actor())
