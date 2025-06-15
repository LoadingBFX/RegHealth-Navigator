"""
Intent Recognition Agent for RegHealth Navigator
==============================================

This module implements the intent recognition agent that identifies
the user's intent and extracts relevant entities from the query.
"""

from typing import Dict, List, Optional, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from .types import QueryIntent

class IntentAgent:
    """Agent for recognizing user intent and extracting entities."""
    
    def __init__(self):
        """Initialize the intent recognition agent."""
        self.chain = self._create_chain()
    
    def _create_chain(self):
        """Create the intent recognition chain."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intent recognition agent for healthcare regulation queries. Your task is to identify the user's intent and extract ALL relevant entities from their query.

You must respond in the following JSON format:
{{
    "intent": "search" | "clarify" | "compare",
    "program_type": "HOSPICE" | "MPFS" | "SNF" | "IPPS" | "OPPS",
    "regulation_type": "final" | "proposed",
    "time_window": {{
        "start": "YYYY-MM-DD",
        "end": "YYYY-MM-DD"
    }},
    "entities": ["entity1", "entity2", ...]
}}

Important guidelines:
1. For entities, extract ALL relevant terms including:
   - Program names (e.g., "hospice", "MPFS", "SNF")
   - Years and dates
   - Key terms (e.g., "changes", "rates", "regulations")
2. Convert program names to their standard form:
   - "hospice" -> "HOSPICE"
   - "physician fee schedule" -> "MPFS"
   - "skilled nursing" -> "SNF"
3. For time windows:
   - If a single year is mentioned, use Jan 1 to Dec 31
   - If comparing years, use both years as start/end

Example:
Query: "What are the 2024 MPFS changes?"
Response: {{
    "intent": "search",
    "program_type": "MPFS",
    "regulation_type": "final",
    "time_window": {{
        "start": "2024-01-01",
        "end": "2024-12-31"
    }},
    "entities": ["MPFS", "2024", "changes"]
}}

Current state:
{state}

What is the user's intent and what entities can you extract?"""),
            ("human", "{query}")
        ])
        
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        
        parser = JsonOutputParser(pydantic_object=QueryIntent)
        
        return prompt | model | parser
    
    def recognize_intent(self, state: Dict) -> QueryIntent:
        """Recognize the intent and extract entities from the query.
        
        Args:
            state: The current workflow state containing the query and conversation history
            
        Returns:
            QueryIntent: The recognized intent and extracted entities
            
        Example:
            >>> state = {
            ...     "query": "What are the 2024 MPFS changes?",
            ...     "conversation_history": []
            ... }
            >>> intent = agent.recognize_intent(state)
            >>> print(intent)
            {
                "intent": "search",
                "program_type": "MPFS",
                "regulation_type": "final",
                "time_window": {
                    "start": "2024-01-01",
                    "end": "2024-12-31"
                },
                "entities": ["MPFS", "2024", "changes"]
            }
        """
        intent = self.chain.invoke({
            "query": state["query"],
            "state": state
        })
        return intent 