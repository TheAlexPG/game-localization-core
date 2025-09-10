"""
Base file processor interface
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..core.models import TranslationUnit, ProjectConfig


class BaseFileProcessor(ABC):
    """Abstract base class for file processors"""
    
    def __init__(self, config: ProjectConfig):
        self.config = config
    
    @abstractmethod
    def read_file(self, file_path: Path) -> List[TranslationUnit]:
        """Read file and return list of translation units"""
        pass
    
    @abstractmethod
    def write_file(self, file_path: Path, units: List[TranslationUnit]) -> None:
        """Write translated units to file"""
        pass
    
    @abstractmethod
    def get_output_filename(self, source_filename: str) -> str:
        """Transform source filename to output filename"""
        pass
    
    def get_all_source_files(self) -> List[Path]:
        """Get all source files to process"""
        source_dir = Path(self.config.source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        return list(source_dir.glob("*"))  # Override in subclasses for specific patterns
    
    def extract_text_for_terms(self, file_path: Path) -> str:
        """Extract all text from file for term extraction"""
        units = self.read_file(file_path)
        return "\n".join([unit.original_text for unit in units])