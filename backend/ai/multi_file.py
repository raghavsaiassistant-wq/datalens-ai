"""
multi_file.py — DataLens AI Multi-File Pipeline (Phase 1: 2026-07-14)

Accepts N files, detects PKs and FKs, builds unified star schema, runs AI pipeline.

Design:
- Per-file profiling (reuse DataProfiler)
- PK detection: column uniqueness + non-null
- FK detection: name match (normalized) + value overlap (sampled)
- Build join graph, find fact table (most FKs)
- Build star schema: 1 fact + N dimensions
- Flatten to single DataFrame for AI pipeline

NOT production-grade:
- Simple FK detection (no cardinality inference beyond M:1)
- In-memory only (no persistence of multi-file state)
- Cap at 10 files, 100K total rows
- Synchronous (no streaming)
"""
from __future__ import annotations
import os
import re
import uuid
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict

import pandas as pd
import numpy as np

logger = logging.getLogger("DataLensMultiFile")

MAX_FILES = 10
MAX_TOTAL_ROWS = 100_000
VALUE_OVERLAP_SAMPLE = 500  # for FK value overlap check


# ════════════════════════════════════════════════════════════════
# Data Classes
# ════════════════════════════════════════════════════════════════

@dataclass
class ColumnProfile:
    name: str
    dtype: str
    null_pct: float
    unique_count: int
    uniqueness_ratio: float  # unique / total
    sample_values: List[Any]
    is_pk_candidate: bool = False
    is_fk_candidate: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class FileProfile:
    file_id: str
    file_name: str
    rows: int
    cols: int
    columns: List[str]
    column_profiles: Dict[str, ColumnProfile]
    pk_candidates: List[str] = field(default_factory=list)
    dtypes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        # Convert column_profiles dict-of-ColumnProfile to dict-of-dict
        d['column_profiles'] = {k: v.to_dict() for k, v in self.column_profiles.items()}
        return d


@dataclass
class Relationship:
    from_file: str
    from_column: str
    to_file: str
    to_column: str
    confidence: float
    relationship_type: str  # "one_to_many", "many_to_one", "one_to_one"
    detection_method: str   # "name_match", "value_overlap", "both"

    def to_dict(self):
        return asdict(self)


@dataclass
class UnifiedSchema:
    fact_table: Optional[str]
    dimension_tables: List[str]
    relationships: List[Relationship]
    unified_dataframe: Optional[pd.DataFrame] = None
    joined_columns: List[str] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        if self.unified_dataframe is not None:
            d['unified_dataframe_rows'] = len(self.unified_dataframe)
            d['unified_dataframe_cols'] = list(self.unified_dataframe.columns)
            del d['unified_dataframe']
        return d


# ════════════════════════════════════════════════════════════════
# File Profiler
# ════════════════════════════════════════════════════════════════

def profile_file(file_id: str, file_name: str, df: pd.DataFrame) -> FileProfile:
    """Profile a single file's schema + detect PK candidates."""
    col_profiles = {}
    pk_candidates = []
    dtypes = {}

    for col in df.columns:
        s = df[col]
        null_pct = float(s.isna().sum() / max(len(s), 1))
        unique_count = int(s.nunique(dropna=True))
        uniqueness_ratio = unique_count / max(len(s), 1)
        sample_values = s.dropna().head(5).tolist()
        # Normalize dtype
        dtype_str = str(s.dtype)
        if 'int' in dtype_str:
            dtype_str = 'int'
        elif 'float' in dtype_str:
            dtype_str = 'float'
        elif 'datetime' in dtype_str.lower():
            dtype_str = 'datetime'
        elif 'bool' in dtype_str:
            dtype_str = 'bool'
        else:
            dtype_str = 'string'
        dtypes[col] = dtype_str
        is_pk = (
            uniqueness_ratio > 0.95
            and null_pct < 0.05
            and unique_count > 1
        )
        col_profiles[col] = ColumnProfile(
            name=col,
            dtype=dtype_str,
            null_pct=round(null_pct, 3),
            unique_count=unique_count,
            uniqueness_ratio=round(uniqueness_ratio, 3),
            sample_values=[str(v) for v in sample_values],
            is_pk_candidate=is_pk,
            is_fk_candidate=(not is_pk) and dtype_str in ('int', 'string') and unique_count < len(s) * 0.8,
        )
        if is_pk:
            pk_candidates.append(col)

    return FileProfile(
        file_id=file_id,
        file_name=file_name,
        rows=len(df),
        cols=len(df.columns),
        columns=list(df.columns),
        column_profiles=col_profiles,
        pk_candidates=pk_candidates,
        dtypes=dtypes,
    )


