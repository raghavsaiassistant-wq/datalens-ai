"""
anomaly_detector.py

Detects outliers, sudden changes, and missing data spikes in a DataProfile.
Connects to NIMClient for AI-generated explanations in plain English.
"""
import numpy as np
import scipy.stats as stats
from dataclasses import dataclass
from typing import List, Optional, Any
import pandas as pd
from ai.nim_client import NIMClient
from parsers.base_parser import DataProfile

@dataclass
class AnomalyFlag:
    column: str
    value: Any
    row_index: int
    anomaly_type: str
    severity: str
    explanation: str
    z_score: Optional[float]

class AnomalyDetector:
    """Statistical detector combined with AI-generated business explanations."""

    def detect(self, profile: DataProfile, nim_client: NIMClient) -> List[AnomalyFlag]:
        """Runs the 5-step anomaly detection pipeline."""
        df = profile.df
        anomalies: List[AnomalyFlag] = []
        numeric_cols = [c for c, t in profile.column_types.items() if t == "numeric"]
        
        caught_indexes = {c: set() for c in numeric_cols}

        def _safe_idx(idx):
            """Convert row index to int safely; return -1 if not convertible."""
            try:
                return int(idx)
            except (ValueError, TypeError):
                return -1

        # STEP 1: Z-Score Outliers
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            # Cast to float to avoid bool/integer edge cases with zscore
            series = series.astype(float)
            try:
                z_scores = stats.zscore(series, nan_policy='omit')
            except Exception:
                continue
            col_anomalies = 0

            for idx, z in zip(series.index, z_scores):
                if col_anomalies >= 3:
                    break
                if pd.isna(z) or np.isinf(z):
                    continue
                if abs(z) > 3.0:
                    caught_indexes[col].add(idx)
                    val = series.loc[idx]
                    sev = "high" if z > 3.0 else "medium"
                    atype = "outlier_high" if z > 3.0 else "outlier_low"
                    val = float(val) if hasattr(val, 'item') else val
                    anomalies.append(AnomalyFlag(
                        column=col, value=val, row_index=_safe_idx(idx),
                        anomaly_type=atype, severity=sev, explanation="", z_score=float(z)
                    ))
                    col_anomalies += 1

        # STEP 2: IQR Fence
        for col in numeric_cols:
            series = df[col].dropna().astype(float)
            if len(series) < 10:
                continue
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                continue  # zero-variance column, skip
            lower_fence = Q1 - 1.5 * IQR
            upper_fence = Q3 + 1.5 * IQR

            col_anomalies = 0
            for idx, val in series.items():
                if col_anomalies >= 2:
                    break
                if idx in caught_indexes[col]:
                    continue
                if val < lower_fence or val > upper_fence:
                    caught_indexes[col].add(idx)
                    val_native = float(val) if hasattr(val, 'item') else val
                    atype = "outlier_high" if val > upper_fence else "outlier_low"
                    anomalies.append(AnomalyFlag(
                        column=col, value=val_native, row_index=_safe_idx(idx),
                        anomaly_type=atype, severity="medium", explanation="", z_score=None
                    ))
                    col_anomalies += 1

        # STEP 3: Sudden change
        if profile.has_datetime:
            date_cols = [c for c, t in profile.column_types.items() if t == "datetime"]
            if date_cols:
                date_col = date_cols[0]
                df_sorted = df.sort_values(by=date_col)
                for col in numeric_cols:
                    series = df_sorted[col].astype(float)
                    pct_change = series.pct_change()
                    col_anomalies = 0
                    for idx, change in pct_change.items():
                        # Skip NaN and inf (inf happens when previous value was 0)
                        if pd.isna(change) or np.isinf(change):
                            continue
                        if col_anomalies >= 2:
                            break
                        if abs(change) > 0.5:
                            val = series.loc[idx]
                            val_native = float(val) if hasattr(val, 'item') else val
                            anomalies.append(AnomalyFlag(
                                column=col, value=val_native, row_index=_safe_idx(idx),
                                anomaly_type="sudden_change", severity="high", explanation="", z_score=None
                            ))
                            col_anomalies += 1

        # STEP 4: Missing data spike
        for col, pct in profile.null_pct.items():
            if pct > 30.0:
                sev = "high" if pct > 50.0 else "medium"
                anomalies.append(AnomalyFlag(
                    column=col, value=f"{pct}% missing", row_index=-1,
                    anomaly_type="missing_spike", severity=sev, explanation="", z_score=None
                ))

        # Sort by severity
        severity_map = {"high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda x: severity_map.get(x.severity, 4))
        anomalies = anomalies[:10]

        # STEP 5: AI explanation
        for flag in anomalies:
            try:
                system_prompt = "You are a business analyst. Explain data anomalies in plain English for non-technical managers. Be concise — one sentence only."
                user_prompt = f"Dataset: {profile.file_name}. Column: {flag.column}. Anomaly: {flag.anomaly_type}. Value: {flag.value}. Explain why this is concerning for business."
                resp = nim_client.chat(model_name="mistral_7b", user_prompt=user_prompt, system_prompt=system_prompt, max_tokens=60)
                flag.explanation = resp.strip()
            except Exception:
                flag.explanation = f"Detected {flag.anomaly_type} in {flag.column} with value {flag.value}."

        return anomalies
