"""Game Translator - AI-powered game localization library

A comprehensive toolkit for AI-powered game localization with validation and quality control.
Supports multiple AI providers, custom validation patterns, and professional workflows.
"""

# Core models and project management
from .core.models import (
    TranslationEntry,
    TranslationStatus,
    ProjectConfig,
    ProgressStats
)
from .core.project import TranslationProject
from .core.tracking import VersionTracker
from .core.translator import TranslationManager

# Validation system
from .core.validation import (
    TranslationValidator,
    ValidationResult,
    ValidationIssue,
    QualityMetrics
)
from .core.custom_patterns import CustomPatternsManager
from .core.smart_glossary import SmartGlossaryMatcher, create_smart_glossary_matcher

# Provider system
from .providers.base import BaseTranslationProvider
from .providers.direct_openai import DirectOpenAIProvider
from .providers.direct_local import DirectLocalProvider
from .providers.mock_provider import MockTranslationProvider

__version__ = "1.0.0"
__author__ = "Oleksandr Basiuk"

# Public API
__all__ = [
    # Core components
    "TranslationProject",
    "TranslationEntry",
    "TranslationStatus",
    "ProjectConfig",
    "ProgressStats",
    "VersionTracker",
    "TranslationManager",

    # Validation
    "TranslationValidator",
    "ValidationResult",
    "ValidationIssue",
    "QualityMetrics",
    "CustomPatternsManager",
    "SmartGlossaryMatcher",
    "create_smart_glossary_matcher",

    # Providers
    "BaseTranslationProvider",
    "DirectOpenAIProvider",
    "DirectLocalProvider",
    "MockTranslationProvider",

    # Convenience functions
    "create_project",
    "load_project",
    "create_validator",
    "get_provider",
]

# Convenience functions
def create_project(name: str, source_lang: str = "en", target_lang: str = "uk",
                  project_dir: str = None) -> TranslationProject:
    """Create new translation project with specified languages

    Args:
        name: Project name
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "uk")
        project_dir: Custom project directory (optional)

    Returns:
        TranslationProject: New project instance
    """
    if project_dir:
        return TranslationProject(name, source_lang, target_lang, project_dir=project_dir)
    return TranslationProject(name, source_lang, target_lang)

def load_project(name: str) -> TranslationProject:
    """Load existing translation project

    Args:
        name: Project name or path

    Returns:
        TranslationProject: Loaded project instance
    """
    return TranslationProject.load(name)

def create_validator(custom_patterns_path: str = None, strict_mode: bool = False) -> TranslationValidator:
    """Create translation validator with optional custom patterns

    Args:
        custom_patterns_path: Path to custom validation patterns file (CSV/Excel/JSON)
        strict_mode: Enable strict validation mode

    Returns:
        TranslationValidator: Configured validator instance
    """
    validator = TranslationValidator()

    if custom_patterns_path:
        manager = CustomPatternsManager()
        custom_patterns = manager.load_patterns(custom_patterns_path)
        validator.add_custom_patterns(custom_patterns)

    if strict_mode:
        validator.strict_mode = True

    return validator

def get_provider(provider_type: str, **kwargs) -> BaseTranslationProvider:
    """Get translation provider instance

    Args:
        provider_type: Provider type ("openai", "local", "mock")
        **kwargs: Provider-specific configuration

    Returns:
        BaseTranslationProvider: Configured provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    providers = {
        "openai": DirectOpenAIProvider,
        "local": DirectLocalProvider,
        "mock": MockTranslationProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unsupported provider type: {provider_type}. "
                        f"Available: {list(providers.keys())}")

    return providers[provider_type](**kwargs)