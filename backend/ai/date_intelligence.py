"""
date_intelligence.py

Computes advanced time-series baseline metrics from a DataFrame:
MoM, WoW, YoY % changes, trend R², best/worst periods, and simple forecasts.
"""
import logging
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger("DateIntelligence")


class DateIntelligence:
    """
    Analyzes a date column against one or more numeric columns to produce
    baseline intelligence metrics for the v2.0 dashboard.
    """

    def analyze(self, df: pd.DataFrame, date_col: str, numeric_cols: list, profile) -> dict:
        """
        Args:
            df:           DataFrame (may be full or sampled)
            date_col:     Name of the datetime column
            numeric_cols: List of numeric column names to analyze
            profile:      DataProfile (used for warnings list if needed)

        Returns dict with structure:
        {
          "date_col": str,
          "date_range": {"start": str, "end": str},
          "granularity": str,
          "metrics": {
            col_name: {
              "mom_pct": float | None,
              "wow_pct": float | None,
              "yoy_pct": float | None,
              "trend_slope": float,
              "trend_r2": float,
              "best_period": str,
              "worst_period": str,
              "forecast_next": float
            }
          }
        }
        Returns {} on failure.
        """
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.dropna(subset=[date_col])
            df = df.sort_values(date_col).reset_index(drop=True)

            if len(df) < 4:
                logger.warning(f"DateIntelligence: too few rows ({len(df)}) after date parse.")
                return {}

            date_range = {
                "start": df[date_col].min().isoformat(),
                "end": df[date_col].max().isoformat()
            }
            granularity = self._detect_granularity(df[date_col])

            metrics = {}
            for col in numeric_cols:
                if col not in df.columns:
                    continue
                series = df[[date_col, col]].dropna()
                if len(series) < 4:
                    continue
                try:
                    metrics[col] = self._compute_col_metrics(series, date_col, col)
                except Exception as e:
                    logger.warning(f"DateIntelligence: failed on col '{col}': {e}")

            return {
                "date_col": date_col,
                "date_range": date_range,
                "granularity": granularity,
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"DateIntelligence.analyze() failed: {e}")
            return {}

    def _compute_col_metrics(self, series: pd.DataFrame, date_col: str, value_col: str) -> dict:
        series = series.copy()
        series = series.set_index(date_col)
        s = series[value_col].astype(float)

        # --- Trend via linear regression ---
        x = np.arange(len(s))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, s.values)
        trend_r2 = round(float(r_value ** 2), 4)
        trend_slope = round(float(slope), 6)

        # --- Forecast next point ---
        last_value = float(s.iloc[-1])
        forecast_next = round(last_value + slope, 4)

        # --- Monthly resampling for period stats ---
        monthly = s.resample('ME').mean().dropna()

        best_period = None
        worst_period = None
        if len(monthly) >= 2:
            best_period = str(monthly.idxmax().strftime('%Y-%m'))
            worst_period = str(monthly.idxmin().strftime('%Y-%m'))

        # --- MoM: last full month vs previous ---
        mom_pct = self._pct_change_between_periods(monthly, -1, -2)

        # --- WoW: last full week vs previous ---
        weekly = s.resample('W').mean().dropna()
        wow_pct = self._pct_change_between_periods(weekly, -1, -2)

        # --- YoY: last full year vs year before ---
        yearly = s.resample('YE').mean().dropna()
        yoy_pct = self._pct_change_between_periods(yearly, -1, -2)

        return {
            "mom_pct": mom_pct,
            "wow_pct": wow_pct,
            "yoy_pct": yoy_pct,
            "trend_slope": trend_slope,
            "trend_r2": trend_r2,
            "best_period": best_period,
            "worst_period": worst_period,
            "forecast_next": forecast_next
        }

    def _pct_change_between_periods(self, resampled: pd.Series, current_idx: int, prev_idx: int):
        """Returns % change between two indexed periods, or None if unavailable."""
        try:
            if len(resampled) < abs(min(current_idx, prev_idx)):
                return None
            current = float(resampled.iloc[current_idx])
            previous = float(resampled.iloc[prev_idx])
            if previous == 0:
                return None
            return round((current - previous) / abs(previous) * 100, 2)
        except Exception:
            return None

    def _detect_granularity(self, date_series: pd.Series) -> str:
        """Infers time granularity from the median gap between consecutive dates."""
        try:
            diffs = date_series.diff().dropna()
            median_days = diffs.median().days
            if median_days <= 1:
                return 'daily'
            elif median_days <= 8:
                return 'weekly'
            elif median_days <= 35:
                return 'monthly'
            elif median_days <= 100:
                return 'quarterly'
            else:
                return 'yearly'
        except Exception:
            return 'unknown'
