"""Adapt exactly six retained methods to the historical four-authority fixture (names and assertions kept)."""
import sys,shutil
from pathlib import Path
root=Path(sys.argv[1]);new=Path(sys.argv[2])
def sub(path,pairs):
    p=root/path;t=p.read_text()
    for old,newtext in pairs:
        assert t.count(old)==1,(path,old[:70],t.count(old))
        t=t.replace(old,newtext)
    p.write_text(t)
FIX="            # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.\n"
sub('tests/test_product_requirements.py',[
 # PRV03
 ("""    def test_PRV03_failed_verdict_cannot_be_promoted(self):
        for state in ('Developer-tested','Independently verified','Implemented'):
            with self.subTest(state=state):
                self.rejects(self.changed_field('AAOS-BNK-03','Implementation state',state),'independent Verification failed cannot be promoted')
""",
 """    def test_PRV03_failed_verdict_cannot_be_promoted(self):
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as tmp,rf_checkpoint(self,tmp) as (root,text):
            for state in ('Developer-tested','Independently verified','Implemented'):
                with self.subTest(state=state):
                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):
                        validate_register(self.changed_field('AAOS-BNK-03','Implementation state',state,text),root)
"""),
 # PRV12 omitted/changed/invented
 ("""        import copy
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root=self.reviewer_fault_copy(tmp)
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
            original=json.loads(path.read_text())
            removed=copy.deepcopy(original);removed['results'].pop(4)
""",
 """        import copy
        import json
        from tests.rf_checkpoint_fixture import rf_checkpoint
        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as tmp,rf_checkpoint(self,tmp) as (root,checkpoint_text):
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json'
            original=json.loads(path.read_text())
            removed=copy.deepcopy(original);removed['results'].pop(4)
"""),
 ("""                    text=self.changed_field(identifier,'Implementation state',state)
""","""                    text=self.changed_field(identifier,'Implementation state',state,checkpoint_text)
"""),
 # PRV14 (second half only)
 ("""            # Historical three-authority fixture: omit only the fourth pinned inputs as data.
            fourth={'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json',
                    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'}
            three_inputs={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in fourth}
""",
 """            # Historical three-authority fixture: omit only the fourth and fifth pinned inputs as data; RF-checkpoint register bytes.
            from tests.rf_checkpoint_fixture import FIFTH,checkpoint_bytes
            checkpoint_text=checkpoint_bytes('docs/PRODUCT_REQUIREMENTS.md').decode()
            fourth={'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_RESULTS.json',
                    'exports/FABLE_RE_ACCEPTANCE/FABLE_RE_ACCEPTANCE_REPORT.md'}
            three_inputs={key:value for key,value in cpr.REVIEW_INPUT_HASHES.items() if key not in fourth and key not in FIFTH}
"""),
 ("""                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(self.text,root)
                    validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
""",
 """                    with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):validate_register(checkpoint_text,root)
                    validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed',checkpoint_text),root)
"""),
])
sub('tests/test_product_requirements_rf.py',[
 ("""from tests import test_product_requirements as prior
""","""from tests import test_product_requirements as prior
from tests.rf_checkpoint_fixture import rf_checkpoint
"""),
 # wins / cannot override
 ("""        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);original=cpr.reviewer_verdicts(root)[0]
            current=original['AAOS-KNO-04']
""","""        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            original=cpr.reviewer_verdicts(root)[0]
            current=original['AAOS-KNO-04']
"""),
 ("""            fixture_text=self.changed_field('AAOS-KNO-04','Evidence','independent review '+current['bundle_sha256']+' '+current['report_path']+' tests/test_product_requirements_rf.py')
""","""            fixture_text=self.changed_field('AAOS-KNO-04','Evidence','independent review '+current['bundle_sha256']+' '+current['report_path']+' tests/test_product_requirements_rf.py',text)
"""),
 # changed verdict controls
 ("""        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);path=root/FOURTH;data=json.loads(path.read_text())
""","""        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            path=root/FOURTH;data=json.loads(path.read_text())
"""),
 ("""                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):cpr.validate_register(self.text,root)
                cpr.validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed'),root)
    def test_fourth_stale""","""                with self.assertRaisesRegex(ValueError,'independent Verification failed cannot be promoted'):cpr.validate_register(text,root)
                cpr.validate_register(self.changed_field('AAOS-KNO-04','Implementation state','Verification failed',text),root)
    def test_fourth_stale"""),
 # stale/missing/...
 ("""        with tempfile.TemporaryDirectory() as t:
            root=self.reviewer_fault_copy(t);path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';original=json.loads(path.read_text())
            for fault in ('stale','missing','extra','duplicate','changed','swapped','reversed'):
""","""        # Historical four-authority fixture: omit only the fifth pinned inputs as data; RF-checkpoint register/results bytes.
        with tempfile.TemporaryDirectory() as t,rf_checkpoint(self,t) as (root,text):
            path=root/'docs/INDEPENDENT_VERIFICATION_RESULTS.json';original=json.loads(path.read_text())
            for fault in ('stale','missing','extra','duplicate','changed','swapped','reversed'):
"""),
 ("""                with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'reviewer|Independent'):cpr.validate_register(self.text,root)
""","""                with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'reviewer|Independent'):cpr.validate_register(text,root)
"""),
])
shutil.copyfile(new/'rf_checkpoint_fixture.py',root/'tests/rf_checkpoint_fixture.py')
print('adapted')
