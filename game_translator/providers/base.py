"""Base interface for translation providers"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseTranslationProvider(ABC):
    """Base class for AI translation providers"""

    def __init__(self, model_name: str = None, **kwargs):
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None) -> List[str]:
        """
        Translate list of texts.

        Args:
            texts: List of source texts to translate
            source_lang: Source language code/name
            target_lang: Target language code/name
            glossary: Optional glossary for consistent terms
            context: Optional context information

        Returns:
            List of translated texts in same order
        """
        pass

    def translate_single(self, text: str, source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None) -> str:
        """Translate single text (convenience method)"""
        result = self.translate_texts([text], source_lang, target_lang, glossary, context)
        return result[0] if result else text

    def validate_connection(self) -> bool:
        """Test if provider is available and working"""
        try:
            test_result = self.translate_single("Hello", "en", "uk")
            return len(test_result) > 0
        except Exception:
            return False

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": self.__class__.__name__,
            "model": self.model_name or "default",
            "config": str(self.config)
        }