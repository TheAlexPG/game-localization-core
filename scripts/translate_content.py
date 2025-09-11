#!/usr/bin/env python3
"""
Step 3: Translate game content using the validated glossary
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import config_manager
from src.games.silksong_config import SILKSONG_CONFIG
from src.processors.silksong_processor import SilksongProcessor
from src.providers.openai_provider import OpenAIProvider
from src.providers.local_provider import LocalProvider
from src.pipeline.translator import Translator
from src.utils.cache import TranslationCache
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
    parser = argparse.ArgumentParser(description="Translate game content")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai", 
                       help="AI provider to use")
    parser.add_argument("--model", default="gpt-4o", help="Model name to use")
    parser.add_argument("--batch-size", type=int, default=5, help="Translation batch size")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process (for testing)")
    parser.add_argument("--parallel", action="store_true", default=True, help="Enable parallel processing")
    parser.add_argument("--no-parallel", dest="parallel", action="store_false", help="Disable parallel processing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without actually doing it")
    parser.add_argument("--clear-cache", action="store_true", help="Clear translation cache before starting")
    
    args = parser.parse_args()
    
    print(f"🌍 Starting content translation for project: {args.project}")
    print(f"Provider: {args.provider}, Model: {args.model}")
    print(f"Batch size: {args.batch_size}, Parallel: {args.parallel}")
    
    # Register available projects
    config_manager.register_project(SILKSONG_CONFIG)
    
    try:
        # Get project config
        config = config_manager.get_project(args.project)
        print(f"Source: {config.source_dir}")
        print(f"Output: {config.get_output_dir()}")
        
        # Ensure directories exist
        config_manager.ensure_project_dirs(args.project)
        
        # Setup file processor
        if args.project == "silksong":
            file_processor = SilksongProcessor(config)
        else:
            raise ValueError(f"Unsupported project: {args.project}")
        
        if args.dry_run:
            print("\\n🔍 DRY RUN - Files that would be processed:")
            files = file_processor.get_all_source_files()
            if args.max_files:
                files = files[:args.max_files]
            
            for i, file_path in enumerate(files, 1):
                # Check how many translation units
                units = file_processor.read_file(file_path)
                output_path = file_processor.get_output_path(file_path)
                print(f"{i:3}. {file_path.name} ({len(units)} units) → {output_path.name}")
            
            print(f"\\nTotal: {len(files)} files")
            return 0
        
        # Setup cache
        cache = TranslationCache(config)
        if args.clear_cache:
            cache.clear_cache()
        
        cache_stats = cache.get_cache_stats()
        print(f"Cache: {cache_stats['total_entries']} entries")
        
        # Setup AI provider and translator
        ai_provider = setup_ai_provider(args.provider, args.model)
        translator = Translator(config, file_processor, ai_provider, batch_size=args.batch_size)
        
        # Check for glossary
        glossary = translator.load_glossary()
        if glossary:
            print(f"Using glossary with {len(glossary)} terms")
        else:
            print("⚠️  No glossary found - translations may be inconsistent")
            print("   Consider running extract_terms.py and translate_terms.py first")
        
        # Run translation
        print("\\n🚀 Starting translation...")
        stats = translator.translate_all_files(
            max_files=args.max_files,
            parallel=args.parallel
        )
        
        print(f"\\n🎉 Translation completed!")
        print(f"Files: {stats['files_successful']}/{stats['files_processed']} successful")
        print(f"Units: {stats['successful_translations']}/{stats['total_units']} translated")
        
        if stats['failed_files']:
            print(f"Failed files: {', '.join(stats['failed_files'])}")
        
        # Update cache
        print(f"\\n💾 Saving cache...")
        cache.save_cache()
        
        print(f"\\n✅ Results saved to: {config.get_output_dir()}")
        print(f"   You can now encrypt these files and add them to the game")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())