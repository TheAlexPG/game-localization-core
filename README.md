# AI Game Localization Pipeline

Модульна система для локалізації ігор за допомогою AI. Підтримує різні AI провайдери та формати файлів з повною автоматизацією криптографії.

## Архітектура

Пайплайн складається з 3 основних кроків:

1. **Витяжка термінів** - збір важливих імен та термінів з ігрових файлів
2. **Переклад глосарія** - переклад зібраних термінів (одразу створюється final_glossary.json)  
3. **Переклад контенту** - основний переклад з використанням глосарія

## Структура проекту

```
src/
├── core/           # Базові моделі та конфігурація
├── providers/      # AI провайдери (OpenAI, DeepSeek, локальні моделі)  
├── pipeline/       # Компоненти пайплайну
├── processors/     # Обробники файлів для різних ігор
├── games/          # Конфігурації конкретних ігор
└── utils/          # Допоміжні утиліти (включно з криптографією)

scripts/            # CLI скрипти для кожного кроку
data/              # Дані проектів (глосарії, кеш, результати)
```

## Налаштування

1. Встановіть залежності:
```bash
pip install -r requirements.txt
pip install cryptography  # Для Silksong криптографії
```

2. Створіть `.env` файл:
```bash
# Для OpenAI
OPENAI_API_KEY=your_openai_key

# Для DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key

# Для локальних моделей (LM Studio)
LOCAL_API_URL=http://localhost:1234/v1/chat/completions
```

## AI Провайдери

### 🎯 Рекомендації по етапах

#### 1. Збір термінів (витяжка)
**Рекомендовано**: `google/gemma-3-12b` (локально)
- Швидко та точно розпізнає ігрові терміни
- Безкоштовно для тестування
- Менший ризик false positives

#### 2. Переклад глосарія
**Рекомендовано**: `DeepSeek` або `GPT-5`
- DeepSeek: дешевше, але ~18 токенів/сек
- GPT-5: швидше, але дорожче

#### 3. Переклад контенту (основний)
**Рекомендовано**: `OSS-120B`, `GPT-5 mini`, або `Gemini-2.5-flash/pro`
- Найкращий баланс якості та швидкості
- Критично важливий етап

### 📊 Порівняння провайдерів

#### OpenAI
- **Моделі**: gpt-4o, gpt-5, gpt-5-mini
- **Плюси**: висока якість, швидкість, стабільність
- **Мінуси**: платний
- **Використання**: фінальний переклад контенту

#### DeepSeek  
- **Модель**: deepseek-chat
- **Плюси**: дешево, хороша якість перекладу
- **Мінуси**: повільний (~18 токенів/сек)
- **Використання**: переклад глосарія

#### Gemini
- **Моделі**: gemini-2.5-flash, gemini-2.5-pro
- **Плюси**: швидкість, хороша якість
- **Мінуси**: платний
- **Використання**: фінальний переклад контенту

#### Локальні моделі (LM Studio/Ollama)
- **Рекомендовані**: google/gemma-3-12b, OSS-120B
- **Плюси**: повністю безкоштовно, приватність
- **Мінуси**: малі моделі - багато помилок, великі - повільні
- **Використання**: тестування пайплайну

### ⚡ Стратегії використання

#### Тестовий пайплайн (безкоштовно)
```bash
# Весь пайплайн на локальній моделі
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_content.py --project silksong --provider local --model google/gemma-3-12b
```

#### Оптимальний пайплайн (якість/швидкість)
```bash
# Витяжка термінів - безкоштовно
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b

# Глосарій - DeepSeek (дешево, якісно)
python scripts/translate_terms.py --project silksong --provider deepseek --model deepseek-chat

# Контент - GPT-5 mini (швидко, якісно)
python scripts/translate_content.py --project silksong --provider openai --model gpt-5-mini
```

#### Преміум пайплайн (найкраща якість)
```bash
# Все на найсильніших моделях
python scripts/extract_terms.py --project silksong --provider openai --model gpt-5
python scripts/translate_terms.py --project silksong --provider openai --model gpt-5  
python scripts/translate_content.py --project silksong --provider openai --model gpt-5
```

## Повна автоматизація Silksong

### 1. Розшифрування оригінальних файлів
```bash
# Розшифрувати файли гри (замінює C# декриптор)
python scripts/decrypt_silksong.py "E:\Games\Hollow Knight Silksong\Hollow Knight Silksong_Data\Texts"
```

### 2. Пайплайн перекладу

#### 🏆 Рекомендований (оптимальний)
```bash
# Витяжка - локально (швидко + безкоштовно)
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b

# Глосарій - DeepSeek (якісно + дешево)  
python scripts/translate_terms.py --project silksong --provider deepseek --model deepseek-chat

# Контент - GPT-5 mini (швидко + якісно)
python scripts/translate_content.py --project silksong --provider openai --model gpt-5-mini
```

