"""Assemble fable_ra_acceptance_probes.py: new header + the unchanged harness (lines 30-254 of the
earlier independent script exports/FABLE_RV_ACCEPTANCE/fable_rv_acceptance_probes.py) + new probes."""
import sys
from pathlib import Path
old = Path(sys.argv[1]).read_text().splitlines()
body = Path(sys.argv[2]).read_text()
header = '''"""Fable acceptance probes for the RA-01 to RA-08 corrections (Accounting Agent OS).

Usage (from anywhere):
    python3 fable_ra_acceptance_probes.py <project-root> [PROBE_ID ...]

Imports the application from <project-root> and drives it through public service operations
only. Temporary SQLite files, fictional data, no network, model, posting or payment.
Authority is explicit: every synthetic grant is in ROLES or made on the line that needs it.
Each refusal is paired with a positive control.

Verdicts: OK control held | WEAK confirmed gap (exit 1) | NOTE observation needing a decision
          | ERROR probe could not reach its intended state (exit 1)

The helper section is copied unchanged from the earlier independent script
(fable_rv_acceptance_probes.py, lines 30-254); one line is added to new_os to remember the
database path for the restart check.
"""
'''
harness = '\n'.join(old[29:254]).replace("TemporaryDirectory(prefix='fable-rv-accept-')", "TemporaryDirectory(prefix='fable-ra-accept-')")
harness = harness.replace("    os_ = AccountingOS(Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0]), [SCOPE])", "    os_ = AccountingOS(Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0]), [SCOPE])\n    os_.probe_path = Path(TMP.name) / ('probe%03d.sqlite3' % COUNTER[0])")
Path(sys.argv[3]).write_text(header + harness + '\n' + body)
