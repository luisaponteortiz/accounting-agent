"""Fault injection for the product register gate, not copies of document prose."""
from pathlib import Path
import re
import tempfile
import unittest

from scripts.check_product_requirements import validate_register, client_terms, validate_shared_sources

ROOT=Path(__file__).resolve().parents[1]


class ProductRequirements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.text=(ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text()

    def rejects(self,text,message):
        with self.assertRaisesRegex(ValueError,message):validate_register(text,ROOT)

    def test_current_register_has_split_states_and_all_backlog_tickets(self):
        result=validate_register(self.text,ROOT)
        self.assertGreaterEqual(result['requirements'],76)
        self.assertEqual(result['backlog_tickets'],27)
        self.assertEqual(sum(result['implementation_state_counts'].values()),result['requirements'])

    def test_duplicate_id_is_rejected(self):
        self.rejects(self.text.replace('### AAOS-GOV-02 —','### AAOS-GOV-01 —',1),'Duplicate requirement')

    def test_missing_field_is_rejected(self):
        self.rejects(self.text.replace('- **Evidence:**','- **Omitted evidence:**',1),'missing or repeated field Evidence')

    def test_unknown_dependency_is_rejected(self):
        self.rejects(self.text.replace('- **Dependencies:** None.','- **Dependencies:** AAOS-BOGUS-99.',1),'Unknown requirement')

    def test_dependency_cycle_is_rejected(self):
        self.rejects(self.text.replace('- **Dependencies:** None.','- **Dependencies:** AAOS-GOV-02.',1),'Dependency cycle')

    def test_missing_backlog_ticket_is_rejected(self):
        self.rejects(re.sub(r'^\| T-27 \|.*\n','',self.text,flags=re.M),'Backlog crosswalk')

    def test_mixed_implementation_state_is_rejected(self):
        self.rejects(self.text.replace('- **Implementation state:** Developer-tested','- **Implementation state:** Developer-tested and Deferred',1),'invalid implementation state')

    def test_developer_tested_without_named_tests_is_rejected(self):
        start=self.text.index('- **Implementation state:** Developer-tested')
        evidence=self.text.index('- **Evidence:**',start);end=self.text.index('\n',evidence)
        self.rejects(self.text[:evidence]+'- **Evidence:** Claims only'+self.text[end:],'named test/probe evidence')

    def test_shared_criteria_cannot_impose_first_client_facts(self):
        start=self.text.index('### AAOS-ARC-01 —')
        criterion=self.text.index('- **Acceptance criteria:**',start)+len('- **Acceptance criteria:**')
        self.rejects(self.text[:criterion]+' Bird Bowl-only policy;'+self.text[criterion:],'client-specific fact')

    def test_established_id_cannot_be_silently_renamed(self):
        self.rejects(self.text.replace('AAOS-INT-04','AAOS-INT-44'),'Previously established requirement IDs')

    def test_independent_verification_requires_review_and_checkpoint(self):
        self.rejects(self.text.replace('- **Implementation state:** Developer-tested','- **Implementation state:** Independently verified',1),'independent review and checkpoint')

    def changed_field(self,identifier,field,value,text=None):
        text=text or self.text
        start=text.index('### '+identifier+' —')
        end=text.find('\n### ',start+5)
        end=end if end>=0 else len(text)
        body=re.sub(r'^- \*\*'+re.escape(field)+r':\*\*[^\n]*',lambda m:'- **'+field+':** '+value,text[start:end],count=1,flags=re.M)
        return text[:start]+body+text[end:]

    def test_PRV02_nonexistent_test_ticket_and_arbitrary_token_are_rejected(self):
        for evidence in ('tests/test_does_not_exist.py','See PR-04','R2D2 says so'):
            with self.subTest(evidence=evidence):
                self.rejects(self.changed_field('AAOS-ARC-02','Evidence',evidence),'named test/probe evidence')
        validate_register(self.changed_field('AAOS-ARC-02','Evidence','R01a'),ROOT)

    def test_PRV03_self_asserted_independent_verification_is_rejected(self):
        changed=self.changed_field('AAOS-ARC-02','Implementation state','Independently verified')
        changed=self.changed_field('AAOS-ARC-02','Evidence','independent review '+'ab'*32+' tests/test_platform.py',changed)
        self.rejects(changed,'independent review result entry required')

    def test_PRV03_failed_verdict_cannot_be_promoted(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as tmp,rf_checkpoint(self,tmp) as (root,text):
            for state in ('Developer-tested','Independently verified','Implemented'):
                with self.subTest(state=state):
                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):
                        validate_register(self.changed_field('AAOS-BNK-03','Implementation state',state,text),root)

    def test_PRV04_shared_web_and_python_are_checked_but_fixtures_are_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'accounting_agent'
            for rel in ('web/app.js','core.py','config/demo.json','fixtures/demo.json','demo.py'):
                path=base/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('')
            for rel in ('web/app.js','core.py'):
                path=base/rel;path.write_text('bird_bowl_default')
                with self.assertRaisesRegex(ValueError,'Client-specific fact in shared source'):
                    validate_shared_sources(root,client_terms(self.text))
                path.write_text('')
            for rel in ('config/demo.json','fixtures/demo.json','demo.py'):(base/rel).write_text('Bird Bowl')
            validate_shared_sources(root,client_terms(self.text))

    def test_PRV05_approved_cannot_depend_unconditionally_on_proposed(self):
        self.rejects(self.changed_field('AAOS-ARC-04','Dependencies','AAOS-ONB-01'),'unconditional Proposed dependency')
        validate_register(self.changed_field('AAOS-ARC-04','Dependencies','AAOS-ONB-01 if ratified'),ROOT)

    def test_PRV06_unstarted_or_deferred_dependency_needs_local_condition(self):
        for dependencies in ('AAOS-KNO-01','AAOS-CTL-13','AAOS-CTL-13, the only prerequisite','only AAOS-CTL-13'):
            with self.subTest(dependencies=dependencies):
                self.rejects(self.changed_field('AAOS-GL-02','Dependencies',dependencies),'unconditional deferred/not-started dependency')
        validate_register(self.changed_field('AAOS-GL-02','Dependencies','AAOS-CTL-13 for real data only'),ROOT)

    def test_PRV07_scope_disposition_must_match_table(self):
        self.rejects(self.text.replace('| AAOS-EXC-05 | Reserved |','| AAOS-EXC-05 | Rejected |'),'scope table disposition differs')
        self.rejects(self.changed_field('AAOS-EXC-05','Scope note','Payment remains reserved.'),'fixed scope disposition prefix')

    def test_PRV08_stray_dependency_punctuation_is_rejected(self):
        self.rejects(self.changed_field('AAOS-BNK-02','Dependencies','AAOS-BNK-03. ; AAOS-CTL-04'),'stray dependency punctuation')

    def test_PRV10_every_shared_field_except_trace_uses_client_section_terms(self):
        for field in ('Description','Business purpose','Scope note','Evidence','Target stage','Acceptance criteria'):
            with self.subTest(field=field):
                value='Theresa '+('tests/test_platform.py' if field=='Evidence' else 'client-specific fact')
                self.rejects(self.changed_field('AAOS-ARC-01',field,value),'client-specific fact in shared')
        validate_register(self.changed_field('AAOS-ARC-01','Trace','Theresa reference only'),ROOT)
        changed=self.text.replace('Expensify; Desktop','Expensify; Desktop; Camila')
        changed=self.changed_field('AAOS-BB-08','Description','Camila owns the fictional client context.',changed)
        changed=self.changed_field('AAOS-ARC-01','Description','Camila controls the shared core.',changed)
        self.rejects(changed,'client-specific fact in shared Description')

    def reviewer_fault_copy(self, directory):
        import shutil
        root=Path(directory)/'project'
        shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__','*.zip','*.sqlite3','.venv'))
        baseline='exports/FABLE_RA_AND_PRODUCT_REQUIREMENTS_REVIEW_BUNDLE.zip'
        shutil.copyfile(ROOT/baseline,root/baseline)
        return root

    def test_PRV12_omitted_changed_and_invented_results_cannot_promote_records(self):
        import copy
        import json
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as tmp,rf_checkpoint(self,tmp) as (root,checkpoint_text):
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
            original=json.loads(path.read_text())
            removed=copy.deepcopy(original);removed['results'].pop(4)
            changed=copy.deepcopy(original);changed['results'][4]['state']='Independently verified'
            added=copy.deepcopy(original);added['results'].append(dict(added['results'][0],id='AAOS-ARC-02'))
            for data,identifier,state in ((removed,'AAOS-BNK-03','Developer-tested'),
                                          (changed,'AAOS-BNK-03','Independently verified'),
                                          (added,'AAOS-ARC-02','Independently verified')):
                with self.subTest(identifier=identifier,state=state):
                    path.write_text(json.dumps(data))
                    text=self.changed_field(identifier,'Implementation state',state,checkpoint_text)
                    text=self.changed_field(identifier,'Evidence','independent review '+original['results'][0]['bundle_sha256']+' '+original['results'][0]['report_path']+' tests/test_platform.py',text)
                    with self.assertRaisesRegex(ValueError,'reviewer verdict'):
                        validate_register(text,root)

    def test_PRV12_both_reviewer_authority_files_are_hash_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp)
            for name in ('exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json',
                         'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json'):
                with self.subTest(name=name):
                    path=root/name;before=path.read_bytes();path.write_bytes(before+b'\n')
                    try:
                        with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):
                            validate_register(self.text,root)
                    finally:path.write_bytes(before)

    def test_PRV12_stale_checkpoint_metadata_is_rejected(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp)
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
            data=json.loads(path.read_text())
            # A real older conclusion is not the latest reviewer result.
            data['results'][0]['bundle_sha256']='00a13d9309cc8a26a281214e2c86bbf23050b2f1197f7f1a685aaf95f1be001d'
            data['results'][0]['report_path']='exports/FABLE_RB_ACCEPTANCE/FABLE_RB_ACCEPTANCE_REPORT.md'
            data['results'][0]['report_sha256']='528c94e49a951e7a1fca1869e2f3b57d13584a3157682772189344e8ee57fd9c'
            data['results'][0]['scope']='Synthetic local preparation controls only; see named probes and scope limits in the report.'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'reviewer verdict'):
                validate_register(self.text,root)

    def test_PRV13_terms_must_include_the_display_name_in_the_client_heading(self):
        missing=self.text.replace('**Client-specific terms:** Bird Bowl; ','**Client-specific terms:** ',1)
        self.rejects(missing,'client display name')
        renamed=self.text.replace('## Bird Bowl onboarding and validation','## Cedar Hall onboarding and validation',1)
        self.rejects(renamed,'client display name')
        validate_register(self.text.replace('Bird Bowl','Cedar Hall'),ROOT)

    def test_PRV15_result_row_swaps_and_reversal_are_rejected(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp);path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';original=json.loads(path.read_text())
            for rows in ([original['results'][1],original['results'][0]]+original['results'][2:],original['results'][::-1]):
                path.write_text(json.dumps(dict(original,results=rows)))
                with self.assertRaisesRegex(ValueError,'row order'):validate_register(self.text,root)

    def test_PRV14_third_authority_is_pinned_and_latest_verdict_controls(self):
        import hashlib,json
        from unittest.mock import patch
        import scripts.check_product_requirements as cpr
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;original=path.read_bytes()
            path.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):validate_register(self.text,root)
            path.write_bytes(original)
            # Historical three-authority fixture: omit only the fourth and fifth pinned inputs as data; RF-checkpoint register bytes.
            from tests.rf_checkpoint_fixture import FIFTH,checkpoint_bytes
            checkpoint_text=checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode()
            fourth={'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json',
                    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'}
            three_inputs={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in fourth and key not in FIFTH}
            with patch.dict(cpr.REVIEW_INPUT_HASHES,three_inputs,clear=True):
                data=json.loads(original)
                for row in data['register_verdicts']:
                    if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
                changed=json.dumps(data).encode();path.write_bytes(changed)
                result_path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';results=json.loads(result_path.read_text())
                # Derive the fixture rows with the same unmodified validation code.
                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                    results['results']=list(cpr.reviewer_verdicts(root)[0].values())
                result_path.write_text(json.dumps(results))
                with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(checkpoint_text,root)
                    validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed',checkpoint_text),root)
