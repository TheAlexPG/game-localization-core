#!/usr/bin/env python3
"""Test simplified validation system"""

from game_translator.core.validation import TranslationValidator, QualityMetrics
from game_translator.core.models import TranslationEntry, TranslationStatus


def main():
    """Demo of simplified validation system"""
    print("Simplified Translation Validation System")
    print("=" * 50)

    # Create test entries
    entries = [
        # 1. Good translation - no issues
        TranslationEntry(
            key="good_example",
            source_text="Welcome to the game!",
            translated_text="¡Bienvenido al juego!",  # Spanish example
            status=TranslationStatus.TRANSLATED
        ),

        # 2. Empty translation
        TranslationEntry(
            key="empty_translation",
            source_text="Continue",
            translated_text="",  # Empty
            status=TranslationStatus.TRANSLATED  # Wrong status
        ),

        # 3. Unchanged translation (exact match)
        TranslationEntry(
            key="unchanged_exact",
            source_text="Start Game",
            translated_text="Start Game",  # Identical
            status=TranslationStatus.TRANSLATED
        ),

        # 4. Technical term unchanged (OK)
        TranslationEntry(
            key="technical_term",
            source_text="API",
            translated_text="API",  # OK for technical terms
            status=TranslationStatus.TRANSLATED
        ),

        # 5. Placeholder mismatch
        TranslationEntry(
            key="placeholder_error",
            source_text="Level {level} with {score} points",
            translated_text="Nivel con puntos",  # Missing placeholders
            status=TranslationStatus.TRANSLATED
        ),

        # 6. HTML tag mismatch
        TranslationEntry(
            key="tag_error",
            source_text="Click <b>here</b> to continue",
            translated_text="Haz clic aquí para continuar",  # Missing tags
            status=TranslationStatus.TRANSLATED
        ),

        # 7. Repeated words
        TranslationEntry(
            key="repeated_words",
            source_text="Collect coins",
            translated_text="Recoger monedas monedas",  # Repeated word
            status=TranslationStatus.TRANSLATED
        ),

        # 8. TODO marker
        TranslationEntry(
            key="todo_marker",
            source_text="Exit game",
            translated_text="TODO: translate this",
            status=TranslationStatus.TRANSLATED
        ),

        # 9. Placeholder text
        TranslationEntry(
            key="placeholder_text",
            source_text="Enter name",
            translated_text="Ingresa nombre ???",  # Has ??? placeholder
            status=TranslationStatus.TRANSLATED
        ),

        # 10. Whitespace formatting issue
        TranslationEntry(
            key="formatting_issue",
            source_text=" Start ",  # Has leading/trailing spaces
            translated_text="Comenzar",  # Different whitespace
            status=TranslationStatus.TRANSLATED
        ),
    ]

    validator = TranslationValidator()

    print("Testing individual entries:")
    print("-" * 30)

    for entry in entries:
        print(f"\n[{entry.key}]")
        print(f"  Source: '{entry.source_text}'")
        print(f"  Translation: '{entry.translated_text}'")

        result = validator.validate_entry(entry)

        if result.issues:
            print(f"  ERRORS:")
            for issue in result.issues:
                print(f"    - {issue.issue_type}: {issue.message}")

        if result.warnings:
            print(f"  WARNINGS:")
            for warning in result.warnings:
                print(f"    - {warning.issue_type}: {warning.message}")

        if result.info:
            print(f"  INFO:")
            for info in result.info:
                print(f"    - {info.issue_type}: {info.message}")

        if not result.issues and not result.warnings and not result.info:
            print("  OK: No issues")

    # Test project-wide validation
    print("\n" + "=" * 50)
    print("Project-wide validation:")
    print("-" * 30)

    class MockProject:
        def __init__(self, entries):
            self.entries = {entry.key: entry for entry in entries}

    project = MockProject(entries)
    result = validator.validate_project(project)

    print(f"Checked {result.checked_count} entries")
    print(f"Found {len(result.issues)} errors, {len(result.warnings)} warnings")

    completion_rate = QualityMetrics.calculate_completion_rate(entries)
    quality_score = QualityMetrics.calculate_quality_score(result)
    quality_grade = QualityMetrics.get_quality_grade(quality_score)

    print(f"Completion Rate: {completion_rate:.1f}%")
    print(f"Quality Score: {quality_score:.1f}/100 (Grade: {quality_grade})")


if __name__ == "__main__":
    main()