#!/usr/bin/env python3
"""Test core validation functionality - placeholders and HTML/XML tags"""

from game_translator.core.validation import TranslationValidator
from game_translator.core.models import TranslationEntry, TranslationStatus


def demo_placeholder_validation():
    """Demonstrate how placeholder validation works"""
    print("PLACEHOLDER VALIDATION")
    print("=" * 30)

    validator = TranslationValidator()

    examples = [
        {
            "name": "OK Correct placeholders",
            "source": "Level {level} completed with {score} points",
            "translation": "Рівень {level} завершено з {score} очками"
        },
        {
            "name": "ERROR Missing placeholder",
            "source": "Player {name} has {coins} coins",
            "translation": "Гравець має монети"  # Missing both {name} and {coins}
        },
        {
            "name": "ERROR Extra placeholder",
            "source": "Welcome to the game",
            "translation": "Ласкаво просимо до гри {version}"  # Extra {version}
        },
        {
            "name": "ERROR Wrong placeholder names",
            "source": "Damage: {damage}",
            "translation": "Урон: {dmg}"  # {damage} -> {dmg}
        },
        {
            "name": "OK Multiple same placeholders",
            "source": "{value} + {value} = {result}",
            "translation": "{value} + {value} = {result}"
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  Source:      '{example['source']}'")
        print(f"  Translation: '{example['translation']}'")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        # Show placeholder analysis
        import re
        source_placeholders = re.findall(r'\{[^}]+\}', example['source'])
        trans_placeholders = re.findall(r'\{[^}]+\}', example['translation'])

        print(f"  Source placeholders:      {source_placeholders}")
        print(f"  Translation placeholders: {trans_placeholders}")

        if result.issues:
            for issue in result.issues:
                if issue.issue_type == "placeholder_mismatch":
                    print(f"  ERROR: {issue.message}")
                    if issue.suggestion:
                        print(f"      Suggestion: {issue.suggestion}")
        else:
            print(f"  OK: Placeholders match")


def demo_html_xml_validation():
    """Demonstrate how HTML/XML tag validation works"""
    print("\n\nHTML/XML TAG VALIDATION")
    print("=" * 30)

    validator = TranslationValidator()

    examples = [
        {
            "name": "OK Correct HTML tags",
            "source": "Click <b>here</b> to continue",
            "translation": "Натисніть <b>тут</b> для продовження"
        },
        {
            "name": "ERROR Missing closing tag",
            "source": "This is <strong>important</strong> text",
            "translation": "Це <strong>важливий текст"  # Missing </strong>
        },
        {
            "name": "ERROR Different tag",
            "source": "Click <b>Start</b> button",
            "translation": "Натисніть <strong>Старт</strong> кнопку"  # <b> -> <strong>
        },
        {
            "name": "OK Self-closing XML tags",
            "source": "Next page<br/>Continue",
            "translation": "Наступна сторінка<br/>Продовжити"
        },
        {
            "name": "ERROR Removed all tags",
            "source": "Press <i>any</i> key to <u>continue</u>",
            "translation": "Натисніть будь-яку клавішу для продовження"  # No tags
        },
        {
            "name": "OK Tags with attributes (simplified check)",
            "source": '<a href="#menu">Menu</a>',
            "translation": '<a href="#menu">Меню</a>'
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  Source:      '{example['source']}'")
        print(f"  Translation: '{example['translation']}'")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        # Show tag analysis
        import re
        source_tags = re.findall(r'<[^>]+>', example['source'])
        trans_tags = re.findall(r'<[^>]+>', example['translation'])

        print(f"  Source tags:      {source_tags}")
        print(f"  Translation tags: {trans_tags}")

        if result.issues:
            for issue in result.issues:
                if issue.issue_type == "tag_mismatch":
                    print(f"  ERROR: {issue.message}")
                    if issue.suggestion:
                        print(f"      Suggestion: {issue.suggestion}")
        else:
            print(f"  OK: Tags match")


def explain_validation_logic():
    """Explain how the validation logic works internally"""
    print("\n\nVALIDATION LOGIC EXPLAINED")
    print("=" * 30)

    print("""
PLACEHOLDER VALIDATION:
1. Uses regex pattern: r'\\{[^}]+\\}'
2. Finds all {placeholder} patterns in source text
3. Finds all {placeholder} patterns in translation
4. Compares two sets of placeholders
5. Reports missing or extra placeholders

Example code:
    source_placeholders = re.findall(r'\\{[^}]+\\}', source_text)
    trans_placeholders = re.findall(r'\\{[^}]+\\}', translation)

    source_set = set(source_placeholders)
    trans_set = set(trans_placeholders)

    if source_set != trans_set:
        missing = source_set - trans_set  # In source but not in translation
        extra = trans_set - source_set    # In translation but not in source
        # Report as error

HTML/XML TAG VALIDATION:
1. Uses regex pattern: r'<[^>]+>'
2. Finds all <tag> patterns in source text
3. Finds all <tag> patterns in translation
4. Compares tag lists (order matters for now)
5. Reports mismatched tag structure

Example code:
    source_tags = re.findall(r'<[^>]+>', source_text)
    trans_tags = re.findall(r'<[^>]+>', translation)

    if source_tags != trans_tags:
        # Report tag mismatch error

NOTE: Current implementation does simple string comparison.
Could be enhanced to:
- Normalize tag attributes
- Check only tag names, ignore attributes
- Handle tag reordering
- Validate proper nesting
""")


def main():
    """Run core validation demos"""
    import sys

    with open('core_validation_demo.txt', 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f

        demo_placeholder_validation()
        demo_html_xml_validation()
        explain_validation_logic()

        sys.stdout = original_stdout

    print("Core validation demo completed. Results saved to: core_validation_demo.txt")


if __name__ == "__main__":
    main()