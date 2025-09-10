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
SOURCE_DIR = "../SILKSONG_EN/._Decrypted"  # Папка з оригінальними файлами
OUTPUT_DIR = "../SILKSONG_UA"  # Папка для перекладених файлів
BATCH_SIZE = 10  # Кількість рядків для перекладу за раз (збільшено для економії)

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
        self.stats = {"translated": 0, "cached": 0, "errors": 0, "tokens_used": 0, "api_calls": 0}
        self.load_cache()

    def create_batch_prompt(self, texts: List[str]) -> str:
        """Створює промпт для батч-перекладу"""
        glossary_str = "\n".join([f"- {en}: {ua}" for en, ua in GLOSSARY.items()])
        preserve_str = ", ".join(PRESERVE_TERMS)

        prompt = f"""You are translating the game "Hollow Knight: Silksong" from English to Ukrainian.

CRITICAL RULES:
1. Preserve ALL tags, formatting, special characters (\\n, <tag>, {{variable}}, etc.)
2. Keep dark fantasy atmosphere and poetic style
3. Do NOT translate these names: {preserve_str}
4. Use this glossary: 
{glossary_str}

Translate each text below and return ONLY a JSON object with translations.
Format: {{"1": "translation1", "2": "translation2", ...}}

TEXTS TO TRANSLATE:
"""

        for i, text in enumerate(texts, 1):
            # Екрануємо текст для JSON
            escaped_text = text.replace('"', '\\"').replace('\n', '\\n')
            prompt += f'{i}. "{escaped_text}"\n'

        prompt += "\nReturn ONLY the JSON object with Ukrainian translations:"

        return prompt

    def translate_batch(self, texts: List[str]) -> List[str]:
        """Перекладає батч текстів одним API викликом"""
        if not texts:
            return []

        # Фільтруємо тексти що потребують перекладу
        texts_to_translate = []
        results = []
        indices_to_translate = []

        for i, text in enumerate(texts):
            # Пропускаємо пусті або технічні рядки
            if not text or text.startswith('$') or len(text) <= 2:
                results.append(text)
            elif text in self.translation_cache:
                results.append(self.translation_cache[text])
                self.stats["cached"] += 1
            else:
                texts_to_translate.append(text)
                results.append(None)  # Placeholder
                indices_to_translate.append(i)

        # Якщо всі з кешу або не потребують перекладу
        if not texts_to_translate:
            return results

        # Перекладаємо батч
        for attempt in range(MAX_RETRIES):
            try:
                print(f"    Translating batch of {len(texts_to_translate)} texts...")

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional game translator. Return ONLY a JSON object with translations, no explanations."
                        },
                        {
                            "role": "user",
                            "content": self.create_batch_prompt(texts_to_translate)
                        }
                    ],
                    temperature=TEMPERATURE,
                    max_completion_tokens=30000,
                    response_format={"type": "json_object"}  # Форсуємо JSON відповідь
                )

                self.stats["api_calls"] += 1

                # Оновлюємо статистику токенів
                if hasattr(response, 'usage'):
                    self.stats["tokens_used"] += response.usage.total_tokens

                # Парсимо JSON відповідь
                content = response.choices[0].message.content.strip()

                # Видаляємо можливі markdown блоки
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]

                translations_dict = json.loads(content)

                # Заповнюємо результати та кеш
                for i, (idx, text) in enumerate(zip(indices_to_translate, texts_to_translate), 1):
                    translation = translations_dict.get(str(i), f"[ERROR] {text}")
                    results[idx] = translation
                    self.translation_cache[text] = translation
                    self.stats["translated"] += 1

                return results

            except json.JSONDecodeError as e:
                print(f"    JSON parsing error: {e}")
                # Fallback - пробуємо витягнути переклади з тексту
                try:
                    content = response.choices[0].message.content
                    # Простий парсинг якщо JSON зламаний
                    for i, (idx, text) in enumerate(zip(indices_to_translate, texts_to_translate), 1):
                        # Шукаємо паттерн "1": "переклад"
                        pattern = f'"{i}"\\s*:\\s*"([^"]*)"'
                        match = re.search(pattern, content)
                        if match:
                            translation = match.group(1)
                            results[idx] = translation
                            self.translation_cache[text] = translation
                            self.stats["translated"] += 1
                        else:
                            results[idx] = f"[PARSE ERROR] {text}"
                    return results
                except:
                    pass

            except Exception as e:
                print(f"    API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

                if "rate_limit" in str(e).lower():
                    print(f"    Rate limit hit, waiting {RETRY_DELAY * 2} seconds...")
                    time.sleep(RETRY_DELAY * 2)

                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        # Якщо всі спроби невдалі - перекладаємо по одному (fallback)
        print("    Batch translation failed, falling back to individual translations...")
        for idx, text in zip(indices_to_translate, texts_to_translate):
            results[idx] = self.translate_single(text)

        return results

    def translate_single(self, text: str) -> str:
        """Fallback метод для перекладу одного тексту"""
        if text in self.translation_cache:
            self.stats["cached"] += 1
            return self.translation_cache[text]

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Translate from English to Ukrainian. Keep all tags and formatting."
                    },
                    {
                        "role": "user",
                        "content": f"Translate: {text}"
                    }
                ],
                temperature=TEMPERATURE,
                max_completion_tokens=500
            )

            self.stats["api_calls"] += 1
            translation = response.choices[0].message.content.strip()

            self.translation_cache[text] = translation
            self.stats["translated"] += 1

            return translation

        except Exception as e:
            self.stats["errors"] += 1
            return f"[ERROR] {text}"

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
        """Обробляє один файл локалізації БАТЧАМИ"""
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

        # Перекладаємо БАТЧАМИ
        translated_content = content
        total_batches = (len(entries) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(0, len(entries), BATCH_SIZE):
            batch = entries[batch_num:batch_num + BATCH_SIZE]
            current_batch = batch_num // BATCH_SIZE + 1

            print(f"  Processing batch {current_batch}/{total_batches} ({len(batch)} entries)")

            # Витягуємо тексти для батчу
            batch_texts = [text for name, text in batch]

            # Перекладаємо весь батч одним викликом
            translations = self.translate_batch(batch_texts)

            # Замінюємо в контенті
            for (name, original), translated in zip(batch, translations):
                old_entry = f'<entry name="{name}">{original}</entry>'
                new_entry = f'<entry name="{name}">{translated}</entry>'
                translated_content = translated_content.replace(old_entry, new_entry)

            # Зберігаємо кеш після кожного батчу
            if batch_num % (BATCH_SIZE * 5) == 0:
                self.save_cache()

            # Невелика затримка між батчами
            time.sleep(0.5)

        # Зберігаємо файл
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        print(f"  ✅ Saved to: {output_path}")
        self.save_cache()

    def process_all_files(self):
        """Обробляє всі файли"""
        source_path = Path(SOURCE_DIR)
        output_path = Path(OUTPUT_DIR)

        # Знаходимо файли
        files = list(source_path.glob("EN_*.txt")) + list(source_path.glob("EN_*.xml"))

        if not files:
            print("❌ No files found! Make sure SILKSONG_EN/._Decrypted folder contains decrypted files")
            return

        print(f"🎮 SILKSONG UKRAINIAN TRANSLATION (BATCH MODE)")
        print(f"📁 Found {len(files)} files to translate")
        print(f"📦 Batch size: {BATCH_SIZE} entries per API call")
        print(f"🤖 Using model: {MODEL_NAME}")
        print(f"🔑 API: OpenAI\n")

        # Оцінка вартості з урахуванням батчів
        estimated_cost = self.estimate_cost_with_batches(files)
        print(f"💰 Estimated cost with batching: ${estimated_cost:.2f} (approximate)")

        response = input("\n⚠️  Continue with translation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Translation cancelled.")
            return

        # Обробляємо файли
        start_time = time.time()

        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}]", end="")
            relative_path = file_path.relative_to(source_path)
            output_file = output_path / relative_path

            self.process_file(str(file_path), str(output_file))

        # Фінальна статистика
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 50}")
        print(f"✅ TRANSLATION COMPLETED in {elapsed_time / 60:.1f} minutes!")
        print(f"📊 Statistics:")
        print(f"  - Translated: {self.stats['translated']} strings")
        print(f"  - From cache: {self.stats['cached']} strings")
        print(f"  - Errors: {self.stats['errors']} strings")
        print(
            f"  - API calls: {self.stats['api_calls']} (saved {self.stats['translated'] - self.stats['api_calls']} calls with batching!)")
        print(f"  - Tokens used: {self.stats['tokens_used']:,}")

        # Розрахунок вартості
        if "gpt-4" in MODEL_NAME.lower():
            cost = (self.stats['tokens_used'] / 1000) * 0.01
        else:
            cost = (self.stats['tokens_used'] / 1000) * 0.0015

        print(f"💵 Actual cost: ${cost:.2f}")
        print(f"📁 Output folder: {OUTPUT_DIR}")
        print(f"💾 Cache saved to: translation_cache.json")

    def estimate_cost_with_batches(self, files):
        """Оцінює вартість з урахуванням батчів"""
        total_entries = 0
        for file_path in files[:3]:
            entries = self.extract_entries(str(file_path))
            total_entries += len(entries)

        # Екстраполюємо
        avg_per_file = total_entries / min(3, len(files))
        total_estimated_entries = avg_per_file * len(files)

        # Кількість API викликів з батчами
        estimated_api_calls = total_estimated_entries / BATCH_SIZE

        # Приблизно 50 токенів на entry (prompt + response)
        estimated_tokens = total_estimated_entries * 50

        if "gpt-4" in MODEL_NAME.lower():
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
                {"role": "user", "content": "Translate to Ukrainian: Hello. Return only translation."}
            ],
            max_completion_tokens=50
        )

        result = response.choices[0].message.content
        print(f"✅ Connection successful!")
        print(f"   Test response: {result}")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🎮 HOLLOW KNIGHT: SILKSONG - Ukrainian Translation Tool (Batch Mode)")
    print("=" * 50)

    # Перевірка API ключа
    if not OPENAI_API_KEY:
        print("❌ Please set your OpenAI API key in .env file!")
        exit(1)

    # Тестуємо з'єднання
    if not test_connection():
        print("\n⚠️  Please check:")
        print("1. Your OpenAI API key is valid")
        print("2. You have credits in your OpenAI account")
        print("3. The model name is correct")
        exit(1)

    print("\n" + "=" * 50)

    # Запускаємо переклад
    translator = SilksongOpenAITranslator()
    translator.process_all_files()

    print("\n🎉 Done! Now you can:")
    print("1. Check translations in SILKSONG_UA folder")
    print("2. Use 'SilksongDecryptor.exe -encrypt SILKSONG_UA' to encrypt back")
    print("3. Replace original files in the game")