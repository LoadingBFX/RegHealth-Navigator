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

config = Config()