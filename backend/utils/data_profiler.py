"""
data_profiler.py

Generates a comprehensive statistical profile from a raw Pandas DataFrame.
"""
import pandas as pd
import json

class DataProfiler:
    """Stateless profiler that computes metrics and schemas for datasets."""

    @staticmethod
    def profile(df: pd.DataFrame, source_type: str, file_name: str, processing_time: float, warnings: list) -> 'DataProfile': # type: ignore
        """
        Computes all profiling metrics for a given DataFrame step-by-step.
        """
        from parsers.base_parser import DataProfile
        
        # STEP 1: Basic shape
        rows, cols = df.shape
        columns = df.columns.tolist()
        dtypes = {col: str(df[col].dtype) for col in columns}

        # STEP 2: Null analysis
        nulls = {col: int(df[col].isnull().sum()) for col in columns}
        null_pct = {col: round(nulls[col] / rows * 100, 1) if rows > 0 else 0.0 for col in columns}
        
        for col, pct in null_pct.items():
            if pct > 30.0:
                warnings.append(f"Column '{col}' has {pct}% missing values")

        # STEP 3: Duplicate detection
        duplicates = int(df.duplicated().sum())
        if duplicates > 0:
            warnings.append(f"Found {duplicates} duplicate rows")

        # STEP 4: Column type classification
        column_types = {}
        for col in columns:
            dt = df[col].dtype
            col_lower = str(col).lower()
            unique_count = df[col].nunique()

            if pd.api.types.is_datetime64_any_dtype(dt) or any(x in col_lower for x in ["date", "time", "year", "month", "day"]):
                column_types[col] = "datetime"
            elif pd.api.types.is_bool_dtype(dt):
                # bool must come before numeric — pandas treats bool as numeric dtype
                column_types[col] = "categorical"
            elif pd.api.types.is_numeric_dtype(dt):
                column_types[col] = "numeric"
            elif col_lower.endswith("_id") or col_lower == "id":
                if rows > 0 and (unique_count / rows) > 0.8:
                    column_types[col] = "id"
                else:
                    column_types[col] = "categorical"
            elif pd.api.types.is_object_dtype(dt):
                if rows > 0 and (unique_count / rows) < 0.5:
                    column_types[col] = "categorical"
                else:
                    column_types[col] = "text"
            else:
                column_types[col] = "text"
        
        has_datetime = any(v == "datetime" for v in column_types.values())
        has_numeric = any(v == "numeric" for v in column_types.values())

        # STEP 4b: Promote numeric-string columns (e.g. "$1,234", "12.5%", "1 000")
        for col in list(columns):
            if column_types[col] in ("categorical", "text"):
                series = df[col].dropna()
                if len(series) < 2:
                    continue
                cleaned = series.astype(str).str.replace(r'[\$,€£¥\s%]', '', regex=True)
                try:
                    num = pd.to_numeric(cleaned, errors='coerce')
                    if num.notna().sum() / len(series) >= 0.8:
                        df[col] = pd.to_numeric(
                            df[col].astype(str).str.replace(r'[\$,€£¥\s%]', '', regex=True),
                            errors='coerce'
                        )
                        column_types[col] = "numeric"
                        dtypes[col] = str(df[col].dtype)
                        has_numeric = True
                except Exception:
                    pass

        # STEP 4c: Drop datetime classification for columns where all values are NaT
        for col in list(columns):
            if column_types[col] == "datetime" and pd.api.types.is_datetime64_any_dtype(df[col]):
                if df[col].notna().sum() == 0:
                    column_types[col] = "text"
        has_datetime = any(v == "datetime" for v in column_types.values())

        # STEP 5: KPI column detection
        kpi_keywords = ["revenue", "sales", "profit", "amount", "total", "count", 
                        "price", "cost", "value", "quantity", "qty", "income", 
                        "loss", "margin", "growth", "rate", "score", "salary"]
        kpi_columns = []
        for col in columns:
            if column_types[col] == "numeric":
                col_lower = str(col).lower()
                if any(kw in col_lower for kw in kpi_keywords):
                    kpi_columns.append(col)

        # STEP 6: Numeric summary
        numeric_cols = [c for c in columns if column_types[c] == "numeric"]
        # Exclude any residual bool columns that pandas may still consider numeric
        numeric_cols = [c for c in numeric_cols if not pd.api.types.is_bool_dtype(df[c].dtype)]
        numeric_summary = {}
        if numeric_cols:
            desc = df[numeric_cols].describe().to_dict()
            for c in desc:
                numeric_summary[c] = {k: round(v, 2) if pd.notnull(v) else None for k, v in desc[c].items()}

        # STEP 7: Sample rows
        sample_df = df.head(5).copy()
        for col in sample_df.columns:
            if column_types[col] == "datetime" or pd.api.types.is_datetime64_any_dtype(sample_df[col]):
                sample_df[col] = sample_df[col].astype(str)
            else:
                # convert numpy types to native
                sample_df[col] = sample_df[col].apply(lambda x: x.item() if hasattr(x, 'item') else x)
        
        # Handle nan for json serialization
        sample_df = sample_df.fillna("None")
        sample = sample_df.to_dict(orient='records')

        # STEP 8: Text content for AI
        col_list_str = ""
        for col in columns:
            ctype = column_types[col]
            npct = null_pct[col]
            ucount = df[col].nunique()
            col_list_str += f"{col}: {ctype} | nulls: {npct}% | unique: {ucount}\n"

        num_stat_str = ""
        for col in numeric_cols:
            stat = numeric_summary.get(col)
            if stat:
                num_stat_str += f"{col}: min={stat.get('min')}, max={stat.get('max')}, mean={stat.get('mean')}, std={stat.get('std')}\n"
            else:
                num_stat_str += f"{col}: No statistical data available.\n"

        sample_str = json.dumps(sample[:3], indent=2, ensure_ascii=False)

        text_content = f"Dataset: {file_name}\n"
        text_content += f"Shape: {rows} rows × {cols} columns\n"
        text_content += f"Source: {source_type}\n\n"
        text_content += f"Columns and Types:\n{col_list_str}\n"
        text_content += f"Numeric Statistics:\n{num_stat_str}\n"
        text_content += f"KPI Columns Detected: {kpi_columns}\n"
        
        datetime_cols = [c for c, t in column_types.items() if t == "datetime"]
        text_content += f"Date Columns Detected: {datetime_cols}\n"
        text_content += f"Data Quality Warnings: {warnings}\n\n"
        text_content += f"Sample Data (first 3 rows):\n{sample_str}\n"
        
        if len(text_content) > 8000:
            text_content = text_content[:7997] + "..."

        # STEP 9: Return DataProfile
        return DataProfile(
            df=df,
            source_type=source_type,
            file_name=file_name,
            rows=rows,
            cols=cols,
            columns=columns,
            dtypes=dtypes,
            nulls=nulls,
            null_pct=null_pct,
            duplicates=duplicates,
            numeric_summary=numeric_summary,
            sample=sample,
            text_content=text_content,
            column_types=column_types,
            has_datetime=has_datetime,
            has_numeric=has_numeric,
            kpi_columns=kpi_columns,
            processing_time=processing_time,
            warnings=warnings
        )
