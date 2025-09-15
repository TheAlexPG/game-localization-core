"""Base class for file importers"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BaseImporter(ABC):
    """Base class for all file importers"""

    @abstractmethod
    def import_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Import file and return list of entry dictionaries.

        Each dictionary should contain:
        - key: unique identifier
        - source_text: original text
        - context (optional): additional context
        - file_path (optional): source file path
        - metadata (optional): any additional data
        """
        pass

    def import_directory(self, dir_path: Path, pattern: str = "*") -> List[Dict[str, Any]]:
        """Import all matching files from directory"""
        entries = []
        dir_path = Path(dir_path)

        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                try:
                    file_entries = self.import_file(file_path)
                    entries.extend(file_entries)
                except Exception as e:
                    print(f"Error importing {file_path}: {e}")

        return entries

    def validate_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate that entry has required fields"""
        return "key" in entry and "source_text" in entry