"""
Core types and data structures for the RegHealth Navigator agent system.
"""
from typing import Dict, List, Optional, TypedDict, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class QueryIntent(BaseModel):
    """Represents the identified intent and entities from a user query."""
    intent: str = Field(..., description="The primary intent of the query")
    program_type: Optional[str] = Field(None, description="Type of program (HOSPICE, MPFS, SNF, etc.)")
    regulation_type: Optional[str] = Field(None, description="Type of regulation (final, proposed)")
    time_window: Optional[Dict[str, datetime]] = Field(None, description="Time window for the query")
    entities: List[str] = Field(default_factory=list, description="Extracted entities from the query")
    confidence: float = Field(..., description="Confidence score for the intent classification")

class QueryState(TypedDict):
    """Represents the state of a query as it moves through the agent system."""
    query: str
    conversation_history: List[Dict[str, str]]
    current_intent: Optional[QueryIntent]
    normalized_query: Optional[str]
    optimized_query: Optional[str]
    awaiting_clarification: bool
    clarification_question: Optional[str]
    slots_filled: Dict[str, bool]
    retrieval_results: Optional[List[Dict]]
    final_answer: Optional[str]

class ProgramType(str, Enum):
    """Valid program types in the system."""
    HOSPICE = "HOSPICE"
    MPFS = "MPFS"
    SNF = "SNF"
    IPPS = "IPPS"
    OPPS = "OPPS"

class RegulationType(str, Enum):
    """Valid regulation types."""
    FINAL = "final"
    PROPOSED = "proposed" 