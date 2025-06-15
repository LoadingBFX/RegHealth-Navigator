"""
Router for RegHealth Navigator
=============================

This module implements the router agent that decides the next step in the workflow
based on the current state and query.
"""

from typing import Dict, List, Optional, TypedDict, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from .types import QueryState, QueryIntent

class RouterDecision(TypedDict):
    """Type for router's decision output."""
    next_step: Literal["intent_recognition", "clarification", "retrieval"]
    explanation: str

class Router:
    """Router agent that decides the next step in the workflow."""
    
    def __init__(self):
        """Initialize the router with its chain."""
        self.chain = self._create_chain()
    
    def _create_chain(self):
        """Create the router's decision chain."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a router agent in a healthcare regulation query processing system.
Your task is to decide the next step in the workflow based on the current state.

Available steps:
1. intent_recognition: When we need to understand the user's intent and extract entities
2. clarification: When we need more information from the user
3. retrieval: When we have all necessary information and can proceed to retrieval

You must respond in the following JSON format:
{{
    "next_step": "intent_recognition" | "clarification" | "retrieval",
    "explanation": "Your explanation for this decision"
}}

Current state:
{state}

What should be the next step?"""),
            ("human", "{query}")
        ])
        
        model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )
        
        parser = JsonOutputParser(pydantic_object=RouterDecision)
        
        return prompt | model | parser
    
    def decide_next_step(self, state: QueryState) -> RouterDecision:
        """
        Decide the next step based on the current state.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            RouterDecision containing the next step and explanation
        """
        decision = self.chain.invoke({
            "state": state,
            "query": state["query"]
        })
        return decision

    def should_clarify(self, state: QueryState) -> Dict[str, bool]:
        """Determine if clarification is needed based on missing slots.
        
        Args:
            state: Current state of the workflow
            
        Returns:
            Dict[str, bool]: Dictionary of slot names and whether they are missing
        """
        missing_slots = {}
        current_intent = state.get("current_intent")
        
        if not current_intent:
            missing_slots["program_type"] = True
            missing_slots["regulation_type"] = True
            return missing_slots
            
        # Check for missing slots
        if not current_intent.get("program_type"):
            missing_slots["program_type"] = True
        if not current_intent.get("regulation_type"):
            missing_slots["regulation_type"] = True
        if not current_intent.get("time_window"):
            missing_slots["time_window"] = True
            
        return missing_slots
    
    def format_clarification_question(self, missing_slots: Dict[str, bool]) -> str:
        """Format a question to ask for missing information.
        
        Args:
            missing_slots: Dictionary of slot names and whether they are missing
            
        Returns:
            str: A formatted question asking for the missing information
        """
        # Convert slot names to user-friendly format
        slot_names = {
            "program_type": "program type (e.g., HOSPICE, MPFS, SNF)",
            "regulation_type": "regulation type (final or proposed)",
            "time_window": "time period (e.g., 2024, 2023-2024)"
        }
        
        missing = [slot_names[slot] for slot, is_missing in missing_slots.items() if is_missing]
        
        if not missing:
            return ""
            
        if len(missing) == 1:
            return f"Could you please specify the {missing[0]}?"
        else:
            return f"Could you please provide the following information: {', '.join(missing)}?" 