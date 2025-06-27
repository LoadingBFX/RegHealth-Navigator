import os
import yaml
from pathlib import Path

class Config:
    def __init__(self):
        self.env = os.getenv('FLASK_ENV', 'development')
        self.config = self._load_config()

    def _load_config(self):
        config_path = Path(__file__).parent / f'{self.env}.yml'
        with open(config_path) as f:
            return yaml.safe_load(f)

    @property
    def api_port(self):
        return self.config['server']['port']

    @property
    def api_host(self):
        return self.config['server']['host']

    @property
    def debug(self):
        return self.config['server']['debug']

    @property
    def cors_origins(self):
        return self.config['cors']['origins']

    @property
    def faiss_index_path(self):
        project_root = Path(__file__).parent.parent.parent.resolve()
        rel_path = self.config['rag_data']['faiss_index']
        return str(project_root / rel_path)

    @property
    def faiss_metadata_path(self):
        project_root = Path(__file__).parent.parent.parent.resolve()
        rel_path = self.config['rag_data']['metadata']
        return str(project_root / rel_path)

    @property
    def docs_data_path(self):
        project_root = Path(__file__).parent.parent.parent.resolve()
        rel_path = self.config['docs_data']['path']
        return str(project_root / rel_path)

    @property
    def build_faiss_output_folder(self):
        project_root = Path(__file__).parent.parent.parent.resolve()
        rel_path = self.config['build_faiss']['output_folder']
        return str(project_root / rel_path)

    # Embedding model configuration
    @property
    def default_embedding_model(self):
        """Get the default embedding model from config."""
        return self.config['embedding']['default_model']

    @property
    def embedding_models(self):
        """Get all available embedding models configuration."""
        return self.config['embedding']['models']

    def get_embedding_model_config(self, model_name: str = None):
        """
        Get configuration for a specific embedding model.
        
        Args:
            model_name: Name of the model. If None, uses default model.
            
        Returns:
            Dictionary with model configuration
            
        Raises:
            ValueError: If model is not found in configuration
        """
        if model_name is None:
            model_name = self.default_embedding_model
        
        models = self.embedding_models
        if model_name not in models:
            available_models = list(models.keys())
            raise ValueError(f"Model '{model_name}' not found in configuration. Available models: {available_models}")
        
        return models[model_name]

    def get_embedding_model_price(self, model_name: str = None):
        """Get price per 1K tokens for a model."""
        config = self.get_embedding_model_config(model_name)
        return config['price_per_1k_tokens']

    def get_embedding_model_encoding(self, model_name: str = None):
        """Get encoding type for a model."""
        config = self.get_embedding_model_config(model_name)
        return config['encoding']

    def get_embedding_model_dimension(self, model_name: str = None):
        """Get embedding dimension for a model."""
        config = self.get_embedding_model_config(model_name)
        return config['dimension']

    def get_embedding_model_description(self, model_name: str = None):
        """Get description for a model."""
        config = self.get_embedding_model_config(model_name)
        return config['description']

config = Config()