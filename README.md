# Game Translator 🎮🌍

AI-powered universal game localization system with validation and quality control.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-Oleksandr%20Basiuk-green.svg)](https://github.com/oleksandr-basiuk)

## 🚀 Features

### Core Capabilities
- **🤖 AI Translation**: OpenAI, OpenRouter, DeepSeek, and local models support
- **✅ Smart Validation**: Automatic quality checks with custom patterns
- **📊 Excel Integration**: Professional workflow with Excel import/export
- **🔤 Format Preservation**: Maintains placeholders, HTML tags, and game markup
- **📈 Quality Scoring**: Grading system (0-100) with detailed reports
- **🌐 Multi-Provider**: Single interface for multiple AI providers
- **💾 Version Control**: Track changes between game versions
- **📚 Glossary Management**: Consistent terminology across translations

### Validation Features
- Empty translation detection
- Unchanged text identification
- Placeholder validation (`{player}`, `%VALUE%`, `{{var}}`)
- HTML/XML tag preservation
- Custom game-specific patterns (CSV/Excel/JSON)
- HTML entities checking (`&nbsp;`, `&#8212;`)
- System variables (`$test$`, `#ID#`)
- Length ratio warnings

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

# Create validation patterns template
game-translator create-patterns --template excel

# Translate with AI
game-translator translate --project "my-game" --provider openai --api-key "sk-..."

# Validate translations
game-translator validate --project "my-game" --patterns "patterns.xlsx"

# Check project status
game-translator status --project "my-game"
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

# Import source files
project.import_source("source.json")

# Setup AI provider
provider = get_provider("openai", api_key="sk-...")

# Translate
manager = project.translate_all(provider)

# Validate
validator = create_validator("patterns.xlsx")
results = validator.validate_project(project)
print(f"Quality Score: {results.quality_metrics.overall_score}/100")

# Export results
project.export_table("translations.xlsx")
```

## 🔧 Configuration

### Environment Variables
```bash
# OpenAI
export OPENAI_API_KEY="sk-your-key"

# OpenRouter
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
provider = get_provider("openai",
    api_key="sk-or-...",
    base_url="https://openrouter.ai/api/v1",
    model="meta-llama/llama-3.2-90b-text-preview"
)
```

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
   game-translator translate \
     --project "rpg-game" \
     --provider openai \
     --patterns "validation_patterns_template.xlsx"
   ```

5. **Validate Quality**
   ```bash
   game-translator validate --project "rpg-game" --strict
   ```

6. **Export for Review**
   ```bash
   # Results are in projects/rpg-game/output/
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

## 📈 Quality Metrics

The validation system provides comprehensive quality scoring:

```
Validation Results:
  Entries: 150
  Issues: 12
  Warnings: 5
  Quality: 85/100 (Grade: B)

Issues by Type:
  - Empty translations: 3
  - Unchanged text: 2
  - Missing placeholders: 5
  - Tag mismatches: 2
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
