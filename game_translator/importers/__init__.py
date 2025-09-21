"""Import system for various file formats"""

from typing import Dict, Type
from .base import BaseImporter


_importers: Dict[str, Type[BaseImporter]] = {}


def register_importer(format: str, importer_class: Type[BaseImporter]):
    """Register an importer for a specific format"""
    _importers[format.lower()] = importer_class


def get_importer(format: str) -> BaseImporter:
    """Get importer instance for a specific format"""
    format = format.lower()
    if format not in _importers:
        raise ValueError(f"No importer registered for format: {format}")
    return _importers[format]()


# Import and register available importers
from .json_importer import JsonImporter
from .csv_importer import CSVImporter, TSVImporter

register_importer("json", JsonImporter)
register_importer("csv", CSVImporter)
register_importer("tsv", TSVImporter)