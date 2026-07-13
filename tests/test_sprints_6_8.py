"""
Test suite for Sprint 6-8 modules (multi_file_store, data_quality, lineage)
"""
import os
import sys
import pandas as pd
import json
import time

sys.path.insert(0, r"C:\James\engineering_lab\datalens-ai\backend")
from ai.multi_file_store import MultiFileStore
from ai.data_quality import check_data_quality, quality_summary
from ai.lineage import build_lineage, lineage_summary, trace_to_source

# ════════════════════════════════════════════════════════
# Test 6: Persistence (Sprint 6)
# ════════════════════════════════════════════════════════

print("="*70)
print("TEST 6: Multi-file persistence")
print("="*70)
store = MultiFileStore()
job_id = "test_" + str(int(time.time()))
file_bytes = {
    "a.csv": b"x,y\n1,2\n3,4\n",
    "b.csv": b"z,w\n5,6\n7,8\n",
}
meta = store.save_job(
    job_id=job_id,
    file_bytes=file_bytes,
    relationships=[{"from": "a", "to": "b", "type": "M:1"}],
    schema={"fact": "a"},
)
print(f"  Saved: {meta['file_count']} files, {meta['relationship_count']} rels")
assert meta['file_count'] == 2

# Load
loaded = store.load_job(job_id)
print(f"  Loaded: {loaded['job_id'][:20]}...")
assert loaded is not None

# Files
files = store.get_files(job_id)
print(f"  Files on disk: {list(files.keys())}")
assert "a.csv" in files
assert files["a.csv"] == b"x,y\n1,2\n3,4\n"

# List
jobs = store.list_jobs()
print(f"  Total persisted jobs: {len(jobs)}")
assert len(jobs) >= 1

# Disk usage
usage = store.disk_usage()
print(f"  Disk: {usage['total_kb']} KB, {usage['job_count']} jobs")
assert usage['job_count'] >= 1

# Delete
deleted = store.delete_job(job_id)
print(f"  Deleted: {deleted}")
assert deleted

# Verify gone
assert store.load_job(job_id) is None
print("  Persistence tests passed!")

# ════════════════════════════════════════════════════════
# Test 7: Data quality (Sprint 7)
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 7: Data quality")
print("="*70)

# Clean data
df_clean = pd.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "value": [10, 20, 30, 40, 50],
    "category": ["A", "B", "A", "B", "A"],
})
q = check_data_quality("clean.csv", df_clean)
print(f"  Clean: score={q['score']}, warnings={len(q['warnings'])}")
assert q['score'] >= 90
assert len(q['warnings']) == 0

# Dirty data
df_dirty = pd.DataFrame({
    "id": [1, 1, 1, 1, 1],  # constant
    "value": [10, 20, 30, 40, 1000000],  # outlier
    "missing": [None, None, None, None, 1],  # 80% null
    "category": ["A", "B", None, None, None],  # 60% null
})
q = check_data_quality("dirty.csv", df_dirty)
print(f"  Dirty: score={q['score']}, warnings={len(q['warnings'])}")
for w in q['warnings'][:3]:
    print(f"    - {w}")
assert q['score'] < 100
assert len(q['warnings']) >= 3

# Summary
summary = quality_summary({"clean.csv": q, "dirty.csv": q})
print(f"  Summary: overall={summary['overall_score']}, total_warnings={summary['total_warnings']}")
assert summary['total_warnings'] >= 6
print("  Data quality tests passed!")

# ════════════════════════════════════════════════════════
# Test 8: Lineage (Sprint 8)
# ════════════════════════════════════════════════════════

print("\n" + "="*70)
print("TEST 8: Column lineage")
print("="*70)

file_columns = {
    "customers": ["customer_id", "name", "region"],
    "orders": ["order_id", "customer_id", "amount"],
    "products": ["product_id", "name", "price"],
}
relationships = [
    {"from_file": "orders", "from_column": "customer_id",
     "to_file": "customers", "to_column": "customer_id",
     "relationship_type": "many_to_one"},
]
lineages = build_lineage(
    list(file_columns.keys()),
    file_columns,
    relationships,
    "orders",
    ["customers", "products"],
)
print(f"  Total lineage columns: {len(lineages)}")
for col, l in list(lineages.items())[:3]:
    print(f"    {col}: from {l['source_file']}.{l['source_column']} ({l['transformation']})")
assert len(lineages) == 9  # 3 + 3 + 3, with prefix for "name" collision
assert "customers_name" in lineages  # "name" appears in 2 files, gets prefix
assert "customers_customer_id" in lineages  # customer_id also appears in 2 files
assert "orders_customer_id" in lineages  # both sides get prefixed

# Trace
trace = trace_to_source(lineages, "customers_customer_id")
print(f"  Trace customers_customer_id: {trace}")
assert len(trace) == 1
assert trace[0]["source_file"] == "customers"

# Summary
summary = lineage_summary(lineages, relationships)
print(f"  Summary: total={summary['total_columns']}, source_files={summary['source_files']}")
assert summary['total_columns'] == len(lineages)
assert len(summary['source_files']) == 3

print("  Lineage tests passed!")

print("\n" + "="*70)
print("ALL SPRINT 6-8 TESTS PASSED ✅")
print("="*70)
