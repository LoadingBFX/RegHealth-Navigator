"""
Data Persistence Utilities

Provides standardized file I/O operations with proper error handling,
atomic writes, and backup capabilities for reliable data management.

Example:
    # Save data with automatic backup
    DataPersistence.save_json({'key': 'value'}, 'data.json')
    
    # Load with default fallback
    data = DataPersistence.load_json('data.json', default={})
    
    # Atomic operations for critical data
    with DataPersistence.atomic_operation('critical_data.json') as temp_path:
        write_data_to(temp_path)
        # File is atomically moved to final location on success
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import logging

from .error_handler import handle_operation, ProcessingError

logger = logging.getLogger(__name__)


class DataPersistence:
    """Utility class for standardized data persistence operations."""
    
    @staticmethod
    @handle_operation("JSON save", error_fields={'saved': False})
    def save_json(
        data: Union[Dict, List], 
        file_path: Union[str, Path],
        ensure_ascii: bool = False,
        indent: int = 2,
        create_backup: bool = False
    ) -> Dict[str, Any]:
        """
        Save data to JSON file with error handling and optional backup.
        
        Args:
            data: Data to save (dict or list)
            file_path: Output file path
            ensure_ascii: Whether to escape non-ASCII characters
            indent: JSON indentation level
            create_backup: Whether to create backup of existing file
            
        Returns:
            Result dictionary with operation status
            
        Example:
            result = DataPersistence.save_json(
                {'chunks': [...]}, 
                'chunks.json',
                create_backup=True
            )
            # Result: {'status': 'success', 'saved': True, 'file_path': '...', 'size_bytes': 1024}
        """
        file_path = Path(file_path)
        
        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if requested and file exists
        backup_path = None
        if create_backup and file_path.exists():
            backup_path = file_path.with_suffix(f'{file_path.suffix}.backup')
            shutil.copy2(file_path, backup_path)
        
        try:
            # Write to temporary file first for atomic operation
            with tempfile.NamedTemporaryFile(
                mode='w', 
                dir=file_path.parent,
                delete=False,
                encoding='utf-8'
            ) as temp_file:
                json.dump(data, temp_file, indent=indent, ensure_ascii=ensure_ascii)
                temp_path = temp_file.name
            
            # Atomic move to final location
            shutil.move(temp_path, file_path)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            return {
                'saved': True,
                'file_path': str(file_path),
                'size_bytes': file_size,
                'backup_created': backup_path is not None,
                'backup_path': str(backup_path) if backup_path else None
            }
            
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise ProcessingError(f"Failed to save JSON to {file_path}: {e}")
    
    @staticmethod  
    @handle_operation("JSON load", error_fields={'loaded': False})
    def load_json(
        file_path: Union[str, Path],
        default: Any = None,
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """
        Load data from JSON file with error handling and default fallback.
        
        Args:
            file_path: Input file path
            default: Default value if file doesn't exist or is invalid
            encoding: File encoding
            
        Returns:
            Result dictionary with loaded data
            
        Example:
            result = DataPersistence.load_json('chunks.json', default=[])
            if result['status'] == 'success':
                chunks = result['data']
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            if default is not None:
                return {
                    'loaded': True,
                    'data': default,
                    'file_path': str(file_path),
                    'used_default': True,
                    'file_exists': False
                }
            else:
                raise ProcessingError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            
            file_size = file_path.stat().st_size
            
            return {
                'loaded': True,
                'data': data,
                'file_path': str(file_path),
                'size_bytes': file_size,
                'used_default': False,
                'file_exists': True
            }
            
        except json.JSONDecodeError as e:
            if default is not None:
                logger.warning(f"Invalid JSON in {file_path}, using default: {e}")
                return {
                    'loaded': True,
                    'data': default,
                    'file_path': str(file_path),
                    'used_default': True,
                    'file_exists': True,
                    'json_error': str(e)
                }
            else:
                raise ProcessingError(f"Invalid JSON in {file_path}: {e}")
        
        except Exception as e:
            raise ProcessingError(f"Failed to load JSON from {file_path}: {e}")
    
    @staticmethod
    @contextmanager
    def atomic_operation(target_path: Union[str, Path]):
        """
        Context manager for atomic file operations.
        
        Creates a temporary file in the same directory as the target,
        yields the temp path for writing, then atomically moves to target on success.
        
        Args:
            target_path: Final file path
            
        Yields:
            Path to temporary file for writing
            
        Example:
            with DataPersistence.atomic_operation('important.json') as temp_path:
                with open(temp_path, 'w') as f:
                    json.dump(data, f)
            # File is now atomically moved to 'important.json'
        """
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in same directory as target
        with tempfile.NamedTemporaryFile(
            dir=target_path.parent,
            delete=False,
            prefix=f".{target_path.name}.",
            suffix=".tmp"
        ) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            yield temp_path
            # Atomic move on successful completion
            shutil.move(temp_path, target_path)
        except Exception:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    @classmethod
    def save_chunks(
        cls,
        chunks: List[Dict],
        output_path: Union[str, Path],
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Save chunks data with standardized format and validation.
        
        Args:
            chunks: List of chunk dictionaries
            output_path: Output file path
            create_backup: Whether to backup existing file
            
        Returns:
            Operation result dictionary
            
        Example:
            chunks = [{'text': 'content', 'metadata': {...}}, ...]
            result = DataPersistence.save_chunks(chunks, 'chunks.json')
        """
        if not isinstance(chunks, list):
            raise ProcessingError("Chunks must be a list")
        
        # Validate chunk format
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                raise ProcessingError(f"Chunk {i} must be a dictionary")
            if 'text' not in chunk:
                raise ProcessingError(f"Chunk {i} missing required 'text' field")
        
        return cls.save_json(
            chunks,
            output_path,
            ensure_ascii=False,
            create_backup=create_backup
        )
    
    @classmethod  
    def load_chunks(
        cls,
        chunks_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Load chunks data with validation.
        
        Args:
            chunks_path: Path to chunks file
            
        Returns:
            Operation result with validated chunks data
            
        Example:
            result = DataPersistence.load_chunks('chunks.json')
            if result['status'] == 'success':
                chunks = result['data']
        """
        result = cls.load_json(chunks_path, default=[])
        
        if result['status'] == 'success':
            chunks = result['data']
            
            # Validate chunks format
            if not isinstance(chunks, list):
                raise ProcessingError("Chunks file must contain a list")
            
            # Add validation statistics
            valid_chunks = 0
            for chunk in chunks:
                if isinstance(chunk, dict) and 'text' in chunk:
                    valid_chunks += 1
            
            result.update({
                'total_chunks': len(chunks),
                'valid_chunks': valid_chunks,
                'validation_passed': valid_chunks == len(chunks)
            })
        
        return result
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """
        Ensure directory exists, creating it if necessary.
        
        Args:
            path: Directory path
            
        Returns:
            Path object for the directory
            
        Example:
            output_dir = DataPersistence.ensure_directory('output/data')
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_file_stats(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive file statistics.
        
        Args:
            file_path: File path to analyze
            
        Returns:
            Dictionary with file statistics
            
        Example:
            stats = DataPersistence.get_file_stats('data.json')
            # Returns: {'size_bytes': 1024, 'modified_time': '...', 'exists': True}
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                'exists': False,
                'file_path': str(file_path)
            }
        
        stat = file_path.stat()
        
        return {
            'exists': True,
            'file_path': str(file_path),
            'size_bytes': stat.st_size,
            'modified_time': stat.st_mtime,
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'suffix': file_path.suffix,
            'name': file_path.name
        }