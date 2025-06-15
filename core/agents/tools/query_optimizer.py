"""
Query optimization tool for the RegHealth Navigator system.
This tool is responsible for optimizing queries for better search results.
"""
from typing import Dict, List, Optional, Set
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class QueryOptimizer:
    """Tool for optimizing queries for better search results."""
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        """Initialize the query optimizer.
        
        Args:
            model_name: The name of the OpenAI model to use
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)
        
        # Common synonyms and related terms
        self.synonyms = {
            "payment": ["reimbursement", "compensation", "fee", "rate"],
            "regulation": ["rule", "policy", "guideline", "requirement"],
            "requirement": ["mandate", "obligation", "necessity", "prerequisite"],
            "compliance": ["adherence", "conformity", "observance"],
            "documentation": ["record", "paperwork", "charting", "notes"],
            "certification": ["accreditation", "qualification", "endorsement"],
            "audit": ["review", "examination", "inspection", "assessment"],
            "violation": ["breach", "infraction", "noncompliance"],
            "penalty": ["sanction", "fine", "punishment"],
            "appeal": ["challenge", "protest", "dispute"]
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in healthcare regulations and policy analysis.
            Your task is to optimize queries for better search results in healthcare regulations.
            
            Follow these optimization rules:
            1. Add relevant synonyms and related terms
            2. Include common variations of key terms
            3. Add specific program or regulation identifiers
            4. Maintain the original intent and meaning
            5. Keep the query clear and focused
            
            Common synonyms to consider:
            {synonyms}
            
            Optimize the following query:"""),
            ("human", "{query}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def optimize_query(self, query: str, program_type: Optional[str] = None) -> str:
        """Optimize a query for better search results.
        
        Args:
            query: The query to optimize
            program_type: Optional program type to include in optimization
            
        Returns:
            str: The optimized query
        """
        # Format synonyms for the prompt
        synonym_str = "\n".join(f"- {k}: {', '.join(v)}" for k, v in self.synonyms.items())
        
        # Get the optimized query from the LLM
        optimized = self.chain.invoke({
            "query": query,
            "synonyms": synonym_str
        })
        
        # Add program type if provided
        if program_type:
            optimized = f"{program_type} {optimized}"
        
        return optimized
    
    def add_synonyms(self, text: str) -> str:
        """Add synonyms to key terms in the text.
        
        Args:
            text: The text to add synonyms to
            
        Returns:
            str: The text with added synonyms
        """
        # Convert to lowercase for matching
        text_lower = text.lower()
        words = text_lower.split()
        
        # Find terms that have synonyms
        terms_with_synonyms = set()
        for word in words:
            for term, synonyms in self.synonyms.items():
                if word == term:
                    terms_with_synonyms.add(term)
        
        # Add synonyms for found terms
        if terms_with_synonyms:
            synonym_phrases = []
            for term in terms_with_synonyms:
                synonyms = self.synonyms[term]
                synonym_phrases.append(f"({term} OR {' OR '.join(synonyms)})")
            
            # Add synonyms as a parenthetical expression
            text = f"{text} {' '.join(synonym_phrases)}"
        
        return text
    
    def add_program_context(self, query: str, program_type: str) -> str:
        """Add program-specific context to the query.
        
        Args:
            query: The query to add context to
            program_type: The program type to add
            
        Returns:
            str: The query with added program context
        """
        program_contexts = {
            "HOSPICE": "hospice care end-of-life",
            "MPFS": "physician fee schedule payment",
            "SNF": "skilled nursing facility care",
            "IPPS": "inpatient hospital payment",
            "OPPS": "outpatient hospital payment"
        }
        
        if program_type in program_contexts:
            context = program_contexts[program_type]
            return f"{context} {query}"
        
        return query 