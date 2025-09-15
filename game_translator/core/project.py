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

        config = state["config"]
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
                    "translation": entry.translated_text,
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

        # Load config
        self.config = ProjectConfig.from_dict(state["config"])
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