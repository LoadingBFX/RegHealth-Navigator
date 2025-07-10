"""
Configuration Loader

Provides unified configuration loading and management for the preprocessing package,
integrating with the main application config system.

Example:
    # Load configuration
    config = ConfigLoader()
    
    # Get chunking settings
    chunk_config = config.get_chunking_config()
    print(f"Chunk words: {chunk_config['chunk_words']}")
    
    # Get paths
    paths = config.get_paths_config()
    print(f"Data directory: {paths['data_directory']}")
    
    # Get embedding settings
    embedding_config = config.get_embedding_config()
    print(f"Model: {embedding_config['model']}")
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Unified configuration loader for preprocessing package.
    
    Integrates with the main application config system and provides
    sensible defaults for all preprocessing operations.
    """
    
    def __init__(self, config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize ConfigLoader.
        
        Args:
            config_override: Optional configuration dictionary to override defaults
            
        Example:
            config = ConfigLoader({'chunk_words': 300})
        """
        self._config_override = config_override or {}
        self._app_config = None
        
        # Try to load main application config
        self._load_app_config()
        
        logger.debug("ConfigLoader initialized")
    
    def _load_app_config(self) -> None:
        """Load main application configuration if available."""
        try:
            # Add app directory to path
            app_dir = Path(__file__).parent.parent.parent
            if str(app_dir) not in sys.path:
                sys.path.append(str(app_dir))
            
            from config import config
            self._app_config = config
            logger.debug("Loaded main application config")
            
        except ImportError as e:
            logger.warning(f"Could not load main application config: {e}")
            self._app_config = None
    
    def _get_from_app_config(self, attribute: str, default: Any = None) -> Any:
        """Get value from application config with fallback."""
        if self._app_config and hasattr(self._app_config, attribute):
            return getattr(self._app_config, attribute)
        return default
    
    def get_chunking_config(self) -> Dict[str, Any]:
        """
        Get chunking configuration.
        
        Returns:
            Dictionary with chunking settings
            
        Example:
            config = loader.get_chunking_config()
            chunker = XMLChunker(**config)
        """
        config = {
            'chunk_words': 500,
            'overlap_sentences': 1,
            'encoding': 'utf-8'
        }
        
        # Override from app config
        if self._app_config:
            config['chunk_words'] = self._get_from_app_config('chunk_words', config['chunk_words'])
            config['overlap_sentences'] = self._get_from_app_config('overlap_sentences', config['overlap_sentences'])
        
        # Override from manual config
        config.update(self._config_override.get('chunking', {}))
        
        return config
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """
        Get embedding configuration.
        
        Returns:
            Dictionary with embedding settings
            
        Example:
            config = loader.get_embedding_config()
            builder = FAISSBuilder(**config)
        """
        config = {
            'model': 'text-embedding-3-small',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'batch_size': 50,
            'max_retries': 5,
            'rate_limit_delay': 1.0
        }
        
        # Override from app config
        if self._app_config:
            config['model'] = self._get_from_app_config('default_embedding_model', config['model'])
        
        # Override from manual config
        config.update(self._config_override.get('embedding', {}))
        
        return config
    
    def get_paths_config(self) -> Dict[str, Path]:
        """
        Get file paths configuration.
        
        Returns:
            Dictionary with configured paths
            
        Example:
            paths = loader.get_paths_config()
            manager = IncrementalManager(
                data_directory=paths['data_directory'],
                output_directory=paths['output_directory']
            )
        """
        # Default paths relative to project root
        project_root = self._get_project_root()
        
        config = {
            'data_directory': project_root / 'data',
            'output_directory': project_root / 'rag_data',
            'chunks_file': project_root / 'rag_data' / 'chunks.json',
            'faiss_index': project_root / 'rag_data' / 'faiss.index',
            'faiss_metadata': project_root / 'rag_data' / 'faiss_metadata.json',
            'tracking_file': project_root / 'rag_data' / 'file_tracking.json'
        }
        
        # Override from app config
        if self._app_config:
            try:
                config['data_directory'] = Path(self._get_from_app_config('docs_data_path', str(config['data_directory'])))
                config['output_directory'] = Path(self._get_from_app_config('build_faiss_output_folder', str(config['output_directory'])))
                config['faiss_index'] = Path(self._get_from_app_config('faiss_index_path', str(config['faiss_index'])))
                config['faiss_metadata'] = Path(self._get_from_app_config('faiss_metadata_path', str(config['faiss_metadata'])))
            except Exception as e:
                logger.warning(f"Error loading paths from app config: {e}")
        
        # Override from manual config
        paths_override = self._config_override.get('paths', {})
        for key, value in paths_override.items():
            if key in config:
                config[key] = Path(value)
        
        return config
    
    def get_processing_config(self) -> Dict[str, Any]:
        """
        Get processing pipeline configuration.
        
        Returns:
            Dictionary with processing settings
            
        Example:
            config = loader.get_processing_config()
            pipeline = ProcessingPipeline(**config)
        """
        paths = self.get_paths_config()
        chunking = self.get_chunking_config()
        embedding = self.get_embedding_config()
        
        config = {
            'data_dir': paths['data_directory'],
            'output_dir': paths['output_directory'],
            'api_key': embedding['api_key'],
            'model': embedding['model'],
            'chunk_words': chunking['chunk_words'],
            'overlap_sentences': chunking['overlap_sentences'],
            'days_back': 30  # Default for regulation fetching
        }
        
        # Override from manual config
        config.update(self._config_override.get('processing', {}))
        
        return config
    
    def get_validation_config(self) -> Dict[str, Any]:
        """
        Get system validation configuration.
        
        Returns:
            Dictionary with validation settings
        """
        paths = self.get_paths_config()
        
        config = {
            'chunks_file': str(paths['chunks_file']),
            'faiss_index': str(paths['faiss_index']),
            'faiss_metadata': str(paths['faiss_metadata']),
            'tracking_file': str(paths['tracking_file']),
            'data_directory': str(paths['data_directory']),
            'max_chunk_file_size_mb': 500,
            'max_metadata_file_size_mb': 100,
            'check_data_consistency': True
        }
        
        # Override from manual config
        config.update(self._config_override.get('validation', {}))
        
        return config
    
    def _get_project_root(self) -> Path:
        """Get the project root directory."""
        # Start from current file and look for project indicators
        current = Path(__file__).parent
        
        for _ in range(5):  # Limit search depth
            if any((current / indicator).exists() for indicator in ['README.md', 'requirements.txt', '.git']):
                return current
            current = current.parent
        
        # Fallback: assume standard structure
        return Path(__file__).parent.parent.parent.parent
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate configuration settings.
        
        Returns:
            Validation result dictionary
            
        Example:
            validation = loader.validate_config()
            if not validation['valid']:
                for issue in validation['issues']:
                    print(f"Config issue: {issue}")
        """
        issues = []
        warnings = []
        
        # Validate embedding config
        embedding_config = self.get_embedding_config()
        if not embedding_config['api_key']:
            issues.append("OpenAI API key not configured")
        
        if embedding_config['model'] not in [
            'text-embedding-3-small', 
            'text-embedding-ada-002', 
            'text-embedding-3-large'
        ]:
            warnings.append(f"Unknown embedding model: {embedding_config['model']}")
        
        # Validate paths
        paths_config = self.get_paths_config()
        if not paths_config['data_directory'].exists():
            warnings.append(f"Data directory does not exist: {paths_config['data_directory']}")
        
        # Validate chunking config
        chunking_config = self.get_chunking_config()
        if chunking_config['chunk_words'] < 50:
            warnings.append("Very small chunk size may not be effective")
        if chunking_config['chunk_words'] > 2000:
            warnings.append("Very large chunk size may exceed token limits")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config_sources': {
                'app_config_loaded': self._app_config is not None,
                'override_provided': bool(self._config_override)
            }
        }
    
    def create_example_config(self, output_path: Path) -> Dict[str, Any]:
        """
        Create example configuration file.
        
        Args:
            output_path: Path to save example config
            
        Returns:
            Result dictionary with creation status
        """
        example_config = {
            'chunking': {
                'chunk_words': 500,
                'overlap_sentences': 1,
                'encoding': 'utf-8'
            },
            'embedding': {
                'model': 'text-embedding-3-small',
                'api_key': 'your-openai-api-key-here',
                'batch_size': 50,
                'max_retries': 5,
                'rate_limit_delay': 1.0
            },
            'paths': {
                'data_directory': 'data',
                'output_directory': 'rag_data'
            },
            'processing': {
                'days_back': 30
            },
            'validation': {
                'max_chunk_file_size_mb': 500,
                'max_metadata_file_size_mb': 100,
                'check_data_consistency': True
            }
        }
        
        try:
            from .utils import DataPersistence
            result = DataPersistence.save_json(example_config, output_path)
            
            if result['status'] == 'success':
                logger.info(f"Example configuration saved to: {output_path}")
                return {
                    'created': True,
                    'config_path': str(output_path),
                    'config': example_config
                }
            else:
                return {
                    'created': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'created': False,
                'error': str(e)
            }


# Convenience function for quick config loading
def load_config(config_override: Optional[Dict[str, Any]] = None) -> ConfigLoader:
    """
    Quick configuration loader.
    
    Args:
        config_override: Optional configuration overrides
        
    Returns:
        Configured ConfigLoader instance
        
    Example:
        config = load_config({'chunk_words': 300})
        paths = config.get_paths_config()
    """
    return ConfigLoader(config_override)