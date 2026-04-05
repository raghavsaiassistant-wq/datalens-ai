"""
smart_viz_selector.py

Generates ONLY meaningful visualizations based on column ROLES and analytical findings.
Never charts identifier columns. Every chart answers a specific business question.
Pure pandas aggregations — all data is pre-computed for Plotly.
"""
import json
import logging
import math
from typing import List, Optional
import pandas as pd
import numpy as np
from ai.chart_recommender import ChartConfig
from ai.dataset_classifier import DatasetMeta
from ai.analytical_engine import Finding

logger = logging.getLogger("SmartVizSelector")

MAX_CHARTS = 6


def _safe(v):
    if isinstance(v, (np.integer,)):  return int(v)
    if isinstance(v, (np.floating,)): return None if (math.isnan(float(v)) or math.isinf(float(v))) else float(v)
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)): return None
    return v


class SmartVizSelector:
    """Selects and pre-computes chart data based on analytical findings and dataset type."""

    def select_charts(
        self, df: pd.DataFrame, meta: DatasetMeta, findings: list
    ) -> List[ChartConfig]:
        charts: List[ChartConfig] = []

        dispatch = {
            "experiment":    self._charts_experiment,
            "timeseries":    self._charts_timeseries,
            "transactional": self._charts_transactional,
            "customer":      self._charts_transactional,  # same pattern
            "financial":     self._charts_timeseries,     # same pattern
            "general":       self._charts_general,
        }
        fn = dispatch.get(meta.dataset_type, self._charts_general)

        try:
            charts = fn(df, meta, findings)
        except Exception as e:
            logger.error(f"SmartVizSelector failed: {e}. Falling back to general.")
            charts = self._charts_general(df, meta, findings)

        # KPI cards always first, then content charts
        kpi   = [c for c in charts if c.chart_type == "kpi_card"]
        other = [c for c in charts if c.chart_type != "kpi_card"]
        return (kpi + other)[:MAX_CHARTS]

    # ══════════════════════════════════════════════════════════════════════
    # EXPERIMENT CHARTS
    # ══════════════════════════════════════════════════════════════════════

    def _charts_experiment(self, df, meta, findings):
        charts = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension
        pt = meta.primary_time
        identifiers = set(meta.identifiers)

        if not pm or not pd_col:
            return self._charts_general(df, meta, findings)

        # Locate key findings
        winner_finding  = next((f for f in findings if f.insight_type == "winner"), None)
        segment_finding = next((f for f in findings if f.insight_type == "segment"), None)
        spread_finding  = next((f for f in findings if f.insight_type == "gap" and "std_by_variant" in f.data), None)
        pattern_finding = next((f for f in findings if f.insight_type == "pattern"), None)
        trend_finding   = next((f for f in findings if f.insight_type == "trend"), None)

        # ── KPI Cards ──────────────────────────────────────────────────────
        for m_col in meta.measures[:3]:
            if m_col not in df.columns or m_col in identifiers:
                continue
            mean_val = _safe(float(df[m_col].mean()))
            total_val = _safe(float(df[m_col].sum()))
            question = f"What is the average {m_col}?"
            charts.append(ChartConfig(
                chart_type="kpi_card",
                title=f"Avg {m_col}",
                x_col=None, y_col=m_col, color_col=None,
                aggregation="mean", priority=1,
                insight_hint=json.dumps({"business_question": question, "annotation_text": f"${mean_val:.1f}K mean", "chart_subtype": "kpi"}),
                data=[{"x": "KPI", "y": mean_val, "secondary": total_val, "label": f"${mean_val:.1f}K avg"}]
            ))

        # ── Chart B: Main promotion bar (sorted desc) ──────────────────────
        if pd_col in df.columns and pd_col not in identifiers:
            group_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False)
            winner_val = float(group_means.iloc[0])
            bar_data = [
                {
                    "x": str(k),
                    "y": _safe(float(v)),
                    "pct_diff": _safe(round((float(v) - winner_val) / abs(winner_val) * 100, 1)) if winner_val != 0 else 0
                }
                for k, v in group_means.items()
            ]
            hint_text = winner_finding.answer if winner_finding else f"Mean {pm} by {pd_col}"
            charts.append(ChartConfig(
                chart_type="bar",
                title=f"Mean {pm} by {pd_col}",
                x_col=pd_col, y_col=pm, color_col=None,
                aggregation="mean", priority=2,
                insight_hint=json.dumps({
                    "business_question": f"Which {pd_col} drives highest {pm}?",
                    "annotation_text": hint_text[:200],
                    "chart_subtype": "sorted_bar",
                    "color_by": pd_col
                }),
                data=bar_data
            ))

        # ── Chart C: Grouped bar (segment × variant) ───────────────────────
        seg_dims = [c for c in meta.dimensions if c != pd_col and c in df.columns and c not in identifiers]
        if seg_dims and segment_finding and not segment_finding.data.get("winner_is_consistent", True):
            other_dim = seg_dims[0]
            try:
                cross = (
                    df[[other_dim, pd_col, pm]].dropna()
                    .groupby([other_dim, pd_col])[pm]
                    .mean()
                    .reset_index()
                )
                # Pivot to grouped_bar format: [{category, Promo1: val, Promo2: val, ...}]
                pivot = cross.pivot(index=other_dim, columns=pd_col, values=pm)
                gb_data = []
                for seg_val in pivot.index:
                    row = {"category": str(seg_val)}
                    for promo_val in pivot.columns:
                        row[str(promo_val)] = _safe(float(pivot.loc[seg_val, promo_val]))
                    gb_data.append(row)

                charts.append(ChartConfig(
                    chart_type="grouped_bar",
                    title=f"{pm} by {other_dim} and {pd_col}",
                    x_col=other_dim, y_col=pm, color_col=pd_col,
                    aggregation="mean", priority=3,
                    insight_hint=json.dumps({
                        "business_question": f"Does the best {pd_col} differ by {other_dim}?",
                        "annotation_text": segment_finding.answer[:200],
                        "chart_subtype": "grouped",
                        "color_by": pd_col
                    }),
                    data=gb_data
                ))
            except Exception as e:
                logger.debug(f"Grouped bar failed: {e}")

        # ── Chart D: Box plot — distribution per variant ───────────────────
        if pd_col in df.columns and pd_col not in identifiers:
            try:
                box_data = {}
                for variant in df[pd_col].dropna().unique():
                    vals = df[df[pd_col] == variant][pm].dropna().astype(float).tolist()
                    box_data[str(variant)] = [_safe(v) for v in vals[:500]]  # cap for perf

                hint_text = spread_finding.answer if spread_finding else f"Distribution of {pm} per {pd_col}"
                charts.append(ChartConfig(
                    chart_type="box_plot",
                    title=f"Distribution of {pm} per {pd_col}",
                    x_col=pd_col, y_col=pm, color_col=None,
                    aggregation=None, priority=4,
                    insight_hint=json.dumps({
                        "business_question": f"How consistent is performance within each {pd_col}?",
                        "annotation_text": hint_text[:200],
                        "chart_subtype": "box",
                        "color_by": pd_col
                    }),
                    data=[{"group": k, "values": v} for k, v in box_data.items()]
                ))
            except Exception as e:
                logger.debug(f"Box plot failed: {e}")

        # ── Chart E: Multi-line trend ──────────────────────────────────────
        if pt and pt in df.columns and pt not in identifiers:
            try:
                trend_agg = (
                    df[[pt, pd_col, pm]].dropna()
                    .groupby([pt, pd_col])[pm]
                    .mean()
                    .reset_index()
                    .sort_values(pt)
                )
                line_data = [
                    {"x": str(row[pt]), "y": _safe(float(row[pm])), "group": str(row[pd_col])}
                    for _, row in trend_agg.iterrows()
                ]
                hint_text = trend_finding.answer if trend_finding else f"Weekly {pm} by {pd_col}"
                charts.append(ChartConfig(
                    chart_type="line",
                    title=f"Weekly {pm} by {pd_col}",
                    x_col=pt, y_col=pm, color_col=pd_col,
                    aggregation="mean", priority=5,
                    insight_hint=json.dumps({
                        "business_question": f"Is {pd_col} performance consistent over {pt}?",
                        "annotation_text": hint_text[:200],
                        "chart_subtype": "multi_line",
                        "color_by": pd_col
                    }),
                    data=line_data
                ))
            except Exception as e:
                logger.debug(f"Multi-line failed: {e}")

        # ── Chart F: Segment factor bar ────────────────────────────────────
        if meta.segments and pattern_finding:
            seg_col = meta.segments[0]
            if seg_col in df.columns and seg_col not in identifiers:
                try:
                    # Bucket into quantiles
                    df_tmp = df.copy()
                    try:
                        df_tmp["_bucket"] = pd.qcut(df_tmp[seg_col], q=4, duplicates="drop").astype(str)
                    except Exception:
                        df_tmp["_bucket"] = pd.cut(df_tmp[seg_col], bins=4, include_lowest=True).astype(str)

                    bucket_means = df_tmp.groupby("_bucket")[pm].mean().sort_index()
                    seg_data = [
                        {"x": _safe(float(row[pm])), "y": str(row["_bucket"])}
                        for _, row in df_tmp.groupby("_bucket")[pm].mean().reset_index().iterrows()
                    ]
                    charts.append(ChartConfig(
                        chart_type="bar",
                        title=f"Mean {pm} by {seg_col} Group",
                        x_col="_bucket", y_col=pm, color_col=None,
                        aggregation="mean", priority=6,
                        insight_hint=json.dumps({
                            "business_question": f"Does {seg_col} predict {pm}?",
                            "annotation_text": pattern_finding.answer[:200],
                            "chart_subtype": "horizontal",
                            "color_by": None
                        }),
                        data=seg_data
                    ))
                except Exception as e:
                    logger.debug(f"Segment bar failed: {e}")

        return charts

    # ══════════════════════════════════════════════════════════════════════
    # TIMESERIES CHARTS
    # ══════════════════════════════════════════════════════════════════════

    def _charts_timeseries(self, df, meta, findings):
        charts = []
        pm = meta.primary_measure
        pt = meta.primary_time
        pd_col = meta.primary_dimension
        identifiers = set(meta.identifiers)

        # KPI cards
        for m_col in meta.measures[:2]:
            if m_col not in df.columns or m_col in identifiers:
                continue
            mean_val = _safe(float(df[m_col].mean()))
            charts.append(ChartConfig(
                chart_type="kpi_card", title=f"Avg {m_col}",
                x_col=None, y_col=m_col, color_col=None,
                aggregation="mean", priority=1,
                insight_hint=json.dumps({"business_question": f"Average {m_col}", "chart_subtype": "kpi"}),
                data=[{"x": "KPI", "y": mean_val}]
            ))

        if pm and pt and pm in df.columns and pt in df.columns and pt not in identifiers:
            # Line chart
            grouped = df[[pt, pm]].dropna().groupby(pt)[pm].mean().sort_index()
            line_data = [{"x": str(k), "y": _safe(float(v))} for k, v in grouped.items()]
            charts.append(ChartConfig(
                chart_type="line", title=f"{pm} Over Time",
                x_col=pt, y_col=pm, color_col=None,
                aggregation="mean", priority=2,
                insight_hint=json.dumps({"business_question": f"How does {pm} trend over time?", "chart_subtype": "line"}),
                data=line_data
            ))

            # Bar chart: top vs bottom periods
            bar_data = [{"x": str(k), "y": _safe(float(v))} for k, v in grouped.sort_values(ascending=False).items()]
            charts.append(ChartConfig(
                chart_type="bar", title=f"{pm} by Period (ranked)",
                x_col=pt, y_col=pm, color_col=None,
                aggregation="mean", priority=3,
                insight_hint=json.dumps({"business_question": "Which periods performed best?", "chart_subtype": "sorted_bar"}),
                data=bar_data
            ))

        if pm and pd_col and pd_col in df.columns and pd_col not in identifiers and pt and pt in df.columns:
            # Multi-line by dimension
            try:
                trend_agg = (
                    df[[pt, pd_col, pm]].dropna()
                    .groupby([pt, pd_col])[pm].mean()
                    .reset_index().sort_values(pt)
                )
                line_data2 = [{"x": str(r[pt]), "y": _safe(float(r[pm])), "group": str(r[pd_col])} for _, r in trend_agg.iterrows()]
                charts.append(ChartConfig(
                    chart_type="line", title=f"{pm} by {pd_col} Over Time",
                    x_col=pt, y_col=pm, color_col=pd_col,
                    aggregation="mean", priority=4,
                    insight_hint=json.dumps({"business_question": f"Which {pd_col} segment is growing?", "chart_subtype": "multi_line", "color_by": pd_col}),
                    data=line_data2
                ))
            except Exception:
                pass

        return charts

    # ══════════════════════════════════════════════════════════════════════
    # TRANSACTIONAL CHARTS
    # ══════════════════════════════════════════════════════════════════════

    def _charts_transactional(self, df, meta, findings):
        charts = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension
        identifiers = set(meta.identifiers)

        # KPI cards
        for m_col in meta.measures[:2]:
            if m_col not in df.columns or m_col in identifiers:
                continue
            total = _safe(float(df[m_col].sum()))
            mean_val = _safe(float(df[m_col].mean()))
            charts.append(ChartConfig(
                chart_type="kpi_card", title=f"Total {m_col}",
                x_col=None, y_col=m_col, color_col=None,
                aggregation="sum", priority=1,
                insight_hint=json.dumps({"business_question": f"Total {m_col}", "chart_subtype": "kpi"}),
                data=[{"x": "KPI", "y": total}]
            ))

        if pm and pd_col and pm in df.columns and pd_col in df.columns and pd_col not in identifiers:
            dim_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False).head(15)
            bar_data = [{"x": str(k), "y": _safe(float(v))} for k, v in dim_means.items()]
            charts.append(ChartConfig(
                chart_type="bar", title=f"Mean {pm} by {pd_col}",
                x_col=pd_col, y_col=pm, color_col=None,
                aggregation="mean", priority=2,
                insight_hint=json.dumps({"business_question": f"Which {pd_col} has highest {pm}?", "chart_subtype": "sorted_bar"}),
                data=bar_data
            ))

            # Box plot
            try:
                box_data = {}
                for cat in df[pd_col].dropna().unique()[:10]:
                    vals = df[df[pd_col] == cat][pm].dropna().astype(float).tolist()
                    box_data[str(cat)] = [_safe(v) for v in vals[:300]]
                charts.append(ChartConfig(
                    chart_type="box_plot", title=f"{pm} Distribution by {pd_col}",
                    x_col=pd_col, y_col=pm, color_col=None,
                    aggregation=None, priority=3,
                    insight_hint=json.dumps({"business_question": f"How variable is {pm} within {pd_col}?", "chart_subtype": "box"}),
                    data=[{"group": k, "values": v} for k, v in box_data.items()]
                ))
            except Exception:
                pass

        return charts

    # ══════════════════════════════════════════════════════════════════════
    # GENERAL FALLBACK CHARTS
    # ══════════════════════════════════════════════════════════════════════

    def _charts_general(self, df, meta, findings):
        charts = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension
        identifiers = set(meta.identifiers)

        # KPI card for primary measure
        if pm and pm in df.columns and pm not in identifiers:
            mean_val = _safe(float(df[pm].mean()))
            charts.append(ChartConfig(
                chart_type="kpi_card", title=f"Avg {pm}",
                x_col=None, y_col=pm, color_col=None,
                aggregation="mean", priority=1,
                insight_hint=json.dumps({"business_question": f"Average {pm}", "chart_subtype": "kpi"}),
                data=[{"x": "KPI", "y": mean_val}]
            ))

        # Bar by dimension
        if pm and pd_col and pm in df.columns and pd_col in df.columns and pd_col not in identifiers:
            group_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False).head(20)
            bar_data = [{"x": str(k), "y": _safe(float(v))} for k, v in group_means.items()]
            charts.append(ChartConfig(
                chart_type="bar", title=f"{pm} by {pd_col}",
                x_col=pd_col, y_col=pm, color_col=None,
                aggregation="mean", priority=2,
                insight_hint=json.dumps({"business_question": f"Which {pd_col} has highest {pm}?", "chart_subtype": "sorted_bar"}),
                data=bar_data
            ))

        # Histogram
        if pm and pm in df.columns and pm not in identifiers:
            try:
                series = df[pm].dropna().astype(float)
                counts, bins = np.histogram(series, bins=20)
                hist_data = [{"x": _safe(float((bins[i]+bins[i+1])/2)), "y": int(c)} for i, c in enumerate(counts)]
                charts.append(ChartConfig(
                    chart_type="histogram", title=f"Distribution of {pm}",
                    x_col=pm, y_col="count", color_col=None,
                    aggregation="count", priority=3,
                    insight_hint=json.dumps({"business_question": f"How is {pm} distributed?", "chart_subtype": "histogram"}),
                    data=hist_data
                ))
            except Exception:
                pass

        return charts
