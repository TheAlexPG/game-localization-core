#!/usr/bin/env python3
"""Test translation validation system"""

from game_translator.core.validation import TranslationValidator, QualityMetrics
from game_translator.core.models import TranslationEntry, TranslationStatus


def create_test_entries():
    """Create sample translation entries for testing"""
    entries = []

    # Good translation
    entries.append(TranslationEntry(
        key="good_translation",
        source_text="Welcome to the game!",
        translated_text="Ласкаво просимо до гри!",
        status=TranslationStatus.TRANSLATED
    ))

    # Missing translation
    entries.append(TranslationEntry(
        key="missing_translation",
        source_text="Continue",
        translated_text=None,
        status=TranslationStatus.TRANSLATED  # Wrong status
    ))

    # Unchanged translation (non-technical)
    entries.append(TranslationEntry(
        key="unchanged_translation",
        source_text="Start Game",
        translated_text="Start Game",  # Same as source
        status=TranslationStatus.TRANSLATED
    ))

    # Placeholder mismatch
    entries.append(TranslationEntry(
        key="placeholder_issue",
        source_text="Level {level} completed with {score} points",
        translated_text="Рівень завершено з очками",  # Missing placeholders
        status=TranslationStatus.TRANSLATED
    ))

    # HTML tag mismatch
    entries.append(TranslationEntry(
        key="tag_issue",
        source_text="Click <b>here</b> to continue",
        translated_text="Натисніть тут для продовження",  # Missing <b> tags
        status=TranslationStatus.TRANSLATED
    ))

    # Too long translation
    entries.append(TranslationEntry(
        key="too_long",
        source_text="Yes",
        translated_text="Так, звичайно, я погоджуюся з цим рішенням повністю",  # Way too long
        status=TranslationStatus.TRANSLATED
    ))

    # Too short translation
    entries.append(TranslationEntry(
        key="too_short",
        source_text="This is a very detailed explanation of game mechanics",
        translated_text="Так",  # Too short
        status=TranslationStatus.TRANSLATED
    ))

    # Wrong language (English instead of Ukrainian)
    entries.append(TranslationEntry(
        key="wrong_language",
        source_text="Game Over",
        translated_text="Game Over",  # Should be Ukrainian
        status=TranslationStatus.TRANSLATED
    ))

    # Technical entry (should be unchanged)
    entries.append(TranslationEntry(
        key="technical_ok",
        source_text="API",
        translated_text="API",  # OK for technical terms
        status=TranslationStatus.TRANSLATED
    ))

    # Contains English words
    entries.append(TranslationEntry(
        key="english_words",
        source_text="Save your progress",
        translated_text="Save ваш прогрес",  # Mixed languages
        status=TranslationStatus.TRANSLATED
    ))

    # Repeated words
    entries.append(TranslationEntry(
        key="repeated_words",
        source_text="Collect coins",
        translated_text="Збирайте монети монети",  # Repeated word
        status=TranslationStatus.TRANSLATED
    ))

    # Placeholder text
    entries.append(TranslationEntry(
        key="placeholder_text",
        source_text="Enter your name",
        translated_text="Введіть ваше ім'я ???",  # Has placeholder
        status=TranslationStatus.TRANSLATED
    ))

    # TODO marker
    entries.append(TranslationEntry(
        key="todo_marker",
        source_text="Exit game",
        translated_text="TODO: translate this",
        status=TranslationStatus.TRANSLATED
    ))

    # Inconsistent translations (same source, different translations)
    entries.append(TranslationEntry(
        key="inconsistent_1",
        source_text="Exit",
        translated_text="Вихід",
        status=TranslationStatus.TRANSLATED
    ))

    entries.append(TranslationEntry(
        key="inconsistent_2",
        source_text="Exit",
        translated_text="Вийти",  # Different translation for same source
        status=TranslationStatus.TRANSLATED
    ))

    return entries


