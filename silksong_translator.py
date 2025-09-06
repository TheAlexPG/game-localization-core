import os
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ===== НАЛАШТУВАННЯ =====
SOURCE_DIR = "./SILKSONG_EN/._Decrypted"  # Папка з оригінальними файлами
OUTPUT_DIR = "./SILKSONG_UA"  # Папка для перекладених файлів
BATCH_SIZE = 5  # Кількість рядків для перекладу за раз

# OpenAI налаштування
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5"  # або "gpt-3.5-turbo" для дешевшого варіанту
TEMPERATURE = 1  # Низька для консистентності перекладу
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


class SilksongOpenAITranslator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.translation_cache = {}
        self.stats = {"translated": 0, "cached": 0, "errors": 0, "tokens_used": 0}
        self.load_cache()

    def create_prompt(self, text: str) -> str:
        """Створює промпт для перекладу з урахуванням тегів та форматування"""
        glossary_str = "\n".join([f"- {en}: {ua}" for en, ua in GLOSSARY.items()])
        preserve_str = ", ".join(PRESERVE_TERMS)

        prompt = f"""You are an expert translator for the dark fantasy game "Hollow Knight: Silksong", translating from English to Ukrainian. Provide ONLY the Ukrainian translation of the text.

### CRITICAL RULES ###
1.  **Preserve ALL Tags and Formatting:** All special characters, line breaks (\\n), and tags like `<tag>`, `<|token|>` or `{{variable}}` MUST be preserved exactly as they are in the original text. DO NOT translate, change, or remove them.
2.  **Atmospheric Style:** Maintain the poetic, dark, and sometimes archaic style of the original game.
3.  **Glossary Adherence:** Strictly use the provided glossary for consistency.
{glossary_str}
4.  **Do Not Translate Names:** The following names must remain in English: {preserve_str}.

### EXAMPLE OF PRESERVING TAGS AND NEWLINES ###
- **Original Text:**
"Ah, <|hero_name|>. Your journey is long.\\nUse the {{item_bell}} to call for aid."
- **Correct Ukrainian Translation:**
"Ах, <|hero_name|>. Твоя подорож довга.\\nВикористай {{item_bell}}, щоб покликати на допомогу."

### TEXT TO TRANSLATE ###
{text}

### UKRAINIAN TRANSLATION ###"""

        return prompt

    def call_openai(self, text: str) -> str:
        """Викликає OpenAI API для перекладу"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional Ukrainian game translator specializing in dark fantasy games. Translate accurately while preserving the atmospheric style and all formatting/tags."
                        },
                        {
                            "role": "user",
                            "content": self.create_prompt(text)
                        }
                    ],
                    temperature=TEMPERATURE,
                    max_completion_tokens=30000
                )

                translation = response.choices[0].message.content.strip()

                # Оновлюємо статистику токенів
                if hasattr(response, 'usage'):
                    self.stats["tokens_used"] += response.usage.total_tokens

                # Очищаємо відповідь від можливих пояснень
                if ":" in translation[:50]:  # Якщо є заголовок типу "Translation:"
                    translation = translation.split(":", 1)[1].strip()

                return translation

            except Exception as e:
                print(f"  API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

                if "rate_limit" in str(e).lower():
                    print(f"  Rate limit hit, waiting {RETRY_DELAY * 2} seconds...")
                    time.sleep(RETRY_DELAY * 2)
                elif "api_key" in str(e).lower():
                    print("❌ Invalid API key! Please check your OpenAI API key.")
                    exit(1)

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
        translation = self.call_openai(text)

        # Зберігаємо в кеш
        self.translation_cache[text] = translation
        self.stats["translated"] += 1

        # Невелика затримка щоб не перевантажити API
        time.sleep(0.2)

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
            print("❌ No files found! Make sure SILKSONG_EN/._Decrypted folder contains decrypted files")
            return

        print(f"🎮 SILKSONG UKRAINIAN TRANSLATION")
        print(f"📁 Found {len(files)} files to translate")
        print(f"🤖 Using model: {MODEL_NAME}")
        print(f"🔑 API: OpenAI\n")

        # Оцінка вартості
        estimated_cost = self.estimate_cost(files)
        print(f"💰 Estimated cost: ${estimated_cost:.2f} (approximate)")

        response = input("\n⚠️  Continue with translation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Translation cancelled.")
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
        print(f"  - Tokens used: {self.stats['tokens_used']:,}")

        # Розрахунок вартості
        if MODEL_NAME == "gpt-4-turbo-preview":
            cost = (self.stats['tokens_used'] / 1000) * 0.01  # $0.01 per 1K tokens (approximate)
        else:  # gpt-3.5-turbo
            cost = (self.stats['tokens_used'] / 1000) * 0.0015  # $0.0015 per 1K tokens

        print(f"💵 Approximate cost: ${cost:.2f}")
        print(f"📁 Output folder: {OUTPUT_DIR}")
        print(f"💾 Cache saved to: translation_cache.json")

    def estimate_cost(self, files):
        """Оцінює приблизну вартість перекладу"""
        total_chars = 0
        for file_path in files[:3]:  # Беремо перші 3 файли для оцінки
            entries = self.extract_entries(str(file_path))
            for _, text in entries:
                total_chars += len(text)

        # Екстраполюємо на всі файли
        avg_per_file = total_chars / min(3, len(files))
        total_estimated = avg_per_file * len(files)

        # Приблизно 4 символи = 1 токен
        estimated_tokens = (total_estimated / 4) * 2  # x2 для запиту і відповіді

        if MODEL_NAME == "gpt-4-turbo-preview":
            return (estimated_tokens / 1000) * 0.01
        else:
            return (estimated_tokens / 1000) * 0.0015

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
    """Тестує з'єднання з OpenAI API"""
    print("🔍 Testing OpenAI API connection...")

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": "Say 'Hello' in Ukrainian"}
            ]
        )

        result = response.choices[0].message.content
        print(f"✅ Connection successful!")
        print(f"   Test response: {result}")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🎮 HOLLOW KNIGHT: SILKSONG - Ukrainian Translation Tool (OpenAI)")
    print("=" * 50)

    # Перевірка API ключа
    if OPENAI_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ Please set your OpenAI API key in the script!")
        print("   Edit the OPENAI_API_KEY variable")
        exit(1)

    # Тестуємо з'єднання
    if not test_connection():
        print("\n⚠️  Please check:")
        print("1. Your OpenAI API key is valid")
        print("2. You have credits in your OpenAI account")
        print("3. The model name is correct (gpt-4-turbo-preview or gpt-3.5-turbo)")
        exit(1)

    print("\n" + "=" * 50)

    # Запускаємо переклад
    translator = SilksongOpenAITranslator()
    translator.process_all_files()

    print("\n🎉 Done! Now you can:")
    print("1. Check translations in SILKSONG_UA folder")
    print("2. Use 'SilksongDecryptor.exe -encrypt SILKSONG_UA' to encrypt back")
    print("3. Replace original files in the game")