"""Translation management and coordination"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import TranslationEntry, TranslationStatus
from ..providers.base import BaseTranslationProvider


class TranslationManager:
    """Manages translation process with AI providers"""

    def __init__(self, project: 'TranslationProject', provider: BaseTranslationProvider):
        self.project = project
        self.provider = provider
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }

    def translate_entries(self, entries: List[TranslationEntry],
                         batch_size: int = 10,
                         max_retries: int = 3,
                         skip_technical: bool = True,
                         use_smart_glossary: bool = True,
                         progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Translate multiple entries with batching and error handling.

        Args:
            entries: List of entries to translate
            batch_size: Number of entries per batch
            max_retries: Maximum retries for failed batches
            skip_technical: Skip technical entries automatically
            use_smart_glossary: Use smart glossary filtering for efficiency
            progress_callback: Optional callback for progress updates

        Returns:
            Translation results and statistics
        """
        self._reset_stats()
        self.stats["start_time"] = datetime.now()

        # Filter entries
        entries_to_translate = []
        for entry in entries:
            if entry.status == TranslationStatus.TRANSLATED:
                self.stats["skipped"] += 1
                continue

            if skip_technical and entry.is_technical():
                self.stats["skipped"] += 1
                continue

            entries_to_translate.append(entry)

        total_entries = len(entries_to_translate)
        if total_entries == 0:
            return self._get_final_stats()

        print(f"Starting translation of {total_entries} entries...")

        # Process in batches
        for i in range(0, total_entries, batch_size):
            batch = entries_to_translate[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_entries + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} entries)...")

            success = self._translate_batch(batch, max_retries)

            self.stats["processed"] += len(batch)
            if success:
                self.stats["successful"] += len(batch)
            else:
                self.stats["failed"] += len(batch)

            # Progress callback
            if progress_callback:
                progress = (i + len(batch)) / total_entries * 100
                progress_callback(progress, batch_num, total_batches)

            # Save progress after each batch
            self.project._save_project_state()

            # Small delay between batches to be nice to APIs
            time.sleep(0.5)

        self.stats["end_time"] = datetime.now()
        return self._get_final_stats()

    def translate_pending(self, limit: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Translate all pending entries"""
        pending_entries = self.project.get_pending_entries(limit)
        return self.translate_entries(pending_entries, **kwargs)

    def retranslate_failed(self, **kwargs) -> Dict[str, Any]:
        """Retry translation for entries that previously failed"""
        # In our simple model, we don't track "failed" status separately
        # So we'll retranslate all pending entries
        return self.translate_pending(**kwargs)

    def _translate_batch(self, entries: List[TranslationEntry], max_retries: int) -> bool:
        """Translate a single batch with retry logic"""
        texts = [entry.source_text for entry in entries]

        for attempt in range(max_retries + 1):
            try:
                # Use project configuration for languages
                source_lang = self.project.config.source_lang
                target_lang = self.project.config.target_lang

                # Get project context for better translations
                project_context = self.project.format_context_for_prompt("project")

                # Get translations from provider
                translations = self.provider.translate_texts(
                    texts=texts,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    glossary=self.project.glossary,
                    context=project_context or f"Game: {self.project.config.name}",
                    use_smart_glossary=use_smart_glossary
                )

                # Update entries with translations
                for entry, translation in zip(entries, translations):
                    if translation and translation != entry.source_text:
                        entry.update_translation(translation)
                    else:
                        # If translation failed or is identical, keep as pending
                        print(f"Warning: No translation for '{entry.key[:50]}...'")

                return True

            except Exception as e:
                print(f"Batch translation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    print(f"Retrying in {(attempt + 1) * 2} seconds...")
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"Batch failed after {max_retries + 1} attempts")

        return False

    def validate_provider(self) -> bool:
        """Test if provider is working"""
        try:
            return self.provider.validate_connection()
        except Exception as e:
            print(f"Provider validation failed: {e}")
            return False

    def get_provider_info(self) -> Dict[str, str]:
        """Get information about current provider"""
        return self.provider.get_info()

    def estimate_cost(self, entry_count: int) -> Dict[str, Any]:
        """Estimate translation cost/time (basic implementation)"""
        # This is a simple estimation - could be enhanced per provider
        avg_chars_per_entry = 50
        total_chars = entry_count * avg_chars_per_entry

        return {
            "entries": entry_count,
            "estimated_chars": total_chars,
            "estimated_time_minutes": (entry_count / 100) * 5,  # ~5 min per 100 entries
            "provider": self.provider.get_info()["name"]
        }

    def _reset_stats(self):
        """Reset translation statistics"""
        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }

    def _get_final_stats(self) -> Dict[str, Any]:
        """Get final translation statistics"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        return {
            **self.stats,
            "duration_seconds": duration,
            "success_rate": (
                self.stats["successful"] / max(self.stats["processed"], 1) * 100
                if self.stats["processed"] > 0 else 0
            ),
            "provider_info": self.provider.get_info()
        }