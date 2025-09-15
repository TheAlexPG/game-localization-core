"""JSON format exporter"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .base import BaseExporter


class JsonExporter(BaseExporter):
    """Export to JSON format"""

    def __init__(self, format_type: str = "simple"):
        """
        Initialize JSON exporter.

        Args:
            format_type: Output format type
                - "simple": {"key": "translation"}
                - "full": Complete entry data
                - "nested": {"key": {"source": "...", "translation": "..."}}
        """
        self.format_type = format_type

    def export(self, data: Dict[str, Any], output_path: Path,
               glossary: Optional[Dict[str, str]] = None):
        """Export to JSON file"""
        self.ensure_output_dir(output_path)

        entries = data.get("entries", [])

        if self.format_type == "simple":
            output_data = self._export_simple(entries)
        elif self.format_type == "full":
            output_data = self._export_full(data)
        elif self.format_type == "nested":
            output_data = self._export_nested(entries)
        else:
            output_data = self._export_simple(entries)

        # Write main file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Exported to JSON: {output_path}")

        # Export glossary separately if provided
        if glossary:
            glossary_path = output_path.parent / f"{output_path.stem}_glossary.json"
            with open(glossary_path, 'w', encoding='utf-8') as f:
                json.dump(glossary, f, indent=2, ensure_ascii=False)
            print(f"Exported glossary to JSON: {glossary_path}")

    def _export_simple(self, entries: list) -> Dict[str, str]:
        """Export as simple key-value pairs"""
        output = {}
        for entry in entries:
            key = entry.get("key", "")
            # Use translation if available, otherwise use source
            text = entry.get("translation") or entry.get("source", "")
            output[key] = text
        return output

    def _export_full(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export complete data structure"""
        return {
            "project": data.get("project", ""),
            "source_lang": data.get("source_lang", ""),
            "target_lang": data.get("target_lang", ""),
            "stats": data.get("stats", {}),
            "entries": data.get("entries", [])
        }

    def _export_nested(self, entries: list) -> Dict[str, Dict[str, Any]]:
        """Export as nested structure"""
        output = {}
        for entry in entries:
            key = entry.get("key", "")
            output[key] = {
                "source": entry.get("source", ""),
                "translation": entry.get("translation", ""),
                "status": entry.get("status", "pending"),
                "context": entry.get("context", "")
            }
        return output