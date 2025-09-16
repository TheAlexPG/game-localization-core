# CLI Usage Guide

Command-line interface for Game Translator with AI-powered translation and validation.

## Installation

```bash
# Install dependencies
pip install click rich

# Run CLI from project root
python cli.py --help
```

## Commands Overview

```bash
python cli.py --help
```

Available commands:
- `init` - Initialize new translation project
- `translate` - Translate text using AI providers
- `validate` - Check translation quality and consistency
- `status` - Show project statistics
- `create-patterns` - Generate custom validation pattern templates
- `context` - Manage project and glossary context for better translations

## Command Reference

### 1. Initialize Project

Create a new translation project with proper directory structure.

```bash
python cli.py init --name "my-game" --target-lang "uk"
```

**Options:**
- `--name, -n` *(required)*: Project name
- `--source-lang, -s`: Source language code (default: `en`)
- `--target-lang, -t` *(required)*: Target language code
- `--source-format`: Input file format (default: `json`)
- `--output-format`: Output file format (default: `json`)
- `--dir, -d`: Custom project directory

**Example:**
```bash
python cli.py init \
  --name "fantasy-rpg" \
  --source-lang "en" \
  --target-lang "uk" \
  --dir "./projects/rpg-localization"
```

**Creates structure:**
```
projects/my-game/
├── project.json         # Project configuration
├── source/             # Source translation files
├── translations/       # Work-in-progress translations
├── output/            # Final translated files
├── glossary/          # Translation glossaries
└── validation/        # Validation reports
```

### 2. Translate Content

Translate text entries using AI providers with validation.

```bash
python cli.py translate --project "my-game" --provider openai
```

**Options:**
- `--project, -p` *(required)*: Project name or path
- `--provider` *(required)*: AI provider (`openai`, `local`, `mock`)
- `--model`: Provider-specific model name
- `--api-key`: API key for provider (if required)
- `--batch-size`: Texts per translation batch (default: `5`)
- `--max-entries`: Limit translation count (for testing)
- `--patterns`: Custom validation patterns file

**Examples:**

**OpenAI Provider:**
```bash
python cli.py translate \
  --project "my-game" \
  --provider openai \
  --model "gpt-4o-mini" \
  --api-key "sk-..." \
  --batch-size 10
```

**Local Model:**
```bash
python cli.py translate \
  --project "my-game" \
  --provider local \
  --model "llama3-8b"
```

**With Custom Patterns:**
```bash
python cli.py translate \
  --project "my-game" \
  --provider openai \
  --patterns "my_patterns.csv"
```

### 3. Validate Translations

Check translation quality, consistency, and markup preservation.

```bash
python cli.py validate --project "my-game"
```

**Options:**
- `--project, -p` *(required)*: Project name or path
- `--patterns`: Custom validation patterns file
- `--strict`: Enable strict validation mode
- `--output, -o`: Save validation report to file

**Examples:**

**Basic Validation:**
```bash
python cli.py validate --project "my-game"
```

**Strict Mode with Custom Patterns:**
```bash
python cli.py validate \
  --project "my-game" \
  --patterns "game_patterns.xlsx" \
  --strict \
  --output "validation_report.txt"
```

**Sample Output:**
```
Validating 150 entries...

Validation Results:
------------------------------
Entry: welcome_msg
  OK: No issues

Entry: level_complete
  ERROR: 1 issues found
    - Regular placeholders mismatch. Missing: {score}

Entry: menu_text
  WARNING: 1 warnings
    - Translation identical to source text

Summary:
  Entries: 150
  Issues: 12
  Warnings: 5
  Quality: 85/100 (Grade: B)
```

### 4. Project Status

Display project statistics and completion progress.

```bash
python cli.py status --project "my-game"
```

**Sample Output:**
```
Project: my-game
Source: en -> uk

Statistics:
  Total entries: 150
  Pending: 45 (30.0%)
  Translated: 85 (56.7%)
  Reviewed: 15 (10.0%)
  Approved: 5 (3.3%)

Completion: 70.0%
```

### 5. Create Pattern Templates

Generate template files for custom validation patterns.

```bash
python cli.py create-patterns --template excel
```

**Options:**
- `--template`: Template format (`csv`, `excel`, `json`)
- `--output, -o`: Output file path

**Examples:**

**Excel Template:**
```bash
python cli.py create-patterns \
  --template excel \
  --output "my_patterns.xlsx"
```

**CSV Template:**
```bash
python cli.py create-patterns --template csv
```

Creates `validation_patterns_template.csv` with example patterns:
```csv
name,pattern,description,enabled
square_brackets,\[\w+\],"Square bracket markers like [ACTION]",true
special_ids,#\d{4,6},"Special ID numbers like #1234",true
percentage_vars,%\w+%,"Percentage variables like %PLAYER%",true
```

### 6. Manage Context

Set additional context information to help AI understand your game better and provide more accurate translations.

```bash
python cli.py context --help
```

Context has two types:
- **Project Context**: General game information (genre, tone, audience)
- **Glossary Context**: Instructions for term extraction and translation

#### Set Context from File

**Set project context:**
```bash
python cli.py context set --project "my-game" --file "game_info.md"
```

**Set glossary context:**
```bash
python cli.py context set --project "my-game" --type glossary --file "glossary_rules.md"
```

#### Set Context with JSON

**Project context:**
```bash
python cli.py context set --project "my-game" --json '{"genre": "Dark Fantasy RPG", "tone": "epic and serious", "audience": "adults 18-30"}'
```

**Glossary context:**
```bash
python cli.py context set --project "my-game" --type glossary --json '{"extract_npcs": true, "keep_item_ids": true, "translate_locations": false}'
```

#### Add Single Properties

