"""
test_upgrade.py

Standalone test suite for DataLens AI v2.0 upgrade components.
Run from backend/: python test_upgrade.py

Tests:
  1. DateIntelligence.analyze() — basic output structure
  2. FilterTrigger — 10% reduction on large dataset -> True
  3. FilterTrigger — 5% reduction on large dataset -> False
  4. DataSerializer — output structure and record count
  5. InsightEngine — mock NIMClient returns l3_insights
  6. FilterTrigger — 20% reduction on small dataset -> True
"""
import sys
import os
import io
import json
import tempfile
import traceback

# Ensure backend/ is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []


def run_test(name, fn):
    try:
        fn()
        print(f"  [{PASS}] {name}")
        results.append(True)
    except Exception as e:
        print(f"  [{FAIL}] {name}")
        print(f"         {type(e).__name__}: {e}")
        traceback.print_exc()
        results.append(False)


# ────────────────────────────────────────────────────────────────────── #
#  Synthetic dataset                                                      #
# ────────────────────────────────────────────────────────────────────── #

def make_synthetic_df(rows=200):
    rng = np.random.default_rng(42)
    dates = pd.date_range("2023-01-01", periods=rows, freq="D")
    df = pd.DataFrame({
        "date":    dates,
        "region":  rng.choice(["North", "South", "East", "West"], rows),
        "product": rng.choice(["Widget", "Gadget", "Doohickey"], rows),
        "revenue": rng.normal(50000, 12000, rows).round(2),
        "units":   rng.integers(100, 1000, rows).astype(float),
        "cost":    rng.normal(30000, 8000, rows).round(2),
    })
    return df


def make_mock_profile(df):
    """Build a minimal DataProfile-like namespace for testing."""
    from types import SimpleNamespace
    return SimpleNamespace(
        df=df,
        rows=len(df),
        cols=len(df.columns),
        columns=list(df.columns),
        dtypes={c: str(df[c].dtype) for c in df.columns},
        nulls={c: int(df[c].isna().sum()) for c in df.columns},
        null_pct={c: round(df[c].isna().sum() / len(df) * 100, 2) for c in df.columns},
        duplicates=int(df.duplicated().sum()),
        numeric_summary={
            "revenue": {"mean": round(df["revenue"].mean(), 2), "std": round(df["revenue"].std(), 2),
                        "min": round(df["revenue"].min(), 2), "max": round(df["revenue"].max(), 2)},
            "units":   {"mean": round(df["units"].mean(), 2),   "std": round(df["units"].std(), 2),
                        "min": round(df["units"].min(), 2),     "max": round(df["units"].max(), 2)},
            "cost":    {"mean": round(df["cost"].mean(), 2),    "std": round(df["cost"].std(), 2),
                        "min": round(df["cost"].min(), 2),      "max": round(df["cost"].max(), 2)},
        },
        sample=[],
        text_content="",
        column_types={
            "date":    "datetime",
            "region":  "categorical",
            "product": "categorical",
            "revenue": "numeric",
            "units":   "numeric",
            "cost":    "numeric",
        },
        has_datetime=True,
        has_numeric=True,
        kpi_columns=["revenue", "units"],
        source_type="csv",
        file_name="test_sales.csv",
        processing_time=0.1,
        warnings=[],
    )


# ────────────────────────────────────────────────────────────────────── #
#  Mock NIMClient                                                          #
# ────────────────────────────────────────────────────────────────────── #

class MockNIMClient:
    """Returns canned JSON responses for each InsightEngine prompt level."""

    def chat(self, model_name, user_prompt, system_prompt="", max_tokens=2048, temperature=0.3):
        # Detect which level by looking at the prompt
        if "factual observations" in user_prompt:
            # L1
            return json.dumps([
                "Revenue mean is $50,000 with moderate variance.",
                "Units sold range from 100 to 1000 per day.",
                "Cost tracks closely with revenue (positive correlation).",
                "No significant missing data detected.",
                "Sales peak in Q3 based on monthly aggregation."
            ])
        elif "ROOT CAUSE" in user_prompt.upper() or "root cause" in user_prompt:
            # L2
            return json.dumps([
                {"observation": "Revenue mean is $50,000", "root_cause": "Stable market demand"},
                {"observation": "Units range 100-1000", "root_cause": "Seasonal demand variation"},
                {"observation": "Cost tracks revenue", "root_cause": "Variable cost model"},
                {"observation": "No missing data", "root_cause": "Complete data pipeline"},
                {"observation": "Q3 sales peak", "root_cause": "Summer promotional campaigns"},
            ])
        else:
            # L3
            return json.dumps([
                {"title": "Optimize Q3 Campaign Spend", "insight": "Q3 shows consistent revenue peaks driven by promotions.", "action": "Increase Q3 marketing budget by 15% to capitalize on peak demand.", "urgency": "high", "metric_impact": "Revenue +12%"},
                {"title": "Review Variable Cost Structure", "insight": "Cost scales proportionally with revenue, limiting margin expansion.", "action": "Negotiate fixed-cost contracts with top 3 suppliers.", "urgency": "medium", "metric_impact": "Margin +5%"},
                {"title": "Expand East Region Coverage", "insight": "East region shows highest unit velocity relative to cost.", "action": "Allocate additional headcount to East region sales team.", "urgency": "low", "metric_impact": "Units +8%"},
            ])

    def _strip_thinking(self, text):
        import re
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return cleaned.strip()


