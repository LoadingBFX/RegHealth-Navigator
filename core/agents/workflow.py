"""
Main workflow implementation for RegHealth Navigator
=================================================

This module implements the main workflow using LangGraph to coordinate
the different agents and tools in the system.
"""
from typing import Dict, List, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from .core.types import QueryState, QueryIntent
from .core.router import Router
from .core.intent_agent import IntentAgent
from .tools.date_resolver import DateResolver
from .tools.query_normalizer import QueryNormalizer
from .tools.query_optimizer import QueryOptimizer

class WorkflowState(TypedDict):
    """State for the workflow."""
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

class RegHealthWorkflow:
    """Main workflow for processing healthcare regulation queries."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """Initialize the workflow with its components.
        
        Args:
            model_name: Name of the OpenAI model to use
        """
        # Initialize agents and tools
        self.router = Router()
        self.intent_agent = IntentAgent()
        self.date_resolver = DateResolver()
        self.query_normalizer = QueryNormalizer()
        self.query_optimizer = QueryOptimizer()
        
        # Create the workflow graph
        self.graph = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create the workflow graph.
        
        Returns:
            StateGraph: The workflow graph
        """
        # Create the graph
        graph = StateGraph(WorkflowState)
        
        # Add nodes
        graph.add_node("router", self._router_node)
        graph.add_node("intent_recognition", self._intent_recognition_node)
        graph.add_node("date_resolution", self._date_resolution_node)
        graph.add_node("query_normalization", self._query_normalization_node)
        graph.add_node("query_optimization", self._query_optimization_node)
        graph.add_node("clarification", self._clarification_node)
        graph.add_node("retrieval", self._retrieval_node)
        graph.add_node("answer_generation", self._answer_generation_node)
        
        # Add edges
        graph.add_edge("router", "intent_recognition")
        graph.add_edge("intent_recognition", "date_resolution")
        graph.add_edge("date_resolution", "query_normalization")
        graph.add_edge("query_normalization", "query_optimization")
        graph.add_edge("query_optimization", "retrieval")
        graph.add_edge("retrieval", "answer_generation")
        # Add edge for answer_generation to END
        graph.add_edge("answer_generation", END)
        
        # Add conditional edges
        graph.add_conditional_edges(
            "router",
            self._should_clarify,
            {
                True: "clarification",
                False: "intent_recognition"
            }
        )
        # Add edge for clarification to router (user answers, go back to router)
        graph.add_edge("clarification", "router")
        
        # Set entry point
        graph.set_entry_point("router")
        
        return graph.compile()
    
    def _router_node(self, state: WorkflowState) -> WorkflowState:
        """Router node that decides the next step.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        decision = self.router.decide_next_step(state)
        return state
    
    def _intent_recognition_node(self, state: WorkflowState) -> WorkflowState:
        """Intent recognition node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        intent = self.intent_agent.recognize_intent(state)
        state["current_intent"] = intent
        return state
    
    def _date_resolution_node(self, state: WorkflowState) -> WorkflowState:
        """Date resolution node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        if state["current_intent"] and state["current_intent"].time_window:
            # Resolve any relative time references
            time_window = state["current_intent"].time_window
            if isinstance(time_window, str):
                resolved = self.date_resolver.resolve_date(time_window)
                if resolved:
                    state["current_intent"].time_window = resolved
        return state
    
    def _query_normalization_node(self, state: WorkflowState) -> WorkflowState:
        """Query normalization node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        normalized = self.query_normalizer.normalize_query(state["query"])
        state["normalized_query"] = normalized
        return state
    
    def _query_optimization_node(self, state: WorkflowState) -> WorkflowState:
        """Query optimization node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        program_type = state["current_intent"].program_type if state["current_intent"] else None
        optimized = self.query_optimizer.optimize_query(
            state["normalized_query"],
            program_type
        )
        state["optimized_query"] = optimized
        return state
    
    def _clarification_node(self, state: WorkflowState) -> WorkflowState:
        """Clarification node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        missing_slots = self.router.should_clarify(state)
        if missing_slots:
            question = self.router.format_clarification_question(missing_slots)
            state["awaiting_clarification"] = True
            state["clarification_question"] = question
        return state
    
    def _retrieval_node(self, state: WorkflowState) -> WorkflowState:
        """Retrieval node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        # TODO: Implement retrieval logic
        state["retrieval_results"] = []
        return state
    
    def _answer_generation_node(self, state: WorkflowState) -> WorkflowState:
        """Answer generation node.
        
        Args:
            state: The current workflow state
            
        Returns:
            WorkflowState: The updated state
        """
        # TODO: Implement answer generation logic
        state["final_answer"] = "Answer placeholder"
        return state
    
    def _should_clarify(self, state: WorkflowState) -> bool:
        """Check if clarification is needed.
        
        Args:
            state: The current workflow state
            
        Returns:
            bool: True if clarification is needed, False otherwise
        """
        missing_slots = self.router.should_clarify(state)
        return len(missing_slots) > 0
    
    def process_query(self, query: str, conversation_history: List[Dict[str, str]] = None) -> WorkflowState:
        """Process a user query through the workflow.
        
        Args:
            query: The user's query
            conversation_history: Optional conversation history
            
        Returns:
            WorkflowState: The final state after processing
        """
        # Initialize state
        state = WorkflowState(
            query=query,
            conversation_history=conversation_history or [],
            current_intent=None,
            normalized_query=None,
            optimized_query=None,
            awaiting_clarification=False,
            clarification_question=None,
            slots_filled={},
            retrieval_results=None,
            final_answer=None
        )
        
        # Run the workflow
        final_state = self.graph.invoke(state)
        return final_state 