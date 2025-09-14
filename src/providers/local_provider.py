"""
Local AI provider implementation (LM Studio, Ollama, etc.)
"""
import json
import time
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import AIProvider
from ..core.models import TranslationUnit


class LocalProvider(AIProvider):
    """Local AI provider (LM Studio format) with batch support"""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1/chat/completions",
                 model_name: str = "local-model", temperature: float = 0.3,
                 max_parallel: int = 2, max_retries: int = 3, retry_delay: int = 2,
                 timeout: int = 120):
        super().__init__(model_name, temperature)
        self.base_url = base_url
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
    
    def _make_api_call(self, prompt: str, use_json_schema: bool = False, schema_type: str = "term_extraction") -> str:
        """Make a single API call to local model"""
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 8000  # Increased for large glossaries
        }
        
        # Add structured output (LM Studio format)
        if use_json_schema:
            if schema_type == "term_extraction":
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "term_extraction",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "terms": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of extracted game-specific terms"
                                }
                            },
                            "required": ["terms"]
                        }
                    }
                }
            elif schema_type == "glossary_translation":
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "glossary_translation",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "translations": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                    "description": "Dictionary mapping English terms to Ukrainian translations"
                                }
                            },
                            "required": ["translations"]
                        }
                    }
                }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Local API call failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    raise e
    
    def translate_batch(self, units: List[TranslationUnit], 
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       preserve_terms: Optional[List[str]] = None) -> List[TranslationUnit]:
        """Translate a batch of units"""
        
        # For local models, we might want smaller batches
        batch_size = min(5, len(units))  # Smaller batches for local models
        batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
        
        translated_units = []
        
        # Local models might have limited parallel capacity
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            future_to_batch = {}
            for batch in batches:
                prompt = self._create_translation_prompt(batch, source_lang, target_lang, glossary, preserve_terms)
                future = executor.submit(self._make_api_call, prompt)
                future_to_batch[future] = batch
            
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    response = future.result()
                    translations = response.split('\n')
                    
                    # Match translations to units
                    for i, unit in enumerate(batch):
                        if i < len(translations) and translations[i].strip():
                            unit.translated_text = translations[i].strip()
                        else:
                            unit.translated_text = unit.original_text  # Fallback
                    
                    translated_units.extend(batch)
                    
                except Exception as e:
                    print(f"Batch translation failed: {e}")
                    # Fallback: keep original text
                    for unit in batch:
                        unit.translated_text = unit.original_text
                    translated_units.extend(batch)
        
        return translated_units
    
    def extract_terms(self, text: str, context: Optional[str] = None, max_retries: int = 5) -> List[str]:
        """Extract important terms from text with retry logic"""
        prompt = self._create_extraction_prompt(text, context)
        
        # Try structured output first, fallback to regular if it fails
        use_structured = False  # Disable for now, can enable later
        
        for attempt in range(max_retries):
            try:
                # Use structured output for better JSON compliance
                response = self._make_api_call(prompt, use_json_schema=use_structured)
                
                # Check if response is empty or just whitespace
                if not response or not response.strip():
                    print(f"  Empty response on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        print(f"  Failed: Got empty response after {max_retries} attempts")
                        return None
                
                # Clean up response in case model adds extra text
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()
                
                # Try to parse JSON response
                data = json.loads(response)
                
                # Handle structured output format {"terms": [...]}
                if isinstance(data, dict) and "terms" in data:
                    terms = data["terms"]
                elif isinstance(data, list):
                    terms = data
                else:
                    print(f"  Invalid response format on attempt {attempt + 1}/{max_retries}: unexpected structure")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        print(f"  Failed: Invalid format after {max_retries} attempts")
                        return None
                
                # Validate that it's a list
                if not isinstance(terms, list):
                    print(f"  Invalid response format on attempt {attempt + 1}/{max_retries}: not a list")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        print(f"  Failed: Invalid format after {max_retries} attempts")
                        return None
                
                # Success
                return terms
                
            except json.JSONDecodeError as e:
                print(f"  JSON parse error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"  Failed: JSON parse errors after {max_retries} attempts")
                    return None
                    
            except Exception as e:
                print(f"  API error on attempt {attempt + 1}/{max_retries}: {e}")
                
                # If structured output fails and this is first attempt, try without it
                if use_structured and "400" in str(e):
                    print(f"  Structured output failed, trying without schema...")
                    use_structured = False
                    continue
                
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"  Failed: API errors after {max_retries} attempts")
                    return None
    
    def translate_glossary(self, terms: List[str], 
                          source_lang: str, target_lang: str) -> Dict[str, str]:
        """Translate glossary terms"""
        if not terms:
            return {}
        
        # For large glossaries, break into chunks to avoid token limits
        chunk_size = 100  # Process 100 terms at a time for local models
        all_translations = {}
        
        for i in range(0, len(terms), chunk_size):
            chunk = terms[i:i + chunk_size]
            print(f"Translating chunk {i//chunk_size + 1}/{(len(terms) + chunk_size - 1)//chunk_size} ({len(chunk)} terms)")
            
            prompt = self._create_glossary_prompt(chunk, source_lang, target_lang)
            
            try:
                # Use JSON schema for better structured output
                response = self._make_api_call(prompt, use_json_schema=True, schema_type="glossary_translation")
                # Clean up response in case model adds extra text
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                
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