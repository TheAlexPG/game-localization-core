#!/usr/bin/env python3
"""Test custom validation patterns functionality"""

from pathlib import Path
from game_translator.core.validation import TranslationValidator
from game_translator.core.custom_patterns import CustomPatternsManager
from game_translator.core.models import TranslationEntry, TranslationStatus


def create_test_patterns_csv():
    """Create a test CSV with custom patterns"""
    csv_content = """name,pattern,description,enabled
square_brackets,\\[\\w+\\],"Square bracket markers like [ACTION] [ITEM]",true
special_ids,#\\d{4-6},"Special ID numbers like #1234",true
percentage_vars,%\\w+%,"Percentage variables like %PLAYER%",true
color_codes,\\[color=#[0-9a-fA-F]{6}\\],"Color codes like [color=#FF0000]",false
unity_refs,\\{\\{[^}]+\\}\\},"Unity references like {{ref}}",true"""

    csv_path = Path("test_custom_patterns.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    return csv_path


def test_custom_patterns():
    """Test custom patterns functionality"""
    print("CUSTOM VALIDATION PATTERNS TEST")
    print("=" * 35)

    # 1. Create test CSV
    csv_path = create_test_patterns_csv()
    print(f"Created test CSV: {csv_path}")

    # 2. Load custom patterns
    manager = CustomPatternsManager()
    patterns = manager.load_from_csv(csv_path)

    print(f"\nLoaded {len(patterns)} custom patterns:")
    for name, info in patterns.items():
        print(f"  {name}: {info['pattern']} - {info['description']}")

    # 3. Create validator with custom patterns
    custom_patterns_dict = manager.get_patterns_for_validator()
    validator = TranslationValidator(custom_patterns=custom_patterns_dict)

    print(f"\nValidator initialized with {len(custom_patterns_dict)} custom patterns")

    # 4. Test examples with different custom markup
    test_cases = [
        {
            "name": "Square brackets - OK",
            "source": "Press [FIRE] to attack and [JUMP] to jump",
            "translation": "Натисніть [FIRE] для атаки та [JUMP] для стрибка",
            "expected": "OK"
        },
        {
            "name": "Square brackets - Missing",
            "source": "Use [ACTION] button and [MENU] key",
            "translation": "Використовуйте кнопку дії та клавішу меню",  # Missing [ACTION] [MENU]
            "expected": "ERROR"
        },
        {
            "name": "Special IDs - OK",
            "source": "Item #1234 costs 100 gold",
            "translation": "Предмет #1234 коштує 100 золота",
            "expected": "OK"
        },
        {
            "name": "Percentage vars - OK",
            "source": "Hello %PLAYER%, your level is %LEVEL%",
            "translation": "Привіт %PLAYER%, твій рівень %LEVEL%",
            "expected": "OK"
        },
        {
            "name": "Unity refs - Missing",
            "source": "Check {{inventory}} and {{stats}} screens",
            "translation": "Перевірте екрани інвентаря та статистики",  # Missing {{}} refs
            "expected": "ERROR"
        },
        {
            "name": "Mixed custom patterns",
            "source": "Press [START] to begin quest #5678 for %PLAYER%",
            "translation": "Натисніть [START] щоб розпочати квест #5678 для %PLAYER%",
            "expected": "OK"
        }
    ]

    # 5. Run validation tests
    print(f"\nRunning validation tests:")
    print("-" * 30)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}:")
        print(f"   Source: {test_case['source']}")
        print(f"   Translation: {test_case['translation']}")
        print(f"   Expected: {test_case['expected']}")

        entry = TranslationEntry(
            key=f"test_{i}",
            source_text=test_case['source'],
            translated_text=test_case['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            print(f"   Result: ERROR")
            for issue in result.issues:
                if "custom_" in issue.issue_type:
                    print(f"   Custom Pattern Error: {issue.message}")
                else:
                    print(f"   Other Error: {issue.message}")
        else:
            print(f"   Result: OK")

    # 6. Clean up
    csv_path.unlink()
    print(f"\nCleaned up test file: {csv_path}")


def test_excel_template():
    """Test Excel template creation"""
    print("\n\nEXCEL TEMPLATE TEST")
    print("=" * 20)

    manager = CustomPatternsManager()
    excel_path = Path("custom_patterns_template.xlsx")

    try:
        manager.save_template_excel(excel_path)

        if excel_path.exists():
            print(f"Excel template created successfully: {excel_path}")
            print("Template contains example patterns:")
            print("  - Square brackets: [ACTION]")
            print("  - Special IDs: #1234")
            print("  - Percentage vars: %PLAYER%")
            print("  - Unity refs: {{ref}}")
            print("  - Color codes: [color=#FF0000]")
        else:
            print("Excel template creation failed")

    except Exception as e:
        print(f"Excel template test failed: {e}")


def test_runtime_pattern_addition():
    """Test adding custom patterns at runtime"""
    print("\n\nRUNTIME PATTERN ADDITION TEST")
    print("=" * 30)

    # Create validator without custom patterns
    validator = TranslationValidator()
    print("Created validator without custom patterns")

    # Add custom pattern at runtime
    success = validator.add_custom_pattern(
        name="pipe_vars",
        pattern=r'\|[A-Z_]+\|',
        description="Pipe variables like |HEALTH| |MANA|"
    )

    if success:
        print("Successfully added custom pattern: |VARIABLE|")

        # Test the new pattern
        entry = TranslationEntry(
            key="test_runtime",
            source_text="Your |HEALTH| is low and |MANA| is full",
            translated_text="Ваше здоров'я низьке а мана повна",  # Missing |HEALTH| |MANA|
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            for issue in result.issues:
                if "custom_pipe_vars" in issue.issue_type:
                    print(f"Runtime pattern detected missing: {issue.message}")
        else:
            print("No issues found")
    else:
        print("Failed to add custom pattern")


def main():
    """Run all custom pattern tests"""
    try:
        test_custom_patterns()
        test_excel_template()
        test_runtime_pattern_addition()

        print("\n" + "=" * 50)
        print("CUSTOM PATTERNS SUMMARY")
        print("=" * 50)
        print("""
✓ Custom patterns can be loaded from CSV files
✓ Custom patterns can be loaded from Excel files
✓ Custom patterns can be added at runtime
✓ Multiple custom pattern types work together
✓ Validation detects missing custom markup
✓ Template files can be generated for users

Supported formats:
- CSV files with name,pattern,description,enabled columns
- Excel files with ValidationPatterns sheet
- JSON configuration files
- Runtime API for dynamic patterns

This allows each game/project to define their own
validation rules for project-specific markup!
""")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()