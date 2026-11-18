"""Observe HTTPCase setup inside unmodified unittest discovery; no deadline changes."""
import json
import sys
import time
import unittest

_original=unittest.TestSuite._handleClassSetUp

def _timed(self,test,result):
    cls=test.__class__
    if cls.__name__!='HTTPCase' or cls is getattr(result,'_previousTestClass',None):
        return _original(self,test,result)
    module=sys.modules['accounting_agent.http'];server_type=module.DemoServer
    init=server_type.__init__;worker_start=[];started=time.monotonic()
    def observe_init(server,*args,**kwargs):
        init(server,*args,**kwargs);worker_start.append(time.monotonic())
    server_type.__init__=observe_init
    try:return _original(self,test,result)
    finally:
        ended=time.monotonic();server_type.__init__=init
        print('RF_HTTP_SETUP '+json.dumps({'class':cls.__module__+'.'+cls.__name__,'total_seconds':round(ended-started,6),'worker_wait_seconds':round(ended-worker_start[0],6) if worker_start else None,'setup_failed':bool(getattr(cls,'_classSetupFailed',False))}),file=sys.stderr,flush=True)

unittest.TestSuite._handleClassSetUp=_timed
