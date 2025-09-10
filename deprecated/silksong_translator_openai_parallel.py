import os
import re
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ===== НАЛАШТУВАННЯ =====
SOURCE_DIR = "./SILKSONG_RU/._Decrypted"  # <<< ЗМІНЕНО: Папка з російськими файлами
OUTPUT_DIR = "../SILKSONG_UA"  # Папка для перекладених файлів
BATCH_SIZE = 10  # Кількість рядків для перекладу за раз
MAX_PARALLEL_FILES = 5  # Кількість файлів що обробляються паралельно

# OpenAI налаштування
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5"  # <<< ЗМІНЕНО: Використовуємо актуальну та потужну модель
TEMPERATURE = 1  # <<< ЗМІНЕНО: Знижено для більшої точності та консистентності
MAX_RETRIES = 3
RETRY_DELAY = 5  # Збільшено для публічного API

# Глосарій термінів що не перекладаємо
PRESERVE_TERMS = [
    "Hornet", "Pharloom", "Silksong", "Citadel",
    "Garmond", "Lace", "Shakra", "Coral"
]

# Глосарій для консистентного перекладу
GLOSSARY = {
    "Weaver": "Ткач", "Weavers": "Ткачі",
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
        self.cache_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.load_cache()

    def update_stats(self, **kwargs):
        with self.stats_lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    self.stats[key] += value

    def get_from_cache(self, text: str):
        with self.cache_lock:
            return self.translation_cache.get(text)

    def add_to_cache(self, text: str, translation: str):
        with self.cache_lock:
            self.translation_cache[text] = translation

    def create_batch_prompt(self, texts: List[str]) -> str:
        # <<< ЗМІНЕНО: Промпт значно покращено для точності та збереження тегів
        glossary_str = "\n".join([f"- '{en}': '{ua}'" for en, ua in GLOSSARY.items()])
        preserve_str = ", ".join(PRESERVE_TERMS)

        prompt = f"""You are a meticulous game localizer translating "Hollow Knight: Silksong" from Russian to Ukrainian. Your task is to translate a batch of texts and return a single JSON object.

### CRITICAL INSTRUCTIONS ###
1.  **Translate from Russian to Ukrainian**: The source language is Russian.
2.  **Strict Tag Preservation**: The text contains special tags like `<page>`, `<hpage>`, `&lt;...&gt;`, `{{...}}`, `\\n`. You MUST copy these tags to the output **EXACTLY** as they appear in the original, without any changes.
3.  **Adhere to Glossary**: Strictly use the provided glossary for consistency.
    {glossary_str}
4.  **Do Not Translate Names**: Keep these names in English: {preserve_str}.
5.  **Maintain Style**: Preserve the dark, poetic, and atmospheric style of the original.
6.  **JSON Output**: Return ONLY a valid JSON object mapping the original index to the Ukrainian translation. Do not add any explanations or markdown.

### EXAMPLE ###
- **Input Texts**:
1. "Так-так! Что это у нас тут?&lt;page&gt;Заражение?"
2. "Используй свой Crest"
- **Correct JSON Output**:
{{"1": "Так-так! Що це в нас тут?&lt;page&gt;Зараження?", "2": "Використай свій Герб"}}

### TEXTS TO TRANSLATE (RUSSIAN) ###
"""
        for i, text in enumerate(texts, 1):
            prompt += f'{i}. "{text}"\n'

        return prompt

    def translate_batch(self, texts: List[str], file_name: str = "") -> List[str]:
        if not texts:
            return []

        texts_to_translate = []
        results = [None] * len(texts)
        indices_to_translate = []

        for i, text in enumerate(texts):
            if not text or text.startswith('$') or not re.search(r'[a-zA-Zа-яА-Я]', text):
                results[i] = text
            else:
                cached = self.get_from_cache(text)
                if cached:
                    results[i] = cached
                    self.update_stats(cached=1)
                else:
                    texts_to_translate.append(text)
                    indices_to_translate.append(i)

        if not texts_to_translate:
            return [res for res in results if res is not None]

        for attempt in range(MAX_RETRIES):
            try:
                thread_id = threading.current_thread().name
                print(f"    [{thread_id}] {file_name}: Translating batch of {len(texts_to_translate)} texts...")

                response = self.client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a highly precise translation engine. You will receive a list of Russian texts and must return a single, valid JSON object with their Ukrainian translations, preserving all technical tags perfectly."
                        },
                        {
                            "role": "user",
                            "content": self.create_batch_prompt(texts_to_translate)
                        }
                    ],
                    temperature=TEMPERATURE,
                    max_completion_tokens=16000,  # Максимум для багатьох моделей
                    response_format={"type": "json_object"}
                )

                self.update_stats(api_calls=1, tokens_used=response.usage.total_tokens if response.usage else 0)

                translations_dict = json.loads(response.choices[0].message.content.strip())

                for i, (original_idx, text) in enumerate(zip(indices_to_translate, texts_to_translate), 1):
                    translation = translations_dict.get(str(i), f"[ERROR] {text}")
                    results[original_idx] = translation
                    self.add_to_cache(text, translation)
                    self.update_stats(translated=1)

                return [res for res in results if res is not None]

            except Exception as e:
                print(f"    [{thread_id}] API error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if "rate_limit" in str(e).lower():
                    time.sleep(RETRY_DELAY * (attempt + 1))
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)

        for original_idx, text in zip(indices_to_translate, texts_to_translate):
            results[original_idx] = f"[ERROR] {text}"
            self.update_stats(errors=1)

        return [res for res in results if res is not None]

    def extract_entries(self, file_path: str) -> List[Tuple[str, str]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            pattern = r'<entry name="([^"]+)">(.*?)</entry>'
            return re.findall(pattern, content, re.DOTALL)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

    def process_file(self, input_path: str, output_path: str, file_index: int, total_files: int):
        file_name = Path(input_path).name
        thread_id = threading.current_thread().name
        print(f"\n[{file_index}/{total_files}] 📄 {thread_id} Processing: {file_name}")

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        entries = self.extract_entries(input_path)
        if not entries:
            print(f"  [{thread_id}] No entries found in {file_name}, copying.")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        print(f"  [{thread_id}] Found {len(entries)} entries in {file_name}")

        original_texts = [text for name, text in entries]
        translated_texts = []
        total_batches = (len(original_texts) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(original_texts), BATCH_SIZE):
            batch_texts = original_texts[i:i + BATCH_SIZE]
            current_batch_num = (i // BATCH_SIZE) + 1
            print(f"  [{thread_id}] {file_name}: Processing batch {current_batch_num}/{total_batches}")
            translated_batch = self.translate_batch(batch_texts, file_name)
            translated_texts.extend(translated_batch)
            self.save_cache()  # Зберігаємо кеш після кожного батчу

        translated_content = content
        for (name, original), translated in zip(entries, translated_texts):
            # Використовуємо функцію для заміни, щоб уникнути помилок з однаковими рядками
            old_entry = f'<entry name="{name}">{original}</entry>'
            new_entry = f'<entry name="{name}">{translated}</entry>'
            translated_content = translated_content.replace(old_entry, new_entry, 1)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        print(f"  [{thread_id}] ✅ {file_name} saved to: {output_path}")
        return True

    def process_all_files(self):
        source_path = Path(SOURCE_DIR)
        output_path = Path(OUTPUT_DIR)

        # <<< ЗМІНЕНО: Шукаємо файли, що починаються з RU_
        files = list(source_path.glob("RU_*.txt")) + list(source_path.glob("RU_*.xml"))

        if not files:
            print(f"❌ No files found in {SOURCE_DIR} starting with 'RU_'")
            return

        print(f"🎮 SILKSONG UKRAINIAN TRANSLATION (from RU)")
        print(f"📁 Found {len(files)} files to translate")
        print(f"⚡ Parallel processing: {MAX_PARALLEL_FILES} files")
        print(f"📦 Batch size: {BATCH_SIZE} entries per API call")
        print(f"🤖 Using model: {MODEL_NAME}")

        response = input("\n⚠️  Continue with translation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Translation cancelled.")
            return

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FILES) as executor:
            future_to_file = {}
            for i, file_path in enumerate(files, 1):
                relative_path = file_path.relative_to(source_path)
                # <<< ЗМІНЕНО: Замінюємо RU_ на UA_ у назві вихідного файлу
                output_filename = file_path.name.replace("RU_", "UA_", 1)
                output_file = output_path / relative_path.with_name(output_filename)

                future = executor.submit(self.process_file, str(file_path), str(output_file), i, len(files))
                future_to_file[future] = file_path.name

            for future in as_completed(future_to_file):
                try:
                    future.result()
                except Exception as exc:
                    print(f'❌ {future_to_file[future]} generated an exception: {exc}')

        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 50}")
        print(f"✅ TRANSLATION COMPLETED in {elapsed_time / 60:.1f} minutes!")
        print(f"📊 Statistics:")
        print(f"  - Translated: {self.stats['translated']} strings")
        print(f"  - From cache: {self.stats['cached']} strings")
        print(f"  - Errors: {self.stats['errors']} strings")
        print(f"  - API calls: {self.stats['api_calls']}")
        print(f"  - Tokens used: {self.stats['tokens_used']:,}")

        cost = (self.stats['tokens_used'] / 1_000_000) * 1.5  # Приблизна вартість gpt-4o
        print(f"💵 Actual cost: ${cost:.3f}")
        print(f"📁 Output folder: {OUTPUT_DIR}")
        print(f"💾 Cache saved to: translation_cache.json")

    def save_cache(self):
        with self.cache_lock:
            with open("translation_cache.json", 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        try:
            with open("translation_cache.json", 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
                print(f"📚 Loaded {len(self.translation_cache)} cached translations")
        except FileNotFoundError:
            print("📚 Starting with empty translation cache")


# ... (решта коду без змін) ...

def test_connection():
    print("🔍 Testing OpenAI API connection...")
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Translate to Ukrainian: Hello"}],
            max_completion_tokens=10
        )
        result = response.choices[0].message.content
        print(f"✅ Connection successful! Test response: {result}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("❌ Please set your OpenAI API key in .env file!")
        exit(1)
    if not test_connection():
        exit(1)

    translator = SilksongOpenAITranslator()
    translator.process_all_files()