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
                       context: Optional[str] = None,
                       use_smart_glossary: bool = True) -> List[str]:
        """
        Translate list of texts.

        Args:
            texts: List of source texts to translate
            source_lang: Source language code/name
            target_lang: Target language code/name
            glossary: Optional glossary for consistent terms
            context: Optional context information
            use_smart_glossary: If True, filter glossary to only relevant terms

        Returns:
            List of translated texts in same order
        """
        pass

    def translate_single(self, text: str, source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None,
                        use_smart_glossary: bool = True) -> str:
        """Translate single text (convenience method)"""
        result = self.translate_texts([text], source_lang, target_lang, glossary, context, use_smart_glossary)
        return result[0] if result else text

    def validate_connection(self) -> bool:
        """Test if provider is available and working"""
        try:
            test_result = self.translate_single("Hello", "en", "uk")
            return len(test_result) > 0
        except Exception:
            return False

    @abstractmethod
    def translate_glossary_structured(self, terms: List[str], source_lang: str, target_lang: str,
                                    context: Optional[str] = None) -> Dict[str, str]:
        """
        Translate glossary terms using structured output.

        Args:
            terms: List of terms to translate
            source_lang: Source language code/name
            target_lang: Target language code/name
            context: Optional glossary context with translation rules

        Returns:
            Dictionary mapping source terms to translations
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": self.__class__.__name__,
            "model": self.model_name or "default",
            "config": str(self.config)
        }