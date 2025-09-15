"""JSON file importer"""

import json
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseImporter


class JsonImporter(BaseImporter):
    """Import JSON files in various formats"""

    def __init__(self, key_field: str = "key", text_field: str = "text",
                 translation_field: str = "translation"):
        """
        Initialize JSON importer.

        Args:
            key_field: Field name for entry key
            text_field: Field name for source text
            translation_field: Field name for translation (if exists)
        """
        self.key_field = key_field
        self.text_field = text_field
        self.translation_field = translation_field

    def import_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Import JSON file and extract entries"""
        entries = []
        file_path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, dict):
            entries.extend(self._process_dict(data, file_path))
        elif isinstance(data, list):
            entries.extend(self._process_list(data, file_path))
        else:
            raise ValueError(f"Unsupported JSON structure in {file_path}")

        # Validate all entries
        valid_entries = [e for e in entries if self.validate_entry(e)]
        if len(valid_entries) < len(entries):
            print(f"Warning: Skipped {len(entries) - len(valid_entries)} invalid entries from {file_path}")

        return valid_entries

    def _process_dict(self, data: Dict, file_path: Path) -> List[Dict[str, Any]]:
        """Process dictionary-based JSON structure"""
        entries = []

        for key, value in data.items():
            if isinstance(value, str):
                # Simple key-value format: {"key1": "text1", "key2": "text2"}
                entry = {
                    "key": key,
                    "source_text": value,
                    "file_path": str(file_path)
                }
                entries.append(entry)

            elif isinstance(value, dict):
                # Nested format: {"key1": {"text": "...", "context": "..."}}
                entry = {
                    "key": key,
                    "source_text": value.get(self.text_field, ""),
                    "file_path": str(file_path)
                }

                # Add optional fields if present
                if "context" in value:
                    entry["context"] = value["context"]
                if self.translation_field in value:
                    entry["translated_text"] = value[self.translation_field]
                if "metadata" in value:
                    entry["metadata"] = value["metadata"]

                entries.append(entry)

            elif isinstance(value, list):
                # Array format for multiple texts per key
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        entry = {
                            "key": f"{key}[{i}]",
                            "source_text": item,
                            "file_path": str(file_path)
                        }
                        entries.append(entry)

        return entries

    def _process_list(self, data: List, file_path: Path) -> List[Dict[str, Any]]:
        """Process list-based JSON structure"""
        entries = []

        for i, item in enumerate(data):
            if isinstance(item, dict):
                # List of objects: [{"key": "...", "text": "..."}, ...]
                if self.key_field in item:
                    key = item[self.key_field]
                else:
                    # Generate key if not present
                    key = f"{file_path.stem}_{i}"

                entry = {
                    "key": key,
                    "source_text": item.get(self.text_field, ""),
                    "file_path": str(file_path)
                }

                # Add optional fields
                if "context" in item:
                    entry["context"] = item["context"]
                if self.translation_field in item:
                    entry["translated_text"] = item[self.translation_field]
                if "metadata" in item:
                    entry["metadata"] = item["metadata"]

                entries.append(entry)

            elif isinstance(item, str):
                # Simple list of strings
                entry = {
                    "key": f"{file_path.stem}_{i}",
                    "source_text": item,
                    "file_path": str(file_path)
                }
                entries.append(entry)

        return entries