#### 💰 Тестовий (повністю безкоштовно)
```bash
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_content.py --project silksong --provider local --model google/gemma-3-12b
```

#### 💎 Преміум (найкраща якість)
```bash
python scripts/extract_terms.py --project silksong --provider openai --model gpt-5
python scripts/translate_terms.py --project silksong --provider openai --model gpt-5
python scripts/translate_content.py --project silksong --provider openai --model gpt-5
```

### 3. Зашифрування перекладених файлів
```bash
# Зашифрувати українські файли назад у формат гри
python scripts/encrypt_silksong.py "data/silksong/output/SILKSONG_UA"
```

## Особливості Silksong

### Криптографія
- **Алгоритм**: AES ECB + PKCS7 padding
- **Ключ**: `UKu52ePUBwetZ9wNX88o54dnfKRu0T1l` 
- **Формат**: JSON з полями `m_Name` та `m_Script` (base64)
- **Python реалізація**: повна сумісність з C# версією

### Форматування
- **XML теги**: `&lt;page=S&gt;`, `&lt;hpage&gt;` зберігаються
- **HTML entities**: `&#8217;`, `&amp;` не змінюються
- **Спеціальні символи**: всі зберігаються в оригінальному вигляді
- **Тільки текст**: перекладається лише текстовий контент

### Структура файлів
- **Вхідні**: `EN_*.json` (зашифровані)
- **Проміжні**: `EN_*.txt` (розшифровані)
- **Вихідні**: `DE_*.txt` (перекладені)
- **Фінальні**: `DE_*.json` (зашифровані українською)

## Глоссарій

### Автоматичне створення
- `translate_terms.py` одразу створює `final_glossary.json`
- Жодних проміжних кроків - готовий до використання
- `glossary_for_review.txt` для ручної перевірки при потребі

### Token-based batching
- **DeepSeek/OpenAI**: chunking уникає JSON truncation
- **Локальні моделі**: адаптується до context window
- **Retry logic**: автоматичні повтори при помилках

## Конфігурація проектів

### Silksong
```python
SILKSONG_CONFIG = ProjectConfig(
    name="silksong",
    source_lang="English", 
    target_lang_code="DE",  # Замінюємо німецьку локалізацію
    source_dir="./SILKSONG_EN/._Decrypted",
    output_dir="./data/silksong/output"
)
```

## Додавання підтримки нових ігор

1. Створіть новий процесор файлів у `src/processors/`
2. Додайте конфігурацію у `src/games/`
3. Зареєструйте проект у відповідних скриптах
4. За потреби додайте криптографію у `src/utils/`

## Корисні параметри

### Всі скрипти підтримують:
- `--project` - назва проекту (обов'язково)
- `--provider` - openai, deepseek, local
- `--model` - назва моделі
- `--dry-run` - показати що буде оброблено
- `--max-files` - обмежити кількість файлів

### Специфічні параметри:
- `--target-tokens` - розмір батчів для витяжки термінів
- `--max-retries` - максимум спроб при помилках
- `--retry-failed` - повторити тільки проблемні файли
- `--clear-cache` - очистити кеш перекладів
- `--batch-size` - розмір батчів для перекладу

## Приклади використання

```bash
# Рекомендований повний цикл (оптимальний)
python scripts/decrypt_silksong.py "path/to/silksong/texts"
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_terms.py --project silksong --provider deepseek --model deepseek-chat  
python scripts/translate_content.py --project silksong --provider openai --model gpt-5-mini
python scripts/encrypt_silksong.py "data/silksong/output/SILKSONG_UA"

# Тестовий цикл (безкоштовно)
python scripts/decrypt_silksong.py "path/to/silksong/texts"
python scripts/extract_terms.py --project silksong --provider local --model google/gemma-3-12b
python scripts/translate_terms.py --project silksong --provider local --model google/gemma-3-12b  
python scripts/translate_content.py --project silksong --provider local --model google/gemma-3-12b
python scripts/encrypt_silksong.py "data/silksong/output/SILKSONG_UA"

# Тестування на обмеженій кількості файлів
python scripts/extract_terms.py --project silksong --max-files 3 --dry-run

# Повтор проблемних файлів з більшою кількістю спроб
python scripts/extract_terms.py --project silksong --retry-failed --max-retries 10

# Переклад з очищенням кешу
python scripts/translate_content.py --project silksong --provider openai --model gpt-5 --clear-cache
```

## Технічні особливості

- **Кешування** - уникнення повторного перекладу
- **Паралельна обробка** - швидша обробка файлів  
- **JSON схеми** - структурований вивід від AI
- **Unicode підтримка** - правильна обробка українських символів
- **Chunking** - обробка великих глосаріїв по частинах
- **Retry logic** - автоматичні повтори при помилках
- **Fallback** - збереження оригіналу при невдачах