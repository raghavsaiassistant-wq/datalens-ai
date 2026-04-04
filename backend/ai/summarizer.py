"""
summarizer.py

Synthesizes profiles and anomalies into an executive JSON summary via LLM.
"""
from parsers.base_parser import DataProfile
from ai.nim_client import NIMClient
from ai.anomaly_detector import AnomalyFlag
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger("Summarizer")

class Summarizer:
    """Sends combined profile + anomalies to the LLM to get a structured summary."""

    def summarize(self, profile: DataProfile, anomalies: List[AnomalyFlag], nim_client: NIMClient) -> Dict[str, Any]:
        
        date_range = 'No date column'
        if profile.has_datetime:
            date_col = next((c for c, t in profile.column_types.items() if t == "datetime"), None)
            if date_col and date_col in profile.df.columns:
                try:
                    col_series = profile.df[date_col].dropna()
                    if len(col_series) > 0:
                        d_min = col_series.min()
                        d_max = col_series.max()
                        # Guard against NaT (failed date coercion)
                        import pandas as _pd
                        if _pd.notna(d_min) and _pd.notna(d_max):
                            date_range = str(d_min)[:10] + " to " + str(d_max)[:10]
                except Exception:
                    pass
        
        top5_stats = {k: profile.numeric_summary[k] for k in list(profile.numeric_summary.keys())[:5]}
        stat_lines = "\\n".join([f"- {k}: {v}" for k, v in top5_stats.items()])
        anom_lines = "\\n".join([f"- {a.anomaly_type} in {a.column}: {a.value}" for a in anomalies[:3]])
        
        cols_with_nulls = [k for k, v in profile.null_pct.items() if v > 0]
        cols_with_nulls_str = ", ".join(cols_with_nulls) if cols_with_nulls else "None"
        
        system_prompt = "You are a senior business intelligence analyst presenting to C-suite executives. Write insight-driven analysis using actual numbers from the data. Never use technical jargon. Always speak in business language. Be concise and impactful."
        
        user_prompt = f"""Analyze this dataset and generate a business intelligence report.

DATASET OVERVIEW:
- File: {profile.file_name}
- Size: {profile.rows} rows × {profile.cols} columns
- KPI Columns: {profile.kpi_columns}
- Date Range: {date_range}

KEY STATISTICS:
{stat_lines}

ANOMALIES DETECTED:
{anom_lines}

DATA QUALITY:
- Duplicate rows: {profile.duplicates}
- Columns with missing data: {cols_with_nulls_str}

Generate your response in this EXACT JSON format:
{{
  "executive_summary": "3-5 sentence paragraph. Must include at least 2 specific numbers from the data. Written for a CEO.",
  "key_findings": [
    {{
      "headline": "Short punchy title under 8 words",
      "detail": "One sentence with a specific number or percentage",
      "impact": "high"
    }},
    {{
      "headline": "...",
      "detail": "...",
      "impact": "medium"
    }},
    {{
      "headline": "...",
      "detail": "...",
      "impact": "low"
    }}
  ],
  "next_steps": [
    {{
      "action": "Specific action verb + what to do",
      "reason": "One sentence why this matters",
      "priority": "immediate"
    }},
    {{
      "action": "...",
      "reason": "...",
      "priority": "short-term"
    }},
    {{
      "action": "...",
      "reason": "...",
      "priority": "long-term"
    }}
  ],
  "data_health_score": 85
}}

data_health_score: integer 0-100 based on:
- Starts at 100
- Minus 10 for each column with >30% nulls
- Minus 5 for every 100 duplicate rows
- Minus 10 for each high severity anomaly
- Minus 5 for each medium severity anomaly
- Never below 0

Return ONLY valid JSON. No markdown fences. No explanation. No preamble.
"""
        try:
            resp = nim_client.chat(model_name="llama_70b", user_prompt=user_prompt, system_prompt=system_prompt, max_tokens=1000, temperature=0.3)
            parsed = self._parse_json_result(resp)
            if not parsed:
                resp = nim_client.chat(model_name="kimi_k2", user_prompt=user_prompt, system_prompt=system_prompt, max_tokens=1000, temperature=0.3)
                parsed = self._parse_json_result(resp)
            if parsed:
                self._validate_keys(parsed)
                return parsed
        except Exception as e:
            logger.error(f"Summarizer failed: {e}")

        return {
            "executive_summary": "Analysis failed due to API limitations or unexpected errors.",
            "key_findings": [{"headline": "Error", "detail": "Data unavailable.", "impact": "low"}] * 3,
            "next_steps": [{"action": "Retry", "reason": "System error", "priority": "immediate"}] * 3,
            "data_health_score": 0
        }

    def _parse_json_result(self, raw: str) -> dict:
        try:
            raw = raw.strip()
            if raw.startswith("```json"): raw = raw[7:]
            if raw.startswith("```"): raw = raw[3:]
            if raw.endswith("```"): raw = raw[:-3]
            return json.loads(raw.strip())
        except Exception:
            return {}
            
    def _validate_keys(self, result: dict):
        """Ensures the response has the required keys and types for the frontend."""
        defaults = {
            "executive_summary": "Analysis summary unavailable.",
            "key_findings": [
                {"headline": "Insight Pending", "detail": "Developing data perspectives...", "impact": "low"},
                {"headline": "Insight Pending", "detail": "Synthesizing trends...", "impact": "low"},
                {"headline": "Insight Pending", "detail": "Finalizing data patterns...", "impact": "low"}
            ],
            "next_steps": [
                {"action": "Verify Data", "reason": "System error during next step generation", "priority": "short-term"},
                {"action": "Review Dashboard", "reason": "Consult existing charts for patterns", "priority": "short-term"},
                {"action": "Check Sources", "reason": "Ensure data integrity for future analysis", "priority": "short-term"}
            ],
            "data_health_score": 50
        }
        
        for key, default in defaults.items():
            if key not in result or not result[key]:
                result[key] = default
            elif key in ("key_findings", "next_steps") and not isinstance(result[key], list):
                result[key] = default
