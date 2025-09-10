"""
Term extraction pipeline component
"""
import json
from pathlib import Path
from typing import List, Set, Dict, Any
from ..core.models import ProjectConfig
from ..processors.base_file_processor import BaseFileProcessor
from ..processors.batch_processor import BatchProcessor
from ..providers.base import AIProvider


class TermExtractor:
    """Extracts important terms/names from game files for glossary creation"""
    
    def __init__(self, config: ProjectConfig, file_processor: BaseFileProcessor, 
                 ai_provider: AIProvider):
        self.config = config
        self.file_processor = file_processor
        self.ai_provider = ai_provider
        self.batch_processor = BatchProcessor()
    
    def extract_all_terms(self, max_files: int = None, max_retries: int = 5) -> Dict[str, Any]:
        """Extract terms from all source files"""
        print(f"Extracting terms from {self.config.name} files...")
        
        # Get all source files
        source_files = self.file_processor.get_all_source_files()
        if max_files:
            source_files = source_files[:max_files]
        
        print(f"Found {len(source_files)} files to process")
        
        all_terms = set()
        file_terms = {}
        failed_files = []  # Track files that failed after all retries
        
        # Process each file
        for i, file_path in enumerate(source_files, 1):
            print(f"Processing {i}/{len(source_files)}: {file_path.name}")
            
            try:
                # Extract text from file
                text = self.file_processor.extract_text_for_terms(file_path)
                
                if text.strip():
                    # Extract terms using AI with retry logic
                    terms = self.ai_provider.extract_terms(
                        text, 
                        context=f"Video game localization file: {file_path.name}",
                        max_retries=max_retries
                    )
                    
                    # Check if extraction failed (returns None on failure)
                    if terms is None:
                        print(f"  FAILED after {max_retries} retries - adding to failed files list")
                        failed_files.append({
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'reason': 'extraction_failed',
                            'text_length': len(text)
                        })
                        continue
                    
                    if terms:  # Non-empty list
                        file_terms[file_path.name] = terms
                        all_terms.update(terms)
                        print(f"  Found {len(terms)} terms: {', '.join(terms[:5])}{'...' if len(terms) > 5 else ''}")
                    else:  # Empty list (valid response but no terms)
                        print(f"  No terms found (valid empty response)")
                else:
                    print(f"  Empty file, skipping")
                    
            except Exception as e:
                print(f"  Error processing {file_path.name}: {e}")
                failed_files.append({
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'reason': 'processing_error',
                    'error': str(e)
                })
                continue
        
        # Prepare results
        successful_files = len(source_files) - len(failed_files)
        results = {
            'project': self.config.name,
            'total_unique_terms': len(all_terms),
            'terms': sorted(list(all_terms)),
            'file_breakdown': file_terms,
            'failed_files': failed_files,
            'extraction_config': {
                'source_lang': self.config.source_lang,
                'ai_model': self.ai_provider.model_name,
                'files_processed': len(source_files),
                'successful_files': successful_files,
                'failed_files': len(failed_files),
                'max_retries_used': max_retries
            }
        }
        
        print(f"\nExtraction complete!")
        print(f"Found {len(all_terms)} unique terms across {successful_files}/{len(source_files)} files")
        
        if failed_files:
            print(f"WARNING: {len(failed_files)} files failed after {max_retries} retries:")
            for failed_file in failed_files:
                print(f"  - {failed_file['file_name']}: {failed_file['reason']}")
        
        return results
    
    def save_extracted_terms(self, terms_data: Dict[str, Any]) -> Path:
        """Save extracted terms to JSON file"""
        glossary_dir = Path(self.config.get_glossary_dir())
        glossary_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = glossary_dir / "extracted_terms.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved extracted terms to: {output_file}")
        return output_file
    
    def load_extracted_terms(self) -> Dict[str, Any]:
        """Load previously extracted terms"""
        glossary_dir = Path(self.config.get_glossary_dir())
        terms_file = glossary_dir / "extracted_terms.json"
        
        if not terms_file.exists():
            raise FileNotFoundError(f"No extracted terms found at: {terms_file}")
        
        with open(terms_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def run_extraction(self, max_files: int = None, save: bool = True) -> Dict[str, Any]:
        """Run complete term extraction process"""
        # Ensure directories exist
        Path(self.config.get_glossary_dir()).mkdir(parents=True, exist_ok=True)
        
        # Extract terms
        terms_data = self.extract_all_terms(max_files)
        
        # Save results
        if save:
            self.save_extracted_terms(terms_data)
        
        return terms_data
    
    def retry_failed_files(self, max_retries: int = 10) -> Dict[str, Any]:
        """Retry extraction for previously failed files"""
        # Load previous extraction results
        try:
            terms_data = self.load_extracted_terms()
            failed_files = terms_data.get('failed_files', [])
            
            if not failed_files:
                print("No failed files found to retry")
                return terms_data
            
            print(f"Retrying extraction for {len(failed_files)} failed files with {max_retries} retries...")
            
            # Current terms
            all_terms = set(terms_data.get('terms', []))
            file_terms = terms_data.get('file_breakdown', {}).copy()
            still_failed = []
            
            # Retry each failed file
            for i, failed_file_info in enumerate(failed_files, 1):
                file_path = Path(failed_file_info['file_path'])
                print(f"Retrying {i}/{len(failed_files)}: {file_path.name}")
                
                try:
                    # Extract text from file
                    text = self.file_processor.extract_text_for_terms(file_path)
                    
                    if text.strip():
                        # Extract terms using AI with more retries
                        terms = self.ai_provider.extract_terms(
                            text,
                            context=f"Video game localization file: {file_path.name}",
                            max_retries=max_retries
                        )
                        
                        if terms is None:
                            print(f"  FAILED again after {max_retries} retries")
                            still_failed.append(failed_file_info)
                            continue
                        
                        if terms:
                            file_terms[file_path.name] = terms
                            all_terms.update(terms)
                            print(f"  SUCCESS: Found {len(terms)} terms")
                        else:
                            print(f"  SUCCESS: No terms found (valid empty response)")
                            
                except Exception as e:
                    print(f"  ERROR: {e}")
                    failed_file_info['error'] = str(e)
                    still_failed.append(failed_file_info)
            
            # Update results
            terms_data.update({
                'total_unique_terms': len(all_terms),
                'terms': sorted(list(all_terms)),
                'file_breakdown': file_terms,
                'failed_files': still_failed,
            })
            
            # Update config
            config = terms_data.get('extraction_config', {})
            config.update({
                'retry_attempts': config.get('retry_attempts', 0) + 1,
                'last_retry_max_retries': max_retries,
                'failed_files': len(still_failed)
            })
            terms_data['extraction_config'] = config
            
            print(f"\nRetry complete!")
            print(f"Successfully processed: {len(failed_files) - len(still_failed)} files")
            print(f"Still failed: {len(still_failed)} files")
            
            return terms_data
            
        except FileNotFoundError:
            print("No previous extraction results found. Run extract_terms.py first.")
            return {}
        except Exception as e:
            print(f"Error during retry: {e}")
            return {}
    
