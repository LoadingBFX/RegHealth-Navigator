"""
Command line test script for the RegHealth Navigator agent system.
"""
import json
from typing import Dict, List
from datetime import datetime
from .workflow import RegHealthWorkflow
from .core.types import QueryIntent

def format_state(state: Dict) -> str:
    """Format the workflow state for display.
    
    Args:
        state: The workflow state
        
    Returns:
        str: Formatted state string
    """
    output = []
    output.append("\n=== Workflow State ===")
    
    # Original query
    output.append(f"\nOriginal Query: {state['query']}")
    
    # Intent and entities
    if state['current_intent']:
        intent = state['current_intent']
        output.append("\nExtracted Information:")
        output.append(f"- Intent: {intent.intent}")
        output.append(f"- Program Type: {intent.program_type or 'Not specified'}")
        output.append(f"- Regulation Type: {intent.regulation_type or 'Not specified'}")
        if intent.time_window:
            if isinstance(intent.time_window, dict):
                start = intent.time_window.get('start_date', 'Not specified')
                end = intent.time_window.get('end_date', 'Not specified')
                output.append(f"- Time Window: {start} to {end}")
            else:
                output.append(f"- Time Window: {intent.time_window}")
        if intent.entities:
            output.append(f"- Entities: {', '.join(intent.entities)}")
    
    # Normalized and optimized queries
    if state['normalized_query']:
        output.append(f"\nNormalized Query: {state['normalized_query']}")
    if state['optimized_query']:
        output.append(f"Optimized Query: {state['optimized_query']}")
    
    # Clarification needed
    if state['awaiting_clarification']:
        output.append(f"\nClarification Needed: {state['clarification_question']}")
    
    # Final answer
    if state['final_answer']:
        output.append(f"\nFinal Answer: {state['final_answer']}")
    
    return "\n".join(output)

def main():
    """Main function to test the workflow."""
    # Initialize the workflow
    workflow = RegHealthWorkflow()
    
    print("RegHealth Navigator Query Processing System")
    print("==========================================")
    print("Type 'exit' to quit")
    print()
    
    conversation_history = []
    
    while True:
        # Get user input
        query = input("\nEnter your query: ").strip()
        
        if query.lower() == 'exit':
            break
        
        # Process the query
        state = workflow.process_query(query, conversation_history)
        
        # Display the results
        print(format_state(state))
        
        # Update conversation history
        conversation_history.append({
            "role": "user",
            "content": query
        })
        
        if state['final_answer']:
            conversation_history.append({
                "role": "assistant",
                "content": state['final_answer']
            })

if __name__ == "__main__":
    main() 