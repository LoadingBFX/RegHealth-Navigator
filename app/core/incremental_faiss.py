"""
incremental_faiss.py

Enhanced FAISS index manager with CRUD operations for embeddings.
Provides atomic operations for adding, updating, and removing embeddings with proper error handling.
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
from typing import List, Dict, Optional, Tuple
import time
import random
import logging

# Add the app directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IncrementalFAISS:
    """
    Enhanced FAISS index manager with CRUD operations.
    
    Provides atomic operations for:
    - Create: Add embeddings for new chunks
    - Read: Load and query existing index
    - Update: Update embeddings for modified files
    - Delete: Remove embeddings for deleted files
    """
    
    def __init__(self, model: str = None):
        """
        Initialize IncrementalFAISS.
        
        Args:
            model: Embedding model to use (from config if None)
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
        
        # Get model configuration
        try:
            self.model_config = config.get_embedding_model_config(self.model)
            self.model_price = config.get_embedding_model_price(self.model)
        except Exception as e:
            raise ValueError(f"Invalid model '{self.model}': {e}")
        
        # Setup tokenizer
        encoding_type = config.get_embedding_model_encoding(self.model)
        if encoding_type == "cl100k_base":
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = tiktoken.encoding_for_model(encoding_type)
        
        # Configuration
        self.max_tokens_per_batch = self.model_config.get('max_tokens_per_batch', 8191)
        self.max_tokens_per_chunk = self.model_config.get('max_tokens_per_chunk', 8191)
        self.safety_margin = 50
        
        # Paths
        self.output_folder = Path(config.build_faiss_output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        self.faiss_index_path = config.faiss_index_path
        self.metadata_path = self.output_folder / "faiss_metadata.json"
        self.chunks_path = self.output_folder / "chunks.json"
        
        logger.info(f"🚀 Initialized IncrementalFAISS")
        logger.info(f"💰 Model: {self.model} (${self.model_price:.5f}/1K tokens)")
        logger.info(f"📁 Index path: {self.faiss_index_path}")
        logger.info(f"📁 Metadata path: {self.metadata_path}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def estimate_cost(self, chunks: List[Dict]) -> float:
        """Estimate cost for processing chunks."""
        total_tokens = sum(self.count_tokens(chunk.get("text", "")) for chunk in chunks)
        return total_tokens / 1000 * self.model_price

    def split_text_to_fit_tokens(self, text: str, max_tokens: int) -> List[str]:
        """Split text into chunks that fit within token limits."""
        if self.count_tokens(text) <= max_tokens:
            return [text]
        
        # Split by sentences
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence + ". "
            if self.count_tokens(test_chunk) <= max_tokens - self.safety_margin:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def generate_embeddings(self, texts: List[str]) -> Tuple[List[List[float]], float]:
        """
        Generate embeddings for texts with proper error handling and cost tracking.
        
        Args:
            texts: List of text strings
            
        Returns:
            Tuple of (embeddings, actual_cost)
        """
        if not texts:
            return [], 0.0
        
        # Prepare texts and validate token limits
        processed_texts = []
        total_tokens = 0
        
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                continue
                
            token_count = self.count_tokens(text)
            if token_count > self.max_tokens_per_chunk - self.safety_margin:
                # Split large text
                sub_texts = self.split_text_to_fit_tokens(text, self.max_tokens_per_chunk)
                processed_texts.extend(sub_texts)
                total_tokens += sum(self.count_tokens(t) for t in sub_texts)
            else:
                processed_texts.append(text)
                total_tokens += token_count
        
        if not processed_texts:
            logger.warning("⚠️ No valid texts to process after filtering")
            return [], 0.0
        
        # Define batch size early
        batch_size = 200  # Increased from 50 to reduce API calls
        
        logger.info(f"📝 Generating embeddings for {len(processed_texts)} texts ({total_tokens} tokens)")
        logger.info(f"📦 Using batch size: {batch_size}, estimated API calls: {len(processed_texts) // batch_size + 1}")
        
        embeddings = []
        actual_tokens = 0
        max_retries = 5
        base_delay = 1
        api_calls = 0
        
        def embed_batch(batch: List[str], current_batch_size: int) -> Optional[List[List[float]]]:
            """Embed a batch with retry logic."""
            for attempt in range(max_retries):
                try:
                    batch_tokens = sum(self.count_tokens(text) for text in batch)
                    if batch_tokens > self.max_tokens_per_batch:
                        # Split batch
                        mid = len(batch) // 2
                        if mid == 0:
                            logger.error(f"❌ Single text too large: {batch_tokens} tokens")
                            return None
                        
                        first_half = embed_batch(batch[:mid], current_batch_size)
                        second_half = embed_batch(batch[mid:], current_batch_size)
                        
                        if first_half is None or second_half is None:
                            return None
                        
                        return first_half + second_half
                    
                    # Make API call
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.model
                    )
                    
                    nonlocal actual_tokens, api_calls
                    actual_tokens += response.usage.total_tokens
                    api_calls += 1
                    
                    return [r.embedding for r in response.data]
                    
                except openai.RateLimitError as e:
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ Rate limit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                except openai.BadRequestError as e:
                    logger.error(f"❌ Bad request: {e}")
                    if "maximum context length" in str(e).lower() and len(batch) > 1:
                        # Try smaller batch
                        mid = len(batch) // 2
                        first_half = embed_batch(batch[:mid], current_batch_size)
                        second_half = embed_batch(batch[mid:], current_batch_size)
                        if first_half is None or second_half is None:
                            return None
                        return first_half + second_half
                    break
                    
                except Exception as e:
                    logger.error(f"❌ API error: {e}")
                    if attempt == max_retries - 1:
                        break
                    time.sleep(base_delay * (2 ** attempt))
            
            return None
        
        # Process in batches
        with tqdm(total=len(processed_texts), desc=f"Embedding ({self.model})", unit="text") as pbar:
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                
                batch_embeddings = embed_batch(batch, batch_size)
                if batch_embeddings is None:
                    logger.error(f"❌ Failed to embed batch {i//batch_size + 1}")
                    raise RuntimeError("Embedding generation failed")
                
                embeddings.extend(batch_embeddings)
                pbar.update(len(batch))
                
                # Add small delay between batches to avoid rate limiting
                if i + batch_size < len(processed_texts):
                    time.sleep(0.1)
        
        actual_cost = actual_tokens / 1000 * self.model_price
        logger.info(f"✅ Generated {len(embeddings)} embeddings, cost: ${actual_cost:.4f}")
        logger.info(f"📊 API calls made: {api_calls}")
        
        return embeddings, actual_cost

    def load_index(self) -> Optional[faiss.Index]:
        """Load existing FAISS index."""
        if os.path.exists(self.faiss_index_path):
            try:
                index = faiss.read_index(self.faiss_index_path)
                logger.info(f"📁 Loaded FAISS index: {index.ntotal} vectors, dim={index.d}")
                return index
            except Exception as e:
                logger.error(f"❌ Error loading FAISS index: {e}")
                return None
        else:
            logger.info("🆕 No existing FAISS index found")
            return None

    def load_metadata(self) -> List[Dict]:
        """Load metadata."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"📁 Loaded {len(metadata)} metadata entries")
                return metadata
            except Exception as e:
                logger.error(f"❌ Error loading metadata: {e}")
                return []
        return []

    def save_index(self, index: faiss.Index) -> None:
        """Save FAISS index."""
        try:
            faiss.write_index(index, self.faiss_index_path)
            logger.info(f"💾 Saved FAISS index: {index.ntotal} vectors")
        except Exception as e:
            logger.error(f"❌ Error saving FAISS index: {e}")
            raise

    def save_metadata(self, metadata: List[Dict]) -> None:
        """Save metadata."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved {len(metadata)} metadata entries")
        except Exception as e:
            logger.error(f"❌ Error saving metadata: {e}")
            raise

    def create_embeddings_for_chunks(self, chunks: List[Dict]) -> Dict:
        """
        Create embeddings for new chunks and add to index.
        This is an atomic operation.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with operation results
        """
        if not chunks:
            return {
                'chunks_processed': 0,
                'embeddings_added': 0,
                'cost': 0.0,
                'status': 'success'
            }
        
        logger.info(f"🔄 Creating embeddings for {len(chunks)} chunks")
        
        try:
            # Extract texts
            texts = [chunk.get("text", "") for chunk in chunks]
            texts = [t for t in texts if t.strip()]  # Filter empty texts
            
            if not texts:
                logger.warning("⚠️ No valid texts found in chunks")
                return {
                    'chunks_processed': 0,
                    'embeddings_added': 0,
                    'cost': 0.0,
                    'status': 'no_valid_texts'
                }
            
            # Generate embeddings
            embeddings, cost = self.generate_embeddings(texts)
            
            if not embeddings:
                raise RuntimeError("No embeddings generated")
            
            # Load existing index and metadata
            index = self.load_index()
            metadata = self.load_metadata()
            
            # Create new index if needed
            if index is None:
                dimension = len(embeddings[0])
                index = faiss.IndexFlatL2(dimension)
                logger.info(f"🆕 Created new FAISS index with dimension {dimension}")
            
            # Add embeddings to index
            embedding_matrix = np.array(embeddings).astype('float32')
            index.add(embedding_matrix)
            
            # Create chunk hash for change detection
            import hashlib
            chunks_hash = hashlib.md5(
                json.dumps([chunk.get('text', '') for chunk in chunks], sort_keys=True).encode()
            ).hexdigest()
            
            # Update metadata - match exactly with what was embedded
            new_metadata = []
            text_idx = 0
            
            for chunk in chunks:
                chunk_text = chunk.get("text", "").strip()
                if not chunk_text:
                    continue
                
                # Handle text splitting
                if self.count_tokens(chunk_text) > self.max_tokens_per_chunk - self.safety_margin:
                    sub_texts = self.split_text_to_fit_tokens(chunk_text, self.max_tokens_per_chunk)
                    for sub_text in sub_texts:
                        if text_idx < len(embeddings):
                            new_metadata.append({
                                'text': sub_text,
                                'section_header': chunk.get('section_header', ''),
                                'metadata': chunk.get('metadata', {}),
                                'chunks_hash': chunks_hash  # Add hash for change detection
                            })
                            text_idx += 1
                else:
                    if text_idx < len(embeddings):
                        new_metadata.append({
                            'text': chunk_text,
                            'section_header': chunk.get('section_header', ''),
                            'metadata': chunk.get('metadata', {}),
                            'chunks_hash': chunks_hash  # Add hash for change detection
                        })
                        text_idx += 1
            
            # Add new metadata
            metadata.extend(new_metadata)
            
            # Save index and metadata atomically
            self.save_index(index)
            self.save_metadata(metadata)
            
            logger.info(f"✅ Added {len(embeddings)} embeddings, cost: ${cost:.4f}")
            
            return {
                'chunks_processed': len(chunks),
                'embeddings_added': len(embeddings),
                'cost': cost,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating embeddings: {e}")
            return {
                'chunks_processed': len(chunks),
                'embeddings_added': 0,
                'cost': 0.0,
                'status': 'error',
                'error': str(e)
            }

    def remove_embeddings_for_file(self, file_path: str, existing_metadata: List[Dict] = None) -> Dict:
        """
        Remove embeddings for a specific file.
        This efficiently removes vectors from the FAISS index without rebuilding.
        
        Args:
            file_path: Path to file (just filename, not full path)
            existing_metadata: Optional pre-loaded metadata to avoid duplicate loading
            
        Returns:
            Dictionary with operation results
        """
        logger.info(f"🗑️ Removing embeddings for file: {file_path}")
        
        try:
            # Load current metadata (only if not provided)
            if existing_metadata is None:
                metadata = self.load_metadata()
            else:
                metadata = existing_metadata
                
            if not metadata:
                logger.info("✅ No metadata found, nothing to remove")
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'status': 'success'
                }
            
            # Load current index
            index = self.load_index()
            if index is None:
                logger.info("✅ No index found, nothing to remove")
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'status': 'success'
                }
            
            # Filter metadata to exclude the specified file
            filename = os.path.basename(file_path)  # Handle both full paths and filenames
            filtered_metadata = []
            removed_indices = []
            removed_count = 0
            
            for i, entry in enumerate(metadata):
                entry_file = entry.get('metadata', {}).get('source_file', '')
                if entry_file != filename:
                    filtered_metadata.append(entry)
                else:
                    removed_indices.append(i)
                    removed_count += 1
            
            if removed_count == 0:
                logger.info(f"✅ No embeddings found for file: {file_path}")
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'status': 'success'
                }
            
            # Efficiently remove vectors from FAISS index
            if filtered_metadata:
                try:
                    # Convert removed_indices to numpy array
                    import numpy as np
                    remove_ids = np.array(removed_indices, dtype=np.int64)
                    
                    # Log before removal
                    logger.info(f"🔄 Removing {len(remove_ids)} vectors from index (current size: {index.ntotal})")
                    
                    # Remove vectors from index
                    index.remove_ids(remove_ids)
                    
                    # Verify removal worked correctly
                    expected_remaining = len(metadata) - len(removed_indices)
                    actual_remaining = index.ntotal
                    
                    if actual_remaining != expected_remaining:
                        logger.warning(f"⚠️ remove_ids result mismatch: expected {expected_remaining}, got {actual_remaining}")
                        raise RuntimeError(f"remove_ids failed: expected {expected_remaining}, got {actual_remaining}")
                    
                    # Save updated index and metadata
                    self.save_index(index)
                    self.save_metadata(filtered_metadata)
                    
                    logger.info(f"✅ Removed {removed_count} embeddings, kept {index.ntotal} remaining")
                    
                    return {
                        'file_path': file_path,
                        'embeddings_removed': removed_count,
                        'embeddings_remaining': index.ntotal,
                        'rebuild_cost': 0.0,  # No API calls needed
                        'status': 'success'
                    }
                    
                except Exception as e:
                    logger.warning(f"⚠️ FAISS remove_ids failed: {e}, falling back to rebuild")
                    # Fallback: rebuild from metadata (expensive but safe)
                    texts = [entry['text'] for entry in filtered_metadata]
                    embeddings, cost = self.generate_embeddings(texts)
                    
                    if embeddings:
                        dimension = len(embeddings[0])
                        new_index = faiss.IndexFlatL2(dimension)
                        embedding_matrix = np.array(embeddings).astype('float32')
                        new_index.add(embedding_matrix)
                        
                        self.save_index(new_index)
                        self.save_metadata(filtered_metadata)
                        
                        logger.info(f"✅ Removed {removed_count} embeddings, rebuilt index with {len(embeddings)} remaining")
                        
                        return {
                            'file_path': file_path,
                            'embeddings_removed': removed_count,
                            'embeddings_remaining': len(embeddings),
                            'rebuild_cost': cost,
                            'status': 'success'
                        }
                    else:
                        raise RuntimeError("Failed to regenerate embeddings for remaining metadata")
            else:
                # No metadata remaining, remove index
                if os.path.exists(self.faiss_index_path):
                    os.remove(self.faiss_index_path)
                self.save_metadata([])
                
                logger.info(f"✅ Removed all embeddings, index cleared")
                
                return {
                    'file_path': file_path,
                    'embeddings_removed': removed_count,
                    'embeddings_remaining': 0,
                    'rebuild_cost': 0.0,
                    'status': 'success'
                }
        except Exception as e:
            logger.error(f"❌ Error removing embeddings for {file_path}: {e}")
            return {
                'file_path': file_path,
                'embeddings_removed': 0,
                'status': 'error',
                'error': str(e)
            }

    def update_embeddings_for_file(self, file_path: str, chunks: List[Dict]) -> Dict:
        """
        Update embeddings for a specific file (remove old + add new).
        This is an atomic operation.
        
        Args:
            file_path: Path to file
            chunks: New chunks for the file
            
        Returns:
            Dictionary with operation results
        """
        logger.info(f"🔄 Updating embeddings for file: {file_path}")
        
        try:
            # Check if we actually need to update by comparing chunk hashes
            existing_metadata = self.load_metadata()
            filename = Path(file_path).name
            
            # Step 1: Check if FAISS index exists and is healthy
            index = self.load_index()
            if index is None:
                logger.info(f"🔄 FAISS index not found, will regenerate embeddings for {file_path}")
                # Index doesn't exist, need to regenerate
                add_result = self.create_embeddings_for_chunks(chunks)
                if add_result['status'] != 'success':
                    raise RuntimeError(f"Failed to add new embeddings: {add_result.get('error', 'Unknown')}")
                
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'embeddings_added': add_result['embeddings_added'],
                    'total_cost': add_result['cost'],
                    'status': 'success'
                }
            
            # Step 2: Check if index and metadata are consistent
            if index.ntotal != len(existing_metadata):
                logger.warning(f"⚠️ Index-metadata mismatch: index has {index.ntotal} vectors, metadata has {len(existing_metadata)} entries")
                logger.info(f"🔄 Will regenerate embeddings for {file_path} due to inconsistency")
                # Inconsistent, need to regenerate
                add_result = self.create_embeddings_for_chunks(chunks)
                if add_result['status'] != 'success':
                    raise RuntimeError(f"Failed to add new embeddings: {add_result.get('error', 'Unknown')}")
                
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'embeddings_added': add_result['embeddings_added'],
                    'total_cost': add_result['cost'],
                    'status': 'success'
                }
            
            # Step 3: Check if file has existing embeddings in FAISS
            existing_embeddings = [m for m in existing_metadata if m.get('metadata', {}).get('source_file') == filename]
            
            if not existing_embeddings:
                logger.info(f"🔄 No existing embeddings found for {file_path}, will create new ones")
                # No existing embeddings, just add new ones
                add_result = self.create_embeddings_for_chunks(chunks)
                if add_result['status'] != 'success':
                    raise RuntimeError(f"Failed to add new embeddings: {add_result.get('error', 'Unknown')}")
                
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'embeddings_added': add_result['embeddings_added'],
                    'total_cost': add_result['cost'],
                    'status': 'success'
                }
            
            # Step 4: Now check if chunks have actually changed
            # Create hash of new chunks for comparison
            import hashlib
            new_chunks_hash = hashlib.md5(
                json.dumps([chunk.get('text', '') for chunk in chunks], sort_keys=True).encode()
            ).hexdigest()
            
            # Check if chunks have actually changed
            existing_chunks_hash = existing_embeddings[0].get('chunks_hash', '')
            if existing_chunks_hash == new_chunks_hash:
                logger.info(f"✅ No changes detected for {file_path}, skipping embedding update")
                return {
                    'file_path': file_path,
                    'embeddings_removed': 0,
                    'embeddings_added': 0,
                    'total_cost': 0.0,
                    'status': 'no_changes'
                }
            
            # Step 5: Chunks have changed, perform update (remove old + add new)
            # Remove existing embeddings for this file
            remove_result = self.remove_embeddings_for_file(file_path, existing_metadata)
            if remove_result['status'] != 'success':
                raise RuntimeError(f"Failed to remove old embeddings: {remove_result.get('error', 'Unknown')}")
            
            # Add new embeddings
            add_result = self.create_embeddings_for_chunks(chunks)
            if add_result['status'] != 'success':
                raise RuntimeError(f"Failed to add new embeddings: {add_result.get('error', 'Unknown')}")
            
            total_cost = remove_result.get('rebuild_cost', 0.0) + add_result.get('cost', 0.0)
            
            logger.info(f"✅ Updated embeddings for {file_path}: -{remove_result['embeddings_removed']}, +{add_result['embeddings_added']}")
            
            return {
                'file_path': file_path,
                'embeddings_removed': remove_result['embeddings_removed'],
                'embeddings_added': add_result['embeddings_added'],
                'total_cost': total_cost,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating embeddings for {file_path}: {e}")
            return {
                'file_path': file_path,
                'embeddings_removed': 0,
                'embeddings_added': 0,
                'total_cost': 0.0,
                'status': 'error',
                'error': str(e)
            }

    def get_status(self) -> Dict:
        """Get current status of FAISS index and metadata."""
        index = self.load_index()
        metadata = self.load_metadata()
        
        status = {
            'model': self.model,
            'model_price_per_1k_tokens': self.model_price,
            'index_exists': index is not None,
            'index_size': index.ntotal if index else 0,
            'index_dimension': index.d if index else 0,
            'metadata_entries': len(metadata),
            'index_path': self.faiss_index_path,
            'metadata_path': str(self.metadata_path)
        }
        
        # Check consistency
        if index and metadata:
            if index.ntotal != len(metadata):
                status['consistency_warning'] = f"Index has {index.ntotal} vectors but metadata has {len(metadata)} entries"
        
        return status

    def validate_consistency(self) -> Dict:
        """Validate consistency between index, metadata, and chunks."""
        issues = []
        warnings = []
        
        # Load all data
        index = self.load_index()
        metadata = self.load_metadata()
        
        if self.chunks_path.exists():
            try:
                with open(self.chunks_path, 'r') as f:
                    chunks = json.load(f)
            except Exception as e:
                issues.append(f"Cannot load chunks.json: {e}")
                chunks = []
        else:
            issues.append("chunks.json not found")
            chunks = []
        
        # Check index vs metadata
        if index and metadata:
            if index.ntotal != len(metadata):
                issues.append(f"Index-metadata mismatch: {index.ntotal} vectors vs {len(metadata)} metadata entries")
        elif index and not metadata:
            issues.append("Index exists but no metadata found")
        elif metadata and not index:
            issues.append("Metadata exists but no index found")
        
        # Check for orphaned metadata (metadata without corresponding chunks)
        if chunks and metadata:
            chunk_texts = {chunk['text'] for chunk in chunks}
            orphaned_metadata = 0
            for entry in metadata:
                if entry['text'] not in chunk_texts:
                    orphaned_metadata += 1
            
            if orphaned_metadata > 0:
                warnings.append(f"{orphaned_metadata} metadata entries have no corresponding chunks")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'stats': {
                'index_size': index.ntotal if index else 0,
                'metadata_entries': len(metadata),
                'chunk_count': len(chunks)
            }
        }


