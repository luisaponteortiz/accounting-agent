"""Offline syntax/schema/registry checks without installing a toolchain."""
import ast
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from accounting_agent.core import Actor
from accounting_agent.demo import SCOPE
from accounting_agent.modules import WORKFLOWS, CAPABILITIES
from accounting_agent.service import AccountingOS
import tempfile

files=list((ROOT/'accounting_agent').rglob('*.py'))+list((ROOT/'tests').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))
for path in files:ast.parse(path.read_text(),filename=str(path))
for path in (ROOT/'accounting_agent').rglob('*.json'):json.loads(path.read_text())
with tempfile.TemporaryDirectory() as tmp:
    os=AccountingOS(Path(tmp)/'check.sqlite3',[SCOPE])
    os.onboard(Actor('human-demo-preparer','preparer','demo_org','bird_bowl_demo'),json.loads((ROOT/'accounting_agent/config/bird_bowl.demo.json').read_text()))
for workflow in WORKFLOWS.values():
    workflow.validate()
    assert all(s.capability in CAPABILITIES for s in workflow.steps)
js=(ROOT/'accounting_agent/web/app.js').read_text()
assert 'innerHTML' not in js and 'eval(' not in js
assert not any(p.suffix in ('.pem','.key') for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts)
print('PASS: Python syntax, JSON parsing, executable profile validation, workflow DAG/tool registration, DOM text rendering checks.')
print('No external linter/typechecker/JS compiler installed; these checks are not a claim of those tools passing.')
