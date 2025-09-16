"""Direct OpenAI provider adapted from legacy version"""

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


class DirectOpenAIProvider(BaseTranslationProvider):
    """Direct OpenAI provider based on legacy implementation"""

    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini",
                 temperature: float = 0.3, max_parallel: int = 3,
                 max_retries: int = 3, retry_delay: int = 2, **kwargs):
        super().__init__(model_name, **kwargs)

        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key)
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None) -> List[str]:
        """Translate texts using OpenAI API with batching"""
        if not texts:
            return []

        # Process in small batches for better results
        batch_size = min(5, len(texts))
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

        all_translations = []

        for batch in batches:
            translations = self._translate_batch(batch, source_lang, target_lang, glossary, context)
            all_translations.extend(translations)

        return all_translations

    def _translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None) -> List[str]:
        """Translate a single batch"""
        prompt = self._create_translation_prompt(texts, source_lang, target_lang, glossary, context)

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
                                 context: Optional[str] = None) -> str:
        """Create translation prompt"""
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
            # Context can be a simple string or formatted context from project
            prompt += f"{context}\n\n"

        if glossary:
            prompt += "Use these consistent translations for specific terms:\n"
            for en_term, ua_term in glossary.items():
                prompt += f"- {en_term} → {ua_term}\n"
            prompt += "\n"

        prompt += "Translate each numbered line and provide ONLY the translation, preserving all formatting:\n\n"

        for i, text in enumerate(texts, 1):
            prompt += f"{i}. {text}\n"

        prompt += "\nRespond with only the translations, one per line, in the same order:"

        return prompt

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                     response_schema: Optional[Dict] = None) -> str:
        """Make API call to OpenAI with optional structured output"""

        params = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional video game translator specializing in English to Ukrainian translation. Provide accurate, natural translations while preserving all formatting and technical elements."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": 2000
        }

        # Add structured output if requested and model supports it
        if use_structured_output and response_schema and "gpt-4" in self.model_name:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": response_schema
            }

        response = self.client.chat.completions.create(**params)

        if not response.choices or not response.choices[0].message.content:
            raise Exception("No response from OpenAI")

        return response.choices[0].message.content.strip()

    def _parse_translation_response(self, response: str, expected_count: int) -> List[str]:
        """Parse OpenAI response into list of translations"""
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

        prompt = f"""Translate these video game terms from {source_lang} to {target_lang}.
Provide natural {target_lang} translations that fit in a fantasy/adventure game setting.

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
        """Test OpenAI connection"""
        try:
            test_response = self._make_api_call("Translate to Ukrainian: Hello")
            return len(test_response) > 0
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "DirectOpenAIProvider",
            "model": self.model_name,
            "api": "openai.com",
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel)
        }