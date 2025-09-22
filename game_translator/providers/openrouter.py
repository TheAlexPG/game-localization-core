"""OpenRouter provider - OpenAI-compatible API with custom base URL"""

import json
import time
import os
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseTranslationProvider
from ..core.smart_glossary import SmartGlossaryMatcher, format_glossary_for_prompt


class OpenRouterProvider(BaseTranslationProvider):
    """OpenRouter provider using OpenAI client with custom base URL"""

    def __init__(self, api_key: str = None, model_name: str = "google/gemini-2.5-flash",
                 temperature: float = 1.0, max_parallel: int = 3,
                 max_retries: int = 3, retry_delay: int = 2,
                 site_url: Optional[str] = None, site_name: Optional[str] = None, **kwargs):
        super().__init__(model_name, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required (OPENROUTER_API_KEY env var)")

        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

        self.temperature = temperature
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Optional headers for OpenRouter rankings
        self.extra_headers = {}
        if site_url:
            self.extra_headers["HTTP-Referer"] = site_url
        if site_name:
            self.extra_headers["X-Title"] = site_name

    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None,
                       use_smart_glossary: bool = True) -> List[str]:
        """Translate texts using OpenRouter API with threading (no batching)"""
        if not texts:
            return []

        # OpenRouter doesn't support batching, so process one by one with threads
        # Use smaller batches for better API compatibility
        batch_size = 1  # Process individually for OpenRouter
        batches = [[text] for text in texts]  # Each text as separate batch

        all_translations = []

        # Use threading for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            future_to_batch = {
                executor.submit(self._translate_batch, batch, source_lang, target_lang, glossary, context, use_smart_glossary): batch
                for batch in batches
            }

            for future in as_completed(future_to_batch):
                try:
                    translations = future.result()
                    all_translations.extend(translations)
                except Exception as e:
                    batch = future_to_batch[future]
                    print(f"Translation failed for batch: {e}")
                    # Return original text as fallback
                    all_translations.extend(batch)

        return all_translations

    def _translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None,
                        use_smart_glossary: bool = True) -> List[str]:
        """Translate a single batch (typically one text for OpenRouter)"""
        prompt = self._create_translation_prompt(texts, source_lang, target_lang, glossary, context, use_smart_glossary)

        for attempt in range(self.max_retries):
            try:
                response = self._make_api_call(prompt)
                translations = self._parse_translation_response(response, len(texts))

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

    def _create_translation_prompt(self, texts: List[str], source_lang: str, target_lang: str,
                                 glossary: Optional[Dict[str, str]] = None,
                                 context: Optional[str] = None,
                                 use_smart_glossary: bool = True) -> str:
        """Create translation prompt with smart glossary filtering"""
        prompt = f"""Translate the following texts from {source_lang} to {target_lang}.
Keep the translation natural and contextually appropriate for a video game.

CRITICAL FORMATTING RULES:
- Preserve ALL XML-like tags exactly: &lt;page=S&gt;, &lt;hpage&gt;, etc.
- Keep ALL special characters and HTML entities as-is: &#8217;, &amp;, etc.
- Do NOT change any formatting, tags, or special symbols
- Only translate the actual text content, not the markup
- Keep placeholders like {{value}}, {{level}} exactly as they are

"""

        # Add project context if provided
        if context:
            prompt += f"{context}\n\n"

        # Smart glossary filtering
        if glossary:
            effective_glossary = glossary

            if use_smart_glossary:
                # Use SmartGlossaryMatcher to find only relevant terms
                matcher = SmartGlossaryMatcher(glossary)
                effective_glossary = matcher.find_batch_relevant_terms(texts)

            if effective_glossary:
                formatted_glossary = format_glossary_for_prompt(effective_glossary)
                if formatted_glossary:
                    prompt += f"{formatted_glossary}\n\n"

        prompt += "Translate each numbered line and provide ONLY the translation, preserving all formatting:\n\n"

        for i, text in enumerate(texts, 1):
            prompt += f"{i}. {text}\n"

        prompt += "\nRespond with only the translations, one per line, in the same order:"

        return prompt

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                     response_schema: Optional[Dict] = None) -> str:
        """Make API call to OpenRouter with optional structured output"""

        params = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature
        }

        # Add extra headers for OpenRouter if configured
        if self.extra_headers:
            params["extra_headers"] = self.extra_headers

        # Add structured output if requested (check OpenRouter docs for support)
        if use_structured_output and response_schema:
            # OpenRouter supports structured outputs for some models
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": response_schema
            }

        # Make API call with retry logic
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**params)
                break
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    raise e

        if not response.choices or not response.choices[0].message.content:
            raise Exception("No response from OpenRouter")

        return response.choices[0].message.content.strip()

    def _parse_translation_response(self, response: str, expected_count: int) -> List[str]:
        """Parse OpenRouter response into list of translations"""
        lines = response.strip().split('\n')
        translations = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering if present (1. , 2. , etc.)
            if line and line[0].isdigit() and '. ' in line:
                line = line.split('. ', 1)[1] if '. ' in line else line

            if line:
                translations.append(line)

        return translations

    def extract_terms_structured(self, text: str, context: Optional[str] = None) -> List[str]:
        """Extract terms using structured output for better reliability"""
        prompt = f"""Analyze this game text and extract important terms that should be consistently translated.

Look for:
- Character names, location names, item names
- Skill/ability names, unique game terminology
- Proper nouns specific to the game world

Do NOT include: common words, generic gaming terms, UI text, numbers

Text to analyze:
{text}

"""

        # Add glossary context if provided
        if context:
            prompt += f"{context}\n\n"
        else:
            prompt += "Context: Game localization\n\n"

        prompt += "Return a JSON object with extracted terms."

        schema = {
            "name": "term_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of important game-specific terms"
                    }
                },
                "required": ["terms"]
            }
        }

        try:
            response = self._make_api_call(prompt, use_structured_output=True, response_schema=schema)
            data = json.loads(response)
            return data.get("terms", [])
        except Exception as e:
            print(f"Structured term extraction failed: {e}")
            return []

    def translate_glossary_structured(self, terms: List[str], source_lang: str, target_lang: str) -> Dict[str, str]:
        """Translate glossary terms using structured output"""
        if not terms:
            return {}

        # Map language codes to full names for better AI understanding
        lang_mapping = {
            'uk': 'Ukrainian',
            'ru': 'Russian',
            'de': 'German',
            'fr': 'French',
            'es': 'Spanish',
            'it': 'Italian',
            'pl': 'Polish',
            'en': 'English'
        }

        source_lang_name = lang_mapping.get(source_lang, source_lang)
        target_lang_name = lang_mapping.get(target_lang, target_lang)

        prompt = f"""Translate these video game terms from {source_lang_name} to {target_lang_name}.
Provide natural {target_lang_name} translations that fit in a fantasy/adventure game setting.

Terms: {', '.join(terms)}

Return a JSON object with translations."""

        schema = {
            "name": "glossary_translation",
            "schema": {
                "type": "object",
                "properties": {
                    "translations": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                        "description": "Dictionary mapping source terms to target translations"
                    }
                },
                "required": ["translations"]
            }
        }

        try:
            response = self._make_api_call(prompt, use_structured_output=True, response_schema=schema)
            data = json.loads(response)
            return data.get("translations", {})
        except Exception as e:
            print(f"Structured glossary translation failed: {e}")
            return {term: term for term in terms}  # Fallback

    def validate_connection(self) -> bool:
        """Test OpenRouter connection"""
        try:
            test_response = self._make_api_call("Translate to Ukrainian: Hello")
            return len(test_response) > 0
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "OpenRouterProvider",
            "model": self.model_name,
            "api": "openrouter.ai",
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel)
        }