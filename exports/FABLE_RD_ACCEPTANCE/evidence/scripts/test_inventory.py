import ast, sys, os, hashlib, json
def methods(root):
    out = {}
    td = os.path.join(root, 'tests')
    for f in sorted(os.listdir(td)):
        if not (f.startswith('test_') and f.endswith('.py')): continue
        src = open(os.path.join(td, f)).read(); tree = ast.parse(src)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for n in node.body:
                    if isinstance(n, (ast.FunctionDef,)) and n.name.startswith('test'):
                        seg = ast.get_source_segment(src, n)
                        decos = [ast.get_source_segment(src, d) for d in n.decorator_list]
                        out[(f, node.name, n.name)] = (hashlib.sha256(seg.encode()).hexdigest(), decos)
    return out
b = methods(sys.argv[1]); n = methods(sys.argv[2])
print('baseline methods', len(b), '| new methods', len(n))
print('baseline methods missing in new:', [k for k in b if k not in n])
print('baseline methods whose body changed:', [k for k in b if k in n and n[k][0] != b[k][0]])
added = [k for k in n if k not in b]
from collections import Counter
print('added methods', len(added), dict(Counter(k[0] for k in added)))
for k in added: print('   +', k[0], k[2])
import re
skips = []
for root in (sys.argv[2],):
    td = os.path.join(root, 'tests')
    for f in sorted(os.listdir(td)):
        if f.endswith('.py'):
            s = open(os.path.join(td, f)).read()
            for m in re.finditer(r'skip|expectedFailure|SkipTest', s): skips.append((f, s[max(0, m.start()-40):m.end()+40].replace('\n', ' ')))
print('skip/expectedFailure mentions in new tests:', skips)
# earlier test files byte comparison
td_b, td_n = os.path.join(sys.argv[1], 'tests'), os.path.join(sys.argv[2], 'tests')
for dp, _, fs in os.walk(td_b):
    for f in fs:
        pb = os.path.join(dp, f); pn = os.path.join(td_n, os.path.relpath(pb, td_b))
        if not os.path.exists(pn): print('REMOVED test file', pb); continue
        A, B = open(pb, 'rb').read(), open(pn, 'rb').read()
        if A != B: print('changed earlier test file:', os.path.relpath(pb, td_b), '| baseline bytes are a prefix of the new file:', B.startswith(A), '| appended bytes:', len(B) - len(A))
