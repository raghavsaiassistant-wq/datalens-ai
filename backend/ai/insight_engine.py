"""
insight_engine.py (refactored) — L1+L2 in ONE call.
Collapsed from the old 3-prompt chain (L1→L2→L3) to save 1/3 of LLM calls.
L3 is now handled by grounded_insight.py (sole writer to result["insights"]).
"""
import json
import logging
from typing import Dict, Any
from ai.prompts import ANALYST_SYSTEM
from ai.ollama_client import OllamaClient

logger = logging.getLogger("InsightEngine")


class InsightEngine:
    """Produces L1 facts + L2 root causes in a single LLM call."""

    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama

    async def l1l2(self, profile, anomalies, findings) -> Dict[str, Any]:
        """
        Generate L1 (facts) + L2 (causes) in one call.
        Returns: {l1_facts: [...], l2_causes: [...], l3_insights: []}
        """
        numeric_summary_str = self._format_numeric_summary(profile)
        kpi_str = ", ".join(profile.kpi_columns[:6]) if profile.kpi_columns else "none detected"
        anomaly_str = self._format_anomalies(anomalies, max_count=5)
        findings_str = self._format_findings(findings)

        user_prompt = f"""Analyze this dataset and produce L1 facts + L2 causes.

DATASET: {profile.rows} rows, {profile.cols} columns
KPI COLUMNS: {kpi_str}

NUMERIC SUMMARY (top columns):
{numeric_summary_str}

TOP ANOMALIES (statistical):
{anomaly_str}

COMPUTED FINDINGS (from analytical engine):
{findings_str}

Output the JSON with EXACTLY 5 L1 facts and matching L2 causes."""

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        try:
            raw = await self.ollama.chat("analyst", messages, json_mode=True, max_tokens=2500)
            data = self._extract_json(raw)
            return {
                "l1_facts": data.get("l1_facts", [])[:5],
                "l2_causes": data.get("l2_causes", [])[:5],
                # l3 from L1L2 will be DISCARDED — grounded_insight.l3 is the sole L3 writer
                "l3_insights": [],
            }
        except Exception as e:
            logger.error(f"InsightEngine.l1l2 failed: {e}")
            return {"l1_facts": [], "l2_causes": [], "l3_insights": []}

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from text that may be wrapped in ```json ... ``` fences."""
        import re
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try extracting from ```json ... ``` fence
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # Try to find first { ... last } block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise ValueError(f"Could not extract JSON from: {text[:200]}")

    @staticmethod
    def _format_numeric_summary(profile) -> str:
        if not profile.numeric_summary:
            return "(no numeric columns)"
        lines = []
        for col, stats in list(profile.numeric_summary.items())[:5]:
            if isinstance(stats, dict):
                lines.append(f"- {col}: min={stats.get('min', '?')}, max={stats.get('max', '?')}, mean={stats.get('mean', '?')}")
        return "\n".join(lines) if lines else "(numeric summary not populated)"

    @staticmethod
    def _format_anomalies(anomalies, max_count=5) -> str:
        if not anomalies:
            return "(no statistical anomalies detected)"
        lines = []
        for a in anomalies[:max_count]:
            if hasattr(a, "column"):
                lines.append(f"- {a.column}: value={a.value} (z={a.z_score}, severity={a.severity})")
        return "\n".join(lines) if lines else "(no anomalies)"

    @staticmethod
    def _format_findings(findings) -> str:
        if not findings:
            return "(no analytical findings)"
        lines = []
        for f in findings[:8]:
            if hasattr(f, "statement"):
                lines.append(f"- [{f.significance}] {f.statement}")
            elif isinstance(f, dict):
                lines.append(f"- {f.get('statement', f.get('title', str(f)[:100]))}")
        return "\n".join(lines) if lines else "(no findings)"
