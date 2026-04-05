"""
insight_engine.py

Level 3 Insight Engine — runs a 3-prompt chain to produce board-level
business insights from statistical data profiles and anomalies.

Chain:
  L1 — "What happened?" (facts)
  L2 — "Why?" (root causes)
  L3 — "What should the board decide?" (strategic actions)
"""
import json
import logging
from ai.nim_client import NIMClient

logger = logging.getLogger("InsightEngine")


class InsightEngine:
    """
    Orchestrates the 3-level insight generation chain.
    Each level builds on the previous, producing increasingly strategic output.
    """

    def generate_insights(
        self,
        profile,
        anomalies: list,
        nim_client: NIMClient,
        filter_context: dict = None
    ) -> dict:
        """
        Args:
            profile:        DataProfile or SimpleNamespace with numeric_summary,
                            kpi_columns, rows, cols, column_types
            anomalies:      List of anomaly dicts from AnomalyDetector
            nim_client:     NIMClient instance
            filter_context: Optional dict with filter info for regeneration context
                            e.g. {"filtered_rows": 450, "original_rows": 1000, "active_filters": {...}}

        Returns:
        {
          "l1_facts":    [str, ...],         # 5 factual observations
          "l2_causes":   [{observation, root_cause}, ...],
          "l3_insights": [{title, insight, action, urgency, metric_impact}, ...]  # 3 items
        }
        """
        result = {"l1_facts": [], "l2_causes": [], "l3_insights": []}

        # --- L1: What happened? ---
        l1_facts = self._generate_l1(profile, anomalies, nim_client)
        result["l1_facts"] = l1_facts

        if not l1_facts:
            logger.warning("InsightEngine: L1 produced no facts, stopping chain.")
            return result

        # --- L2: Why? ---
        l2_causes = self._generate_l2(profile, l1_facts, anomalies, nim_client)
        result["l2_causes"] = l2_causes

        # --- L3: Board-level decisions ---
        l3_insights = self._generate_l3(l1_facts, l2_causes, filter_context, nim_client)
        result["l3_insights"] = l3_insights

        return result

    # ------------------------------------------------------------------ #
    #  L1 — Facts                                                          #
    # ------------------------------------------------------------------ #
    def _generate_l1(self, profile, anomalies: list, nim_client: NIMClient) -> list:
        numeric_summary_str = self._format_numeric_summary(profile)
        kpi_str = ", ".join(profile.kpi_columns[:6]) if profile.kpi_columns else "none detected"
        anomaly_str = self._format_anomalies(anomalies, max_count=5)

        prompt = f"""You are a data analyst. Analyze the following dataset statistics and return EXACTLY 5 factual observations.

Dataset: {profile.rows} rows, {profile.cols} columns
KPI columns: {kpi_str}

Numeric summary:
{numeric_summary_str}

Top anomalies detected:
{anomaly_str}

Return ONLY a valid JSON array of exactly 5 strings. Each string is one factual observation.
No interpretation, no recommendations — only facts visible in the data.
Example: ["Revenue mean is $45,230 with high variance (std=$12,400)", ...]

JSON array:"""

        try:
            raw = nim_client.chat("kimi_k2", prompt, max_tokens=600, temperature=0.1)
            raw = nim_client._strip_thinking(raw)
            raw = self._clean_json(raw)
            facts = json.loads(raw)
            if isinstance(facts, list):
                return [str(f) for f in facts[:5]]
        except Exception as e:
            logger.error(f"InsightEngine L1 failed: {e}")
        return []

    # ------------------------------------------------------------------ #
    #  L2 — Root Causes                                                    #
    # ------------------------------------------------------------------ #
    def _generate_l2(self, profile, l1_facts: list, anomalies: list, nim_client: NIMClient) -> list:
        facts_str = "\n".join(f"- {f}" for f in l1_facts)
        corr_str = self._format_correlations(profile)

        prompt = f"""You are a senior data scientist. Given these factual observations from a dataset:
{facts_str}

Column correlations:
{corr_str}

For each observation, provide one likely root cause based on statistical patterns.
Return ONLY a valid JSON array of objects with keys "observation" and "root_cause".
Exactly {len(l1_facts)} objects.

JSON array:"""

        try:
            raw = nim_client.chat("kimi_k2", prompt, max_tokens=800, temperature=0.2)
            raw = nim_client._strip_thinking(raw)
            raw = self._clean_json(raw)
            causes = json.loads(raw)
            if isinstance(causes, list):
                return [
                    {"observation": str(c.get("observation", "")), "root_cause": str(c.get("root_cause", ""))}
                    for c in causes if isinstance(c, dict)
                ]
        except Exception as e:
            logger.error(f"InsightEngine L2 failed: {e}")
        return []

    # ------------------------------------------------------------------ #
    #  L3 — Board Decisions                                                #
    # ------------------------------------------------------------------ #
    def _generate_l3(self, l1_facts: list, l2_causes: list, filter_context, nim_client: NIMClient) -> list:
        facts_str = "\n".join(f"- {f}" for f in l1_facts)
        causes_str = "\n".join(
            f"- Observation: {c['observation']} → Root cause: {c['root_cause']}"
            for c in l2_causes
        ) if l2_causes else "Root cause analysis unavailable."

        filter_note = ""
        if filter_context:
            filtered = filter_context.get("filtered_rows", "?")
            original = filter_context.get("original_rows", "?")
            filter_note = f"\nNote: These insights are based on a filtered view ({filtered} of {original} rows)."

        prompt = f"""You are a board-level business advisor. Based on data analysis findings:

FACTS:
{facts_str}

ROOT CAUSES:
{causes_str}{filter_note}

Generate exactly 3 strategic business decisions the board should consider.
Return ONLY valid JSON — an array of exactly 3 objects with these keys:
- "title": short decision title (5-8 words)
- "insight": one sentence explaining the strategic finding
- "action": one sentence describing the recommended action
- "urgency": exactly one of "high", "medium", or "low"
- "metric_impact": one metric that will be affected (e.g. "Revenue +15%", "Churn -8%")

JSON array:"""

        try:
            raw = nim_client.chat("llama_70b", prompt, max_tokens=1000, temperature=0.3)
            raw = nim_client._strip_thinking(raw)
            raw = self._clean_json(raw)
            insights = json.loads(raw)
            if isinstance(insights, list):
                validated = []
                for item in insights[:3]:
                    if not isinstance(item, dict):
                        continue
                    validated.append({
                        "title":         str(item.get("title", "Strategic Insight")),
                        "insight":       str(item.get("insight", "")),
                        "action":        str(item.get("action", "")),
                        "urgency":       item.get("urgency", "medium") if item.get("urgency") in ("high", "medium", "low") else "medium",
                        "metric_impact": str(item.get("metric_impact", ""))
                    })
                return validated
        except Exception as e:
            logger.error(f"InsightEngine L3 failed: {e}")
        return []

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _format_numeric_summary(self, profile) -> str:
        try:
            summary = profile.numeric_summary
            if not summary:
                return "No numeric summary available."
            lines = []
            for col, stats in list(summary.items())[:8]:
                mean = stats.get("mean", "?")
                std = stats.get("std", "?")
                min_v = stats.get("min", "?")
                max_v = stats.get("max", "?")
                lines.append(f"  {col}: mean={mean}, std={std}, min={min_v}, max={max_v}")
            return "\n".join(lines) if lines else "No numeric summary available."
        except Exception:
            return "No numeric summary available."

    def _format_anomalies(self, anomalies: list, max_count: int = 5) -> str:
        if not anomalies:
            return "No anomalies detected."
        lines = []
        for a in anomalies[:max_count]:
            col = a.get("column", "?")
            atype = a.get("anomaly_type", "?")
            explanation = a.get("explanation", "")
            lines.append(f"  [{atype}] {col}: {explanation[:120]}")
        return "\n".join(lines)

    def _format_correlations(self, profile) -> str:
        try:
            col_types = profile.column_types if hasattr(profile, 'column_types') else {}
            numeric_cols = [c for c, t in col_types.items() if t == 'numeric']
            if len(numeric_cols) < 2:
                return "Insufficient numeric columns for correlation."
            return f"Numeric columns available: {', '.join(numeric_cols[:10])}"
        except Exception:
            return "Correlation data unavailable."

    def _clean_json(self, raw: str) -> str:
        """Strip markdown code fences and leading/trailing whitespace."""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.replace("```", "").strip()
        # Find first [ or { to handle models that add preamble text
        for start_char in ('[', '{'):
            idx = raw.find(start_char)
            if idx != -1:
                raw = raw[idx:]
                break
        return raw