# ════════════════════════════════════════════════════════════════
# FK Inference (Cross-File)
# ════════════════════════════════════════════════════════════════

def _normalize_col_name(name: str) -> str:
    """Normalize column name for matching: lowercase, strip _id suffix variants,
    and treat 'region' and 'region_name' as the same."""
    n = name.lower().strip()
    # Remove common suffixes
    for suf in ['_id', '_key', '_fk', '_code']:
        if n.endswith(suf):
            n = n[:-len(suf)]
            break
    # Strip common prefixes/suffixes for entity columns
    n = re.sub(r'^(dim|fact|raw|stg)_', '', n)
    n = re.sub(r'_(name|key|val|value|category|type)$', '', n)
    # Singular (very basic)
    if n.endswith('s') and len(n) > 3 and not n.endswith('ss'):
        n = n[:-1]
    return n


def _value_overlap_pct(series_a: pd.Series, series_b: pd.Series, sample: int = VALUE_OVERLAP_SAMPLE) -> float:
    """Compute fraction of A's values that exist in B."""
    a_vals = set(series_a.dropna().astype(str).sample(min(sample, len(series_a)), random_state=42))
    b_vals = set(series_b.dropna().astype(str).sample(min(sample, len(series_b)), random_state=42))
    if not a_vals:
        return 0.0
    return len(a_vals & b_vals) / len(a_vals)


def _infer_cardinality(series_a: pd.Series, series_b: pd.Series, a_is_pk: bool, b_is_pk: bool) -> str:
    """Infer cardinality from actual data, not just PK status.

    Logic:
    - 1:1 if A has no duplicates AND B has no duplicates (one-to-one mapping)
    - M:1 if A has duplicates but B has none (A is "many", B is "one")
    - M:N if both have duplicates (junction table scenario)
    - 1:M if A has none but B has duplicates (1 to many, opposite of M:1)

    Note: returns the relationship FROM A's perspective TO B's perspective.
    Caller is responsible for flipping if needed.
    """
    # Sample for speed
    a_sample = series_a.dropna().head(VALUE_OVERLAP_SAMPLE)
    b_sample = series_b.dropna().head(VALUE_OVERLAP_SAMPLE)
    if len(a_sample) == 0 or len(b_sample) == 0:
        return "many_to_one"  # default fallback

    a_unique_ratio = a_sample.nunique() / len(a_sample)
    b_unique_ratio = b_sample.nunique() / len(b_sample)

    a_has_dups = a_unique_ratio < 0.99
    b_has_dups = b_unique_ratio < 0.99

    if not a_has_dups and not b_has_dups:
        return "one_to_one"
    elif a_has_dups and not b_has_dups:
        return "many_to_one"  # A is many, B is one
    elif not a_has_dups and b_has_dups:
        return "one_to_many"  # A is one, B is many
    else:
        return "many_to_many"  # both have dups (junction table)


