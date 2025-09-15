"""Export system for various file formats"""

from typing import Dict, Type
from .base import BaseExporter


_exporters: Dict[str, Type[BaseExporter]] = {}


def register_exporter(format: str, exporter_class: Type[BaseExporter]):
    """Register an exporter for a specific format"""
    _exporters[format.lower()] = exporter_class


def get_exporter(format: str) -> BaseExporter:
    """Get exporter instance for a specific format"""
    format = format.lower()
    if format not in _exporters:
        raise ValueError(f"No exporter registered for format: {format}")
    return _exporters[format]()


# Import and register available exporters
from .table_exporter import ExcelExporter, CsvExporter
from .json_exporter import JsonExporter

register_exporter("excel", ExcelExporter)
register_exporter("xlsx", ExcelExporter)
register_exporter("csv", CsvExporter)
register_exporter("json", JsonExporter)