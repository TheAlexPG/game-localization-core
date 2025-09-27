"""Direct OpenAI provider implementation"""

import os
from typing import Dict, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .llm_base import BaseLLMProvider


class DirectOpenAIProvider(BaseLLMProvider):
    """Direct OpenAI provider for translation using OpenAI API"""

    def __init__(self, api_key: str = None, model_name: str = "gpt-4o-mini",
                 temperature: float = 1.0, max_parallel: int = 3,
                 max_retries: int = 3, retry_delay: int = 2, **kwargs):

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

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=self.api_key)

    def _make_api_call(self, prompt: str, use_structured_output: bool = False,
                      response_schema: Optional[Dict] = None) -> str:
        """Make API call to OpenAI"""

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
        # Don't set max_tokens - let API use defaults

        # Add structured output if requested
        if use_structured_output and response_schema:
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
            raise Exception("No response from OpenAI")

        return response.choices[0].message.content.strip()

    def _get_batch_size(self, total_texts: int) -> int:
        """OpenAI works well with batches of 5"""
        return min(5, total_texts)

    def get_info(self) -> Dict[str, str]:
        """Get provider information"""
        return {
            "name": "DirectOpenAIProvider",
            "model": self.model_name,
            "api": "openai.com",
            "temperature": str(self.temperature),
            "max_parallel": str(self.max_parallel)
        }