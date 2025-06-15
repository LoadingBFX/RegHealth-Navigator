"""
Unit tests for the Intent Recognition Agent
=========================================

This module contains tests for the IntentAgent's core functionality:
1. Intent recognition
2. Entity extraction
3. Program type validation
4. Regulation type validation
"""

import unittest
from typing import Dict
from core.agents.core.intent_agent import IntentAgent
from core.agents.core.types import QueryState

class TestIntentAgent(unittest.TestCase):
    """Test cases for the Intent Recognition Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = IntentAgent()
    
    def test_recognize_intent(self):
        """Test intent recognition and entity extraction."""
        # Test case 1: MPFS changes query
        state: QueryState = {
            "query": "What are the 2024 MPFS changes?",
            "conversation_history": [],
            "current_intent": None,
            "normalized_query": None,
            "optimized_query": None,
            "awaiting_clarification": False,
            "clarification_question": None,
            "slots_filled": {},
            "retrieval_results": None,
            "final_answer": None
        }
        
        intent = self.agent.recognize_intent(state)
        self.assertIsNotNone(intent)
        self.assertIn("intent", intent)
        self.assertIn("program_type", intent)
        self.assertIn("regulation_type", intent)
        self.assertIn("time_window", intent)
        self.assertIn("entities", intent)
        
        # Verify specific fields
        self.assertEqual(intent["program_type"], "MPFS")
        self.assertIn("2024", intent["entities"])
        self.assertIn("MPFS", intent["entities"])
        
        # Test case 2: Hospice query
        state["query"] = "Show me the final hospice regulations for 2023"
        intent = self.agent.recognize_intent(state)
        self.assertEqual(intent["program_type"], "HOSPICE")
        self.assertEqual(intent["regulation_type"], "final")
        self.assertIn("2023", intent["entities"])
        self.assertIn("HOSPICE", intent["entities"])
        
        # Test case 3: SNF query with comparison
        state["query"] = "Compare SNF payment rates between 2023 and 2024"
        intent = self.agent.recognize_intent(state)
        self.assertEqual(intent["program_type"], "SNF")
        self.assertEqual(intent["intent"], "compare")
        self.assertIn("2023", intent["entities"])
        self.assertIn("2024", intent["entities"])
        self.assertIn("SNF", intent["entities"])

if __name__ == '__main__':
    unittest.main() 