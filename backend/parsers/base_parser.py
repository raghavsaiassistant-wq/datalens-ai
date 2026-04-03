"""
base_parser.py

Defines the DataProfile schema and the BaseParser interface for all data parsers.
"""
from dataclasses import dataclass
import pandas as pd
from typing import List, Dict, Any
import chardet
from pathlib import Path

@dataclass
class DataProfile:
    """Structure containing the full analytical profile of an uploaded dataset."""
    # Raw data
    df: pd.DataFrame
    source_type: str
    file_name: str
    
    # Shape
    rows: int
    cols: int
    
    # Column info
    columns: list
    dtypes: dict
    
    # Quality
    nulls: dict
    null_pct: dict
    duplicates: int
    
    # Stats
    numeric_summary: dict
    sample: list
    
    # AI-ready
    text_content: str
    column_types: dict
    has_datetime: bool
    has_numeric: bool
    kpi_columns: list
    
    # Processing
    processing_time: float
    warnings: list

class BaseParser:
    """Base class defining the contract for data source parsers."""

    def parse(self, file_path: str, file_name: str) -> DataProfile:
        """Abstract method to parse a file and return a DataProfile."""
        raise NotImplementedError("Subclasses must implement parse()")

    def _validate_file(self, file_path: str, allowed_extensions: List[str]) -> None:
        """
        Validates that the file exists and has an allowed extension.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        if ext not in allowed_extensions:
            raise ValueError(f"Invalid file extension: {ext}. Allowed: {allowed_extensions}")

    def _detect_encoding(self, file_path: str) -> str:
        """
        Detects the file encoding using chardet, falling back to try utf-8, latin-1, cp1252.
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            if result['encoding']:
                return result['encoding']
        except Exception:
            pass
            
        return "utf-8"
