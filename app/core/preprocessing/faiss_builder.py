"""
FAISS Index Builder

Provides comprehensive FAISS index building capabilities with OpenAI embeddings,
batch processing, error handling, and cost tracking for large-scale document indexing.

Example:
    # Initialize builder with OpenAI API key
    builder = FAISSBuilder(api_key="your-api-key", model="text-embedding-3-small")
    
    # Build index from chunks
    result = builder.build_index_from_chunks(chunks)
    if result['status'] == 'success':
        print(f"Built index with {result['vectors_created']} vectors")
        print(f"Total cost: ${result['total_cost']:.4f}")
    
    # Save index and metadata
    save_result = builder.save_index("output/faiss.index", "output/metadata.json")
"""

import os
import numpy as np
import faiss
import openai
import tiktoken
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any
import logging
from tqdm import tqdm
from datetime import datetime

# Import utilities
from .utils import handle_operation, ProcessingError, DataPersistence

logger = logging.getLogger(__name__)


class FAISSBuilder:
    """
    Advanced FAISS index builder with OpenAI embeddings integration.
    
    This class handles the complete workflow of generating embeddings from text chunks,
    building FAISS indices, and managing metadata with proper error handling and cost tracking.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        batch_size: int = 50,
        max_retries: int = 5,
        rate_limit_delay: float = 1.0
    ):
        """
        Initialize FAISSBuilder with OpenAI configuration.
        
        Args:
            api_key: OpenAI API key (loads from environment if None)
            model: OpenAI embedding model to use
            batch_size: Number of texts to process per API call
            max_retries: Maximum retry attempts for failed API calls
            rate_limit_delay: Base delay between API calls in seconds
            
        Example:
            builder = FAISSBuilder(
                model="text-embedding-3-large",
                batch_size=100,
                max_retries=3
            )
        """
        # Set up OpenAI client
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ProcessingError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        # Model configuration and pricing
        self.model_configs = {
            "text-embedding-3-small": {
                "price_per_1k_tokens": 0.00002,
                "max_tokens": 8191,
                "encoding": "cl100k_base",
                "dimension": 1536
            },
            "text-embedding-ada-002": {
                "price_per_1k_tokens": 0.0001,
                "max_tokens": 8191,
                "encoding": "text-embedding-ada-002",
                "dimension": 1536
            },
            "text-embedding-3-large": {
                "price_per_1k_tokens": 0.00013,
                "max_tokens": 8191,
                "encoding": "cl100k_base",
                "dimension": 3072
            }
        }
        
        if model not in self.model_configs:
            raise ProcessingError(f"Unsupported model: {model}. Supported models: {list(self.model_configs.keys())}")
        
        self.config = self.model_configs[model]
        
        # Set up tokenizer
        if self.config["encoding"] == "cl100k_base":
            self.encoding = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoding = tiktoken.encoding_for_model(self.config["encoding"])
        
        # Initialize FAISS index
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        
        # Cost tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        logger.info(f"FAISSBuilder initialized with model {model}")
        logger.info(f"Price: ${self.config['price_per_1k_tokens']:.5f}/1K tokens, Dimension: {self.config['dimension']}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using the model's tokenizer.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
            
        Example:
            token_count = builder.count_tokens("Hello world!")
        """
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using word-based estimate: {e}")
            # Fallback to word-based estimation
            return len(text.split()) * 1.3  # Rough approximation
    
    def estimate_cost(self, texts: List[str]) -> float:
        """
        Estimate the cost of generating embeddings for given texts.
        
        Args:
            texts: List of texts to estimate cost for
            
        Returns:
            Estimated cost in USD
            
        Example:
            estimated_cost = builder.estimate_cost(["Text one", "Text two"])
            print(f"Estimated cost: ${estimated_cost:.4f}")
        """
        total_tokens = sum(self.count_tokens(text) for text in texts)
        return (total_tokens / 1000) * self.config["price_per_1k_tokens"]
    
    def split_text_to_fit_tokens(self, text: str, max_tokens: int) -> List[str]:
        """
        Split text into chunks that fit within token limits.
        
        Args:
            text: Text to split
            max_tokens: Maximum tokens per chunk
            
        Returns:
            List of text chunks within token limits
            
        Example:
            chunks = builder.split_text_to_fit_tokens(long_text, 8000)
        """
        if self.count_tokens(text) <= max_tokens:
            return [text]
        
        # Split by sentences first
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence + ". "
            if self.count_tokens(test_chunk) <= max_tokens - 50:  # Safety margin
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @handle_operation("embedding generation", success_fields={'embeddings_created': 0, 'tokens_used': 0})
    def generate_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """
        Generate embeddings for a list of texts with robust error handling.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Result dictionary with embeddings and cost information
            
        Example:
            result = builder.generate_embeddings(["Text 1", "Text 2"])
            if result['status'] == 'success':
                embeddings = result['embeddings']
                cost = result['actual_cost']
        """
        if not texts:
            return {
                'embeddings': [],
                'embeddings_created': 0,
                'tokens_used': 0,
                'actual_cost': 0.0,
                'estimated_cost': 0.0
            }
        
        # Prepare and validate texts
        processed_texts = []
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                continue
            
            # Split texts that are too long
            token_count = self.count_tokens(text)
            if token_count > self.config["max_tokens"] - 50:
                sub_texts = self.split_text_to_fit_tokens(text, self.config["max_tokens"])
                processed_texts.extend(sub_texts)
            else:
                processed_texts.append(text)
        
        if not processed_texts:
            logger.warning("No valid texts to process after filtering")
            return {
                'embeddings': [],
                'embeddings_created': 0,
                'tokens_used': 0,
                'actual_cost': 0.0,
                'estimated_cost': 0.0
            }
        
        estimated_cost = self.estimate_cost(processed_texts)
        logger.info(f"Generating embeddings for {len(processed_texts)} texts (estimated cost: ${estimated_cost:.4f})")
        
        embeddings = []
        actual_tokens = 0
        
        def embed_batch(batch: List[str]) -> Optional[List[List[float]]]:
            """Embed a batch with retry logic and rate limiting."""
            for attempt in range(self.max_retries):
                try:
                    # Check batch token limit
                    batch_tokens = sum(self.count_tokens(text) for text in batch)
                    if batch_tokens > self.config["max_tokens"]:
                        # Split batch if too large
                        mid = len(batch) // 2
                        if mid == 0:
                            logger.error(f"Single text too large: {batch_tokens} tokens")
                            return None
                        
                        first_half = embed_batch(batch[:mid])
                        second_half = embed_batch(batch[mid:])
                        
                        if first_half is None or second_half is None:
                            return None
                        
                        return first_half + second_half
                    
                    # Make API call
                    response = self.client.embeddings.create(
                        input=batch,
                        model=self.model
                    )
                    
                    nonlocal actual_tokens
                    actual_tokens += response.usage.total_tokens
                    
                    return [r.embedding for r in response.data]
                    
                except openai.RateLimitError as e:
                    wait_time = self.rate_limit_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    
                except openai.BadRequestError as e:
                    logger.error(f"Bad request: {e}")
                    if "maximum context length" in str(e).lower() and len(batch) > 1:
                        # Try smaller batch
                        mid = len(batch) // 2
                        first_half = embed_batch(batch[:mid])
                        second_half = embed_batch(batch[mid:])
                        if first_half is None or second_half is None:
                            return None
                        return first_half + second_half
                    break
                    
                except Exception as e:
                    logger.error(f"API error (attempt {attempt + 1}): {e}")
                    if attempt == self.max_retries - 1:
                        break
                    time.sleep(self.rate_limit_delay * (2 ** attempt))
            
            return None
        
        # Process in batches with progress bar
        with tqdm(total=len(processed_texts), desc=f"Embedding ({self.model})", unit="text") as pbar:
            for i in range(0, len(processed_texts), self.batch_size):
                batch = processed_texts[i:i + self.batch_size]
                
                batch_embeddings = embed_batch(batch)
                if batch_embeddings is None:
                    raise ProcessingError(f"Failed to embed batch {i//self.batch_size + 1}")
                
                embeddings.extend(batch_embeddings)
                pbar.update(len(batch))
                
                # Add delay between batches to respect rate limits
                if i + self.batch_size < len(processed_texts):
                    time.sleep(self.rate_limit_delay)
        
        actual_cost = (actual_tokens / 1000) * self.config["price_per_1k_tokens"]
        
        # Update tracking
        self.total_tokens_used += actual_tokens
        self.total_cost += actual_cost
        
        logger.info(f"Generated {len(embeddings)} embeddings, actual cost: ${actual_cost:.4f}")
        
        return {
            'embeddings': embeddings,
            'embeddings_created': len(embeddings),
            'tokens_used': actual_tokens,
            'actual_cost': actual_cost,
            'estimated_cost': estimated_cost,
            'processed_texts': processed_texts
        }
    
    @handle_operation("FAISS index creation", success_fields={'vectors_added': 0})
    def create_index(self, embeddings: List[List[float]], index_type: str = "flat") -> Dict[str, Any]:
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: List of embedding vectors
            index_type: Type of FAISS index ("flat", "ivf", "hnsw")
            
        Returns:
            Result dictionary with index creation status
            
        Example:
            result = builder.create_index(embeddings, index_type="flat")
            if result['status'] == 'success':
                print(f"Created index with {result['vectors_added']} vectors")
        """
        if not embeddings:
            raise ProcessingError("Cannot create index from empty embeddings list")
        
        # Convert to numpy array
        embedding_matrix = np.array(embeddings).astype('float32')
        dimension = embedding_matrix.shape[1]
        num_vectors = embedding_matrix.shape[0]
        
        # Create appropriate index type
        if index_type == "flat":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "ivf":
            # IVF index for larger datasets
            nlist = min(100, max(1, num_vectors // 100))  # Adaptive nlist
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            
            # Train the index if needed
            if num_vectors >= nlist * 10:  # Only train if we have enough data
                logger.info(f"Training IVF index with {num_vectors} vectors...")
                self.index.train(embedding_matrix)
            else:
                logger.warning(f"Not enough vectors ({num_vectors}) to train IVF index, using flat index")
                self.index = faiss.IndexFlatL2(dimension)
                
        elif index_type == "hnsw":
            # HNSW index for fast approximate search
            M = 16  # Number of connections
            self.index = faiss.IndexHNSWFlat(dimension, M)
        else:
            raise ProcessingError(f"Unsupported index type: {index_type}")
        
        # Add vectors to index
        self.index.add(embedding_matrix)
        
        logger.info(f"Created {index_type} FAISS index: {num_vectors} vectors, dimension {dimension}")
        
        return {
            'vectors_added': num_vectors,
            'index_dimension': dimension,
            'index_type': index_type,
            'index_size': self.index.ntotal if self.index else 0
        }
    
    def create_metadata(self, chunks: List[Dict[str, Any]], processed_texts: List[str]) -> List[Dict[str, Any]]:
        """
        Create metadata entries that align with embeddings.
        
        Args:
            chunks: Original chunk data
            processed_texts: Texts that were actually embedded (may include splits)
            
        Returns:
            List of metadata dictionaries aligned with embeddings
            
        Example:
            metadata = builder.create_metadata(chunks, processed_texts)
        """
        metadata = []
        text_idx = 0
        
        for chunk in chunks:
            chunk_text = chunk.get('text', '').strip()
            if not chunk_text:
                continue
            
            # Check if this chunk was split due to token limits
            token_count = self.count_tokens(chunk_text)
            if token_count > self.config["max_tokens"] - 50:
                # This chunk was split
                sub_texts = self.split_text_to_fit_tokens(chunk_text, self.config["max_tokens"])
                for i, sub_text in enumerate(sub_texts):
                    if text_idx < len(processed_texts):
                        metadata.append({
                            'text': sub_text,
                            'section_header': chunk.get('section_header', ''),
                            'metadata': {
                                **chunk.get('metadata', {}),
                                'is_split_chunk': True,
                                'split_index': i,
                                'total_splits': len(sub_texts),
                                'original_chunk_id': chunk.get('metadata', {}).get('chunk_id'),
                                'embedding_model': self.model,
                                'embedding_timestamp': datetime.now().isoformat()
                            }
                        })
                        text_idx += 1
            else:
                # Chunk was not split
                if text_idx < len(processed_texts):
                    metadata.append({
                        'text': chunk_text,
                        'section_header': chunk.get('section_header', ''),
                        'metadata': {
                            **chunk.get('metadata', {}),
                            'is_split_chunk': False,
                            'embedding_model': self.model,
                            'embedding_timestamp': datetime.now().isoformat()
                        }
                    })
                    text_idx += 1
        
        logger.info(f"Created {len(metadata)} metadata entries")
        return metadata
    
    @handle_operation("index building from chunks", success_fields={'vectors_created': 0, 'total_cost': 0.0})
    def build_index_from_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        index_type: str = "flat"
    ) -> Dict[str, Any]:
        """
        Build complete FAISS index from chunk data.
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            index_type: Type of FAISS index to create
            
        Returns:
            Result dictionary with complete build status
            
        Example:
            chunks = [{'text': 'content', 'metadata': {...}}, ...]
            result = builder.build_index_from_chunks(chunks)
            if result['status'] == 'success':
                print(f"Built index: {result['vectors_created']} vectors, ${result['total_cost']:.4f}")
        """
        if not chunks:
            raise ProcessingError("Cannot build index from empty chunks list")
        
        # Extract texts from chunks
        texts = []
        for chunk in chunks:
            text = chunk.get('text', '').strip()
            if text:
                texts.append(text)
        
        if not texts:
            raise ProcessingError("No valid text content found in chunks")
        
        logger.info(f"Building FAISS index from {len(texts)} text chunks")
        
        # Generate embeddings
        embedding_result = self.generate_embeddings(texts)
        if embedding_result['status'] != 'success':
            raise ProcessingError(f"Embedding generation failed: {embedding_result.get('error')}")
        
        embeddings = embedding_result['embeddings']
        processed_texts = embedding_result['processed_texts']
        
        # Create FAISS index
        index_result = self.create_index(embeddings, index_type)
        if index_result['status'] != 'success':
            raise ProcessingError(f"Index creation failed: {index_result.get('error')}")
        
        # Create aligned metadata
        self.metadata = self.create_metadata(chunks, processed_texts)
        
        total_cost = embedding_result['actual_cost']
        
        logger.info(f"Index build completed: {len(embeddings)} vectors, ${total_cost:.4f} cost")
        
        return {
            'vectors_created': len(embeddings),
            'index_dimension': index_result['index_dimension'],
            'index_type': index_type,
            'total_cost': total_cost,
            'tokens_used': embedding_result['tokens_used'],
            'metadata_entries': len(self.metadata),
            'processing_stats': {
                'original_chunks': len(chunks),
                'processed_texts': len(processed_texts),
                'split_occurred': len(processed_texts) > len(texts)
            }
        }
    
    @handle_operation("index save", success_fields={'index_saved': False, 'metadata_saved': False})
    def save_index(
        self, 
        index_path: Union[str, Path], 
        metadata_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Save FAISS index and metadata to files.
        
        Args:
            index_path: Path to save FAISS index file
            metadata_path: Path to save metadata JSON file
            
        Returns:
            Result dictionary with save operation status
            
        Example:
            result = builder.save_index("faiss.index", "metadata.json")
            if result['status'] == 'success':
                print("Index and metadata saved successfully")
        """
        if self.index is None:
            raise ProcessingError("No index to save. Build index first.")
        
        if not self.metadata:
            raise ProcessingError("No metadata to save. Build index first.")
        
        index_path = Path(index_path)
        metadata_path = Path(metadata_path)
        
        # Ensure directories exist
        DataPersistence.ensure_directory(index_path.parent)
        DataPersistence.ensure_directory(metadata_path.parent)
        
        # Save FAISS index
        try:
            faiss.write_index(self.index, str(index_path))
            index_saved = True
            index_size = index_path.stat().st_size if index_path.exists() else 0
        except Exception as e:
            raise ProcessingError(f"Failed to save FAISS index: {e}")
        
        # Save metadata
        metadata_result = DataPersistence.save_json(
            self.metadata, 
            metadata_path, 
            create_backup=True
        )
        
        if metadata_result['status'] != 'success':
            raise ProcessingError(f"Failed to save metadata: {metadata_result.get('error')}")
        
        metadata_saved = True
        metadata_size = metadata_result.get('size_bytes', 0)
        
        logger.info(f"Saved index ({index_size:,} bytes) and metadata ({metadata_size:,} bytes)")
        
        return {
            'index_saved': index_saved,
            'metadata_saved': metadata_saved,
            'index_path': str(index_path),
            'metadata_path': str(metadata_path),
            'index_size_bytes': index_size,
            'metadata_size_bytes': metadata_size,
            'vectors_saved': self.index.ntotal if self.index else 0
        }
    
    @handle_operation("index loading", success_fields={'index_loaded': False, 'metadata_loaded': False})
    def load_index(
        self, 
        index_path: Union[str, Path], 
        metadata_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Load FAISS index and metadata from files.
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
            
        Returns:
            Result dictionary with load operation status
            
        Example:
            result = builder.load_index("faiss.index", "metadata.json")
            if result['status'] == 'success':
                print(f"Loaded index with {result['vectors_loaded']} vectors")
        """
        index_path = Path(index_path)
        metadata_path = Path(metadata_path)
        
        # Load FAISS index
        if not index_path.exists():
            raise ProcessingError(f"FAISS index file not found: {index_path}")
        
        try:
            self.index = faiss.read_index(str(index_path))
            index_loaded = True
            vectors_loaded = self.index.ntotal
            index_dimension = self.index.d
        except Exception as e:
            raise ProcessingError(f"Failed to load FAISS index: {e}")
        
        # Load metadata
        metadata_result = DataPersistence.load_json(metadata_path)
        if metadata_result['status'] != 'success':
            raise ProcessingError(f"Failed to load metadata: {metadata_result.get('error')}")
        
        self.metadata = metadata_result['data']
        metadata_loaded = True
        metadata_entries = len(self.metadata)
        
        logger.info(f"Loaded index: {vectors_loaded} vectors, {metadata_entries} metadata entries")
        
        # Validate consistency
        if vectors_loaded != metadata_entries:
            logger.warning(f"Index-metadata mismatch: {vectors_loaded} vectors vs {metadata_entries} metadata entries")
        
        return {
            'index_loaded': index_loaded,
            'metadata_loaded': metadata_loaded,
            'vectors_loaded': vectors_loaded,
            'metadata_entries': metadata_entries,
            'index_dimension': index_dimension,
            'consistent': vectors_loaded == metadata_entries
        }
    
    def search(
        self, 
        query_text: str, 
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Search the FAISS index for similar text.
        
        Args:
            query_text: Text query to search for
            top_k: Number of top results to return
            
        Returns:
            Search results with scores and metadata
            
        Example:
            results = builder.search("regulatory compliance", top_k=5)
            for result in results['matches']:
                print(f"Score: {result['score']}, Text: {result['text'][:100]}...")
        """
        if self.index is None:
            raise ProcessingError("No index loaded. Load or build index first.")
        
        # Generate query embedding
        embedding_result = self.generate_embeddings([query_text])
        if embedding_result['status'] != 'success':
            raise ProcessingError("Failed to generate query embedding")
        
        query_embedding = np.array(embedding_result['embeddings'][0]).reshape(1, -1).astype('float32')
        
        # Search index
        scores, indices = self.index.search(query_embedding, top_k)
        
        # Format results
        matches = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                metadata_entry = self.metadata[idx]
                matches.append({
                    'score': float(score),
                    'index': int(idx),
                    'text': metadata_entry.get('text', ''),
                    'section_header': metadata_entry.get('section_header', ''),
                    'metadata': metadata_entry.get('metadata', {})
                })
        
        return {
            'query': query_text,
            'matches': matches,
            'search_cost': embedding_result['actual_cost']
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the builder state.
        
        Returns:
            Dictionary with current statistics
            
        Example:
            stats = builder.get_statistics()
            print(f"Total cost: ${stats['total_cost']:.4f}")
        """
        return {
            'model': self.model,
            'model_config': self.config,
            'total_tokens_used': self.total_tokens_used,
            'total_cost': self.total_cost,
            'index_exists': self.index is not None,
            'index_size': self.index.ntotal if self.index else 0,
            'index_dimension': self.index.d if self.index else 0,
            'metadata_entries': len(self.metadata),
            'cost_per_vector': self.total_cost / self.index.ntotal if self.index and self.index.ntotal > 0 else 0
        }
    
    def reset(self) -> None:
        """Reset the builder state, clearing index and metadata."""
        self.index = None
        self.metadata = []
        self.total_tokens_used = 0
        self.total_cost = 0.0
        logger.info("FAISSBuilder state reset")