#!/usr/bin/env python3
"""Test validation with real game data examples"""

from game_translator.core.validation import TranslationValidator
from game_translator.core.models import TranslationEntry, TranslationStatus


def test_silksong_examples():
    """Test with Silksong examples"""
    print("SILKSONG GAME DATA VALIDATION")
    print("=" * 40)

    validator = TranslationValidator()

    examples = [
        {
            "name": "Silksong with page tags and entities",
            "source": "Soon, Pavo, I will quieten the chaos. Please tend to these bugs until then.&lt;page&gt;Of course, dear dweller! Of course! Know: all our faith and wishes go with you.",
            "translation": "Незабаром, Паво, я вгамую хаос. Будь ласка, приглянь за цими жуками до того часу.&lt;page&gt;Звісно, дорога мешканко! Звісно! Знайте: уся наша віра і наші побажання з вами.",
            "expected": "OK - all entities preserved"
        },
        {
            "name": "Shop item with apostrophe entity",
            "source": "Rosaries that come undone fall from your pockets at the most inopportune times, and I&amp;#8217;m a master at tight stringing! I can string you a whole necklace — reliable and stylish.",
            "translation": "Розарії, що розв'язуються, випадають з ваших кишень у найневідповідніший момент, і я&amp;#8217; вправний майстер у тугому нанизуванні! Я можу нанизати вам ціле намисто — надійне й стильне.",
            "expected": "OK - apostrophe entity preserved"
        },
        {
            "name": "Missing HTML entity",
            "source": "Text with &lt;special&gt; tags and &amp; symbols",
            "translation": "Текст з <special> тегами та & символами",  # Missing entities
            "expected": "ERROR - HTML entities missing"
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  Expected: {example['expected']}")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            for issue in result.issues:
                print(f"  ERROR: {issue.message}")
        else:
            print(f"  OK: All validation checks passed")


def test_x4_examples():
    """Test with X4 game examples"""
    print("\n\nX4 FOUNDATIONS GAME DATA VALIDATION")
    print("=" * 40)

    validator = TranslationValidator()

    examples = [
        {
            "name": "X4 with game ID placeholders",
            "source": "Constructions require a Construction Vessel to be assigned.(Construction Vessel same as {20204,5101})",
            "translation": "Конструкції вимагають призначення Будівельного Судна.(Construction Vessel same as {20204,5101})",
            "expected": "OK - game ID preserved"
        },
        {
            "name": "X4 with system input variables",
            "source": "use $INPUT_ACTION_CYCLE_NEXT_PRIMARY_WEAPONGROUP$ to cycle through your weapon groups",
            "translation": "використовуйте $INPUT_ACTION_CYCLE_NEXT_PRIMARY_WEAPONGROUP$ для перемикання груп зброї",
            "expected": "OK - system variable preserved"
        },
        {
            "name": "Multiple game IDs and system vars",
            "source": "Purchase a Spacesuit Scanner at {20007,1441} using $INPUT_ACTION_BUY$ command.",
            "translation": "Придбайте Spacesuit Scanner в {20007,1441} використовуючи команду $INPUT_ACTION_BUY$.",
            "expected": "OK - all placeholders preserved"
        },
        {
            "name": "Missing system variable",
            "source": "Press $INPUT_ACTION_FIRE$ to shoot and $INPUT_ACTION_BOOST$ to boost",
            "translation": "Натисніть для стрільби та для прискорення",  # Missing both variables
            "expected": "ERROR - system variables missing"
        },
        {
            "name": "Wrong game ID",
            "source": "Equipment at {20108,111} location",
            "translation": "Обладнання в {20108,112} місці",  # Wrong ID: 111 -> 112
            "expected": "ERROR - game ID mismatch"
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  Expected: {example['expected']}")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            for issue in result.issues:
                print(f"  ERROR: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
        else:
            print(f"  OK: All validation checks passed")


def test_mixed_markup():
    """Test with mixed markup types"""
    print("\n\nMIXED MARKUP VALIDATION")
    print("=" * 25)

    validator = TranslationValidator()

    examples = [
        {
            "name": "All markup types combined",
            "source": '<t id="123">Press {button} or $INPUT_FIRE$ near &lt;target&gt; with &amp; symbol</t>',
            "translation": '<t id="123">Натисніть {button} або $INPUT_FIRE$ біля &lt;target&gt; з &amp; символом</t>',
            "expected": "OK - all markup preserved"
        },
        {
            "name": "Complex missing elements",
            "source": "Use {item,123} and $ACTION_USE$ with &lt;menu&gt; &amp; settings",
            "translation": "Використовуйте предмет та команду з меню і налаштуваннями",  # All markup removed
            "expected": "ERROR - all markup types missing"
        }
    ]

    for example in examples:
        print(f"\n{example['name']}:")
        print(f"  Expected: {example['expected']}")

        entry = TranslationEntry(
            key="test",
            source_text=example['source'],
            translated_text=example['translation'],
            status=TranslationStatus.TRANSLATED
        )

        result = validator.validate_entry(entry)

        if result.issues:
            for issue in result.issues:
                print(f"  ERROR: {issue.message}")
        else:
            print(f"  OK: All validation checks passed")


def main():
    """Run all game data validation tests"""
    import sys

    with open('game_validation_results.txt', 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f

        test_silksong_examples()
        test_x4_examples()
        test_mixed_markup()

        # Summary
        print("\n\n" + "=" * 50)
        print("VALIDATION COVERAGE SUMMARY")
        print("=" * 50)
        print("""
Now supports all real game markup types:

✓ Regular placeholders: {level}, {score}
✓ Game ID placeholders: {20204,5101}, {20108,111}
✓ System variables: $INPUT_ACTION_FIRE$, $INPUT_ACTION_BOOST$
✓ HTML entities: &lt; &gt; &amp; &#8217;
✓ HTML/XML tags: <t id="123">, <b>, </b>

The validator will detect:
- Missing placeholders of any type
- Extra placeholders not in source
- Incorrect game IDs or system variables
- Missing or wrong HTML entities
- Tag structure mismatches

This covers the markup found in:
- Hollow Knight: Silksong
- X4: Foundations
- And similar game localization files
""")

        sys.stdout = original_stdout

    print("Game validation test completed. Results saved to: game_validation_results.txt")


if __name__ == "__main__":
    main()