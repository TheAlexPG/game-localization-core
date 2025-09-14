#!/usr/bin/env python3
"""
Show details about files that failed during term extraction
"""
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import config_manager
from src.games.silksong_config import SILKSONG_CONFIG


def main():
    parser = argparse.ArgumentParser(description="Show failed extraction files")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    parser.add_argument("--details", action="store_true", help="Show detailed error information")
    
    args = parser.parse_args()
    
    # Register projects
    config_manager.register_project(SILKSONG_CONFIG)
    
    try:
        config = config_manager.get_project(args.project)
        
        # Load extraction data
        extracted_file = Path(config.get_glossary_dir()) / "extracted_terms.json"
        
        if not extracted_file.exists():
            print("No extraction data found. Run extract_terms.py first.")
            return 1
        
        with open(extracted_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        failed_files = data.get('failed_files', [])
        
        if not failed_files:
            print("No failed files found!")
            return 0
        
        print(f"Failed Files Report for {args.project}")
        print("=" * 50)
        print(f"Total failed files: {len(failed_files)}")
        
        # Group by reason
        by_reason = {}
        for failed_file in failed_files:
            reason = failed_file.get('reason', 'unknown')
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(failed_file)
        
        print(f"\\nFailure reasons:")
        for reason, files in by_reason.items():
            print(f"  {reason}: {len(files)} files")
        
        if args.details:
            print(f"\\nDetailed breakdown:")
            print("-" * 50)
            
            for i, failed_file in enumerate(failed_files, 1):
                print(f"{i:2}. {failed_file['file_name']}")
                print(f"    Reason: {failed_file.get('reason', 'unknown')}")
                if 'error' in failed_file:
                    print(f"    Error: {failed_file['error']}")
                if 'text_length' in failed_file:
                    print(f"    Text length: {failed_file['text_length']} chars")
                print()
        else:
            print(f"\\nFailed files:")
            for failed_file in failed_files:
                print(f"  - {failed_file['file_name']} ({failed_file.get('reason', 'unknown')})")
        
        print(f"\\nTo retry these files:")
        print(f"  python scripts/extract_terms.py --project {args.project} --retry-failed --max-retries 10")
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())