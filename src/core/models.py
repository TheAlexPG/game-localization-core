"""
Core models for translation pipeline
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class TranslationUnit(ABC):
    """Base abstract class for translation objects"""
    key: str
    original_text: str
    translated_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranslationUnit':
        """Create from dictionary"""
        pass


@dataclass
class LineTranslationUnit(TranslationUnit):
    """For line-by-line translation (like Silksong entries)"""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'line',
            'key': self.key,
            'original_text': self.original_text,
            'translated_text': self.translated_text,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LineTranslationUnit':
        return cls(
            key=data['key'],
            original_text=data['original_text'],
            translated_text=data.get('translated_text'),
            metadata=data.get('metadata')
        )


@dataclass
class BlockTranslationUnit(TranslationUnit):
    """For block translation (for other games that might need it)"""
    block_type: str = "paragraph"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'block',
            'key': self.key,
            'original_text': self.original_text,
            'translated_text': self.translated_text,
            'block_type': self.block_type,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockTranslationUnit':
        return cls(
            key=data['key'],
            original_text=data['original_text'],
            translated_text=data.get('translated_text'),
            block_type=data.get('block_type', 'paragraph'),
            metadata=data.get('metadata')
        )


@dataclass
class ProjectConfig:
    """Configuration for a translation project"""
    name: str
    source_lang: str
    target_lang_code: str
    source_dir: str
    glossary_terms: Optional[Dict[str, str]] = None
    preserve_terms: Optional[list] = None
    
    def get_data_dir(self) -> str:
        """Get data directory for this project"""
        return f"./data/{self.name}"
    
    def get_output_dir(self) -> str:
        """Get output directory for translated files"""
        return f"./data/{self.name}/{self.name}_ua"
    
    def get_glossary_dir(self) -> str:
        """Get glossary directory"""
        return f"./data/{self.name}/glossaries"
    
    def get_cache_dir(self) -> str:
        """Get cache directory"""
        return f"./data/{self.name}/cache"