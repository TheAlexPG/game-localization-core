#!/usr/bin/env python3
"""
Step 1: Extract important terms/names from game files for glossary creation
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
from src.pipeline.extractor import TermExtractor
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
    parser = argparse.ArgumentParser(description="Extract terms for glossary creation")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai", 
                       help="AI provider to use")
    parser.add_argument("--model", default="gpt-4o", help="Model name to use")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process (for testing)")
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum retries for failed extractions (default: 5)")
    parser.add_argument("--target-tokens", type=int, default=10000, help="Target tokens per batch (default: 10000)")
    parser.add_argument("--retry-failed", action="store_true", help="Retry only previously failed files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without actually doing it")
    
    args = parser.parse_args()
    
    print(f"Starting term extraction for project: {args.project}")
    print(f"Provider: {args.provider}, Model: {args.model}")
    
    # Register available projects
    config_manager.register_project(SILKSONG_CONFIG)
    
    try:
        # Get project config
        config = config_manager.get_project(args.project)
        print(f"Source directory: {config.source_dir}")
        print(f"Output will be saved to: {config.get_glossary_dir()}")
        
        # Ensure directories exist
        config_manager.ensure_project_dirs(args.project)
        
        if args.dry_run:
            print("\\nDRY RUN - Files that would be processed:")
            if args.project == "silksong":
                processor = SilksongProcessor(config)
                files = processor.get_all_source_files()
                if args.max_files:
                    files = files[:args.max_files]
                
                for i, file_path in enumerate(files, 1):
                    print(f"{i:3}. {file_path.name}")
                
                print(f"\\nTotal: {len(files)} files")
            return
        
        # Setup components
        ai_provider = setup_ai_provider(args.provider, args.model)
        
        if args.project == "silksong":
            file_processor = SilksongProcessor(config)
        else:
            raise ValueError(f"Unsupported project: {args.project}")
        
        extractor = TermExtractor(config, file_processor, ai_provider)
        
        # Run extraction or retry
        if args.retry_failed:
            print("\\nRetrying failed files...")
            terms_data = extractor.retry_failed_files(max_retries=args.max_retries)
            
            if terms_data:
                # Save updated results
                extractor.save_extracted_terms(terms_data)
        else:
            print("\\nStarting extraction...")
            terms_data = extractor.extract_all_terms(
                max_files=args.max_files, 
                max_retries=args.max_retries,
                target_tokens=args.target_tokens
            )
            
            # Save results
            extractor.save_extracted_terms(terms_data)
        
        if not terms_data:
            print("No data to process")
            return 1
        
        print(f"\\nExtraction completed!")
        print(f"Found {terms_data['total_unique_terms']} unique terms")
        
        # Show extraction stats
        config_info = terms_data.get('extraction_config', {})
        if 'successful_files' in config_info:
            print(f"Files: {config_info['successful_files']}/{config_info['files_processed']} successful")
            
        if terms_data.get('failed_files'):
            failed_count = len(terms_data['failed_files'])
            print(f"WARNING: {failed_count} files failed - use --retry-failed to retry them")
        
        print(f"Results saved to: {config.get_glossary_dir()}/extracted_terms.json")
        
        # Show sample terms
        if terms_data['terms']:
            print(f"\\nSample terms found:")
            for term in terms_data['terms'][:10]:
                print(f"  - {term}")
            if len(terms_data['terms']) > 10:
                print(f"  ... and {len(terms_data['terms']) - 10} more")
        
        print(f"\\nNext step: Run 'python scripts/translate_terms.py --project {args.project}' to translate these terms")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())