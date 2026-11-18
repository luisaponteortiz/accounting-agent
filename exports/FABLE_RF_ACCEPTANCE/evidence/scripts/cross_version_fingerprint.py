"""Observation only: what a database prepared by the RE checkpoint looks like when the RF checkpoint opens it.
usage: cross_version_fingerprint.py <project-root> <db-path> create|inspect
create  (run with the RE source): approved and locked November, an approved and finalized December row.
inspect (run with the RF source): open the same file read-mostly and report what the new code says, then deliver one unrelated row."""
import importlib.util, sys, json
from pathlib import Path
root = Path(sys.argv[1]).resolve(); db = Path(sys.argv[2]); mode = sys.argv[3]
path = root / 'exports/FABLE_RE_ACCEPTANCE/fable_re_acceptance_probes.py'
spec = importlib.util.spec_from_file_location('fable_re_probes', path); p = importlib.util.module_from_spec(spec)
argv = sys.argv; sys.argv = [str(path), str(root)]; spec.loader.exec_module(p); sys.argv = argv
h = p.h
from accounting_agent.service import AccountingOS
if mode == 'create':
    h.TMP.cleanup(); db.parent.mkdir(parents=True, exist_ok=True)
    class T: name = str(db.parent)
    h.TMP = T; h.COUNTER[0] = 0
    os_ = p.base()                      # written as <dir>/probe001.sqlite3
    rows = [p.tx('U', '2026-12-08', '15.00'), p.rc('U', '2026-12-08', '15.00')]
    p.send(os_, 'xv-u', rows + [p.stmt(rows, p.DEC, opening='100.00')]); p.prep(os_)
    a = p.gov(os_, p.K('U'), '2026-12'); print('review:', p.review(os_, p.REV2, a, 'approve'))
    print('finalize:', p.attempt(os_.finalize_package, p.FIN, '2026-12', 'card_preparation', 'Fictional finalization', 'Fictional acknowledgement'))
    print('U approved:', p.approved(os_, p.K('U'), '2026-12'), '| database:', os_.probe_path)
else:
    os_ = AccountingOS(db, [h.SCOPE]); os_.probe_path = db
    a = p.gov(os_, p.K('U'), '2026-12')
    print('opened by this source: U governing artifact review status:', a['review_status'] if a else None, '| November A1:', p.gov(os_, p.K('A1'), '2026-11')['review_status'])
    ev = lambda: [e['code'] for e in os_.export(p.PREP)['accounting_events'] if e['code'] == 'POST_FINALIZATION_CHANGE']
    print('POST_FINALIZATION_CHANGE events before any new delivery:', len(ev()))
    rows = [p.tx('V', '2026-12-09', '16.00'), p.rc('V', '2026-12-09', '16.00')]
    print('one unrelated delivery:', p.send(os_, 'xv-v', rows))
    print('POST_FINALIZATION_CHANGE events after it:', len(ev()))
    p.prep(os_); a = p.gov(os_, p.K('U'), '2026-12')
    print('after a new preparation: U review status:', a['review_status'] if a else None, '| audit verifies:', os_.verify_audit(p.PREP))
