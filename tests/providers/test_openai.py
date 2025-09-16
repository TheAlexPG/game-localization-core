#!/usr/bin/env python3
"""Test with real OpenAI provider"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from game_translator import create_project, TranslationManager
from game_translator.providers import get_provider
from game_translator.importers import get_importer

# Load environment variables
load_dotenv()

def test_openai_translation():
    """Test translation with real OpenAI API"""
    print("Testing Real OpenAI Translation (gpt-4o-mini)")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        return False

    print(f"   OK OpenAI API key found (length: {len(api_key)})")

    # Create test project
    print("\n1. Creating OpenAI test project...")
    project = create_project("openai-test", source_lang="English", target_lang="Ukrainian")
    print(f"   OK Project created at: {project.project_dir}")

    # Create realistic game texts for testing
    print("\n2. Creating realistic game text samples...")
    game_texts = {
        # Menu items
        "menu.new_game": "New Game",
        "menu.continue": "Continue",
        "menu.load_game": "Load Game",
        "menu.settings": "Settings",
        "menu.quit": "Quit Game",

        # UI elements
        "ui.health": "Health: {current}/{max}",
        "ui.mana": "Mana: {current}/{max}",
        "ui.level": "Level {level}",
        "ui.experience": "Experience: {exp}/{next_level}",

        # Dialog samples
        "dialog.welcome": "Welcome, brave adventurer! Your quest begins here.",
        "dialog.merchant": "What can I do for you today? I have the finest weapons and armor!",
        "dialog.quest_complete": "Excellent work! You have completed the quest successfully.",

        # Items
        "item.iron_sword": "Iron Sword",
        "item.health_potion": "Health Potion",
        "item.magic_scroll": "Scroll of Lightning",
        "item.dragon_scale": "Ancient Dragon Scale",

        # Locations
        "location.village": "Riverside Village",
        "location.dungeon": "Forgotten Catacombs",
        "location.forest": "Enchanted Forest",

        # Skills/Spells
        "skill.fireball": "Fireball",
        "skill.heal": "Divine Healing",
        "skill.stealth": "Shadow Step"
    }

    # Save test data
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)
    openai_file = test_dir / "openai_texts.json"

    with open(openai_file, 'w', encoding='utf-8') as f:
        json.dump(game_texts, f, indent=2)
    print(f"   OK Created {len(game_texts)} realistic game texts")

    # Import data
    print("\n3. Importing game texts...")
    importer = get_importer("json")
    entries_data = importer.import_file(openai_file)
    result = project.import_source(entries_data)
    print(f"   OK Imported {result['new']} entries")

    # Setup comprehensive glossary
    print("\n4. Setting up game glossary...")
    project.glossary = {
        # Character/Story terms
        "Adventurer": "Авантюрист",
        "Quest": "Квест",
        "Dragon": "Дракон",

        # Game mechanics
        "Health": "Здоров'я",
        "Mana": "Мана",
        "Level": "Рівень",
        "Experience": "Досвід",

        # Items
        "Sword": "Меч",
        "Potion": "Зілля",
        "Scroll": "Сувій",
        "Scale": "Луска",

        # Locations
        "Village": "Село",
        "Forest": "Ліс",
        "Dungeon": "Підземелля",
        "Catacombs": "Катакомби",

        # Magic/Skills
        "Fireball": "Вогняна куля",
        "Healing": "Зцілення",
        "Shadow": "Тінь",
        "Lightning": "Блискавка"
    }
    project.save_glossary()
    print(f"   OK Added {len(project.glossary)} glossary terms")

    # Setup OpenAI provider
    print("\n5. Initializing OpenAI provider...")
    try:
        provider = get_provider("openai",
                              model_name="gpt-4o-mini",  # Using the specified model
                              api_key=api_key)
        manager = TranslationManager(project, provider)

        print(f"   OK Provider initialized: {provider.get_info()['name']}")

        # Test connection
        if manager.validate_provider():
            print("   OK Provider connection validated")
        else:
            print("   WARNING: Provider validation failed, but continuing...")

    except Exception as e:
        print(f"   ERROR: Failed to initialize OpenAI provider: {e}")
        return False

    # Show pre-translation stats
    stats = project.get_progress_stats()
    print(f"\n6. Pre-translation stats:")
    print(f"   Total entries: {stats.total}")
    print(f"   Pending: {stats.pending}")
    print(f"   Completion: {stats.completion_rate:.1f}%")

    # Estimate cost/time
    estimate = manager.estimate_cost(stats.pending)
    print(f"\n7. Translation estimate:")
    print(f"   Entries: {estimate['entries']}")
    print(f"   Est. characters: {estimate['estimated_chars']}")
    print(f"   Est. time: {estimate['estimated_time_minutes']:.1f} minutes")

    # Start translation
    print(f"\n8. Starting OpenAI translation...")
    print("   This will make real API calls and may take a minute...")

    def progress_callback(progress, batch_num, total_batches):
        print(f"   Progress: {progress:.1f}% (batch {batch_num}/{total_batches})")

    start_time = time.time()
    translation_result = manager.translate_pending(
        batch_size=5,  # Small batches for OpenAI
        max_retries=3,
        skip_technical=True,
        progress_callback=progress_callback
    )
    end_time = time.time()

    # Show detailed results
    print(f"\n9. Translation results:")
    print(f"   Processed: {translation_result['processed']}")
    print(f"   Successful: {translation_result['successful']}")
    print(f"   Failed: {translation_result['failed']}")
    print(f"   Skipped: {translation_result['skipped']}")
    print(f"   Success rate: {translation_result['success_rate']:.1f}%")
    print(f"   Total time: {end_time - start_time:.1f}s")

    # Show final stats
    final_stats = project.get_progress_stats()
    print(f"\n10. Final project stats:")
    print(f"   Completion: {final_stats.completion_rate:.1f}%")
    print(f"   Translated: {final_stats.translated}/{final_stats.total}")

    # Show example translations (save to file due to console encoding issues)
    print(f"\n11. Example OpenAI translations (saving to file...):")
    translated_entries = [e for e in project.entries.values()
                         if e.status.value == "translated"]

    # Save examples to file for review
    examples_file = test_dir / "openai_examples.txt"
    with open(examples_file, 'w', encoding='utf-8') as f:
        f.write("OpenAI Translation Examples\n")
        f.write("=" * 50 + "\n\n")

        for i, entry in enumerate(translated_entries[:8], 1):
            f.write(f"{i}. Source: '{entry.source_text}'\n")
            f.write(f"   Translation: '{entry.translated_text}'\n\n")

    print(f"   Examples saved to: {examples_file}")
    print(f"   Total translated: {len(translated_entries)} entries")

    # Export results
    print(f"12. Exporting OpenAI results...")
    from game_translator.exporters import get_exporter

    excel_exporter = get_exporter("excel")
    export_data = project.export_for_review()
    excel_path = test_dir / "openai_translation_results.xlsx"
    excel_exporter.export(export_data, excel_path, project.glossary)
    print(f"   OK Excel export: {excel_path}")

    # Create version
    version = project.create_snapshot(bump_type="minor")
    print(f"   OK Version snapshot: {version}")

    print(f"\nSUCCESS: OpenAI translation test completed!")
    print(f"\nQuality check - Review these translations:")
    print(f"   - {excel_path}")
    print(f"   - Look for natural Ukrainian translations")
    print(f"   - Verify glossary terms were used consistently")
    print(f"   - Check that formatting/markup was preserved")

    return True

if __name__ == "__main__":
    import time

    try:
        test_openai_translation()
    except Exception as e:
        print(f"\nERROR: OpenAI test failed: {e}")
        import traceback
        traceback.print_exc()