def detect_relationships(
    file_profiles: Dict[str, FileProfile],
    dataframes: Dict[str, pd.DataFrame],
) -> List[Relationship]:
    """Detect FK relationships across all file pairs.

    Strategy:
    1. For each pair of files (A, B), find column name matches (after normalization).
    2. For each name match, verify value overlap (if > 50%, it's a real FK).
    3. Determine cardinality: M:1 if A has duplicates of B's PK values.
    4. NEW: Composite key detection (multi-column FKs like (order_id, product_id))
    """
    file_names = list(file_profiles.keys())
    relationships = []
    seen = set()

    # Pass 1: Single-column FKs (existing logic)
    for i, name_a in enumerate(file_names):
        for j, name_b in enumerate(file_names):
            if i >= j:
                continue  # avoid duplicate pairs

            prof_a = file_profiles[name_a]
            prof_b = file_profiles[name_b]
            df_a = dataframes[name_a]
            df_b = dataframes[name_b]

            for col_a in prof_a.columns:
                norm_a = _normalize_col_name(col_a)
                prof_a_cols_norm = {c: _normalize_col_name(c) for c in prof_a.columns}

                for col_b in prof_b.columns:
                    norm_b = _normalize_col_name(col_b)

                    # Strict: same normalized name + same dtype
                    dtype_match = (
                        prof_a.column_profiles[col_a].dtype
                        == prof_b.column_profiles[col_b].dtype
                    )
                    name_match = (norm_a == norm_b) and len(norm_a) > 0

                    if not (name_match and dtype_match):
                        continue

                    # Skip self-joins (same file)
                    if name_a == name_b and col_a == col_b:
                        continue

                    # Check: at least one side has a PK candidate
                    a_is_pk = col_a in prof_a.pk_candidates
                    b_is_pk = col_b in prof_b.pk_candidates
                    if not (a_is_pk or b_is_pk):
                        continue

                    # Compute value overlap
                    overlap = _value_overlap_pct(df_a[col_a], df_b[col_b])
                    if overlap < 0.5:
                        continue

                    # Determine direction and VERIFY cardinality
                    # (M:1 vs M:N vs 1:1) based on actual data
                    cardinality = _infer_cardinality(
                        df_a[col_a], df_b[col_b], a_is_pk, b_is_pk
                    )
                    if a_is_pk and not b_is_pk:
                        from_file, from_col, to_file, to_col = name_b, col_b, name_a, col_a
                        rel_type = cardinality
                    elif b_is_pk and not a_is_pk:
                        from_file, from_col, to_file, to_col = name_a, col_a, name_b, col_b
                        rel_type = cardinality
                    else:
                        # Both PK candidates — one_to_one by default
                        from_file, from_col, to_file, to_col = name_a, col_a, name_b, col_b
                        rel_type = cardinality if cardinality != "many_to_many" else "one_to_one"

                    # Confidence = name_match (0.4) + value_overlap (0.6 * overlap)
                    confidence = 0.4 + 0.6 * overlap
                    detection = "both" if overlap > 0.7 else "name_match"

                    key = (from_file, from_col, to_file, to_col)
                    if key in seen:
                        continue
                    seen.add(key)

                    relationships.append(Relationship(
                        from_file=from_file,
                        from_column=from_col,
                        to_file=to_file,
                        to_column=to_col,
                        confidence=round(confidence, 3),
                        relationship_type=rel_type,
                        detection_method=detection,
                    ))

    # Pass 2: Composite keys (NEW in Sprint 2)
    # Heuristic: 2+ columns in A whose combined uniqueness is much higher than any single column
    # AND match columns in B (e.g., order_id+product_id in A vs same in B)
    for i, name_a in enumerate(file_names):
        for j, name_b in enumerate(file_names):
            if i >= j:
                continue
            prof_a = file_profiles[name_a]
            prof_b = file_profiles[name_b]
            df_a = dataframes[name_a]
            df_b = dataframes[name_b]

            # Find pairs of columns in A that look like composite keys
            int_cols_a = [c for c in prof_a.columns
                          if prof_a.column_profiles[c].dtype == 'int'
                          and prof_a.column_profiles[c].uniqueness_ratio < 0.5]
            for k, col_a1 in enumerate(int_cols_a):
                for col_a2 in int_cols_a[k+1:]:
                    # Check if combined uniqueness is high
                    combined = df_a[col_a1].astype(str) + "_" + df_a[col_a2].astype(str)
                    combined_uniqueness = combined.nunique() / max(len(combined), 1)
                    # If combined uniqueness > 0.95, this might be a composite key
                    if combined_uniqueness < 0.95:
                        continue
                    # Look for matching pair in B
                    for col_b1 in prof_b.columns:
                        if col_b1 not in int_cols_a and prof_b.column_profiles[col_b1].dtype != 'int':
                            continue
                        for col_b2 in prof_b.columns:
                            if col_b2 == col_b1:
                                continue
                            if prof_b.column_profiles[col_b2].dtype != 'int':
                                continue
                            # Check combined uniqueness in B
                            combined_b = df_b[col_b1].astype(str) + "_" + df_b[col_b2].astype(str)
                            if combined_b.nunique() / max(len(combined_b), 1) < 0.95:
                                continue
                            # Compute combined overlap
                            overlap = _value_overlap_pct(combined, combined_b)
                            if overlap < 0.5:
                                continue
                            key = (name_a, f"{col_a1}+{col_a2}", name_b, f"{col_b1}+{col_b2}")
                            if key in seen:
                                continue
                            seen.add(key)
                            relationships.append(Relationship(
                                from_file=name_a,
                                from_column=f"{col_a1}+{col_a2}",
                                to_file=name_b,
                                to_column=f"{col_b1}+{col_b2}",
                                confidence=round(0.3 + 0.7 * overlap, 3),
                                relationship_type="many_to_one",
                                detection_method="composite_key",
                            ))

    # Sort by confidence desc
    relationships.sort(key=lambda r: r.confidence, reverse=True)
    return relationships


