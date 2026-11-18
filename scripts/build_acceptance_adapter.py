"""Explicit RA-04 statement-acceptance setup; independent verdicts stay intact."""
import ast
import difflib
from pathlib import Path

root=Path(__file__).resolve().parents[1]
original=root/'exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py'
before=original.read_text();s=before
helper='''def accept_statement_revision(os_, key, period='2026-11'):
    """Positive fixture only: assert the hold, then obtain explicit human acceptance."""
    a=gov(os_,key,period)
    assert a is not None and 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'], brief(a)
    assert any(r.get('source_kind')=='statement' for r in a['payload']['data']['evidence_revisions']), 'Statement revision must be disclosed'
    result=dispose(os_,key,'EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',period=period)
    assert result[0]=='ok',result
    run(os_,'card_preparation',period)


'''
s=s.replace('def lines_of(a):',helper+'def lines_of(a):')
replacements=[
 ("os_.intake(PREP, packet('b2', gone + [stmt(rows[:4])])); run(os_, 'card_preparation')", "os_.intake(PREP, packet('b2', gone + [stmt(rows[:4])])); run(os_, 'card_preparation'); accept_statement_revision(os_,CARD+':A1'); accept_statement_revision(os_,CARD+':A2')"),
 ("os_.intake(PREP, packet('dec2', more[2:] + [stmt(more, DEC, opening='100.00')])); both()", "os_.intake(PREP, packet('dec2', more[2:] + [stmt(more, DEC, opening='100.00')])); both(); accept_statement_revision(os_,CARD+':M3','2026-12')"),
 ("    run(os_, 'card_preparation')\n    for k in ('A1', 'A2', 'A3'):", "    run(os_, 'card_preparation')\n    for item in ('A1','A2','A3'):accept_statement_revision(os_,CARD+':'+item)\n    for k in ('A1', 'A2', 'A3'):"),
 ("os_.intake(PREP, packet('void-d1', gone + [stmt(rows[2:])])); run(os_, 'card_preparation')", "os_.intake(PREP, packet('void-d1', gone + [stmt(rows[2:])])); run(os_, 'card_preparation'); accept_statement_revision(os_,CARD+':D2')"),
]
for old,new in replacements:
    assert s.count(old)==1,old
    s=s.replace(old,new)
s='# RA-04 positive-setup adaptation; original independent file remains unchanged.\n'+s
def probes(text):
    return {d.args[0].value:n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) for d in n.decorator_list if isinstance(d,ast.Call) and getattr(d.func,'id',None)=='probe'}
old,new=probes(before),probes(s)
assert old.keys()==new.keys()
for key in old:
    for kind in (ast.Return,ast.Assign):
        extract=lambda fn:[ast.dump(n,include_attributes=False) for n in ast.walk(fn) if isinstance(n,kind)]
        assert extract(old[key])==extract(new[key]),(key,kind.__name__)
target=root/'review/fable_rv_acceptance_probes.py';target.write_text(s)
(root/'docs/acceptance_ra/acceptance-probe-adaptations.patch').write_text(''.join(difflib.unified_diff(before.splitlines(keepends=True),s.splitlines(keepends=True),fromfile=str(original.relative_to(root)),tofile=str(target.relative_to(root)))))
print('Adapted positive statement acceptance in A03/A05/A17/X09; all 24 original returns and assignments preserved.')
