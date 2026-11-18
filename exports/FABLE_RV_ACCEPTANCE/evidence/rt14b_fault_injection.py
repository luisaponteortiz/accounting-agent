"""Independent fault injection for the strengthened RT14b in review/fable_reverification_probes.py.
Test-only substitutions of the probe file's own helper functions; no accounting record is edited.
Usage: python3 rt14b_fault_injection.py <project-root>"""
import contextlib, importlib.util, io, re, sys
root = sys.argv[1]
path = root + '/review/fable_reverification_probes.py'

def case(label, patcher):
    sys.argv = [path, root, 'RT14b']
    spec = importlib.util.spec_from_file_location('adapted_probes_under_fault', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    seen = {'d3': False}
    make_tx = m.tx
    def tx(sid, *a, **k):
        if sid == 'D3':
            seen['d3'] = True
        return make_tx(sid, *a, **k)
    m.tx = tx
    patcher(m)
    buf = io.StringIO(); code = None
    with contextlib.redirect_stdout(buf):
        try:
            m.main()
        except SystemExit as exc:
            code = exc.code
    out = buf.getvalue()
    verdict = re.search(r'(?m)^RT14b\s+\S+\s+(\w+)', out).group(1)
    reason = [l.strip() for l in out.splitlines() if 'AssertionError' in l]
    states = [l.strip() for l in out.splitlines() if 'D1 after disposition' in l or 'after a third identical charge' in l]
    print('%-34s runner verdict=%-5s exit=%s third charge constructed=%s' % (label, verdict, code, seen['d3']))
    for l in reason[-1:] + states:
        print('      ', l[:230])
    return verdict, code, seen['d3']

def refuse(item):
    def patcher(m):
        real = m.dispose
        def dispose(os_, key, *a, **k):
            if key == m.CARD + ':' + item:
                return ('refused', 400, 'Deliberate refusal injected by the reviewer')
            return real(os_, key, *a, **k)
        m.dispose = dispose
    return patcher

def ineligible(m):
    real = m.gov
    def gov(os_, key, *a, **k):
        art = real(os_, key, *a, **k)
        return dict(art, eligible=False) if key == m.CARD + ':D1' and art and art['eligible'] else art
    m.gov = gov

r = [case('initial D1 disposition refused', refuse('D1')), case('initial D2 disposition refused', refuse('D2')),
     case('D1 ineligible before third charge', ineligible), case('no fault (valid path)', lambda m: None)]
ok = all(v == ('ERROR', 1, False) for v in r[:3]) and r[3] == ('OK', 0, True)
print('fault injection result:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
