"""
DeepSeek AI provider implementation
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek AI provider (OpenAI-compatible API)"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat",
                 temperature: float = 1.3, max_parallel: int = 5, max_retries: int = 3,
                 retry_delay: int = 2, timeout: int = 120):
        # Initialize parent without calling super().__init__()
        self.model_name = model_name
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Create DeepSeek client with custom base URL
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        # DeepSeek specific token limit
        self.max_tokens = 8000
    
    def _make_api_call(self, prompt: str, use_json_schema: bool = False, schema_type: str = "glossary_translation") -> str:
        """Make a single API call with retry logic and DeepSeek settings"""
        import time
        
        params = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # Add JSON schema for structured output
        if use_json_schema and schema_type == "glossary_translation":
            params["response_format"] = {
                "type": "json_object"
            }
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    raise e
    
    def translate_glossary(self, terms, source_lang: str, target_lang: str):
        """Translate glossary terms with DeepSeek-specific response cleaning"""
        if not terms:
            return {}
        
        # For large glossaries, break into chunks to avoid token limits
        chunk_size = 100  # Process 100 terms at a time for DeepSeek
        all_translations = {}
        
        for i in range(0, len(terms), chunk_size):
            chunk = terms[i:i + chunk_size]
            print(f"Translating chunk {i//chunk_size + 1}/{(len(terms) + chunk_size - 1)//chunk_size} ({len(chunk)} terms)")
            
            prompt = self._create_glossary_prompt(chunk, source_lang, target_lang)
            
            try:
                # Use JSON schema for structured output
                response = self._make_api_call(prompt, use_json_schema=True, schema_type="glossary_translation")
                
                # With json_object response format, should get clean JSON
                import json
                data = json.loads(response)
                
                # Handle structured output format {"translations": {...}}
                if isinstance(data, dict) and "translations" in data:
                    translations = data["translations"]
                elif isinstance(data, dict):
                    translations = data
                else:
                    translations = {}
                
                if isinstance(translations, dict):
                    all_translations.update(translations)
                else:
                    print(f"Chunk {i//chunk_size + 1}: Invalid response format")
                    # Fallback: return original terms for this chunk
                    for term in chunk:
                        all_translations[term] = term
                        
            except (json.JSONDecodeError, Exception) as e:
                print(f"Chunk {i//chunk_size + 1} translation failed: {e}")
                # Fallback: return original terms for this chunk
                for term in chunk:
                    all_translations[term] = term
        
        return all_translations