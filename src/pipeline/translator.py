"""
Translation pipeline component
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..core.models import ProjectConfig, TranslationUnit
from ..processors.base_file_processor import BaseFileProcessor
from ..processors.batch_processor import BatchProcessor
from ..providers.base import AIProvider


class Translator:
    """Main translation pipeline component"""
    
    def __init__(self, config: ProjectConfig, file_processor: BaseFileProcessor,
                 ai_provider: AIProvider, batch_size: int = 10):
        self.config = config
        self.file_processor = file_processor
        self.ai_provider = ai_provider
        self.batch_processor = BatchProcessor()
        self.batch_size = batch_size
        self.glossary = None
    
    def load_glossary(self) -> Dict[str, str]:
        """Load translated glossary"""
        glossary_dir = Path(self.config.get_glossary_dir())
        glossary_file = glossary_dir / "final_glossary.json"
        
        if glossary_file.exists():
            with open(glossary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.glossary = data.get('translations', {})
                print(f"📖 Loaded glossary with {len(self.glossary)} terms")
        else:
            print(f"⚠️ No glossary found at {glossary_file}, continuing without glossary")
            self.glossary = {}
        
        return self.glossary
    
    def translate_file(self, source_file: Path) -> List[TranslationUnit]:
        """Translate a single file"""
        print(f"🔄 Translating: {source_file.name}")
        
        # Read source file
        units = self.file_processor.read_file(source_file)
        print(f"  Found {len(units)} translation units")
        
        if not units:
            return units
        
        # Split into batches
        batches = self.batch_processor.batch_translation_units(units, self.batch_size)
        print(f"  Processing in {len(batches)} batches")
        
        # Translate each batch
        translated_batches = []
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}/{len(batches)}: {len(batch)} units")
            
            try:
                translated_batch = self.ai_provider.translate_batch(
                    batch,
                    source_lang=self.config.source_lang,
                    target_lang="Ukrainian",  # Always translate to Ukrainian
                    glossary=self.glossary,
                    preserve_terms=self.config.preserve_terms
                )
                translated_batches.append(translated_batch)
                
            except Exception as e:
                print(f"    Error translating batch {i}: {e}")
                # Keep original units as fallback
                translated_batches.append(batch)
        
        # Merge results
        translated_units = self.batch_processor.merge_results(translated_batches)
        
        # Count successful translations
        success_count = sum(1 for unit in translated_units if unit.translated_text and unit.translated_text != unit.original_text)
        print(f"  ✅ Successfully translated {success_count}/{len(translated_units)} units")
        
        return translated_units
    
    def translate_all_files(self, max_files: int = None, parallel: bool = True) -> Dict[str, Any]:
        """Translate all source files"""
        print(f"🌍 Starting translation of {self.config.name} project")
        print(f"Source: {self.config.source_lang} → Target: Ukrainian (as {self.config.target_lang_code})")
        
        # Load glossary
        self.load_glossary()
        
        # Get source files
        source_files = self.file_processor.get_all_source_files()
        if max_files:
            source_files = source_files[:max_files]
        
        print(f"Found {len(source_files)} files to translate")
        
        # Ensure output directory exists
        Path(self.config.get_output_dir()).mkdir(parents=True, exist_ok=True)
        
        translation_stats = {
            'files_processed': 0,
            'files_successful': 0,
            'total_units': 0,
            'successful_translations': 0,
            'failed_files': []
        }
        
        if parallel:
            # Parallel processing
            def process_single_file(file_path: Path):
                try:
                    translated_units = self.translate_file(file_path)
                    
                    # Write output file
                    output_path = self.file_processor.get_output_path(file_path)
                    self.file_processor.write_file(output_path, translated_units)
                    
                    return {
                        'file': file_path.name,
                        'success': True,
                        'units': len(translated_units),
                        'translations': sum(1 for u in translated_units if u.translated_text and u.translated_text != u.original_text)
                    }
                except Exception as e:
                    print(f"❌ Failed to process {file_path.name}: {e}")
                    return {
                        'file': file_path.name,
                        'success': False,
                        'error': str(e)
                    }
            
            results = self.batch_processor.process_files_parallel(
                self.file_processor,
                process_single_file,
                max_files
            )
            
            # Aggregate statistics
            for result in results:
                if result:
                    translation_stats['files_processed'] += 1
                    if result.get('success'):
                        translation_stats['files_successful'] += 1
                        translation_stats['total_units'] += result.get('units', 0)
                        translation_stats['successful_translations'] += result.get('translations', 0)
                    else:
                        translation_stats['failed_files'].append(result.get('file', 'unknown'))
        
        else:
            # Sequential processing
            for i, source_file in enumerate(source_files, 1):
                print(f"\n📁 Processing file {i}/{len(source_files)}")
                
                try:
                    translated_units = self.translate_file(source_file)
                    
                    # Write output file
                    output_path = self.file_processor.get_output_path(source_file)
                    self.file_processor.write_file(output_path, translated_units)
                    
                    # Update stats
                    translation_stats['files_processed'] += 1
                    translation_stats['files_successful'] += 1
                    translation_stats['total_units'] += len(translated_units)
                    translation_stats['successful_translations'] += sum(
                        1 for u in translated_units 
                        if u.translated_text and u.translated_text != u.original_text
                    )
                    
                except Exception as e:
                    print(f"❌ Failed to process {source_file.name}: {e}")
                    translation_stats['files_processed'] += 1
                    translation_stats['failed_files'].append(source_file.name)
        
        # Print final statistics
        print(f"\n🎉 Translation complete!")
        print(f"Files processed: {translation_stats['files_successful']}/{translation_stats['files_processed']}")
        print(f"Translation units: {translation_stats['successful_translations']}/{translation_stats['total_units']}")
        
        if translation_stats['failed_files']:
            print(f"Failed files: {', '.join(translation_stats['failed_files'])}")
        
        return translation_stats
    
    def translate_glossary_terms(self, terms: List[str]) -> Dict[str, str]:
        """Translate a list of terms for glossary"""
        print(f"📚 Translating {len(terms)} glossary terms...")
        
        translations = self.ai_provider.translate_glossary(
            terms,
            source_lang=self.config.source_lang,
            target_lang="Ukrainian"
        )
        
        print(f"✅ Translated {len(translations)} terms")
        return translations
    
    def save_translated_glossary(self, terms: List[str], translations: Dict[str, str]) -> Path:
        """Save translated glossary"""
        glossary_dir = Path(self.config.get_glossary_dir())
        glossary_dir.mkdir(parents=True, exist_ok=True)
        
        glossary_data = {
            'project': self.config.name,
            'source_lang': self.config.source_lang,
            'target_lang': 'Ukrainian',
            'target_lang_code': self.config.target_lang_code,
            'terms_count': len(terms),
            'translations': translations,
            'all_terms': terms
        }
        
        output_file = glossary_dir / "final_glossary.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(glossary_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved translated glossary to: {output_file}")
        return output_file