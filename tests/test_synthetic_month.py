import unittest
from scripts.synthetic_month import exercise

class SyntheticMonth(unittest.TestCase):
    def test_full_teaching_month_and_isolated_second_client(self):
        result=exercise()
        self.assertEqual(len(result['reviewed_items']),10)
        self.assertEqual(len(result['carried_dispositioned_items']),3)
        self.assertEqual(result['period_status'],'locked')
        self.assertEqual(result['isolation'],'PASS')
        self.assertEqual(result['proposed_entry_impact'],{'DEMO_CARD_LIABILITY':'-211.00','DEMO_CASH':'-300.00','DEMO_OFFICE_SUPPLIES':'311.00','DEMO_REPAIRS':'200.00'})
