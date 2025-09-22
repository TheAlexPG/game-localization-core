"""Direct Local provider adapted from legacy version"""

import json
import time
import os
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseTranslationProvider
from ..core.smart_glossary import SmartGlossaryMatcher, format_glossary_for_prompt


class DirectLocalProvider(BaseTranslationProvider):
    """Direct Local provider for LM Studio/Ollama"""

    def __init__(self, base_url: str = None, model_name: str = "local-model",
                 temperature: float = 0.3, max_parallel: int = 2,
                 max_retries: int = 3, retry_delay: int = 2,
                 timeout: int = 120, **kwargs):
        super().__init__(model_name, **kwargs)

        self.base_url = base_url or os.getenv("LOCAL_API_URL", "http://localhost:1234/v1/chat/completions")
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None,
                       use_smart_glossary: bool = True) -> List[str]:
        """Translate texts using local API"""
        if not texts:
            return []

        # Process in smaller batches for local models
        batch_size = min(3, len(texts))  # Smaller batches for local models
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

        all_translations = []

        for batch in batches:
            translations = self._translate_batch(batch, source_lang, target_lang, glossary, context, use_smart_glossary)
            all_translations.extend(translations)

        return all_translations

    def _translate_batch(self, texts: List[str], source_lang: str, target_lang: str,
                        glossary: Optional[Dict[str, str]] = None,
                        context: Optional[str] = None,
                        use_smart_glossary: bool = True) -> List[str]:
        """Translate a single batch"""
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
        """Create translation prompt optimized for local models with smart glossary filtering"""
        prompt = f"""Translate the following texts from {source_lang} to {target_lang}.
Provide natural, contextually appropriate translations for a video game.

IMPORTANT RULES:
- Preserve ALL formatting, XML tags, placeholders like {{value}}, {{level}}, etc.
- Keep HTML entities and special characters exactly as they are
- Only translate the actual text content, not markup or code
- Be concise and natural

"""

        if context:
            prompt += f"Context: {context}\n\n"

        # Smart glossary filtering
        if glossary:
            effective_glossary = glossary

            if use_smart_glossary:
                # Use SmartGlossaryMatcher to find only relevant terms
                matcher = SmartGlossaryMatcher(glossary)
                effective_glossary = matcher.find_batch_relevant_terms(texts)

                # Smart Glossary is working silently

            if effective_glossary:
                formatted_glossary = format_glossary_for_prompt(effective_glossary)
                if formatted_glossary:
                    prompt += f"{formatted_glossary}\n\n"

        prompt += "Translate each numbered line:\n\n"
        for i, text in enumerate(texts, 1):
            prompt += f"{i}. {text}\n"

        prompt += "\nProvide only the translations, one per line, same order:"

        return prompt

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                     response_schema: Optional[Dict] = None) -> str:
        """Make API call to local model with optional structured output"""
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional video game translator specializing in English to Ukrainian translation. Provide accurate, natural translations while preserving all formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": 2000
        }

        # Add structured output if requested (LM Studio supports it)
        if use_structured_output and response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": response_schema
            }

        response = requests.post(
            self.base_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout
        )
        response.raise_for_status()

        data = response.json()
        if "choices" not in data or not data["choices"]:
            raise Exception("No response from local model")

        return data["choices"][0]["message"]["content"].strip()

    def _parse_translation_response(self, response: str, expected_count: int) -> List[str]:
        """Parse local model response into list of translations"""
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
        """Extract terms using structured output (if supported by local model)"""
        prompt = f"""Analyze this game text and extract important terms that should be consistently translated.

Look for:
- Character names, location names, item names
- Skill/ability names, unique game terminology
- Proper nouns specific to the game world

Do NOT include: common words, generic gaming terms, UI text, numbers

Text to analyze:
{text}

Context: {context or "Game localization"}

Return a JSON object with extracted terms."""

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
            # Try structured output first
            response = self._make_api_call(prompt, use_structured_output=True, response_schema=schema)

            # Clean up response if needed
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)
            return data.get("terms", [])
        except Exception as e:
            print(f"Structured term extraction failed, trying fallback: {e}")
            # Fallback to non-structured
            try:
                response = self._make_api_call(prompt)
                # Try to parse JSON from response
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                data = json.loads(response.strip())
                return data.get("terms", [])
            except:
                return []

    def translate_glossary_structured(self, terms: List[str], source_lang: str, target_lang: str,
                                    context: Optional[str] = None) -> Dict[str, str]:
        """Translate glossary terms using structured output"""
        if not terms:
            return {}

        prompt = f"""Translate these video game terms from {source_lang} to {target_lang}.
Provide natural {target_lang} translations that fit in a fantasy/adventure game setting.

"""

        # Add glossary context if provided
        if context:
            prompt += f"{context}\n\n"

        prompt += f"""Terms: {', '.join(terms)}

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

            # Clean up response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            data = json.loads(response.strip())
            return data.get("translations", {})
        except Exception as e:
            print(f"Structured glossary translation failed: {e}")
            return {term: term for term in terms}  # Fallback

    def validate_connection(self) -> bool:
        """Test local model connection"""
        try:
            test_response = self._make_api_call("Translate to Ukrainian: Hello")
            return len(test_response) > 0
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "DirectLocalProvider",
            "model": self.model_name,
            "api": self.base_url,
            "temperature": str(self.temperature),
            "timeout": f"{self.timeout}s"
        }