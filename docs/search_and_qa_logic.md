# Backend Search and Q&A Logic

## 1. Overview

The `app/core/search.py` module implements the core logic for semantic search and question answering over regulatory documents. It is the backend engine that powers the Q&A, citation, and retrieval-augmented generation (RAG) features of the RegHealth Navigator system.

## 2. Main Class: `ChatSearchService`

### Initialization
- Loads a FAISS vector index and associated metadata (chunked document passages).
- Builds a TF-IDF matrix and BM25 index for hybrid (dense + sparse) retrieval.
- Uses OpenAI API for embedding generation and LLM-based answer synthesis.

### Key Methods
- **`embed_text(text: str) -> np.ndarray`**  
  Generates a normalized embedding for the input text using OpenAI’s embedding API.

- **`search(query: str, filters: Dict = None, top_k: int = 20)`**  
  Retrieves the top-k most relevant document chunks for a query, optionally filtered by source file.  
  - Embeds the query.  
  - Computes cosine similarity with all (or filtered) document vectors.  
  - Returns the top-k chunks with similarity scores.

- **`generate_answer(query: str, chunks: List[Dict], max_context_length: int = 4000)`**  
  Constructs a prompt using the retrieved chunks and sends it to the OpenAI LLM (GPT-4o-mini) to generate a grounded, citation-backed answer.  
  - Enforces rules: only use provided content, cite sources, handle calculations with explicit variable checks, etc.  
  - Returns the answer, confidence score, and structured source metadata.

- **`ask_question(query: str, filters: Dict = None, top_k: int = 5)`**  
  Full pipeline for handling a user question:
  1. Moderation check (rejects unsafe queries).
  2. Retrieves relevant chunks.
  3. Generates an answer.
  4. Extracts and processes cited sources.
  5. Removes inline citations for frontend display.
  6. Returns both the answer and the actually cited chunks.

- **Helper methods**:  
  - `_extract_cited_chunks`: Returns only the chunks cited in the answer.  
  - `_process_cited_sources_and_print`: Logs detailed info about cited sources (for debugging).  
  - `_remove_citations`: Strips `[Source X]` tags from the answer text.

- **Standalone function**:  
  - `ask_query(query)`: Convenience wrapper for CLI/testing.

## 3. Usage in `main.py`

- The Flask app (`main.py`) initializes a `ChatSearchService` instance at startup, passing in the OpenAI API key and index paths from config.
- The service is injected into the app and used in API route handlers.

### Key Endpoints
- **`/api/chat`** (`POST`):  
  - Receives a user query (and optional filters).  
  - Calls `chat_service.ask_question(...)`.  
  - Returns the answer, confidence, and cited sources as JSON.

- **Other endpoints**:  
  - Document listing, summary, and comparison routes use similar patterns, but the core Q&A always routes through `ChatSearchService`.

## 4. Query Flow (End-to-End)

1. **User submits a question** via the frontend.
2. **Flask API** receives the request and calls `ChatSearchService.ask_question`.
3. **Moderation**: The query is checked for unsafe content.
4. **Retrieval**: The query is embedded and compared to all document chunks (optionally filtered).
5. **LLM Answer Generation**: The most relevant chunks are used as context for the LLM, which generates a citation-backed answer.
6. **Post-processing**: Cited sources are extracted, and inline citations are removed for frontend display.
7. **Response**: The answer, confidence, and sources are returned to the frontend.

## 5. Design Notes

- The system enforces strict grounding: answers must be based only on retrieved content, with explicit source citations.
- All retrieval and answer generation is logged for traceability.
- The architecture supports both filtered (document-specific) and unfiltered (corpus-wide) search. 
- Supports hybrid retrieval (dense + BM25), but the main flow uses dense (FAISS) retrieval, with BM25 only for assistance and future expansion.
- Supports source_file filtering, allowing frontend to specify document scope for more targeted comparison/Q&A.
- Supports OpenAI embedding model configuration, defaulting to text-embedding-3-small, configurable via config.
- End-to-end flow includes moderation, embedding, FAISS retrieval, prompt construction, LLM response, citation extraction, and frontend formatting, with detailed logging at all steps.
- Future support planned for Heuristic search, Summary, and other features (marked as TODO in code).
- Documentation is synchronized with search.py, with all parameters, API paths, and field names consistent with code implementation. 