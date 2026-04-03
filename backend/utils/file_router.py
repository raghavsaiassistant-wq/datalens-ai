"""
file_router.py

Single entry point routing files to their correct parser.
"""
import os
import logging
from pathlib import Path
from parsers.csv_parser import CSVParser
from parsers.excel_parser import ExcelParser
from parsers.sql_parser import SQLParser
from parsers.json_parser import JSONParser
from parsers.pdf_parser import PDFParser
from parsers.image_parser import ImageParser

logger = logging.getLogger("FileRouter")

class FileRouter:
    
    EXTENSION_MAP = {
        ".csv":  CSVParser,
        ".txt":  CSVParser,
        ".xlsx": ExcelParser,
        ".xls":  ExcelParser,
        ".sql":  SQLParser,
        ".json": JSONParser,
        ".pdf":  PDFParser,
        ".png":  ImageParser,
        ".jpg":  ImageParser,
        ".jpeg": ImageParser,
        ".webp": ImageParser,
    }

    @classmethod
    def route(cls, file_path: str, file_name: str, nim_client=None):
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext not in cls.EXTENSION_MAP:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {list(cls.EXTENSION_MAP.keys())}")
            
        parser_class = cls.EXTENSION_MAP[ext]
        parser = parser_class()
        
        if parser_class in (PDFParser, ImageParser):
            profile = parser.parse(file_path, file_name, nim_client=nim_client)
        else:
            profile = parser.parse(file_path, file_name)
            
        logger.info(f"Routed {file_name} ({ext}) to {parser_class.__name__}")
        return profile
        
    @classmethod
    def get_supported_extensions(cls) -> list:
        return sorted(list(cls.EXTENSION_MAP.keys()))
        
    @classmethod
    def validate_file_size(cls, file_path: str, max_mb: float = 25.0) -> None:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_mb:
            raise ValueError(f"File too large: {size_mb:.2f}MB. Maximum: {max_mb}MB")
