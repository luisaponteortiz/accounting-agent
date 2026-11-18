"""Build a reviewable setup-only adaptation; never modify Fable's supplied file."""
import ast
import difflib
from pathlib import Path

root=Path(__file__).resolve().parents[1]
original=root/'exports/FABLE_REVERIFICATION/fable_reverification_probes.py'
target=root/'review/fable_reverification_probes.py'
s=original.read_text();before=s
lines=s.splitlines(keepends=True);offset=[0]
for line in lines:offset.append(offset[-1]+len(line))
edits=[]
for fn in ast.walk(ast.parse(s)):
    if not isinstance(fn,ast.FunctionDef):continue
    identifiers=[d.args[0].value for d in fn.decorator_list if isinstance(d,ast.Call) and getattr(d.func,'id',None)=='probe']
    if not identifiers or identifiers[0]=='RT10b':continue
    for call in ast.walk(fn):
        if isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and call.func.attr=='create_mandate' and len(call.args)>7:
            freshness=call.args[7]
            if isinstance(freshness,ast.Dict) and not freshness.keys:
                edits.append((offset[freshness.lineno-1]+freshness.col_offset,offset[freshness.end_lineno-1]+freshness.end_col_offset,"{'none':'Explicit fixed-evidence baseline for the original '+%r+' scenario; freshness rejection is tested in RT10b'}"%identifiers[0]))
for start,end,replacement in sorted(edits,reverse=True):s=s[:start]+replacement+s[end:]
helper='''def accept_revised_evidence(os_, key):
    """RV-12 positive setup: an explicitly granted non-supplier accepts the revision."""
    a=gov(os_,key)
    assert 'EVIDENCE_REVISED_REQUIRES_REVIEW' in a['blockers'], 'Revised evidence must be held first'
    assert a['payload']['data']['evidence_revisions'], 'Revision history must be disclosed'
    result=dispose(os_,key,'EVIDENCE_REVISED_REQUIRES_REVIEW','revised_evidence_accepted',who=DISP)
    assert result[0]=='ok',result


'''
s=s.replace('def dispose(os_, key,',helper+'def dispose(os_, key,')
s=s.replace("a['payload']['data']['evidence'] if evidence is None else evidence", "a['payload']['data']['evidence']+(a['payload']['data'].get('duplicate_evidence',[]) if choice=='distinct_purchases' else []) if evidence is None else evidence")
s=s.replace("if e['source_key'] in (CARD + ':' + k, 'receipt-' + k)]", "if e['source_key'] in (CARD + ':' + k, 'receipt-' + k)]+gov(os_,CARD+':'+k)['payload']['data'].get('duplicate_evidence',[])")
rt14b_setup="""        dispose(os_, CARD + ':' + k, 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own)      # charge and its own receipt only
    run(os_, 'card_preparation'); print('    D1 after disposition:', brief(gov(os_, CARD + ':D1')))
"""
rt14b_asserted_setup="""        initial_result = dispose(os_, CARD + ':' + k, 'POSSIBLE_DUPLICATE', 'distinct_purchases', evidence=own)  # own and candidate receipts; no statement
        print('    initial distinct-purchases disposition', k + ':', initial_result)
        assert initial_result[0] == 'ok', ('Initial distinct-purchases disposition must succeed', k, initial_result)
    run(os_, 'card_preparation')
    initial_d1 = gov(os_, CARD + ':D1')
    assert initial_d1 is not None and initial_d1['eligible'], ('D1 must be eligible before D3 arrives', brief(initial_d1))
    print('    D1 after disposition:', brief(initial_d1))
"""
assert s.count(rt14b_setup)==1,'Original RT14b positive setup changed'
s=s.replace(rt14b_setup,rt14b_asserted_setup)
s=s.replace("os_.intake(PREP, packet('s7', newer + [stmt(newer)])); run(os_, 'card_preparation'); a1b =", "os_.intake(PREP, packet('s7', newer + [stmt(newer)])); run(os_, 'card_preparation'); accept_revised_evidence(os_,CARD+':A1'); run(os_,'card_preparation'); a1b =")
s=s.replace("os_.intake(PREP, packet('teaching-corrections', [fixed_rc, fixed_j])); run(os_, 'card_preparation'); run(os_, 'journal_preparation')", "os_.intake(PREP, packet('teaching-corrections', [fixed_rc, fixed_j])); run(os_, 'card_preparation'); run(os_, 'journal_preparation'); accept_revised_evidence(os_,CARD+':TX-009'); run(os_,'card_preparation')")
rt18="    run(os_, 'card_preparation')\n    a1 = gov(os_, CARD + ':A1'); review(os_, REV, a1, 'approve'); review(os_, REV2, a1, 'reject')"
assert s.count(rt18)==1
s=s.replace(rt18,"    run(os_, 'card_preparation'); accept_revised_evidence(os_,CARD+':A1'); run(os_,'card_preparation')\n    a1 = gov(os_, CARD + ':A1'); review(os_, REV, a1, 'approve'); review(os_, REV2, a1, 'reject')")
s='''# Setup-only compatibility copy for RV-11/RV-12/RV-15; original input is unchanged.
# See docs/reverification/probe-adaptations.md and reverification-probe-adaptations.patch.
'''+s
ast.parse(s)
# Original gate expressions and verdict returns are preserved; additions strengthen setup.
def criteria(text):
    result=[]
    for fn in ast.walk(ast.parse(text)):
        if isinstance(fn,ast.FunctionDef) and fn.decorator_list:
            for n in ast.walk(fn):
                if isinstance(n,ast.Return):result.append(ast.dump(n,include_attributes=False))
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('ok','base','held','bad','held_while_locked') for t in n.targets):result.append(ast.dump(n,include_attributes=False))
    return result
assert criteria(before)==criteria(s),'Original control criteria changed'
target.write_text(s)
patch=root/'docs/reverification/reverification-probe-adaptations.patch'
patch.write_text(''.join(difflib.unified_diff(before.splitlines(keepends=True),s.splitlines(keepends=True),fromfile='exports/FABLE_REVERIFICATION/fable_reverification_probes.py',tofile='review/fable_reverification_probes.py')))
print('Adapted',len(edits),'positive mandate setups; positive duplicate evidence and revised-document acceptance; RT14b explicitly asserts both initial dispositions and D1 eligibility; all original verdict/gate expressions preserved.')
