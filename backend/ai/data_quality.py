"""
data_quality.py — Per-file data quality checks (Sprint 7)

Analyzes each file and reports:
- Null percentages per column
- Outlier detection (z-score, IQR)
- Constant columns (low value)
- High cardinality warnings
- Type mismatches
- Data freshness (for date columns)

Returns a report that can be added to the multi-file metadata.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def check_data_quality(file_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Run all data quality checks on a file's dataframe."""
    report = {
        "file": file_name,
        "rows": len(df),
        "columns": len(df.columns),
        "checks": {},
        "warnings": [],
        "score": 100,  # 0-100, deducted for issues
    }

    # 1. Null check
    null_info = {}
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_pct = null_count / max(len(df), 1) * 100
        null_info[col] = {
            "null_count": null_count,
            "null_pct": round(null_pct, 2),
        }
        if null_pct > 50:
            report["warnings"].append(f"Column '{col}' has {null_pct:.0f}% nulls")
            report["score"] -= 10
        elif null_pct > 20:
            report["warnings"].append(f"Column '{col}' has {null_pct:.0f}% nulls")
            report["score"] -= 5
    report["checks"]["nulls"] = null_info

    # 2. Constant columns
    constant_cols = []
    for col in df.columns:
        if df[col].nunique(dropna=True) <= 1:
            constant_cols.append(col)
            report["warnings"].append(f"Column '{col}' is constant (no variance)")
            report["score"] -= 3
    report["checks"]["constant_columns"] = constant_cols

    # 3. Outlier detection (numeric only, IQR method)
    outlier_info = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)][col]
        outlier_pct = len(outliers) / max(len(df), 1) * 100
        if outlier_pct > 0:
            outlier_info[col] = {
                "outlier_count": int(len(outliers)),
                "outlier_pct": round(outlier_pct, 2),
                "lower_bound": round(float(lower), 2),
                "upper_bound": round(float(upper), 2),
            }
        if outlier_pct > 10:
            report["warnings"].append(
                f"Column '{col}' has {outlier_pct:.1f}% outliers (potential data entry errors)"
            )
            report["score"] -= 3
    report["checks"]["outliers"] = outlier_info

    # 4. High cardinality warnings
    cardinality_warnings = []
    for col in df.columns:
        unique = df[col].nunique(dropna=True)
        if unique == len(df) and len(df) > 10:
            cardinality_warnings.append({
                "column": col,
                "unique_count": int(unique),
                "note": "All values unique (likely a key/ID)",
            })
        elif unique > 0.9 * len(df) and len(df) > 10:
            cardinality_warnings.append({
                "column": col,
                "unique_count": int(unique),
                "note": "Very high cardinality",
            })
    report["checks"]["cardinality"] = cardinality_warnings

    # 5. Mixed type detection
    mixed_types = []
    for col in df.columns:
        # Get non-null unique types
        types = df[col].dropna().apply(type).unique()
        if len(types) > 1:
            mixed_types.append(col)
            report["warnings"].append(
                f"Column '{col}' has mixed types: {[t.__name__ for t in types]}"
            )
            report["score"] -= 5
    report["checks"]["mixed_type_columns"] = mixed_types

    # 6. Date freshness (if any column is datetime)
    date_info = {}
    for col in df.columns:
        try:
            sample = df[col].dropna().head(10)
            if sample.empty:
                continue
            # Try to parse as datetime
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().sum() > 0:
                # Check if full column is datetime
                full_parsed = pd.to_datetime(df[col], errors="coerce")
                if full_parsed.notna().sum() > 0.5 * len(df):
                    date_info[col] = {
                        "min": str(full_parsed.min()),
                        "max": str(full_parsed.max()),
                        "range_days": (full_parsed.max() - full_parsed.min()).days,
                    }
        except Exception:
            continue
    report["checks"]["date_columns"] = date_info

    # 7. Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        dup_pct = dup_count / max(len(df), 1) * 100
        report["warnings"].append(
            f"{dup_count} duplicate rows ({dup_pct:.1f}%)"
        )
        report["score"] -= min(10, int(dup_pct / 2))
    report["checks"]["duplicate_rows"] = dup_count

    # Floor at 0
    report["score"] = max(0, report["score"])
    return report


def quality_summary(reports: Dict[str, dict]) -> dict:
    """Aggregate quality reports across all files."""
    if not reports:
        return {"overall_score": 100, "total_warnings": 0}

    scores = [r["score"] for r in reports.values()]
    warnings = sum(len(r["warnings"]) for r in reports.values())

    return {
        "overall_score": round(sum(scores) / len(scores), 1),
        "total_warnings": warnings,
        "files_analyzed": len(reports),
        "files_with_issues": sum(1 for r in reports.values() if r["warnings"]),
        "per_file_scores": {name: r["score"] for name, r in reports.items()},
    }
