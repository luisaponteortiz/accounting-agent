# tests/test_product_requirements.py::ProductRequirements.test_PRV03_failed_verdict_cannot_be_promoted
def test_PRV03_failed_verdict_cannot_be_promoted(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as tmp,rf_checkpoint(self,tmp) as (root,text):
            for state in ('Developer-tested','Independently verified','Implemented'):
                with self.subTest(state=state):
                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):
                        validate_register(self.changed_field('AAOS-BNK-03','Implementation state',state,text),root)

# tests/test_product_requirements.py::ProductRequirements.test_PRV12_omitted_changed_and_invented_results_cannot_promote_records
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

# tests/test_product_requirements.py::ProductRequirements.test_PRV14_third_authority_is_pinned_and_latest_verdict_controls
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

# tests/test_product_requirements_rf.py::ProductRequirementsRF.test_fourth_authority_wins_and_all_older_authorities_cannot_override
def test_fourth_authority_wins_and_all_older_authorities_cannot_override(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            original=cpr.reviewer_verdicts(root)[0]
            current=original['AAOS-KNO-04']
            # Cite the fourth accepted checkpoint: the injected older failure
            # intentionally invalidates the real register's earlier citation.
            fixture_text=self.changed_field('AAOS-KNO-04','Evidence','independent review '+current['bundle_sha256']+' '+current['report_path']+' tests/test_product_requirements_rf.py',text)
            self.assertTrue(all(r['report_path']==REPORT for r in original.values()))
            for name in ('exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json','exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json','exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json'):
                path=root/name;raw=path.read_bytes();data=json.loads(raw)
                if 'register_verdicts' in data:
                    for row in data['register_verdicts']:
                        if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
                else:
                    for row in data['verification_conclusions_for_the_seven_failed_records']['records']:
                        if row['id']=='AAOS-KNO-04':row['conclusion']='Remains Verification failed'
                changed=json.dumps(data).encode();path.write_bytes(changed)
                try:
                    with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(changed).hexdigest()}):
                        self.assertEqual(cpr.reviewer_verdicts(root)[0],original);cpr.validate_register(fixture_text,root)
                finally:path.write_bytes(raw)

# tests/test_product_requirements_rf.py::ProductRequirementsRF.test_fourth_changed_verdict_controls_even_with_matching_project_results
def test_fourth_changed_verdict_controls_even_with_matching_project_results(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            path=root/FOURTH;data=json.loads(path.read_text())
            for row in data['register_verdicts']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            raw=json.dumps(data).encode();path.write_bytes(raw)
            results=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';d=json.loads(results.read_text())
            for row in d['results']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            results.write_text(json.dumps(d))
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{FOURTH:hashlib.sha256(raw).hexdigest()}):
                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):cpr.validate_register(text,root)
                cpr.validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed',text),root)

# tests/test_product_requirements_rf.py::ProductRequirementsRF.test_fourth_stale_missing_extra_duplicate_changed_and_reordered_results_refused
def test_fourth_stale_missing_extra_duplicate_changed_and_reordered_results_refused(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';original=json.loads(path.read_text())
            for fault in ('stale','missing','extra','duplicate','changed','swapped','reversed'):
                d=copy.deepcopy(original)
                if fault=='stale':
                    older=json.loads((ROOT/'docs/corrections_rf/initial-independent-results.json').read_text());d['results']=older['results']
                elif fault=='missing':d['results'].pop()
                elif fault=='extra':d['results'].append(dict(d['results'][0],id='AAOS-ARC-02'))
                elif fault=='duplicate':d['results'][1]=d['results'][0]
                elif fault=='changed':d['results'][4]['state']='Independently verified'
                elif fault=='swapped':d['results'][0],d['results'][1]=d['results'][1],d['results'][0]
                else:d['results'].reverse()
                path.write_text(json.dumps(d))
                with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'reviewer|Independent'):cpr.validate_register(text,root)
