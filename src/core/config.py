"""
Configuration management for translation projects
"""
import os
from pathlib import Path
from typing import Dict, Optional
from .models import ProjectConfig


class ConfigManager:
    """Manages project configurations"""
    
    def __init__(self):
        self._configs: Dict[str, ProjectConfig] = {}
    
    def register_project(self, config: ProjectConfig):
        """Register a project configuration"""
        self._configs[config.name] = config
    
    def get_project(self, name: str) -> ProjectConfig:
        """Get project configuration by name"""
        if name not in self._configs:
            raise ValueError(f"Project '{name}' not found. Available projects: {list(self._configs.keys())}")
        return self._configs[name]
    
    def list_projects(self) -> list:
        """List all registered projects"""
        return list(self._configs.keys())
    
    def ensure_project_dirs(self, project_name: str):
        """Ensure all necessary directories exist for a project"""
        config = self.get_project(project_name)
        
        dirs_to_create = [
            config.get_data_dir(),
            config.get_output_dir(),
            config.get_glossary_dir(),
            config.get_cache_dir()
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


# Global config manager instance
config_manager = ConfigManager()