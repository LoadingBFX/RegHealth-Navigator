"""
Unit tests for the QueryNormalizer tool
"""
import unittest
from core.agents.tools.query_normalizer import QueryNormalizer

class TestQueryNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = QueryNormalizer(model_name="gpt-3.5-turbo")  # Use a fast/testable model

    def test_expand_abbreviations(self):
        text = "The MPFS and SNF rules."
        expanded = self.normalizer.expand_abbreviations(text)
        self.assertIn("Medicare Physician Fee Schedule", expanded)
        self.assertIn("Skilled Nursing Facility", expanded)

    def test_normalize_query(self):
        query = "What are the MPFS changes for 2024?"
        normalized = self.normalizer.normalize_query(query)
        self.assertIsInstance(normalized, str)
        self.assertIn("Medicare Physician Fee Schedule", normalized)
        self.assertIn("2024", normalized)

if __name__ == "__main__":
    unittest.main() 