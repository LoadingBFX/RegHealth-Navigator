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
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import numpy as np
import faiss
import openai
import json
from typing import List, Dict, Any
import logging
# from key import OPENAI_API_KEY
from rank_bm25 import BM25Okapi

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ChatSearchService:
    def __init__(self, openai_api_key: str, faiss_index_path: str = "./rag_data/faiss.index",
                 metadata_path: str = "./rag_data/faiss_metadata.json"):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.faiss_index = faiss.read_index(faiss_index_path)

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.all_chunks = json.load(f)

        logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
        logger.info(f"Loaded metadata with {len(self.all_chunks)} chunks")

        if self.faiss_index.ntotal != len(self.all_chunks):
            logger.warning("Inconsistency detected between index and metadata!")

        # Build sparse index for hybrid search
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        self.doc_texts = [chunk['text'] for chunk in self.all_chunks]
        self.sparse_matrix = self.tfidf_vectorizer.fit_transform(self.doc_texts)

        self.tokenized_docs = [doc.split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(self.tokenized_docs)

    def embed_text(self, text: str) -> np.ndarray:
        response = self.openai_client.embeddings.create(
            #model="text-embedding-ada-002",
            model = "text-embedding-3-small",
            input=text
        )
        embedding = np.array(response.data[0].embedding, dtype='float32')
        return embedding / np.linalg.norm(embedding)

    # def search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 20) -> List[Dict]:
    #     # Step 1: Apply filters if present
    #     if filters:
    #         filtered_chunks = []
    #         for i, chunk in enumerate(self.all_chunks):
    #             if all(chunk.get("metadata", {}).get(k) == v for k, v in filters.items()):
    #                 chunk['__original_index__'] = i
    #                 filtered_chunks.append(chunk)
    #
    #         if not filtered_chunks:
    #             return []
    #
    #         embeddings = [self.faiss_index.reconstruct(chunk['__original_index__']) for chunk in filtered_chunks]
    #         doc_matrix = np.vstack(embeddings).astype("float32")
    #         doc_matrix /= np.linalg.norm(doc_matrix, axis=1, keepdims=True)
    #     else:
    #         doc_matrix = np.vstack([self.faiss_index.reconstruct(i) for i in range(self.faiss_index.ntotal)])
    #         doc_matrix /= np.linalg.norm(doc_matrix, axis=1, keepdims=True)
    #         filtered_chunks = self.all_chunks.copy()
    #
    #     # Step 2: Embed and normalize the query
    #     query_embedding = self.embed_text(query).reshape(1, -1)
    #
    #     # Step 3: Compute cosine similarity
    #     similarities = np.dot(doc_matrix, query_embedding.T).squeeze()
    #
    #     # Step 4: Hybrid: Get BM25 (TF-IDF) similarity scores
    #     sparse_query_vec = self.tfidf_vectorizer.transform([query])
    #     sparse_similarities = cosine_similarity(sparse_query_vec, self.sparse_matrix).flatten()
    #
    #     # Step 5: Combine scores (weighted sum)
    #     alpha = 0.3  # weight for embedding, 0.5 for sparse
    #     combined_scores = alpha * similarities + (1 - alpha) * sparse_similarities[:len(filtered_chunks)]
    #
    #     top_indices = np.argsort(-combined_scores)[:top_k]
    #
    #     # Step 6: Prepare results
    #     results = []
    #     for i in top_indices:
    #         chunk = filtered_chunks[i].copy()
    #         chunk["distance"] = float(1 - combined_scores[i])
    #         results.append(chunk)
    #
    #     return results

    def search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 20):
        query_embedding = self.embed_text(query).reshape(1, -1)
        distances, indices = self.faiss_index.search(query_embedding, top_k)
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.all_chunks):
                chunk = self.all_chunks[idx].copy()
                chunk["distance"] = float(dist)
                results.append(chunk)
        return results


    def generate_answer(self, query: str, chunks: List[Dict], max_context_length: int = 4000) -> Dict[str, Any]:
        if not chunks:
            return {
                "answer": "Sorry, I couldn't find relevant information to answer your question.",
                "confidence": 0.0,
                "sources_used": [],
                "source_file":[],
                "total_sources": 0
            }

        context_parts = []
        current_length = 0
        sources_used = []
        source_file=[]


        for i, chunk in enumerate(chunks):
            chunk_text = f"[Source {i+1}] {chunk['text']}"
            context_parts.append(chunk_text)
            current_length += len(chunk_text)

            file_name = chunk.get("metadata", {}).get("source_file", "")
            source_file.append(file_name)

            sources_used.append({
                "source_id": i+1,
                "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                "distance": chunk.get('distance', 0),
                "metadata": chunk.get('metadata', {}),
                "source_file":file_name
            })

        context = "\n\n".join(context_parts)

        prompt = f"""
                    You are a senior expert in medical policy and regulation analysis. Based on the following medical regulation document content, please answer the user's question.
                    Please follow these rules:
                    1. Only answer based on the provided content, do not add external knowledge
                    2. Cite relevant sources in your answer using the format [Source 1], [Source 2], etc.
                    3. Keep answers accurate, professional, and easy to understand
                    4. If there are multiple relevant pieces of information, organize them into a clear structure
                    5. For any question involving a calculation, comparison, or logical condition (e.g., percent change, difference, thresholds), first determine if the question requires such reasoning. Then identify all necessary variables, check if they are present in the retrieved sources, and only proceed with step-by-step computation if all variables are available. If any are missing, stop and return a clear message indicating which variable is unavailable. Do not assume, guess, or fabricate missing values. Cite sources using [Source 1], [Source 2], etc.
                    6. If the user question does not specify a year, prioritize using the most recent available source (source_file starts with year) in the sources as the basis for your answer.

                    Context content:
                    {context}

                    User question: {query}

                    Answer:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional medical regulation assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=1500,
                top_p=0.9
            )

            answer = response.choices[0].message.content

            avg_distance = sum(src['distance'] for src in sources_used) / len(sources_used)
            confidence = max(0, 1 - avg_distance / 2)

            return {
                "answer": answer,
                "confidence": round(confidence, 2),
                "sources_used": sources_used,
                "source_file":source_file,
                "total_sources": len(chunks),
                "context_length": current_length
            }

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "confidence": 0.0,
                "sources_used": sources_used,
                "total_sources": len(chunks)
            }

    def ask_question(self, query: str, filters: Dict[str, Any] = None, top_k: int = 5) -> Dict[str, Any]:
        logger.info(f"Processing question: {query}")

        response = self.openai_client.moderations.create(
            model="text-moderation-latest",
            input=query
        )

        if response.results[0].flagged:
            return {
                "answer": "Sorry, cannot process this query!",
                "query": query,
                "filters_applied": filters,
                "sources_used": []
            }

        chunks = self.search(query, filters=filters, top_k=top_k)
        result = self.generate_answer(query, chunks)
        
        # Background processing: Extract cited sources and print chunk information
        self._process_cited_sources_and_print(result, chunks)
        
        # Replace [Source X] in answer with corresponding source_file
        result['answer'] = self._replace_citations_with_files(result['answer'], result.get('sources_used', []))
        
        result.update({
            "query": query,
            "filters_applied": filters,
            "retrieval_method": "filtered" if filters else "unfiltered"
        })

        return result, chunks

    def _process_cited_sources_and_print(self, result: Dict[str, Any], chunks: List[Dict]) -> None:
        """
        Background processing: Extract cited sources and print chunk information
        """
        import re
        
        answer = result.get('answer', '')
        citation_pattern = r'\[Source\s+(\d+)\]'
        citations = re.findall(citation_pattern, answer)
        
        if not citations:
            print("🔍 No citations found in answer")
            return
            
        cited_source_numbers = list(set([int(citation) for citation in citations]))
        cited_source_numbers.sort()
        
        print(f"🔍 Found citations in answer: {citations}")
        print(f"📊 Unique source numbers cited: {cited_source_numbers}")
        
        sources_used = result.get('sources_used', [])
        
        print("\n" + "="*80)
        print("📚 CITED CHUNKS INFORMATION (Background)")
        print("="*80)
        
        for source_num in cited_source_numbers:
            source_index = source_num - 1
            
            if 0 <= source_index < len(sources_used):
                source = sources_used[source_index]
                if isinstance(source, dict):
                    source_file = source.get('source_file', '')
                    citation_count = citations.count(str(source_num))
                    
                    print(f"\n--- Source {source_num} (Cited {citation_count} times) ---")
                    print(f"📄 File: {source_file}")
                    print(f"📊 Distance: {source.get('distance', 0):.4f}")
                    print(f"📈 Similarity: {1-source.get('distance', 0):.4f}")
                    print(f"📝 Preview: {source.get('text_preview', '')}")
                    
                    # Find corresponding chunk and print complete information
                    for chunk in chunks:
                        chunk_source_file = chunk.get("metadata", {}).get("source_file", "")
                        if chunk_source_file == source_file:
                            print(f"📖 Full Text Length: {len(chunk.get('text', ''))} characters")
                            print(f"📖 Full Text (first 300 chars): {chunk.get('text', '')[:300]}...")
                            break
                    
                    if source.get('metadata'):
                        print(f"🏷️  Metadata: {source['metadata']}")
            else:
                print(f"\n⚠️  Source {source_num} not found in sources_used (index out of range)")
        
        print("\n" + "="*80)

    def _replace_citations_with_files(self, answer: str, sources_used: List[Dict]) -> str:
        """
        Replace [Source X] in answer with corresponding source_file and format display
        """
        import re
        
        def format_source_file(filename: str) -> str:
            """
            Format filename like 2022_MPFS_proposed_2021-14973.xml to:
            2022 MPFS proposed, Doc id: 2021-14973
            """
            if not filename or not filename.endswith('.xml'):
                return filename
            
            # Remove .xml extension
            name_without_ext = filename[:-4]
            
            # Split by underscore
            parts = name_without_ext.split('_')
            
            if len(parts) >= 4:
                year = parts[0]
                program = parts[1]
                type_name = parts[2]
                doc_id = parts[3]
                
                # Format output
                return f"{year} {program} {type_name}, Doc id: {doc_id}"
            else:
                # If format doesn't match, return original filename
                return filename
        
        def replace_citation(match):
            source_num = int(match.group(1))
            source_index = source_num - 1
            
            if 0 <= source_index < len(sources_used):
                source = sources_used[source_index]
                if isinstance(source, dict):
                    source_file = source.get('source_file', '')
                    formatted_name = format_source_file(source_file)
                    return f"[{formatted_name}]"
            
            # If corresponding source not found, keep original
            return match.group(0)
        
        citation_pattern = r'\[Source\s+(\d+)\]'
        return re.sub(citation_pattern, replace_citation, answer)

def ask_query(query):
    """
    Ask a query and return the answer along with chunks.
    
    Args:
        query: The question to ask
        
    Returns:
        tuple: (final_output, chunks)
    """
    try:
        # Initialize service with actual FAISS index and metadata files
        service = ChatSearchService(
            openai_api_key=OPENAI_API_KEY,  # Ensure you have set your OpenAI API key
            faiss_index_path="./rag_data/faiss.index",
            metadata_path="./rag_data/faiss_metadata.json"
        )

        result, chunks = service.ask_question(query, top_k=20)

        # prepare final output
        final_output = result['answer']

        return final_output, chunks

    except Exception as e:
        print(f"Error: {e}")
        print("Please ensure faiss.index and faiss_metadata.json files exist in the ./rag_data/ directory")
        print("Also ensure you have set the correct OpenAI API key")


if __name__ == "__main__":
    questions = [
        "How are PE RVUs established for specific services?",
    ]
    for i, query in enumerate(questions, 1):
        print("\n" + "=" * 60)
        print(f"📌 Test Case {i}")
        print("🔎 Question:", query)
        try:
            answer, sources = ask_query(query)

            # 显示答案
            print("\n✅ Answer:\n", answer)

        except Exception as e:
            print("❌ Error:", e)

        print("=" * 60 + "\n")
