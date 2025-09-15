"""Game Translator - AI-powered game localization library"""

from .core.models import TranslationEntry, TranslationStatus, ProjectConfig, ProgressStats
from .core.project import TranslationProject
from .core.tracking import VersionTracker
from .core.translator import TranslationManager
from .providers.base import BaseTranslationProvider

__version__ = "1.0.0"

__all__ = [
    "TranslationProject",
    "TranslationEntry",
    "TranslationStatus",
    "ProjectConfig",
    "ProgressStats",
    "VersionTracker",
    "TranslationManager",
    "BaseTranslationProvider",
]

# Convenience functions
def create_project(name: str, source_lang: str = "en", target_lang: str = "uk") -> TranslationProject:
    """Create new translation project"""
    return TranslationProject(name, source_lang, target_lang)

def load_project(name: str) -> TranslationProject:
    """Load existing project"""
    return TranslationProject.load(name)