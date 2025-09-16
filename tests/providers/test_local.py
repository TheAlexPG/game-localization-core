#!/usr/bin/env python3
"""Test local provider with LM Studio"""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from game_translator import create_project, TranslationManager
from game_translator.providers import get_provider
from game_translator.importers import get_importer

# Load environment variables
load_dotenv()

def test_lm_studio_connection():
    """Test if LM Studio is running and accessible"""
    try:
        api_url = os.getenv("LOCAL_API_URL", "http://localhost:1234/v1/chat/completions")

        # Simple test request
        test_payload = {
            "model": "google/gemma-3-12b",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.3,
            "max_tokens": 50
        }

        print(f"Testing connection to LM Studio at: {api_url}")
        response = requests.post(
            api_url,
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and data["choices"]:
                print("   OK LM Studio is responding")
                return True
            else:
                print("   ERROR: Invalid response format from LM Studio")
                return False
        else:
            print(f"   ERROR: LM Studio returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ERROR: Cannot connect to LM Studio")
        print("   Make sure LM Studio is running on localhost:1234")
        print("   And that google/gemma-3-12b model is loaded")
        return False
    except Exception as e:
        print(f"   ERROR: Connection test failed: {e}")
        return False

def test_local_translation():
    """Test translation with local LM Studio provider"""
    print("Testing Local Provider with LM Studio (google/gemma-3-12b)")

    # Test connection first
    if not test_lm_studio_connection():
        print("\nSkipping local provider test - LM Studio not available")
        return False

    # Create test project
    print("\n1. Creating local test project...")
    project = create_project("local-test", source_lang="English", target_lang="Ukrainian")
    print(f"   OK Project created at: {project.project_dir}")

    # Create test data - smaller set for local model
    print("\n2. Creating test data for local model...")
    game_texts = {
        # Simple menu items
        "menu.play": "Play",
        "menu.quit": "Quit",
        "menu.settings": "Settings",

        # Basic UI
        "ui.health": "Health: {value}",
        "ui.level": "Level {level}",

        # Simple dialog
        "dialog.welcome": "Welcome, adventurer!",
        "dialog.confirm": "Are you sure?",

        # Items
        "item.sword": "Iron Sword",
        "item.potion": "Health Potion",

        # Technical (should be skipped)
        "tech.empty": "",
        "tech.number": "123"
    }

    # Save test data
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)
    local_file = test_dir / "local_texts.json"

    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(game_texts, f, indent=2)
    print(f"   OK Created {len(game_texts)} test entries")

    # Import data
    print("\n3. Importing test data...")
    importer = get_importer("json")
    entries_data = importer.import_file(local_file)
    result = project.import_source(entries_data)
    print(f"   OK Imported {result['new']} entries")

    # Setup simple glossary
    print("\n4. Setting up glossary...")
    project.glossary = {
        "Health": "Здоров'я",
        "Level": "Рівень",
        "Sword": "Меч",
        "Potion": "Зілля"
    }
    project.save_glossary()
    print(f"   OK Added {len(project.glossary)} glossary terms")

    # Setup Local provider
    print("\n5. Initializing Local provider...")
    try:
        api_url = os.getenv("LOCAL_API_URL", "http://localhost:1234/v1/chat/completions")
        provider = get_provider("local",
                              base_url=api_url,
                              model_name="google/gemma-3-12b")
        manager = TranslationManager(project, provider)

        print(f"   OK Provider initialized: {provider.get_info()['name']}")

        # Test connection
        if manager.validate_provider():
            print("   OK Provider connection validated")
        else:
            print("   WARNING: Provider validation failed, but continuing...")

    except Exception as e:
        print(f"   ERROR: Failed to initialize Local provider: {e}")
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
    print(f"   Est. time: {estimate['estimated_time_minutes']:.1f} minutes (local model may be slower)")

    # Start translation
    print(f"\n8. Starting Local model translation...")
    print("   Note: Local models are typically slower than cloud APIs")

    def progress_callback(progress, batch_num, total_batches):
        print(f"   Progress: {progress:.1f}% (batch {batch_num}/{total_batches})")

    start_time = time.time()
    translation_result = manager.translate_pending(
        batch_size=3,  # Smaller batches for local model
        max_retries=2,  # Fewer retries
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

    # Show example translations (save to file due to console encoding)
    print(f"\n11. Example Local model translations (saving to file...):")
    translated_entries = [e for e in project.entries.values()
                         if e.status.value == "translated"]

    # Save examples to file for review
    examples_file = test_dir / "local_examples.txt"
    with open(examples_file, 'w', encoding='utf-8') as f:
        f.write("Local Model Translation Examples (google/gemma-3-12b)\n")
        f.write("=" * 60 + "\n\n")

        for i, entry in enumerate(translated_entries, 1):
            f.write(f"{i}. Source: '{entry.source_text}'\n")
            f.write(f"   Translation: '{entry.translated_text}'\n\n")

    print(f"   Examples saved to: {examples_file}")
    print(f"   Total translated: {len(translated_entries)} entries")

    # Export results
    print(f"\n12. Exporting Local model results...")
    from game_translator.exporters import get_exporter

    excel_exporter = get_exporter("excel")
    export_data = project.export_for_review()
    excel_path = test_dir / "local_translation_results.xlsx"
    excel_exporter.export(export_data, excel_path, project.glossary)
    print(f"   OK Excel export: {excel_path}")

    # Create version
    version = project.create_snapshot(bump_type="minor")
    print(f"   OK Version snapshot: {version}")

    print(f"\nSUCCESS: Local provider test completed!")
    print(f"\nLocal model quality check:")
    print(f"   - {examples_file} (translation examples)")
    print(f"   - {excel_path} (full results)")
    print(f"   - Compare with OpenAI results for quality assessment")

    return True

if __name__ == "__main__":
    try:
        test_local_translation()
    except Exception as e:
        print(f"\nERROR: Local test failed: {e}")
        import traceback
        traceback.print_exc()