# ════════════════════════════════════════════════════════════════
# Star Schema Builder
# ════════════════════════════════════════════════════════════════

def find_fact_table(
    file_profiles: Dict[str, FileProfile],
    dataframes: Dict[str, pd.DataFrame],
    relationships: List[Relationship],
) -> str:
    """Heuristic: fact table is the file with the most outgoing FKs (most references to other tables)."""
    outgoing_count: Dict[str, int] = {name: 0 for name in file_profiles}
    for rel in relationships:
        outgoing_count[rel.from_file] = outgoing_count.get(rel.from_file, 0) + 1

    # If no FKs, pick the file with the most rows
    if max(outgoing_count.values()) == 0:
        return max(file_profiles, key=lambda n: file_profiles[n].rows)

    # Else, pick file with most outgoing FKs (most normalized)
    return max(outgoing_count, key=lambda n: outgoing_count[n])


def build_star_schema(
    file_profiles: Dict[str, FileProfile],
    dataframes: Dict[str, pd.DataFrame],
    relationships: List[Relationship],
) -> UnifiedSchema:
    """Build star schema: 1 fact table + N dimension tables, joined into 1 DataFrame."""
    fact = find_fact_table(file_profiles, dataframes, relationships)
    dimensions = [n for n in file_profiles if n != fact]

    # Start with fact table
    unified = dataframes[fact].copy()
    joined_cols = list(unified.columns)
    used_rels = []

    for rel in relationships:
        if rel.from_file == fact and rel.to_file in dimensions:
            dim_df = dataframes[rel.to_file].copy()
            # Avoid column name collision by prefixing dimension columns (except the join key)
            join_key = rel.to_column
            prefixed_cols = {}
            for c in dim_df.columns:
                if c == join_key:
                    continue  # already in unified
                if c in unified.columns:
                    prefixed_cols[c] = f"{rel.to_file}_{c}"
                else:
                    prefixed_cols[c] = c
            dim_df = dim_df.rename(columns=prefixed_cols)
            try:
                unified = unified.merge(
                    dim_df,
                    left_on=rel.from_column,
                    right_on=join_key,
                    how='left',
                    suffixes=('', f'_{rel.to_file}_dup'),
                )
                used_rels.append(rel)
                joined_cols = list(unified.columns)
            except Exception as e:
                logger.warning(f"Join failed: {rel.from_file}.{rel.from_column} -> {rel.to_file}.{rel.to_column}: {e}")

    # Drop duplicate columns from joins
    dup_cols = [c for c in unified.columns if c.endswith('_dup')]
    if dup_cols:
        unified = unified.drop(columns=dup_cols)

    return UnifiedSchema(
        fact_table=fact,
        dimension_tables=dimensions,
        relationships=used_rels,
        unified_dataframe=unified,
        joined_columns=joined_cols,
    )


# ════════════════════════════════════════════════════════════════
# Main Pipeline
# ════════════════════════════════════════════════════════════════

