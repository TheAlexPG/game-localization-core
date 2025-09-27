"""Centralized prompt management for all LLM providers"""

from typing import List, Dict, Optional


class PromptManager:
    """Manages all prompts for translation and glossary operations"""

    @staticmethod
    def get_translation_prompt(texts: List[str],
                              source_lang: str,
                              target_lang: str,
                              glossary: Optional[str] = None,
                              context: Optional[str] = None) -> str:
        """Create a standardized translation prompt

        Args:
            texts: List of texts to translate
            source_lang: Source language
            target_lang: Target language
            glossary: Optional formatted glossary string
            context: Optional context information

        Returns:
            Formatted prompt string
        """
        prompt = f"""Translate the following texts from {source_lang} to {target_lang}.
Keep the translation natural and contextually appropriate for a video game.

CRITICAL FORMATTING RULES:
- Preserve ALL XML-like tags exactly: &lt;page=S&gt;, &lt;hpage&gt;, etc.
- Keep ALL special characters and HTML entities as-is: &#8217;, &amp;, etc.
- Do NOT change any formatting, tags, or special symbols
- Only translate the actual text content, not the markup
- Keep placeholders like {{value}}, {{level}} exactly as they are
- PRESERVE THE ORIGINAL CASE (uppercase/lowercase) OF THE SOURCE TEXT

"""

        # Add project context if provided
        if context:
            prompt += f"{context}\n\n"

        # Add glossary if provided
        if glossary:
            prompt += f"{glossary}\n\n"

        prompt += "Translate each numbered line and provide ONLY the translation, preserving all formatting:\n\n"

        for i, text in enumerate(texts, 1):
            prompt += f"{i}. {text}\n"

        prompt += "\nRespond with only the translations, one per line, in the same order:"

        return prompt

    @staticmethod
    def get_term_extraction_prompt(text: str, context: Optional[str] = None) -> str:
        """Create prompt for extracting important terms from text

        Args:
            text: Text to analyze
            context: Optional context about the game/project

        Returns:
            Formatted prompt string
        """
        prompt = """Analyze this game text and extract important terms that should be consistently translated.

Look for:
- Character names, location names, item names
- Skill/ability names, unique game terminology
- Proper nouns specific to the game world

Do NOT include: common words, generic gaming terms, UI text, numbers

"""

        if context:
            prompt += f"{context}\n\n"
        else:
            prompt += "Context: Game localization\n\n"

        prompt += f"Text to analyze:\n{text}\n\n"
        prompt += "Return a JSON object with extracted terms."

        return prompt

    @staticmethod
    def get_glossary_translation_prompt(terms: List[str],
                                       source_lang: str,
                                       target_lang: str,
                                       context: Optional[str] = None) -> str:
        """Create prompt for translating glossary terms

        Args:
            terms: List of terms to translate
            source_lang: Source language
            target_lang: Target language
            context: Optional glossary context with translation rules

        Returns:
            Formatted prompt string
        """
        # Map language codes to full names for better AI understanding
        lang_mapping = {
            'uk': 'Ukrainian',
            'ru': 'Russian',
            'de': 'German',
            'fr': 'French',
            'es': 'Spanish',
            'it': 'Italian',
            'pl': 'Polish',
            'en': 'English'
        }

        source_lang_name = lang_mapping.get(source_lang, source_lang)
        target_lang_name = lang_mapping.get(target_lang, target_lang)

        prompt = f"""Translate these video game terms from {source_lang_name} to {target_lang_name}.
Provide natural {target_lang_name} translations that fit in a fantasy/adventure game setting.

"""

        # Add glossary context if provided
        if context:
            prompt += f"{context}\n\n"

        prompt += f"Terms: {', '.join(terms)}\n\n"
        prompt += "Return a JSON object with translations."

        return prompt

    @staticmethod
    def get_validation_test_prompt() -> str:
        """Get a simple prompt for connection validation"""
        return "Translate to Ukrainian: Hello"


class ResponseParser:
    """Parses responses from LLM models"""

    @staticmethod
    def parse_translation_response(response: str, expected_count: int) -> List[str]:
        """Parse translation response into list of translations

        Args:
            response: Raw response from LLM
            expected_count: Expected number of translations

        Returns:
            List of parsed translations
        """
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


class PromptSchemas:
    """JSON schemas for structured outputs"""

    @staticmethod
    def get_term_extraction_schema() -> Dict:
        """Schema for term extraction structured output"""
        return {
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

    @staticmethod
    def get_glossary_translation_schema() -> Dict:
        """Schema for glossary translation structured output"""
        return {
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