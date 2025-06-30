"""
incremental_faiss.py

Module for incrementally updating FAISS index with new embeddings.
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
from pathlib import Path
from typing import List, Dict, Optional
import time
import random

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Configure logging
import logging
logger = logging.getLogger(__name__)

class IncrementalFAISS:
    """
    Class for incrementally updating FAISS index with new embeddings.
    
    This class supports:
    - Loading existing FAISS index
    - Generating embeddings for new chunks
    - Adding new embeddings to existing index
    - Updating metadata files
    """
    
    def __init__(self, model: str = None):
        """
        Initialize IncrementalFAISS.
        
        Args:
            model: Embedding model to use. If None, uses default from config.
                   Available models are defined in config files.
        """
        # Load environment variables
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Set model from config
        self.model = model if model else config.default_embedding_model
        
        # Get model configuration from config
        try:
            self.model_config = config.get_embedding_model_config(self.model)
        except ValueError as e:
            raise ValueError(f"Invalid model '{self.model}': {e}")
        
        # Setup tokenizer based on model configuration
        encoding_type = config.get_embedding_model_encoding(self.model)
        if encoding_type == "cl100k_base":
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = tiktoken.encoding_for_model(encoding_type)
        
        # Configuration
        self.max_tokens_per_batch = 8191
        self.max_tokens_per_chunk = 8191
        self.safety_margin = 50
        
        # Paths
        self.output_folder = config.build_faiss_output_folder
        self.chunks_path = os.path.join(self.output_folder, "chunks.json")
        self.faiss_index_path = config.faiss_index_path
        self.metadata_path = os.path.join(self.output_folder, "faiss_metadata.json")
        
        logger.info(f"🚀 Initialized IncrementalFAISS with model: {self.model}")
        logger.info(f"💰 Model pricing: ${config.get_embedding_model_price(self.model):.5f} per 1K tokens")
        logger.info(f"📝 Model description: {config.get_embedding_model_description(self.model)}")
        logger.info(f"📁 Output folder: {self.output_folder}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def split_into_chunks(self, text: str, max_tokens: int) -> List[str]:
        """Split long text into smaller parts by sentence."""
        sentences = text.split('. ')
        chunks = []
        current = ""
        for sentence in sentences:
            if self.count_tokens(current + sentence) < max_tokens - self.safety_margin:
                current += sentence + '. '
            else:
                chunks.append(current.strip())
                current = sentence + '. '
        if current:
            chunks.append(current.strip())
        return chunks

    def get_embeddings_for_chunks(self, chunks: List[str], model: str = None) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks.
        Handles OpenAI API 429 errors with exponential backoff and logs all errors clearly.
        Only returns embeddings if all succeed; otherwise returns None.
        """
        if not chunks:
            return []
        if model is None:
            model = self.model
        embeddings = []
        batch = []
        batch_token_count = 0
        all_chunks = []
        max_retries = 5
        base_delay = 1  # Start with 1 second
        
        # Validate and prepare chunks
        for text in chunks:
            if self.count_tokens(text) > self.max_tokens_per_chunk - self.safety_margin:
                sub_chunks = self.split_into_chunks(text, self.max_tokens_per_chunk)
            else:
                sub_chunks = [text]
            for chunk in sub_chunks:
                if isinstance(chunk, str) and chunk.strip():
                    tokens = self.count_tokens(chunk)
                    if tokens > self.max_tokens_per_chunk - self.safety_margin:
                        encoded = self.encoding.encode(chunk)
                        chunk = self.encoding.decode(encoded[:self.max_tokens_per_chunk - self.safety_margin])
                    all_chunks.append(chunk)
        
        def embed_batch(batch, model):
            """Embed a batch with robust rate limit handling."""
            for attempt in range(max_retries):
                try:
                    # Validate batch size before sending
                    total_tokens = sum(self.count_tokens(text) for text in batch)
                    if total_tokens > self.max_tokens_per_batch:
                        logger.warning(f"⚠️ Batch too large ({total_tokens} tokens), splitting...")
                        # Split batch if too large
                        mid = len(batch) // 2
                        first_half = embed_batch(batch[:mid], model)
                        second_half = embed_batch(batch[mid:], model)
                        if first_half is None or second_half is None:
                            return None
                        return first_half + second_half
                    
                    response = self.client.embeddings.create(input=batch, model=model)
                    return [r.embedding for r in response.data]
                    
                except openai.RateLimitError as e:
                    # Exponential backoff with jitter
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    
                except openai.BadRequestError as e:
                    logger.error(f"❌ Bad request error: {e}")
                    # Check if it's a token limit issue
                    if "maximum context length" in str(e).lower():
                        logger.error(f"❌ Token limit exceeded. Batch size: {len(batch)}, tokens: {total_tokens}")
                        # Try with smaller batch
                        if len(batch) > 1:
                            mid = len(batch) // 2
                            first_half = embed_batch(batch[:mid], model)
                            second_half = embed_batch(batch[mid:], model)
                            if first_half is None or second_half is None:
                                return None
                            return first_half + second_half
                    break
                    
                except Exception as e:
                    logger.error(f"❌ OpenAI API error: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Failed after {max_retries} attempts")
                    break
            
            logger.error(f"❌ Failed to get embeddings after {max_retries} retries")
            return None
        
        with tqdm(total=len(all_chunks), desc=f"Generating embeddings ({model})", unit="chunk") as pbar:
            for chunk in all_chunks:
                tokens = self.count_tokens(chunk)
                
                # Check if adding this chunk would exceed batch limit
                if batch_token_count + tokens > self.max_tokens_per_batch - self.safety_margin:
                    if batch:
                        result = embed_batch(batch, model)
                        if result is None:
                            logger.error("❌ Batch embedding failed, aborting all processing")
                            return None
                        embeddings.extend(result)
                        pbar.update(len(batch))
                        batch = []
                        batch_token_count = 0
                
                batch.append(chunk)
                batch_token_count += tokens
            
            # Process final batch
            if batch:
                result = embed_batch(batch, model)
                if result is None:
                    logger.error("❌ Final batch embedding failed")
                    return None
                embeddings.extend(result)
                pbar.update(len(batch))
        
        return embeddings

    def load_existing_index(self) -> Optional[faiss.Index]:
        """Load existing FAISS index if it exists."""
        if os.path.exists(self.faiss_index_path):
            logger.info(f"📁 Loading existing FAISS index from {self.faiss_index_path}")
            return faiss.read_index(self.faiss_index_path)
        else:
            logger.info("🆕 No existing FAISS index found, will create new one")
            return None

    def load_existing_metadata(self) -> List[Dict]:
        """Load existing metadata if it exists."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        return []

    def create_new_index(self, dimension: int) -> faiss.Index:
        """Create a new FAISS index."""
        logger.info(f"🔍 Creating new FAISS index with dimension {dimension}")
        return faiss.IndexFlatL2(dimension)

    def update_index_with_new_chunks(self, new_chunks: List[Dict]) -> int:
        """
        Update FAISS index with new chunks.
        This method ensures that the same exact chunks are used for both embeddings and metadata.
        
        Args:
            new_chunks: List of new chunk dictionaries
            
        Returns:
            Number of new embeddings added
        """
        if not new_chunks:
            logger.info("✅ No new chunks to process")
            return 0
        
        # Extract and prepare text chunks (same logic as get_embeddings_for_chunks)
        all_chunks = []
        for chunk in new_chunks:
            text = chunk["text"]
            
            if self.count_tokens(text) > self.max_tokens_per_chunk - self.safety_margin:
                sub_chunks = self.split_into_chunks(text, self.max_tokens_per_chunk)
            else:
                sub_chunks = [text]
            
            for sub_chunk in sub_chunks:
                if isinstance(sub_chunk, str) and sub_chunk.strip():
                    tokens = self.count_tokens(sub_chunk)
                    if tokens > self.max_tokens_per_chunk - self.safety_margin:
                        encoded = self.encoding.encode(sub_chunk)
                        sub_chunk = self.encoding.decode(encoded[:self.max_tokens_per_chunk - self.safety_margin])
                    
                    # Store both the processed text and original chunk metadata
                    all_chunks.append({
                        "text": sub_chunk,
                        "original_chunk": chunk
                    })
        
        if not all_chunks:
            logger.warning("⚠️ No valid chunks after processing")
            return 0
        
        # Extract text for embedding generation
        texts = [chunk["text"] for chunk in all_chunks]
        logger.info(f"📝 Processing {len(texts)} text chunks with model: {self.model}")
        
        # Generate embeddings
        embeddings = self.get_embeddings_for_chunks(texts)
        
        if not embeddings:
            logger.warning("⚠️ No embeddings generated")
            return 0
        
        # Load or create index
        index = self.load_existing_index()
        if index is None:
            dimension = len(embeddings[0])
            index = self.create_new_index(dimension)
        
        # Convert embeddings to numpy array
        embedding_matrix = np.array(embeddings).astype("float32")
        
        # Add embeddings to index
        logger.info(f"📥 Adding {len(embedding_matrix)} embeddings to FAISS index")
        index.add(embedding_matrix)
        
        # Save updated index
        faiss.write_index(index, self.faiss_index_path)
        logger.info(f"✅ FAISS index saved to {self.faiss_index_path}")
        
        # Update metadata with the exact same chunks that were embedded
        self._update_metadata_with_processed_chunks(all_chunks)
        
        return len(embeddings)

    def _update_metadata_with_processed_chunks(self, processed_chunks: List[Dict]) -> None:
        """
        Update metadata with the exact chunks that were processed for embeddings.
        
        Args:
            processed_chunks: List of processed chunks with text and original_chunk
        """
        existing_metadata = self.load_existing_metadata()
        
        # Create metadata entries for each processed chunk
        new_metadata_entries = []
        for processed_chunk in processed_chunks:
            original_chunk = processed_chunk["original_chunk"]
            new_metadata_entries.append({
                "text": processed_chunk["text"],
                "section_header": original_chunk["section_header"],
                "metadata": original_chunk["metadata"]
            })
        
        # Add new entries to existing metadata
        existing_metadata.extend(new_metadata_entries)
        
        # Save updated metadata
        with open(self.metadata_path, "w") as f:
            json.dump(existing_metadata, f, indent=2)
        
        logger.info(f"📦 Updated metadata: {len(existing_metadata)} total entries")

    def remove_metadata_for_file(self, file_path: str) -> int:
        """
        Remove metadata entries for a specific file and update FAISS index accordingly.
        
        Args:
            file_path: Path to the file (relative to data directory)
            
        Returns:
            Number of metadata entries removed
        """
        existing_metadata = self.load_existing_metadata()
        original_count = len(existing_metadata)
        
        # Filter out entries for the specified file
        filtered_metadata = []
        for entry in existing_metadata:
            entry_file = entry["metadata"].get("source_file", "")
            if entry_file != file_path:
                filtered_metadata.append(entry)
        
        removed_count = original_count - len(filtered_metadata)
        
        if removed_count > 0:
            # Save updated metadata
            with open(self.metadata_path, "w") as f:
                json.dump(filtered_metadata, f, indent=2)
            
            # Rebuild FAISS index to match the filtered metadata
            logger.info(f"🔄 Rebuilding FAISS index after removing {removed_count} entries for {file_path}")
            rebuild_result = self.rebuild_index_from_existing_embeddings()
            
            if "error" in rebuild_result:
                logger.warning(f"⚠️ Efficient rebuild failed: {rebuild_result['error']}")
                logger.info("🔄 Falling back to full rebuild with API calls")
                rebuild_result = self.rebuild_index_from_chunks()
            
            logger.info(f"🧹 Removed {removed_count} metadata entries for {file_path}")
        
        return removed_count

    def update_metadata_with_new_chunks(self, new_chunks: List[Dict]) -> None:
        """
        Update metadata file with new chunks.
        This method should match the exact chunks that were used to generate embeddings.
        """
        existing_metadata = self.load_existing_metadata()
        
        # Process new chunks to match exactly what was sent to embedding API
        new_metadata_entries = []
        for chunk in new_chunks:
            text = chunk["text"]
            
            # Use the same splitting logic as get_embeddings_for_chunks
            if self.count_tokens(text) > self.max_tokens_per_chunk - self.safety_margin:
                sub_chunks = self.split_into_chunks(text, self.max_tokens_per_chunk)
            else:
                sub_chunks = [text]
            
            for sub_chunk in sub_chunks:
                if not isinstance(sub_chunk, str) or not sub_chunk.strip():
                    continue
                
                # Apply the same token limit as in get_embeddings_for_chunks
                if self.count_tokens(sub_chunk) > self.max_tokens_per_chunk - self.safety_margin:
                    encoded = self.encoding.encode(sub_chunk)
                    sub_chunk = self.encoding.decode(encoded[:self.max_tokens_per_chunk - self.safety_margin])
                
                new_metadata_entries.append({
                    "text": sub_chunk,
                    "section_header": chunk["section_header"],
                    "metadata": chunk["metadata"]
                })
        
        # Add new entries to existing metadata
        existing_metadata.extend(new_metadata_entries)
        
        # Save updated metadata
        with open(self.metadata_path, "w") as f:
            json.dump(existing_metadata, f, indent=2)
        
        logger.info(f"📦 Updated metadata: {len(existing_metadata)} total entries")

    def process_incremental_update(self, new_chunks: List[Dict]) -> Dict:
        """
        Process incremental update with new chunks.
        
        Args:
            new_chunks: List of new chunk dictionaries
            
        Returns:
            Dictionary with update statistics
        """
        logger.info(f"🔄 Starting incremental FAISS update with {len(new_chunks)} new chunks")
        
        # Update FAISS index and metadata (metadata is now handled within update_index_with_new_chunks)
        new_embeddings_count = self.update_index_with_new_chunks(new_chunks)
        
        # Calculate costs
        total_tokens = sum(self.count_tokens(chunk["text"]) for chunk in new_chunks)
        estimated_cost = total_tokens / 1000 * config.get_embedding_model_price(self.model)
        
        stats = {
            "new_chunks_processed": len(new_chunks),
            "new_embeddings_added": new_embeddings_count,
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 4),
            "model_used": self.model,
            "model_pricing": config.get_embedding_model_price(self.model)
        }
        
        logger.info(f"✅ Incremental update completed:")
        logger.info(f"   - New chunks: {stats['new_chunks_processed']}")
        logger.info(f"   - New embeddings: {stats['new_embeddings_added']}")
        logger.info(f"   - Total tokens: {stats['total_tokens']}")
        logger.info(f"   - Model: {stats['model_used']}")
        logger.info(f"   - Estimated cost: ${stats['estimated_cost']}")
        
        return stats

    def get_index_stats(self) -> Dict:
        """Get statistics about the current FAISS index."""
        if not os.path.exists(self.faiss_index_path):
            return {"error": "FAISS index not found"}
        
        index = faiss.read_index(self.faiss_index_path)
        metadata = self.load_existing_metadata()
        
        return {
            "index_size": index.ntotal,
            "index_dimension": index.d,
            "metadata_entries": len(metadata),
            "index_path": self.faiss_index_path
        }

    def rebuild_index_from_existing_embeddings(self) -> Dict:
        """
        Rebuild FAISS index using existing embeddings (no API calls).
        This is more efficient when files are deleted.
        
        Returns:
            Dictionary with rebuild statistics
        """
        logger.info("🔄 Rebuilding FAISS index from existing embeddings (no API calls)")
        
        # Load existing index and metadata
        if not os.path.exists(self.faiss_index_path):
            logger.error(f"❌ FAISS index not found: {self.faiss_index_path}")
            return {"error": "FAISS index not found"}
        
        if not os.path.exists(self.metadata_path):
            logger.error(f"❌ Metadata not found: {self.metadata_path}")
            return {"error": "Metadata not found"}
        
        # Load chunks to get the current valid chunks
        chunks_file = os.path.join(self.output_folder, "chunks.json")
        if not os.path.exists(chunks_file):
            logger.error(f"❌ Chunks file not found: {chunks_file}")
            return {"error": "Chunks file not found"}
        
        with open(chunks_file, "r") as f:
            current_chunks = json.load(f)
        
        with open(self.metadata_path, "r") as f:
            existing_metadata = json.load(f)
        
        # Create a set of valid chunk texts for fast lookup
        valid_chunk_texts = {chunk["text"] for chunk in current_chunks}
        
        # Filter metadata to only include chunks that still exist
        filtered_metadata = []
        valid_embeddings = []
        
        logger.info(f"🔍 Filtering {len(existing_metadata)} metadata entries")
        
        for i, metadata_entry in enumerate(existing_metadata):
            if metadata_entry["text"] in valid_chunk_texts:
                filtered_metadata.append(metadata_entry)
                # Extract embedding from existing index
                if i < len(existing_metadata):  # Safety check
                    valid_embeddings.append(i)
        
        if not filtered_metadata:
            logger.warning("⚠️ No valid metadata entries found after filtering")
            return {"error": "No valid metadata entries found"}
        
        logger.info(f"✅ Filtered to {len(filtered_metadata)} valid entries")
        
        # Load existing index and extract valid embeddings
        existing_index = faiss.read_index(self.faiss_index_path)
        
        if len(valid_embeddings) > existing_index.ntotal:
            logger.warning(f"⚠️ More valid embeddings ({len(valid_embeddings)}) than index size ({existing_index.ntotal})")
            valid_embeddings = valid_embeddings[:existing_index.ntotal]
        
        # Extract embeddings for valid entries
        embeddings_list = []
        for idx in valid_embeddings:
            if idx < existing_index.ntotal:
                embedding = existing_index.reconstruct(idx)
                embeddings_list.append(embedding)
        
        if not embeddings_list:
            logger.error("❌ No valid embeddings extracted")
            return {"error": "No valid embeddings extracted"}
        
        # Create new index
        dimension = len(embeddings_list[0])
        new_index = self.create_new_index(dimension)
        
        # Convert embeddings to numpy array
        embedding_matrix = np.array(embeddings_list).astype("float32")
        
        # Add embeddings to new index
        logger.info(f"📥 Adding {len(embedding_matrix)} embeddings to new FAISS index")
        new_index.add(embedding_matrix)
        
        # Save new index
        faiss.write_index(new_index, self.faiss_index_path)
        logger.info(f"✅ New FAISS index saved to {self.faiss_index_path}")
        
        # Save filtered metadata
        with open(self.metadata_path, "w") as f:
            json.dump(filtered_metadata, f, indent=2)
        
        logger.info(f"📦 Updated metadata: {len(filtered_metadata)} total entries")
        
        stats = {
            "chunks_processed": len(current_chunks),
            "embeddings_kept": len(embeddings_list),
            "embeddings_removed": len(existing_metadata) - len(filtered_metadata),
            "estimated_cost": 0.0,  # No API calls
            "index_size": new_index.ntotal,
            "index_dimension": new_index.d
        }
        
        logger.info(f"✅ Index rebuild completed (no API calls):")
        logger.info(f"   - Chunks: {stats['chunks_processed']}")
        logger.info(f"   - Embeddings kept: {stats['embeddings_kept']}")
        logger.info(f"   - Embeddings removed: {stats['embeddings_removed']}")
        logger.info(f"   - Cost: $0.00 (no API calls)")
        
        return stats


# -------- MAIN INCREMENTAL FAISS RUNNER --------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Incremental FAISS index manager")
    args = parser.parse_args()

    faiss_mgr = IncrementalFAISS()
    print("No action specified. Only incremental and cleanup operations are supported.") 