"""
grounded_insight_generator.py

Generates Level 3 board-level insights by feeding the LLM COMPUTED ANSWERS,
not raw statistics. The LLM synthesizes and articulates — never calculates.
"""
import json
import logging
import time
import re
from ai.dataset_classifier import DatasetMeta
from ai.analytical_engine import Finding
from ai.nim_client import NIMClient

logger = logging.getLogger("GroundedInsightGenerator")

# Words that must NOT appear in final insights (replace with plain English)
FORBIDDEN_STAT_TERMS = {
    "mean":          "average",
    "std":           "variation",
    "variance":      "spread",
    "correlation":   "connection",
    "distribution":  "spread",
    "outlier":       "unusually high or low value",
    "regression":    "trend line",
    "coefficient":   "relationship strength",
    "percentile":    "ranking",
    "z-score":       "statistical flag",
}

SYSTEM_PROMPT = """You are a Chief Strategy Officer presenting to the board of directors.

Your job: Transform computed data findings into strategic business insights that drive decisions.

STRICT RULES:
1. Every insight MUST reference a specific number from the findings
2. Never state what is directly visible in the numbers — reveal what is non-obvious
3. Focus on IMPLICATIONS, not observations
4. Each insight = what happened + why it matters + what to do
5. Business language only — no technical terms, no stat jargon
6. The insight should surprise or challenge assumptions
7. Never say "the data shows" or "analysis reveals"
8. Never use: mean, std, variance, correlation, outlier, distribution, z-score
9. Speak as if you already knew this from years of industry experience
10. Each recommended action must be executable within one business week"""


