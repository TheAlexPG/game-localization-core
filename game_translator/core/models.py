"""Core data models for translation system"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import hashlib
import re


class TranslationStatus(Enum):
    """Translation entry status"""
    PENDING = "pending"
    TRANSLATED = "translated"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    NEEDS_UPDATE = "needs_update"
    SKIPPED = "skipped"


@dataclass
class TranslationEntry:
    """Single translation unit"""
    key: str
    source_text: str
    source_hash: str = field(init=False)
    translated_text: Optional[str] = None
    status: TranslationStatus = TranslationStatus.PENDING
    context: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_modified: datetime = field(default_factory=datetime.now)
    translator_notes: Optional[str] = None

    def __post_init__(self):
        self.source_hash = self._calculate_hash(self.source_text)

    @staticmethod
    def _calculate_hash(text: str) -> str:
        """Calculate hash of text for change detection"""
        # Normalize whitespace but preserve structure
        normalized = re.sub(r'\s+', ' ', text.strip())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def is_technical(self) -> bool:
        """Check if this is technical text (markers, tags, etc)"""
        # Remove common markup patterns
        clean = re.sub(r'<[^>]+>|{[^}]+}|\[[^\]]+\]', '', self.source_text)
        clean = clean.strip()

        # Technical if empty after cleanup or just numbers
        return len(clean) < 3 or clean.isdigit()

    def should_skip_translation(self, skip_symbols: bool = True) -> bool:
        """Check if this entry should be skipped from translation

        Args:
            skip_symbols: If True, skip entries that are just numbers or symbols

        Returns:
            True if entry should be skipped
        """
        if not skip_symbols:
            return False

        text = self.source_text.strip()

        # Skip if empty
        if not text:
            return True

        # Skip if only numbers
        if text.replace(',', '').replace('.', '').replace(' ', '').isdigit():
            return True

        # Skip if only symbols (including variables like {1}, ${1}, etc)
        # but preserve actual text with variables
        import re
        # Remove known variable patterns
        clean = re.sub(r'\{[^}]+\}|\$:\s*\{[^}]+\}|\$\{[^}]+\}|\$[^$]+\$', '', text)
        clean = clean.strip()

        # If nothing left after removing variables, it's just variables
        if not clean:
            return True

        # Check if remaining is just punctuation/symbols
        if all(c in ' ,.!?;:()[]{}"\'-_=+*&^%$#@~/\\|<>' for c in clean):
            return True

        return False

    def needs_update(self, new_source: str) -> bool:
        """Check if source has changed"""
        return self._calculate_hash(new_source) != self.source_hash

    def update_translation(self, translation: str):
        """Update translation and status"""
        self.translated_text = translation
        self.status = TranslationStatus.TRANSLATED
        self.last_modified = datetime.now()


@dataclass
class ProjectConfig:
    """Project configuration"""
    name: str
    source_lang: str
    target_lang: str
    source_format: str = "json"
    output_format: str = "json"
    glossary_path: Optional[str] = None
    preserve_terms: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Context for better translations
    project_context: Dict[str, Any] = field(default_factory=dict)  # General project context
    glossary_context: Dict[str, Any] = field(default_factory=dict)  # Context for glossary extraction

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "source_format": self.source_format,
            "output_format": self.output_format,
            "glossary_path": self.glossary_path,
            "preserve_terms": self.preserve_terms,
            "metadata": self.metadata,
            "project_context": self.project_context,
            "glossary_context": self.glossary_context
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create from dictionary"""
        return cls(
            name=data["name"],
            source_lang=data["source_lang"],
            target_lang=data["target_lang"],
            source_format=data.get("source_format", "json"),
            output_format=data.get("output_format", "json"),
            glossary_path=data.get("glossary_path"),
            preserve_terms=data.get("preserve_terms", []),
            metadata=data.get("metadata", {}),
            project_context=data.get("project_context", {}),
            glossary_context=data.get("glossary_context", {})
        )


@dataclass
class ProgressStats:
    """Translation progress statistics"""
    total: int = 0
    pending: int = 0
    translated: int = 0
    reviewed: int = 0
    approved: int = 0
    needs_update: int = 0
    skipped: int = 0

    @property
    def completion_rate(self) -> float:
        """Calculate completion percentage"""
        if self.total == 0:
            return 0
        return (self.translated + self.reviewed + self.approved) / self.total * 100

    def update_from_entries(self, entries: list):
        """Update stats from entry list"""
        self.total = len(entries)
        self.pending = sum(1 for e in entries if e.status == TranslationStatus.PENDING)
        self.translated = sum(1 for e in entries if e.status == TranslationStatus.TRANSLATED)
        self.reviewed = sum(1 for e in entries if e.status == TranslationStatus.REVIEWED)
        self.approved = sum(1 for e in entries if e.status == TranslationStatus.APPROVED)
        self.needs_update = sum(1 for e in entries if e.status == TranslationStatus.NEEDS_UPDATE)
        self.skipped = sum(1 for e in entries if e.status == TranslationStatus.SKIPPED)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total": self.total,
            "pending": self.pending,
            "translated": self.translated,
            "reviewed": self.reviewed,
            "approved": self.approved,
            "needs_update": self.needs_update,
            "skipped": self.skipped,
            "completion_rate": self.completion_rate
        }