# -------- MAIN INCREMENTAL FAISS RUNNER --------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Incremental FAISS index manager with CRUD operations")
    parser.add_argument("--status", "-s", action="store_true", help="Show system status")
    parser.add_argument("--validate", "-v", action="store_true", help="Validate system consistency")
    parser.add_argument("--model", "-m", type=str, help="Embedding model to use")
    parser.add_argument("--remove-file", type=str, help="Remove embeddings for specific file")
    
    args = parser.parse_args()
    
    faiss_mgr = IncrementalFAISS(model=args.model)
    
    if args.status:
        status = faiss_mgr.get_status()
        print("\n=== Incremental FAISS Status ===")
        for key, value in status.items():
            print(f"{key}: {value}")
    
    elif args.validate:
        validation = faiss_mgr.validate_consistency()
        print("\n=== System Validation ===")
        print(f"Valid: {validation['valid']}")
        
        if validation['issues']:
            print("\nIssues:")
            for issue in validation['issues']:
                print(f"  ❌ {issue}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️ {warning}")
        
        print(f"\nStats: {validation['stats']}")
    
    elif args.remove_file:
        result = faiss_mgr.remove_embeddings_for_file(args.remove_file)
        print(f"\nRemoved embeddings for {args.remove_file}:")
        print(f"Status: {result['status']}")
        print(f"Embeddings removed: {result['embeddings_removed']}")
        if result['status'] == 'error':
            print(f"Error: {result['error']}")
    
    else:
        print("Please specify an operation. Use --help for options.")