# Validation Quick Start Guide

Get started with translation validation in 5 minutes.

## 1. Basic Usage

```python
from game_translator.core.validation import TranslationValidator
from game_translator.core.models import TranslationEntry, TranslationStatus

# Create validator
validator = TranslationValidator()

# Create a translation entry
entry = TranslationEntry(
    key="welcome_message",
    source_text="Welcome {player}! Press $INPUT_FIRE$ to start.",
    translated_text="Ласкаво просимо {player}! Натисніть $INPUT_FIRE$ для початку.",
    status=TranslationStatus.TRANSLATED
)

# Validate
result = validator.validate_entry(entry)

# Check results
if result.issues:
    print("❌ Validation errors found:")
    for issue in result.issues:
        print(f"  - {issue.message}")
else:
    print("✅ Validation passed!")
```

## 2. Common Patterns Detected

| Pattern Type | Example | Purpose |
|-------------|---------|---------|
| **Placeholders** | `{level}`, `{score}` | Variable substitution |
| **System Variables** | `$INPUT_FIRE$`, `$MENU_BACK$` | Input mappings |
| **HTML Tags** | `<b>text</b>`, `<br/>` | Text formatting |
| **HTML Entities** | `&lt;`, `&amp;`, `&#8217;` | Escaped characters |

## 3. Adding Custom Patterns

### Method 1: CSV File
Create `patterns.csv`:
```csv
name,pattern,description,enabled
square_brackets,\[\w+\],"Markers like [ACTION]",true
special_ids,#\d{4,6},"IDs like #1234",true
```

Load patterns:
```python
from game_translator.core.custom_patterns import CustomPatternsManager

manager = CustomPatternsManager()
patterns = manager.load_from_csv("patterns.csv")
validator = TranslationValidator(custom_patterns=manager.get_patterns_for_validator())
```

### Method 2: Runtime API
```python
validator.add_custom_pattern(
    name="pipe_vars",
    pattern=r'\|[A-Z_]+\|',
    description="Variables like |HEALTH|"
)
```

## 4. Quick Examples

### ✅ Good Translation
```python
source: "Level {level}: Press [FIRE] to attack enemy #1234"
translation: "Рівень {level}: Натисніть [FIRE] для атаки на ворога #1234"
# All patterns preserved ✓
```

### ❌ Bad Translation
```python
source: "Level {level}: Press [FIRE] to attack enemy #1234"
translation: "Рівень: Натисніть для атаки на ворога"
# Missing: {level}, [FIRE], #1234 ❌
```

## 5. Excel Template

Generate template for your team:
```python
from game_translator.core.custom_patterns import CustomPatternsManager

manager = CustomPatternsManager()
manager.save_template_excel("custom_patterns.xlsx")
# Edit the Excel file and load it back
```

## 6. Quality Scoring

```python
from game_translator.core.validation import QualityMetrics

# Get quality score (0-100)
score = QualityMetrics.calculate_quality_score(validation_result)
grade = QualityMetrics.get_quality_grade(score)

print(f"Quality: {score}/100 (Grade: {grade})")
```

## 7. Project Validation

```python
# Validate entire project
result = validator.validate_project(project)

print(f"Checked: {result.checked_count} entries")
print(f"Errors: {len(result.issues)}")
print(f"Warnings: {len(result.warnings)}")
```

## Next Steps

- Read full [Validation Documentation](VALIDATION.md)
- See real game examples in the documentation
- Create custom patterns for your project
- Integrate with your translation workflow

## Common Issues

**Q: Why is my custom pattern not working?**
A: Check if the regex is valid and properly escaped. Use online regex testers.

**Q: Can I disable certain validations?**
A: Set `enabled=false` in CSV/Excel or don't add unwanted patterns.

**Q: How to handle technical terms?**
A: Technical terms (API, URL, etc.) are automatically detected and allowed to be unchanged.

**Q: What about different languages?**
A: The system is language-agnostic and focuses on markup preservation, not language-specific rules.