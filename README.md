# Game Translator 🎮🌍

AI-powered universal game localization system with versioning and collaborative workflow.

## Features

- **Universal Format**: Key-value based system works with any game
- **Version Control**: Track changes between game versions
- **Translation Status**: Monitor progress with clear status tracking
- **Collaborative Workflow**: Export to Excel/CSV for translators
- **AI Integration**: Support for OpenAI, DeepSeek, and local models
- **Validation System**: Automatic quality checks for translations
- **Glossary Management**: Consistent terminology across translations

## Quick Start

### Installation

```bash
pip install -e .
```

### Command Line Usage

```bash
# Initialize new project
game-translator init --name my-game --source-lang en --target-lang uk

# Import source files
game-translator import --project my-game --files "./source/*.json"

# Export for translators
game-translator export --project my-game --format excel

# Translate with AI
game-translator translate --project my-game --provider openai --model gpt-4

# Validate translations
game-translator validate --project my-game
```

### Python Library Usage

```python
from game_translator import TranslationProject

# Create project
project = TranslationProject("my-game", source_lang="en", target_lang="uk")

# Import source files
project.import_source(["./game/texts.json"])

# Export for review
project.export_table("translations.xlsx")

# Get statistics
stats = project.get_progress_stats()
print(f"Completion: {stats.completion_rate}%")
```

## Project Structure

```
my-game-project/
├── data/               # Source data storage
├── output/            # Translated files
├── glossary/          # Terminology management
├── .versions/         # Version snapshots
└── project.json       # Project state
```

## Data Format

The system uses a universal key-value format:

```json
{
  "menu.play": "Play Game",
  "menu.settings": "Settings",
  "dialog.confirm": "Are you sure?"
}
```

Each entry tracks:
- **Key**: Unique identifier
- **Source Text**: Original text
- **Translation**: Translated text
- **Status**: pending/translated
- **Hash**: For change detection
- **Context**: Additional information
- **Notes**: Translator comments

## Translation Workflow

1. **Import**: Convert game files to key-value format
2. **Extract Terms**: Build glossary of important terms
3. **Translate**: Use AI or export for manual translation
4. **Validate**: Automatic quality checks
5. **Export**: Convert back to game format

## Supported Formats

- JSON (native)
- CSV
- Excel (with formatting)
- XML (planned)
- Unity (planned)

## Development

See [progress.md](progress.md) for development roadmap and current status.

## License

MIT