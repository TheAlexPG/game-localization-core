#!/usr/bin/env python3
"""
Show status of translation project
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import config_manager
from src.games.silksong_config import SILKSONG_CONFIG
from src.utils.glossary import GlossaryManager
from src.utils.cache import TranslationCache
from src.processors.silksong_processor import SilksongProcessor


def main():
    parser = argparse.ArgumentParser(description="Show project status")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    
    args = parser.parse_args()
    
    # Register projects
    config_manager.register_project(SILKSONG_CONFIG)
    
    try:
        config = config_manager.get_project(args.project)
        glossary_manager = GlossaryManager(config)
        cache = TranslationCache(config)
        
        print(f"Project Status: {args.project}")
        print("=" * 50)
        
        # Project info
        print(f"\\nConfiguration:")
        print(f"  Source language: {config.source_lang}")
        print(f"  Target language code: {config.target_lang_code}")
        print(f"  Source directory: {config.source_dir}")
        print(f"  Data directory: {config.get_data_dir()}")
        
        # Check source files
        if args.project == "silksong":
            processor = SilksongProcessor(config)
            try:
                source_files = processor.get_all_source_files()
                total_units = 0
                for file_path in source_files:
                    units = processor.read_file(file_path)
                    total_units += len(units)
                
                print(f"\\nSource Files:")
                print(f"  Files found: {len(source_files)}")
                print(f"  Total translation units: {total_units}")
                
                if source_files:
                    print(f"  Sample files:")
                    for file_path in source_files[:5]:
                        units = processor.read_file(file_path)
                        print(f"    {file_path.name} ({len(units)} units)")
                    if len(source_files) > 5:
                        print(f"    ... and {len(source_files) - 5} more")
                        
            except Exception as e:
                print(f"\\nSource Files: ERROR - Error accessing source files: {e}")
        
        # Glossary status
        glossary_stats = glossary_manager.get_glossary_stats()
        print(f"\\nGlossary Status:")
        print(f"  Extracted terms: {glossary_stats['extracted_terms']}")
        print(f"  Translated terms: {glossary_stats['translated_terms']}")
        print(f"  Final glossary terms: {glossary_stats['final_glossary_terms']}")
        print(f"  Files: {', '.join(glossary_stats['files']) if glossary_stats['files'] else 'None'}")
        
        # Check for failed extractions
        glossary_dir = Path(config.get_glossary_dir())
        extracted_file = glossary_dir / "extracted_terms.json"
        if extracted_file.exists():
            import json
            with open(extracted_file, 'r', encoding='utf-8') as f:
                extraction_data = json.load(f)
                failed_files = extraction_data.get('failed_files', [])
                if failed_files:
                    print(f"  Failed files: {len(failed_files)} files need retry")
                    print(f"    Run: python scripts/extract_terms.py --project {args.project} --retry-failed")
        
        # Cache status
        cache_stats = cache.get_cache_stats()
        print(f"\\nCache Status:")
        print(f"  Cached translations: {cache_stats['total_entries']}")
        print(f"  Cache size: {cache_stats['cache_size_mb']:.2f} MB")
        
        # Output status
        output_dir = Path(config.get_output_dir())
        if output_dir.exists():
            output_files = list(output_dir.glob("*"))
            print(f"\\nOutput Status:")
            print(f"  Output directory: {output_dir}")
            print(f"  Translated files: {len(output_files)}")
            
            if output_files:
                print(f"  Sample output files:")
                for file_path in output_files[:5]:
                    print(f"    {file_path.name}")
                if len(output_files) > 5:
                    print(f"    ... and {len(output_files) - 5} more")
        else:
            print(f"\\nOutput Status: No output files yet")
        
        # Pipeline recommendations
        print(f"\\nRecommendations:")
        
        if glossary_stats['extracted_terms'] == 0:
            print(f"  1. Run: python scripts/extract_terms.py --project {args.project}")
        elif glossary_stats['translated_terms'] == 0:
            print(f"  1. Run: python scripts/translate_terms.py --project {args.project}")
        elif glossary_stats['final_glossary_terms'] == 0:
            print(f"  1. Review and approve glossary, then copy to final_glossary.json")
        elif not output_dir.exists() or len(list(output_dir.glob("*"))) == 0:
            print(f"  1. Run: python scripts/translate_content.py --project {args.project}")
        else:
            print(f"  OK Project appears to be complete!")
            print(f"     You can now encrypt the files in {output_dir} and add them to the game")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())