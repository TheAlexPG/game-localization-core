# Game Translator 🎮🌍

AI-powered universal game localization system with validation and quality control.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Oleksandr%20Basiuk-green.svg)](https://github.com/oleksandr-basiuk)

## 🚀 Features

### Core Capabilities
- **🤖 AI Translation**: OpenAI, OpenRouter (200+ models), DeepSeek, and local models support
- **✅ Smart Validation**: Automatic quality checks with custom patterns
- **📊 Excel Integration**: Professional workflow with Excel import/export
- **🔤 Format Preservation**: Maintains placeholders, HTML tags, and game markup
- **📈 Quality Scoring**: Grading system (0-100) with detailed reports
- **🌐 Multi-Provider**: Single interface for multiple AI providers
- **💾 Version Control**: Track changes between game versions
- **📚 Glossary Management**: Consistent terminology across translations
- **🎯 Context System**: Project and glossary context for better AI understanding

### Validation Features
- Empty translation detection
- Unchanged text identification
- Placeholder validation (`{player}`, `%VALUE%`, `{{var}}`)
- HTML/XML tag preservation
- Custom game-specific patterns (CSV/Excel/JSON)
- HTML entities checking (`&nbsp;`, `&#8212;`)
- System variables (`$test$`, `#ID#`)
- Length ratio warnings

### Context System
- **Project Context**: Game genre, tone, audience, special instructions
- **Glossary Context**: Term extraction rules and translation guidelines
- **File Support**: Markdown, JSON, or inline text
- **Auto-Detection**: Automatic loading of PROJECT_CONTEXT.md and GLOSSARY_CONTEXT.md
- **CLI Management**: Easy context setup and viewing

## 📦 Installation

### Standard Installation
```bash
pip install game-translator
```

Includes everything needed:
- CLI tools
- OpenAI/OpenRouter/DeepSeek support
- Excel file handling
- Validation system

### Development Installation
```bash
# Clone repository
git clone https://github.com/oleksandr-basiuk/game-translator.git
cd game-translator

# Install in development mode
pip install -e .

# Install development tools
pip install -e .[dev]
```

## 🎯 Quick Start

### Command Line Interface

```bash
# Initialize new project
game-translator init --name "my-game" --target-lang "uk"

# Set up context for better translations
game-translator context set --project "my-game" --json '{"genre": "RPG", "tone": "epic"}'

# Create validation patterns template
game-translator create-patterns --template excel

# Translate with AI (context automatically included)
game-translator translate --project "my-game" --provider openai --api-key "sk-..."

# Or use OpenRouter for access to 200+ models
game-translator translate --project "my-game" --provider openrouter --model "google/gemini-2.5-flash"

# Validate translations (updates status to PENDING for failed entries by default)
game-translator validate --project "my-game" --patterns "patterns.xlsx"

# Just check validation without updating status
game-translator validate --project "my-game" --ignore-update-status

# Check project status (shows real statistics)
game-translator status --project "my-game"

# Export translations (replaces invalid with original by default)
game-translator export --project "my-game" --format json

# Export with validation errors as-is
game-translator export --project "my-game" --format json --ignore-validation
```

### Python Library

```python
from game_translator import (
    create_project,
    get_provider,
    create_validator
)

# Create project
project = create_project("my-game", "en", "uk")

# Set up context for better translations
project.set_project_context({
    "genre": "Dark Fantasy RPG",
    "tone": "epic and serious",
    "audience": "adults 18-30"
})

# Import source files
project.import_source("source.json")

# Setup AI provider
provider = get_provider("openai", api_key="sk-...")

# Translate (context automatically included)
manager = project.translate_all(provider)

# Validate
validator = create_validator("patterns.xlsx")
results = validator.validate_project(project)
print(f"Quality Score: {results.quality_metrics.overall_score}/100")

# Export results
project.export_table("translations.xlsx")
```

## 📄 Supported File Formats

### CSV Import

The CSV importer automatically detects column names for translation data.

**Supported column names:**
- **Key/ID column** (required): `key`, `Key`, `KEY`, `id`, `Id`, `ID`
- **Source text column** (required): `source`, `Source`, `SOURCE`, `text`, `Text`, `TEXT`, `original`, `Original`
- **Target/translation column** (optional): `target`, `Target`, `TARGET`, `translation`, `Translation`, `translated`
- **Context column** (optional): `context`, `Context`, `CONTEXT`, `description`, `Description`

**CSV file requirements:**
- First row must contain column headers
- UTF-8 encoding (with or without BOM)
- Comma (`,`) or tab (`\t`) separated values
- At minimum must have a key column and source text column

**Example CSV structure:**
```csv
key,source,target
/ID001,Hello World,Привіт Світ
/ID002,New Game,Нова гра
/ID003,Settings,Налаштування
```

**Note:** If your CSV uses different column names (e.g., `string_id`, `en_US`, `uk_UA`), you'll need to rename them to match supported names or modify the CSV importer.

### JSON Format

Standard JSON format with key-value pairs:
```json
{
  "menu.new_game": "New Game",
  "menu.load_game": "Load Game",
  "menu.settings": "Settings"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# OpenAI
export OPENAI_API_KEY="sk-your-key"

# OpenRouter (200+ models access)
export OPENROUTER_API_KEY="sk-or-your-key"

# Local Model
export LOCAL_API_URL="http://localhost:1234/v1/chat/completions"
```

### Custom Validation Patterns

Create `patterns.csv`:
```csv
name,pattern,description,enabled
unity_refs,\{\{[^}]+\}\},Unity references like {{inventory}},true
color_codes,\[color=#[0-9a-fA-F]{6}\],Color codes like [color=#FF0000],true
input_actions,INPUT_ACTION_\w+,Input action constants,true
```

Or use Excel template:
```bash
game-translator create-patterns --template excel --output "my_patterns.xlsx"
```

### Project Context

Context helps AI understand your game better for more accurate translations.

**Set up context via CLI:**
```bash
# From JSON
game-translator context set --project "my-game" --json '{"genre": "Fantasy RPG", "tone": "epic"}'

# From file
game-translator context set --project "my-game" --file "PROJECT_CONTEXT.md"

# View context
game-translator context show --project "my-game"
```

**Context file example:**
```markdown
# PROJECT_CONTEXT.md

## Genre
Dark Fantasy RPG with Souls-like elements

## Target Audience
Hardcore gamers (18-35), fantasy enthusiasts

## Tone
- Dark and atmospheric
- Epic boss encounters
- Melancholic storytelling

## Special Instructions
- Keep all [ITEM_] tags unchanged
- Character names should sound ancient
- Use formal language for lore texts
```

**Python API:**
```python
# Set context programmatically
project.set_project_context({
    "genre": "RPG",
    "tone": "dark",
    "preserve_ids": True
})

# From file
project.set_project_context(from_file="game_context.md")

# Set glossary context
project.set_glossary_context({
    "extract_npcs": True,
    "keep_locations": False
})
```

## 📚 Documentation

- **[CLI Usage Guide](docs/CLI_USAGE.md)** - Complete CLI reference
- **[Validation System](docs/VALIDATION.md)** - Validation features and patterns
- **[Package Build Guide](docs/PACKAGE_BUILD_GUIDE.md)** - Building and distribution

## 🎮 Real Game Support

Successfully tested with:
- **Hollow Knight: Silksong** - Complex markup, placeholders
- **X4: Foundations** - HTML entities, system variables
- **Unity Games** - Color codes, input actions
- **Unreal Engine** - Blueprint references, markup

## 🏗️ Project Structure

```
game-translator/
├── game_translator/           # Core library
│   ├── core/                 # Core functionality
│   │   ├── models.py         # Data models
│   │   ├── project.py        # Project management
│   │   ├── validation.py     # Validation system
│   │   └── translator.py     # Translation engine
│   ├── providers/            # AI providers
│   ├── importers/            # File importers
│   └── exporters/            # File exporters
├── game_translator_cli/       # CLI application
├── docs/                     # Documentation
├── examples/                 # Usage examples
└── tests/                    # Test suite
```

## 🤝 Supported AI Providers

### OpenAI
```python
provider = get_provider("openai",
    api_key="sk-...",
    model="gpt-4o-mini"
)
```

### OpenRouter
```python
provider = get_provider("openrouter",
    api_key="sk-or-...",
    model="google/gemini-2.5-flash"
)
```

**CLI Usage:**
```bash
# Set environment variable
export OPENROUTER_API_KEY="sk-or-your-key"

# Use with CLI
game-translator translate --project "my-game" --provider openrouter --model "google/gemini-2.5-flash"
```

**Features:**
- Access to 200+ models through OpenRouter
- No batching (individual requests for each text)
- Parallel processing with threading
- Structured output support for compatible models
- Optional site ranking headers

**Popular Models:**
- `google/gemini-2.5-flash` - Fast and reliable (default)
- `anthropic/claude-3.5-sonnet` - High quality translations
- `meta-llama/llama-3.2-90b-text-preview` - Large context window
- `openai/gpt-4o` - OpenAI's latest through OpenRouter
- `qwen/qwen-2.5-72b-instruct` - Multilingual specialist

### DeepSeek
```python
provider = get_provider("openai",
    api_key="sk-...",
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat"
)
```

### Local Models
```python
provider = get_provider("local",
    api_url="http://localhost:1234/v1/chat/completions",
    model="gemma-2-2b"
)
```

## 📊 Example Workflow

1. **Initialize Project**
   ```bash
   game-translator init --name "rpg-game" --target-lang "es"
   ```

2. **Import Game Files**
   ```bash
   cd projects/rpg-game
   cp /path/to/game/texts.json source/
   ```

3. **Create Custom Patterns**
   ```bash
   game-translator create-patterns --template excel
   # Edit validation_patterns_template.xlsx
   ```

4. **Translate with AI**
   ```bash
   # Using OpenAI
   game-translator translate \
     --project "rpg-game" \
     --provider openai \
     --patterns "validation_patterns_template.xlsx"

   # Using OpenRouter (access to 200+ models)
   game-translator translate \
     --project "rpg-game" \
     --provider openrouter \
     --model "google/gemini-2.5-flash" \
     --patterns "validation_patterns_template.xlsx"
   ```

5. **Validate Quality**
   ```bash
   # Validate and update status for failed entries
   game-translator validate --project "rpg-game" --strict

   # Or just check without updating status
   game-translator validate --project "rpg-game" --strict --ignore-update-status
   ```

6. **Export for Game**
   ```bash
   # Safe export (replaces invalid translations with original)
   game-translator export --project "rpg-game" --format json

   # Export everything as-is (risky)
   game-translator export --project "rpg-game" --format json --ignore-validation

   # Export to Excel for review
   game-translator export --project "rpg-game" --format excel
   ```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=game_translator

# Specific test
pytest tests/validation/
```

## 📈 Quality Metrics & Validation

The validation system provides comprehensive quality scoring:

### Validation Output Example
```
Validation Summary
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Type                ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Entries       │ 72035 │
│ Entries with Issues │  1593 │
│ Total Issues        │  1650 │
│ Total Warnings      │   315 │
└─────────────────────┴───────┘

Quality score: 97.8/100 (Grade: A)
```

### Validation Behavior
- **Default**: Automatically updates status to `PENDING` for entries with validation errors
- **With `--ignore-update-status`**: Only shows issues without modifying status

### Export Behavior
- **Default**: Replaces invalid translations with original text (safe for game)
- **With `--ignore-validation`**: Exports all translations as-is (may break game)

### Status Command
Shows real-time statistics from your project:
```
Project: x4-foundation
┏━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃ Status     ┃ Count ┃ Percentage ┃
┡━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ Total      │ 72035 │     100.0% │
│ Pending    │  1593 │       2.2% │
│ Translated │ 70442 │      97.8% │
│ Reviewed   │     0 │       0.0% │
│ Approved   │     0 │       0.0% │
└────────────┴───────┴────────────┘

Completion: 97.8%
```

## 🛠️ Advanced Features

### Batch Processing
```python
# Process multiple files
for file in Path("source").glob("*.json"):
    project.import_source(file)

# Batch translate with progress
project.translate_all(provider, batch_size=10, callback=progress_fn)
```

### Custom Validators
```python
# Add custom validation patterns
validator.add_custom_pattern(
    name="skill_refs",
    pattern=r"SKILL_\w+",
    description="Skill references"
)
```

### Export Options
```python
# Excel with formatting
project.export_table("translations.xlsx", include_glossary=True)

# CSV for simple tools
project.export_csv("translations.csv")

# JSON for reimport
project.export_json("translated.json")
```

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Oleksandr Basiuk**

- GitHub: [@oleksandr-basiuk](https://github.com/TheAlexPG)
- Email: alexpremiumgame@gmail.com

## 🙏 Acknowledgments

- OpenAI for GPT models
- Team behind LM Studio for local model support
- Game development community for feedback
- Contributors and testers

## 📊 Status

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-production--ready-green)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

---

*Built with ❤️ for game developers and localization teams*
