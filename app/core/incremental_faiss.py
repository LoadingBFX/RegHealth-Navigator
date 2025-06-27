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
    
    def __init__(self):
        """Initialize IncrementalFAISS."""
        # Load environment variables
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Setup tokenizer
        self.encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
        
        # Configuration
        self.max_tokens_per_batch = 8191
        self.max_tokens_per_chunk = 8191
        self.safety_margin = 50
        
        # Paths
        self.output_folder = config.build_faiss_output_folder
        self.chunks_path = os.path.join(self.output_folder, "chunks.json")
        self.faiss_index_path = config.faiss_index_path
        self.metadata_path = os.path.join(self.output_folder, "faiss_metadata.json")
        
        logger.info(f"Initialized IncrementalFAISS with output folder: {self.output_folder}")

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

    def get_embeddings_for_chunks(self, chunks: List[str], model: str = "text-embedding-ada-002") -> List[List[float]]:
        """Generate embeddings for a list of text chunks."""
        if not chunks:
            return []
        
        embeddings = []
        batch = []
        batch_token_count = 0
        
        # First pass: prepare all chunks
        all_chunks = []
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
        
        # Second pass: generate embeddings
        with tqdm(total=len(all_chunks), desc="Generating embeddings", unit="chunk") as pbar:
            for chunk in all_chunks:
                tokens = self.count_tokens(chunk)
                
                # Check if we need to process current batch
                if batch_token_count + tokens > self.max_tokens_per_batch - self.safety_margin:
                    if batch:  # Process current batch
                        response = self.client.embeddings.create(input=batch, model=model)
                        embeddings.extend([r.embedding for r in response.data])
                        pbar.update(len(batch))
                        
                        # Reset batch
                        batch = []
                        batch_token_count = 0
                
                batch.append(chunk)
                batch_token_count += tokens
            
            # Process final batch
            if batch:
                response = self.client.embeddings.create(input=batch, model=model)
                embeddings.extend([r.embedding for r in response.data])
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
        
        Args:
            new_chunks: List of new chunk dictionaries
            
        Returns:
            Number of new embeddings added
        """
        if not new_chunks:
            logger.info("✅ No new chunks to process")
            return 0
        
        # Extract text from chunks
        texts = [chunk["text"] for chunk in new_chunks]
        logger.info(f"📝 Processing {len(texts)} new chunks")
        
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
        
        return len(embeddings)

    def update_metadata_with_new_chunks(self, new_chunks: List[Dict]) -> None:
        """Update metadata file with new chunks."""
        existing_metadata = self.load_existing_metadata()
        
        # Process new chunks (handle potential splitting)
        new_metadata_entries = []
        for chunk in new_chunks:
            text = chunk["text"]
            
            if self.count_tokens(text) > self.max_tokens_per_chunk - self.safety_margin:
                sub_chunks = self.split_into_chunks(text, self.max_tokens_per_chunk)
            else:
                sub_chunks = [text]
            
            for sub_chunk in sub_chunks:
                if not isinstance(sub_chunk, str) or not sub_chunk.strip():
                    continue
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
        
        # Update FAISS index
        new_embeddings_count = self.update_index_with_new_chunks(new_chunks)
        
        # Update metadata
        self.update_metadata_with_new_chunks(new_chunks)
        
        # Calculate costs
        total_tokens = sum(self.count_tokens(chunk["text"]) for chunk in new_chunks)
        estimated_cost = total_tokens / 1000 * 0.0001
        
        stats = {
            "new_chunks_processed": len(new_chunks),
            "new_embeddings_added": new_embeddings_count,
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 4)
        }
        
        logger.info(f"✅ Incremental update completed:")
        logger.info(f"   - New chunks: {stats['new_chunks_processed']}")
        logger.info(f"   - New embeddings: {stats['new_embeddings_added']}")
        logger.info(f"   - Total tokens: {stats['total_tokens']}")
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

    def rebuild_index_from_chunks(self) -> Dict:
        """
        Rebuild FAISS index from chunks.json file.
        This is used when files are deleted and we need to remove their embeddings.
        
        Returns:
            Dictionary with rebuild statistics
        """
        logger.info("🔄 Rebuilding FAISS index from chunks")
        
        # Load chunks from chunks.json
        chunks_file = os.path.join(self.output_folder, "chunks.json")
        if not os.path.exists(chunks_file):
            logger.error(f"❌ Chunks file not found: {chunks_file}")
            return {"error": "Chunks file not found"}
        
        with open(chunks_file, "r") as f:
            chunks = json.load(f)
        
        if not chunks:
            logger.warning("⚠️ No chunks found in chunks.json")
            return {"error": "No chunks found"}
        
        logger.info(f"📝 Rebuilding index from {len(chunks)} chunks")
        
        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.get_embeddings_for_chunks(texts)
        
        if not embeddings:
            logger.error("❌ No embeddings generated")
            return {"error": "No embeddings generated"}
        
        # Create new index
        dimension = len(embeddings[0])
        index = self.create_new_index(dimension)
        
        # Convert embeddings to numpy array
        embedding_matrix = np.array(embeddings).astype("float32")
        
        # Add embeddings to index
        logger.info(f"📥 Adding {len(embedding_matrix)} embeddings to new FAISS index")
        index.add(embedding_matrix)
        
        # Save new index
        faiss.write_index(index, self.faiss_index_path)
        logger.info(f"✅ New FAISS index saved to {self.faiss_index_path}")
        
        # Update metadata to match chunks
        new_metadata_entries = []
        for chunk in chunks:
            text = chunk["text"]
            
            if self.count_tokens(text) > self.max_tokens_per_chunk - self.safety_margin:
                sub_chunks = self.split_into_chunks(text, self.max_tokens_per_chunk)
            else:
                sub_chunks = [text]
            
            for sub_chunk in sub_chunks:
                if not isinstance(sub_chunk, str) or not sub_chunk.strip():
                    continue
                if self.count_tokens(sub_chunk) > self.max_tokens_per_chunk - self.safety_margin:
                    encoded = self.encoding.encode(sub_chunk)
                    sub_chunk = self.encoding.decode(encoded[:self.max_tokens_per_chunk - self.safety_margin])
                
                new_metadata_entries.append({
                    "text": sub_chunk,
                    "section_header": chunk["section_header"],
                    "metadata": chunk["metadata"]
                })
        
        # Save updated metadata
        with open(self.metadata_path, "w") as f:
            json.dump(new_metadata_entries, f, indent=2)
        
        logger.info(f"📦 Updated metadata: {len(new_metadata_entries)} total entries")
        
        # Calculate costs
        total_tokens = sum(self.count_tokens(chunk["text"]) for chunk in chunks)
        estimated_cost = total_tokens / 1000 * 0.0001
        
        stats = {
            "chunks_processed": len(chunks),
            "embeddings_created": len(embeddings),
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 4),
            "index_size": index.ntotal,
            "index_dimension": index.d
        }
        
        logger.info(f"✅ Index rebuild completed:")
        logger.info(f"   - Chunks: {stats['chunks_processed']}")
        logger.info(f"   - Embeddings: {stats['embeddings_created']}")
        logger.info(f"   - Total tokens: {stats['total_tokens']}")
        logger.info(f"   - Estimated cost: ${stats['estimated_cost']}")
        
        return stats

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
    
    parser = argparse.ArgumentParser(description="Incrementally update FAISS index")
    parser.add_argument("--chunks", "-c", help="Path to new chunks JSON file")
    parser.add_argument("--stats", "-s", action="store_true", help="Show index statistics")
    
    args = parser.parse_args()
    
    faiss_updater = IncrementalFAISS()
    
    if args.stats:
        stats = faiss_updater.get_index_stats()
        print("FAISS Index Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.chunks:
        if not os.path.exists(args.chunks):
            print(f"❌ Chunks file not found: {args.chunks}")
            exit(1)
        
        with open(args.chunks, "r") as f:
            new_chunks = json.load(f)
        
        result = faiss_updater.process_incremental_update(new_chunks)
        print(f"✅ Incremental update completed: {result}")
    
    else:
        print("Please specify --chunks or --stats")
        parser.print_help() 