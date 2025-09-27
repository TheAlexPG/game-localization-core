"""Direct Local provider implementation"""

import os
import json
import requests
from typing import Dict, Optional

from .llm_base import BaseLLMProvider


class DirectLocalProvider(BaseLLMProvider):
    """Direct Local provider for LM Studio/Ollama and other local LLM servers"""

    def __init__(self, base_url: str = None, model_name: str = "local-model",
                 temperature: float = 0.3, max_parallel: int = 2,
                 max_retries: int = 3, retry_delay: int = 2,
                 timeout: int = 120, **kwargs):

        super().__init__(
            model_name=model_name,
            temperature=temperature,
            max_parallel=max_parallel,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs
        )

        self.base_url = base_url or os.getenv("LOCAL_API_URL", "http://localhost:1234/v1/chat/completions")
        self.timeout = timeout

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                      response_schema: Optional[Dict] = None) -> str:
        """Make API call to local LLM server"""

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature
        }

        # Local models may or may not support structured output
        if use_structured_output and response_schema:
            # Try JSON mode if available
            payload["response_format"] = {"type": "json"}

        # Make HTTP request with retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                break
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    import time
                    time.sleep(self.retry_delay)
                else:
                    raise e

        result = response.json()

        if not result.get('choices') or not result['choices'][0].get('message', {}).get('content'):
            raise Exception("No response from local model")

        return result['choices'][0]['message']['content'].strip()

    def _get_batch_size(self, total_texts: int) -> int:
        """Local models work better with smaller batches"""
        return min(3, total_texts)

    def extract_terms_structured(self, text: str, context: Optional[str] = None):
        """Override for local models that may not support structured output well"""
        # Try structured output first
        try:
            return super().extract_terms_structured(text, context)
        except Exception as e:
            print(f"Structured extraction failed for local model: {e}")
            # Fallback to simple extraction
            prompt = self.prompt_manager.get_term_extraction_prompt(text, context)
            prompt += "\n\nList the terms one per line:"

            try:
                response = self._make_api_call(prompt)
                # Parse simple line-based response
                terms = [line.strip() for line in response.split('\n') if line.strip()]
                # Filter out common instructions or meta text
                terms = [t for t in terms if len(t) > 1 and not t.startswith('[') and not t.startswith('(')]
                return terms[:20]  # Limit to reasonable number
            except Exception as e2:
                print(f"Simple extraction also failed: {e2}")
                return []

    def translate_glossary_structured(self, terms, source_lang: str, target_lang: str,
                                    context: Optional[str] = None) -> Dict[str, str]:
        """Override for local models that may not support structured output well"""
        # Try structured output first
        try:
            return super().translate_glossary_structured(terms, source_lang, target_lang, context)
        except Exception as e:
            print(f"Structured glossary translation failed for local model: {e}")
            # Fallback to simple format
            prompt = self.prompt_manager.get_glossary_translation_prompt(
                terms, source_lang, target_lang, context
            )
            prompt = prompt.replace("Return a JSON object with translations.",
                                  "Translate each term and provide the translation after '->':\nExample: term1 -> translation1")

            try:
                response = self._make_api_call(prompt)
                # Parse simple format
                translations = {}
                for line in response.split('\n'):
                    if '->' in line:
                        parts = line.split('->', 1)
                        if len(parts) == 2:
                            term = parts[0].strip()
                            translation = parts[1].strip()
                            # Match with original terms
                            for original_term in terms:
                                if term.lower() in original_term.lower() or original_term.lower() in term.lower():
                                    translations[original_term] = translation
                                    break

                # Fill missing with originals
                for term in terms:
                    if term not in translations:
                        translations[term] = term

                return translations
            except Exception as e2:
                print(f"Simple glossary translation also failed: {e2}")
                return {term: term for term in terms}

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "DirectLocalProvider",
            "model": self.model_name,
            "api": self.base_url,
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel),
            "timeout": str(self.timeout)
        }