"""
build_faiss.py

FAISS index builder for regulatory document embeddings.
Creates vector search index from preprocessed document chunks.

Functionality:
- FAISS index construction from document chunks
- OpenAI embedding generation with token management
- Batch processing with progress tracking
- Cost estimation and model configuration
- Long text splitting and token optimization
- Index persistence and metadata management

Process Flow:
1. Load preprocessed chunks from JSON file
2. Setup model configuration and tokenizer
3. Split long texts into token-appropriate chunks
4. Generate embeddings using OpenAI API
5. Create FAISS index with proper dimensionality
6. Add embeddings to index in batches
7. Save index and metadata files
8. Provide cost and performance statistics

Previous Team, Dhruv, Fanxing Bu
"""

import json
import os
import numpy as np
import faiss
from tqdm import tqdm
from dotenv import load_dotenv
import openai
import tiktoken
import sys
import argparse

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

def setup_model(model_name):
    """Setup model configuration and tokenizer from config."""
    if model_name is None:
        model_name = config.default_embedding_model
    
    try:
        model_config = config.get_embedding_model_config(model_name)
    except ValueError as e:
        raise ValueError(f"Invalid model '{model_name}': {e}")
    
    # Setup tokenizer
    encoding_type = config.get_embedding_model_encoding(model_name)
    if encoding_type == "cl100k_base":
        encoding = tiktoken.get_encoding("cl100k_base")
    else:
        encoding = tiktoken.encoding_for_model(encoding_type)
    
    return encoding, model_config

# Estimate token count for a string
def count_tokens(text, encoding):
    return len(encoding.encode(text))

# Split a long text into smaller parts by sentence
def split_into_chunks(text, max_tokens, encoding):
    sentences = text.split('. ')
    chunks = []
    current = ""
    for sentence in sentences:
        if count_tokens(current + sentence, encoding) < max_tokens - SAFETY_MARGIN:
            current += sentence + '. '
        else:
            chunks.append(current.strip())
            current = sentence + '. '
    if current:
        chunks.append(current.strip())
    return chunks