class GroundedInsightGenerator:
    """
    Generates 3 board-level strategic insights from pre-computed analytical findings.
    Only module that calls NIM — never receives raw DataFrames.
    """

    def generate(
        self, meta: DatasetMeta, findings: list, nim_client: NIMClient
    ) -> dict:
        """
        Args:
            meta:       DatasetMeta from DatasetClassifier
            findings:   list[Finding] from AnalyticalEngine (sorted high→low significance)
            nim_client: NIMClient instance

        Returns dict with keys:
            insights, dataset_type, business_question, findings_count,
            insight_quality, generated_at
        """
        if not findings:
            return self._fallback_result(meta, [])

        # Sort by significance and take top 6 findings
        order = {"high": 0, "medium": 1, "low": 2}
        sorted_findings = sorted(findings, key=lambda f: order.get(f.significance, 3))[:6]

        findings_text = self._format_findings(sorted_findings)
        user_prompt   = self._build_user_prompt(meta, findings_text)

        try:
            raw = nim_client.chat(
                model_name="kimi_k2",
                user_prompt=user_prompt,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=1000,
                temperature=0.3
            )
            raw = nim_client._strip_thinking(raw)
            raw = self._clean_json(raw)
            insights = json.loads(raw)

            if not isinstance(insights, list):
                raise ValueError("Response is not a JSON array")

            validated = [self._validate_insight(ins, i, sorted_findings) for i, ins in enumerate(insights[:3])]
            validated = self._sanitize_language(validated)

            return {
                "insights":          validated,
                "dataset_type":      meta.dataset_type,
                "business_question": meta.business_question,
                "findings_count":    len(findings),
                "insight_quality":   "grounded",
                "generated_at":      int(time.time()),
            }

        except Exception as e:
            logger.error(f"GroundedInsightGenerator failed: {e}")
            return self._fallback_result(meta, sorted_findings)

    # ────────────────────────────────────────────────────────────────────
    # Prompt Building
    # ────────────────────────────────────────────────────────────────────

    def _format_findings(self, findings: list) -> str:
        lines = []
        for i, f in enumerate(findings):
            lines.append(f"""
FINDING {i+1}: {f.question}
COMPUTED ANSWER: {f.answer}
SIGNIFICANCE: {f.significance}
KEY DATA: {json.dumps({k: v for k, v in list(f.data.items())[:5]}, default=str)}
---""")
        return "\n".join(lines)

    def _build_user_prompt(self, meta: DatasetMeta, findings_text: str) -> str:
        return f"""DATASET: {meta.dataset_description}
BUSINESS QUESTION: {meta.business_question}

COMPUTED FINDINGS (these are factual — do not recalculate):
{findings_text}

Generate exactly 3 strategic insights.

Each insight MUST follow this JSON structure:
{{
  "headline": "One powerful sentence — the strategic conclusion (max 15 words)",
  "context": "Two sentences explaining why this matters for the business",
  "recommended_action": "One specific action a manager can take this week",
  "supporting_metric": "The single most compelling number that proves this insight",
  "impact_area": "revenue|cost|risk|growth|efficiency",
  "magnitude": "high|medium|low",
  "finding_reference": "FINDING 1|FINDING 2|FINDING 3|etc"
}}

QUALITY CHECK before each insight:
- Would a CFO find this useful and actionable?
- Does it go beyond what is obvious from looking at the numbers?
- Does it recommend a specific action that can start this week?
- Is it grounded in the computed findings above?

Return ONLY a valid JSON array of 3 insights. No markdown. No preamble. No text outside the JSON."""

    # ────────────────────────────────────────────────────────────────────
    # Post-Processing
    # ────────────────────────────────────────────────────────────────────

    def _validate_insight(self, ins: dict, idx: int, findings: list) -> dict:
        """Ensure all required fields are present, filling with fallbacks."""
        required = {
            "headline":           f"Strategic insight {idx+1} from {findings[min(idx, len(findings)-1)].question[:40]}",
            "context":            findings[min(idx, len(findings)-1)].answer[:200] if findings else "",
            "recommended_action": "Review this finding with your team and develop a targeted response plan.",
            "supporting_metric":  findings[min(idx, len(findings)-1)].data.get("gap_pct",
                                  findings[min(idx, len(findings)-1)].data.get("winner_val", "See finding")) if findings else "",
            "impact_area":        "growth",
            "magnitude":          findings[min(idx, len(findings)-1)].significance if findings else "medium",
            "finding_reference":  f"FINDING {idx+1}",
        }
        result = {}
        for key, fallback in required.items():
            val = ins.get(key)
            if not val or (isinstance(val, str) and not val.strip()):
                result[key] = str(fallback)[:300]
            else:
                result[key] = str(val)[:300]

        # Validate magnitude
        if result["magnitude"] not in ("high", "medium", "low"):
            result["magnitude"] = "medium"

        # Validate impact_area
        valid_areas = ("revenue", "cost", "risk", "growth", "efficiency")
        if result["impact_area"] not in valid_areas:
            result["impact_area"] = "growth"

        return result

    def _sanitize_language(self, insights: list) -> list:
        """Replace forbidden statistical terms with plain English."""
        insights_str = json.dumps(insights)
        for term, replacement in FORBIDDEN_STAT_TERMS.items():
            insights_str = re.sub(
                r'\b' + re.escape(term) + r'\b',
                replacement,
                insights_str,
                flags=re.IGNORECASE
            )
        try:
            return json.loads(insights_str)
        except Exception:
            return insights

    def _clean_json(self, raw: str) -> str:
        """Strip markdown fences and find first JSON array."""
        raw = raw.strip()
        # Remove code fences
        raw = re.sub(r'```(?:json)?', '', raw)
        raw = raw.replace('```', '').strip()
        # Find first [
        idx = raw.find('[')
        if idx != -1:
            raw = raw[idx:]
        # Find last ]
        ridx = raw.rfind(']')
        if ridx != -1:
            raw = raw[:ridx+1]
        return raw

    def _fallback_result(self, meta: DatasetMeta, findings: list) -> dict:
        """Return structured fallback when LLM call fails."""
        fallback_insights = []
        for i, f in enumerate(findings[:3]):
            fallback_insights.append({
                "headline":           f.answer[:120],
                "context":            f"This finding addresses: {f.question}",
                "recommended_action": "Review this finding with your team and develop a response plan.",
                "supporting_metric":  str(list(f.data.values())[0])[:80] if f.data else "See analysis",
                "impact_area":        "growth",
                "magnitude":          f.significance,
                "finding_reference":  f"FINDING {i+1}",
            })

        return {
            "insights":          fallback_insights,
            "dataset_type":      meta.dataset_type,
            "business_question": meta.business_question,
            "findings_count":    len(findings),
            "insight_quality":   "fallback",
            "generated_at":      int(time.time()),
        }
