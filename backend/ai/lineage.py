"""
lineage.py — Track column-level lineage (Sprint 8)

For each output column in the unified dataset, track which source file
and source column it came from. Enables:
- "Where did this column come from?" questions
- "What happens if I change source X?" impact analysis
- Trust/explainability for AI insights
"""
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class ColumnLineage:
    """Lineage for a single output column."""
    output_column: str
    source_file: str
    source_column: str
    transformation: str  # "passthrough", "prefix_added", "join_key", "derived"
    join_chain: List[str] = None  # Files in the join chain (for joined cols)


def build_lineage(
    file_names: List[str],
    file_columns: Dict[str, List[str]],
    relationships: List[dict],
    fact_table: str,
    dimensions: List[str],
) -> Dict[str, List[ColumnLineage]]:
    """Build column-level lineage map for the unified dataset.

    Returns: {output_column: lineage} for each output column.
    """
    lineages = {}

    # 1. Each source column from each file -> prefix with file name
    for file in file_names:
        cols = file_columns.get(file, [])
        for col in cols:
            # Skip if this column will collide with another file's
            # (we use prefix strategy in JOIN)
            output_name = f"{file}_{col}" if _needs_prefix(col, file_names, file_columns) else col
            lineages[output_name] = ColumnLineage(
                output_column=output_name,
                source_file=file,
                source_column=col,
                transformation="passthrough",
                join_chain=[file],
            )

    # 2. Join keys (from relationships) get "join_key" transformation
    for rel in relationships:
        from_f = rel["from_file"]
        to_f = rel["to_file"]
        from_c = rel["from_column"]
        # (to_c dropped — unused after the dict-only refactor)
        # The FK side gets "join_key" tag
        if from_c in file_columns.get(from_f, []):
            lineages[f"{from_f}_{from_c}" if _needs_prefix(from_c, file_names, file_columns) else from_c] = ColumnLineage(
                output_column=lineages.get(f"{from_f}_{from_c}", None).output_column if f"{from_f}_{from_c}" in lineages else from_c,
                source_file=from_f,
                source_column=from_c,
                transformation="join_key",
                join_chain=[from_f, to_f],
            )

    return {k: asdict(v) for k, v in lineages.items()}


def _needs_prefix(col_name: str, file_names: List[str], file_columns: Dict[str, List[str]]) -> bool:
    """Check if a column name appears in multiple files (collision risk)."""
    count = 0
    for f, cols in file_columns.items():
        if col_name in cols:
            count += 1
    return count > 1


def lineage_summary(lineages: Dict[str, dict], relationships: List[dict]) -> dict:
    """High-level summary of lineage for display."""
    passthrough = sum(1 for lin in lineages.values() if lin["transformation"] == "passthrough")
    join_keys = sum(1 for lin in lineages.values() if lin["transformation"] == "join_key")

    # Count source files
    source_files = set(lin["source_file"] for lin in lineages.values())

    return {
        "total_columns": len(lineages),
        "passthrough_columns": passthrough,
        "join_key_columns": join_keys,
        "source_files": list(source_files),
        "join_paths": [
            f"{r['from_file']}.{r['from_column']} -> {r['to_file']}.{r['to_column']}"
            for r in relationships
        ],
    }


def trace_to_source(lineages: Dict[str, dict], output_column: str) -> List[dict]:
    """Trace a single output column back to its source(s)."""
    if output_column not in lineages:
        return []
    lineage = lineages[output_column]
    return [{
        "output": output_column,
        "source_file": lineage["source_file"],
        "source_column": lineage["source_column"],
        "transformation": lineage["transformation"],
        "join_chain": lineage.get("join_chain", []),
    }]
