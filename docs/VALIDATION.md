# Translation Validation System

The validation system ensures translation quality by checking for consistency of placeholders, markup, and custom patterns between source and translated text.

## Overview

The validation system provides:
- **Standard validation** for common markup types
- **Custom pattern support** for project-specific markup
- **Flexible configuration** via CSV, Excel, or runtime API
- **Detailed error reporting** with suggestions

## Core Validation Types

### 1. Empty Translations
Detects missing or empty translations when status indicates completion.

```python
# ERROR: Translation is empty but status is not pending
source: "Continue"
translation: ""  # Empty
status: TRANSLATED  # Should be PENDING
```

### 2. Unchanged Text
Identifies translations identical to source text (excluding technical terms).

```python
# WARNING: Translation identical to source text
source: "Start Game"
translation: "Start Game"  # Same as source
```

**Technical terms are handled differently:**
```python
# INFO: Technical text unchanged (expected)
source: "API"
translation: "API"  # OK for technical terms
```

### 3. Placeholders
Ensures all `{placeholder}` variables are preserved.

```python
# ✓ Correct
source: "Level {level} completed with {score} points"
translation: "Рівень {level} завершено з {score} очками"

# ✗ Missing placeholders
source: "Player {name} has {coins} coins"
translation: "Player has coins"  # Missing {name}, {coins}
# ERROR: Regular placeholders mismatch. Missing: {coins}, {name}
```

### 4. System Variables
Validates `$VARIABLE$` patterns commonly used for input mappings.

```python
# ✓ Correct
source: "Press $INPUT_ACTION_FIRE$ to shoot"
translation: "Натисніть $INPUT_ACTION_FIRE$ для стрільби"

# ✗ Missing variable
source: "Use $INPUT_ACTION_BOOST$ to boost"
translation: "Use boost button"  # Missing $INPUT_ACTION_BOOST$
# ERROR: System variables mismatch. Missing: $INPUT_ACTION_BOOST$
```

### 5. HTML/XML Tags
Ensures proper tag structure is maintained.

```python
# ✓ Correct tags
source: "Click <b>here</b> to continue"
translation: "Натисніть <b>тут</b> для продовження"

# ✗ Missing closing tag
source: "This is <strong>important</strong> text"
translation: "Це <strong>важливий текст"  # Missing </strong>
# ERROR: HTML/XML tags don't match. Source: ['<strong>', '</strong>'], Translation: ['<strong>']

# ✗ Different tags
source: "Click <b>Start</b> button"
translation: "Натисніть <strong>Старт</strong> кнопку"  # <b> changed to <strong>
# ERROR: HTML/XML tags don't match
```

### 6. HTML Entities
Validates escaped HTML characters.

```python
# ✓ Correct entities
source: "Text with &lt;special&gt; tags and &amp; symbols"
translation: "Текст з &lt;special&gt; тегами та &amp; символами"

# ✗ Missing entities
source: "Use &lt;menu&gt; and &amp; options"
translation: "Use <menu> and & options"  # Entities converted to actual chars
# ERROR: HTML entities mismatch. Missing: &lt;, &amp;, &gt;
```

## Real Game Examples

### Hollow Knight: Silksong
```python
# Complex markup with page tags and entities
source: "Soon, Pavo, I will quieten the chaos. Please tend to these bugs until then.&lt;page&gt;Of course, dear dweller!"
translation: "Незабаром, Паво, я вгамую хаос. Будь ласка, приглянь за цими жуками до того часу.&lt;page&gt;Звісно, дорога мешканко!"
# ✓ All entities preserved correctly

# Apostrophe entity
source: "I&amp;#8217;m a master at tight stringing!"
translation: "Я&amp;#8217; вправний майстер у тугому нанизуванні!"
# ✓ Apostrophe entity preserved
```

### X4: Foundations
```python
# Game ID placeholders
source: "Construction Vessel same as {20204,5101}"
translation: "Construction Vessel same as {20204,5101}"
# ✓ Game ID preserved

# System input variables
source: "use $INPUT_ACTION_CYCLE_NEXT_PRIMARY_WEAPONGROUP$ to cycle"
translation: "використовуйте $INPUT_ACTION_CYCLE_NEXT_PRIMARY_WEAPONGROUP$ для перемикання"
# ✓ Long system variable preserved

# Mixed patterns
source: "Purchase at {20007,1441} using $INPUT_ACTION_BUY$ command"
translation: "Придбайте в {20007,1441} використовуючи команду $INPUT_ACTION_BUY$"
# ✓ All placeholder types preserved
```

## Custom Patterns

The validation system supports custom patterns for project-specific markup.

### Loading Custom Patterns

