import os
import re
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Tuple

# ===== НАЛАШТУВАННЯ =====
# <<< ЗМІНЕНО: Вказано RU як вихідну мову
SOURCE_DIR = "./SILKSONG_RU/._Decrypted"  # Папка з оригінальними файлами (російськими)
OUTPUT_DIR = "./SILKSONG_UA"  # Папка для перекладених файлів
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "openai-gpt-oss-20b-temp"
TEMPERATURE = 0.3  # Низька для консистентності перекладу
MAX_RETRIES = 3
RETRY_DELAY = 2

# Глосарій термінів що не перекладаємо
PRESERVE_TERMS = [
    "Hornet", "Pharloom", "Silksong", "Citadel",
    "Garmond", "Lace", "Shakra", "Coral", "Ярнаби"  # Додав ім'я з прикладу
]

# Глосарій для консистентного перекладу
GLOSSARY = {
    "Weaver": "Ткач",
    "Needle": "Голка",
    "Thread": "Нитка",
    "Silk": "Шовк",
    "Hunter": "Мисливець",
    "Knight": "Лицар",
    "Crest": "Герб",
    "Wilds": "Пустка",
    "Forge": "Кузня",
    "Peak": "Пік",
    "Void": "Порожнеча",
    "Soul": "Душа",
    "Mask": "Маска",
    "Charm": "Оберіг",
    "Spool": "Котушка",
    "Fragment": "Фрагмент",
    "Up": "Вгору",
    "No": "Ні",
    "Yes": "Так",
    "Down": "Вниз"
}


