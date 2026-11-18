"""PRV-16: fourth reviewer authority, original order and immutable reviewer pins."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests import test_product_requirements as prior
import scripts.check_product_requirements as cpr
ROOT=Path(__file__).resolve().parents[1]
FOURTH='exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json'
REPORT='exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'

class ProductRequirementsRF(unittest.TestCase):
    reviewer_fault_copy=prior.ProductRequirements.reviewer_fault_copy
    changed_field=prior.ProductRequirements.changed_field
    @classmethod
    def setUpClass(cls):cls.text=(ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text()
    def test_fourth_results_and_report_are_hash_pinned(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t)
            for name in (FOURTH,REPORT):
                with self.subTest(name=name):
                    self.assertIn(name,cpr.REVIEW_INPUT_HASHES)
                    path=root/name;raw=path.read_bytes();path.write_bytes(raw+b'\n')
                    try:
                        with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):cpr.validate_register(self.text,root)
                    finally:path.write_bytes(raw)
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

    def test_results_following_an_altered_and_repinned_older_authority_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);name='exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json';path=root/name;data=json.loads(path.read_text())
            for row in data['register_verdicts']:
                if row['id']=='AAOS-KNO-04':row['state']='Verification failed'
            raw=json.dumps(data).encode();path.write_bytes(raw)
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:hashlib.sha256(raw).hexdigest()}):
                latest,history=cpr.reviewer_verdicts(root)
                self.assertEqual(latest['AAOS-KNO-04']['state'],'Independently verified')
                results=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';d=json.loads(results.read_text())
                d['results']=[history[row['id']][-2] if row['id']=='AAOS-KNO-04' else row for row in d['results']]
                results.write_text(json.dumps(d))
                with self.assertRaisesRegex(ValueError,'disagree with reviewer verdict'):
                    cpr.validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
