"""
Caching utilities for translation results
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..core.models import TranslationUnit, ProjectConfig


class TranslationCache:
    """Cache for translation results to avoid re-translating same content"""
    
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.cache_dir = Path(config.get_cache_dir())
        self.cache_file = self.cache_dir / "translation_cache.json"
        self.cache_data = {}
        self.load_cache()
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str,
                      glossary: Optional[Dict[str, str]] = None) -> str:
        """Generate cache key for translation"""
        cache_content = f"{text}|{source_lang}|{target_lang}"
        if glossary:
            cache_content += f"|{json.dumps(glossary, sort_keys=True)}"
        
        return hashlib.md5(cache_content.encode()).hexdigest()
    
    def load_cache(self):
        """Load existing cache from disk"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache_data = json.load(f)
                print(f"📦 Loaded translation cache with {len(self.cache_data)} entries")
            except Exception as e:
                print(f"⚠️ Error loading cache: {e}")
                self.cache_data = {}
        else:
            self.cache_data = {}
    
    def save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def get_translation(self, text: str, source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Get cached translation if available"""
        cache_key = self._get_cache_key(text, source_lang, target_lang, glossary)
        return self.cache_data.get(cache_key)
    
    def set_translation(self, text: str, translation: str, source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None):
        """Cache a translation"""
        cache_key = self._get_cache_key(text, source_lang, target_lang, glossary)
        self.cache_data[cache_key] = translation
    
    def cache_batch_translations(self, units: List[TranslationUnit], source_lang: str, target_lang: str,
                               glossary: Optional[Dict[str, str]] = None):
        """Cache multiple translations at once"""
        for unit in units:
            if unit.translated_text and unit.translated_text != unit.original_text:
                self.set_translation(unit.original_text, unit.translated_text, 
                                   source_lang, target_lang, glossary)
        
        # Save to disk after batch update
        self.save_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_entries': len(self.cache_data),
            'cache_file': str(self.cache_file),
            'cache_size_mb': self.cache_file.stat().st_size / 1024 / 1024 if self.cache_file.exists() else 0
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache_data = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        print("🗑️ Cache cleared")