"""
Unit tests for the Router component
==================================

This module contains tests for the Router's core functionality:
1. Decision making
2. Clarification checking
3. Question formatting
"""

import unittest
from typing import Dict
from core.agents.core.router import Router
from core.agents.core.types import QueryState

class TestRouter(unittest.TestCase):
    """Test cases for the Router component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = Router()
    
    def test_decide_next_step(self):
        """Test the router's decision making."""
        # Test case 1: New query, should go to intent recognition
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
        
        decision = self.router.decide_next_step(state)
        self.assertIn(decision["next_step"], ["intent_recognition", "clarification", "retrieval"])
        self.assertIsInstance(decision["explanation"], str)
    
    def test_should_clarify(self):
        """Test the clarification check logic."""
        # Test case 1: No intent yet
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
        self.assertTrue(self.router.should_clarify(state))
        
        # Test case 2: Missing program type
        state["current_intent"] = {
            "intent": "search",
            "program_type": None,
            "regulation_type": "final",
            "time_window": {"start": "2024-01-01", "end": "2024-12-31"},
            "entities": ["MPFS", "2024"]
        }
        self.assertTrue(self.router.should_clarify(state))
        
        # Test case 3: All slots filled
        state["current_intent"] = {
            "intent": "search",
            "program_type": "MPFS",
            "regulation_type": "final",
            "time_window": {"start": "2024-01-01", "end": "2024-12-31"},
            "entities": ["MPFS", "2024"]
        }
        self.assertFalse(self.router.should_clarify(state))
    
    def test_format_clarification_question(self):
        """Test the clarification question formatting."""
        missing_slots = {
            "program_type": True,
            "regulation_type": False,
            "time_window": True
        }
        question = self.router.format_clarification_question(missing_slots)
        self.assertIsInstance(question, str)
        self.assertIn("program type", question.lower())
        self.assertIn("time period", question.lower())

if __name__ == '__main__':
    unittest.main() 