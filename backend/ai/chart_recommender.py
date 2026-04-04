"""
chart_recommender.py

Recommends optimal charts using pure Python heuristic logic.
Assesses cardinality, datatype and numeric correlation.
"""
from dataclasses import dataclass
from typing import List, Optional, Any
import pandas as pd
import numpy as np
from parsers.base_parser import DataProfile

@dataclass
class ChartConfig:
    chart_type: str
    title: str
    x_col: Optional[str]
    y_col: Optional[str]
    color_col: Optional[str]
    aggregation: Optional[str]
    priority: int
    insight_hint: str
    data: List[dict]

class ChartRecommender:
    """Applies 7 heuristic rules to suggest best visualizations."""

    def recommend(self, profile: DataProfile) -> List[ChartConfig]:
        charts: List[ChartConfig] = []
        df = profile.df
        
        kpis = profile.kpi_columns[:4]
        date_cols = [c for c, t in profile.column_types.items() if t == "datetime"]
        # Exclude bool columns from numeric ops to avoid numpy boolean subtract errors
        num_cols = [c for c, t in profile.column_types.items()
                    if t == "numeric" and not pd.api.types.is_bool_dtype(df[c].dtype)]
        cat_cols = [c for c, t in profile.column_types.items() if t in ("categorical", "text")]
        
        cat_cardinality = {c: df[c].nunique() for c in cat_cols}
        best_cats = sorted([c for c, count in cat_cardinality.items() if 2 <= count <= 15], key=lambda c: cat_cardinality[c])
        best_cat = best_cats[0] if best_cats else None

        # RULE 1: KPI Cards
        for k in kpis:
            agg = "mean" if any(x in k.lower() for x in ["rate", "score", "margin"]) else "sum"
            val = df[k].mean() if agg == "mean" else df[k].sum()
            val = float(val) if hasattr(val, 'item') else val
            charts.append(ChartConfig(
                chart_type="kpi_card", title=f"Total {k}" if agg=="sum" else f"Average {k}",
                x_col=None, y_col=k, color_col=None, aggregation=agg,
                priority=1, insight_hint=f"Total {k}" if agg=="sum" else f"Average {k}",
                data=[{"x": "KPI", "y": val}]
            ))

        # RULE 2: Time series line chart
        if date_cols and kpis:
            dt_col = date_cols[0]
            for k in kpis[:2]:
                try:
                    sub_df = df[[dt_col, k]].dropna().copy()
                    sub_df[dt_col] = pd.to_datetime(sub_df[dt_col], format='mixed', dayfirst=False, errors='coerce')
                    sub_df = sub_df.dropna(subset=[dt_col])  # drop rows where date failed to parse
                    if sub_df.empty:
                        continue
                    date_span = (sub_df[dt_col].max() - sub_df[dt_col].min()).days
                    if date_span > 90:
                        sub_df = sub_df.set_index(dt_col).sort_index()  # must be monotonic for resample
                        try:
                            grouped = sub_df.resample('ME').sum().reset_index()
                        except ValueError:
                            grouped = sub_df.resample('M').sum().reset_index()
                    else:
                        grouped = sub_df.groupby(dt_col, as_index=False)[k].sum()

                    # Show all resampled points (already aggregated), cap at 200
                    limit = grouped.head(200).copy()
                    limit[dt_col] = limit[dt_col].astype(str)
                    data_records = [{"x": str(row[dt_col]), "y": float(row[k])} for _, row in limit.iterrows()]
                    if data_records:
                        charts.append(ChartConfig(
                            chart_type="line", title=f"{k} Over Time",
                            x_col=dt_col, y_col=k, color_col=None, aggregation="sum",
                            priority=2, insight_hint=f"Track {k} trends over time",
                            data=data_records
                        ))
                except Exception:
                    pass  # Skip this time series chart on any date-related error
                
        # RULE 3: Bar chart — sort by value descending, show top 20 categories
        if best_cat and kpis:
            k = kpis[0]
            grouped = df.groupby(best_cat, as_index=False)[k].sum().dropna(subset=[k])
            grouped = grouped.sort_values(k, ascending=False).head(20)
            data_records = [{"x": str(row[best_cat]), "y": float(row[k])} for _, row in grouped.iterrows()]
            
            charts.append(ChartConfig(
                chart_type="bar", title=f"{k} by {best_cat}",
                x_col=best_cat, y_col=k, color_col=None, aggregation="sum",
                priority=3, insight_hint=f"Compare {k} across {best_cat} categories",
                data=data_records
            ))

        # RULE 4: Scatter plot
        if len(num_cols) >= 2:
            sub = df[num_cols].dropna()
            # Remove zero-variance columns — corr() returns NaN for them, crashing idxmax()
            valid_cols = [c for c in sub.columns if sub[c].std() > 0]
            if len(valid_cols) >= 2:
                sub = sub[valid_cols]
            if not sub.empty and len(sub.columns) >= 2:
                corr = sub.corr()
                corr_vals = corr.abs().unstack()
                corr_vals = corr_vals[(corr_vals < 1.0) & corr_vals.notna()]
                if not corr_vals.empty:
                    best_pair = corr_vals.idxmax()
                    val = corr.loc[best_pair[0], best_pair[1]]
                    if abs(val) > 0.3:
                        c1, c2 = best_pair
                        # Random sample for scatter to avoid first-row bias
                        sample = sub.sample(min(200, len(sub)), random_state=42)
                        data_records = [{"x": float(row[c1]), "y": float(row[c2])} for _, row in sample.iterrows()]
                        charts.append(ChartConfig(
                            chart_type="scatter", title=f"{c1} vs {c2}",
                            x_col=c1, y_col=c2, color_col=None, aggregation=None,
                            priority=4, insight_hint=f"Relationship between {c1} and {c2}",
                            data=data_records
                        ))

        # RULE 5: Pie chart
        pie_cat = None
        for c, count in cat_cardinality.items():
            if 3 <= count <= 8 and (not best_cat or c != best_cat):
                pie_cat = c
                break
        
        if pie_cat:
            counts = df[pie_cat].value_counts().reset_index()
            counts.columns = [pie_cat, 'count']
            data_records = [{"x": str(row[pie_cat]), "y": int(row['count'])} for _, row in counts.iterrows()]
            charts.append(ChartConfig(
                chart_type="pie", title=f"Distribution of {pie_cat}",
                x_col=pie_cat, y_col="count", color_col=None, aggregation="count",
                priority=5, insight_hint=f"Breakdown of {pie_cat} categories",
                data=data_records
            ))

        # RULE 6: Histogram
        if num_cols:
            variances = df[num_cols].var().dropna()
            if not variances.empty:
                var_col = variances.idxmax()
            else:
                var_col = num_cols[0]
            sub = df[var_col].dropna()
            if not sub.empty and sub.std() > 0:
                counts, bins = np.histogram(sub, bins=20)
                data_records = [{"x": float((bins[i]+bins[i+1])/2), "y": int(c)} for i, c in enumerate(counts)]
                charts.append(ChartConfig(
                    chart_type="histogram", title=f"Distribution of {var_col}",
                    x_col=var_col, y_col="count", color_col=None, aggregation="count",
                    priority=6, insight_hint=f"How {var_col} values are distributed",
                    data=data_records
                ))
                
        # RULE 7: Correlation heatmap
        if len(num_cols) >= 4:
            sub = df[num_cols].dropna()
            # Only keep columns with variance > 0 for meaningful correlation
            valid_cols = [c for c in sub.columns if sub[c].std() > 0]
            if len(valid_cols) >= 4:
                sub = sub[valid_cols]
            if not sub.empty and len(sub.columns) >= 2:
                corr = sub.corr()
                data_records = []
                for idx in corr.index:
                    for col in corr.columns:
                        data_records.append({"x": idx, "y": col, "value": round(float(corr.loc[idx, col]), 2)})
                charts.append(ChartConfig(
                    chart_type="heatmap", title="Correlation Matrix",
                    x_col=None, y_col=None, color_col=None, aggregation=None,
                    priority=7, insight_hint="Which metrics move together",
                    data=data_records
                ))

        charts.sort(key=lambda c: c.priority)
        return charts[:6]
