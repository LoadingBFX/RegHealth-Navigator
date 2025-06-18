"""
Search Service - Core of Q&A System
Main functionality: Receive user query, return relevant document chunks
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import numpy as np
import faiss
import openai
import json
from typing import List, Tuple, Dict, Any
import logging
import sys
from pathlib import Path
logger = logging.getLogger(__name__)
sys.path.append(str(Path(__file__).parent.parent))


class ChatSearchService:
    """
    Complete RAG service:
    1. Retrieval: Search relevant chunks from pre-built index
    2. Generation: Use LLM to generate answers based on chunks

    Two search modes:
    1. With filter: Filter results from pre-built index
    2. Without filter: Direct search using pre-built FAISS index
    """

    def __init__(self, openai_api_key: str, faiss_index_path: str = "../rag_data/faiss.index",
                 metadata_path: str = "../rag_data/faiss_metadata.json"):
        """
        Initialize

        Args:
            openai_api_key: OpenAI API key
            faiss_index_path: FAISS index file path
            metadata_path: Metadata file path
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)

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

    def search_with_filter(self, query: str, filters: Dict[str, Any], top_k: int = 20) -> List[Dict]:
        """
        Search with filters
        Steps:
        1. First search more results using FAISS index (e.g., top_k*5)
        2. Apply filters to search results
        3. Return top_k results that meet the conditions

        Args:
            query: User's question
            filters: Filter conditions, e.g., {"year": 2024, "program": "hospice"}
            top_k: Return top k results

        Returns:
            List of relevant chunks
        """
        # Step 1: Search more results first, leaving room for filtering
        search_k = min(top_k * 5, self.faiss_index.ntotal)  # Search 5x results
        query_embedding = self.embed_text(query).reshape(1, -1)
        distances, indices = self.faiss_index.search(query_embedding, search_k)

        # Step 2: Apply filters
        filtered_results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.all_chunks):
                chunk = self.all_chunks[idx].copy()

                # Check if all filter conditions are met
                match = True
                for key, value in filters.items():
                    if chunk.get('metadata', {}).get(key) != value:
                        match = False
                        break

                if match:
                    chunk['distance'] = float(dist)
                    filtered_results.append(chunk)

                    # Stop if we have enough results
                    if len(filtered_results) >= top_k:
                        break

        logger.info(f"Returned {len(filtered_results)} results after filtering")
        return filtered_results

    def search_without_filter(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        Search without filters
        Directly use pre-built FAISS index

        Args:
            query: User's question
            top_k: Return top k results

        Returns:
            List of relevant chunks
        """
        # Create embedding for query
        query_embedding = self.embed_text(query).reshape(1, -1)

        # Search in FAISS index
        print("Searching FAISS index...")
        distances, indices = self.faiss_index.search(query_embedding, top_k)
        print("Search completed.")

        # Return results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.all_chunks):
                chunk = self.all_chunks[idx].copy()
                chunk['distance'] = float(dist)
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

            # if current_length + len(chunk_text) > max_context_length:
            #     break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)
            sources_used.append({
                "source_id": i+1,
                "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                "distance": chunk.get('distance', 0),
                "metadata": chunk.get('metadata', {})
            })

        context = "\n\n".join(context_parts)

        # Build prompt
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

        # Step 1: Retrieve relevant chunks
        if filters:
            logger.info(f"Retrieving with filters: {filters}")
            chunks = self.search_with_filter(query, filters, top_k)
        else:
            logger.info("Retrieving without filters")
            print(f"Retrieving without filters")
            chunks = self.search_without_filter(query, top_k)

        logger.info(f"Retrieved {len(chunks)} relevant chunks")

        # Step 2: Generate answer using LLM
        result = self.generate_answer(query, chunks)

        # Add query information
        result.update({
            "query": query,
            "filters_applied": filters,
            "retrieval_method": "filtered" if filters else "unfiltered"
        })

        logger.info(f"Answer generation completed, confidence: {result['confidence']}")
        return result

    def ask_simple_question(self, query: str, top_k: int = 3) -> str:
        """
        Simplified Q&A interface, only returns answer text

        Args:
            query: User's question
            top_k: Number of chunks to retrieve

        Returns:
            Answer text
        """
        result = self.ask_question(query, filters=None, top_k=top_k)
        return result["answer"]

    def get_chunk_by_index(self, index: int) -> Dict:
        """
        Get chunk by index

        Args:
            index: Chunk index

        Returns:
            Chunk dictionary
        """
        if 0 <= index < len(self.all_chunks):
            return self.all_chunks[index]
        else:
            raise IndexError(f"Index {index} out of range")

    def ask_query(self, query):
        # Example usage
        try:
            # Initialize service with actual FAISS index and metadata files
            # service = ChatSearchService(
            #     openai_api_key=OPENAI_API_KEY,  # Ensure you have set your OpenAI API key
            #     faiss_index_path="./rag_data/faiss.index",
            #     metadata_path="./rag_data/faiss_metadata.json"
            # )

            # Test complete RAG Q&A
            #query = "When did the SNF Prospective Payment System transition end?"
            #query = "When did the CY 2024 Medicare Physician Fee Schedule (MPFS) Final Rule become effective?"
            #query = "What is the finalized conversion factor for CY 2024, and how does it compare to CY 2023?"
            #query = "Summarize CY 2024 Medicare Physician Fee Schedule final rule?"
            #query = "Summarize  Correction of Errors in the Preambleof the CY 2025 PFS Final Rule"
            '''
            while True:
                query = input("Enter your question: \n")
                if not query.strip():
                    print("Exiting...")
                    break
                if query.lower() == "exit":
                    print("Exiting...")
                    break
            '''
            result = self.ask_question(query, top_k=10)
            print(f"Question: {result['query']}")
            print(f"Answer: {result['answer']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Number of sources used: {len(result['sources_used'])}")
            print("\nSource details:")
            for source in result['sources_used']:
                print(f"  - Source {source['source_id']}: {source['text_preview']}")
                print(f"    Similarity: {1-source['distance']:.3f}")


            #print("\n=== Retrieval Only Test (no answer generation) ===")
            # Retrieval only functionality (if needed)
            #chunks = service.search_without_filter(query, top_k=3)
            #print(f"Number of retrieved chunks: {len(chunks)}")
            #for i, chunk in enumerate(chunks):
            #    print(f"Chunk {i+1}: {chunk['text'][:100]}...")

            # prepare final output
            final_output = result['answer']

            return final_output

        except Exception as e:
            print(f"Error: {e}")
            print("Please ensure faiss.index and faiss_metadata.json files exist in the ./rag_data/ directory")
            print("Also ensure you have set the correct OpenAI API key")

# query = "When did the SNF Prospective Payment System transition end?"
# response = ask_query(query)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    service = ChatSearchService(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        faiss_index_path="./rag_data/faiss.index",
        metadata_path="./rag_data/faiss_metadata.json"
    )
    query = "When did the CY 2024 Medicare Physician Fee Schedule (MPFS) Final Rule become effective?"
    result = service.ask_query(query)
    print(result)