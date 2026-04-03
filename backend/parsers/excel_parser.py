"""
excel_parser.py

Parser responsible for loading, cleaning, and profiling Excel files (.xlsx, .xls).
"""
import pandas as pd
import time
import openpyxl
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class ExcelParser(BaseParser):
    """Parser for Excel data sources."""
    
    def parse(self, file_path: str, file_name: str) -> DataProfile:
        """
        Parses an Excel file by selecting the largest sheet and profiling it.
        """
        start_time = time.time()
        warnings = []
        
        # 1. Validate extension
        self._validate_file(file_path, ['.xlsx', '.xls'])
        
        # Check for merged cells using openpyxl (only for .xlsx)
        if str(file_path).endswith('.xlsx'):
            try:
                wb = openpyxl.load_workbook(file_path, read_only=True)
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    if hasattr(ws, 'merged_cells') and len(ws.merged_cells.ranges) > 0:
                        warnings.append("Merged cells detected, data may be misaligned")
                        break
                wb.close()
            except Exception:
                pass
        
        # 2. Read all sheets
        ef = pd.ExcelFile(file_path)
        sheet_names = ef.sheet_names
        
        if not sheet_names:
            raise ValueError("File is empty (no sheets)")
            
        chosen_sheet = sheet_names[0]
        
        # 3. Find largest sheet if multiple
        if len(sheet_names) > 1:
            max_rows = -1
            for sheet in sheet_names:
                df_shape = ef.parse(sheet)
                if len(df_shape) > max_rows:
                    max_rows = len(df_shape)
                    chosen_sheet = sheet
            warnings.append(f"Multiple sheets found: {sheet_names}. Using largest: {chosen_sheet}")
            
        # 4. Read chosen sheet
        df = ef.parse(chosen_sheet)
        
        if df.empty and len(df.columns) == 0:
            raise ValueError("File is empty")
        if len(df.columns) == 0:
            raise ValueError("No columns detected")
            
        # Title row check
        if len(df) > 0:
            first_row_non_null = df.iloc[0].count()
            if first_row_non_null == 1 and len(df.columns) > 1:
                df = ef.parse(chosen_sheet, skiprows=1)
                warnings.append("Skipped first row (detected as title)")
                
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
        
        # 9. Return profiling
        return DataProfiler.profile(df, "excel", file_name, processing_time, warnings)
