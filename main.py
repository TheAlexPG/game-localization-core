import os
import re
import time
import json
import requests
from pathlib import Path
from typing import List, Dict, Tuple

# ===== НАЛАШТУВАННЯ =====
SOURCE_DIR = "./SILKSONG_EN/._Decrypted"  # Папка з оригінальними файлами
OUTPUT_DIR = "./SILKSONG_UA"  # Папка для перекладених файлів
BATCH_SIZE = 5  # Кількість рядків для перекладу за раз (менше для кращої якості)
API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "openai-gpt-oss-20b-temp"
TEMPERATURE = 0.3  # Низька для консистентності перекладу
MAX_RETRIES = 3
RETRY_DELAY = 2

# Глосарій термінів що не перекладаємо
PRESERVE_TERMS = [
    "Hornet", "Pharloom", "Silksong", "Citadel",
    "Garmond", "Lace", "Shakra", "Coral"
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
    "Fragment": "Фрагмент"
}


class SilksongLMStudioTranslator:
    def __init__(self):
        self.translation_cache = {}
        self.stats = {"translated": 0, "cached": 0, "errors": 0}
        self.load_cache()

    def create_prompt(self, text: str) -> str:
        """Створює промпт для перекладу"""
        glossary_str = "\n".join([f"- {en}: {ua}" for en, ua in GLOSSARY.items()])
        preserve_str = ", ".join(PRESERVE_TERMS)

        prompt = f"""You are translating a dark fantasy game "Hollow Knight: Silksong" to Ukrainian.

IMPORTANT RULES:
1. Preserve the poetic and atmospheric style
2. Keep these names unchanged: {preserve_str}
3. Use this glossary for consistency:
{glossary_str}
4. Maintain gender-neutral forms where possible
5. Keep any special characters like &lt;, &gt;, &#8217;

TEXT TO TRANSLATE:
{text}

UKRAINIAN TRANSLATION:"""

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
                                "content": "You are a professional Ukrainian game translator. Translate accurately while preserving the dark fantasy atmosphere."
                            },
                            {
                                "role": "user",
                                "content": self.create_prompt(text)
                            }
                        ],
                        "temperature": TEMPERATURE,
                        "max_tokens": 500,
                        "stream": False
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    translation = result['choices'][0]['message']['content'].strip()

                    # Очищаємо відповідь від можливих пояснень
                    if ":" in translation[:50]:  # Якщо є заголовок типу "Translation:"
                        translation = translation.split(":", 1)[1].strip()

                    return translation
                else:
                    print(f"Error {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            except Exception as e:
                print(f"Unexpected error: {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        self.stats["errors"] += 1
        return f"[TRANSLATION ERROR] {text}"

    def translate_text(self, text: str) -> str:
        """Перекладає текст з кешуванням"""
        # Пропускаємо технічні рядки
        if not text or text.startswith('$') or len(text) <= 2:
            return text

        # Перевіряємо кеш
        if text in self.translation_cache:
            self.stats["cached"] += 1
            return self.translation_cache[text]

        # Перекладаємо
        print(f"  Translating: {text[:50]}...")
        translation = self.call_lm_studio(text)

        # Зберігаємо в кеш
        self.translation_cache[text] = translation
        self.stats["translated"] += 1

        # Невелика затримка щоб не перевантажити модель
        time.sleep(0.5)

        return translation

    def extract_entries(self, file_path: str) -> List[Tuple[str, str]]:
        """Витягує всі entry з файлу"""
        entries = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Шукаємо entry теги
            pattern = r'<entry name="([^"]+)">([^<]*)</entry>'
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

        # Витягуємо entries
        entries = self.extract_entries(input_path)

        if not entries:
            print("  No entries found, copying as is")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return

        print(f"  Found {len(entries)} entries")

        # Перекладаємо
        translated_content = content
        for i, (name, text) in enumerate(entries):
            if i % 10 == 0 and i > 0:
                print(f"  Progress: {i}/{len(entries)}")
                # Зберігаємо кеш кожні 10 записів
                self.save_cache()

            # Перекладаємо текст
            translated = self.translate_text(text)

            # Замінюємо в контенті
            old_entry = f'<entry name="{name}">{text}</entry>'
            new_entry = f'<entry name="{name}">{translated}</entry>'
            translated_content = translated_content.replace(old_entry, new_entry)

        # Зберігаємо файл
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        print(f"  ✅ Saved to: {output_path}")

    def process_all_files(self):
        """Обробляє всі файли"""
        source_path = Path(SOURCE_DIR)
        output_path = Path(OUTPUT_DIR)

        # Знаходимо файли
        files = list(source_path.glob("EN_*.txt")) + list(source_path.glob("EN_*.xml"))

        if not files:
            print("❌ No files found! Make sure SILKSONG_EN folder contains decrypted files")
            return

        print(f"🎮 SILKSONG UKRAINIAN TRANSLATION")
        print(f"📁 Found {len(files)} files to translate")
        print(f"🤖 Using model: {MODEL_NAME}")
        print(f"🌐 API: {API_URL}\n")

        # Перевіряємо з'єднання з LM Studio
        try:
            test_response = requests.get("http://localhost:1234/v1/models", timeout=5)
            if test_response.status_code != 200:
                print("❌ Cannot connect to LM Studio! Make sure it's running on port 1234")
                return
        except:
            print("❌ LM Studio is not running! Start it first and load the model")
            return

        # Обробляємо файли
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end="")
            relative_path = file_path.relative_to(source_path)
            output_file = output_path / relative_path

            self.process_file(str(file_path), str(output_file))

            # Зберігаємо прогрес
            self.save_cache()

        # Фінальна статистика
        print(f"\n{'=' * 50}")
        print(f"✅ TRANSLATION COMPLETED!")
        print(f"📊 Statistics:")
        print(f"  - Translated: {self.stats['translated']} strings")
        print(f"  - From cache: {self.stats['cached']} strings")
        print(f"  - Errors: {self.stats['errors']} strings")
        print(f"📁 Output folder: {OUTPUT_DIR}")
        print(f"💾 Cache saved to: translation_cache.json")

    def save_cache(self):
        """Зберігає кеш перекладів"""
        with open("translation_cache.json", 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        """Завантажує кеш перекладів"""
        try:
            with open("translation_cache.json", 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
                print(f"📚 Loaded {len(self.translation_cache)} cached translations")
        except FileNotFoundError:
            print("📚 Starting with empty translation cache")


def test_connection():
    """Тестує з'єднання з LM Studio"""
    print("🔍 Testing LM Studio connection...")

    try:
        response = requests.post(
            API_URL,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": "Translate to Ukrainian: Hello"}
                ],
                "temperature": 0.1,
                "max_tokens": 10,
                "stream": False
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Connection successful!")
            print(f"   Test response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🎮 HOLLOW KNIGHT: SILKSONG - Ukrainian Translation Tool")
    print("=" * 50)

    # Тестуємо з'єднання
    if not test_connection():
        print("\n⚠️  Please make sure:")
        print("1. LM Studio is running")
        print("2. Model 'openai-gpt-oss-20b-temp' is loaded")
        print("3. Server is running on port 1234")
        exit(1)

    print("\n" + "=" * 50)

    # Запускаємо переклад
    translator = SilksongLMStudioTranslator()
    translator.process_all_files()

    print("\n🎉 Done! Now you can:")
    print("1. Check translations in SILKSONG_UA folder")
    print("2. Use 'SilksongDecryptor.exe -encrypt SILKSONG_UA' to encrypt back")
    print("3. Replace original files in the game")