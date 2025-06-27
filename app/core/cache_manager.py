"""
Document Cache Manager

This module provides an extensible caching system for storing and retrieving
document processing results including summaries, FAQs, and comparison results.

Author: Fanxing Bu
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Enumeration of supported cache types."""
    SUMMARY = "summary"
    FAQ = "faq"
    COMPARISON = "comparison"


@dataclass
class CacheEntry:
    """Data class representing a cache entry."""
    document_id: str
    cache_type: CacheType
    content: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for storage."""
        return {
            'document_id': self.document_id,
            'cache_type': self.cache_type.value,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create cache entry from dictionary."""
        return cls(
            document_id=data['document_id'],
            cache_type=CacheType(data['cache_type']),
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None,
            metadata=data.get('metadata', {})
        )


class DocumentCacheManager:
    """
    Extensible cache manager for document processing results.
    
    This class provides a unified interface for caching different types of
    document processing results (summaries, FAQs, comparisons) with support
    for expiration, metadata storage, and efficient retrieval.
    
    Attributes:
        db_path (Path): Path to the SQLite database file
        default_ttl_hours (int): Default time-to-live for cache entries in hours
        connection (sqlite3.Connection): Database connection
    """
    
    def __init__(self, db_path: Union[str, Path] = "rag_data/document_cache.db", 
                 default_ttl_hours: int = 24):
        """
        Initialize the cache manager.
        
        Args:
            db_path: Path to the SQLite database file
            default_ttl_hours: Default time-to-live for cache entries in hours
        """
        self.db_path = Path(db_path)
        self.default_ttl_hours = default_ttl_hours
        self.connection = None
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            # Create cache entries table
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    cache_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    metadata TEXT,
                    UNIQUE(document_id, cache_type)
                )
            """)
            
            # Create indexes for efficient querying
            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_cache_type 
                ON cache_entries(document_id, cache_type)
            """)
            
            self.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at 
                ON cache_entries(expires_at)
            """)
            
            self.connection.commit()
            logger.info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _generate_document_id(self, file_name: str, content_hash: Optional[str] = None) -> str:
        """
        Generate a unique document ID.
        
        Args:
            file_name: Name of the document file
            content_hash: Optional content hash for versioning
            
        Returns:
            Unique document identifier
        """
        if content_hash:
            return f"{file_name}_{content_hash[:8]}"
        return file_name
    
    def _calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Calculate hash of content for versioning.
        
        Args:
            content: Content to hash
            
        Returns:
            SHA-256 hash of the content
        """
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def set_cache(self, file_name: str, cache_type: CacheType, 
                  content: Dict[str, Any], ttl_hours: Optional[int] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store content in cache.
        
        Args:
            file_name: Name of the document file
            cache_type: Type of cache entry
            content: Content to cache
            ttl_hours: Time-to-live in hours (uses default if None)
            metadata: Optional metadata to store with the entry
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            content_hash = self._calculate_content_hash(content)
            document_id = self._generate_document_id(file_name, content_hash)
            
            ttl = ttl_hours or self.default_ttl_hours
            expires_at = datetime.now() + timedelta(hours=ttl)
            
            cache_entry = CacheEntry(
                document_id=document_id,
                cache_type=cache_type,
                content=content,
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata
            )
            
            # Use INSERT OR REPLACE for upsert behavior
            self.connection.execute("""
                INSERT OR REPLACE INTO cache_entries 
                (document_id, cache_type, content, created_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cache_entry.document_id,
                cache_entry.cache_type.value,
                json.dumps(cache_entry.content),
                cache_entry.created_at.isoformat(),
                cache_entry.expires_at.isoformat(),
                json.dumps(cache_entry.metadata or {})
            ))
            
            self.connection.commit()
            logger.info(f"Cached {cache_type.value} for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache {cache_type.value} for {file_name}: {e}")
            return False
    
    def get_cache(self, file_name: str, cache_type: CacheType) -> Optional[Dict[str, Any]]:
        """
        Retrieve content from cache.
        
        Args:
            file_name: Name of the document file
            cache_type: Type of cache entry to retrieve
            
        Returns:
            Cached content if found and not expired, None otherwise
        """
        try:
            # First try with content hash (most recent version)
            cursor = self.connection.execute("""
                SELECT * FROM cache_entries 
                WHERE document_id LIKE ? AND cache_type = ? AND 
                      (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC
                LIMIT 1
            """, (f"{file_name}_%", cache_type.value, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            
            if not row:
                # Try without content hash (legacy entries)
                cursor = self.connection.execute("""
                    SELECT * FROM cache_entries 
                    WHERE document_id = ? AND cache_type = ? AND 
                          (expires_at IS NULL OR expires_at > ?)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (file_name, cache_type.value, datetime.now().isoformat()))
                
                row = cursor.fetchone()
            
            if row:
                logger.info(f"Cache hit for {cache_type.value} of {file_name}")
                return json.loads(row['content'])
            
            logger.info(f"Cache miss for {cache_type.value} of {file_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cache for {file_name}: {e}")
            return None
    
    def has_cache(self, file_name: str, cache_type: CacheType) -> bool:
        """
        Check if cache exists and is not expired.
        
        Args:
            file_name: Name of the document file
            cache_type: Type of cache entry
            
        Returns:
            True if valid cache exists, False otherwise
        """
        return self.get_cache(file_name, cache_type) is not None
    
    def get_cache_metadata(self, file_name: str, cache_type: CacheType) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a cache entry.
        
        Args:
            file_name: Name of the document file
            cache_type: Type of cache entry
            
        Returns:
            Metadata if cache exists, None otherwise
        """
        try:
            cursor = self.connection.execute("""
                SELECT metadata FROM cache_entries 
                WHERE document_id LIKE ? AND cache_type = ? AND 
                      (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC
                LIMIT 1
            """, (f"{file_name}_%", cache_type.value, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            
            if not row:
                cursor = self.connection.execute("""
                    SELECT metadata FROM cache_entries 
                    WHERE document_id LIKE ? AND cache_type = ? AND 
                          (expires_at IS NULL OR expires_at > ?)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (file_name, cache_type.value, datetime.now().isoformat()))
                
                row = cursor.fetchone()
            
            if row and row['metadata']:
                return json.loads(row['metadata'])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache metadata for {file_name}: {e}")
            return None
    
    def invalidate_cache(self, file_name: str, cache_type: Optional[CacheType] = None) -> bool:
        """
        Invalidate cache entries.
        
        Args:
            file_name: Name of the document file
            cache_type: Type of cache to invalidate (None for all types)
            
        Returns:
            True if successfully invalidated, False otherwise
        """
        try:
            if cache_type:
                # Invalidate specific cache type
                self.connection.execute("""
                    DELETE FROM cache_entries 
                    WHERE document_id LIKE ? AND cache_type = ?
                """, (f"{file_name}%", cache_type.value))
            else:
                # Invalidate all cache types for the document
                self.connection.execute("""
                    DELETE FROM cache_entries 
                    WHERE document_id LIKE ?
                """, (f"{file_name}%",))
            
            self.connection.commit()
            logger.info(f"Invalidated cache for {file_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {file_name}: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        try:
            cursor = self.connection.execute("""
                DELETE FROM cache_entries 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now().isoformat(),))
            
            removed_count = cursor.rowcount
            self.connection.commit()
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache entries")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache entries: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        try:
            stats = {}
            
            # Total entries
            cursor = self.connection.execute("SELECT COUNT(*) as count FROM cache_entries")
            stats['total_entries'] = cursor.fetchone()['count']
            
            # Entries by type
            cursor = self.connection.execute("""
                SELECT cache_type, COUNT(*) as count 
                FROM cache_entries 
                GROUP BY cache_type
            """)
            stats['entries_by_type'] = {row['cache_type']: row['count'] for row in cursor.fetchall()}
            
            # Expired entries
            cursor = self.connection.execute("""
                SELECT COUNT(*) as count 
                FROM cache_entries 
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            """, (datetime.now().isoformat(),))
            stats['expired_entries'] = cursor.fetchone()['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Cache manager connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global cache manager instance
_cache_manager: Optional[DocumentCacheManager] = None


def get_cache_manager() -> DocumentCacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        DocumentCacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = DocumentCacheManager()
    return _cache_manager


def close_cache_manager() -> None:
    """Close the global cache manager."""
    global _cache_manager
    if _cache_manager:
        _cache_manager.close()
        _cache_manager = None 