```bash
# Add to project context
python cli.py context add --project "my-game" --key "genre" --value "RPG"
python cli.py context add --project "my-game" --key "tone" --value "epic"

# Add to glossary context
python cli.py context add --project "my-game" --type glossary --key "extract_skills" --value "true"
```

#### View Current Context

```bash
# Show all context
python cli.py context show --project "my-game"

# Show only project context
python cli.py context show --project "my-game" --type project

# Show only glossary context
python cli.py context show --project "my-game" --type glossary
```

#### Context File Examples

**PROJECT_CONTEXT.md:**
```markdown
# Game Context

## Genre
Dark Fantasy RPG with Metroidvania elements

## Target Audience
Young adults (18-30), fantasy enthusiasts

## Tone and Style
- Epic and serious main storyline
- Some humor in NPC interactions
- Archaic language for ancient texts and spells

## Special Instructions
- Keep all [ITEM_ID] tags unchanged
- Dragon names should sound ancient
- Use formal language for official documents
- Preserve color codes like [color=#FF0000]
```

**GLOSSARY_CONTEXT.md:**
```markdown
# Glossary Extraction Rules

## Extract These Terms
- Character names (NPCs, bosses, companions)
- Location names (cities, dungeons, regions)
- Item names (weapons, armor, consumables)
- Skill and spell names
- Unique game terminology and lore terms

## Do NOT Extract
- Common gaming terms (level, health, mana, inventory)
- UI elements (button labels, menu items)
- Generic descriptive words

## Translation Guidelines
- Character names: Keep original or adapt phonetically
- Locations: Translate descriptive names, keep proper nouns
- Items: Translate functionality, keep brand names
- Skills: Make them sound powerful and fantasy-appropriate
```

## Workflow Examples

### Complete Translation Workflow

1. **Initialize project:**
   ```bash
   python cli.py init --name "rpg-game" --target-lang "es"
   ```

2. **Set up context for better translations:**
   ```bash
   # Create context files
   python cli.py context set --project "rpg-game" --json '{"genre": "Fantasy RPG", "tone": "epic", "audience": "adults"}'

   # Or from files
   echo "Fantasy RPG with epic storyline targeting adults" > game_context.md
   python cli.py context set --project "rpg-game" --file "game_context.md"
   ```

3. **Create custom patterns:**
   ```bash
   python cli.py create-patterns --template excel
   # Edit the created template file
   ```

4. **Translate with validation:**
   ```bash
   python cli.py translate \
     --project "rpg-game" \
     --provider openai \
     --patterns "validation_patterns_template.xlsx"
   ```

5. **Check quality:**
   ```bash
   python cli.py validate --project "rpg-game" --strict
   ```

6. **Monitor progress:**
   ```bash
   python cli.py status --project "rpg-game"
   ```

### Quality Assurance Workflow

1. **Validate existing translations:**
   ```bash
   python cli.py validate \
     --project "existing-game" \
     --patterns "qa_patterns.csv" \
     --output "qa_report.txt"
   ```

2. **Review validation report and fix issues**

3. **Re-validate:**
   ```bash
   python cli.py validate --project "existing-game"
   ```

4. **Check final status:**
   ```bash
   python cli.py status --project "existing-game"
   ```

## Configuration

### Environment Variables

```bash
# OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Local model API URL
export LOCAL_API_URL="http://localhost:1234/v1/chat/completions"
```

### Project Configuration

The `project.json` file contains project settings:

```json
{
  "name": "my-game",
  "source_lang": "en",
  "target_lang": "uk",
  "source_format": "json",
  "output_format": "json",
  "glossary_path": null,
  "preserve_terms": [],
  "metadata": {}
}
```

### Custom Validation Patterns

Create CSV, Excel, or JSON files with custom patterns:

**CSV Format:**
```csv
name,pattern,description,enabled
unity_refs,\{\{[^}]+\}\},"Unity references like {{inventory}}",true
color_codes,\[color=#[0-9a-fA-F]{6}\],"Color codes like [color=#FF0000]",true
```

**Excel Format:**
- Sheet name: `ValidationPatterns`
- Columns: Name, Pattern, Description, Enabled

## Rich Console Output

When `rich` library is available, the CLI provides enhanced output:

- **Colorful panels and tables**
- **Progress bars for translation**
- **Syntax highlighting**
- **Better formatting**

Install with: `pip install rich`

## Error Handling

### Common Issues

**Project not found:**
```
Error: Project not found at projects/my-game
```
→ Check project name or path

**Provider initialization failed:**
```
Error initializing provider: OpenAI API key is required
```
→ Set API key or use environment variable

**Invalid patterns file:**
```
Error: Unsupported patterns file format: .txt
```
→ Use CSV, Excel, or JSON format

### Debug Mode

Add verbose output by using click's debug features:
```bash
python cli.py --help  # Shows all available options
```

## Integration

The CLI can be integrated into larger workflows:

### CI/CD Pipeline
```yaml
# .github/workflows/translation.yml
- name: Validate translations
  run: |
    python cli.py validate --project "${{ github.event.repository.name }}" --strict
```

### Build Scripts
```bash
#!/bin/bash
# build-translations.sh

echo "Validating translations..."
python cli.py validate --project "my-game" --output "validation.log"

if [ $? -eq 0 ]; then
    echo "Validation passed, proceeding with build..."
    # Continue with build process
else
    echo "Validation failed, check validation.log"
    exit 1
fi
```

### Batch Processing
```bash
# Process multiple projects
for project in projects/*/; do
    project_name=$(basename "$project")
    echo "Processing $project_name..."
    python cli.py validate --project "$project_name"
done
```

This CLI provides a complete interface for AI-powered game translation with quality control and validation features.