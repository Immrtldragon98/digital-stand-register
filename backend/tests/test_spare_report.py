import unittest
from app.services.spare_report_service import present_spare_report


class SpareReportTests(unittest.TestCase):
    def test_receipt_shortfall_and_surplus_are_separate(self):
        payload = {'plans': [{'rows': [
            {'monthly_target': 9, 'received': 31},
            {'monthly_target': 300, 'received': 170},
        ]}]}
        rows = present_spare_report(payload)['plans'][0]['rows']
        self.assertEqual((rows[0]['still_to_receive'], rows[0]['extra_received']), (0, 22))
        self.assertEqual((rows[1]['still_to_receive'], rows[1]['extra_received']), (130, 0))
        self.assertIsNone(rows[0]['stock_balance'])
        self.assertNotIn('still_to_receive', payload['plans'][0]['rows'][0])

    def test_blank_target_stays_unknown_even_with_receipts(self):
        row = present_spare_report({'plans': [{'rows': [{'monthly_target': None, 'received': 5}]}]})['plans'][0]['rows'][0]
        self.assertIsNone(row['still_to_receive'])
        self.assertIsNone(row['extra_received'])

    def test_explicit_zero_target_is_distinct_from_missing(self):
        row = present_spare_report({'plans': [{'rows': [{'monthly_target': 0, 'received': 5}]}]})['plans'][0]['rows'][0]
        self.assertEqual(row['still_to_receive'], 0)
        self.assertEqual(row['extra_received'], 5)
