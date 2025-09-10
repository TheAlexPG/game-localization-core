# AI Game Localization Pipeline

Модульна система для локалізації ігор за допомогою AI. Підтримує різні AI провайдери та формати файлів.

## Архітектура

Пайплайн складається з 3 основних кроків:

1. **Витяжка термінів** - збір важливих імен та термінів з ігрових файлів
2. **Переклад глосарія** - переклад зібраних термінів з можливістю ручної валідації  
3. **Переклад контенту** - основний переклад з використанням валідованого глосарія

## Структура проекту

```
src/
├── core/           # Базові моделі та конфігурація
├── providers/      # AI провайдери (OpenAI, локальні моделі)  
├── pipeline/       # Компоненти пайплайну
├── processors/     # Обробники файлів для різних ігор
├── games/          # Конфігурації конкретних ігор
└── utils/          # Допоміжні утиліти

scripts/            # CLI скрипти для кожного кроку
data/              # Дані проектів (глосарії, кеш, результати)
```

## Налаштування

1. Встановіть залежності:
```bash
pip install -r requirements.txt
```

2. Створіть `.env` файл:
```bash
# Для OpenAI
OPENAI_API_KEY=your_openai_key

# Для локальних моделей (LM Studio)
LOCAL_API_URL=http://localhost:1234/v1/chat/completions
```

## Використання

### Повний пайплайн
```bash
# Запустити весь пайплайн для Silksong
python scripts/full_pipeline.py --project silksong --provider openai

# Або з локальною моделлю
python scripts/full_pipeline.py --project silksong --provider local --model your-model
```

### Покрокове виконання

#### 1. Витяжка термінів
```bash
# Основна витяжка з ретраями (за замовчуванням 5 спроб)
python scripts/extract_terms.py --project silksong --provider openai

# З підвищеним числом ретраїв
python scripts/extract_terms.py --project silksong --provider openai --max-retries 10

# Повтор тільки проблемних файлів після першого запуску
python scripts/extract_terms.py --project silksong --retry-failed --max-retries 10
```

#### 2. Переклад глосарія
```bash
python scripts/translate_terms.py --project silksong --provider openai
```

Після цього перевірте переклади у файлі `data/silksong/glossaries/glossary_for_review.txt` та скопіюйте схвалені переклади до `final_glossary.json`.

#### 3. Переклад контенту
```bash
python scripts/translate_content.py --project silksong --provider openai
```

### Перевірка статусу
```bash
# Загальний статус проекту
python scripts/project_status.py --project silksong

# Перегляд проблемних файлів
python scripts/show_failed_files.py --project silksong --details
```

## Конфігурація для Silksong

Проект налаштований для заміни німецької локалізації на українську:
- Вхідні файли: `./SILKSONG_EN/._Decrypted/EN_*`
- Вихідні файли: `./data/silksong/silksong_ua/DE_*`

## Додавання підтримки нових ігор

1. Створіть новий процесор файлів у `src/processors/`
2. Додайте конфігурацію у `src/games/`
3. Зареєструйте проект у відповідних скриптах

## Особливості

- **Кешування** - уникнення повторного перекладу
- **Паралельна обробка** - швидша обробка файлів
- **Гнучкі провайдери** - OpenAI або локальні моделі
- **Валідація глосарія** - ручна перевірка термінів
- **Батчинг** - оптимізація API запитів

## Параметри командного рядка

Всі скрипти підтримують:
- `--project` - назва проекту (обов'язково)
- `--provider` - openai або local
- `--model` - назва моделі
- `--dry-run` - показати що буде оброблено без виконання
- `--max-files` - обмежити кількість файлів (для тестування)

## Приклади використання

```bash
# Тестування на 3 файлах
python scripts/extract_terms.py --project silksong --max-files 3 --dry-run

# Використання локальної моделі
python scripts/translate_content.py --project silksong --provider local --model llama-3

# Очистка кешу перед перекладом
python scripts/translate_content.py --project silksong --clear-cache
```