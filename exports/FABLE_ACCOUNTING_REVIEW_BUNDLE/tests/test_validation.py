import copy
import tempfile
import unittest
from pathlib import Path
from accounting_agent.demo import SCOPE, actor, load, seed
from accounting_agent.service import AccountingOS


class ValidationCase(unittest.TestCase):
    def test_separate_regression_cases(self):
        for case in load('fixtures/validation.json')['cases']:
            with self.subTest(case=case['id']), tempfile.TemporaryDirectory() as root:
                os=AccountingOS(Path(root)/'test.sqlite3',[SCOPE]);seed(os)
                source=copy.deepcopy(next(s for s in load('fixtures/teaching.json')['sources'] if s['kind']==case['source_kind'] and s['key']==case['source_key']))
                source['data'].update(case['changes'])
                packet=load('fixtures/teaching.json');packet.update(batch_id=case['id'],sources=[source]);os.intake(actor(),packet)
                rid=os.enqueue(actor(),case['workflow']);os.drain(actor('worker'))
                target='demo_card_001:TX-001' if case['workflow']=='card_preparation' else 'J-001'
                a=next(a for a in os.state(actor())['artifacts'] if a['run_id']==rid and a['item_key']==target)
                self.assertTrue(set(case['expected_blockers']).issubset(a['blockers']))
                self.assertEqual(bool(a['eligible']),case['eligible'])
                if 'expected_category' in case:self.assertEqual(a['payload']['data']['proposed_category'],case['expected_category'])
                if case['eligible']:self.assertEqual(a['blockers'],[])


if __name__=='__main__':unittest.main()
