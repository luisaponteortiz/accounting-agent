"""Adapt only Y05(a), as expressly authorized by CODEX_RE_CORRECTIONS_PROMPT.md."""
import difflib
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'exports/FABLE_RD_ACCEPTANCE/fable_rd_acceptance_probes.py'
ADAPTED=ROOT/'review/fable_rd_feed_contract_probes.py'
PART_A='    # (a) most recent target\n'
PART_B='    # (b) open target: the claimed row is an ordinary December row\n'
REPLACEMENT='''    # (a) D-026: the first pending claim stays active; a second target is contested.
    os_ = h.approved_locked_november()
    os_.intake(PREP2, packet('first', [sup('A1Y', '2026-12-03', '40.00', 'A1X'), rc('A1Y', '2026-12-03', '40.00')]))
    before = lifecycle(os_)
    result = os_.intake(PREP2, packet('retarget', [sup('A1Y', '2026-12-03', '40.00', 'A1W')]))
    after = lifecycle(os_)
    conflicts = [e for e in os_.export(PREP)['accounting_events'] if e['code'] == 'SOURCE_CLAIM_CONFLICT_RECORDED' and e['item_key'] == K('A1Y')]
    good &= check('(a) the second target is recorded once and changes the control state', result['changed'] and len(conflicts) == 1)
    good &= check('(a) the second claim changes no binding, move or link', all(before[t] == after[t] for t in ('bindings', 'moves', 'links')))
    os_.intake(PREP2, packet('old-target', [tx('A1X', '2026-12-02', '40.00'), rc('A1X', '2026-12-02', '40.00')]))
    good &= check('(a) the first claim still links when its target arrives', (K('A1X'), K('A1Y')) in links(os_))
    os_.intake(PREP2, packet('new-target', [sup('A1W', '2026-12-02', '40.00', 'A1'), rc('A1W', '2026-12-02', '40.00')])); prep(os_)
    y = gov(os_, K('A1Y'), '2026-12')
    good &= check('(a) the contested target is not applied and the row stays blocked in December', (K('A1W'), K('A1Y')) not in links(os_) and y is not None and 'SOURCE_CLAIM_CONFLICT' in y['blockers'] and not y['eligible'] and K('A1Y') not in held_under(os_))
'''

def adapted_text():
    text=ORIGINAL.read_text();a=text.index(PART_A,text.index("@probe('Y05'"));b=text.index(PART_B,a)
    return text[:a]+REPLACEMENT+text[b:]

if __name__=='__main__':
    new=adapted_text()
    if '--check' in sys.argv:
        assert ADAPTED.read_text()==new,'Y05 adapter differs from its declared part-(a)-only change'
    else:
        ADAPTED.write_text(new)
        patch=''.join(difflib.unified_diff(ORIGINAL.read_text().splitlines(True),new.splitlines(True),fromfile=str(ORIGINAL.relative_to(ROOT)),tofile=str(ADAPTED.relative_to(ROOT))))
        (ROOT/'docs/corrections_re/Y05-contract.patch').write_text(patch)
    print('Y05(a) contract adaptation checked; all bytes outside part (a) unchanged.')
