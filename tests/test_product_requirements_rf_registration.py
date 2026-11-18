"""RF result registration: the fifth reviewer authority on the unmodified shipped configuration."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests import test_product_requirements as prior
from tests import rf_checkpoint_fixture as fixture
import scripts.check_product_requirements as cpr
ROOT=Path(__file__).resolve().parents[1]
FIFTH,REPORT=fixture.FIFTH
RF_BUNDLE='c002b8617f10dafac0aecad2281a9d333e14ca2604b3f0b56c0b579340bde7cd'
RE_BUNDLE='4890b297d7653e6f821eb6e8c2c97b8d766a7808858e9b3ca318ff38aa5998ae'
RE_REPORT='exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'
OLDER=('exports/FABLE_PR_REVERIFICATION/FABLE_PR_REVERIFICATION_CORRECTIONS.json',
       'exports/FABLE_RC_ACCEPTANCE/FABLE_RC_ACCEPTANCE_RESULTS.json',
       'exports/FABLE_RD_ACCEPTANCE/FABLE_RD_ACCEPTANCE_RESULTS.json',
       'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json')
SEVEN=['AAOS-KNO-04','AAOS-CTL-01','AAOS-BNK-02','AAOS-CTL-09','AAOS-BNK-03','AAOS-CTL-04','AAOS-GOV-03']
RECORDED=('AAOS-BNK-03','AAOS-CTL-04','AAOS-GOV-03')
RESULTS='docs/INDEPENDENT_VERIFICATION_RESULTS.json'


def altered(root,name,identifier,state):
    """Write a reviewer JSON whose verdict for one record is changed; return its new hash."""
    path=root/name;data=json.loads(path.read_text())
    if 'register_verdicts' in data:
        rows=[row for row in data['register_verdicts'] if row['id']==identifier]
        if state is None:data['register_verdicts']=[row for row in data['register_verdicts'] if row['id']!=identifier]
        else:
            for row in rows:row['state']=state
    else:
        rows=[row for row in data['verification_conclusions_for_the_seven_failed_records']['records'] if row['id']==identifier]
        for row in rows:row['conclusion']='Remains Verification failed' if state=='Verification failed' else 'May be recorded Independently verified'
    assert rows,(name,identifier)
    raw=json.dumps(data).encode();path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class ProductRequirementsRFRegistration(unittest.TestCase):
    reviewer_fault_copy=prior.ProductRequirements.reviewer_fault_copy
    changed_field=prior.ProductRequirements.changed_field
    @classmethod
    def setUpClass(cls):cls.text=(ROOT/'docs/PRODUCT_REQUIREMENTS.md').read_text()

    def follow(self,root):
        """Make the project results file follow whatever the (re-pinned) authorities now say."""
        path=root/RESULTS;data=json.loads(path.read_text())
        data['results']=list(cpr.reviewer_verdicts(root)[0].values());path.write_text(json.dumps(data))

    def test_shipped_configuration_reads_five_authorities_and_the_fifth_is_latest(self):
        self.assertEqual([name for name in cpr.REVIEW_INPUT_HASHES if name.endswith('.json')],list(OLDER)+[FIFTH])
        self.assertEqual(list(cpr.REVIEW_INPUT_HASHES)[-2:],[FIFTH,REPORT])
        latest,history=cpr.reviewer_verdicts(ROOT)
        self.assertEqual(list(latest),SEVEN)
        for identifier,row in latest.items():
            with self.subTest(identifier=identifier):
                self.assertEqual((row['state'],row['report_path'],row['bundle_sha256']),('Independently verified',REPORT,RF_BUNDLE))
                self.assertEqual(row['report_sha256'],hashlib.sha256((ROOT/REPORT).read_bytes()).hexdigest())
        for identifier in RECORDED:
            previous=history[identifier][-2]
            self.assertEqual((previous['state'],previous['report_path'],previous['bundle_sha256']),('Verification failed',RE_REPORT,RE_BUNDLE))
        self.assertEqual(json.loads((ROOT/RESULTS).read_text())['results'],list(latest.values()))

    def test_fifth_results_and_report_are_hash_pinned(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t)
            for name in (FIFTH,REPORT):
                with self.subTest(name=name):
                    path=root/name;raw=path.read_bytes();path.write_bytes(raw+b'\n')
                    try:
                        with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):cpr.validate_register(self.text,root)
                    finally:path.write_bytes(raw)
            cpr.validate_register(self.text,root)

    def test_three_recorded_scopes_cite_the_fifth_checkpoint_and_nothing_else_moved(self):
        before=cpr.parse_register(fixture.checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode());after=cpr.parse_register(self.text)
        self.assertEqual(list(before),list(after))
        changed={key for key in before if before[key]!=after[key]}
        self.assertEqual(changed,set(RECORDED)|{'AAOS-GOV-02'})
        for key in before:
            self.assertEqual(before[key]['Product decision'],after[key]['Product decision'],key)
            if key!='AAOS-GOV-02':self.assertEqual(before[key]['Acceptance criteria'],after[key]['Acceptance criteria'],key)
            if key not in RECORDED:self.assertEqual(before[key]['Implementation state'],after[key]['Implementation state'],key)
        self.assertEqual({field for field in cpr.FIELDS if before['AAOS-GOV-02'][field]!=after['AAOS-GOV-02'][field]},{'Scope note','Acceptance criteria'})
        # Owner decision D-037 changed one sentence of this criterion and nothing else in it.
        old_rule='Only independent review can establish verification; a failed independent probe downgrades affected records in the same change.'
        new_rule='Only a recorded review can establish verification (under D-037 the reviewer may be the author, Fable, when the record says so; developer tests alone cannot); a failed review probe downgrades affected records in the same change.'
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].replace(old_rule,new_rule),after['AAOS-GOV-02']['Acceptance criteria'])
        self.assertEqual(before['AAOS-GOV-02']['Acceptance criteria'].count(old_rule),1)
        for key in RECORDED:
            with self.subTest(key=key):
                self.assertEqual(before[key]['Implementation state'],'Verification failed')
                self.assertEqual(after[key]['Implementation state'],'Independently verified')
                self.assertEqual({field for field in cpr.FIELDS if before[key][field]!=after[key][field]},{'Implementation state','Scope note','Evidence'})
                self.assertIn(RF_BUNDLE,after[key]['Evidence']);self.assertIn(REPORT,after[key]['Evidence'])
                self.assertIn(RF_BUNDLE,after[key]['Scope note'])
                # The earlier review failed this record: citing it alone cannot carry the verified state.
                stale=self.changed_field(key,'Evidence','independent review '+RE_BUNDLE+' '+RE_REPORT+' tests/test_product_requirements_rf.py')
                with self.assertRaisesRegex(ValueError,'independent review entry/checkpoint differs from evidence'):cpr.validate_register(stale,ROOT)

    def test_fifth_failed_verdict_cannot_be_promoted_and_a_downgrade_is_accepted_when_results_and_register_follow(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);new_hash=altered(root,FIFTH,'AAOS-BNK-03','Verification failed')
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{FIFTH:new_hash}):
                self.assertEqual(cpr.reviewer_verdicts(root)[0]['AAOS-BNK-03']['state'],'Verification failed')
                # Results that still say verified disagree with the latest authority.
                with self.assertRaisesRegex(ValueError,'disagree with reviewer verdict'):cpr.validate_register(self.text,root)
                self.follow(root)
                for state in ('Independently verified','Developer-tested','Implemented'):
                    with self.subTest(state=state),self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):
                        cpr.validate_register(self.changed_field('AAOS-BNK-03','Implementation state',state),root)
                cpr.validate_register(self.changed_field('AAOS-BNK-03','Implementation state','Verification failed'),root)

    def test_each_older_authority_altered_and_repinned_cannot_override_the_fifth(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);original=cpr.reviewer_verdicts(root)[0]
            current=original['AAOS-KNO-04']
            # Cite the fifth accepted checkpoint: the injected older failure
            # intentionally invalidates the real register's earlier citation.
            fixture_text=self.changed_field('AAOS-KNO-04','Evidence','independent review '+current['bundle_sha256']+' '+current['report_path']+' tests/test_product_requirements_rf_registration.py')
            for name in OLDER:
                with self.subTest(name=name):
                    raw=(root/name).read_bytes();new_hash=altered(root,name,'AAOS-KNO-04','Verification failed')
                    try:
                        with self.assertRaisesRegex(ValueError,'Protected reviewer input hash differs'):cpr.validate_register(fixture_text,root)
                        with patch.dict(cpr.REVIEW_INPUT_HASHES,{name:new_hash}):
                            self.assertEqual(cpr.reviewer_verdicts(root)[0],original);cpr.validate_register(fixture_text,root)
                    finally:(root/name).write_bytes(raw)
            # The fourth authority still failed the three recorded scopes; re-pinned as verified it adds nothing the fifth does not control.
            for identifier in RECORDED:
                self.assertEqual(cpr.reviewer_verdicts(root)[1][identifier][-2]['state'],'Verification failed')

    def test_results_and_register_that_follow_the_fourth_authority_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);path=root/RESULTS;current=json.loads(path.read_text())
            checkpoint_text=fixture.checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode()
            # The whole RF-checkpoint results file (RE latest), with the current and the RF-checkpoint register.
            path.write_bytes(fixture.checkpoint_bytes(RESULTS))
            for text in (self.text,checkpoint_text):
                with self.assertRaisesRegex(ValueError,'disagree with reviewer verdict'):cpr.validate_register(text,root)
            # One row at a time, taken from the real history.
            history=cpr.reviewer_verdicts(root)[1]
            for identifier in SEVEN:
                with self.subTest(identifier=identifier):
                    data=copy.deepcopy(current);data['results']=[history[row['id']][-2] if row['id']==identifier else row for row in data['results']]
                    path.write_text(json.dumps(data))
                    with self.assertRaisesRegex(ValueError,'disagree with reviewer verdict: '+identifier):cpr.validate_register(self.text,root)
            path.write_text(json.dumps(current));cpr.validate_register(self.text,root)
            # With the results restored, a register that still follows the fourth authority's failure is consistent only as a downgrade, never as the reverse.
            cpr.validate_register(checkpoint_text,root)

    def test_record_absent_from_the_fifth_falls_back_to_the_fourth_verdict(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);new_hash=altered(root,FIFTH,'AAOS-BNK-03',None)
            with patch.dict(cpr.REVIEW_INPUT_HASHES,{FIFTH:new_hash}):
                latest=cpr.reviewer_verdicts(root)[0]
                self.assertEqual(list(latest),SEVEN)
                self.assertEqual((latest['AAOS-BNK-03']['state'],latest['AAOS-BNK-03']['report_path']),('Verification failed',RE_REPORT))
                with self.assertRaisesRegex(ValueError,'disagree with reviewer verdict: AAOS-BNK-03'):cpr.validate_register(self.text,root)
                self.follow(root)
                with self.assertRaisesRegex(ValueError,'AAOS-BNK-03: independent Verification failed cannot be promoted'):cpr.validate_register(self.text,root)

    def test_seven_row_order_and_exact_rows_are_enforced_on_five_authorities(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);path=root/RESULTS;original=json.loads(path.read_text())
            self.assertEqual([row['id'] for row in original['results']],SEVEN)
            expected={'swapped':'row order','reversed':'row order','moved':'row order','missing':'must name every reviewer verdict',
                      'extra':'must name every reviewer verdict','duplicate':'must name every reviewer verdict','changed':'disagree with reviewer verdict',
                      'stale-bundle':'disagree with reviewer verdict','stale-report':'Independent report hash differs|disagree with reviewer verdict'}
            for fault,message in expected.items():
                d=copy.deepcopy(original);rows=d['results']
                if fault=='swapped':rows[4],rows[5]=rows[5],rows[4]
                elif fault=='reversed':rows.reverse()
                elif fault=='moved':rows.insert(0,rows.pop())
                elif fault=='missing':rows.pop(4)
                elif fault=='extra':rows.append(dict(rows[0],id='AAOS-ARC-02'))
                elif fault=='duplicate':rows[5]=rows[4]
                elif fault=='changed':rows[4]['state']='Verification failed'
                elif fault=='stale-bundle':rows[4]['bundle_sha256']=RE_BUNDLE
                else:rows[4]['report_path']=RE_REPORT
                path.write_text(json.dumps(d))
                with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,message):cpr.validate_register(self.text,root)

    def test_historical_fixture_bytes_are_hash_checked_and_leave_the_shipped_pins_alone(self):
        pins=dict(cpr.REVIEW_INPUT_HASHES)
        for name in fixture.CHECKPOINT:
            with self.subTest(name=name),patch.dict(fixture.CHECKPOINT,{name:'0'*64}):
                with self.assertRaisesRegex(ValueError,'RF checkpoint fixture hash differs'):fixture.checkpoint_bytes(name)
        with tempfile.TemporaryDirectory() as t:
            with fixture.rf_checkpoint(self,t) as (root,text):
                self.assertEqual(set(pins)-set(cpr.REVIEW_INPUT_HASHES),set(fixture.FIFTH))
                self.assertEqual({row['report_path'] for row in cpr.reviewer_verdicts(root)[0].values()},{RE_REPORT})
                cpr.validate_register(text,root)
        self.assertEqual(cpr.REVIEW_INPUT_HASHES,pins)
        self.assertEqual(list(cpr.REVIEW_INPUT_HASHES),list(pins))
