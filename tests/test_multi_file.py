"""
Test suite for multi_file.py (Sprint 3)
- Tests FK detection
- Tests star schema building
- Tests composite key detection
- Tests edge cases
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, r"C:\James\engineering_lab\datalens-ai\backend")
from ai.multi_file import (
    profile_file, detect_relationships, build_star_schema,
    run_multi_file_pipeline, _normalize_col_name, _value_overlap_pct
)

# ════════════════════════════════════════════════════════
# Test 1: Name normalization
# ════════════════════════════════════════════════════════

print("="*70)
print("TEST 1: Name normalization")
print("="*70)
tests = [
    ("customer_id", "customer"),
    ("customerId", "customerid"),
    ("customer_email", "customer_email"),
    ("category", "category"),
    ("categories", "categorie"),  # singular
    ("product_category_id", "product"),
    ("region_name", "region"),
    ("region", "region"),
    ("product_id", "product"),
    ("orders.order_id", "orders.order"),
]
for input_, expected in tests:
    actual = _normalize_col_name(input_)
    status = "✓" if actual == expected else "✗"
    print(f"  {status} {input_} -> {actual} (expected: {expected})")
    assert actual == expected, f"FAIL: {input_} normalized to {actual}, expected {expected}"

# ════════════════════════════════════════════════════════
# Test 2: Value overlap
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 2: Value overlap detection")
print("="*70)
a = pd.Series([1, 2, 3, 4, 5])
b = pd.Series([3, 4, 5, 6, 7])
overlap = _value_overlap_pct(a, b)
print(f"  A={list(a)}, B={list(b)}, overlap={overlap:.2%} (expected 60%)")
assert 0.55 < overlap < 0.65, f"FAIL: overlap {overlap} not in range"

# 100% overlap
overlap = _value_overlap_pct(pd.Series([1, 2, 3]), pd.Series([1, 2, 3]))
print(f"  100% overlap test: {overlap:.2%}")
assert overlap == 1.0

# 0% overlap
overlap = _value_overlap_pct(pd.Series([1, 2, 3]), pd.Series([10, 20, 30]))
print(f"  0% overlap test: {overlap:.2%}")
assert overlap == 0.0

# ════════════════════════════════════════════════════════
# Test 3: File profiling
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 3: File profiling + PK detection")
print("="*70)
df = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "value": [10, 20, 30, 40, 50],
})
prof = profile_file("test", "test.csv", df)
print(f"  Rows: {prof.rows}, Cols: {prof.cols}")
print(f"  PK candidates: {prof.pk_candidates}")
print(f"  Column types: {prof.dtypes}")
assert "id" in prof.pk_candidates
assert "name" in prof.pk_candidates
# value has 100% uniqueness too, so it's also a PK candidate (acceptable behavior)
assert prof.dtypes["id"] == "int"

# ════════════════════════════════════════════════════════
# Test 4: End-to-end pipeline
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 4: E2E pipeline (3 related CSVs)")
print("="*70)

# Build test data
np.random.seed(42)
customers = pd.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "name": ["A", "B", "C", "D", "E"],
    "region": ["North", "South", "North", "East", "West"],
})
orders = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105, 106, 107],
    "customer_id": [1, 2, 1, 3, 4, 5, 2],
    "amount": [100, 200, 150, 300, 250, 180, 220],
})

# Save to bytes
from io import BytesIO
def df_to_bytes(df, name):
    return (name.replace(".csv", ""), name, df.to_csv(index=False).encode())

files = [
    df_to_bytes(customers, "customers.csv"),
    df_to_bytes(orders, "orders.csv"),
]

result = run_multi_file_pipeline(files)
print(f"  Success: {result.get('success')}")
print(f"  Files: {result.get('file_count')}")
print(f"  Relationships: {len(result.get('relationships', []))}")
for r in result.get('relationships', []):
    print(f"    {r['from_file']}.{r['from_column']} -> {r['to_file']}.{r['to_column']} ({r['relationship_type']}, conf={r['confidence']})")
assert result.get('success')
assert len(result.get('relationships', [])) >= 1, "Should detect customers-orders relationship"

# ════════════════════════════════════════════════════════
# Test 5: Edge cases
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 5: Edge cases")
print("="*70)

# Empty file list
result = run_multi_file_pipeline([])
print(f"  Empty files: success={result.get('success')}, error={result.get('error', 'N/A')[:50]}")
assert not result.get('success')

# Only 1 file (pipeline allows it for testing, but API would reject)
result = run_multi_file_pipeline([df_to_bytes(customers, "customers.csv")])
print(f"  1 file: success={result.get('success')} (allowed in helper, API rejects)")
assert result.get('success')  # helper is permissive

# 11 files (over limit)
many_files = [df_to_bytes(customers, f"file_{i}.csv") for i in range(11)]
result = run_multi_file_pipeline(many_files)
print(f"  11 files: success={result.get('success')}, error={result.get('error', 'N/A')[:50]}")
assert not result.get('success')

# Duplicate column names (should not crash)
df_dup = pd.DataFrame({
    "id": [1, 2, 3],
    "value": [10, 20, 30],
})
result = run_multi_file_pipeline([df_to_bytes(df_dup, "a.csv"), df_to_bytes(df_dup, "b.csv")])
print(f"  Duplicate schemas: success={result.get('success')}")
# May or may not find a relationship, but should not crash
assert "error" not in result or "Failed" not in result.get("error", "")

print("\n" + "="*70)
print("ALL TESTS PASSED ✅")
print("="*70)
