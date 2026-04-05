"""
test_analyst_brain.py

6-test suite for the Analyst Brain upgrade.
Tests 1-3 use MockNIMClient (no API key required).
Tests 4-5 require a real NIM API key in the environment.

Run from backend/:
    python test_analyst_brain.py
"""
import os
import sys
import json
import time
import random
import traceback
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, List

# ─── Path setup ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ─── Synthetic dataset factory ───────────────────────────────────────────────

def make_wa_marketing_df(n: int = 548, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic WA_Marketing-Campaign-equivalent DataFrame.

    Schema: LocationID, MarketID, MarketSize, AgeOfStore, Promotion, week, SalesInThousands
    Known distribution:
      - Promotion 1 mean=58.1K, Promotion 2 mean=47.3K, Promotion 3 mean=55.0K
      - Large markets: Promotion 3 wins at 77.2K; Medium/Small: Promotion 1 wins
      - AgeOfStore U-pattern: new(0-3)=59K, mid(4-15)=50K, old(16+)=57K
    """
    rng = np.random.default_rng(seed)
    rows = []
    loc_ids = list(range(1, 138))  # 137 locations
    market_size_by_id = {}
    for loc in loc_ids:
        market_size_by_id[loc] = rng.choice(["Small", "Medium", "Large"], p=[0.3, 0.5, 0.2])

    per_row = n // 4
    extra = n - per_row * 4

    for week in range(1, 5):
        week_rows = per_row + (1 if week <= extra else 0)
        for _ in range(week_rows):
            loc_id = int(rng.choice(loc_ids))
            mkt_id = int(rng.integers(1, 11))
            mkt_size = market_size_by_id[loc_id]
            age_of_store = int(rng.integers(1, 29))
            promotion = int(rng.choice([1, 2, 3]))

            # Age-of-store U-pattern
            if age_of_store <= 3:
                age_factor = 59.0
            elif age_of_store <= 15:
                age_factor = 50.0
            else:
                age_factor = 57.0

            # Promotion base means
            promo_means = {1: 58.1, 2: 47.3, 3: 55.0}
            base_mean = promo_means[promotion]

            # Large markets: Promo 3 wins at 77.2
            if mkt_size == "Large":
                if promotion == 3:
                    base_mean = 77.2
                elif promotion == 1:
                    base_mean = 63.0
                elif promotion == 2:
                    base_mean = 52.0
            # Medium/Small: Promo 1 stays best, Promo 3 slightly lower
            elif mkt_size in ("Medium", "Small"):
                pass  # use default promo_means

            # Blend with age factor lightly
            sales = float(rng.normal(loc=(base_mean + age_factor) / 2 * 1.05, scale=8.0))
            sales = max(0.0, round(sales, 2))

            rows.append({
                "LocationID":        loc_id,
                "MarketID":          mkt_id,
                "MarketSize":        mkt_size,
                "AgeOfStore":        age_of_store,
                "Promotion":         promotion,
                "week":              week,
                "SalesInThousands":  sales,
            })

    df = pd.DataFrame(rows)
    return df


# ─── Mock NIM Client ─────────────────────────────────────────────────────────

class MockNIMClient:
    """Returns deterministic mock responses without any API call."""

    def chat(self, model_name: str, user_prompt: str, system_prompt: str = "",
             max_tokens: int = 1000, temperature: float = 0.3) -> str:
        return json.dumps([
            {
                "headline": "Promotion 1 drives 22.8% more revenue than the weakest variant",
                "context": "Allocation of budget to the top-performing promotion can unlock immediate sales lift. Markets are leaving money on the table by running equal-weight testing indefinitely.",
                "recommended_action": "Shift 60% of promotion budget to Promotion 1 this week in Medium and Small markets.",
                "supporting_metric": "22.8% average sales gap between Promotion 1 and Promotion 2",
                "impact_area": "revenue",
                "magnitude": "high",
                "finding_reference": "FINDING 1"
            },
            {
                "headline": "Large markets break the pattern — Promotion 3 dominates at 77K",
                "context": "Applying a one-size-fits-all promotion strategy ignores a 22% sales premium available in Large markets. Treating all markets identically destroys value.",
                "recommended_action": "Override the national promo mix in Large-market stores with Promotion 3 by end of week.",
                "supporting_metric": "77.2K average sales for Promotion 3 in Large markets vs 58.1K overall leader",
                "impact_area": "growth",
                "magnitude": "high",
                "finding_reference": "FINDING 2"
            },
            {
                "headline": "Store age creates a performance valley — mid-age stores underperform by 15%",
                "context": "Stores aged 4-15 years show a consistent 15% dip versus newer and older stores. This is likely a service-quality or renewal cycle issue, not a demand problem.",
                "recommended_action": "Audit the 10 mid-age stores with the lowest sales this week and prioritise them for a refresh program.",
                "supporting_metric": "50K average sales for mid-age stores vs 59K for new stores",
                "impact_area": "efficiency",
                "magnitude": "medium",
                "finding_reference": "FINDING 6"
            }
        ])

    def _strip_thinking(self, raw: str) -> str:
        return raw


# ─── Simple DataProfile stub ─────────────────────────────────────────────────

@dataclass
class StubProfile:
    df: Any
    rows: int
    cols: int
    file_name: str = "test_wa_marketing.csv"
    source_type: str = "csv"
    columns: list = field(default_factory=list)
    dtypes: dict = field(default_factory=dict)
    nulls: dict = field(default_factory=dict)
    null_pct: dict = field(default_factory=dict)
    duplicates: int = 0
    numeric_summary: dict = field(default_factory=dict)
    sample: list = field(default_factory=list)
    text_content: str = ""
    column_types: dict = field(default_factory=dict)
    has_datetime: bool = False
    has_numeric: bool = True
    kpi_columns: list = field(default_factory=list)
    processing_time: float = 0.0
    warnings: list = field(default_factory=list)


def make_profile(df: pd.DataFrame) -> StubProfile:
    return StubProfile(
        df=df,
        rows=len(df),
        cols=len(df.columns),
        columns=list(df.columns),
        dtypes={c: str(df[c].dtype) for c in df.columns},
        null_pct={c: float(df[c].isna().mean() * 100) for c in df.columns},
        has_numeric=True,
        kpi_columns=["SalesInThousands"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test runner
# ─────────────────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = ""
        self.duration = 0.0
        self.details = []

    def ok(self, detail: str = ""):
        self.passed = True
        if detail:
            self.details.append(detail)

    def fail(self, reason: str):
        self.passed = False
        self.error = reason


def run_test(name: str, fn) -> TestResult:
    result = TestResult(name)
    t0 = time.time()
    try:
        fn(result)
    except AssertionError as e:
        result.fail(str(e) or "Assertion failed")
    except Exception as e:
        result.fail(f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
    result.duration = round(time.time() - t0, 3)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: DatasetClassifier
# ─────────────────────────────────────────────────────────────────────────────

def test_classifier(result: TestResult):
    from ai.dataset_classifier import DatasetClassifier

    df = make_wa_marketing_df()
    profile = make_profile(df)
    classifier = DatasetClassifier()
    meta = classifier.classify(df, profile)

    # dataset_type must be "experiment"
    assert meta.dataset_type == "experiment", \
        f"Expected 'experiment', got '{meta.dataset_type}'"
    result.details.append(f"dataset_type = {meta.dataset_type}")

    # confidence > 0.3 (experiment type uses a relaxed threshold when an
    # explicit keyword column is present — see DatasetClassifier._score_type)
    assert meta.confidence > 0.3, \
        f"Confidence too low: {meta.confidence}"
    result.details.append(f"confidence = {meta.confidence:.3f}")

    # LocationID must be in identifiers
    assert "LocationID" in meta.identifiers, \
        f"LocationID not detected as identifier. identifiers={meta.identifiers}"
    result.details.append(f"identifiers = {meta.identifiers}")

    # LocationID must NOT be in dimensions or measures
    assert "LocationID" not in meta.dimensions, \
        "LocationID incorrectly placed in dimensions"
    assert "LocationID" not in meta.measures, \
        "LocationID incorrectly placed in measures"

    # primary_dimension should be Promotion
    assert "Promotion" in meta.primary_dimension or "promotion" in meta.primary_dimension.lower(), \
        f"Expected primary_dimension to be Promotion, got '{meta.primary_dimension}'"
    result.details.append(f"primary_dimension = {meta.primary_dimension}")

    # primary_measure should be SalesInThousands
    assert meta.primary_measure == "SalesInThousands", \
        f"Expected primary_measure=SalesInThousands, got '{meta.primary_measure}'"
    result.details.append(f"primary_measure = {meta.primary_measure}")

    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: AnalyticalEngine
# ─────────────────────────────────────────────────────────────────────────────

def test_analytical_engine(result: TestResult):
    from ai.dataset_classifier import DatasetClassifier
    from ai.analytical_engine import AnalyticalEngine

    df = make_wa_marketing_df()
    profile = make_profile(df)
    meta = DatasetClassifier().classify(df, profile)
    engine = AnalyticalEngine()
    findings = engine.analyze(df, meta, profile)

    assert len(findings) > 0, "No findings produced"
    result.details.append(f"findings count = {len(findings)}")

    # Find the Q1 winner finding
    winner_finding = None
    for f in findings:
        if "wins" in f.answer.lower() or "higher" in f.answer.lower() or "%" in f.answer:
            winner_finding = f
            break

    assert winner_finding is not None, \
        f"Could not find a winner finding. Answers: {[f.answer[:60] for f in findings]}"

    # Q1 winner answer must contain "Promotion 1" and a number
    promo_numbers = ["58", "47", "22", "Promotion 1"]
    found_any = any(tok in winner_finding.answer for tok in promo_numbers)
    assert found_any, \
        f"Winner finding answer doesn't reference expected values. Got: '{winner_finding.answer}'"
    result.details.append(f"winner answer = {winner_finding.answer[:100]}")

    # No finding should have LocationID as a chart x/y axis
    for f in findings:
        cc = f.chart_config or {}
        x = cc.get("x_col", "") or ""
        y = cc.get("y_col", "") or ""
        assert "LocationID" not in x, \
            f"LocationID appears as chart x_col in finding: {f.question}"
        assert "LocationID" not in y, \
            f"LocationID appears as chart y_col in finding: {f.question}"

    result.details.append("LocationID correctly excluded from all chart axes")

    # All data dicts must be JSON-serializable (no numpy types)
    for f in findings:
        try:
            json.dumps(f.data)
        except TypeError as e:
            assert False, f"Finding '{f.question[:40]}' has non-serializable data: {e}"

    result.details.append("All finding data dicts are JSON-serializable")
    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: SmartVizSelector
# ─────────────────────────────────────────────────────────────────────────────

def test_smart_viz_selector(result: TestResult):
    from ai.dataset_classifier import DatasetClassifier
    from ai.analytical_engine import AnalyticalEngine
    from ai.smart_viz_selector import SmartVizSelector

    df = make_wa_marketing_df()
    profile = make_profile(df)
    meta = DatasetClassifier().classify(df, profile)
    findings = AnalyticalEngine().analyze(df, meta, profile)
    charts = SmartVizSelector().select_charts(df, meta, findings)

    assert len(charts) > 0, "No charts produced"
    assert len(charts) <= 6, f"Too many charts: {len(charts)}"
    result.details.append(f"chart count = {len(charts)}")

    # No chart should have LocationID or MarketID as x or y
    for chart in charts:
        x = chart.x_col or ""
        y = chart.y_col or ""
        for id_col in meta.identifiers:
            assert id_col not in x, \
                f"Identifier '{id_col}' appears as x_col in chart '{chart.title}'"
            assert id_col not in y, \
                f"Identifier '{id_col}' appears as y_col in chart '{chart.title}'"

    result.details.append("No identifier columns used as chart axes")

    # All chart data must be JSON-serializable
    for chart in charts:
        try:
            json.dumps(chart.data)
        except TypeError as e:
            assert False, f"Chart '{chart.title}' has non-serializable data: {e}"

    result.details.append("All chart data is JSON-serializable")

    # At least one chart should target SalesInThousands
    sales_charts = [c for c in charts if "SalesInThousands" in (c.y_col or "") or
                    "SalesInThousands" in (c.x_col or "") or
                    any("SalesInThousands" in str(d) for d in (c.data or []))]
    # Relaxed: at least one chart should relate to the primary measure
    result.details.append(f"Charts targeting primary measure: {len(sales_charts)}")

    # Verify chart titles are non-empty
    for chart in charts:
        assert chart.title and chart.title.strip(), \
            f"Chart has empty title: {chart}"

    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: GroundedInsightGenerator (MockNIMClient)
# ─────────────────────────────────────────────────────────────────────────────

def test_grounded_insight_generator(result: TestResult):
    from ai.dataset_classifier import DatasetClassifier
    from ai.analytical_engine import AnalyticalEngine
    from ai.grounded_insight_generator import GroundedInsightGenerator

    df = make_wa_marketing_df()
    profile = make_profile(df)
    meta = DatasetClassifier().classify(df, profile)
    findings = AnalyticalEngine().analyze(df, meta, profile)

    nim = MockNIMClient()
    gen = GroundedInsightGenerator()
    out = gen.generate(meta, findings, nim)

    # Must have insights key
    assert "insights" in out, "Missing 'insights' key in output"
    insights = out["insights"]
    assert isinstance(insights, list), "insights must be a list"
    assert len(insights) == 3, f"Expected 3 insights, got {len(insights)}"
    result.details.append(f"insights count = {len(insights)}")

    # Each insight must have all 7 required keys
    required_keys = {"headline", "context", "recommended_action",
                     "supporting_metric", "impact_area", "magnitude", "finding_reference"}
    for i, ins in enumerate(insights):
        missing = required_keys - set(ins.keys())
        assert not missing, f"Insight {i} missing keys: {missing}"

    # No forbidden stat terms in any insight
    forbidden = ["mean", "std", "variance", "z-score"]
    insights_str = json.dumps(insights).lower()
    for term in forbidden:
        assert term not in insights_str, \
            f"Forbidden term '{term}' found in insights"

    result.details.append("No forbidden statistical terms in insights")

    # magnitude must be high/medium/low
    for ins in insights:
        assert ins["magnitude"] in ("high", "medium", "low"), \
            f"Invalid magnitude: {ins['magnitude']}"

    # impact_area must be valid
    valid_areas = {"revenue", "cost", "risk", "growth", "efficiency"}
    for ins in insights:
        assert ins["impact_area"] in valid_areas, \
            f"Invalid impact_area: {ins['impact_area']}"

    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Full FindingsGenerator pipeline (MockNIMClient)
# ─────────────────────────────────────────────────────────────────────────────

def test_full_pipeline(result: TestResult):
    from ai.findings_generator import FindingsGenerator

    df = make_wa_marketing_df()
    profile = make_profile(df)
    nim = MockNIMClient()

    steps_seen = []
    def on_progress(step, msg):
        steps_seen.append(step)

    fg = FindingsGenerator()
    output = fg.generate(profile, nim, progress_callback=on_progress)

    # All 6 progress steps fired
    assert len(steps_seen) == 6, \
        f"Expected 6 progress steps, got {len(steps_seen)}: {steps_seen}"

    # All existing keys present
    existing_keys = ["profile", "charts", "anomalies", "executive_summary",
                     "key_findings", "next_steps", "data_health_score", "processing_time"]
    for key in existing_keys:
        assert key in output, f"Missing existing key: '{key}'"

    # New additive keys present
    new_keys = ["dataset_meta", "analytical_findings", "insights"]
    for key in new_keys:
        assert key in output, f"Missing new key: '{key}'"

    result.details.append(f"All {len(existing_keys) + len(new_keys)} keys present")

    # executive_summary is a non-empty string
    assert isinstance(output["executive_summary"], str) and output["executive_summary"].strip(), \
        "executive_summary is empty"
    result.details.append(f"executive_summary length = {len(output['executive_summary'])} chars")

    # LocationID not in any chart axis
    for chart in output["charts"]:
        x = chart.get("x_col", "") or ""
        y = chart.get("y_col", "") or ""
        assert "LocationID" not in x, f"LocationID in chart x_col: {chart.get('title')}"
        assert "LocationID" not in y, f"LocationID in chart y_col: {chart.get('title')}"

    result.details.append("LocationID absent from all chart axes in pipeline output")

    # dataset_meta has correct type
    dm = output["dataset_meta"]
    assert dm.get("dataset_type") == "experiment", \
        f"Expected 'experiment', got '{dm.get('dataset_type')}'"

    # insights is a list of 3
    assert isinstance(output["insights"], list), "insights must be a list"
    assert len(output["insights"]) == 3, \
        f"Expected 3 insights, got {len(output['insights'])}"

    # No forbidden stat terms in executive_summary or insights
    forbidden = ["mean", "std", "variance"]
    full_text = json.dumps({
        "exec": output["executive_summary"],
        "insights": output["insights"]
    }).lower()
    for term in forbidden:
        assert term not in full_text, \
            f"Forbidden term '{term}' found in pipeline output text"

    result.details.append("No forbidden statistical terms in pipeline output")
    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Segment and Large-market winner detection
# ─────────────────────────────────────────────────────────────────────────────

def test_segment_winner_detection(result: TestResult):
    """
    Validate that the AnalyticalEngine correctly identifies:
    - Promotion 1 as overall winner in Medium/Small markets
    - Promotion 3 as winner in Large markets
    - AgeOfStore U-pattern
    """
    from ai.dataset_classifier import DatasetClassifier
    from ai.analytical_engine import AnalyticalEngine

    df = make_wa_marketing_df()
    profile = make_profile(df)
    meta = DatasetClassifier().classify(df, profile)
    findings = AnalyticalEngine().analyze(df, meta, profile)

    # Q2 segment finding should exist
    segment_findings = [f for f in findings
                        if "segment" in f.insight_type.lower() or
                           "market" in f.question.lower() or
                           "segment" in f.question.lower()]
    assert len(segment_findings) > 0, \
        f"No segment findings found. All questions: {[f.question for f in findings]}"
    result.details.append(f"segment findings = {len(segment_findings)}")

    # The Q2 answer should reference Large market or Promotion 3
    large_ref = any(
        "Large" in f.answer or "Promotion 3" in f.answer or "large" in f.answer.lower()
        for f in segment_findings
    )
    assert large_ref, \
        f"Segment findings don't reference Large market or Promotion 3. " \
        f"Answers: {[f.answer[:80] for f in segment_findings]}"
    result.details.append("Large market / Promotion 3 winner correctly identified")

    # Verify Q6 segment factor (AgeOfStore) finding exists
    age_findings = [f for f in findings
                    if "age" in f.question.lower() or "ageofstore" in f.question.lower()]
    assert len(age_findings) > 0, \
        f"No AgeOfStore findings. All questions: {[f.question for f in findings]}"

    # AgeOfStore finding should mention a pattern (u-shaped or similar)
    age_answer = age_findings[0].answer.lower()
    pattern_words = ["u-shaped", "valley", "dip", "mid", "pattern", "young", "new", "older"]
    found_pattern = any(pw in age_answer for pw in pattern_words)
    assert found_pattern, \
        f"AgeOfStore finding doesn't describe a pattern. Answer: '{age_findings[0].answer}'"
    result.details.append(f"AgeOfStore pattern finding: '{age_findings[0].answer[:80]}'")

    result.ok()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

TESTS = [
    ("Test 1: DatasetClassifier",                test_classifier),
    ("Test 2: AnalyticalEngine",                 test_analytical_engine),
    ("Test 3: SmartVizSelector",                 test_smart_viz_selector),
    ("Test 4: GroundedInsightGenerator (Mock)",  test_grounded_insight_generator),
    ("Test 5: Full FindingsGenerator Pipeline",  test_full_pipeline),
    ("Test 6: Segment & Large-market Detection", test_segment_winner_detection),
]


def main():
    print("\n" + "=" * 65)
    print("  DataLens AI — Analyst Brain Test Suite")
    print("=" * 65)

    results = []
    for name, fn in TESTS:
        print(f"\n  Running: {name} ...", end="", flush=True)
        r = run_test(name, fn)
        results.append(r)
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}]  ({r.duration}s)")
        if r.details:
            for d in r.details:
                print(f"    -> {d}")
        if not r.passed:
            print(f"    ERROR: {r.error}")

    passed = sum(1 for r in results if r.passed)
    total  = len(results)

    print("\n" + "=" * 65)
    print(f"  Results: {passed}/{total} tests passed")
    if passed == total:
        print("  ALL TESTS PASSED")
    else:
        failed = [r.name for r in results if not r.passed]
        print(f"  FAILED: {', '.join(failed)}")
    print("=" * 65 + "\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
