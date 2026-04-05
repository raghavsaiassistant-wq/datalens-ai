"""
analytical_engine.py

Computes ANSWERS to analytical questions — not raw stats.
Dispatches to dataset-type-specific analyzers.
Pure pandas + scipy. No NIM calls. Max 3 seconds.
"""
import logging
import math
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from ai.dataset_classifier import DatasetMeta

logger = logging.getLogger("AnalyticalEngine")


def _s(v):
    """Safely convert a numpy scalar to a plain Python scalar for JSON serialization."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _safe_dict(d: dict) -> dict:
    """Recursively make a dict JSON-safe."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[str(k)] = _safe_dict(v)
        elif isinstance(v, (list, tuple)):
            out[str(k)] = [_s(x) for x in v]
        else:
            out[str(k)] = _s(v)
    return out


@dataclass
class Finding:
    question: str
    answer: str
    insight_type: str       # winner|segment|trend|gap|pattern|outlier|correlation
    significance: str       # high|medium|low
    data: dict              # JSON-safe computed values
    chart_recommendation: str
    chart_config: dict


class AnalyticalEngine:
    """Dispatches to type-specific analyzers and returns list[Finding]."""

    def analyze(self, df: pd.DataFrame, meta: DatasetMeta, profile) -> list:
        try:
            dispatch = {
                "experiment":    self._analyze_experiment,
                "timeseries":    self._analyze_timeseries,
                "transactional": self._analyze_transactional,
                "customer":      self._analyze_customer,
                "financial":     self._analyze_financial,
                "general":       self._analyze_general,
            }
            fn = dispatch.get(meta.dataset_type, self._analyze_general)
            findings = fn(df, meta)
            # Sort high→medium→low
            order = {"high": 0, "medium": 1, "low": 2}
            findings.sort(key=lambda f: order.get(f.significance, 3))
            return findings
        except Exception as e:
            logger.error(f"AnalyticalEngine.analyze() failed: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # EXPERIMENT ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_experiment(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension
        pt = meta.primary_time

        if not pm or not pd_col or pm not in df.columns or pd_col not in df.columns:
            return self._analyze_general(df, meta)

        df_clean = df[[pd_col, pm]].dropna()
        group_means = df_clean.groupby(pd_col)[pm].mean().sort_values(ascending=False)
        if len(group_means) < 2:
            return self._analyze_general(df, meta)

        winner = str(group_means.index[0])
        loser  = str(group_means.index[-1])
        winner_val = float(group_means.iloc[0])
        loser_val  = float(group_means.iloc[-1])
        gap_pct    = round((winner_val - loser_val) / abs(loser_val) * 100, 1) if loser_val != 0 else 0.0
        sig = "high" if gap_pct > 10 else ("medium" if gap_pct >= 5 else "low")

        all_means_str = ", ".join(
            f"{str(idx)}=${float(v):.1f}K" for idx, v in group_means.items()
        )
        findings.append(Finding(
            question=f"Which {pd_col} drives highest {pm} overall?",
            answer=(
                f"{winner} generates ${winner_val:.1f}K mean {pm} — "
                f"{gap_pct:.1f}% higher than {loser} (${loser_val:.1f}K). "
                f"All values: {all_means_str}."
            ),
            insight_type="winner",
            significance=sig,
            data=_safe_dict({
                "winner": winner, "winner_val": winner_val,
                "loser": loser,   "loser_val": loser_val,
                "gap_pct": gap_pct,
                "group_means": {str(k): float(v) for k, v in group_means.items()},
            }),
            chart_recommendation="bar",
            chart_config={
                "type": "bar", "x": pd_col, "y": f"mean({pm})",
                "sort": "desc", "annotate_pct_diff": True
            }
        ))

        # Q2: Does winner change by segment?
        other_dims = [c for c in meta.dimensions if c != pd_col and c in df.columns]
        for other_dim in other_dims[:2]:
            try:
                cross = (
                    df[[other_dim, pd_col, pm]].dropna()
                    .groupby([other_dim, pd_col])[pm].mean()
                    .unstack(pd_col)
                )
                if cross.empty or cross.shape[1] < 2:
                    continue

                segment_winners = {}
                for seg in cross.index:
                    row = cross.loc[seg].dropna()
                    if not row.empty:
                        segment_winners[str(seg)] = str(row.idxmax())

                consistent = len(set(segment_winners.values())) == 1
                seg_desc = "; ".join(f"{seg}: {w}" for seg, w in segment_winners.items())

                if consistent:
                    answer = (
                        f"Yes — {winner} wins consistently across all {other_dim} segments. "
                        f"({seg_desc})"
                    )
                    fsig = "medium"
                else:
                    answer = (
                        f"No — the winning {pd_col} differs by {other_dim}. "
                        f"{seg_desc}. A segmented strategy outperforms a one-size-fits-all approach."
                    )
                    fsig = "high"

                findings.append(Finding(
                    question=f"Does the best {pd_col} differ by {other_dim}?",
                    answer=answer,
                    insight_type="segment",
                    significance=fsig,
                    data=_safe_dict({
                        "other_dim": other_dim,
                        "segment_winners": segment_winners,
                        "winner_is_consistent": consistent,
                        "cross_means": {
                            str(seg): {str(k): float(v) for k, v in cross.loc[seg].dropna().items()}
                            for seg in cross.index
                        }
                    }),
                    chart_recommendation="grouped_bar" if not consistent else "bar",
                    chart_config={
                        "type": "grouped_bar",
                        "x": other_dim, "y": f"mean({pm})", "group": pd_col,
                    }
                ))
            except Exception as e:
                logger.debug(f"Q2 failed for {other_dim}: {e}")

        # Q3: Time stability
        if pt and pt in df.columns:
            try:
                pivot = (
                    df[[pt, pd_col, pm]].dropna()
                    .groupby([pt, pd_col])[pm].mean()
                    .unstack(pd_col)
                )
                if not pivot.empty and pivot.shape[1] >= 2:
                    # For each period, find the winner
                    period_winners = {str(p): str(pivot.loc[p].dropna().idxmax()) for p in pivot.index if not pivot.loc[p].dropna().empty}
                    stable = len(set(period_winners.values())) == 1

                    weekly_means = {}
                    for v in pivot.columns:
                        weekly_means[str(v)] = [_s(x) for x in pivot[v].tolist()]

                    answer = (
                        f"{'Yes' if stable else 'No'} — {winner} "
                        f"{'maintains its lead consistently across all ' + str(len(pivot)) + ' periods' if stable else 'shows inconsistent performance across periods'}. "
                        f"Period winners: {'; '.join(f'{p}: {w}' for p,w in period_winners.items())}"
                    )
                    findings.append(Finding(
                        question=f"Is {pd_col} performance consistent over {pt}?",
                        answer=answer,
                        insight_type="trend",
                        significance="high" if not stable else "low",
                        data=_safe_dict({"stable": stable, "period_winners": period_winners, "weekly_means": weekly_means}),
                        chart_recommendation="line",
                        chart_config={"type": "multi_line", "x": pt, "y": f"mean({pm})", "group": pd_col}
                    ))
            except Exception as e:
                logger.debug(f"Q3 time stability failed: {e}")

        # Q4: Within-variant spread
        try:
            stds = df.groupby(pd_col)[pm].std()
            means = df.groupby(pd_col)[pm].mean()
            cv = stds / means.replace(0, np.nan)
            high_cv = cv[cv > 0.3]
            std_dict = {str(k): round(float(v), 2) for k, v in stds.items()}
            sig_q4 = "high" if len(high_cv) > 0 else "low"

            answer = (
                f"{'High variability within groups' if sig_q4 == 'high' else 'Consistent performance within groups'} — "
                f"std by {pd_col}: {', '.join(f'{k}={v}' for k, v in std_dict.items())}. "
                f"{'Location/unit factors dominate over ' + pd_col + ' choice.' if sig_q4 == 'high' else ''}"
            )
            findings.append(Finding(
                question=f"How consistent is performance within each {pd_col}?",
                answer=answer,
                insight_type="gap",
                significance=sig_q4,
                data=_safe_dict({"std_by_variant": std_dict}),
                chart_recommendation="box",
                chart_config={"type": "box_plot", "x": pd_col, "y": pm}
            ))
        except Exception as e:
            logger.debug(f"Q4 spread failed: {e}")

        # Q5: Unit performance gap (for identifier columns)
        for id_col in meta.identifiers[:1]:
            if id_col not in df.columns:
                continue
            try:
                unit_means = df.groupby(id_col)[pm].mean()
                n_units = len(unit_means)
                top_cutoff = int(n_units * 0.1) + 1
                top_mean   = float(unit_means.nlargest(top_cutoff).mean())
                bot_mean   = float(unit_means.nsmallest(top_cutoff).mean())
                gap_pct_u  = round((top_mean - bot_mean) / abs(bot_mean) * 100, 1) if bot_mean > 0 else 0.0

                findings.append(Finding(
                    question=f"How large is the performance gap between best and worst {id_col}s?",
                    answer=(
                        f"Top {id_col}s average ${top_mean:.1f}K vs bottom at ${bot_mean:.1f}K — "
                        f"a {gap_pct_u:.0f}% gap suggesting location/unit factors dominate outcomes."
                    ),
                    insight_type="gap",
                    significance="high" if gap_pct_u > 50 else "medium",
                    data=_safe_dict({
                        "top_mean": top_mean, "bottom_mean": bot_mean,
                        "gap_pct": gap_pct_u, "n_units": n_units,
                        "top_ids": [str(x) for x in unit_means.nlargest(top_cutoff).index.tolist()[:5]],
                    }),
                    chart_recommendation=None,  # NEVER chart identifiers
                    chart_config={}
                ))
            except Exception as e:
                logger.debug(f"Q5 unit gap failed: {e}")

        # Q6: Segment factor impact
        for seg_col in meta.segments[:2]:
            if seg_col not in df.columns:
                continue
            try:
                buckets, labels = self._bucket_segment(df[seg_col])
                df_tmp = df.copy()
                df_tmp["_bucket"] = buckets
                bucket_means = df_tmp.groupby("_bucket")[pm].mean().sort_index()

                if bucket_means.empty:
                    continue

                pattern = self._detect_pattern(bucket_means.values.tolist())
                bucket_dict = {str(k): round(float(v), 2) for k, v in bucket_means.items()}

                findings.append(Finding(
                    question=f"Does {seg_col} predict {pm} performance?",
                    answer=(
                        f"{pattern.replace('-', ' ').title()} pattern for {seg_col}: "
                        f"{'; '.join(f'{k}=${v:.1f}K' for k, v in bucket_dict.items())}."
                    ),
                    insight_type="pattern",
                    significance="high" if pattern != "flat" else "low",
                    data=_safe_dict({"pattern": pattern, "bucket_means": bucket_dict, "segment_col": seg_col}),
                    chart_recommendation="bar",
                    chart_config={"type": "bar_horizontal", "x": "_bucket", "y": f"mean({pm})"}
                ))
            except Exception as e:
                logger.debug(f"Q6 segment impact failed for {seg_col}: {e}")

        return findings

    # ══════════════════════════════════════════════════════════════════════
    # TIMESERIES ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_timeseries(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pt = meta.primary_time

        if not pm or not pt or pm not in df.columns or pt not in df.columns:
            return self._analyze_general(df, meta)

        try:
            ts = df[[pt, pm]].dropna().sort_values(pt)
            grouped = ts.groupby(pt)[pm].mean()

            if len(grouped) < 2:
                return self._analyze_general(df, meta)

            # Q1: Trend
            x = np.arange(len(grouped))
            slope, intercept, r_val, _, _ = scipy_stats.linregress(x, grouped.values.astype(float))
            total_change_pct = round((float(grouped.iloc[-1]) - float(grouped.iloc[0])) / abs(float(grouped.iloc[0])) * 100, 1)
            direction = "upward" if slope > 0 else "downward"
            r2 = round(float(r_val ** 2), 3)

            findings.append(Finding(
                question=f"What is the overall trend of {pm}?",
                answer=(
                    f"{pm} shows a {direction} trend over {len(grouped)} periods "
                    f"(R²={r2}). Total change: {'+' if total_change_pct > 0 else ''}{total_change_pct}%. "
                    f"Range: ${float(grouped.min()):.1f}K–${float(grouped.max()):.1f}K."
                ),
                insight_type="trend",
                significance="high" if abs(total_change_pct) > 15 else "medium",
                data=_safe_dict({"direction": direction, "slope": float(slope), "r2": r2, "total_change_pct": total_change_pct}),
                chart_recommendation="line",
                chart_config={"type": "line", "x": pt, "y": pm}
            ))

            # Q2: Best/worst period
            best_period = str(grouped.idxmax())
            worst_period = str(grouped.idxmin())
            findings.append(Finding(
                question=f"What was the best and worst period for {pm}?",
                answer=(
                    f"Best: {best_period} at ${float(grouped.max()):.1f}K. "
                    f"Worst: {worst_period} at ${float(grouped.min()):.1f}K. "
                    f"Gap: {round((float(grouped.max()) - float(grouped.min())) / abs(float(grouped.min())) * 100, 1)}%."
                ),
                insight_type="gap",
                significance="medium",
                data=_safe_dict({"best_period": best_period, "best_val": float(grouped.max()),
                                 "worst_period": worst_period, "worst_val": float(grouped.min())}),
                chart_recommendation="bar",
                chart_config={"type": "bar", "x": pt, "y": f"mean({pm})"}
            ))

            # Q3: Sudden spikes/drops
            pct_changes = grouped.pct_change().dropna()
            notable = pct_changes[pct_changes.abs() > 0.25]
            if not notable.empty:
                top_change = notable.abs().idxmax()
                change_val = round(float(notable.loc[top_change]) * 100, 1)
                findings.append(Finding(
                    question=f"Are there sudden spikes or drops in {pm}?",
                    answer=(
                        f"Notable change at {top_change}: {'+' if change_val > 0 else ''}{change_val}%. "
                        f"{len(notable)} period(s) show changes >25%."
                    ),
                    insight_type="outlier",
                    significance="high" if abs(change_val) > 50 else "medium",
                    data=_safe_dict({"notable_period": str(top_change), "change_pct": change_val,
                                     "n_notable": int(len(notable))}),
                    chart_recommendation="line",
                    chart_config={"type": "line", "x": pt, "y": pm, "annotate_spikes": True}
                ))

            # Q4: Most recent period change
            if len(grouped) >= 2:
                last_val = float(grouped.iloc[-1])
                prev_val = float(grouped.iloc[-2])
                last_period = str(grouped.index[-1])
                prev_period = str(grouped.index[-2])
                mom = round((last_val - prev_val) / abs(prev_val) * 100, 1) if prev_val != 0 else 0
                findings.append(Finding(
                    question=f"What is the most recent change in {pm}?",
                    answer=(
                        f"Most recent period ({last_period}): ${last_val:.1f}K vs "
                        f"previous ({prev_period}): ${prev_val:.1f}K. "
                        f"Change: {'+' if mom > 0 else ''}{mom}%."
                    ),
                    insight_type="trend",
                    significance="high" if abs(mom) > 10 else "low",
                    data=_safe_dict({"last_period": last_period, "last_val": last_val,
                                     "prev_val": prev_val, "mom_pct": mom}),
                    chart_recommendation="line",
                    chart_config={"type": "line", "x": pt, "y": pm}
                ))

        except Exception as e:
            logger.error(f"_analyze_timeseries failed: {e}")

        if not findings:
            return self._analyze_general(df, meta)
        return findings

    # ══════════════════════════════════════════════════════════════════════
    # TRANSACTIONAL ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_transactional(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension

        if not pm or pm not in df.columns:
            return self._analyze_general(df, meta)

        series = df[pm].dropna().astype(float)

        # Q1: Top 10% Pareto
        try:
            top_cutoff = max(1, int(len(series) * 0.1))
            top_mean = float(series.nlargest(top_cutoff).mean())
            total = float(series.sum())
            top_share = round(float(series.nlargest(top_cutoff).sum()) / total * 100, 1) if total > 0 else 0

            findings.append(Finding(
                question=f"Do top performers dominate {pm}?",
                answer=(
                    f"Top 10% of records account for {top_share}% of total {pm}. "
                    f"Average: ${top_mean:.1f} vs overall ${float(series.mean()):.1f}. "
                    f"{'High concentration risk.' if top_share > 50 else 'Reasonably distributed.'}"
                ),
                insight_type="gap",
                significance="high" if top_share > 50 else "medium",
                data=_safe_dict({"top_10pct_share": top_share, "top_mean": top_mean,
                                 "overall_mean": float(series.mean()), "total": total}),
                chart_recommendation="bar",
                chart_config={"type": "bar", "x": pd_col or "rank", "y": pm}
            ))
        except Exception:
            pass

        # Q2: Distribution shape
        try:
            skew = float(series.skew())
            findings.append(Finding(
                question=f"What is the distribution shape of {pm}?",
                answer=(
                    f"{pm} distribution is {'right-skewed (high outliers)' if skew > 1 else 'left-skewed' if skew < -1 else 'approximately symmetric'}. "
                    f"Mean: ${float(series.mean()):.1f}, Median: ${float(series.median()):.1f}, "
                    f"Range: ${float(series.min()):.1f}–${float(series.max()):.1f}."
                ),
                insight_type="pattern",
                significance="medium",
                data=_safe_dict({"skew": skew, "mean": float(series.mean()),
                                 "median": float(series.median())}),
                chart_recommendation="histogram",
                chart_config={"type": "histogram", "x": pm}
            ))
        except Exception:
            pass

        # Q3: Dimension impact
        if pd_col and pd_col in df.columns:
            try:
                dim_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False)
                best_dim = str(dim_means.index[0])
                best_val = float(dim_means.iloc[0])
                worst_val = float(dim_means.iloc[-1])
                gap = round((best_val - worst_val) / abs(worst_val) * 100, 1) if worst_val > 0 else 0

                findings.append(Finding(
                    question=f"Which {pd_col} drives highest average {pm}?",
                    answer=(
                        f"{best_dim} has the highest average {pm} at ${best_val:.1f} — "
                        f"{gap:.1f}% above the lowest performing group."
                    ),
                    insight_type="winner",
                    significance="high" if gap > 20 else "medium",
                    data=_safe_dict({"dim_means": {str(k): float(v) for k, v in dim_means.items()}}),
                    chart_recommendation="bar",
                    chart_config={"type": "bar", "x": pd_col, "y": f"mean({pm})", "sort": "desc"}
                ))
            except Exception:
                pass

        return findings if findings else self._analyze_general(df, meta)

    # ══════════════════════════════════════════════════════════════════════
    # CUSTOMER ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_customer(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension

        if not pm or pm not in df.columns:
            return self._analyze_general(df, meta)

        # Q1: Segment comparison
        if pd_col and pd_col in df.columns:
            try:
                seg_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False)
                best = str(seg_means.index[0])
                worst = str(seg_means.index[-1])
                gap = round((float(seg_means.iloc[0]) - float(seg_means.iloc[-1])) / abs(float(seg_means.iloc[-1])) * 100, 1)

                findings.append(Finding(
                    question=f"Which customer segment has the highest {pm}?",
                    answer=(
                        f"{best} segment leads with ${float(seg_means.iloc[0]):.1f} average {pm} — "
                        f"{gap:.1f}% above {worst}."
                    ),
                    insight_type="winner",
                    significance="high" if gap > 20 else "medium",
                    data=_safe_dict({"seg_means": {str(k): float(v) for k, v in seg_means.items()}}),
                    chart_recommendation="bar",
                    chart_config={"type": "bar", "x": pd_col, "y": f"mean({pm})"}
                ))
            except Exception:
                pass

        # Q2: Segment distribution
        if pd_col and pd_col in df.columns:
            try:
                counts = df[pd_col].value_counts()
                dom = str(counts.index[0])
                dom_pct = round(float(counts.iloc[0]) / len(df) * 100, 1)

                findings.append(Finding(
                    question=f"How are customers distributed across {pd_col} segments?",
                    answer=(
                        f"{dom} is the largest segment at {dom_pct}% of customers. "
                        f"Total segments: {len(counts)}."
                    ),
                    insight_type="pattern",
                    significance="medium",
                    data=_safe_dict({"counts": {str(k): int(v) for k, v in counts.items()}}),
                    chart_recommendation="pie",
                    chart_config={"type": "pie", "x": pd_col}
                ))
            except Exception:
                pass

        return findings if findings else self._analyze_general(df, meta)

    # ══════════════════════════════════════════════════════════════════════
    # FINANCIAL ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_financial(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pt = meta.primary_time

        if not pm or pm not in df.columns:
            return self._analyze_general(df, meta)

        series = df[pm].dropna().astype(float)
        total = float(series.sum())

        findings.append(Finding(
            question=f"What is the total and trend of {pm}?",
            answer=(
                f"Total {pm}: ${total:,.1f}. "
                f"Average per period: ${float(series.mean()):.1f}. "
                f"Range: ${float(series.min()):.1f}–${float(series.max()):.1f}."
            ),
            insight_type="trend",
            significance="high",
            data=_safe_dict({"total": total, "mean": float(series.mean())}),
            chart_recommendation="line" if pt else "bar",
            chart_config={"type": "line" if pt else "bar", "x": pt or meta.primary_dimension, "y": pm}
        ))

        # Profitability by dimension
        if meta.primary_dimension and meta.primary_dimension in df.columns:
            try:
                dim_totals = df.groupby(meta.primary_dimension)[pm].sum().sort_values(ascending=False)
                top_dim = str(dim_totals.index[0])
                top_share = round(float(dim_totals.iloc[0]) / total * 100, 1) if total > 0 else 0

                findings.append(Finding(
                    question=f"Which {meta.primary_dimension} contributes most to {pm}?",
                    answer=(
                        f"{top_dim} accounts for {top_share}% of total {pm} "
                        f"(${float(dim_totals.iloc[0]):,.1f})."
                    ),
                    insight_type="winner",
                    significance="high" if top_share > 40 else "medium",
                    data=_safe_dict({"dim_totals": {str(k): float(v) for k, v in dim_totals.items()}}),
                    chart_recommendation="bar",
                    chart_config={"type": "bar", "x": meta.primary_dimension, "y": f"sum({pm})"}
                ))
            except Exception:
                pass

        return findings if findings else self._analyze_general(df, meta)

    # ══════════════════════════════════════════════════════════════════════
    # GENERAL FALLBACK ANALYZER
    # ══════════════════════════════════════════════════════════════════════

    def _analyze_general(self, df: pd.DataFrame, meta: DatasetMeta) -> list:
        findings = []
        pm = meta.primary_measure
        pd_col = meta.primary_dimension

        if not pm or pm not in df.columns:
            # Last resort: pick any numeric column
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c].dtype)]
            if num_cols:
                pm = num_cols[0]
            else:
                return []

        series = df[pm].dropna().astype(float)

        # Q1: Distribution
        findings.append(Finding(
            question=f"What is the distribution of {pm}?",
            answer=(
                f"{pm}: average ${float(series.mean()):.2f}, "
                f"median ${float(series.median()):.2f}, "
                f"range ${float(series.min()):.2f}–${float(series.max()):.2f}. "
                f"Skew: {'right' if float(series.skew()) > 1 else 'left' if float(series.skew()) < -1 else 'symmetric'}."
            ),
            insight_type="pattern",
            significance="medium",
            data=_safe_dict({"mean": float(series.mean()), "median": float(series.median()),
                             "min": float(series.min()), "max": float(series.max())}),
            chart_recommendation="histogram",
            chart_config={"type": "histogram", "x": pm}
        ))

        # Q2: Dimension impact
        if pd_col and pd_col in df.columns:
            try:
                dim_means = df.groupby(pd_col)[pm].mean().sort_values(ascending=False)
                best = str(dim_means.index[0])
                gap = round((float(dim_means.iloc[0]) - float(dim_means.iloc[-1])) / abs(float(dim_means.iloc[-1])) * 100, 1) if float(dim_means.iloc[-1]) != 0 else 0

                findings.append(Finding(
                    question=f"Which {pd_col} has the highest {pm}?",
                    answer=(
                        f"{best} leads with ${float(dim_means.iloc[0]):.2f} average {pm} — "
                        f"{gap:.1f}% above the lowest group."
                    ),
                    insight_type="winner",
                    significance="high" if gap > 15 else "medium",
                    data=_safe_dict({"dim_means": {str(k): float(v) for k, v in dim_means.items()}}),
                    chart_recommendation="bar",
                    chart_config={"type": "bar", "x": pd_col, "y": f"mean({pm})", "sort": "desc"}
                ))
            except Exception:
                pass

        # Q3: Outliers
        try:
            z = scipy_stats.zscore(series, nan_policy='omit')
            outlier_count = int(np.sum(np.abs(z) > 2.5))
            if outlier_count > 0:
                findings.append(Finding(
                    question=f"Are there unusual values in {pm}?",
                    answer=(
                        f"{outlier_count} record(s) show unusually high or low {pm} values "
                        f"(beyond 2.5 standard deviations from average). "
                        f"These may warrant individual investigation."
                    ),
                    insight_type="outlier",
                    significance="high" if outlier_count > 3 else "medium",
                    data=_safe_dict({"outlier_count": outlier_count}),
                    chart_recommendation="scatter",
                    chart_config={"type": "scatter", "x": "index", "y": pm}
                ))
        except Exception:
            pass

        return findings

    # ══════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _bucket_segment(self, series: pd.Series):
        """Bucket a numeric series into 4 quantile groups with descriptive labels."""
        try:
            q = pd.qcut(series, q=4, duplicates="drop")
            labels = [str(interval) for interval in q.cat.categories]
            return q.astype(str), labels
        except Exception:
            # Fall back to simple quartile cut
            try:
                q = pd.cut(series, bins=4, include_lowest=True)
                return q.astype(str), [str(c) for c in q.cat.categories]
            except Exception:
                return series.astype(str), []

    def _detect_pattern(self, values: list) -> str:
        """Detect monotonic or U-shaped pattern in a list of values."""
        if len(values) < 3:
            return "flat"
        v = [x for x in values if x is not None]
        if not v:
            return "flat"

        diffs = [v[i+1] - v[i] for i in range(len(v)-1)]
        all_up   = all(d > 0 for d in diffs)
        all_down = all(d < 0 for d in diffs)

        if all_up:
            return "increasing"
        if all_down:
            return "decreasing"

        mid = len(v) // 2
        first_half_avg  = sum(v[:mid]) / max(1, mid)
        second_half_avg = sum(v[mid:]) / max(1, len(v) - mid)
        mid_val         = v[mid]

        if mid_val < first_half_avg and mid_val < second_half_avg:
            return "u-shaped"
        if mid_val > first_half_avg and mid_val > second_half_avg:
            return "inverted-u"

        return "flat"