class SilksongLMStudioTranslator:
    def __init__(self):
        self.translation_cache = {}
        self.stats = {"translated": 0, "cached": 0, "errors": 0, "retried": 0}
        self.load_cache()

    def create_prompt(self, text: str) -> str:
        """ <<< ЗМІНЕНО: Промпт значно посилено для збереження тегів """
        glossary_str = "\n".join([f"- {en}: {ua}" for en, ua in GLOSSARY.items()])
        preserve_str = ", ".join(PRESERVE_TERMS)

        prompt = f"""You are a meticulous game localizer translating "Hollow Knight: Silksong" from Russian to Ukrainian. Your primary goal is to preserve the original game's technical tags and formatting exactly.

### CRITICAL RULES ###
1.  **Strict Tag Preservation**: The text contains special tags like `<page>`, `<hpage>`, `&lt;page&gt;`, `&#8220;`, etc. You MUST copy these tags to the output **EXACTLY** as they appear in the original text, without any changes, translations, or reformatting.
2.  **Translate ONLY the Text**: Translate only the human-readable text between the tags.
3.  **Atmospheric Style**: Maintain the poetic and dark fantasy style.
4.  **Glossary & Names**: Strictly use this glossary:
{glossary_str}
    And do not translate these names: {preserve_str}.

### EXAMPLE ###
- **Original Text**:
Так-так! Что это у нас тут? Заражение, бз-з-з?&lt;page&gt;Ты хотя бы знаешь, кто я?
- **Correct Ukrainian Translation**:
Так-так! Що це в нас тут? Зараження, бз-з-з?&lt;page&gt;Ти хоча б знаєш, хто я?

### RUSSIAN TEXT TO TRANSLATE ###
{text}

### UKRAINIAN TRANSLATION ###
"""
        return prompt

    def call_lm_studio(self, text: str) -> str:
        """Викликає LM Studio API для перекладу"""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "model": MODEL_NAME,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional Ukrainian game translator. Follow the user's instructions for tag preservation precisely."
                            },
                            {
                                "role": "user",
                                "content": self.create_prompt(text)
                            }
                        ],
                        "temperature": TEMPERATURE,
                        "max_tokens": 1024,  # Збільшено, щоб уникнути обрізки довгих рядків
                        "stream": False
                    },
                    timeout=45  # Збільшено час очікування
                )

                if response.status_code == 200:
                    result = response.json()
                    translation = result['choices'][0]['message']['content'].strip()

                    # <<< ЗМІНЕНО: Перевірка на порожню відповідь
                    if not translation:
                        print(
                            f"  ⚠️ Warning: Received empty response. Retrying... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        self.stats["retried"] += 1
                        time.sleep(RETRY_DELAY)
                        continue  # Переходимо до наступної спроби

                    # Очищення відповіді від можливих пояснень
                    if "### UKRAINIAN TRANSLATION ###" in translation:
                        translation = translation.split("### UKRAINIAN TRANSLATION ###")[-1].strip()

                    return translation
                else:
                    print(f"  ❌ Error {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"  🔗 Connection error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            except Exception as e:
                print(f"  💥 Unexpected error: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        self.stats["errors"] += 1
        return f"[TRANSLATION ERROR] {text}"

    def translate_text(self, text: str) -> str:
        """Перекладає текст з кешуванням"""
        # <<< ЗМІНЕНО: Обробка коротких рядків, які не є технічними
        if not text or text.startswith('$'):
            return text

        # Пропускаємо рядки, що складаються лише з цифр або спецсимволів, але перекладаємо короткі слова
        if not re.search(r'[a-zA-Zа-яА-Я]', text) and len(text) < 10:
            if not any(word in text for word in GLOSSARY.keys()):
                return text

        # Перевіряємо кеш
        if text in self.translation_cache:
            self.stats["cached"] += 1
            return self.translation_cache[text]

        # Перекладаємо
        print(f"  Translating: {text[:60]}...")
        translation = self.call_lm_studio(text)

        # Зберігаємо в кеш
        self.translation_cache[text] = translation
        self.stats["translated"] += 1

        time.sleep(0.5)
        return translation

    def extract_entries(self, file_path: str) -> List[Tuple[str, str]]:
        """Витягує всі entry з файлу"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # <<< ЗМІНЕНО: Більш гнучкий патерн для пошуку тегів
            pattern = r'<entry name="([^"]+)">(.*?)</entry>'
            matches = re.findall(pattern, content, re.DOTALL)
            return matches
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

    def process_file(self, input_path: str, output_path: str):
        """Обробляє один файл локалізації"""
        print(f"\n📄 Processing: {Path(input_path).name}")

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        entries = self.extract_entries(input_path)
        if not entries:
            print("  No entries found, copying as is.")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return

        print(f"  Found {len(entries)} entries.")
        translated_content = content

        for i, (name, text) in enumerate(entries):
            # Використовуємо re.escape для безпечної заміни спеціальних символів у тексті
            escaped_text = re.escape(text)

            # Створюємо більш точний патерн для заміни, щоб уникнути помилок
            pattern_to_replace = re.compile(f'(<entry name="{re.escape(name)}">){escaped_text}(</entry>)')

            translated = self.translate_text(text)

            # Виконуємо заміну, зберігаючи оригінальні теги
            translated_content = pattern_to_replace.sub(f'\\1{translated}\\2', translated_content, count=1)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(entries)}")
                self.save_cache()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        print(f"  ✅ Saved to: {output_path}")

    def process_all_files(self):
        """Обробляє всі файли"""
        source_path = Path(SOURCE_DIR)
        output_path = Path(OUTPUT_DIR)

        # <<< ЗМІНЕНО: Шукаємо файли, що починаються з RU_
        files = list(source_path.glob("RU_*.txt")) + list(source_path.glob("RU_*.xml"))

        if not files:
            print("❌ No files found! Make sure SOURCE_DIR contains decrypted files starting with 'RU_'")
            return

        print(f"🎮 SILKSONG UKRAINIAN TRANSLATION (from RU)")
        print(f"📁 Found {len(files)} files to translate.")
        print(f"🤖 Using model: {MODEL_NAME}")
        print(f"🌐 API: {API_URL}\n")

        if not test_connection():
            return

        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end="")
            relative_path = file_path.relative_to(source_path)

            # <<< ЗМІНЕНО: Замінюємо RU_ на UA_ у назві вихідного файлу
            output_filename = file_path.name.replace("RU_", "UA_", 1)
            output_file = output_path / relative_path.with_name(output_filename)

            self.process_file(str(file_path), str(output_file))
            self.save_cache()

        print(f"\n{'=' * 50}")
        print(f"✅ TRANSLATION COMPLETED!")
        print(f"📊 Statistics:")
        print(f"  - Translated: {self.stats['translated']} strings")
        print(f"  - From cache: {self.stats['cached']} strings")
        print(f"  - Retried (empty): {self.stats['retried']} times")
        print(f"  - Errors: {self.stats['errors']} strings")
        print(f"📁 Output folder: {OUTPUT_DIR}")
        print(f"💾 Cache saved to: translation_cache.json")

    def save_cache(self):
        with open("translation_cache.json", 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        try:
            with open("translation_cache.json", 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
                print(f"📚 Loaded {len(self.translation_cache)} cached translations.")
        except FileNotFoundError:
            print("📚 Starting with empty translation cache.")


def test_connection():
    """Тестує з'єднання з LM Studio"""
    print("🔍 Testing LM Studio connection...")
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ Connection successful!")
            return True
        else:
            print("❌ Cannot connect to LM Studio! Make sure it's running on port 1234.")
            return False
    except requests.exceptions.RequestException:
        print("❌ LM Studio is not running! Start it first and load the model.")
        return False


if __name__ == "__main__":
    print("=" * 50)
    translator = SilksongLMStudioTranslator()
    translator.process_all_files()
    print("=" * 50)