"""
json_parser.py

Handles hierarchical JSON data by flattening logic.
"""
import json
import time
import pandas as pd
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class JSONParser(BaseParser):
    def parse(self, file_path: str, file_name: str) -> DataProfile:
        start_time = time.time()
        warnings = []
        
        self._validate_file(file_path, ['.json'])
        encoding = self._detect_encoding(file_path)

        # Try detected encoding first, fall back through common encodings on UnicodeDecodeError
        data = None
        for enc in [encoding, 'utf-8', 'utf-8-sig', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=enc, errors='replace') as f:
                    data = json.load(f)
                break
            except (UnicodeDecodeError, LookupError):
                continue
            except json.JSONDecodeError:
                break  # Readable but malformed — no point retrying with another encoding
        if data is None:
            raise ValueError("Could not decode JSON file. Ensure the file is valid UTF-8 JSON.")
            
        df = None
        
        if isinstance(data, list) and all(isinstance(x, dict) for x in data):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            list_keys = [k for k, v in data.items() if isinstance(v, list)]
            if len(list_keys) == 1 and all(isinstance(x, dict) for x in data[list_keys[0]]):
                df = pd.DataFrame(data[list_keys[0]])
                warnings.append(f"Used object key '{list_keys[0]}' as root array.")
            else:
                df = pd.DataFrame.from_dict(data, orient="index")
        elif isinstance(data, list):
            df = pd.DataFrame(data, columns=["value"])
            
        if df is None or df.empty:
            df = pd.json_normalize(data, max_level=2)
            
        if df.empty:
            raise ValueError("Cannot parse JSON structure into tabular format")
            
        cols_to_drop = []
        for c in list(df.columns)[:20]:  # cap at 20 cols to avoid slow flattening on huge schemas
            try:
                if df[c].apply(lambda x: isinstance(x, (dict, list))).any():
                    flattened = pd.json_normalize(df[c].dropna().head(1000))
                    if len(flattened.columns) > 50:
                        # Too many nested keys — just drop the column
                        cols_to_drop.append(c)
                        warnings.append(f"Dropped deeply nested column '{c}' (>{len(flattened.columns)} sub-fields)")
                        continue
                    flattened.columns = [f"{c}_{fc}" for fc in flattened.columns]
                    flattened.index = df.index[:len(flattened)]
                    df = pd.concat([df, flattened], axis=1)
                    cols_to_drop.append(c)
                    warnings.append(f"Flattened nested column '{c}'")
            except Exception:
                cols_to_drop.append(c)
                warnings.append(f"Skipped un-flattenable column '{c}'")
                
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
            
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        if len(df) > 100000:
            df = df.sample(n=50000, random_state=42).copy()
            warnings.append("File over 100,000 rows. Sampled 50,000 rows for analysis.")
            
        processing_time = round(time.time() - start_time, 2)
        return DataProfiler.profile(df, "json", file_name, processing_time, warnings)
