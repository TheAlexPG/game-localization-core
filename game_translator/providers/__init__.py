"""AI providers for translation system"""

from typing import Dict, Type
from .base import BaseTranslationProvider


_providers: Dict[str, Type[BaseTranslationProvider]] = {}


def register_provider(name: str, provider_class: Type[BaseTranslationProvider]):
    """Register a translation provider"""
    _providers[name.lower()] = provider_class


def get_provider(name: str, **kwargs) -> BaseTranslationProvider:
    """Get provider instance by name"""
    name = name.lower()
    if name not in _providers:
        raise ValueError(f"No provider registered for: {name}")
    return _providers[name](**kwargs)


def list_providers() -> list:
    """List all available providers"""
    return list(_providers.keys())


# Import and register available providers
from .mock_provider import MockTranslationProvider
from .direct_openai import DirectOpenAIProvider
from .direct_local import DirectLocalProvider

# Register provider types
register_provider("mock", MockTranslationProvider)
register_provider("openai", DirectOpenAIProvider)
register_provider("local", DirectLocalProvider)

# Aliases for clarity
register_provider("direct_openai", DirectOpenAIProvider)
register_provider("direct_local", DirectLocalProvider)