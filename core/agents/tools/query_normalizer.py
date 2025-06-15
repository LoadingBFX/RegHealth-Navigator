"""
Query normalization tool for the RegHealth Navigator system.
This tool is responsible for normalizing and standardizing user queries.
"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class QueryNormalizer:
    """Tool for normalizing and standardizing user queries."""
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        """Initialize the query normalizer.
        
        Args:
            model_name: The name of the OpenAI model to use
        """
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)
        
        # Common abbreviations and their full forms
        self.abbreviations = {
            "pfs": "Medicare Physician Fee Schedule",
            "mpfs": "Medicare Physician Fee Schedule",
            "snf": "Skilled Nursing Facility",
            "ipps": "Inpatient Prospective Payment System",
            "opps": "Outpatient Prospective Payment System",
            "hipaa": "Health Insurance Portability and Accountability Act",
            "cms": "Centers for Medicare & Medicaid Services",
            "hcpcs": "Healthcare Common Procedure Coding System",
            "icd": "International Classification of Diseases",
            "drg": "Diagnosis-Related Group",
            "apc": "Ambulatory Payment Classification",
            "mac": "Medicare Administrative Contractor",
            "qpp": "Quality Payment Program",
            "mips": "Merit-based Incentive Payment System",
            "apm": "Alternative Payment Model"
        }
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert in healthcare regulations and policy analysis.
            Your task is to normalize and standardize user queries about healthcare regulations.
            
            Follow these rules:
            1. Expand all common healthcare abbreviations to their full forms
            2. Standardize terminology to official CMS/Medicare terms
            3. Maintain the original intent and meaning
            4. Keep the query clear and professional
            5. Preserve any specific dates, numbers, or technical terms
            
            Common abbreviations to expand:
            {abbreviations}
            
            Normalize the following query:"""),
            ("human", "{query}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def normalize_query(self, query: str) -> str:
        """Normalize and standardize a user query.
        
        Args:
            query: The user's query string
            
        Returns:
            str: The normalized query
        """
        # Format abbreviations for the prompt
        abbrev_str = "\n".join(f"- {k}: {v}" for k, v in self.abbreviations.items())
        
        # Get the normalized query from the LLM
        normalized = self.chain.invoke({
            "query": query,
            "abbreviations": abbrev_str
        })
        
        return normalized
    
    def expand_abbreviations(self, text: str) -> str:
        """Expand common healthcare abbreviations in text.
        
        Args:
            text: The text containing abbreviations
            
        Returns:
            str: The text with expanded abbreviations
        """
        # Convert to lowercase for matching
        text_lower = text.lower()
        
        # Sort abbreviations by length (longest first) to avoid partial matches
        sorted_abbrevs = sorted(self.abbreviations.items(), key=lambda x: len(x[0]), reverse=True)
        
        # Replace abbreviations using placeholders to avoid nested replacements
        placeholder_prefix = "PLACEHOLDER_"
        placeholders = {}
        for i, (abbrev, full_form) in enumerate(sorted_abbrevs):
            if abbrev in text_lower:
                placeholder = f"{placeholder_prefix}{i}"
                placeholders[placeholder] = full_form
                text_lower = text_lower.replace(abbrev, placeholder)
        
        # Replace placeholders with full forms
        for placeholder, full_form in placeholders.items():
            text_lower = text_lower.replace(placeholder, full_form)
        
        return text_lower 