def test_individual_validation():
    """Test validation of individual entries"""
    print("Testing individual entry validation...")

    validator = TranslationValidator()
    entries = create_test_entries()

    for entry in entries:
        print(f"\n--- Validating: {entry.key} ---")
        result = validator.validate_entry(entry)

        if result.issues:
            print(f"  ERRORS ({len(result.issues)}):")
            for issue in result.issues:
                print(f"    - {issue.issue_type}: {issue.message}")
                if issue.suggestion:
                    print(f"      Suggestion: {issue.suggestion}")

        if result.warnings:
            print(f"  WARNINGS ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"    - {warning.issue_type}: {warning.message}")
                if warning.suggestion:
                    print(f"      Suggestion: {warning.suggestion}")

        if result.info:
            print(f"  INFO ({len(result.info)}):")
            for info in result.info:
                print(f"    - {info.issue_type}: {info.message}")

        if not result.issues and not result.warnings and not result.info:
            print("  OK: No issues found")


def test_project_validation():
    """Test project-wide validation"""
    print("\n" + "="*50)
    print("Testing project-wide validation...")

    # Create a mock project object
    class MockProject:
        def __init__(self, entries):
            self.entries = {entry.key: entry for entry in entries}

    validator = TranslationValidator()
    entries = create_test_entries()
    project = MockProject(entries)

    result = validator.validate_project(project)

    print(f"\n--- Project Validation Results ---")
    print(f"Checked {result.checked_count} entries")
    print(f"Found {len(result.issues)} errors, {len(result.warnings)} warnings, {len(result.info)} info items")

    if result.issues:
        print(f"\nERRORS ({len(result.issues)}):")
        for issue in result.issues[:10]:  # Show first 10
            print(f"  [{issue.key}] {issue.issue_type}: {issue.message}")

    if result.warnings:
        print(f"\nWARNINGS ({len(result.warnings)}):")
        for warning in result.warnings[:10]:  # Show first 10
            print(f"  [{warning.key}] {warning.issue_type}: {warning.message}")

    if result.info:
        print(f"\nINFO ({len(result.info)}):")
        for info in result.info[:5]:  # Show first 5
            print(f"  [{info.key}] {info.issue_type}: {info.message}")

    # Calculate quality metrics
    completion_rate = QualityMetrics.calculate_completion_rate(entries)
    quality_score = QualityMetrics.calculate_quality_score(result)
    quality_grade = QualityMetrics.get_quality_grade(quality_score)

    print(f"\n--- Quality Metrics ---")
    print(f"Completion Rate: {completion_rate:.1f}%")
    print(f"Quality Score: {quality_score:.1f}/100 (Grade: {quality_grade})")
    print(f"Summary: {result.get_summary()}")


def test_strict_mode():
    """Test strict mode validation"""
    print("\n" + "="*50)
    print("Testing strict mode...")

    validator_normal = TranslationValidator(strict_mode=False)
    validator_strict = TranslationValidator(strict_mode=True)

    # Test with unchanged translation
    entry = TranslationEntry(
        key="test_unchanged",
        source_text="Start Game",
        translated_text="Start Game",
        status=TranslationStatus.TRANSLATED
    )

    normal_result = validator_normal.validate_entry(entry)
    strict_result = validator_strict.validate_entry(entry)

    print("Normal mode:")
    print(f"  Errors: {len(normal_result.issues)}")
    print(f"  Warnings: {len(normal_result.warnings)}")

    print("Strict mode:")
    print(f"  Errors: {len(strict_result.issues)}")
    print(f"  Warnings: {len(strict_result.warnings)}")


def main():
    """Run all validation tests"""
    # Save results to file to avoid console encoding issues
    import sys
    from pathlib import Path

    output_file = Path("validation_test_results.txt")

    with open(output_file, 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f

        try:
            print("Translation Validation System Test")
            print("=" * 50)

            test_individual_validation()
            test_project_validation()
            test_strict_mode()

            print("\n" + "="*50)
            print("All validation tests completed successfully!")
            print("\nValidation system features:")
            print("  + Individual entry validation")
            print("  + Project-wide consistency checks")
            print("  + Placeholder and tag validation")
            print("  + Length and language checks")
            print("  + Quality scoring and grading")
            print("  + Strict/normal mode support")
            print("  + Detailed issue reporting with suggestions")

        except Exception as e:
            print(f"\nTest failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            sys.stdout = original_stdout

    print(f"Validation test completed. Results saved to: {output_file}")
    print("Check the file for detailed results with Ukrainian text.")


if __name__ == "__main__":
    main()