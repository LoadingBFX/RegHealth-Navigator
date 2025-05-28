"""
chat_engine.py

Module for chat-based Q&A over XML content.

Example expected input:
    query: str
    context: List[str]

Example output:
    str (answer with citations)

>>> answer_query('What are the new safety requirements?', ['chunk1', 'chunk2'])
'Answer with citations.'
"""
from typing import List

def answer_query(query: str, context: List[str]) -> str:
    """
    Answer a user query based on XML context chunks.

    Args:
        query (str): User question.
        context (List[str]): Relevant XML text chunks.

    Returns:
        str: Answer with citations.
    """
    pass 