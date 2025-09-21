"""Project management for translation system"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import TranslationEntry, ProjectConfig, ProgressStats, TranslationStatus
from .tracking import VersionTracker


class TranslationProject:
    """Main class for managing translation project"""

    def __init__(self, name: str, source_lang: str, target_lang: str,
                 project_dir: Optional[Path] = None):
        self.config = ProjectConfig(name=name, source_lang=source_lang, target_lang=target_lang)
        self.entries: Dict[str, TranslationEntry] = {}
        self.glossary: Dict[str, str] = {}

        # Setup project directories
        self.project_dir = project_dir or Path(f"./projects/{name}")
        self.project_dir.mkdir(parents=True, exist_ok=True)

        self.data_dir = self.project_dir / "data"
        self.output_dir = self.project_dir / "output"
        self.glossary_dir = self.project_dir / "glossary"

        for directory in [self.data_dir, self.output_dir, self.glossary_dir]:
            directory.mkdir(exist_ok=True)

        # Version tracking
        self.tracker = VersionTracker(self.project_dir)
        self.version = "1.0.0"

        # Load existing project if present
        self._load_project_state()

    @classmethod
    def load(cls, project_name: str, project_dir: Optional[Path] = None) -> 'TranslationProject':
        """Load existing project"""
        if project_dir is None:
            project_dir = Path(f"./projects/{project_name}")

        state_file = project_dir / "project.json"
        if not state_file.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found at {project_dir}")

        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Handle both old format (with "config" key) and new format (flat)
        if "config" in state:
            config = state["config"]
        else:
            config = state
        project = cls(
            name=config["name"],
            source_lang=config["source_lang"],
            target_lang=config["target_lang"],
            project_dir=project_dir
        )

        return project

    def import_source(self, entries_data: List[Dict[str, Any]], update_existing: bool = True):
        """Import source entries"""
        new_count = 0
        updated_count = 0

        for data in entries_data:
            key = data["key"]
            source_text = data["source_text"]

            if key in self.entries:
                existing = self.entries[key]
                if existing.needs_update(source_text):
                    # Source changed - needs retranslation
                    existing.source_text = source_text
                    existing.source_hash = existing._calculate_hash(source_text)
                    existing.status = TranslationStatus.PENDING
                    existing.last_modified = datetime.now()
                    updated_count += 1
            else:
                # New entry
                entry = TranslationEntry(
                    key=key,
                    source_text=source_text,
                    context=data.get("context"),
                    file_path=data.get("file_path"),
                    metadata=data.get("metadata", {})
                )
                self.entries[key] = entry
                new_count += 1

        self._save_project_state()
        return {"new": new_count, "updated": updated_count}

    def import_translations(self, translations: Dict[str, str], overwrite: bool = False):
        """Import existing translations"""
        imported_count = 0

        for key, translation in translations.items():
            if key in self.entries:
                entry = self.entries[key]
                # Only import if not already translated or overwrite is True
                if entry.status == TranslationStatus.PENDING or overwrite:
                    entry.update_translation(translation)
                    imported_count += 1

        self._save_project_state()
        return imported_count

    def load_glossary(self, glossary_path: Optional[Path] = None):
        """Load glossary for consistent terminology"""
        if glossary_path:
            glossary_file = glossary_path
        else:
            glossary_file = self.glossary_dir / "glossary.json"

        if not glossary_file.exists():
            return 0

        with open(glossary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Support different glossary formats
        if isinstance(data, dict):
            if "translations" in data:
                self.glossary = data["translations"]
            else:
                self.glossary = data

        self.config.glossary_path = str(glossary_file)
        return len(self.glossary)

    def save_glossary(self):
        """Save current glossary"""
        glossary_file = self.glossary_dir / "glossary.json"

        data = {
            "project": self.config.name,
            "source_lang": self.config.source_lang,
            "target_lang": self.config.target_lang,
            "terms_count": len(self.glossary),
            "translations": self.glossary
        }

        with open(glossary_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_progress_stats(self) -> ProgressStats:
        """Get current progress statistics"""
        stats = ProgressStats()
        stats.update_from_entries(list(self.entries.values()))
        return stats

    def get_entries_by_status(self, status: TranslationStatus) -> List[TranslationEntry]:
        """Get entries filtered by status"""
        return [e for e in self.entries.values() if e.status == status]

    def get_pending_entries(self, limit: Optional[int] = None) -> List[TranslationEntry]:
        """Get pending entries for translation"""
        pending = self.get_entries_by_status(TranslationStatus.PENDING)
        if limit:
            return pending[:limit]
        return pending

    def update_entry(self, key: str, translation: str, notes: Optional[str] = None):
        """Update single entry translation"""
        if key not in self.entries:
            raise KeyError(f"Entry '{key}' not found")

        entry = self.entries[key]
        entry.update_translation(translation)
        if notes:
            entry.translator_notes = notes

        self._save_project_state()

    def batch_update(self, updates: Dict[str, str]):
        """Update multiple entries at once"""
        updated_count = 0
        for key, translation in updates.items():
            if key in self.entries:
                self.entries[key].update_translation(translation)
                updated_count += 1

        self._save_project_state()
        return updated_count

    def create_snapshot(self, version: Optional[str] = None, bump_type: str = "patch"):
        """Create version snapshot"""
        if version is None:
            version = self.tracker.increment_version(self.version, bump_type)

        self.tracker.save_snapshot(self.entries, version)
        self.version = version
        self._save_project_state()
        return version

    def get_version_changes(self, old_version: str, new_version: str) -> Dict[str, List[str]]:
        """Get changes between versions"""
        return self.tracker.get_changes(old_version, new_version)

    def export_for_review(self) -> Dict[str, Any]:
        """Export data for translator review"""
        return {
            "project": self.config.name,
            "source_lang": self.config.source_lang,
            "target_lang": self.config.target_lang,
            "stats": self.get_progress_stats().to_dict(),
            "glossary": self.glossary,
            "entries": [
                {
                    "key": entry.key,
                    "context": entry.context,
                    "source": entry.source_text,
                    "translation": entry.translated_text if entry.status != TranslationStatus.SKIPPED else entry.source_text,
                    "status": entry.status.value,
                    "notes": entry.translator_notes,
                    "file": entry.file_path
                }
                for entry in self.entries.values()
            ]
        }

    def _save_project_state(self):
        """Save current project state"""
        state_file = self.project_dir / "project.json"

        state = {
            "config": self.config.to_dict(),
            "version": self.version,
            "last_modified": datetime.now().isoformat(),
            "entries": {
                key: {
                    "source_text": entry.source_text,
                    "source_hash": entry.source_hash,
                    "translated_text": entry.translated_text,
                    "status": entry.status.value,
                    "context": entry.context,
                    "file_path": entry.file_path,
                    "metadata": entry.metadata,
                    "translator_notes": entry.translator_notes,
                    "last_modified": entry.last_modified.isoformat()
                }
                for key, entry in self.entries.items()
            }
        }

        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def _load_project_state(self):
        """Load existing project state"""
        state_file = self.project_dir / "project.json"
        if not state_file.exists():
            return

        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Load config - handle both old format (with "config" key) and new format (flat)
        if "config" in state:
            self.config = ProjectConfig.from_dict(state["config"])
        else:
            # Create config from flat structure (CLI format)
            config_data = {k: v for k, v in state.items()
                          if k in ['name', 'source_lang', 'target_lang', 'source_format', 'output_format']}
            self.config = ProjectConfig.from_dict(config_data)
            # Also load context data
            self.config.project_context = state.get("project_context", {})
            self.config.glossary_context = state.get("glossary_context", {})
        self.version = state.get("version", "1.0.0")

        # Load entries
        for key, data in state.get("entries", {}).items():
            entry = TranslationEntry(
                key=key,
                source_text=data["source_text"],
                translated_text=data.get("translated_text"),
                context=data.get("context"),
                file_path=data.get("file_path"),
                metadata=data.get("metadata", {}),
                translator_notes=data.get("translator_notes")
            )
            entry.status = TranslationStatus(data["status"])
            entry.source_hash = data["source_hash"]

            # Parse last_modified if present
            if "last_modified" in data:
                entry.last_modified = datetime.fromisoformat(data["last_modified"])

            self.entries[key] = entry

        # Load glossary if exists
        self.load_glossary()

    # Context management methods
    def set_project_context(self, context: Dict[str, Any] = None, from_file: str = None):
        """Set general project context for better translations

        Args:
            context: Dictionary with context information
            from_file: Path to file with context (markdown or text)
        """
        if from_file:
            context_path = Path(from_file)
            if not context_path.exists():
                # Try relative to project dir
                context_path = self.project_dir / from_file

            if context_path.exists():
                with open(context_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # If it's a dict-like file (JSON), parse it
                    if from_file.endswith('.json'):
                        self.config.project_context = json.loads(content)
                    else:
                        # Store as text content
                        self.config.project_context["content"] = content
                        self.config.project_context["file"] = str(context_path)
        elif context:
            self.config.project_context.update(context)

        # Check for default PROJECT_CONTEXT.md
        default_context = self.project_dir / "PROJECT_CONTEXT.md"
        if default_context.exists() and not self.config.project_context.get("content"):
            with open(default_context, 'r', encoding='utf-8') as f:
                self.config.project_context["content"] = f.read()
                self.config.project_context["file"] = str(default_context)

        self._save_project_state()

    def add_project_context(self, key: str, value: Any):
        """Add single context property"""
        self.config.project_context[key] = value
        self._save_project_state()

    def get_project_context(self) -> Dict[str, Any]:
        """Get current project context"""
        return self.config.project_context

    def set_glossary_context(self, context: Dict[str, Any] = None, from_file: str = None):
        """Set context for glossary extraction and translation

        Args:
            context: Dictionary with glossary-specific instructions
            from_file: Path to file with glossary context
        """
        if from_file:
            context_path = Path(from_file)
            if not context_path.exists():
                context_path = self.project_dir / from_file

            if context_path.exists():
                with open(context_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if from_file.endswith('.json'):
                        self.config.glossary_context = json.loads(content)
                    else:
                        self.config.glossary_context["content"] = content
                        self.config.glossary_context["file"] = str(context_path)
        elif context:
            self.config.glossary_context.update(context)

        # Check for default GLOSSARY_CONTEXT.md
        default_glossary = self.project_dir / "GLOSSARY_CONTEXT.md"
        if default_glossary.exists() and not self.config.glossary_context.get("content"):
            with open(default_glossary, 'r', encoding='utf-8') as f:
                self.config.glossary_context["content"] = f.read()
                self.config.glossary_context["file"] = str(default_glossary)

        self._save_project_state()

    def add_glossary_context(self, key: str, value: Any):
        """Add single glossary context property"""
        self.config.glossary_context[key] = value
        self._save_project_state()

    def get_glossary_context(self) -> Dict[str, Any]:
        """Get current glossary context"""
        return self.config.glossary_context

    def format_context_for_prompt(self, context_type: str = "project") -> str:
        """Format context for inclusion in AI prompt

        Args:
            context_type: "project" or "glossary"

        Returns:
            Formatted context string for prompt
        """
        context = self.config.project_context if context_type == "project" else self.config.glossary_context

        if not context:
            return ""

        lines = []

        # Add file content if present
        if "content" in context:
            lines.append(f"=== {context_type.upper()} CONTEXT ===")
            lines.append(context["content"])
            lines.append("")

        # Add individual properties
        skip_keys = {"content", "file"}
        properties = {k: v for k, v in context.items() if k not in skip_keys}

        if properties:
            if not lines:  # No content, add header
                lines.append(f"=== {context_type.upper()} CONTEXT ===")

            for key, value in properties.items():
                # Format key nicely
                formatted_key = key.replace('_', ' ').title()
                lines.append(f"{formatted_key}: {value}")

        return "\n".join(lines) if lines else ""

    # ===== 3-STAGE PIPELINE METHODS =====

    def extract_terms_from_sources(self, provider, max_entries: Optional[int] = None,
                                  batch_size: int = 10, max_workers: int = 1) -> List[str]:
        """Extract important terms from all source texts

        Args:
            provider: AI provider instance for term extraction
            max_entries: Maximum entries to process (for testing)
            batch_size: Number of texts per batch
            max_workers: Number of parallel threads

        Returns:
            List of unique extracted terms
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Get source entries
        entries = list(self.entries.values())
        source_texts = [entry.source_text for entry in entries if entry.source_text]

        if max_entries:
            source_texts = source_texts[:max_entries]

        if not source_texts:
            return []

        # Get combined context
        project_context = self.format_context_for_prompt('project')
        glossary_context = self.format_context_for_prompt('glossary')
        combined_context = f"{project_context}\n{glossary_context}".strip()

        # Extract terms in batches
        all_terms = set()

        def extract_batch(texts_batch):
            try:
                combined_text = "\n".join(texts_batch)
                return provider.extract_terms_structured(combined_text, combined_context)
            except Exception as e:
                print(f"Error in batch: {e}")
                return []

        # Create batches
        batches = [source_texts[i:i+batch_size] for i in range(0, len(source_texts), batch_size)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(extract_batch, batch): batch for batch in batches}

            for future in as_completed(future_to_batch):
                try:
                    terms = future.result()
                    all_terms.update(terms)
                except Exception as e:
                    print(f"Batch failed: {e}")

        # Save extracted terms
        extracted_terms = list(all_terms)
        extracted_terms_data = {
            term: {"source": term, "translated": None, "context": "extracted"}
            for term in extracted_terms
        }

        # Save to extracted terms file
        extracted_file = self.glossary_dir / "extracted_terms.json"
        with open(extracted_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_terms_data, f, indent=2, ensure_ascii=False)

        return extracted_terms

    def translate_extracted_glossary(self, provider, input_file: Optional[str] = None,
                                   batch_size: int = 10, max_workers: int = 1) -> Dict[str, str]:
        """Translate extracted glossary terms

        Args:
            provider: AI provider instance for translation
            input_file: Input file with extracted terms (default: extracted_terms.json)
            batch_size: Number of terms per batch
            max_workers: Number of parallel threads

        Returns:
            Dictionary mapping terms to translations
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Load extracted terms
        if not input_file:
            input_file = self.glossary_dir / "extracted_terms.json"
        else:
            input_file = Path(input_file)

        if not input_file.exists():
            raise FileNotFoundError(f"Extracted terms file not found: {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            terms_data = json.load(f)

        # Get terms that need translation
        terms_to_translate = [term for term, data in terms_data.items()
                             if not data.get('translated')]

        if not terms_to_translate:
            return {}

        # Translate in batches
        def translate_batch(terms_batch):
            try:
                # translate_glossary_structured returns Dict[str, str], not List[str]
                translations_dict = provider.translate_glossary_structured(
                    terms_batch,
                    self.config.source_lang,
                    self.config.target_lang
                )
                return translations_dict
            except Exception as e:
                print(f"Error in batch: {e}")
                return {}

        # Create batches
        batches = [terms_to_translate[i:i+batch_size] for i in range(0, len(terms_to_translate), batch_size)]
        translated_terms = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(translate_batch, batch): batch for batch in batches}

            for future in as_completed(future_to_batch):
                try:
                    batch_translations = future.result()
                    translated_terms.update(batch_translations)
                except Exception as e:
                    print(f"Batch failed: {e}")

        # Update terms data with translations
        for term, translation in translated_terms.items():
            if term in terms_data:
                terms_data[term]['translated'] = translation

        # Save updated terms
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)

        # Update project glossary
        glossary = {term: data['translated'] for term, data in terms_data.items()
                   if data.get('translated')}
        self.glossary.update(glossary)
        self.save_glossary()

        return translated_terms

    def run_three_stage_pipeline(self, provider, extract_threads: int = 1, glossary_threads: int = 1,
                               translate_threads: int = 1, extract_batch_size: int = 10,
                               glossary_batch_size: int = 10, translate_batch_size: int = 5,
                               skip_extract: bool = False, skip_glossary: bool = False,
                               max_extract_entries: Optional[int] = None) -> Dict[str, Any]:
        """Run complete 3-stage translation pipeline

        Args:
            provider: AI provider instance
            extract_threads: Threads for term extraction
            glossary_threads: Threads for glossary translation
            translate_threads: Threads for main translation (future use)
            extract_batch_size: Batch size for term extraction
            glossary_batch_size: Batch size for glossary translation
            translate_batch_size: Batch size for main translation
            skip_extract: Skip term extraction stage
            skip_glossary: Skip glossary translation stage
            max_extract_entries: Maximum entries for extraction (testing)

        Returns:
            Dictionary with pipeline results and statistics
        """
        results = {
            "stages_completed": [],
            "extracted_terms": 0,
            "translated_terms": 0,
            "pipeline_success": False
        }

        try:
            # Stage 1: Extract terms
            if not skip_extract:
                print("📋 Stage 1: Extracting terms from source texts...")
                extracted_terms = self.extract_terms_from_sources(
                    provider=provider,
                    max_entries=max_extract_entries,
                    batch_size=extract_batch_size,
                    max_workers=extract_threads
                )
                results["extracted_terms"] = len(extracted_terms)
                results["stages_completed"].append("extract")
                print(f"✅ Extracted {len(extracted_terms)} unique terms")
            else:
                print("📋 Stage 1: Skipped (using existing extracted terms)")

            # Stage 2: Translate glossary
            if not skip_glossary:
                print("📚 Stage 2: Translating glossary terms...")
                translated_terms = self.translate_extracted_glossary(
                    provider=provider,
                    batch_size=glossary_batch_size,
                    max_workers=glossary_threads
                )
                results["translated_terms"] = len(translated_terms)
                results["stages_completed"].append("glossary")
                print(f"✅ Translated {len(translated_terms)} terms")
            else:
                print("📚 Stage 2: Skipped (using existing glossary)")

            # Stage 3: Main translation (using existing translate method)
            print("🎮 Stage 3: Translating game content with glossary...")
            # Note: This would call existing translation logic
            # For now, we'll just mark stage as ready
            results["stages_completed"].append("translate_ready")
            print("✅ Ready for main translation (run translate command)")

            results["pipeline_success"] = True
            return results

        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            results["error"] = str(e)
            return results