"""Collect raw command records without relabeling expected nonzero results as passes."""
import json
from pathlib import Path
import shlex
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/corrections_rf'
records=[]
for path in sorted(OUT.glob('*.json')):
    value=json.loads(path.read_text())
    if isinstance(value,dict) and 'command' in value and 'exit_code' in value:
        records.append(dict(value,label=path.stem,stdout=path.stem+'.stdout.txt',stderr=path.stem+'.stderr.txt'))
(OUT/'execution-results.json').write_text(json.dumps({'scope':'Commands run by the developer; not independent acceptance. Nonzero baseline, obsolete-authority and intermediate results remain disclosed.','commands':records},indent=2)+'\n')
lines=['# Exact developer command results','','Every row links to raw stdout/stderr and JSON metadata with cwd, UTC start, elapsed time, Python/SQLite/platform and exit code. Expected failures and intermediate errors are retained. None is an independent verdict.','','| Label | Command | Exit | Seconds | Raw output |','| --- | --- | --- | --- | --- |']
for r in records:
    command=shlex.join(r['command']).replace('|','\\|')
    lines.append('| [%s](%s.json) | `%s` | %s | %s | [stdout](%s) / [stderr](%s) |'%(r['label'],r['label'],command,r['exit_code'],r['elapsed_seconds'],r['stdout'],r['stderr']))
(OUT/'COMMAND_RESULTS.md').write_text('\n'.join(lines)+'\n')
print('Collected',len(records),'raw command records.')
