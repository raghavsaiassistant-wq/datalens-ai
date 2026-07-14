"""
utils/sampling.py — Smart sampling for large datasets.
Fix for Bug #3: silent 500-row sampling in findings_generator.py.
Always returns a warnings list; never silent.
"""
import logging
from typing import Tuple, List, Dict, Any
import pandas as pd

logger = logging.getLogger("Sampling")

DEFAULT_MAX_ROWS_FOR_AI = 500   # LLM context window safeguard
DEFAULT_MAX_ROWS_FOR_DISPLAY = 30000   # frontend performance safeguard


def smart_sample(
    df: pd.DataFrame,
    max_rows: int = DEFAULT_MAX_ROWS_FOR_AI,
    method: str = "random",
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Returns (sampled_df, warnings). If no sampling needed, warnings is empty.
    Methods: "random", "head", "stratified" (by first categorical column).
    """
    warnings: List[Dict[str, Any]] = []
    original_rows = len(df)
    if original_rows <= max_rows:
        return df, warnings

    if method == "head":
        sampled = df.head(max_rows)
    elif method == "stratified":
        # Stratify by first low-cardinality categorical column
        cat_cols = [c for c in df.columns
                    if df[c].dtype == "object" and df[c].nunique() <= 50 and df[c].nunique() > 1]
        if cat_cols:
            sampled = df.groupby(cat_cols[0], group_keys=False).apply(
                lambda g: g.sample(min(len(g), max(1, max_rows * len(g) // original_rows)),
                                   random_state=42)
            ).head(max_rows)
        else:
            sampled = df.sample(max_rows, random_state=42)
    else:  # random
        sampled = df.sample(max_rows, random_state=42)

    warnings.append({
        "type": "sampled",
        "original_rows": original_rows,
        "kept_rows": len(sampled),
        "method": method,
        "message": f"AI analysis ran on a sample of {len(sampled):,} rows (dataset has {original_rows:,}). "
                   f"Statistics were computed on the full dataset.",
    })
    logger.info(f"Sampled {original_rows} → {len(sampled)} rows ({method})")
    return sampled, warnings


def smart_sample_for_display(
    df: pd.DataFrame, max_rows: int = DEFAULT_MAX_ROWS_FOR_DISPLAY
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """For frontend display: cap at 30k rows to avoid tab freeze on 8GB RAM."""
    warnings: List[Dict[str, Any]] = []
    if len(df) <= max_rows:
        return df, warnings
    sampled = df.head(max_rows)
    warnings.append({
        "type": "display_capped",
        "original_rows": len(df),
        "shown_rows": max_rows,
        "message": f"Displaying the first {max_rows:,} of {len(df):,} rows. "
                   f"Use filters to focus on a subset.",
    })
    return sampled, warnings
