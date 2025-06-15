"""
Unit tests for the DateResolver tool
"""
import unittest
from datetime import datetime
from core.agents.tools.date_resolver import DateResolver, DateRange

class TestDateResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = DateResolver()
        self.current_year = datetime.now().year

    def test_this_year(self):
        dr = self.resolver.resolve_date("this year")
        self.assertIsInstance(dr, DateRange)
        self.assertEqual(dr.start_date, datetime(self.current_year, 1, 1))
        self.assertEqual(dr.end_date, datetime(self.current_year, 12, 31))

    def test_last_year(self):
        dr = self.resolver.resolve_date("last year")
        self.assertIsInstance(dr, DateRange)
        self.assertEqual(dr.start_date, datetime(self.current_year - 1, 1, 1))
        self.assertEqual(dr.end_date, datetime(self.current_year - 1, 12, 31))

    def test_specific_date(self):
        dr = self.resolver.resolve_date("2023-05-01")
        self.assertIsInstance(dr, DateRange)
        self.assertEqual(dr.start_date, datetime(2023, 5, 1))
        self.assertEqual(dr.end_date.year, 2023)
        self.assertEqual(dr.end_date.month, 5)
        self.assertEqual(dr.end_date.day, 1)

    def test_invalid(self):
        dr = self.resolver.resolve_date("not a date")
        self.assertIsNone(dr)

if __name__ == "__main__":
    unittest.main() 