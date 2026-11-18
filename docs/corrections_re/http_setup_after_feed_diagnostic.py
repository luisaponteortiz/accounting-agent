"""Observe retained HTTP setup after the feed unit class; do not change its deadline."""
import json
from pathlib import Path
import sys,time,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tests.test_feed_contract import FeedContract
from tests.test_http import HTTPCase
from accounting_agent.demo import actor
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(FeedContract))
assert result.wasSuccessful()
try:
    HTTPCase.setUpClass();print('HTTP setup passed')
except Exception as exc:
    print('HTTP setup error:',type(exc).__name__,str(exc))
    print('Worker error:',HTTPCase.server.worker_error,'alive:',HTTPCase.server.worker_thread.is_alive())
    for delay in (0,1):
        if delay:time.sleep(delay)
        print('State after additional seconds:',delay)
        for r in HTTPCase.os.state(actor())['runs']:
            print(json.dumps({'workflow':r['workflow'],'status':r['status'],'steps':r['steps']}))
    raise
finally:
    HTTPCase.tearDownClass()
