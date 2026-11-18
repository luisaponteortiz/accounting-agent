"""Create the RF/PRV handoff without overwriting any earlier review envelope."""
import argparse
import ast
import difflib
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'FABLE_RF_AND_PRV_CORRECTIONS'
BASELINE = 'exports/FABLE_RE_AND_PRV_CORRECTIONS_REVIEW_BUNDLE.zip'
BASELINE_HASH = '4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae'
OUT = ROOT/'docs/corrections_rf'
BUNDLE = ROOT/'exports'/(LABEL+'_REVIEW_BUNDLE.zip')
ENVELOPE = {str(p.relative_to(ROOT)) for p in (
    BUNDLE, BUNDLE.with_suffix('.zip.sha256'), BUNDLE.with_suffix('.REVIEW_MANIFEST.json'),
    ROOT/'exports'/(LABEL+'_PACKAGE_CHECK.json'),
    ROOT/'exports'/(LABEL+'_FINAL_VERIFICATION.json'))}
SELF_ARTIFACTS = {'docs/corrections_rf/changed-files.json', 'docs/corrections_rf/source-and-tests.patch'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def payload_files():
    files = {}
    for path in ROOT.rglob('*'):
        relative = path.relative_to(ROOT)
        name = relative.as_posix()
        if any(p in {'.git', '__pycache__', '.venv', '.agents', '.codex'} for p in relative.parts):continue
        if not path.is_file() or path.name == '.DS_Store' or path.suffix in {'.pyc', '.sqlite3', '.db'} or path.name.endswith(('-wal', '-shm')):continue
        if relative.parts[0] == 'data' and name != 'data/.gitkeep':continue
        if name in ENVELOPE or name.startswith('exports/'+LABEL+'_FINAL_VERIFICATION/') or name == 'REVIEW_MANIFEST.json':continue
        if path.is_symlink():raise ValueError('Unexpected symlink in payload: '+name)
        files[name] = path.read_bytes()
    return files


def test_methods(raw):
    tree = ast.parse(raw)
    return {cls.name+'.'+node.name for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)
            for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_')}


def prepare():
    assert sha((ROOT/BASELINE).read_bytes()) == BASELINE_HASH
    initial = json.loads((OUT/'initial-files.json').read_text())
    current = payload_files()
    with zipfile.ZipFile(ROOT/BASELINE) as archive:
        baseline = {n: archive.read(n) for n in archive.namelist() if n != 'REVIEW_MANIFEST.json' and not n.endswith('/')}
    retained = {}
    for name, raw in baseline.items():
        if not name.startswith('tests/') or not name.endswith('.py'):continue
        assert name in current, 'Missing prior test file: '+name
        before=test_methods(raw);after=test_methods(current[name])
        assert before<=after, 'Lost prior method: '+name
        allowed='test_PRV14_third_authority_is_pinned_and_latest_verdict_controls'
        authorized=name=='tests/test_product_requirements.py'
        def masked(body):
            tree=ast.parse(body);node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==allowed)
            lines=body.splitlines(True)
            return b''.join(lines[:node.lineno-1])+b'<D-031 AUTHORIZED METHOD>\n'+b''.join(lines[node.end_lineno:])
        if authorized:
            assert masked(raw)==masked(current[name]), 'Changed bytes outside D-031 method: '+name
            old_methods={n.name:ast.dump(n) for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.FunctionDef)}
            new_methods={n.name:ast.dump(n) for n in ast.walk(ast.parse(current[name])) if isinstance(n,ast.FunctionDef)}
            assert all(k==allowed or new_methods.get(k)==v for k,v in old_methods.items())
        else:assert raw==current[name], 'Retained test file changed: '+name
        retained[name]={'baseline_methods':len(before),'retained_methods':sorted(before),'new_methods':sorted(after-before),'byte_identical':raw==current[name],'authorized_rewrite':[allowed] if authorized else []}
    assert sum(r['baseline_methods'] for r in retained.values())==227
    protected = json.loads((OUT/'input-checksums.json').read_text())
    for name, expected in protected.items():assert name in current and sha(current[name]) == expected, 'Changed immutable input: '+name
    changes = []; patch = []
    for name in sorted(set(baseline) | set(current)):
        if name in SELF_ARTIFACTS:continue
        old = baseline.get(name); new = current.get(name)
        if old == new:continue
        changes.append({'file': name, 'status': 'added' if old is None else 'deleted' if new is None else 'modified',
                        'baseline_sha256': sha(old) if old is not None else None,
                        'initial_working_sha256': initial.get(name), 'sha256': sha(new) if new is not None else None,
                        'pre_existing_difference': initial.get(name) != (sha(old) if old is not None else None),
                        'changed_in_this_pass': initial.get(name) != (sha(new) if new is not None else None)})
        if name in ('Makefile','review/fable_rd_feed_contract_probes.py') or name.startswith(('accounting_agent/', 'tests/', 'scripts/')):
            patch.extend(difflib.unified_diff((old or b'').decode().splitlines(True), (new or b'').decode().splitlines(True),
                         fromfile='a/'+name if old is not None else '/dev/null', tofile='b/'+name if new is not None else '/dev/null'))
    inventory = {'baseline': BASELINE, 'baseline_sha256': BASELINE_HASH,
                 'scope': 'Every deliverable payload file against the RE/PRV correction bundle, including exports/ and START_HERE.md.',
                 'coverage_rules': [
                     'All differing payload files are individually listed except the two self-artifacts named below, which are covered by REVIEW_MANIFEST.json.',
                     'REVIEW_MANIFEST.json hashes every payload file except itself; its own SHA-256 is in the adjacent PACKAGE_CHECK JSON.',
                     'The final archive and its adjacent checksum, external manifest and PACKAGE_CHECK JSON are the output envelope, excluded from the payload to prevent recursion. The checksum sidecar hashes the archive.',
                     'Final extracted-archive verification JSON/logs are adjacent output-envelope evidence, excluded from the payload to avoid self-reference; they verify this archive without rebuilding it.',
                     'Git metadata, caches, virtual environments, .DS_Store and runtime databases/data are excluded; no delivered source/evidence file is excluded by that rule.'
                 ], 'self_artifacts_covered_by_manifest': sorted(SELF_ARTIFACTS),
                 'output_envelope': sorted(ENVELOPE), 'original_tests': retained, 'files': changes}
    (OUT/'source-and-tests.patch').write_text(''.join(patch))
    (OUT/'changed-files.json').write_text(json.dumps(inventory, indent=2)+'\n')
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Refresh only the new inventory/patch before packaging')
    args = parser.parse_args()
    if not args.prepare and any((ROOT/n).exists() for n in ENVELOPE):
        raise SystemExit('Review envelope already exists; never overwrite an earlier archive, sidecar or manifest.')
    inventory = prepare()
    if not args.prepare:
        completion=json.loads((OUT/'completion.json').read_text())
        assert completion['status']=='DEVELOPER_VALIDATED_INDEPENDENT_REVIEW_PENDING', completion
    if args.prepare:
        print('Prepared comprehensive inventory:', len(inventory['files']), 'differences; prior methods retained:', sum(r['baseline_methods'] for r in inventory['original_tests'].values()))
        return
    files = payload_files()
    manifest = {'label': LABEL, 'scope': 'Local fictional RF-01–RF-03/PRV-16 developer corrections under unchanged D-026/D-029; independent acceptance pending; no release or live authority.',
                'hash_rule': 'Every payload file except this manifest itself. Its hash is anchored in the adjacent package-check JSON.',
                'files': {n: sha(raw) for n, raw in sorted(files.items())}}
    manifest_raw = (json.dumps(manifest, indent=2)+'\n').encode()
    with zipfile.ZipFile(BUNDLE, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):archive.writestr(name, raw)
        archive.writestr('REVIEW_MANIFEST.json', manifest_raw)
    with zipfile.ZipFile(BUNDLE) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist()))
        for name, expected in manifest['files'].items():assert sha(archive.read(name)) == expected
    bundle_hash = sha(BUNDLE.read_bytes())
    BUNDLE.with_suffix('.zip.sha256').write_text(bundle_hash+'  '+BUNDLE.name+'\n')
    BUNDLE.with_suffix('.REVIEW_MANIFEST.json').write_bytes(manifest_raw)
    check = {'bundle': BUNDLE.name, 'bundle_sha256': bundle_hash, 'manifest_sha256': sha(manifest_raw),
             'payload_files': len(files), 'all_payload_hashes_and_crc_verified': True,
             'protected_inputs_verified': len(json.loads((OUT/'input-checksums.json').read_text())),
             'baseline_test_methods_retained': sum(r['baseline_methods'] for r in inventory['original_tests'].values()),
             'baseline_test_methods_unchanged':226, 'sole_authorized_rewrite':'D-031 / test_PRV14_third_authority_is_pinned_and_latest_verdict_controls',
             'contract_completion': 'DEVELOPER_VALIDATED_INDEPENDENT_REVIEW_PENDING',
             'owner_clarification': 'D-029: preserve frozen approval; block incoming version until authorized reopen',
             'independent_acceptance': 'PENDING', 'human_G0': 'NOT_GRANTED', 'batch3': 'CLOSED'}
    (ROOT/'exports'/(LABEL+'_PACKAGE_CHECK.json')).write_text(json.dumps(check, indent=2)+'\n')
    print(json.dumps(check, indent=2))


if __name__ == '__main__':
    main()
