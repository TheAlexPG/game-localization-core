"""Enhanced base class with common LLM logic"""

import json
import time
from typing import List, Dict, Optional
from abc import abstractmethod

from .base import BaseTranslationProvider
from ..core.prompts import PromptManager, ResponseParser, PromptSchemas
from ..core.smart_glossary import SmartGlossaryMatcher, format_glossary_for_prompt


class BaseLLMProvider(BaseTranslationProvider):
    """Base class with common logic for LLM-based translation providers"""

    def __init__(self, model_name: str = None,
                 temperature: float = 1.0,
                 max_parallel: int = 3,
                 max_retries: int = 3,
                 retry_delay: int = 2,
                 **kwargs):
        super().__init__(model_name, **kwargs)
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.prompt_manager = PromptManager()
        self.response_parser = ResponseParser()
        self.schemas = PromptSchemas()

    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None,
                       use_smart_glossary: bool = True) -> List[str]:
        """Translate texts using the configured LLM with batching"""
        if not texts:
            return []

        # Get batch size from provider-specific implementation
        batch_size = self._get_batch_size(len(texts))
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

        all_translations = []

        for batch in batches:
            translations = self._translate_batch(
                batch, source_lang, target_lang,
                glossary, context, use_smart_glossary
            )
            all_translations.extend(translations)

        return all_translations

    def _translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None,
                        use_smart_glossary: bool = True) -> List[str]:
        """Translate a single batch with retry logic"""

        # Prepare glossary
        effective_glossary_text = self._prepare_glossary(texts, glossary, use_smart_glossary)

        # Create prompt using centralized manager
        prompt = self.prompt_manager.get_translation_prompt(
            texts, source_lang, target_lang,
            effective_glossary_text, context
        )

        for attempt in range(self.max_retries):
            try:
                response = self._make_api_call(prompt)
                translations = self.response_parser.parse_translation_response(
                    response, len(texts)
                )

                # Ensure we have correct number of translations
                while len(translations) < len(texts):
                    translations.append(texts[len(translations)])

                return translations[:len(texts)]

            except Exception as e:
                print(f"Translation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    print(f"Batch translation failed after {self.max_retries} attempts")
                    return texts  # Return original texts as fallback

    def _prepare_glossary(self, texts: List[str],
                         glossary: Optional[Dict[str, str]],
                         use_smart_glossary: bool) -> Optional[str]:
        """Prepare glossary text with smart filtering"""
        if not glossary:
            return None

        effective_glossary = glossary

        if use_smart_glossary:
            # Use SmartGlossaryMatcher to find only relevant terms
            matcher = SmartGlossaryMatcher(glossary)
            effective_glossary = matcher.find_batch_relevant_terms(texts)

        if effective_glossary:
            return format_glossary_for_prompt(effective_glossary)

        return None

    def extract_terms_structured(self, text: str, context: Optional[str] = None) -> List[str]:
        """Extract terms using structured output for better reliability"""
        prompt = self.prompt_manager.get_term_extraction_prompt(text, context)
        schema = self.schemas.get_term_extraction_schema()

        try:
            response = self._make_api_call(prompt, use_structured_output=True, response_schema=schema)
            data = json.loads(response)
            return data.get("terms", [])
        except Exception as e:
            print(f"Structured term extraction failed: {e}")
            return []

    def translate_glossary_structured(self, terms: List[str], source_lang: str, target_lang: str,
                                    context: Optional[str] = None) -> Dict[str, str]:
        """Translate glossary terms using structured output"""
        if not terms:
            return {}

        prompt = self.prompt_manager.get_glossary_translation_prompt(
            terms, source_lang, target_lang, context
        )
        schema = self.schemas.get_glossary_translation_schema()

        try:
            response = self._make_api_call(prompt, use_structured_output=True, response_schema=schema)
            data = json.loads(response)
            return data.get("translations", {})
        except Exception as e:
            print(f"Structured glossary translation failed: {e}")
            return {term: term for term in terms}  # Fallback

    def validate_connection(self) -> bool:
        """Test LLM connection"""
        try:
            prompt = self.prompt_manager.get_validation_test_prompt()
            test_response = self._make_api_call(prompt)
            return len(test_response) > 0
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False

    @abstractmethod
    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                      response_schema: Optional[Dict] = None) -> str:
        """Make API call to the LLM service

        Args:
            prompt: The prompt to send
            use_structured_output: Whether to use structured output
            response_schema: Schema for structured output

        Returns:
            Response text from the LLM

        Note:
            This method must be implemented by each specific provider
        """
        pass

    def _get_batch_size(self, total_texts: int) -> int:
        """Get optimal batch size for this provider

        Override in specific providers if needed
        """
        return min(5, total_texts)  # Default batch size

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": self.__class__.__name__,
            "model": self.model_name or "default",
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel)
        }