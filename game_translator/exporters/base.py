"""Base class for file exporters"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional


class BaseExporter(ABC):
    """Base class for all file exporters"""

    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: Path,
               glossary: Optional[Dict[str, str]] = None):
        """
        Export translation data to file.

        Args:
            data: Export data from project.export_for_review()
            output_path: Path to output file
            glossary: Optional glossary dictionary
        """
        pass

    def ensure_output_dir(self, output_path: Path):
        """Ensure output directory exists"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)