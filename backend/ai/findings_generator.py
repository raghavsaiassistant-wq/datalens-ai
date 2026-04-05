"""
findings_generator.py

Orchestrates the full AI Intelligence pipeline:
  1. DatasetClassifier  – understand the data
  2. AnalyticalEngine   – compute answers
  3. SmartVizSelector   – choose charts
  4. AnomalyDetector    – flag anomalies
  5. GroundedInsightGenerator – synthesise board-level insights

Zero regression: all existing response keys are preserved.
New additive keys: dataset_meta, analytical_findings, insights.
"""
import time
import logging
import math
from dataclasses import asdict
from typing import Any, Dict, List

from parsers.base_parser import DataProfile
from ai.nim_client import NIMClient
from ai.anomaly_detector import AnomalyDetector, AnomalyFlag
from ai.dataset_classifier import DatasetClassifier
from ai.analytical_engine import AnalyticalEngine
from ai.smart_viz_selector import SmartVizSelector
from ai.grounded_insight_generator import GroundedInsightGenerator

logger = logging.getLogger("FindingsGenerator")


# ─────────────────────────────────────────────────────────────────────────────
# FindingsGenerator
# ─────────────────────────────────────────────────────────────────────────────

class FindingsGenerator:
    """Runs the upgraded Analyst-Brain AI pipeline."""

    def generate(
        self,
        profile: DataProfile,
        nim_client: NIMClient,
        progress_callback: Any = None,
    ) -> Dict[str, Any]:
        start_time = time.time()

        # ── 0. Sampling for performance ──────────────────────────────────────
        original_rows = profile.rows
        if original_rows > 500:
            logger.info(f"Sampling dataset from {original_rows} to 500 rows for AI efficiency.")
            profile.df = profile.df.sample(500, random_state=42)
            profile.rows = 500
            profile.warnings.append(
                f"AI insights generated from a sample of 500 rows (Total: {original_rows})."
            )

        def update_progress(step: int, message: str):
            if progress_callback:
                progress_callback(step, message)

        df = profile.df

        # ── 1. Classify dataset ───────────────────────────────────────────────
        update_progress(1, "📂 Classifying dataset...")
        classifier = DatasetClassifier()
        meta = classifier.classify(df, profile)
        logger.info(f"Dataset classified as '{meta.dataset_type}' (confidence={meta.confidence:.2f})")

        # ── 2. Compute analytical findings ───────────────────────────────────
        update_progress(2, "🔍 Computing analytical findings...")
        engine = AnalyticalEngine()
        findings = engine.analyze(df, meta, profile)
        logger.info(f"AnalyticalEngine produced {len(findings)} findings")

        # ── 3. Select smart visualisations ───────────────────────────────────
        update_progress(3, "🧠 Selecting smart visualizations...")
        viz_selector = SmartVizSelector()
        charts = viz_selector.select_charts(df, meta, findings)
        logger.info(f"SmartVizSelector produced {len(charts)} charts")

        # ── 4. Detect anomalies ───────────────────────────────────────────────
        update_progress(4, "🔍 Detecting anomalies...")
        detector = AnomalyDetector()
        anomalies = detector.detect(profile, nim_client)

        # ── 5. Generate grounded insights ─────────────────────────────────────
        update_progress(5, "✨ Generating grounded insights...")
        insight_gen = GroundedInsightGenerator()
        insights_result = insight_gen.generate(meta, findings, nim_client)

        update_progress(6, "🎉 Analysis complete! Finalizing dashboard...")

        total_time = round(time.time() - start_time, 2)
        logger.info(f"AI Pipeline completed in {total_time}s")

        # ── 6. Build result ───────────────────────────────────────────────────
        executive_summary = _build_summary_from_insights(insights_result, meta)
        key_findings      = _build_key_findings(findings[:3])
        next_steps        = _build_next_steps(insights_result)
        data_health_score = _compute_health_score(profile, anomalies)

        return {
            # ── Existing keys (preserved) ─────────────────────────────────
            "profile": {
                "file_name":    profile.file_name,
                "source_type":  profile.source_type,
                "rows":         profile.rows,
                "cols":         profile.cols,
                "columns":      profile.columns,
                "column_types": profile.column_types,
                "kpi_columns":  profile.kpi_columns,
                "has_datetime": profile.has_datetime,
                "has_numeric":  profile.has_numeric,
                "null_pct":     profile.null_pct,
                "duplicates":   profile.duplicates,
                "warnings":     profile.warnings,
            },
            "charts":            [_dataclass_to_dict(c) for c in charts],
            "anomalies":         [_dataclass_to_dict(a) for a in anomalies],
            "executive_summary": executive_summary,
            "key_findings":      key_findings,
            "next_steps":        next_steps,
            "data_health_score": data_health_score,
            "processing_time":   total_time,
            # ── New additive keys ─────────────────────────────────────────
            "dataset_meta":         _dataclass_to_dict(meta),
            "analytical_findings":  [_dataclass_to_dict(f) for f in findings],
            "insights":             insights_result.get("insights", []),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────

def _build_summary_from_insights(insights_result: dict, meta) -> str:
    """Build a 3-4 sentence executive paragraph from grounded insights."""
    insights = insights_result.get("insights", [])
    dataset_desc = meta.dataset_description or "This dataset"

    if not insights:
        return (
            f"{dataset_desc}. "
            "No significant patterns were detected with the current data. "
            "Consider uploading a larger or more complete dataset for richer analysis."
        )

    # Open with dataset description
    lines = [dataset_desc + "."]

    # One sentence per insight headline (up to 3)
    for ins in insights[:3]:
        headline = ins.get("headline", "")
        context  = ins.get("context", "")
        if headline:
            # Take first sentence of context if available
            ctx_first = context.split(".")[0].strip() if context else ""
            if ctx_first:
                lines.append(f"{headline}. {ctx_first}.")
            else:
                lines.append(f"{headline}.")

    return " ".join(lines)


def _build_key_findings(findings: list) -> List[dict]:
    """Convert top 3 analytical findings into headline/detail/impact dicts."""
    result = []
    for f in findings[:3]:
        result.append({
            "headline": f.answer[:120] if f.answer else f.question[:80],
            "detail":   f.question,
            "impact":   f.significance,
        })
    return result


def _build_next_steps(insights_result: dict) -> List[dict]:
    """Extract recommended actions from insights as next-step dicts."""
    insights = insights_result.get("insights", [])
    steps = []
    for ins in insights[:3]:
        action    = ins.get("recommended_action", "")
        impact    = ins.get("impact_area", "growth")
        magnitude = ins.get("magnitude", "medium")
        headline  = ins.get("headline", "")
        if action:
            steps.append({
                "action":   action,
                "reason":   headline,
                "priority": magnitude,
            })
    return steps


def _compute_health_score(profile, anomalies: list) -> int:
    """
    Score 0-100 based on data quality signals.

    Deductions:
      - 10 per column with > 30% nulls
      - 5 per 100 duplicate rows
      - 10 per high-severity anomaly
      - 5 per medium-severity anomaly
    """
    score = 100

    # Null deduction
    null_pct_map = profile.null_pct or {}
    for col, pct in null_pct_map.items():
        if isinstance(pct, (int, float)) and pct > 30:
            score -= 10

    # Duplicate deduction
    dup_count = profile.duplicates or 0
    score -= int(dup_count / 100) * 5

    # Anomaly deduction
    for anomaly in anomalies:
        sev = getattr(anomaly, "severity", None)
        if sev == "high":
            score -= 10
        elif sev == "medium":
            score -= 5

    return max(0, score)


# ─────────────────────────────────────────────────────────────────────────────
# Serialisation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    try:
        d = asdict(obj)
    except Exception:
        # Fallback: use __dict__ for non-dataclass objects
        d = obj.__dict__ if hasattr(obj, "__dict__") else {"value": str(obj)}
    return _sanitize(d)


def _sanitize(obj: Any) -> Any:
    """Recursively replace float inf/nan with None for safe JSON serialisation."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj
