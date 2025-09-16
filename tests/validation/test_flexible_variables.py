#!/usr/bin/env python3
"""Test flexible system variables validation"""

from game_translator.core.validation import TranslationValidator
from game_translator.core.models import TranslationEntry, TranslationStatus
import re


def test_variable_patterns():
    """Test different types of $variables$"""
    print("FLEXIBLE SYSTEM VARIABLES TEST")
    print("=" * 35)

    validator = TranslationValidator()

    test_cases = [
        "$test$",
        "$INPUT_ACTION_FIRE$",
        "$player_name$",
        "$Level123$",
        "$some-variable$",
        "$UI.menu.title$",
        "$very_LONG_Variable_Name_123$",
        "$ПривітУкраїнською$",  # Ukrainian text
        "$简体中文$",  # Chinese
    ]

    # Test our pattern
    pattern = re.compile(r'\$[^$]+\$')

    print("Testing pattern: r'\\$[^$]+\\$'")
    print("\nVariable examples:")

    for var in test_cases:
        matches = pattern.findall(var)
        status = "OK" if matches and matches[0] == var else "FAIL"
        print(f"  {status}: {var}")

    # Test validation with different variables
    print("\nValidation test:")

    examples = [
        {
            "source": "Press $test$ to continue",
            "translation": "Натисніть $test$ для продовження",
            "expected": "OK"
        },
        {
            "source": "Use $player_name$ and $Level123$",
            "translation": "Використовуйте $player_name$ та $Level123$",
            "expected": "OK"
        },
        {
            "source": "Click $UI.menu.title$ button",
            "translation": "Натисніть кнопку",  # Missing variable
            "expected": "ERROR"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. Testing validation:")
        print(f"   Source: {example['source']}")
        print(f"   Translation: {example['translation']}")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            error_found = any("system_variable" in issue.issue_type for issue in result.issues)
            print(f"   Result: {'ERROR (as expected)' if error_found else 'Unexpected error'}")
            for issue in result.issues:
                if "system_variable" in issue.issue_type:
                    print(f"   Details: {issue.message}")
        else:
            print(f"   Result: OK (as expected)")


if __name__ == "__main__":
    test_variable_patterns()