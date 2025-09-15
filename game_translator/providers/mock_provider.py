"""Mock provider for testing and demonstration"""

import time
import random
from typing import List, Dict, Optional

from .base import BaseTranslationProvider


class MockTranslationProvider(BaseTranslationProvider):
    """Mock provider that simulates translation for testing"""

    def __init__(self, model_name: str = "mock-translator", delay: float = 0.1, **kwargs):
        super().__init__(model_name, **kwargs)
        self.delay = delay
        self.call_count = 0

    def translate_texts(self, texts: List[str],
                       source_lang: str, target_lang: str,
                       glossary: Optional[Dict[str, str]] = None,
                       context: Optional[str] = None) -> List[str]:
        """Simulate translation with simple transformations"""
        self.call_count += 1

        # Simulate API delay
        time.sleep(self.delay)

        translations = []
        for text in texts:
            # Simple mock translation logic
            if source_lang.lower() == "en" and target_lang.lower() == "uk":
                translation = self._mock_en_to_uk(text, glossary)
            else:
                # Generic mock
                translation = f"[{target_lang.upper()}] {text}"

            translations.append(translation)

        return translations

    def _mock_en_to_uk(self, text: str, glossary: Optional[Dict[str, str]] = None) -> str:
        """Mock English to Ukrainian translation"""
        # Use glossary if available
        if glossary:
            for en_term, uk_term in glossary.items():
                if en_term.lower() in text.lower():
                    text = text.replace(en_term, uk_term)

        # Simple word replacements for demo
        replacements = {
            "Play Game": "Грати в гру",
            "Settings": "Налаштування",
            "Quit": "Вийти",
            "Health": "Здоров'я",
            "Menu": "Меню",
            "Start": "Почати",
            "Continue": "Продовжити",
            "Load": "Завантажити",
            "Save": "Зберегти",
            "Options": "Опції",
            "Controls": "Керування",
            "Audio": "Аудіо",
            "Video": "Відео",
            "Back": "Назад",
            "Accept": "Прийняти",
            "Cancel": "Скасувати",
            "Yes": "Так",
            "No": "Ні",
            "OK": "Гаразд"
        }

        result = text
        for en, uk in replacements.items():
            result = result.replace(en, uk)

        # If no replacements were made, add prefix to show it was "translated"
        if result == text and text.strip():
            result = f"[UA] {text}"

        return result

    def validate_connection(self) -> bool:
        """Mock provider is always available"""
        return True

    def get_info(self) -> Dict[str, str]:
        """Get mock provider information"""
        return {
            "name": "MockTranslationProvider",
            "model": self.model_name,
            "calls_made": str(self.call_count),
            "delay": f"{self.delay}s"
        }