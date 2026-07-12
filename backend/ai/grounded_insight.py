"""
grounded_insight.py (refactored) — SOLE writer to result["insights"]["l3_insights"].
Fixes Bug #2: dual-path overwriting.
Uses gpt-oss-120b-cloud (reasoner role) for board-level narrative.
"""
import json
import re
import logging
from typing import Dict, Any, List
from ai.prompts import CSO_SYSTEM
from ai.ollama_client import OllamaClient

logger = logging.getLogger("GroundedInsight")

# Words that must NOT appear in final insights (replace with plain English)
FORBIDDEN_STAT_TERMS = {
    "mean": "average",
    "std": "variation",
    "variance": "spread",
    "correlation": "connection",
    "distribution": "spread",
    "outlier": "unusually high or low value",
    "regression": "trend line",
    "coefficient": "relationship strength",
    "percentile": "ranking",
    "z-score": "statistical flag",
    "sigma": "standard deviations",
}


class GroundedInsight:
    """Generates L3 board-level narrative from L1+L2 facts. Sole writer."""

    def __init__(self, ollama: OllamaClient):
        self.ollama = ollama

    async def l3(self, l1l2: Dict[str, Any], meta) -> Dict[str, Any]:
        """
        Generate L3 board decisions from L1 facts + L2 causes.
        Also produces executive_summary, key_findings, next_steps.
        """
        l1 = l1l2.get("l1_facts", [])
        l2 = l1l2.get("l2_causes", [])
        if not l1:
            logger.warning("No L1 facts to ground; returning empty L3")
            return {"l3_insights": [], "executive_summary": "", "key_findings": [], "next_steps": []}

        facts_text = "\n".join(f"- {f}" for f in l1[:5])
        causes_text = "\n".join(
            f"- {c.get('observation', '')} → {c.get('root_cause', '')}" for c in l2[:5]
        )

        user_prompt = f"""DATASET TYPE: {getattr(meta, 'dataset_type', 'general')}

L1 FACTS (what is happening):
{facts_text}

L2 CAUSES (why it might be happening):
{causes_text}

Synthesize 3 board-level decisions. Each = what + why it matters + what to do this week.
Return the full JSON (executive_summary, key_findings, next_steps, l3_insights)."""

        messages = [
            {"role": "system", "content": CSO_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]
        try:
            raw = await self.ollama.chat("reasoner", messages, json_mode=True, max_tokens=3500)
            data = self._extract_json(raw)
            data = self._scrub_forbidden_terms(data)
            return {
                "l3_insights": data.get("l3_insights", [])[:3] or data.get("key_findings", [])[:3],
                "executive_summary": data.get("executive_summary", ""),
                "key_findings": data.get("key_findings", [])[:3],
                "next_steps": data.get("next_steps", [])[:3],
            }
        except Exception as e:
            logger.error(f"GroundedInsight.l3 failed: {e}")
            return {"l3_insights": [], "executive_summary": "", "key_findings": [], "next_steps": []}

    @staticmethod
    def _scrub_forbidden_terms(data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace forbidden stat terms in all string values of the dict."""
        if isinstance(data, dict):
            return {k: GroundedInsight._scrub_forbidden_terms(v) for k, v in data.items()}
        if isinstance(data, list):
            return [GroundedInsight._scrub_forbidden_terms(v) for v in data]
        if isinstance(data, str):
            for bad, good in FORBIDDEN_STAT_TERMS.items():
                data = re.sub(rf"\b{re.escape(bad)}\b", good, data, flags=re.IGNORECASE)
            return data
        return data

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from text that may be wrapped in ```json ... ``` fences."""
        import json
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try extracting from ```json ... ``` fence (handle nested braces)
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        # Try first { to last } block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        raise ValueError(f"Could not extract JSON from: {text[:200]}")
