"""
Batch processing utilities for parallel file processing
"""
from pathlib import Path
from typing import List, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.models import TranslationUnit
from .base_file_processor import BaseFileProcessor


class BatchProcessor:
    """Handles batch processing and parallelization"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    def process_files_parallel(self, 
                             file_processor: BaseFileProcessor,
                             processing_func: Callable[[Path], Any],
                             max_files: Optional[int] = None) -> List[Any]:
        """Process multiple files in parallel"""
        
        source_files = file_processor.get_all_source_files()
        if max_files:
            source_files = source_files[:max_files]
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {
                executor.submit(processing_func, file_path): file_path 
                for file_path in source_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"✓ Processed: {file_path.name}")
                except Exception as e:
                    print(f"✗ Failed to process {file_path.name}: {e}")
                    results.append(None)
        
        return results
    
    def batch_translation_units(self, units: List[TranslationUnit], 
                              batch_size: int = 5) -> List[List[TranslationUnit]]:
        """Split translation units into batches"""
        return [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
    
    def merge_results(self, results: List[List[TranslationUnit]]) -> List[TranslationUnit]:
        """Merge batched results back into single list"""
        merged = []
        for batch in results:
            if batch:  # Skip None results from failed batches
                merged.extend(batch)
        return merged