#### From CSV File
```csv
name,pattern,description,enabled
square_brackets,\[\w+\],"Square bracket markers like [ACTION] [ITEM]",true
special_ids,#\d{4,6},"Special ID numbers like #1234 #123456",true
percentage_vars,%\w+%,"Percentage variables like %PLAYER% %LEVEL%",false
unity_refs,\{\{[^}]+\}\},"Unity text mesh references like {{ref}}",true
color_codes,\[color=#[0-9a-fA-F]{6}\],"Color codes like [color=#FF0000]",false
```

#### From Excel File
Create a sheet named `ValidationPatterns` with columns:
- **Name**: Pattern identifier
- **Pattern**: Regular expression
- **Description**: Human-readable description
- **Enabled**: TRUE/FALSE to enable/disable

#### Programmatically
```python
from game_translator.core.validation import TranslationValidator
from game_translator.core.custom_patterns import CustomPatternsManager

# Load from file
manager = CustomPatternsManager()
patterns = manager.load_from_csv("custom_patterns.csv")

# Create validator with custom patterns
validator = TranslationValidator(custom_patterns=patterns)

# Or add at runtime
validator.add_custom_pattern(
    name="pipe_vars",
    pattern=r'\|[A-Z_]+\|',
    description="Pipe variables like |HEALTH| |MANA|"
)
```

### Custom Pattern Examples

#### Square Bracket Markers
```python
# Pattern: \[\w+\]
source: "Press [FIRE] to attack and [JUMP] to jump"
translation: "Натисніть [FIRE] для атаки та [JUMP] для стрибка"
# ✓ Square brackets preserved

source: "Use [ACTION] button and [MENU] key"
translation: "Використовуйте кнопку дії та клавішу меню"  # Missing [ACTION] [MENU]
# ERROR: Custom pattern square_brackets mismatch. Missing: [ACTION], [MENU]
```

#### Special ID Numbers
```python
# Pattern: #\d{4,6}
source: "Item #1234 costs 100 gold"
translation: "Предмет #1234 коштує 100 золота"
# ✓ Special ID preserved

source: "Quest #5678 and item #123456"
translation: "Квест та предмет"  # Missing both IDs
# ERROR: Custom pattern special_ids mismatch. Missing: #5678, #123456
```

#### Percentage Variables
```python
# Pattern: %\w+%
source: "Hello %PLAYER%, your level is %LEVEL%"
translation: "Привіт %PLAYER%, твій рівень %LEVEL%"
# ✓ Percentage variables preserved

source: "Welcome %USER% to level %CURRENT_LEVEL%"
translation: "Ласкаво просимо до рівня"  # Missing %USER% %CURRENT_LEVEL%
# ERROR: Custom pattern percentage_vars mismatch. Missing: %USER%, %CURRENT_LEVEL%
```

#### Unity Text Mesh References
```python
# Pattern: \{\{[^}]+\}\}
source: "Check {{inventory}} and {{stats}} screens"
translation: "Перевірте екрани {{inventory}} та {{stats}}"
# ✓ Unity references preserved

source: "Open {{settings}} menu and {{help}} guide"
translation: "Відкрийте меню налаштувань та довідку"  # Missing {{settings}} {{help}}
# ERROR: Custom pattern unity_refs mismatch. Missing: {{settings}}, {{help}}
```

#### Color Codes
```python
# Pattern: \[color=#[0-9a-fA-F]{6}\]
source: "This text is [color=#FF0000]red[/color] and [color=#00FF00]green[/color]"
translation: "Цей текст [color=#FF0000]червоний[/color] та [color=#00FF00]зелений[/color]"
# ✓ Color codes preserved
```

#### Mixed Custom Patterns
```python
source: "Press [START] to begin quest #5678 for %PLAYER% with {{weapon}}"
translation: "Натисніть [START] щоб розпочати квест #5678 для %PLAYER% з {{weapon}}"
# ✓ All custom pattern types preserved

source: "Use [ATTACK] against enemy #9999 while %HEALTH% > 50 via {{combat}}"
translation: "Використовуйте атаку проти ворога поки здоров'я більше 50"  # All patterns missing
# ERROR: Multiple custom pattern mismatches detected
```

## Usage Examples

### Basic Validation
```python
from game_translator.core.validation import TranslationValidator
from game_translator.core.models import TranslationEntry, TranslationStatus

# Create validator
validator = TranslationValidator()

# Create entry to validate
entry = TranslationEntry(
    key="example",
    source_text="Level {level} completed with {score} points",
    translated_text="Рівень завершено з очками",  # Missing placeholders
    status=TranslationStatus.TRANSLATED
)

# Validate
result = validator.validate_entry(entry)

# Check results
if result.issues:
    for issue in result.issues:
        print(f"ERROR: {issue.message}")
        if issue.suggestion:
            print(f"Suggestion: {issue.suggestion}")

if result.warnings:
    for warning in result.warnings:
        print(f"WARNING: {warning.message}")
```

