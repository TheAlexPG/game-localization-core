#!/usr/bin/env python3
"""
Context System Examples for Game Translator

This file demonstrates various ways to use the context system
for better AI translations and term extraction.
"""

from game_translator import create_project, get_provider, TranslationProject

def example_1_basic_context():
    """Example 1: Setting basic project context"""
    print("=== Example 1: Basic Project Context ===")

    # Create project
    project = create_project("fantasy-rpg", "en", "uk")

    # Set basic context
    project.set_project_context({
        "genre": "Fantasy RPG",
        "tone": "epic and serious",
        "audience": "young adults 18-30",
        "preserve_ids": True
    })

    # View context
    context = project.get_project_context()
    print("Project context set:", context)

    return project

def example_2_context_from_file():
    """Example 2: Loading context from markdown file"""
    print("\n=== Example 2: Context from File ===")

    project = create_project("dark-souls-like", "en", "uk")

    # Set context from file (will look for PROJECT_CONTEXT.md in project directory)
    project.set_project_context(from_file="examples/PROJECT_CONTEXT.md")

    # Display formatted context
    formatted = project.format_context_for_prompt("project")
    print("Formatted context for AI:")
    print(formatted[:200] + "..." if len(formatted) > 200 else formatted)

    return project

def example_3_glossary_context():
    """Example 3: Setting up glossary context"""
    print("\n=== Example 3: Glossary Context ===")

    project = create_project("mmorpg", "en", "uk")

    # Set glossary context for term extraction
    project.set_glossary_context({
        "extract_npcs": True,
        "extract_locations": True,
        "extract_items": True,
        "extract_skills": True,
        "skip_common_terms": True,
        "adaptation_style": "phonetic_for_names",
        "preserve_magical_names": True
    })

    # Also set from file
    project.set_glossary_context(from_file="examples/GLOSSARY_CONTEXT.md")

    context = project.get_glossary_context()
    print("Glossary context:", list(context.keys()))

    return project

def example_4_translation_with_context():
    """Example 4: Translation using context"""
    print("\n=== Example 4: Translation with Context ===")

    project = create_project("story-game", "en", "uk")

    # Set detailed context
    project.set_project_context({
        "genre": "Narrative Adventure",
        "tone": "emotional and introspective",
        "audience": "mature players",
        "themes": ["loss", "redemption", "hope"],
        "setting": "post-apocalyptic world",
        "character_style": "realistic and grounded"
    })

    # Add some sample entries
    sample_entries = [
        {"key": "intro_text", "source_text": "Welcome to the wasteland, survivor."},
        {"key": "hope_message", "source_text": "Even in darkness, hope endures."},
        {"key": "companion_greeting", "source_text": "I'm glad you're still alive, friend."}
    ]

    project.import_source(sample_entries)

    # Context will be automatically included in translation prompts
    print("Sample entries imported with context")
    print("Context will enhance translation quality")

    return project

def example_5_context_management():
    """Example 5: Dynamic context management"""
    print("\n=== Example 5: Context Management ===")

    project = create_project("action-rpg", "en", "uk")

    # Start with basic context
    project.set_project_context({"genre": "Action RPG"})

    # Add more context incrementally
    project.add_project_context("tone", "fast-paced and exciting")
    project.add_project_context("combat_style", "hack and slash")
    project.add_project_context("magic_system", "elemental based")

    # Add glossary context
    project.add_glossary_context("extract_spells", True)
    project.add_glossary_context("extract_weapons", True)
    project.add_glossary_context("translate_elements", "fire→вогонь,ice→лід,lightning→блискавка")

    # View all context
    print("Final project context:", project.get_project_context())
    print("Final glossary context:", project.get_glossary_context())

    return project

def example_6_context_in_prompt():
    """Example 6: How context appears in AI prompts"""
    print("\n=== Example 6: Context in AI Prompts ===")

    project = create_project("demo-game", "en", "uk")

    # Set rich context
    project.set_project_context({
        "genre": "Cyberpunk RPG",
        "setting": "Neo-Tokyo 2077",
        "tone": "noir and gritty",
        "themes": ["corporate control", "human enhancement", "identity"],
        "language_style": "street slang mixed with technical terms"
    })

    # Show how context gets formatted for AI
    formatted_context = project.format_context_for_prompt("project")

    print("Context as it appears in AI prompt:")
    print("-" * 50)
    print(formatted_context)
    print("-" * 50)

    return project

def example_7_complete_workflow():
    """Example 7: Complete workflow with context"""
    print("\n=== Example 7: Complete Workflow ===")

    # 1. Create project
    project = create_project("indie-platformer", "en", "uk")

    # 2. Set comprehensive context
    project.set_project_context({
        "genre": "Indie Platformer",
        "art_style": "pixel art",
        "tone": "whimsical and lighthearted",
        "audience": "all ages",
        "mechanics": ["jumping", "collecting", "power-ups"],
        "character": "anthropomorphic animals"
    })

    project.set_glossary_context({
        "extract_characters": True,
        "extract_power_ups": True,
        "extract_locations": True,
        "style": "playful and cute",
        "naming_convention": "simple and memorable"
    })

    # 3. Import sample data
    sample_data = [
        {"key": "player_name", "source_text": "Fuzzy the Rabbit"},
        {"key": "power_up", "source_text": "Super Jump Boots"},
        {"key": "level_name", "source_text": "Candy Mountain Heights"},
        {"key": "tutorial", "source_text": "Press SPACE to jump over obstacles!"}
    ]

    project.import_source(sample_data)

    # 4. Show how context would be used
    print("Project setup complete:")
    print(f"- Entries: {len(project.entries)}")
    print(f"- Project context keys: {list(project.get_project_context().keys())}")
    print(f"- Glossary context keys: {list(project.get_glossary_context().keys())}")

    # 5. Demonstrate translation would use this context
    print("\nContext-aware translation ready!")
    print("AI will understand this is a whimsical platformer for all ages")

    return project

if __name__ == "__main__":
    """Run all examples"""
    print("Game Translator Context System Examples")
    print("=" * 50)

    # Run examples
    examples = [
        example_1_basic_context,
        example_2_context_from_file,
        example_3_glossary_context,
        example_4_translation_with_context,
        example_5_context_management,
        example_6_context_in_prompt,
        example_7_complete_workflow
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Error in {example_func.__name__}: {e}")

        print("\n" + "="*50)

    print("All examples completed!")
    print("\nTo use context in your own projects:")
    print("1. Set project context for general game information")
    print("2. Set glossary context for term extraction rules")
    print("3. Context is automatically included in AI prompts")
    print("4. Use CLI commands: game-translator context --help")