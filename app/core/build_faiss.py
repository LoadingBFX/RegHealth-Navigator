import json
import os
import numpy as np
import faiss
from tqdm import tqdm
from dotenv import load_dotenv
import openai
import tiktoken



# Estimate token count for a string
def count_tokens(text):
    return len(encoding.encode(text))

# Split a long text into smaller parts by sentence
def split_into_chunks(text, max_tokens):
    sentences = text.split('. ')
    chunks = []
    current = ""
    for sentence in sentences:
        if count_tokens(current + sentence) < max_tokens - SAFETY_MARGIN:
            current += sentence + '. '
        else:
            chunks.append(current.strip())
            current = sentence + '. '
    if current:
        chunks.append(current.strip())
    return chunks

# Embedding with token-aware batching and long chunk splitting
def get_openai_embeddings(texts, model="text-embedding-ada-002"):
    embeddings = []
    batch = []
    batch_token_count = 0
    total_tokens = 0
    
    # First pass: count total chunks after splitting
    print("🔍 Analyzing text chunks and counting tokens...")
    all_chunks = []
    for text in tqdm(texts, desc="Preparing chunks", unit="chunk"):
        if count_tokens(text) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
            sub_chunks = split_into_chunks(text, MAX_TOKENS_PER_CHUNK)
        else:
            sub_chunks = [text]
        
        for chunk in sub_chunks:
            if isinstance(chunk, str) and chunk.strip():
                tokens = count_tokens(chunk)
                if tokens > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                    encoded = encoding.encode(chunk)
                    chunk = encoding.decode(encoded[:MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN])
                    tokens = count_tokens(chunk)
                all_chunks.append(chunk)
                total_tokens += tokens
    
    print(f"📊 Total chunks to process: {len(all_chunks)}")
    print(f"📊 Total tokens to embed: {total_tokens}")
    
    # Second pass: generate embeddings with progress bar
    processed_chunks = 0
    batch_count = 0
    
    with tqdm(total=len(all_chunks), desc="Generating embeddings", unit="chunk") as pbar:
        for chunk in all_chunks:
            tokens = count_tokens(chunk)
            
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

    estimated_cost = total_tokens / 1000 * 0.0001
    print(f"\n✅ Embedding generation complete!")
    print(f"📊 Total batches processed: {batch_count}")
    print(f"📊 Total chunks embedded: {len(embeddings)}")
    print(f"📊 Total tokens embedded: {total_tokens}")
    print(f"💰 Estimated cost: ${estimated_cost:.4f}")

    return embeddings, total_tokens




if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Instantiate OpenAI client
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # Ensure output folder exists
    os.makedirs("./rag_data", exist_ok=True)

    # Load preprocessed chunks
    print("📁 Loading preprocessed chunks...")
    with open("./rag_data/chunks.json", "r") as f:
        chunks = json.load(f)

    texts = [chunk["text"] for chunk in chunks]
    print(f"✅ Loaded {len(texts)} text chunks")

    # Tokenizer setup for ada-002
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    #encoding = tiktoken.get_encoding("o200k_base")
    MAX_TOKENS_PER_BATCH = 8191
    MAX_TOKENS_PER_CHUNK = 8191
    SAFETY_MARGIN = 50  # leave headroom

    print("🔄 Generating embeddings with OpenAI using token-aware batching and splitting long chunks...")
    embeddings, total_tokens = get_openai_embeddings(texts)
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

    faiss.write_index(index, "./rag_data/faiss.index")
    print("✅ FAISS index saved as ./rag_data/faiss.index")

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

            if count_tokens(text) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                sub_chunks = split_into_chunks(text, MAX_TOKENS_PER_CHUNK)
            else:
                sub_chunks = [text]

            for sub_chunk in sub_chunks:
                if not isinstance(sub_chunk, str) or not sub_chunk.strip():
                    continue
                if count_tokens(sub_chunk) > MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN:
                    encoded = encoding.encode(sub_chunk)
                    sub_chunk = encoding.decode(encoded[:MAX_TOKENS_PER_CHUNK - SAFETY_MARGIN])
                token_log_by_doc[source_file] += count_tokens(sub_chunk)
                faiss_metadata.append({
                    "text": sub_chunk,
                    "section_header": chunk["section_header"],
                    "metadata": chunk["metadata"]
                })
                embedding_index += 1
            
            pbar.set_postfix({'embeddings': embedding_index})

    # Save metadata
    with open("./rag_data/faiss_metadata.json", "w") as f:
        json.dump(faiss_metadata, f, indent=2)
    print("✅ Metadata saved as ./rag_data/faiss_metadata.json")

    # Print token usage per document
    print("\n📄 Token usage by document:")
    doc_costs = {}
    for doc, tokens in token_log_by_doc.items():
        cost = tokens / 1000 * 0.0001
        doc_costs[doc] = {"tokens": tokens, "cost": round(cost, 4)}
        print(f"- {doc}: {tokens} tokens ≈ ${cost:.4f}")

    # Save cost summary
    with open("./rag_data/embedding_cost_summary.json", "w") as f:
        json.dump({
            "total_tokens": total_tokens,
            "estimated_total_cost": round(total_tokens / 1000 * 0.0001, 4),
            "per_document": doc_costs
        }, f, indent=2)
    print("💾 Cost summary saved as rag_data/embedding_cost_summary.json")
    print("\n🎉 RAG embedding pipeline completed successfully!")