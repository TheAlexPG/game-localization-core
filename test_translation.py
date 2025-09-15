#!/usr/bin/env python3
"""Test translation functionality (Phase 4)"""

import json
from pathlib import Path
from game_translator import create_project, TranslationManager
from game_translator.providers import get_provider
from game_translator.importers import get_importer

def test_translation_workflow():
    """Test AI translation workflow"""
    print("Testing AI Translation Integration")

    # Create test project
    print("\n1. Creating test project...")
    project = create_project("translation-test", source_lang="English", target_lang="Ukrainian")
    print(f"   OK Project created at: {project.project_dir}")

    # Create more comprehensive test data
    print("\n2. Creating test data...")
    game_texts = {
        "menu.play": "Play Game",
        "menu.settings": "Settings",
        "menu.options": "Options",
        "menu.quit": "Quit",
        "ui.health": "Health: {value}/100",
        "ui.level": "Level {level}",
        "dialog.welcome": "Welcome to the adventure!",
        "dialog.confirm": "Are you sure you want to quit?",
        "item.sword": "Iron Sword",
        "item.potion": "Health Potion",
        "location.forest": "Enchanted Forest",
        "skill.fireball": "Fireball Spell",
        # Technical entries (should be skipped)
        "tech.empty": "",
        "tech.number": "123",
        "tech.tag": "<page=5>"
    }

    # Save test data
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)
    sample_file = test_dir / "game_texts.json"

    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(game_texts, f, indent=2)
    print(f"   OK Test data saved: {len(game_texts)} entries")

    # Import data
    print("\n3. Importing test data...")
    importer = get_importer("json")
    entries_data = importer.import_file(sample_file)
    result = project.import_source(entries_data)
    print(f"   OK Imported {result['new']} entries")

    # Show initial stats
    stats = project.get_progress_stats()
    print(f"   Stats: {stats.translated}/{stats.total} ({stats.completion_rate:.1f}%)")

    # Setup glossary
    print("\n4. Setting up glossary...")
    project.glossary = {
        "Health": "Здоров'я",
        "Level": "Рівень",
        "Adventure": "Пригода",
        "Forest": "Ліс",
        "Sword": "Меч",
        "Potion": "Зілля",
        "Spell": "Заклинання"
    }
    project.save_glossary()
    print(f"   OK Added {len(project.glossary)} glossary terms")

    # Setup AI provider (mock for testing)
    print("\n5. Setting up AI provider...")
    provider = get_provider("mock", delay=0.1)  # Fast mock provider
    manager = TranslationManager(project, provider)

    # Validate provider
    if manager.validate_provider():
        print("   OK Provider validated")
        provider_info = manager.get_provider_info()
        print(f"   Provider: {provider_info['name']} ({provider_info['model']})")
    else:
        print("   ERROR: Provider validation failed")
        return False

    # Estimate translation
    pending_count = len(project.get_pending_entries())
    estimate = manager.estimate_cost(pending_count)
    print(f"\n6. Translation estimate:")
    print(f"   Entries to translate: {estimate['entries']}")
    print(f"   Estimated time: {estimate['estimated_time_minutes']:.1f} minutes")

    # Translate entries
    print(f"\n7. Translating {pending_count} entries...")

    def progress_callback(progress, batch_num, total_batches):
        print(f"   Progress: {progress:.1f}% (batch {batch_num}/{total_batches})")

    translation_result = manager.translate_pending(
        batch_size=5,
        max_retries=2,
        skip_technical=True,
        progress_callback=progress_callback
    )

    # Show results
    print(f"\n8. Translation results:")
    print(f"   Processed: {translation_result['processed']}")
    print(f"   Successful: {translation_result['successful']}")
    print(f"   Failed: {translation_result['failed']}")
    print(f"   Skipped: {translation_result['skipped']}")
    print(f"   Success rate: {translation_result['success_rate']:.1f}%")
    print(f"   Duration: {translation_result['duration_seconds']:.1f}s")

    # Show updated stats
    final_stats = project.get_progress_stats()
    print(f"\n9. Final project stats:")
    print(f"   Total entries: {final_stats.total}")
    print(f"   Translated: {final_stats.translated}")
    print(f"   Pending: {final_stats.pending}")
    print(f"   Completion: {final_stats.completion_rate:.1f}%")

    # Show some example translations
    print(f"\n10. Example translations:")
    translated_entries = project.get_entries_by_status(project.entries["menu.play"].status.__class__.TRANSLATED)

    for entry in translated_entries[:5]:  # Show first 5
        print(f"   '{entry.source_text}' -> '{entry.translated_text}'")

    # Export results
    print(f"\n11. Exporting results...")
    from game_translator.exporters import get_exporter

    # Export to Excel with translations
    excel_exporter = get_exporter("excel")
    export_data = project.export_for_review()
    excel_path = test_dir / "translated_review.xlsx"
    excel_exporter.export(export_data, excel_path, project.glossary)
    print(f"   OK Excel export: {excel_path}")

    # Create version snapshot
    print(f"\n12. Creating version snapshot...")
    version = project.create_snapshot(bump_type="minor")
    print(f"   OK Version created: {version}")

    print(f"\nSUCCESS: Translation workflow completed!")
    print(f"Files created:")
    print(f"   - {excel_path} (Translation review)")
    print(f"   - {project.project_dir}/project.json (Project state)")
    print(f"   - {project.project_dir}/.versions/v{version}.json (Version snapshot)")

    return True

if __name__ == "__main__":
    try:
        test_translation_workflow()
    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()