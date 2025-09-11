"""
Base AI provider interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..core.models import TranslationUnit


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, model_name: str, temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature
    
    @abstractmethod
    def translate_batch(self, units: List[TranslationUnit], 
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       preserve_terms: Optional[List[str]] = None) -> List[TranslationUnit]:
        """Translate a batch of translation units"""
        pass
    
    @abstractmethod
    def extract_terms(self, text: str, context: Optional[str] = None, max_retries: int = 5) -> List[str]:
        """Extract important terms/names from text that should be in glossary"""
        pass
    
    @abstractmethod
    def translate_glossary(self, terms: List[str], 
                          source_lang: str, target_lang: str) -> Dict[str, str]:
        """Translate a list of terms for glossary"""
        pass
    
    def _create_translation_prompt(self, units: List[TranslationUnit], 
                                 source_lang: str, target_lang: str,
                                 glossary: Optional[Dict[str, str]] = None,
                                 preserve_terms: Optional[List[str]] = None) -> str:
        """Create prompt for translation"""
        
        prompt = f"""Translate the following text from {source_lang} to {target_lang}.
Keep the translation natural and contextually appropriate for a video game.

CRITICAL FORMATTING RULES:
- Preserve ALL XML-like tags exactly: &lt;page=S&gt;, &lt;hpage&gt;, etc.
- Keep ALL special characters and HTML entities as-is: &#8217;, &amp;, etc.
- Do NOT change any formatting, tags, or special symbols
- Only translate the actual text content, not the markup

"""
        
        if preserve_terms:
            prompt += f"IMPORTANT: Do NOT translate these terms - keep them as is: {', '.join(preserve_terms)}\n\n"
        
        if glossary:
            prompt += "Use these consistent translations for specific terms:\n"
            for en_term, ua_term in glossary.items():
                prompt += f"- {en_term} → {ua_term}\n"
            prompt += "\n"
        
        prompt += "Translate each line and provide ONLY the translation, preserving all formatting:\n\n"
        
        for unit in units:
            prompt += f"{unit.original_text}\n"
        
        return prompt
    
    def _create_extraction_prompt(self, text: str, context: Optional[str] = None) -> str:
        """Create prompt for term extraction"""
        
        prompt = """Analyze the following text and identify important terms that should be consistently translated across a video game localization.

Look for:
- Character names (e.g., "Hornet", "Lace")
- Location names (e.g., "Pharloom", "Citadel") 
- Item names (e.g., "Hunter's Memento", "Silk Spool")
- Skill/ability names (e.g., "Needle Slash", "Thread Bind")
- Unique game terminology (e.g., "Weaver", "Fragment")
- Proper nouns that are part of the game world

Do NOT include:
- Common words (the, and, is, with, to, etc.)
- Generic gaming terms (health, damage, level, points, etc.)
- Basic English words or phrases
- UI text (OK, Cancel, Menu, etc.)
- Numbers or simple adjectives (big, small, red, etc.)

IMPORTANT: 
- If the text contains only common phrases or UI elements with NO game-specific terms, return []
- Only extract terms that are unique to this game world and need consistent translation
- Be selective - better to miss a term than include common words

"""
        
        if context:
            prompt += f"Context: {context}\n\n"
        
        prompt += f"Text to analyze:\n{text}\n\n"
        prompt += "Respond with a JSON object containing a 'terms' array, like: {\"terms\": [\"Term1\", \"Term2\", \"Term3\"]} or {\"terms\": []} if no terms found."
        
        return prompt
    
    def _create_glossary_prompt(self, terms: List[str], 
                              source_lang: str, target_lang: str) -> str:
        """Create prompt for glossary translation"""
        
        prompt = f"""Translate these video game terms from {source_lang} to Ukrainian language (українська мова).
Provide natural Ukrainian translations that would fit in a fantasy/adventure game setting.
Use proper Ukrainian grammar and terminology.

Terms to translate:
"""
        
        for term in terms:
            prompt += f"- {term}\n"
        
        prompt += f"""
Respond with a JSON object containing a 'translations' field with the translations, like:
{{
    "translations": {{
        "{terms[0] if terms else 'Example'}": "Translation1",
        "{terms[1] if len(terms) > 1 else 'Example2'}": "Translation2"
    }}
}}"""
        
        return prompt