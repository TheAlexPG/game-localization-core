"""
OpenAI provider implementation with parallel processing
"""
import json
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

from .base import AIProvider
from ..core.models import TranslationUnit


class OpenAIProvider(AIProvider):
    """OpenAI API provider with parallel processing support"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o", 
                 temperature: float = 1, max_parallel: int = 5,
                 max_retries: int = 3, retry_delay: int = 2):
        super().__init__(model_name, temperature)
        self.client = OpenAI(api_key=api_key)
        self.max_parallel = max_parallel
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def _make_api_call(self, prompt: str) -> str:
        """Make a single API call with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"API call failed (attempt {attempt + 1}), retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    raise e
    
    def translate_batch(self, units: List[TranslationUnit], 
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       preserve_terms: Optional[List[str]] = None) -> List[TranslationUnit]:
        """Translate a batch of units using parallel processing"""
        
        # Create batches for parallel processing
        batch_size = min(10, len(units))  # Adjust batch size as needed
        batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
        
        translated_units = []
        
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            # Submit all batches
            future_to_batch = {}
            for batch in batches:
                prompt = self._create_translation_prompt(batch, source_lang, target_lang, glossary, preserve_terms)
                future = executor.submit(self._make_api_call, prompt)
                future_to_batch[future] = batch
            
            # Collect results
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
        
        for attempt in range(max_retries):
            try:
                response = self._make_api_call(prompt)
                
                # Check if response is empty or just whitespace
                if not response or not response.strip():
                    print(f"  Empty response on attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Brief pause before retry
                        continue
                    else:
                        print(f"  Failed: Got empty response after {max_retries} attempts")
                        return None  # Signal failure to caller
                
                # Try to parse JSON response
                data = json.loads(response.strip())
                
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
                if attempt < max_retries - 1:
                    time.sleep(2)  # Longer pause for API errors
                    continue
                else:
                    print(f"  Failed: API errors after {max_retries} attempts")
                    return None
    
    def translate_glossary(self, terms: List[str], 
                          source_lang: str, target_lang: str) -> Dict[str, str]:
        """Translate glossary terms"""
        if not terms:
            return {}
        
        prompt = self._create_glossary_prompt(terms, source_lang, target_lang)
        
        try:
            response = self._make_api_call(prompt)
            # Try to parse JSON response
            translations = json.loads(response)
            return translations if isinstance(translations, dict) else {}
        except (json.JSONDecodeError, Exception) as e:
            print(f"Glossary translation failed: {e}")
            # Fallback: return empty dict or keep original terms
            return {term: term for term in terms}