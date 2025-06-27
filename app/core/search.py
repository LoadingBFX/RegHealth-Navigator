"""
Search Service - Core of Q&A System
Main functionality: Receive user query, return relevant document chunks
Earlier Authors (Daisy, Dhruv)
Modified by : Saicharan Emmadi

Steps followed :
    1) Query processing
        1.1) Moderation
        1.2) Classify - Q&A, Summary, Compare
    2) Find relevant chunks
        2.1) Use filters
        2.2) Generate embeddings for query
        2.3) Use Heuristic search (TODO)
        2.4) Use similarity search on FAISS
        2.5) Return relevant chunks
    3) Q&A
        3.1) Define prompt
        3.2) Generate response
        3.3) Prepare citations/sources
        3.4) Compute Confidence
    4) Summary (TODO)
"""
import os
import sys

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import numpy as np
import faiss
import openai
import json
from typing import List, Tuple, Dict, Any
import logging
from key import OPENAI_API_KEY 
logger = logging.getLogger(__name__)


class ChatSearchService:
    """
    Complete RAG service:
    1. Retrieval: Search relevant chunks from pre-built index
    2. Generation: Use LLM to generate answers based on chunks
    
    Two search modes:
    1. With filter: Filter results from pre-built index
    2. Without filter: Direct search using pre-built FAISS index
    """
    
    def __init__(self, openai_api_key: str, faiss_index_path: str = None, 
                 metadata_path: str = None):
        """
        Initialize
        
        Args:
            openai_api_key: OpenAI API key
            faiss_index_path: FAISS index file path (defaults to config.faiss_index_path)
            metadata_path: Metadata file path (defaults to config.faiss_metadata_path)
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Use config paths if not provided
        if faiss_index_path is None:
            faiss_index_path = config.faiss_index_path
        if metadata_path is None:
            metadata_path = config.faiss_metadata_path
        
        # Load pre-built FAISS index
        self.faiss_index = faiss.read_index(faiss_index_path)
        
        # Load metadata (contains all chunks information)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.all_chunks = json.load(f)
        
        logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
        logger.info(f"Loaded metadata with {len(self.all_chunks)} chunks")
        
        # Validate consistency between index and metadata
        if self.faiss_index.ntotal != len(self.all_chunks):
            logger.warning(f"Warning: FAISS index contains {self.faiss_index.ntotal} vectors, but metadata contains {len(self.all_chunks)} chunks. Inconsistency detected!")
        
    def embed_text(self, text: str) -> np.ndarray:
        """
        Convert text to vector
        
        Args:
            text: Text to convert (query)
            
        Returns:
            Vector (1536 dimensions)
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding, dtype='float32')

    def search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 20) -> List[Dict]:
        """
        Unified search: Apply filters first if provided, then do embedding similarity search.

        Args:
            query: User's question
            filters: Optional metadata filters (e.g., {"year": 2024})
            top_k: Number of results to return

        Returns:
            List of top_k relevant chunks
        """
        if filters:
            # Step 1: Apply filters
            filtered_chunks = []
            for i, chunk in enumerate(self.all_chunks):
                if all(chunk.get("metadata", {}).get(k) == v for k, v in filters.items()):
                    chunk['__original_index__'] = i  # for FAISS lookup
                    filtered_chunks.append(chunk)

            logger.info(f"Filtered to {len(filtered_chunks)} chunks before similarity search")

            if not filtered_chunks:
                return []

            # Step 2: Get embeddings for filtered chunks
            embeddings = []
            for chunk in filtered_chunks:
                faiss_idx = chunk["__original_index__"]
                embeddings.append(self.faiss_index.reconstruct(faiss_idx))

            doc_matrix = np.vstack(embeddings).astype("float32")
        else:
            # No filters, use full FAISS index
            doc_matrix = np.vstack([self.faiss_index.reconstruct(i) for i in range(self.faiss_index.ntotal)])
            filtered_chunks = self.all_chunks.copy()

        # Step 3: Embed the query
        query_embedding = self.embed_text(query).reshape(1, -1)

        # Step 4: Compute distances manually
        distances = np.linalg.norm(doc_matrix - query_embedding, axis=1)
        sorted_indices = np.argsort(distances)[:top_k]

        # Step 5: Return top_k results
        results = []
        for rank in sorted_indices:
            chunk = filtered_chunks[rank].copy()
            chunk["distance"] = float(distances[rank])
            results.append(chunk)

        return results

    def generate_answer(self, query: str, chunks: List[Dict], max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Use LLM to generate answers based on retrieved chunks
        
        Args:
            query: User's question
            chunks: Retrieved relevant chunks
            max_context_length: Maximum context length (character count)
            
        Returns:
            Dictionary containing answer, confidence, and sources used
        """
        if not chunks:
            return {
                "answer": "Sorry, I couldn't find relevant information to answer your question.",
                "confidence": 0.0,
                "sources_used": [],
                "total_sources": 0
            }
        
        # Build context, ensuring it doesn't exceed length limit
        context_parts = []
        current_length = 0
        sources_used = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = f"[Source {i+1}] {chunk['text']}"
            
            #if current_length + len(chunk_text) > max_context_length:
            #    print('ERROR')
            #    import pdb;pdb.set_trace()
                
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            sources_used.append({
                "source_id": i+1,
                "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                "distance": chunk.get('distance', 0),
                "metadata": chunk.get('metadata', {})
            })
        
        context = "\n\n".join(context_parts)

        prompt = f"""Based on the following medical regulation document content, please answer the user's question.

        Please follow these rules:
        1. Only answer based on the provided content, do not add external knowledge
        2. If the provided content is insufficient to answer the question, please state this clearly
        3. Cite relevant sources in your answer using the format [Source1], [Source2], etc.
        4. Keep answers accurate, professional, and easy to understand
        5. If there are multiple relevant pieces of information, organize them into a clear structure

        Context content:
        {context}

        User question: {query}

        Answer:"""

        '''
        # Build prompt
        prompt = f"""Based on the following medical regulation document content, please answer the user's question.

        Please follow these rules:
        1. Only answer based on the provided content, do not add external knowledge
        2. If the provided content is insufficient to answer the question, please state 'Sorry, I couldn't find relevant information to answer your question.' "
        3. Cite relevant sources in your answer using the format [Source1], [Source2], etc.
        4. Keep answers accurate, professional, and easy to understand
        5. If there are multiple relevant pieces of information, organize them into a clear structure


Context content:
{context}

User question: {query}

Answer:"""
        '''
        try:
            # Call OpenAI GPT-4
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use gpt-4o-mini for lower cost
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a professional medical regulation assistant, specializing in helping users understand Medicare-related regulatory documents."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Lower randomness for more consistency
                max_tokens=1000,
                top_p=0.9
            )
            
            answer = response.choices[0].message.content
            
            # Simple confidence estimation (based on similarity of retrieved chunks)
            if sources_used:
                avg_distance = sum(source['distance'] for source in sources_used) / len(sources_used)
                confidence = max(0, 1 - (avg_distance / 2))  # Simple confidence calculation
            else:
                confidence = 0.0
            
            return {
                "answer": answer,
                "confidence": round(confidence, 2),
                "sources_used": sources_used,
                "total_sources": len(chunks),
                "context_length": current_length
            }
            
        except Exception as e:
            logger.error(f"Error generating answer with LLM: {e}")
            return {
                "answer": f"Sorry, encountered a technical issue while generating the answer: {str(e)}",
                "confidence": 0.0,
                "sources_used": sources_used,
                "total_sources": len(chunks)
            }
    
    def ask_question(self, query: str, filters: Dict[str, Any] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Complete RAG Q&A process: Retrieval + Generation
        
        Args:
            query: User's question
            filters: Optional filter conditions
            top_k: Number of chunks to retrieve
            
        Returns:
            Complete Q&A result including answer, sources, and metadata
        """
        logger.info(f"Processing question: {query}")

        response = self.openai_client.moderations.create(
            model="text-moderation-latest",  # or "text-moderation-007"
            input=query  # string or list[str]
        )

        result = response.results[0]
        if result.flagged:
            print("Input was flagged.")
            result = {
                "answer": "Sorry, cannot process this query!",
                "query": query,
                "filters_applied": filters,
                'sources_used':[]
            }
            return result

        chunks = self.search(query, filters=filters, top_k=top_k)
        logger.info(f"Retrieved {len(chunks)} relevant chunks")

        '''
        # Step 2 : # classify query category
        classification_prompt = f"""
        You are a helpful assistant. Classify the following query into one of three categories:
        1. Summarize
        2. Compare
        3. Other

        Only respond with: Summarize, Compare, or Other.

        Query: \"{query}\"
        """

        chat_response =  self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": "You are a classification assistant."},
                {"role": "user", "content": classification_prompt}
            ],
            temperature=0
        )

        classification = chat_response.choices[0].message.content.strip()
        print(classification)
        '''

        # Step 3: Generate answer using LLM
        result = self.generate_answer(query, chunks)

        # Add query information
        result.update({
            "query": query,
            "filters_applied": filters,
            "retrieval_method": "filtered" if filters else "unfiltered"
        })
        
        logger.info(f"Answer generation completed...")
        return result, chunks

def ask_query(query):
    # Example usage
    try:
        # Initialize service with actual FAISS index and metadata files
        service = ChatSearchService(
            openai_api_key=OPENAI_API_KEY,  # Ensure you have set your OpenAI API key
            faiss_index_path=config.faiss_index_path,
            metadata_path=config.faiss_metadata_path
        )

        result, chunks = service.ask_question(query, top_k=10)
        print(f"Question: {result['query']}")
        print(f"Answer: {result['answer']}")
        #print(f"Confidence: {result['confidence']}")
        print(f"Number of sources used: {len(result['sources_used'])}")
        if len(result['sources_used']) != 0:
            print("\nSource details:")
            for source in result['sources_used']:
                print(f"  - Source {source['source_id']}: {source['text_preview']}")
                print(f"    Similarity: {1-source['distance']:.3f}")

        # prepare final output
        final_output = result['answer']

        return final_output
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Please ensure faiss.index and faiss_metadata.json files exist in the configured directories")
        print("Also ensure you have set the correct OpenAI API key")

# Test complete RAG Q&A
#query = "I hate you. I'm going to hurt you and everyone like you."
#query = "Summarize abc"
#query = "When did the SNF Prospective Payment System transition end?"
#query = "When did the CY 2024 Medicare Physician Fee Schedule (MPFS) Final Rule become effective?"
#query = "What is the finalized conversion factor for CY 2024, and how does it compare to CY 2023?"
#query = "Summarize CY 2024 Medicare Physician Fee Schedule final rule?"
#query = "Summarize  Correction of Errors in the Preambleof the CY 2025 PFS Final Rule"
query = "When did the SNF Prospective Payment System transition end?"

response = ask_query(query)