### Project-Wide Validation
```python
# Validate entire project
class MockProject:
    def __init__(self, entries):
        self.entries = {entry.key: entry for entry in entries}

project = MockProject(entries)
result = validator.validate_project(project)

print(f"Checked {result.checked_count} entries")
print(f"Found {len(result.issues)} errors, {len(result.warnings)} warnings")

# Quality metrics
from game_translator.core.validation import QualityMetrics

completion_rate = QualityMetrics.calculate_completion_rate(entries)
quality_score = QualityMetrics.calculate_quality_score(result)
quality_grade = QualityMetrics.get_quality_grade(quality_score)

print(f"Completion: {completion_rate:.1f}%")
print(f"Quality: {quality_score:.1f}/100 (Grade: {quality_grade})")
```

### Custom Patterns Integration
```python
from game_translator.core.custom_patterns import CustomPatternsManager

# Load custom patterns
manager = CustomPatternsManager()

# From CSV
patterns = manager.load_from_csv("game_patterns.csv")

# From Excel
patterns = manager.load_from_excel("translations.xlsx", "ValidationPatterns")

# Create validator with custom patterns
validator = TranslationValidator(custom_patterns=manager.get_patterns_for_validator())

# Validation now includes custom patterns
entry = TranslationEntry(
    key="custom_test",
    source_text="Press [FIRE] and check item #1234 for %PLAYER%",
    translated_text="Press and check item for player",  # Missing all custom markup
    status=TranslationStatus.TRANSLATED
)

result = validator.validate_entry(entry)
# Will detect missing [FIRE], #1234, and %PLAYER% patterns
```

### Creating Excel Template
```python
# Generate template for users
manager = CustomPatternsManager()
manager.save_template_excel("custom_patterns_template.xlsx")
# Creates Excel file with example patterns that users can modify
```

## Error Types and Severity

### Errors (Critical Issues)
- `empty_translation`: Missing translation with wrong status
- `placeholder_mismatch`: Missing or extra `{placeholders}`
- `system_variable_mismatch`: Missing or extra `$VARIABLES$`
- `html_entity_mismatch`: Missing or extra `&entities;`
- `html_tag_mismatch`: Missing or mismatched `<tags>`
- `custom_*_mismatch`: Missing custom pattern elements

### Warnings (Should Review)
- `unchanged_text`: Translation identical to source (non-technical)

### Info (Informational)
- `technical_unchanged`: Technical term unchanged (expected)
- `content_unchanged`: Content same as source (formatting differences)

## Configuration Options

### Strict Mode
```python
# Normal mode: some issues are warnings
validator = TranslationValidator(strict_mode=False)

# Strict mode: more issues become errors
validator = TranslationValidator(strict_mode=True)
```

### Pattern Compilation
All patterns are compiled once during validator initialization for performance:
- Standard patterns: Built-in regex patterns
- Custom patterns: User-defined regex patterns
- Runtime patterns: Added via API

### Error Handling
- Invalid custom patterns are logged but don't crash validation
- Missing files return empty pattern sets
- Malformed regex patterns are caught and reported

## Best Practices

### For Game Developers
1. **Define project patterns early** - Create custom pattern files at project start
2. **Use descriptive names** - Pattern names should clearly indicate their purpose
3. **Test patterns thoroughly** - Validate regex patterns with representative text
4. **Document patterns** - Include descriptions for team members
5. **Version control patterns** - Track pattern files with your translations

### For Translators
1. **Preserve all markup** - Never remove placeholders, tags, or custom patterns
2. **Maintain order** - Keep markup elements in appropriate positions
3. **Check validation** - Run validation before submitting translations
4. **Ask about unknown patterns** - Clarify purpose of custom markup with developers

### For Quality Assurance
1. **Regular validation** - Run validation on all translation updates
2. **Review warnings** - Check unchanged translations for correctness
3. **Monitor quality scores** - Track quality metrics over time
4. **Update patterns** - Add new patterns as game content evolves

## Integration with Translation Workflow

The validation system integrates with the broader translation pipeline:

1. **Import phase**: Validate source files for consistency
2. **Translation phase**: Check individual entries as they're completed
3. **Review phase**: Full project validation before release
4. **Export phase**: Final validation before generating game files

This ensures translation quality is maintained throughout the localization process while supporting the specific markup requirements of different games and projects.