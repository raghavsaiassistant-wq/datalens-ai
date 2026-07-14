"""
file_router.py — Single entry point routing files to their correct parser.
PDF/Image parsers are lazy-imported to avoid loading PyMuPDF on CSV-only apps.
"""
import os
import logging
from pathlib import Path
from parsers.csv_parser import CSVParser
from parsers.excel_parser import ExcelParser
from parsers.sql_parser import SQLParser
from parsers.json_parser import JSONParser

logger = logging.getLogger("FileRouter")


def _lazy_pdf_parser():
    from parsers.pdf_parser import PDFParser
    return PDFParser


def _lazy_image_parser():
    from parsers.image_parser import ImageParser
    return ImageParser


class FileRouter:

    EXTENSION_MAP = {
        ".csv":  CSVParser,
        ".txt":  CSVParser,
        ".xlsx": ExcelParser,
        ".xls":  ExcelParser,
        ".sql":  SQLParser,
        ".json": JSONParser,
        ".pdf":  None,  # lazy
        ".png":  None,  # lazy
        ".jpg":  None,  # lazy
        ".jpeg": None,  # lazy
        ".webp": None,  # lazy
    }

    @classmethod
    def route(cls, file_path: str, file_name: str, ollama_client=None, max_rows: int = None):
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in cls.EXTENSION_MAP:
            raise ValueError(f"Unsupported file type: {ext}. Supported: {list(cls.EXTENSION_MAP.keys())}")

        parser_class = cls.EXTENSION_MAP[ext]
        if parser_class is None:
            # Lazy load vision parsers
            if ext == ".pdf":
                parser = _lazy_pdf_parser()()
            else:  # image
                parser = _lazy_image_parser()()
        else:
            parser = parser_class()

        if ext in (".pdf", ".png", ".jpg", ".jpeg", ".webp"):
            profile = parser.parse(file_path, file_name, ollama_client=ollama_client)
        else:
            profile = parser.parse(file_path, file_name, max_rows=max_rows)

        logger.info(f"Routed {file_name} ({ext}) to {type(parser).__name__}")
        return profile

    @classmethod
    def get_supported_extensions(cls) -> list:
        return sorted([k for k in cls.EXTENSION_MAP.keys()])

    @classmethod
    def validate_file_size(cls, file_path: str, max_mb: float = 25.0) -> None:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_mb:
            raise ValueError(f"File too large: {size_mb:.2f}MB. Maximum: {max_mb}MB")
