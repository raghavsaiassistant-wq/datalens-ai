"""
sql_parser.py

Parses SQL files to extract tabular data safely and gracefully.
Never executes DROP, DELETE, TRUNCATE, or touches system tables.
"""
import time
import re
import sqlite3
import pandas as pd
import sqlparse
from parsers.base_parser import BaseParser, DataProfile
from utils.data_profiler import DataProfiler

class SQLParser(BaseParser):
    def parse(self, file_path: str, file_name: str) -> DataProfile:
        start_time = time.time()
        warnings = []
        
        self._validate_file(file_path, ['.sql'])
        encoding = self._detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding, errors="replace") as f:
            raw_text = f.read()

        raw_text = re.sub(r'--.*$', '', raw_text, flags=re.MULTILINE)
        raw_text = re.sub(r'/\*.*?\*/', '', raw_text, flags=re.DOTALL)
        
        statements = sqlparse.split(raw_text)
        
        safe_statements = []
        for stmt in statements:
            stmt_clean = stmt.strip().upper()
            if not stmt_clean: continue
            
            if any(danger in stmt_clean for danger in ["DROP ", "DELETE ", "TRUNCATE ", "UPDATE ", "ALTER ", "SQLITE_MASTER", "SQLITE_TEMP_MASTER"]):
                warnings.append("Skipped potentially dangerous statement or system table reference")
                continue
            
            if stmt_clean.startswith("SELECT ") or stmt_clean.startswith("CREATE ") or stmt_clean.startswith("INSERT "):
                safe_statements.append(stmt.strip())
                
        selects = [s for s in safe_statements if s.upper().startswith("SELECT")]
        creates = [s for s in safe_statements if s.upper().startswith("CREATE")]
        inserts = [s for s in safe_statements if s.upper().startswith("INSERT")]
        
        df = pd.DataFrame()
        columns = set()
        
        # STRATEGY A & B
        try:
            if safe_statements:
                conn = sqlite3.connect(":memory:")
                cur = conn.cursor()
                
                for c in creates: cur.execute(c)
                for i in inserts: cur.execute(i)
                conn.commit()
                
                if selects:
                    # Strategy A
                    dfs = []
                    for s in selects:
                        try: dfs.append(pd.read_sql_query(s, conn))
                        except Exception: pass
                    if dfs:
                        df = max(dfs, key=len)
                elif creates or inserts:
                    # Strategy B
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cur.fetchall()
                    dfs = []
                    for t in tables:
                        try: dfs.append(pd.read_sql_query(f"SELECT * FROM {t[0]};", conn))
                        except Exception: pass
                    if dfs:
                        df = max(dfs, key=len)
                conn.close()
        except Exception as e:
            warnings.append(f"SQL execution failed: {e}")
            
        # STRATEGY C
        if df.empty:
            for stmt in creates:
                matches = re.findall(r'\b([A-Za-z0-9_]+)\b\s+(?:INTEGER|TEXT|REAL|VARCHAR|INT|FLOAT|DATE)', stmt, re.IGNORECASE)
                columns.update(matches)
            
            matches = re.findall(r'INSERT\s+INTO\s+[A-Za-z0-9_]+\s*\((.*?)\)', raw_text, re.IGNORECASE)
            for m in matches:
                cols = [c.strip() for c in m.split(',')]
                columns.update(cols)
                
            if columns:
                df = pd.DataFrame(columns=list(columns))
            warnings.append("SQL file contains no executable data queries. Schema extracted only.")
            
        if df.empty and not columns:
            raise ValueError("SQL produced no data rows and no schema could be detected.")
            
        if len(df) > 100000:
            df = df.sample(n=50000, random_state=42).copy()
            warnings.append("File over 100,000 rows. Sampled 50,000 rows for analysis.")
            
        processing_time = round(time.time() - start_time, 2)
        return DataProfiler.profile(df, "sql", file_name, processing_time, warnings)
