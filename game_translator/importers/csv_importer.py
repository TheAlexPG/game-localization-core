"""CSV file importer for game localization"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseImporter


class CSVImporter(BaseImporter):
    """Import CSV files with localization data"""

    def __init__(self, delimiter: str = ',', encoding: str = 'utf-8-sig'):
        """
        Initialize CSV importer.

        Args:
            delimiter: CSV delimiter character (default: ',', can be '\t' for TSV)
            encoding: File encoding (default: 'utf-8-sig' to handle BOM)
        """
        self.delimiter = delimiter
        self.encoding = encoding

    def import_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Import CSV file and return list of entry dictionaries.

        Expected CSV format:
        - First row contains headers
        - Must have 'key' and either 'source' or 'text' column
        - Optional 'target' column for existing translations
        - Optional 'context' column for additional context

        Args:
            file_path: Path to CSV file

        Returns:
            List of entry dictionaries
        """
        entries = []
        file_path = Path(file_path)

        # Try to detect delimiter if tab-separated
        with open(file_path, 'r', encoding=self.encoding) as f:
            first_line = f.readline()
            if '\t' in first_line and ',' not in first_line:
                self.delimiter = '\t'

        with open(file_path, 'r', encoding=self.encoding, newline='') as csvfile:
            # Try to detect dialect
            sample = csvfile.read(1024)
            csvfile.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(csvfile, dialect=dialect)
            except:
                # Fallback to default delimiter
                reader = csv.DictReader(csvfile, delimiter=self.delimiter)

            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
                # Find the key column (case-insensitive)
                key = None
                for k in ['key', 'Key', 'KEY', 'id', 'Id', 'ID']:
                    if k in row:
                        key = row[k]
                        break

                if not key:
                    print(f"Warning: Row {row_num} missing key field, skipping")
                    continue

                # Find the source text column
                source_text = None
                for k in ['source', 'Source', 'SOURCE', 'text', 'Text', 'TEXT', 'original', 'Original']:
                    if k in row:
                        source_text = row[k]
                        break

                if not source_text:
                    print(f"Warning: Row {row_num} (key: {key}) missing source text, skipping")
                    continue

                # Build entry dictionary
                entry = {
                    'key': key.strip() if key else '',
                    'source_text': source_text.strip() if source_text else '',
                    'file_path': str(file_path),
                    'metadata': {
                        'row_number': row_num,
                        'format': 'csv'
                    }
                }

                # Add target/translation if exists
                for k in ['target', 'Target', 'TARGET', 'translation', 'Translation', 'translated']:
                    if k in row and row[k]:
                        entry['translated_text'] = row[k].strip()
                        break

                # Add context if exists
                for k in ['context', 'Context', 'CONTEXT', 'description', 'Description']:
                    if k in row and row[k]:
                        entry['context'] = row[k].strip()
                        break

                # Add any other columns as metadata
                for k, v in row.items():
                    if k not in ['key', 'source', 'target', 'context', 'text', 'translation'] and v:
                        entry['metadata'][k] = v

                entries.append(entry)

        return entries


class TSVImporter(CSVImporter):
    """Import TSV (Tab-Separated Values) files"""

    def __init__(self, encoding: str = 'utf-8'):
        """Initialize TSV importer with tab delimiter"""
        super().__init__(delimiter='\t', encoding=encoding)