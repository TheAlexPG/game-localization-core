#!/usr/bin/env python3
"""Simple test of custom patterns without unicode output"""

from pathlib import Path
from game_translator.core.validation import TranslationValidator
from game_translator.core.custom_patterns import CustomPatternsManager
from game_translator.core.models import TranslationEntry, TranslationStatus


def main():
    """Test basic custom patterns functionality"""
    print("Testing custom patterns...")

    # 1. Create simple CSV
    csv_content = """name,pattern,description,enabled
square_brackets,\\[\\w+\\],"Square brackets",true
special_ids,#\\d{4,6},"Special IDs",true"""

    csv_path = Path("test_patterns.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content)

    # 2. Load patterns
    manager = CustomPatternsManager()
    patterns = manager.load_from_csv(csv_path)
    print(f"Loaded {len(patterns)} custom patterns")

    # 3. Create validator
    custom_patterns_dict = manager.get_patterns_for_validator()
    validator = TranslationValidator(custom_patterns=custom_patterns_dict)

    # 4. Test validation
    entry = TranslationEntry(
        key="test",
        source_text="Press [FIRE] and check item #1234",
        translated_text="Press and check item",  # Missing [FIRE] and #1234
        status=TranslationStatus.TRANSLATED
    )

    result = validator.validate_entry(entry)

    print(f"Found {len(result.issues)} validation errors:")
    for issue in result.issues:
        if "custom_" in issue.issue_type:
            print(f"  - Custom pattern error: {issue.issue_type}")

    # 5. Test runtime addition
    validator.add_custom_pattern("pipe_vars", r'\|[A-Z_]+\|', "Pipe variables")

    entry2 = TranslationEntry(
        key="test2",
        source_text="Your |HEALTH| is low",
        translated_text="Your health is low",  # Missing |HEALTH|
        status=TranslationStatus.TRANSLATED
    )

    result2 = validator.validate_entry(entry2)
    print(f"Runtime pattern test: {len(result2.issues)} errors found")

    # 6. Clean up
    csv_path.unlink()
    print("Test completed successfully!")


if __name__ == "__main__":
    main()