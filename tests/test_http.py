"""Black-box HTTP acceptance tests against the actual server and durable worker."""
import copy
import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from accounting_agent.core import ControlError
from accounting_agent.demo import SCOPE, actor, seed, load
from accounting_agent.http import DemoServer
from accounting_agent.service import AccountingOS


class HTTPCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.os=AccountingOS(Path(cls.temp.name)/'http.sqlite3',[SCOPE])
        seed(cls.os)
        cls.server=DemoServer(('127.0.0.1',0),cls.os)
        cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.tokens={a.role:t for t,a in cls.server.tokens.items()}
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if all(r['status']=='prepared_with_exceptions' for r in cls.os.state(actor())['runs']):break
            time.sleep(.02)
        else:raise AssertionError('Background worker failed to finish')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(2);cls.temp.cleanup()

    def request(self,path,body=None,role='preparer',headers=None,method=None):
        base={'Authorization':'Bearer '+self.tokens.get(role,'invalid')}
        if body is not None:base['Content-Type']='application/json'
        base.update(headers or {})
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        try:
            conn.request(method or ('POST' if body is not None else 'GET'),path,json.dumps(body) if body is not None else None,base)
            response=conn.getresponse();data=response.read()
            return response.status,dict(response.getheaders()),json.loads(data) if response.getheader('Content-Type')=='application/json' else data.decode()
        finally:conn.close()

    def test_health_and_real_worker_results(self):
        status,_,health=self.request('/health',role='none');self.assertEqual(status,200);self.assertEqual(health['ledger'],'unconnected')
        status,_,state=self.request('/api/state');self.assertEqual(status,200);self.assertEqual(len(state['artifacts']),21)
        self.assertTrue(all(s['status']=='complete' for r in state['runs'] for s in r['steps']))

    def test_session_is_explicitly_synthetic_and_authorization_required(self):
        status,_,session=self.request('/api/session',role='none');self.assertEqual(status,200);self.assertTrue(session['synthetic'])
        self.assertEqual(self.request('/api/state',role='none')[0],401)

    def test_reviewer_cannot_intake_or_prepare(self):
        self.assertEqual(self.request('/api/run',{'workflow':'card_preparation'},role='reviewer')[0],403)
        self.assertEqual(self.request('/api/intake',load('fixtures/late_receipt.json'),role='reviewer')[0],403)

    def test_approval_and_export_black_box(self):
        _,_,state=self.request('/api/state')
        clean=next(a for a in state['artifacts'] if a['item_key']=='demo_card_001:TX-001')
        body={'artifact_id':clean['id'],'artifact_hash':clean['hash'],'fingerprint':clean['fingerprint'],'decision':'approve','reason':'Synthetic HTTP acceptance review'}
        self.assertEqual(self.request('/api/review',body)[0],403)
        self.assertEqual(self.request('/api/review',body,role='reviewer')[0],200)
        status,headers,package=self.request('/api/export')
        self.assertEqual(status,200);self.assertIn('attachment',headers['Content-Disposition'])
        found=next(a for a in package['artifacts'] if a['id']==clean['id'])
        self.assertEqual(found['review_status'],'approve')
        self.assertEqual(package['external']['posting'],'disabled')
        self.assertEqual(len([a for a in package['artifacts'] if a['kind']=='card_proposal']),11)
        self.assertEqual(len([a for a in package['artifacts'] if a['blockers']]),12)

    def test_blocked_artifact_approval_fails(self):
        _,_,state=self.request('/api/state');a=next(a for a in state['artifacts'] if a['item_key']=='J-002')
        status,_,_=self.request('/api/review',{'artifact_id':a['id'],'artifact_hash':a['hash'],'fingerprint':a['fingerprint'],'decision':'approve','reason':'This must fail'},role='reviewer')
        self.assertEqual(status,409)

    def test_host_origin_and_scope_override_defenses(self):
        self.assertEqual(self.request('/api/session',headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.request('/api/state',headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.request('/api/session',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
        self.assertEqual(self.request('/api/state?client_id=another-client')[0],400)
        for path in ('/api/clients/other','/api/executive','/api/crm','/api/post','/../service.py'):
            with self.subTest(path=path):self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.request('/api/run',{'workflow':'card_preparation','client_id':'other'})[0],400)

    def test_period_operations_require_independent_human_and_preserve_scope(self):
        body={'period_id':'2026-12','start':'2026-12-01','end':'2026-12-31','reason':'Fictional HTTP period administration'}
        self.assertEqual(self.request('/api/periods/open',body)[0],403)
        self.assertEqual(self.request('/api/periods/open',body,role='reviewer')[0],200)
        _,_,state=self.request('/api/state')
        self.assertEqual({p['period_id'] for p in state['periods']},{'2026-11','2026-12'})
        lock={'period_id':'2026-12','reason':'Fictional HTTP lock'}
        self.assertEqual(self.request('/api/periods/lock',lock,role='reviewer')[0],200)
        self.assertEqual(self.request('/api/run',{'workflow':'journal_preparation','period_id':'2026-12'})[0],409)
        self.assertEqual(self.request('/api/periods/reopen',lock,role='reviewer')[0],200)
        self.assertEqual(self.request('/api/periods/open',dict(body,client_id='other'),role='reviewer')[0],400)

    def test_loopback_only_and_static_assets_with_csp(self):
        with self.assertRaises(ControlError):DemoServer(('0.0.0.0',0),self.os)
        status,headers,html=self.request('/')
        self.assertEqual(status,200);self.assertIn('SYNTHETIC LOCAL DEMONSTRATION',html)
        self.assertIn("default-src 'self'",headers['Content-Security-Policy'])
        self.assertEqual(self.request('/app.js')[0],200);self.assertEqual(self.request('/style.css')[0],200)

    def test_invalid_api_requests_have_no_side_effects(self):
        count=len(self.os.state(actor())['runs'])
        self.assertEqual(self.request('/api/run',{'workflow':'ap.unknown'})[0],403)
        self.assertEqual(self.request('/api/run',[])[0],400)
        self.assertEqual(self.request('/api/run',{'workflow':'card_preparation'},headers={'Content-Type':'text/plain'})[0],415)
        self.assertEqual(len(self.os.state(actor())['runs']),count)

    def test_mandate_proposal_requires_independent_activation(self):
        body={'workflows':['journal_preparation'],'starts':'2026-11-15T00:00:00+00:00','ends':'2026-11-19T00:00:00+00:00','interval_seconds':86400,'max_occurrences':3,'period_rule':{'kind':'fixed','period_id':'2026-11'},'freshness':{'journal':'occurrence_start'}}
        status,_,response=self.request('/api/mandates',body);self.assertEqual(status,200)
        mid=response['mandate_id'];m=next(m for m in self.os.state(actor())['mandates'] if m['id']==mid);self.assertFalse(m['active'])
        self.assertEqual(self.request('/api/mandates/approve',{'mandate_id':mid,'reason':'Self activation forbidden'})[0],403)
        self.assertEqual(self.request('/api/mandates/approve',{'mandate_id':mid,'reason':'Independent fictional activation'},role='reviewer')[0],200)

    def test_package_and_disposition_routes_enforce_controls(self):
        body={'period_id':'2026-11','workflow':'journal_preparation','reason':'Fictional route test','acknowledgement':'J-002 remains blocked; handover only'}
        self.assertEqual(self.request('/api/packages/finalize',body)[0],403)
        status,_,response=self.request('/api/packages/finalize',body,role='reviewer');self.assertEqual(status,200)
        self.assertTrue(any(p['id']==response['package_id'] for p in self.os.export(actor())['packages']))
        a=next(a for a in self.os.state(actor())['artifacts'] if a['item_key']=='J-002')
        disp={'workflow':'journal_preparation','period_id':'2026-11','item_key':'J-002','code':'UNBALANCED_JOURNAL','choice':'ignore','payload':{},'evidence':a['payload']['data']['evidence'],'reason':'Cannot override balance'}
        self.assertEqual(self.request('/api/dispositions',disp)[0],403)
        self.assertEqual(self.request('/api/dispositions',disp,role='reviewer')[0],400)


if __name__=='__main__':unittest.main()
