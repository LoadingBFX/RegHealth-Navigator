"""
Unit tests for the QueryOptimizer tool
"""
import unittest
from core.agents.tools.query_optimizer import QueryOptimizer

class TestQueryOptimizer(unittest.TestCase):
    def setUp(self):
        self.optimizer = QueryOptimizer(model_name="gpt-3.5-turbo")  # Use a fast/testable model

    def test_add_synonyms(self):
        text = "payment regulation"
        expanded = self.optimizer.add_synonyms(text)
        self.assertIn("payment", expanded)
        self.assertIn("reimbursement", expanded)
        self.assertIn("regulation", expanded)
        self.assertIn("rule", expanded)

    def test_add_program_context(self):
        query = "changes in payment rates"
        contexted = self.optimizer.add_program_context(query, "HOSPICE")
        self.assertIn("hospice care end-of-life", contexted)

    def test_optimize_query(self):
        query = "payment regulation changes"
        optimized = self.optimizer.optimize_query(query, program_type="MPFS")
        self.assertIsInstance(optimized, str)
        self.assertIn("MPFS", optimized)

if __name__ == "__main__":
    unittest.main() 