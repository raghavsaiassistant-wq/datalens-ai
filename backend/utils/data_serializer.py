"""
data_serializer.py

Serializes a DataFrame + DataProfile into a frontend-friendly dict
with sampled records, column stats, top correlations, and KPI series.
"""
import math
import logging
import pandas as pd
import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parsers.base_parser import DataProfile

logger = logging.getLogger("DataSerializer")

MAX_RECORDS = 30000


class DataSerializer:
    """
    Converts raw DataProfile + DataFrame into a structured payload
    that the frontend DataStore can consume directly.
    """

    def serialize_for_frontend(self, df: pd.DataFrame, profile) -> dict:
        """
        Args:
            df:      The full (or already-sampled) DataFrame
            profile: DataProfile from the parser

        Returns:
        {
          "records":          list of dicts (≤30k rows),
          "sampled":          bool,
          "sample_size":      int,
          "column_stats":     {col: {min,max,mean,median,std,q25,q75}},
          "top_correlations": [{col_a, col_b, r}],
          "kpi_series":       {col: [values]}
        }
        """
        try:
            sampled = False
            if len(df) > MAX_RECORDS:
                df = df.sample(MAX_RECORDS, random_state=42).reset_index(drop=True)
                sampled = True

            df = self._clean_df(df)

            records = df.to_dict(orient='records')
            column_stats = self._compute_column_stats(df, profile)
            top_correlations = self._compute_top_correlations(df, profile)
            kpi_series = self._extract_kpi_series(df, profile)

            return {
                "records": records,
                "sampled": sampled,
                "sample_size": len(records),
                "column_stats": column_stats,
                "top_correlations": top_correlations,
                "kpi_series": kpi_series
            }

        except Exception as e:
            logger.error(f"DataSerializer failed: {e}")
            return {
                "records": [],
                "sampled": False,
                "sample_size": 0,
                "column_stats": {},
                "top_correlations": [],
                "kpi_series": {}
            }

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace NaN/inf with None and convert datetime cols to ISO strings."""
        df = df.copy()
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%dT%H:%M:%S').where(df[col].notna(), None)
            elif pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].apply(
                    lambda x: None if (x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))) else x
                )
        return df

    def _compute_column_stats(self, df: pd.DataFrame, profile) -> dict:
        stats = {}
        numeric_cols = [c for c, t in profile.column_types.items() if t == 'numeric' and c in df.columns]
        for col in numeric_cols:
            s = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(s) == 0:
                continue
            try:
                stats[col] = {
                    "min":    self._safe_float(s.min()),
                    "max":    self._safe_float(s.max()),
                    "mean":   self._safe_float(s.mean()),
                    "median": self._safe_float(s.median()),
                    "std":    self._safe_float(s.std()),
                    "q25":    self._safe_float(s.quantile(0.25)),
                    "q75":    self._safe_float(s.quantile(0.75))
                }
            except Exception:
                pass
        return stats

    def _compute_top_correlations(self, df: pd.DataFrame, profile) -> list:
        numeric_cols = [c for c, t in profile.column_types.items() if t == 'numeric' and c in df.columns]
        if len(numeric_cols) < 2:
            return []
        try:
            corr_matrix = df[numeric_cols].apply(pd.to_numeric, errors='coerce').corr()
            pairs = (
                corr_matrix
                .unstack()
                .reset_index()
                .rename(columns={'level_0': 'col_a', 'level_1': 'col_b', 0: 'r'})
            )
            # Remove self-correlations and duplicates
            pairs = pairs[pairs['col_a'] < pairs['col_b']]
            pairs = pairs[pairs['r'].abs() > 0.3].dropna()
            pairs = pairs.sort_values('r', key=abs, ascending=False).head(10)
            return [
                {"col_a": row.col_a, "col_b": row.col_b, "r": round(float(row.r), 4)}
                for row in pairs.itertuples()
            ]
        except Exception:
            return []

    def _extract_kpi_series(self, df: pd.DataFrame, profile) -> dict:
        kpi_series = {}
        for col in profile.kpi_columns:
            if col not in df.columns:
                continue
            try:
                values = pd.to_numeric(df[col], errors='coerce').tolist()
                kpi_series[col] = [None if (v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))) else v for v in values]
            except Exception:
                pass
        return kpi_series

    def _safe_float(self, val) -> float | None:
        try:
            f = float(val)
            return None if (math.isnan(f) or math.isinf(f)) else round(f, 6)
        except Exception:
            return None
