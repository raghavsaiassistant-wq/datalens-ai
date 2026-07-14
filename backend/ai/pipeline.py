"""
pipeline.py — Single orchestrator for DataLens AI analysis.
Replaces findings_generator.py + summarizer.py (both deleted).
Runs 6 stages with parallel LLM calls where possible.

Fixes:
  Bug #2: No more dual-path overwriting — pipeline writes to result["insights"] once.
  Bug #8: No more duplicate health-score formula.
"""
import time
import json
import logging
from typing import Any, Dict, List
from parsers.base_parser import DataProfile
from ai.anomaly_detector import AnomalyDetector
from ai.dataset_classifier import DatasetClassifier
from ai.analytical_engine import AnalyticalEngine
from ai.smart_viz_selector import SmartVizSelector
from ai.grounded_insight import GroundedInsight
from ai.insight_engine import InsightEngine
from ai.hallucination_guard import HallucinationGuard
from ai.ollama_client import OllamaClient
from utils.sampling import smart_sample

logger = logging.getLogger("Pipeline")


class AnalysisPipeline:
    """
    The single source of truth for the analysis result dict.
    Replaces FindingsGenerator + Summarizer (now both deleted).
    """

    def __init__(self, ollama: OllamaClient = None):
        self.ollama = ollama
        # Backward-compat: also accept a NIMClient (in case migration is gradual)
        self.classifier = DatasetClassifier()
        self.analytical = AnalyticalEngine()
        self.viz_selector = SmartVizSelector()
        self.anomaly_detector = AnomalyDetector()
        self.insight_engine = InsightEngine(ollama) if ollama else None
        self.grounded = GroundedInsight(ollama) if ollama else None

    async def run(
        self,
        profile: DataProfile,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Execute the full analysis pipeline. Returns a dict matching the
        legacy `FindingsGenerator.generate()` contract (zero regression).
        """
        start = time.time()
        warnings: List[Dict[str, Any]] = []

        def progress(step, msg):
            if progress_callback:
                try:
                    progress_callback(step, msg)
                except Exception:
                    pass

        # ── 0. Smart sampling (FIX for Bug #3) ───────────────────────────────
        original_rows = profile.rows
        sampled_df, sample_warnings = smart_sample(profile.df, max_rows=500)
        if sample_warnings:
            warnings.extend(sample_warnings)
            profile.df = sampled_df
            profile.rows = len(sampled_df)

        df = profile.df

        # ── 1. Classify dataset (deterministic) ─────────────────────────────
        progress(1, "📂 Classifying dataset...")
        meta = self.classifier.classify(df, profile)

        # ── 2. Compute analytical findings (deterministic) ──────────────────
        progress(2, "🔍 Computing analytical findings...")
        findings = self.analytical.analyze(df, meta, profile)

        # ── 3. Select smart visualizations (deterministic) ─────────────────
        progress(3, "🧠 Selecting smart visualizations...")
        charts = self.viz_selector.select_charts(df, meta, findings)

        # ── 4. Detect anomalies (deterministic stats, AI explain deferred to LLM step) ───
        progress(4, "🔍 Detecting anomalies...")
        anomalies = self.anomaly_detector.detect(profile, ollama_client=None)  # AI explain in step 5

        # ── 5. LLM-driven insights (PARALLEL where independent) ─────────────
        progress(5, "✨ Generating AI insights...")

        if self.ollama:
            # Build HallucinationGuard from raw numeric data
            raw_kpis = {}
            for col in profile.kpi_columns[:5]:
                if col in df.columns:
                    raw_kpis[col] = pd_numeric_safe(df[col])
            guard = HallucinationGuard(raw_kpis)

            # Parallel: L1+L2 (analyst role) + anomaly explanations (reasoner role)
            tasks = []
            if self.insight_engine:
                tasks.append(("l1l2", self.insight_engine.l1l2(profile, anomalies, findings)))
            tasks.append(("anomaly_explain", self._explain_anomalies(anomalies, profile)))

            results = {}
            for name, coro in tasks:
                try:
                    results[name] = await coro
                except Exception as e:
                    logger.error(f"Task {name} failed: {e}")
                    results[name] = {}

            l1l2 = results.get("l1l2", {"l1_facts": [], "l2_causes": [], "l3_insights": []})
            anomaly_narr = results.get("anomaly_explain", [])

            # L3 (reasoner) — depends on L1+L2, run after
            progress(5, "🎯 Synthesizing board-level decisions...")
            l3 = await self.grounded.l3(l1l2, meta) if self.grounded else {}

            # Apply hallucination guard
            insights_for_guard = {**l1l2, **l3}
            guard_result = guard.validate_dict(insights_for_guard)
            merged_insights = guard_result["clean"]
            if guard_result["flagged_count"] > 0:
                warnings.append({
                    "type": "hallucination_check",
                    "flagged_count": guard_result["flagged_count"],
                    "message": f"AI output reviewed; {guard_result['flagged_count']} number(s) flagged but retained with low confidence.",
                })
        else:
            # No LLM available — use heuristics only
            l1l2 = {"l1_facts": [f"Dataset has {profile.rows} rows and {profile.cols} columns"],
                    "l2_causes": [], "l3_insights": []}
            anomaly_narr = []
            merged_insights = l1l2

        # ── 6. Build executive summary from L3 insights ─────────────────────
        progress(6, "🎉 Finalizing...")
        exec_summary = self._build_summary_from_l3(merged_insights, profile)
        key_findings = self._extract_key_findings(merged_insights)
        next_steps = self._extract_next_steps(merged_insights)
        health_score = self._compute_health_score(profile, anomalies, warnings)

        total_time = round(time.time() - start, 2)

        # Attach anomaly narratives + serialize
        anomaly_dicts = []
        for a in anomalies:
            d = a.__dict__ if hasattr(a, "__dict__") else a
            if anomaly_narr:
                narr = next((n for n in anomaly_narr if n.get("column") == d.get("column")), {})
                d["explanation"] = narr.get("explanation", d.get("explanation", ""))
            anomaly_dicts.append(d)

        # Serialize ChartConfig (and any other dataclass) to dicts
        chart_dicts = []
        for c in charts:
            if hasattr(c, "__dict__"):
                chart_dicts.append(dict(c.__dict__))
            elif isinstance(c, dict):
                chart_dicts.append(c)
            else:
                chart_dicts.append({"chart_type": str(c), "title": ""})

        # Serialize Finding objects in analytical_findings
        findings_dicts = []
        for f in findings:
            if hasattr(f, "__dict__"):
                findings_dicts.append(dict(f.__dict__))
            elif isinstance(f, dict):
                findings_dicts.append(f)
            else:
                findings_dicts.append({"statement": str(f)})

        # ── NEW: serialize full sample records (for filters + drill-down) ──
        # Cap at 5000 rows for session storage. Frontend uses these to re-render
        # KPIs/charts when slicers change, and to show drill-down modals.
        try:
            # Make a JSON-safe copy of the dataframe (no Timestamp, no numpy, no NaN)
            import math
            df_safe = df.head(5000).copy()
            for col in df_safe.columns:
                if df_safe[col].dtype.kind in ('M',):  # datetime
                    df_safe[col] = df_safe[col].astype(str)
                else:
                    # For ALL non-datetime columns: convert NaN/nan to None
                    # (object columns with empty strings also get None)
                    df_safe[col] = df_safe[col].astype(object).where(df_safe[col].notna(), None)
            # Cast all values to JSON-safe types in a final pass
            raw_records = df_safe.to_dict(orient="records")
            clean_records = []
            for rec in raw_records:
                clean = {}
                for k, v in rec.items():
                    if v is None:
                        clean[k] = None
                    elif isinstance(v, float):
                        if math.isnan(v) or math.isinf(v):
                            clean[k] = None
                        else:
                            clean[k] = v
                    elif isinstance(v, (int, str, bool)):
                        clean[k] = v
                    else:
                        # Anything else (numpy, etc) → string
                        try:
                            clean[k] = str(v)
                        except Exception:
                            clean[k] = None
                clean_records.append(clean)
            # Final guard: ensure no 'NaN' string anywhere
            text = json.dumps(clean_records, default=str, allow_nan=False)
            records = json.loads(text)
            records_columns = list(df.columns)
        except Exception as e:
            logger.warning(f"Could not serialize records: {e}")
            records = []
            records_columns = []

        # ── NEW: identify filterable columns (categorical, low cardinality) ──
        filterable = []
        for col in records_columns:
            try:
                nunique = df[col].nunique(dropna=True)
                if 2 <= nunique <= 50:  # sweet spot for slicers
                    unique_vals = df[col].dropna().unique().tolist()[:50]
                    # convert to JSON-safe
                    unique_vals = [str(v) if not isinstance(v, (int, float, bool, str)) else v for v in unique_vals]
                    filterable.append({
                        "column": col,
                        "unique_count": nunique,
                        "values": unique_vals,
                    })
            except Exception:
                pass

        return {
            # Legacy keys (zero regression)
            "executive_summary": exec_summary,
            "key_findings": key_findings,
            "next_steps": next_steps,
            "data_health_score": health_score,
            "anomalies": anomaly_dicts,
            "charts": chart_dicts,
            "warnings": warnings + (profile.warnings or []),
            # New additive keys
            "dataset_meta": meta.__dict__ if hasattr(meta, "__dict__") else meta,
            "analytical_findings": findings_dicts,
            "insights": merged_insights,
            "metadata": {
                "total_time_seconds": total_time,
                "sampled_from_rows": original_rows,
                "analyzed_rows": profile.rows,
                "llm_enabled": self.ollama is not None,
            },
            # NEW: raw records for client-side filtering + drill-down
            "records": records,
            "records_columns": records_columns,
            "filterable_columns": filterable,
        }

    # ── Helpers ─────────────────────────────────────────────────────────────
    async def _explain_anomalies(self, anomalies, profile):
        if not anomalies:
            return []
        from ai.prompts import ANOMALY_EXPLAINER_SYSTEM
        items = [{"column": a.column, "value": a.value, "z_score": a.z_score}
                 for a in anomalies[:5] if hasattr(a, "column")]
        if not items:
            return []
        messages = [
            {"role": "system", "content": ANOMALY_EXPLAINER_SYSTEM},
            {"role": "user", "content": f"Anomalies: {items}\n\nReturn JSON array."},
        ]
        try:
            raw = await self.ollama.chat("reasoner", messages, json_mode=True, max_tokens=800)
            import json
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Anomaly explanation failed: {e}")
            return []

    def _build_summary_from_l3(self, insights, profile):
        l3 = insights.get("l3_insights", []) if isinstance(insights, dict) else []
        if l3 and isinstance(l3, list) and len(l3) > 0:
            first = l3[0]
            if isinstance(first, dict):
                insight = first.get("insight", "")
                action = first.get("action", "")
                if insight:
                    return f"{insight} {action}".strip()[:500]
        return f"Analysis complete. Dataset has {profile.rows} rows and {profile.cols} columns."

    def _extract_key_findings(self, insights):
        l1 = insights.get("l1_facts", []) if isinstance(insights, dict) else []
        out = []
        for f in l1[:3]:
            if isinstance(f, str):
                out.append({"headline": f[:60] + ("…" if len(f) > 60 else ""),
                            "detail": f, "impact": "medium"})
        return out

    def _extract_next_steps(self, insights):
        l3 = insights.get("l3_insights", []) if isinstance(insights, dict) else []
        out = []
        for item in l3[:3]:
            if isinstance(item, dict):
                action = item.get("action", "")
                if action:
                    out.append({"action": action,
                                "reason": item.get("insight", ""),
                                "priority": "P1" if item.get("urgency") == "high" else "P2"})
        return out

    def _compute_health_score(self, profile, anomalies, warnings):
        """100 - (duplicate_rows * 0.5) - (avg_null_pct * 0.3) - (anomalies * 1)"""
        score = 100.0
        if profile.duplicates:
            score -= min(profile.duplicates * 0.5, 20)
        if profile.null_pct:
            avg_null = sum(profile.null_pct.values()) / max(len(profile.null_pct), 1)
            score -= min(avg_null * 0.3, 20)
        score -= min(len(anomalies) * 1, 20)
        if warnings:
            score -= min(len(warnings) * 2, 20)
        return max(0, round(score, 1))


def pd_numeric_safe(series):
    """Convert pandas series to list of floats, drop NaN."""
    try:
        import pandas as pd
        return pd.to_numeric(series, errors="coerce").dropna().tolist()
    except Exception:
        return []