# ────────────────────────────────────────────────────────────────────── #
#  Tests                                                                   #
# ────────────────────────────────────────────────────────────────────── #

def test_1_date_intelligence():
    from ai.date_intelligence import DateIntelligence
    df = make_synthetic_df()
    profile = make_mock_profile(df)
    intel = DateIntelligence()
    result = intel.analyze(df, "date", ["revenue", "units", "cost"], profile)

    assert "date_col" in result, "Missing 'date_col' key"
    assert result["date_col"] == "date"
    assert "metrics" in result, "Missing 'metrics' key"
    assert "revenue" in result["metrics"], "Missing 'revenue' in metrics"
    rev = result["metrics"]["revenue"]
    assert "mom_pct" in rev, "Missing 'mom_pct'"
    assert "trend_r2" in rev, "Missing 'trend_r2'"
    assert "best_period" in rev, "Missing 'best_period'"
    assert "granularity" in result, "Missing 'granularity'"
    assert "date_range" in result, "Missing 'date_range'"


def test_2_filter_trigger_large_10pct():
    from ai.filter_trigger import FilterTrigger
    trigger = FilterTrigger()
    # Large dataset (>50k rows): threshold is 10%, so 10% reduction should trigger
    result = trigger.should_regenerate(
        original_profile={"rows": 60000},
        filtered_stats={"rows": 54000}  # 10% reduction
    )
    assert result is True, f"Expected True for 10% reduction on 60000 rows, got {result}"


def test_3_filter_trigger_large_5pct():
    from ai.filter_trigger import FilterTrigger
    trigger = FilterTrigger()
    result = trigger.should_regenerate(
        original_profile={"rows": 1000},
        filtered_stats={"rows": 950}  # 5% reduction
    )
    assert result is False, f"Expected False for 5% reduction on 1000 rows, got {result}"


def test_4_data_serializer():
    from utils.data_serializer import DataSerializer
    df = make_synthetic_df()
    profile = make_mock_profile(df)
    serializer = DataSerializer()
    result = serializer.serialize_for_frontend(df, profile)

    assert "records" in result, "Missing 'records'"
    assert "column_stats" in result, "Missing 'column_stats'"
    assert "top_correlations" in result, "Missing 'top_correlations'"
    assert "kpi_series" in result, "Missing 'kpi_series'"
    assert len(result["records"]) <= 30000, f"Too many records: {len(result['records'])}"
    assert len(result["records"]) == 200, f"Expected 200 records, got {len(result['records'])}"
    assert "revenue" in result["column_stats"], "Missing 'revenue' in column_stats"
    assert result["sample_size"] == 200


def test_5_insight_engine_mock():
    from ai.insight_engine import InsightEngine
    df = make_synthetic_df()
    profile = make_mock_profile(df)
    mock_client = MockNIMClient()
    engine = InsightEngine()
    result = engine.generate_insights(profile, [], mock_client)

    assert "l3_insights" in result, "Missing 'l3_insights'"
    assert "l1_facts" in result, "Missing 'l1_facts'"
    assert "l2_causes" in result, "Missing 'l2_causes'"
    assert len(result["l3_insights"]) == 3, f"Expected 3 l3_insights, got {len(result['l3_insights'])}"
    for insight in result["l3_insights"]:
        assert "title" in insight
        assert "insight" in insight
        assert "action" in insight
        assert insight["urgency"] in ("high", "medium", "low"), f"Invalid urgency: {insight['urgency']}"
        assert "metric_impact" in insight


def test_6_filter_trigger_small_20pct():
    from ai.filter_trigger import FilterTrigger
    trigger = FilterTrigger()
    result = trigger.should_regenerate(
        original_profile={"rows": 100},
        filtered_stats={"rows": 80}  # 20% reduction
    )
    assert result is True, f"Expected True for 20% reduction on 100 rows, got {result}"


# ────────────────────────────────────────────────────────────────────── #
#  Runner                                                                  #
# ────────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  DataLens AI v2.0 — Upgrade Test Suite")
    print("=" * 55)

    run_test("Test 1: DateIntelligence.analyze() structure",        test_1_date_intelligence)
    run_test("Test 2: FilterTrigger — 10% reduction -> True",        test_2_filter_trigger_large_10pct)
    run_test("Test 3: FilterTrigger — 5% reduction -> False",        test_3_filter_trigger_large_5pct)
    run_test("Test 4: DataSerializer — records + stats structure",   test_4_data_serializer)
    run_test("Test 5: InsightEngine — mock client -> 3 l3_insights",  test_5_insight_engine_mock)
    run_test("Test 6: FilterTrigger — 20% on small dataset -> True", test_6_filter_trigger_small_20pct)

    passed = sum(results)
    total = len(results)
    print("=" * 55)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 55 + "\n")

    sys.exit(0 if all(results) else 1)
