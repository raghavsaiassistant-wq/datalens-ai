"""
dataset_classifier.py

Understands WHAT a dataset is before any analysis runs.
Assigns roles to every column and detects the dataset type.
Pure Python + pandas — no NIM calls, max 1 second.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("DatasetClassifier")

# ─── Keyword Banks ────────────────────────────────────────────────────────── #

IDENTIFIER_NAMES = {
    "locationid", "marketid", "storeid", "customerid", "orderid",
    "userid", "transactionid", "invoiceid", "productid", "employeeid",
    "accountid", "clientid", "vendorid", "supplieid", "rowid", "id"
}

EXPERIMENT_KEYWORDS   = {"promotion", "variant", "treatment", "group", "test", "campaign", "condition", "experiment"}
TIMESERIES_KEYWORDS   = {"week", "month", "quarter", "year", "day", "date", "period", "time", "timestamp"}
TRANSACTIONAL_KEYWORDS = {"order_id", "transaction_id", "invoice", "receipt", "purchase"}
CUSTOMER_KEYWORDS     = {"customer_id", "user_id", "age", "segment", "churn", "ltv", "gender", "region", "tier"}
FINANCIAL_KEYWORDS    = {"revenue", "cost", "profit", "margin", "budget", "expense", "sales", "income", "ebitda"}
SEGMENT_KEYWORDS      = {"age", "group", "tier", "level", "rank", "score", "grade", "class", "type", "category", "store"}

BUSINESS_QUESTIONS = {
    "experiment":    "Which variant/promotion wins overall, and does the answer differ by segment?",
    "timeseries":    "What are the trends, seasonal patterns, and anomalies over time?",
    "transactional": "Who are the top performers and what drives transaction value?",
    "customer":      "How do customer segments differ, and what predicts behavior?",
    "financial":     "What is financial performance and what drives cost/revenue variance?",
    "general":       "What patterns exist in this data and which factors matter most?",
}


@dataclass
class DatasetMeta:
    dataset_type: str
    confidence: float
    business_question: str
    column_roles: dict
    dimensions: list
    measures: list
    time_cols: list
    identifiers: list
    segments: list
    primary_measure: str
    primary_dimension: str
    primary_time: Optional[str]
    dataset_description: str


class DatasetClassifier:
    """Classify a dataset into one of 6 business types and assign column roles."""

    def classify(self, df: pd.DataFrame, profile) -> DatasetMeta:
        cols_lower = {c: c.lower().replace(" ", "_") for c in df.columns}

        # ── Step 1: Assign column roles ─────────────────────────────────────
        roles = self._assign_roles(df, cols_lower)

        # ── Step 2: Score dataset types ──────────────────────────────────────
        dataset_type, confidence = self._score_type(df, cols_lower, roles)

        # ── Step 3: Primary column selection ────────────────────────────────
        primary_measure   = self._pick_primary_measure(df, roles["measure"])
        primary_dimension = self._pick_primary_dimension(df, roles, cols_lower, dataset_type, primary_measure)
        primary_time      = roles["time"][0] if roles["time"] else None

        # ── Step 4: Build description ────────────────────────────────────────
        n_locations = len(df[roles["identifiers"][0]].unique()) if roles["identifiers"] else None
        n_variants  = len(df[primary_dimension].unique()) if primary_dimension and primary_dimension in df else None
        n_periods   = len(df[primary_time].unique()) if primary_time and primary_time in df else None

        desc = self._build_description(
            df, dataset_type, profile, primary_dimension, primary_measure,
            n_locations, n_variants, n_periods, roles
        )

        return DatasetMeta(
            dataset_type=dataset_type,
            confidence=round(confidence, 3),
            business_question=BUSINESS_QUESTIONS[dataset_type],
            column_roles={
                "identifier": roles["identifiers"],
                "dimension":  roles["dimension"],
                "measure":    roles["measure"],
                "time":       roles["time"],
                "segment":    roles["segment"],
            },
            dimensions=roles["dimension"],
            measures=roles["measure"],
            time_cols=roles["time"],
            identifiers=roles["identifiers"],
            segments=roles["segment"],
            primary_measure=primary_measure or "",
            primary_dimension=primary_dimension or "",
            primary_time=primary_time,
            dataset_description=desc,
        )

    # ────────────────────────────────────────────────────────────────────────
    # Column Role Assignment
    # ────────────────────────────────────────────────────────────────────────

    def _assign_roles(self, df: pd.DataFrame, cols_lower: dict) -> dict:
        roles = {"identifiers": [], "time": [], "segment": [], "dimension": [], "measure": []}
        n = len(df)

        for col, clow in cols_lower.items():
            dtype = df[col].dtype

            # ── Identifier ──────────────────────────────────────────────────
            if self._is_identifier(col, clow, df[col], n):
                roles["identifiers"].append(col)
                continue

            # ── Time ────────────────────────────────────────────────────────
            if self._is_time(col, clow, dtype):
                roles["time"].append(col)
                continue

            # ── Segment (numeric category) ──────────────────────────────────
            if self._is_segment(col, clow, dtype, df[col], n):
                roles["segment"].append(col)
                continue

            # ── Dimension (categorical grouping) ────────────────────────────
            if self._is_dimension(dtype, df[col]):
                roles["dimension"].append(col)
                continue

            # ── Measure (numeric outcome) ────────────────────────────────────
            if pd.api.types.is_numeric_dtype(dtype):
                roles["measure"].append(col)

        return roles

    def _is_identifier(self, col: str, clow: str, series: pd.Series, n: int) -> bool:
        # Name-based (highest confidence — always trust)
        if clow in IDENTIFIER_NAMES:
            return True
        if clow.endswith("_id") or (clow.endswith("id") and len(clow) > 2):
            return True
        # Integer with high cardinality — but skip when the name looks like
        # an attribute/segment (age, score, grade, store, etc.) rather than an ID
        if pd.api.types.is_integer_dtype(series.dtype):
            # Reject cardinality-based detection for obvious measurement columns
            for seg_kw in SEGMENT_KEYWORDS:
                if seg_kw in clow:
                    return False
            nu = series.nunique()
            if nu > 0.5 * n:
                return True
            # Sequential check: max == nunique (1-N pattern)
            try:
                mx = int(series.max())
                if mx == nu and nu > 10:
                    return True
            except Exception:
                pass
        return False

    def _is_time(self, col: str, clow: str, dtype) -> bool:
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return True
        for kw in TIMESERIES_KEYWORDS:
            if kw in clow:
                return True
        return False

    def _is_segment(self, col: str, clow: str, dtype, series: pd.Series, n: int) -> bool:
        if not pd.api.types.is_integer_dtype(dtype):
            return False
        nu = series.nunique()
        if nu > 30:
            return False
        for kw in SEGMENT_KEYWORDS:
            if kw in clow:
                return True
        return False

    def _is_dimension(self, dtype, series: pd.Series) -> bool:
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
            return True
        if pd.api.types.is_bool_dtype(dtype):
            return True
        if pd.api.types.is_integer_dtype(dtype):
            nu = series.nunique()
            if nu <= 15:
                return True
        return False

    # ────────────────────────────────────────────────────────────────────────
    # Dataset Type Scoring
    # ────────────────────────────────────────────────────────────────────────

    def _score_type(self, df: pd.DataFrame, cols_lower: dict, roles: dict):
        scores = {
            "experiment": 0, "timeseries": 0, "transactional": 0,
            "customer": 0, "financial": 0,
        }
        clow_set = set(cols_lower.values())
        has_identifier = len(roles["identifiers"]) > 0
        has_measure    = len(roles["measure"]) > 0
        has_time       = len(roles["time"]) > 0

        # experiment
        for clow in clow_set:
            for kw in EXPERIMENT_KEYWORDS:
                if kw in clow:
                    scores["experiment"] += 3
                    break
        if has_identifier and has_measure:
            scores["experiment"] += 1

        # timeseries
        if has_time:
            # Real datetime columns count more than integer-named period columns
            real_dt_cols = [c for c in df.columns
                            if pd.api.types.is_datetime64_any_dtype(df[c].dtype)]
            scores["timeseries"] += 2 if real_dt_cols else 1
        for clow in clow_set:
            for kw in TIMESERIES_KEYWORDS:
                if kw == clow:  # exact match
                    # Integer period columns (week=1,2,3; month=1-12) count less than
                    # true datetime columns — they may just be experiment periods
                    orig_cols = [c for c, cl in cols_lower.items() if cl == clow]
                    if orig_cols and pd.api.types.is_integer_dtype(df[orig_cols[0]].dtype):
                        scores["timeseries"] += 1
                    else:
                        scores["timeseries"] += 2
                    break

        # transactional
        for clow in clow_set:
            for kw in TRANSACTIONAL_KEYWORDS:
                if kw in clow:
                    scores["transactional"] += 3
                    break
        if has_time and has_measure:
            # Check if there's a customer-like col
            for clow in clow_set:
                if "customer" in clow or "client" in clow or "user" in clow:
                    scores["transactional"] += 1

        # customer
        for clow in clow_set:
            for kw in CUSTOMER_KEYWORDS:
                if kw in clow:
                    scores["customer"] += 2
                    break

        # financial
        for clow in clow_set:
            for kw in FINANCIAL_KEYWORDS:
                if kw in clow:
                    scores["financial"] += 2
                    break

        total = sum(scores.values())
        if total == 0:
            return "general", 0.0

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        confidence = best_score / total

        # ── Experiment special rule ──────────────────────────────────────────
        # When an explicit experiment keyword column is found (score >= 3)
        # and experiment has the highest score, trust it even at lower confidence.
        # Integer "week"/"month" cols in such datasets are experiment periods, not
        # true timeseries — confidence threshold is deliberately relaxed.
        exp_score = scores.get("experiment", 0)
        if exp_score >= 3 and exp_score == best_score:
            return "experiment", confidence

        if confidence < 0.5:
            return "general", confidence

        # Break ties: prefer experiment over timeseries when both are equal
        second_score = sorted(scores.values(), reverse=True)[1]
        if best_score == second_score:
            if scores.get("experiment", 0) == best_score:
                return "experiment", confidence

        return best_type, confidence

    # ────────────────────────────────────────────────────────────────────────
    # Primary Column Selection
    # ────────────────────────────────────────────────────────────────────────

    def _pick_primary_measure(self, df: pd.DataFrame, measures: list) -> Optional[str]:
        if not measures:
            return None
        # Highest variance
        variances = {}
        for col in measures:
            try:
                variances[col] = float(df[col].var())
            except Exception:
                variances[col] = 0.0
        return max(variances, key=variances.get)

    def _pick_primary_dimension(self, df, roles, cols_lower, dataset_type, primary_measure) -> Optional[str]:
        dims = roles["dimension"]
        if not dims:
            return None

        # For experiment: prefer col whose name most closely matches experiment keywords
        if dataset_type == "experiment":
            for col in dims:
                clow = cols_lower[col]
                for kw in EXPERIMENT_KEYWORDS:
                    if kw in clow:
                        return col

        # Otherwise: dimension with highest numeric correlation to primary_measure
        if primary_measure and primary_measure in df.columns:
            best_corr = -1.0
            best_dim = dims[0]
            for col in dims:
                try:
                    # Convert to numeric codes for correlation
                    codes = df[col].astype("category").cat.codes.astype(float)
                    corr = abs(float(codes.corr(df[primary_measure].astype(float))))
                    if corr > best_corr:
                        best_corr = corr
                        best_dim = col
                except Exception:
                    pass
            return best_dim

        # Fallback: most categories
        return max(dims, key=lambda c: df[c].nunique())

    # ────────────────────────────────────────────────────────────────────────
    # Description
    # ────────────────────────────────────────────────────────────────────────

    def _build_description(self, df, dataset_type, profile, primary_dim,
                           primary_measure, n_locations, n_variants, n_periods, roles) -> str:
        rows = len(df)
        file = getattr(profile, "file_name", "dataset")

        if dataset_type == "experiment":
            dim_label = primary_dim or "variants"
            measure_label = primary_measure or "outcome"
            loc_part = f" across {n_locations} locations" if n_locations else ""
            var_part = f" testing {n_variants} {dim_label} strategies" if n_variants else ""
            period_part = f" over {n_periods} time periods" if n_periods else ""
            return (
                f"A marketing {dataset_type} dataset ({rows:,} records){loc_part}"
                f"{var_part}{period_part}, measuring {measure_label}."
            )

        if dataset_type == "timeseries":
            measure_label = primary_measure or "metrics"
            period_label = roles["time"][0] if roles["time"] else "time"
            return (
                f"A time-series dataset ({rows:,} records) tracking {measure_label} "
                f"over {period_label} periods."
            )

        return (
            f"A {dataset_type} dataset ({rows:,} records) with "
            f"{len(roles['dimension'])} dimensions and {len(roles['measure'])} measures."
        )