def run_multi_file_pipeline(
    files: List[Tuple[str, str, bytes]],  # (file_id, file_name, content_bytes)
) -> Dict[str, Any]:
    """Main entry: takes N files, returns unified profile + dashboard-ready data.

    Args:
        files: list of (file_id, file_name, content_bytes) tuples

    Returns:
        dict with file_profiles, relationships, unified_schema, ai_results
    """
    if len(files) > MAX_FILES:
        return {"success": False, "error": f"Max {MAX_FILES} files allowed, got {len(files)}"}

    # Step 1: Parse all files
    dataframes: Dict[str, pd.DataFrame] = {}
    file_profiles: Dict[str, FileProfile] = {}
    total_rows = 0
    parse_errors = []

    for file_id, file_name, content in files:
        try:
            from io import BytesIO
            if file_name.lower().endswith('.csv'):
                df = pd.read_csv(BytesIO(content))
            elif file_name.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(content))
            elif file_name.lower().endswith('.json'):
                df = pd.read_json(BytesIO(content))
            else:
                parse_errors.append(f"{file_name}: unsupported format")
                continue
            dataframes[file_id] = df
            total_rows += len(df)
            if total_rows > MAX_TOTAL_ROWS:
                return {"success": False, "error": f"Total rows {total_rows} exceeds {MAX_TOTAL_ROWS}"}
        except Exception as e:
            parse_errors.append(f"{file_name}: {str(e)}")

    if not dataframes:
        return {"success": False, "error": f"No files parsed. Errors: {parse_errors}"}

    # Step 2: Profile each file
    for file_id, df in dataframes.items():
        file_profiles[file_id] = profile_file(file_id, file_id, df)

    # Step 3: Detect relationships
    relationships = detect_relationships(file_profiles, dataframes)

    # Step 4: Build star schema
    schema = build_star_schema(file_profiles, dataframes, relationships)

    # Step 5: Adapt unified data into profile-like structure for AI pipeline
    if schema.unified_dataframe is None or len(schema.unified_dataframe) == 0:
        return {
            "success": False,
            "error": "Could not build unified schema",
            "file_profiles": {k: v.to_dict() for k, v in file_profiles.items()},
            "relationships": [r.to_dict() for r in relationships],
        }

    # Compute basic stats on unified data
    unified_df = schema.unified_dataframe
    numeric_cols = unified_df.select_dtypes(include=[np.number]).columns.tolist()
    kpis = {}
    for col in numeric_cols[:5]:  # top 5 numeric as KPIs
        kpis[col] = {
            "sum": float(unified_df[col].sum()),
            "mean": float(unified_df[col].mean()),
            "min": float(unified_df[col].min()),
            "max": float(unified_df[col].max()),
        }

    # Identify categorical columns
    categorical_cols = [
        c for c in unified_df.columns
        if unified_df[c].dtype == 'object' and unified_df[c].nunique() < 50
    ]

    # Sprint 7: Data quality checks per file
    from ai.data_quality import check_data_quality, quality_summary
    quality_reports = {}
    for name, df in dataframes.items():
        try:
            quality_reports[name] = check_data_quality(name, df)
        except Exception as e:
            quality_reports[name] = {"error": str(e), "score": 0}
    quality_agg = quality_summary(quality_reports)

    # Sprint 8: Build column-level lineage
    from ai.lineage import build_lineage, lineage_summary
    file_columns_map = {name: list(df.columns) for name, df in dataframes.items()}
    lineage_dict = build_lineage(
        list(dataframes.keys()),
        file_columns_map,
        [r.to_dict() for r in relationships],
        schema.fact_table,
        schema.dimension_tables,
    )
    lineage_agg = lineage_summary(
        lineage_dict, [r.to_dict() for r in relationships]
    )

    # Build the response
    return {
        "success": True,
        "mode": "multi_file",
        "file_count": len(dataframes),
        "total_rows": total_rows,
        "parse_errors": parse_errors,
        "file_profiles": {k: v.to_dict() for k, v in file_profiles.items()},
        "relationships": [r.to_dict() for r in relationships],
        "unified_schema": schema.to_dict(),
        "unified_data": {
            "rows": len(unified_df),
            "cols": list(unified_df.columns),
            "kpis": kpis,
            "categorical_cols": categorical_cols,
            "numeric_cols": numeric_cols,
            "sample_records": unified_df.head(10).fillna('').astype(str).to_dict(orient='records'),
        },
        "data_quality": {
            "per_file": quality_reports,
            "summary": quality_agg,
        },
        "lineage": {
            "columns": lineage_dict,
            "summary": lineage_agg,
        },
    }


def get_unified_dataframe_from_result(result: Dict[str, Any], files: List[Tuple[str, str, bytes]]) -> Optional[pd.DataFrame]:
    """Reconstruct unified DataFrame from pipeline result (for AI pipeline consumption)."""
    from io import BytesIO
    dataframes = {}
    for file_id, file_name, content in files:
        try:
            if file_name.lower().endswith('.csv'):
                dataframes[file_id] = pd.read_csv(BytesIO(content))
            elif file_name.lower().endswith(('.xlsx', '.xls')):
                dataframes[file_id] = pd.read_excel(BytesIO(content))
        except:
            pass

    if not dataframes:
        return None

    file_profiles = {fid: profile_file(fid, fid, df) for fid, df in dataframes.items()}
    relationships = detect_relationships(file_profiles, dataframes)
    schema = build_star_schema(file_profiles, dataframes, relationships)
    return schema.unified_dataframe
