#!/usr/bin/env python3
"""
Full pipeline: Extract terms → Translate terms → Translate content
Note: This will pause for manual glossary validation between steps
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.config import config_manager
from src.games.silksong_config import SILKSONG_CONFIG
from src.utils.glossary import GlossaryManager


def run_script(script_name: str, args: list) -> int:
    """Run a script and return exit code"""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + args
    
    print(f"\\n🚀 Running: {' '.join(cmd[1:])}")
    print("-" * 60)
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run full translation pipeline")
    parser.add_argument("--project", required=True, help="Project name (e.g., silksong)")
    parser.add_argument("--provider", choices=["openai", "local"], default="openai", 
                       help="AI provider to use")
    parser.add_argument("--model", default="gpt-4o", help="Model name to use")
    parser.add_argument("--batch-size", type=int, default=10, help="Translation batch size")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process (for testing)")
    parser.add_argument("--skip-terms", action="store_true", help="Skip term extraction (use existing)")
    parser.add_argument("--skip-glossary", action="store_true", help="Skip glossary translation (use existing)")
    parser.add_argument("--auto-approve", action="store_true", help="Automatically approve glossary without manual review")
    
    args = parser.parse_args()
    
    print(f"🔄 Starting full pipeline for project: {args.project}")
    print(f"Provider: {args.provider}, Model: {args.model}")
    
    # Register projects
    config_manager.register_project(SILKSONG_CONFIG)
    config = config_manager.get_project(args.project)
    glossary_manager = GlossaryManager(config)
    
    try:
        # Step 1: Extract terms
        if not args.skip_terms:
            print("\\n" + "="*60)
            print("STEP 1: EXTRACTING TERMS")
            print("="*60)
            
            extract_args = [
                "--project", args.project,
                "--provider", args.provider,
                "--model", args.model
            ]
            if args.max_files:
                extract_args.extend(["--max-files", str(args.max_files)])
            
            exit_code = run_script("extract_terms.py", extract_args)
            if exit_code != 0:
                print("❌ Term extraction failed")
                return exit_code
        else:
            print("\\n⏭️  Skipping term extraction (using existing)")
        
        # Step 2: Translate glossary terms
        if not args.skip_glossary:
            print("\\n" + "="*60)
            print("STEP 2: TRANSLATING GLOSSARY")
            print("="*60)
            
            translate_args = [
                "--project", args.project,
                "--provider", args.provider,
                "--model", args.model
            ]
            
            exit_code = run_script("translate_terms.py", translate_args)
            if exit_code != 0:
                print("❌ Glossary translation failed")
                return exit_code
            
            # Manual validation step
            if not args.auto_approve:
                print("\\n" + "⚠️ " * 20)
                print("MANUAL VALIDATION REQUIRED")
                print("⚠️ " * 20)
                print(f"\\nPlease review the translated glossary at:")
                print(f"  {config.get_glossary_dir()}/glossary_for_review.txt")
                print(f"\\nThen copy the approved translations to:")
                print(f"  {config.get_glossary_dir()}/final_glossary.json")
                print(f"\\nPress Enter when validation is complete...")
                input()
            else:
                print("\\n🤖 Auto-approving glossary (--auto-approve flag used)")
                # Copy translated_terms.json to final_glossary.json
                import json
                translated_file = Path(config.get_glossary_dir()) / "translated_terms.json"
                final_file = Path(config.get_glossary_dir()) / "final_glossary.json"
                
                if translated_file.exists():
                    with open(translated_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    final_data = {
                        'project': config.name,
                        'source_lang': config.source_lang,
                        'target_lang': 'Ukrainian',
                        'target_lang_code': config.target_lang_code,
                        'translations': data.get('translations', {}),
                        'terms_count': len(data.get('translations', {}))
                    }
                    
                    with open(final_file, 'w', encoding='utf-8') as f:
                        json.dump(final_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Auto-approved glossary saved to: {final_file}")
        else:
            print("\\n⏭️  Skipping glossary translation (using existing)")
        
        # Step 3: Translate content
        print("\\n" + "="*60)
        print("STEP 3: TRANSLATING CONTENT")
        print("="*60)
        
        content_args = [
            "--project", args.project,
            "--provider", args.provider,
            "--model", args.model,
            "--batch-size", str(args.batch_size),
            "--parallel"
        ]
        if args.max_files:
            content_args.extend(["--max-files", str(args.max_files)])
        
        exit_code = run_script("translate_content.py", content_args)
        if exit_code != 0:
            print("❌ Content translation failed")
            return exit_code
        
        print("\\n" + "🎉" * 20)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("🎉" * 20)
        print(f"\\nResults available at: {config.get_output_dir()}")
        print(f"You can now encrypt these files and add them to the game.")
        
        # Show statistics
        stats = glossary_manager.get_glossary_stats()
        print(f"\\n📊 Final Statistics:")
        print(f"  Extracted terms: {stats['extracted_terms']}")
        print(f"  Final glossary terms: {stats['final_glossary_terms']}")
        print(f"  Output directory: {config.get_output_dir()}")
        
    except KeyboardInterrupt:
        print("\\n\\n⏹️  Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\\n❌ Pipeline failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())