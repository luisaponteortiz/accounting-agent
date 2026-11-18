"""Observation only (Fable RF review): time every unittest class setUp and write one JSON line per class.
Active only when FABLE_HTTP_SETUP_LOG is set. Changes no test, assertion, deadline or worker behaviour:
it reads the clock before and after the unmodified setUpClass, and notes when a thread is started inside it."""
import os
_LOG = os.environ.get('FABLE_HTTP_SETUP_LOG')
if _LOG:
    import json, threading, time
    import unittest.suite as _us
    _state = {'inside': None, 'thread_started': None}
    _thread_start = threading.Thread.start

    def _start(self, *a, **k):
        if _state['inside']:
            _state['thread_started'] = time.monotonic()
        return _thread_start(self, *a, **k)
    threading.Thread.start = _start
    _handle = _us.TestSuite._handleClassSetUp

    def _timed(self, test, result):
        cls = test.__class__
        if getattr(result, '_previousTestClass', None) is cls:
            return _handle(self, test, result)
        _state['inside'] = cls.__name__; _state['thread_started'] = None
        t0 = time.monotonic()
        try:
            return _handle(self, test, result)
        finally:
            t1 = time.monotonic()
            row = {'module': cls.__module__, 'class': cls.__name__, 'setup_seconds': round(t1 - t0, 6),
                   'seconds_from_last_thread_start_to_end_of_setup': None if _state['thread_started'] is None else round(t1 - _state['thread_started'], 6),
                   'setup_failed': bool(getattr(cls, '_classSetupFailed', False)), 'pid': os.getpid()}
            _state['inside'] = None
            try:
                with open(_LOG, 'a') as f:
                    f.write(json.dumps(row) + '\n')
            except OSError:
                pass
    _us.TestSuite._handleClassSetUp = _timed
