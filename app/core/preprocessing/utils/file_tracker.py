"""
File Tracking Utilities

Provides comprehensive file discovery, change detection, and tracking
capabilities for managing XML document processing workflows.

Example:
    # Initialize tracker
    tracker = FileTracker('/data/documents', '/output/tracking.json')
    
    # Find XML files
    xml_files = tracker.find_files('*.xml', exclude_root=True)
    
    # Track changes
    changed_files = tracker.find_changed_files()
    deleted_files = tracker.find_deleted_files()
    
    # Update tracking
    tracker.update_tracking('document.xml', {'processed': True})
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Set
import logging
from datetime import datetime

from .error_handler import handle_operation, ProcessingError
from .data_persistence import DataPersistence

logger = logging.getLogger(__name__)


class FileTracker:
    """
    Manages file discovery, change detection, and processing tracking.
    
    This class provides a centralized way to track which files have been processed,
    detect changes in files, and manage the incremental processing workflow.
    """
    
    def __init__(
        self,
        base_directory: Union[str, Path],
        tracking_file: Optional[Union[str, Path]] = None
    ):
        """
        Initialize FileTracker.
        
        Args:
            base_directory: Root directory to track files in
            tracking_file: Path to tracking data file (auto-generated if None)
            
        Example:
            tracker = FileTracker('/data/xml', '/output/tracking.json')
        """
        self.base_dir = Path(base_directory)
        
        if tracking_file is None:
            tracking_file = self.base_dir.parent / 'tracking' / 'processed_files.json'
        
        self.tracking_file = Path(tracking_file)
        self.tracking_data = {}
        
        # Ensure directories exist
        DataPersistence.ensure_directory(self.tracking_file.parent)
        
        # Load existing tracking data
        self._load_tracking_data()
        
        logger.info(f"FileTracker initialized: base={self.base_dir}, tracking={self.tracking_file}")
    
    def _load_tracking_data(self) -> None:
        """Load tracking data from file."""
        result = DataPersistence.load_json(self.tracking_file, default={})
        if result['status'] == 'success':
            self.tracking_data = result['data']
            logger.debug(f"Loaded tracking data for {len(self.tracking_data)} files")
        else:
            logger.warning(f"Could not load tracking data: {result.get('error', 'Unknown error')}")
            self.tracking_data = {}
    
    def _save_tracking_data(self) -> None:
        """Save tracking data to file."""
        result = DataPersistence.save_json(
            self.tracking_data,
            self.tracking_file,
            create_backup=True
        )
        if result['status'] != 'success':
            raise ProcessingError(f"Failed to save tracking data: {result.get('error')}")
    
    @handle_operation("file discovery", success_fields={'files_found': 0})
    def find_files(
        self,
        pattern: str = "*.xml",
        exclude_root: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Find files matching the specified pattern.
        
        Args:
            pattern: Glob pattern for file matching (default: "*.xml")
            exclude_root: Whether to exclude files in the root directory
            exclude_patterns: List of patterns to exclude
            
        Returns:
            Result dictionary with found files
            
        Example:
            result = tracker.find_files('*.xml', exclude_patterns=['*test*'])
            files = result['files'] if result['status'] == 'success' else []
        """
        if not self.base_dir.exists():
            raise ProcessingError(f"Base directory does not exist: {self.base_dir}")
        
        # Find all matching files
        all_files = list(self.base_dir.rglob(pattern))
        
        # Apply exclusion filters
        filtered_files = []
        exclude_patterns = exclude_patterns or []
        
        for file_path in all_files:
            # Skip root files if requested
            if exclude_root and file_path.parent == self.base_dir:
                continue
            
            # Skip files matching exclude patterns
            relative_path = self.get_relative_path(file_path)
            if any(Path(relative_path).match(pattern) for pattern in exclude_patterns):
                continue
            
            # Skip non-files
            if not file_path.is_file():
                continue
                
            filtered_files.append(file_path)
        
        logger.info(f"Found {len(filtered_files)} files matching '{pattern}'")
        
        return {
            'files': filtered_files,
            'files_found': len(filtered_files),
            'pattern': pattern,
            'base_directory': str(self.base_dir)
        }
    
    @handle_operation("change detection", success_fields={'changed_files': 0})
    def find_changed_files(self, file_list: Optional[List[Path]] = None) -> Dict[str, any]:
        """
        Find files that have been modified since last tracking update.
        
        Args:
            file_list: Specific files to check (finds all XML files if None)
            
        Returns:
            Result dictionary with changed files
            
        Example:
            result = tracker.find_changed_files()
            changed = result['files'] if result['status'] == 'success' else []
        """
        if file_list is None:
            find_result = self.find_files()
            if find_result['status'] != 'success':
                raise ProcessingError("Could not find files for change detection")
            file_list = find_result['files']
        
        changed_files = []
        
        for file_path in file_list:
            relative_path = self.get_relative_path(file_path)
            current_hash = self.get_file_hash(file_path)
            
            # Check if file is new or modified
            file_info = self.tracking_data.get(relative_path)
            if not file_info or file_info.get('hash') != current_hash:
                changed_files.append(file_path)
        
        logger.info(f"Found {len(changed_files)} changed files")
        
        return {
            'files': changed_files,
            'changed_files': len(changed_files),
            'total_checked': len(file_list)
        }
    
    @handle_operation("deletion detection", success_fields={'deleted_files': 0})
    def find_deleted_files(self) -> Dict[str, any]:
        """
        Find files that were tracked but no longer exist.
        
        Returns:
            Result dictionary with deleted file paths
            
        Example:
            result = tracker.find_deleted_files()
            deleted = result['file_paths'] if result['status'] == 'success' else []
        """
        deleted_files = []
        
        for relative_path in list(self.tracking_data.keys()):
            full_path = self.base_dir / relative_path
            if not full_path.exists():
                deleted_files.append(relative_path)
        
        logger.info(f"Found {len(deleted_files)} deleted files")
        
        return {
            'file_paths': deleted_files,
            'deleted_files': len(deleted_files)
        }
    
    def get_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate MD5 hash of file content for change detection.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string
            
        Example:
            hash_value = tracker.get_file_hash('document.xml')
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ProcessingError(f"File not found for hashing: {file_path}")
        
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            raise ProcessingError(f"Failed to calculate hash for {file_path}: {e}")
    
    def get_relative_path(self, file_path: Union[str, Path]) -> str:
        """
        Get relative path from base directory.
        
        Args:
            file_path: Absolute or relative file path
            
        Returns:
            Relative path string
            
        Example:
            rel_path = tracker.get_relative_path('/data/xml/folder/file.xml')
            # Returns: 'folder/file.xml'
        """
        file_path = Path(file_path)
        
        try:
            return str(file_path.relative_to(self.base_dir))
        except ValueError:
            # File is not under base directory, return as-is
            return str(file_path)
    
    @handle_operation("tracking update", success_fields={'updated': False})
    def update_tracking(
        self,
        file_path: Union[str, Path],
        metadata: Optional[Dict] = None,
        save_immediately: bool = True
    ) -> Dict[str, any]:
        """
        Update tracking information for a file.
        
        Args:
            file_path: File path to update
            metadata: Additional metadata to store
            save_immediately: Whether to save tracking data immediately
            
        Returns:
            Result dictionary with update status
            
        Example:
            tracker.update_tracking(
                'folder/document.xml',
                {'chunks_count': 150, 'processed_at': '2024-01-01T12:00:00'}
            )
        """
        file_path = Path(file_path)
        relative_path = self.get_relative_path(file_path)
        
        if not file_path.exists():
            raise ProcessingError(f"Cannot track non-existent file: {file_path}")
        
        # Calculate current hash and file stats
        current_hash = self.get_file_hash(file_path)
        file_stats = file_path.stat()
        
        # Create tracking entry
        tracking_entry = {
            'hash': current_hash,
            'processed_at': datetime.now().isoformat(),
            'file_size': file_stats.st_size,
            'modified_time': file_stats.st_mtime
        }
        
        # Add custom metadata
        if metadata:
            tracking_entry.update(metadata)
        
        # Update tracking data
        self.tracking_data[relative_path] = tracking_entry
        
        # Save if requested
        if save_immediately:
            self._save_tracking_data()
        
        logger.debug(f"Updated tracking for {relative_path}")
        
        return {
            'updated': True,
            'file_path': relative_path,
            'hash': current_hash,
            'metadata': tracking_entry
        }
    
    @handle_operation("tracking removal", success_fields={'removed': False})
    def remove_tracking(
        self,
        file_path: Union[str, Path],
        save_immediately: bool = True
    ) -> Dict[str, any]:
        """
        Remove tracking information for a file.
        
        Args:
            file_path: File path to remove from tracking
            save_immediately: Whether to save tracking data immediately
            
        Returns:
            Result dictionary with removal status
            
        Example:
            tracker.remove_tracking('folder/deleted_document.xml')
        """
        relative_path = self.get_relative_path(file_path)
        
        if relative_path in self.tracking_data:
            removed_entry = self.tracking_data.pop(relative_path)
            
            if save_immediately:
                self._save_tracking_data()
            
            logger.debug(f"Removed tracking for {relative_path}")
            
            return {
                'removed': True,
                'file_path': relative_path,
                'previous_metadata': removed_entry
            }
        else:
            return {
                'removed': False,
                'file_path': relative_path,
                'reason': 'File was not being tracked'
            }
    
    def get_tracking_info(self, file_path: Union[str, Path]) -> Optional[Dict]:
        """
        Get tracking information for a specific file.
        
        Args:
            file_path: File path to query
            
        Returns:
            Tracking metadata dictionary or None if not tracked
            
        Example:
            info = tracker.get_tracking_info('folder/document.xml')
            if info:
                print(f"Last processed: {info['processed_at']}")
        """
        relative_path = self.get_relative_path(file_path)
        return self.tracking_data.get(relative_path)
    
    def get_status(self) -> Dict[str, any]:
        """
        Get comprehensive tracking status.
        
        Returns:
            Status dictionary with tracking statistics
            
        Example:
            status = tracker.get_status()
            print(f"Tracking {status['total_tracked']} files")
        """
        # Count current files
        find_result = self.find_files()
        current_files = find_result.get('files_found', 0) if find_result['status'] == 'success' else 0
        
        # Count changes
        change_result = self.find_changed_files()
        changed_files = change_result.get('changed_files', 0) if change_result['status'] == 'success' else 0
        
        # Count deletions
        delete_result = self.find_deleted_files()
        deleted_files = delete_result.get('deleted_files', 0) if delete_result['status'] == 'success' else 0
        
        return {
            'base_directory': str(self.base_dir),
            'tracking_file': str(self.tracking_file),
            'total_tracked': len(self.tracking_data),
            'current_files': current_files,
            'changed_files': changed_files,
            'deleted_files': deleted_files,
            'tracking_file_exists': self.tracking_file.exists()
        }
    
    def cleanup_deleted_tracking(self) -> Dict[str, any]:
        """
        Remove tracking entries for files that no longer exist.
        
        Returns:
            Result dictionary with cleanup statistics
            
        Example:
            result = tracker.cleanup_deleted_tracking()
            print(f"Cleaned up {result['cleaned_entries']} obsolete entries")
        """
        delete_result = self.find_deleted_files()
        if delete_result['status'] != 'success':
            raise ProcessingError("Could not find deleted files for cleanup")
        
        deleted_paths = delete_result['file_paths']
        
        # Remove tracking for deleted files
        for relative_path in deleted_paths:
            if relative_path in self.tracking_data:
                del self.tracking_data[relative_path]
        
        # Save updated tracking data
        if deleted_paths:
            self._save_tracking_data()
        
        logger.info(f"Cleaned up tracking for {len(deleted_paths)} deleted files")
        
        return {
            'cleaned_entries': len(deleted_paths),
            'remaining_tracked': len(self.tracking_data)
        }