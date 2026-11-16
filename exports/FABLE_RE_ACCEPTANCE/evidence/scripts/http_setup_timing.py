"""Time the unchanged HTTP test class setup (seed + background worker until prepared). Read-only on the project."""
import sys, time, tempfile, threading
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
from accounting_agent.demo import SCOPE, actor, seed
from accounting_agent.http import DemoServer
from accounting_agent.service import AccountingOS
out = []
for i in range(int(sys.argv[2]) if len(sys.argv) > 2 else 3):
    temp = tempfile.TemporaryDirectory()
    os_ = AccountingOS(Path(temp.name) / 'http.sqlite3', [SCOPE])
    seed(os_)
    server = DemoServer(('127.0.0.1', 0), os_)
    t = threading.Thread(target=server.serve_forever, daemon=True); t.start()
    start = time.monotonic(); done = None
    while time.monotonic() < start + 60:
        if all(r['status'] == 'prepared_with_exceptions' for r in os_.state(actor())['runs']):
            done = time.monotonic() - start; break
        time.sleep(.02)
    out.append(done)
    server.shutdown(); server.server_close(); t.join(2); temp.cleanup()
print(root.name, 'seconds until the worker finished (test deadline is 5.0):', ['%.2f' % x if x is not None else 'not within 60' for x in out])
