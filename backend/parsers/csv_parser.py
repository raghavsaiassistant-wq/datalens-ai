"""
csv_parser.py

Parser responsible for loading, cleaning, and profiling CSV files.
"""
import pandas as pd
import time
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class CSVParser(BaseParser):
    """Parser for CSV data sources."""
    
    def parse(self, file_path: str, file_name: str) -> DataProfile:
        """
        Parses a CSV file and routes it through the DataProfiler.
        """
        start_time = time.time()
        warnings = []
        
        # 1. Validate extension
        self._validate_file(file_path, ['.csv'])
        
        # 2. Detect encoding
        encoding = self._detect_encoding(file_path)
        
        # 3 & 4. Read CSV with detected encoding or fallback
        try:
            df = pd.read_csv(file_path, encoding=encoding)
        except Exception:
            df = pd.read_csv(file_path, encoding="latin-1", on_bad_lines="skip")
            warnings.append("Failed to read with detected encoding. Fell back to latin-1.")
            
        # Error handling
        if df.empty and len(df.columns) == 0:
            raise ValueError("File is empty")
        if len(df.columns) == 0:
            raise ValueError("No columns detected")
            
        # 5. Drop completely empty rows and columns
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        if df.empty:
            raise ValueError("All data is null")
            
        # 6. Strip whitespace
        str_cols = df.select_dtypes(['object']).columns
        for c in str_cols:
            df[c] = df[c].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
        # 7. Try to parse datetime
        for c in df.columns:
            if any(x in str(c).lower() for x in ["date", "time"]):
                try:
                    df[c] = pd.to_datetime(df[c])
                except Exception:
                    pass
                    
        # 8. Large file check
        if len(df) > 100000:
            df = df.sample(n=50000, random_state=42).copy()
            warnings.append("File over 100,000 rows. Sampled 50,000 rows for analysis.")
            
        processing_time = round(time.time() - start_time, 2)
        
        # 9. Return DataProfile
        return DataProfiler.profile(df, "csv", file_name, processing_time, warnings)
