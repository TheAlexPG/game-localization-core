#!/usr/bin/env python3
"""Basic test to verify core functionality"""

import json
from pathlib import Path
from game_translator import create_project
from game_translator.importers import get_importer
from game_translator.exporters import get_exporter

def test_basic_workflow():
    """Test basic project workflow"""
    print("Testing Game Translator Core System")

    # Create test project
    print("\n1. Creating test project...")
    project = create_project("test-game", source_lang="en", target_lang="uk")
    print(f"   OK Project created at: {project.project_dir}")

    # Create sample JSON data
    print("\n2. Creating sample data...")
    sample_data = {
        "menu.play": "Play Game",
        "menu.settings": "Settings",
        "menu.quit": "Quit",
        "dialog.confirm": "Are you sure?",
        "ui.health": "Health: {value}",
        "story.intro": "Welcome to our adventure!"
    }

    # Save sample data to file
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)

    sample_file = test_dir / "sample.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    print(f"   OK Sample data saved to: {sample_file}")

    # Import data
    print("\n3. Importing data...")
    importer = get_importer("json")
    entries_data = importer.import_file(sample_file)
    result = project.import_source(entries_data)
    print(f"   OK Imported {result['new']} new entries")

    # Show progress
    stats = project.get_progress_stats()
    print(f"   Stats: {stats.translated}/{stats.total} ({stats.completion_rate:.1f}%)")

    # Add some translations manually
    print("\n4. Adding sample translations...")
    translations = {
        "menu.play": "Graty",
        "menu.settings": "Nalashtuvannia",
        "dialog.confirm": "Vy vpevneni?"
    }

    imported = project.import_translations(translations)
    print(f"   OK Added {imported} translations")

    # Update progress
    stats = project.get_progress_stats()
    print(f"   Stats: {stats.translated}/{stats.total} ({stats.completion_rate:.1f}%)")

    # Add glossary
    print("\n5. Adding glossary...")
    project.glossary = {
        "Health": "Zdorovya",
        "Settings": "Nalashtuvannia",
        "Adventure": "Pryhoda"
    }
    project.save_glossary()
    print(f"   OK Added {len(project.glossary)} glossary terms")

    # Export to Excel
    print("\n6. Exporting to Excel...")
    excel_exporter = get_exporter("excel")
    export_data = project.export_for_review()
    excel_path = test_dir / "translation_review.xlsx"
    excel_exporter.export(export_data, excel_path, project.glossary)
    print(f"   OK Exported to: {excel_path}")

    # Export to CSV
    print("\n7. Exporting to CSV...")
    csv_exporter = get_exporter("csv")
    csv_path = test_dir / "translation_review.csv"
    csv_exporter.export(export_data, csv_path, project.glossary)
    print(f"   OK Exported to: {csv_path}")

    # Export to JSON
    print("\n8. Exporting to JSON...")
    json_exporter = get_exporter("json")
    json_path = test_dir / "translation_export.json"
    json_exporter.export(export_data, json_path)
    print(f"   OK Exported to: {json_path}")

    # Create version snapshot
    print("\n9. Creating version snapshot...")
    version = project.create_snapshot()
    print(f"   OK Created version: {version}")

    print("\nSUCCESS: All tests passed! Core system is working.")
    print(f"\nTest files created in: {test_dir.absolute()}")
    print("   - translation_review.xlsx (Excel with formatting)")
    print("   - translation_review.csv (CSV format)")
    print("   - translation_export.json (JSON export)")

    return True

if __name__ == "__main__":
    try:
        test_basic_workflow()
    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()