# Embedding with token-aware batching and long chunk splitting
def get_openai_embeddings(texts, model=None, encoding=None):
    embeddings = []
    batch = []
    batch_token_count = 0
    total_tokens = 0
    
    # Get model configuration from config
    if model is None:
        model = config.default_embedding_model
    
    model_config = config.get_embedding_model_config(model)
    
    # First pass: count total chunks after splitting
    print(f"🔍 Analyzing text chunks and counting tokens for model: {model}")
    print(f"💰 Model pricing: ${config.get_embedding_model_price(model):.5f} per 1K tokens")
    print(f"📝 Model description: {config.get_embedding_model_description(model)}")
    all_chunks = []
    for text in tqdm(texts, desc="Preparing chunks", unit="chunk"):
        if count_tokens(text, encoding) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
            sub_chunks = split_into_chunks(text, MAX_TOKENS_PER_CHUNK, encoding)
        else:
            sub_chunks = [text]
        
        for chunk in sub_chunks:
            if isinstance(chunk, str) and chunk.strip():
                tokens = count_tokens(chunk, encoding)
                if tokens > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                    encoded = encoding.encode(chunk)
                    chunk = encoding.decode(encoded[:MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN])
                    tokens = count_tokens(chunk, encoding)
                all_chunks.append(chunk)
                total_tokens += tokens
    
    print(f"📊 Total chunks to process: {len(all_chunks)}")
    print(f"📊 Total tokens to embed: {total_tokens}")
    
    # Second pass: generate embeddings with progress bar
    processed_chunks = 0
    batch_count = 0
    
    with tqdm(total=len(all_chunks), desc=f"Generating embeddings ({model})", unit="chunk") as pbar:
        for chunk in all_chunks:
            tokens = count_tokens(chunk, encoding)
            
            # Check if we need to process current batch
            if batch_token_count + tokens > MAX_TOKENS_PER_BATCH - SAFETY_MARGIN:
                if batch:  # Process current batch
                    batch_count += 1
                    pbar.set_postfix({
                        'batch': batch_count,
                        'batch_size': len(batch),
                        'tokens': batch_token_count
                    })
                    
                    response = client.embeddings.create(input=batch, model=model)
                    embeddings.extend([r.embedding for r in response.data])
                    processed_chunks += len(batch)
                    pbar.update(len(batch))
                    
                    # Reset batch
                    batch = []
                    batch_token_count = 0
            
            batch.append(chunk)
            batch_token_count += tokens
        
        # Process final batch
        if batch:
            batch_count += 1
            pbar.set_postfix({
                'batch': batch_count,
                'batch_size': len(batch),
                'tokens': batch_token_count
            })
            
            response = client.embeddings.create(input=batch, model=model)
            embeddings.extend([r.embedding for r in response.data])
            processed_chunks += len(batch)
            pbar.update(len(batch))

    estimated_cost = total_tokens / 1000 * config.get_embedding_model_price(model)
    print(f"\n✅ Embedding generation complete!")
    print(f"📊 Model used: {model}")
    print(f"📊 Total batches processed: {batch_count}")
    print(f"📊 Total chunks embedded: {len(embeddings)}")
    print(f"📊 Total tokens embedded: {total_tokens}")
    print(f"💰 Estimated cost: ${estimated_cost:.4f}")

    return embeddings, total_tokens

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Build FAISS index from chunks")
    parser.add_argument("--model", "-m", 
                      type=str,
                      help="Embedding model to use (defaults to config default)")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Instantiate OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Setup model and tokenizer
    encoding, model_config = setup_model(args.model)
    
    # Configuration
    MAX_TOKENS_PER_BATCH = 8191
    MAX_TOKENS_PER_CHUNK = 8191
    SAFETY_MARGIN = 50  # leave headroom

    # Ensure output folder exists
    output_folder = config.build_faiss_output_folder
    os.makedirs(output_folder, exist_ok=True)

    # Load preprocessed chunks from config path
    chunks_path = os.path.join(output_folder, "chunks.json")
    print("📁 Loading preprocessed chunks...")
    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    texts = [chunk["text"] for chunk in chunks]
    print(f"✅ Loaded {len(texts)} text chunks")

    # Get model name for display
    model_name = args.model if args.model else config.default_embedding_model
    
    print(f"🔄 Generating embeddings with OpenAI using model: {model_name}")
    print(f"💰 Model pricing: ${config.get_embedding_model_price(model_name):.5f} per 1K tokens")
    print(f"📝 Model description: {config.get_embedding_model_description(model_name)}")
    
    embeddings, total_tokens = get_openai_embeddings(texts, model_name, encoding)
    embedding_matrix = np.array(embeddings).astype("float32")

    # Create FAISS index
    print("🔍 Building FAISS index...")
    dimension = len(embedding_matrix[0])
    index = faiss.IndexFlatL2(dimension)

    # Add embeddings to index with progress bar
    print("📥 Adding embeddings to FAISS index...")
    batch_size = 1000  # Add embeddings in batches
    for i in tqdm(range(0, len(embedding_matrix), batch_size), desc="Building index", unit="batch"):
        batch_end = min(i + batch_size, len(embedding_matrix))
        index.add(embedding_matrix[i:batch_end])

    faiss.write_index(index, config.faiss_index_path)
    print("✅ FAISS index saved as " + config.faiss_index_path)

    # Save metadata and track per-document token usage
    print("💾 Preparing metadata...")
    faiss_metadata = []
    embedding_index = 0
    token_log_by_doc = {}

    with tqdm(chunks, desc="Processing metadata", unit="chunk") as pbar:
        for chunk in pbar:
            text = chunk["text"]
            source_file = chunk["metadata"].get("source_file", "unknown")
            token_log_by_doc.setdefault(source_file, 0)

            if count_tokens(text, encoding) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                sub_chunks = split_into_chunks(text, MAX_TOKENS_PER_CHUNK, encoding)
            else:
                sub_chunks = [text]

            for sub_chunk in sub_chunks:
                if not isinstance(sub_chunk, str) or not sub_chunk.strip():
                    continue
                if count_tokens(sub_chunk, encoding) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                    encoded = encoding.encode(sub_chunk)
                    sub_chunk = encoding.decode(encoded[:MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN])
                token_log_by_doc[source_file] += count_tokens(sub_chunk, encoding)
                faiss_metadata.append({
                    "text": sub_chunk,
                    "section_header": chunk["section_header"],
                    "metadata": chunk["metadata"]
                })
                embedding_index += 1
            
            pbar.set_postfix({'embeddings': embedding_index})

    # Save metadata
    metadata_path = os.path.join(output_folder, "faiss_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(faiss_metadata, f, indent=2)
    print("✅ Metadata saved as " + metadata_path)

    # Calculate and display costs by document
    print("\n💰 Cost breakdown by document:")
    doc_costs = {}
    for doc, tokens in token_log_by_doc.items():
        cost = tokens / 1000 * config.get_embedding_model_price(model_name)
        doc_costs[doc] = {"tokens": tokens, "cost": round(cost, 4)}
        print(f"- {doc}: {tokens} tokens ≈ ${cost:.4f}")

    # Save cost summary
    cost_summary_path = os.path.join(output_folder, "embedding_cost_summary.json")
    with open(cost_summary_path, "w") as f:
        json.dump({
            "total_tokens": total_tokens,
            "estimated_total_cost": round(total_tokens / 1000 * config.get_embedding_model_price(model_name), 4),
            "model_used": model_name,
            "per_document": doc_costs
        }, f, indent=2)
    print("✅ Cost summary saved as " + cost_summary_path)

    print(f"\n🎉 FAISS index build completed!")
    print(f"📊 Total embeddings: {len(embeddings)}")
    print(f"📊 Index dimension: {dimension}")
    print(f"💰 Total estimated cost: ${total_tokens / 1000 * config.get_embedding_model_price(model_name):.4f}")