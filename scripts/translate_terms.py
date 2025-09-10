#!/usr/bin/env python3
"""
Step 2: Translate extracted terms to create glossary
"""
import os
import sys
import argparse
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import config_manager
from src.games.silksong_config import SILKSONG_CONFIG
from src.providers.openai_provider import OpenAIProvider
from src.providers.local_provider import LocalProvider
from src.utils.glossary import GlossaryManager
from dotenv import load_dotenv

load_dotenv()


def setup_ai_provider(provider_type: str, model: str):
    """Setup AI provider based on type"""
    if provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return OpenAIProvider(api_key=api_key, model_name=model)
    
    elif provider_type == "local":
        base_url = os.getenv("LOCAL_API_URL", "http://localhost:1234/v1/chat/completions")
        return LocalProvider(base_url=base_url, model_name=model)
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def main():
    parser = argparse.ArgumentParser(description="Translate extracted terms for glossary")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai", 
                       help="AI provider to use")
    parser.add_argument("--model", default="gpt-4o", help="Model name to use")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated without actually doing it")
    
    args = parser.parse_args()
    
    print(f"Starting glossary translation for project: {args.project}")
    print(f"Provider: {args.provider}, Model: {args.model}")
    
    # Register available projects
    config_manager.register_project(SILKSONG_CONFIG)
    
    try:
        # Get project config
        config = config_manager.get_project(args.project)
        glossary_manager = GlossaryManager(config)
        
        # Load extracted terms
        terms = glossary_manager.load_extracted_terms()
        if not terms:
            print("No extracted terms found. Run extract_terms.py first.")
            return 1
        
        print(f"Found {len(terms)} terms to translate")
        
        if args.dry_run:
            print("\\nDRY RUN - Terms that would be translated:")
            for i, term in enumerate(terms[:20], 1):
                print(f"{i:3}. {term}")
            if len(terms) > 20:
                print(f"     ... and {len(terms) - 20} more")
            return 0
        
        # Setup AI provider
        ai_provider = setup_ai_provider(args.provider, args.model)
        
        # Translate terms
        print("\\nTranslating terms...")
        translations = ai_provider.translate_glossary(
            terms, 
            source_lang=config.source_lang,
            target_lang="Ukrainian"
        )
        
        print(f"Translated {len(translations)} terms")
        
        # Save translations for manual validation
        translated_file = glossary_manager.save_translated_glossary(terms, translations)
        readable_file = glossary_manager.export_glossary_for_validation()
        
        print(f"\\nResults saved:")
        print(f"  JSON format: {translated_file}")
        print(f"  Human-readable: {readable_file}")
        
        # Show sample translations
        print("\\nSample translations:")
        for i, (en_term, ua_term) in enumerate(list(translations.items())[:10], 1):
            print(f"{i:2}. {en_term:<15} → {ua_term}")
        
        if len(translations) > 10:
            print(f"     ... and {len(translations) - 10} more")
        
        print(f"\\nIMPORTANT: Please review the translations in {readable_file}")
        print(f"   Then copy approved translations to final_glossary.json")
        print(f"\\nNext step: After validation, run 'python scripts/translate_content.py --project {args.project}'")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())