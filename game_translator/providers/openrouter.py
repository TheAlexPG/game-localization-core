"""OpenRouter provider implementation"""

import os
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .llm_base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider using OpenAI-compatible API with custom base URL"""

    def __init__(self, api_key: str = None, model_name: str = "google/gemini-2.5-flash",
                 temperature: float = 1.0, max_parallel: int = 3,
                 max_retries: int = 3, retry_delay: int = 2,
                 site_url: Optional[str] = None, site_name: Optional[str] = None, **kwargs):

        super().__init__(
            model_name=model_name,
            temperature=temperature,
            max_parallel=max_parallel,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs
        )

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
        """Override to use threading since OpenRouter doesn't support batching well"""
        if not texts:
            return []

        # OpenRouter works better with individual requests in parallel
        batches = [[text] for text in texts]  # Each text as separate batch

        all_translations = []

        # Use threading for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            future_to_batch = {
                executor.submit(
                    self._translate_batch,
                    batch, source_lang, target_lang,
                    glossary, context, use_smart_glossary
                ): batch
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

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                      response_schema: Optional[Dict] = None) -> str:
        """Make API call to OpenRouter"""

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

        # Add extra headers if configured
        if self.extra_headers:
            params["extra_headers"] = self.extra_headers

        # OpenRouter may not support structured output for all models
        if use_structured_output and response_schema:
            # Try to use structured output if supported
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
                    import time
                    time.sleep(self.retry_delay)
                else:
                    raise e

        if not response.choices or not response.choices[0].message.content:
            raise Exception("No response from OpenRouter")

        return response.choices[0].message.content.strip()

    def _get_batch_size(self, total_texts: int) -> int:
        """OpenRouter works better with single texts"""
        return 1

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "OpenRouterProvider",
            "model": self.model_name,
            "api": "openrouter.ai",
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel)
        }