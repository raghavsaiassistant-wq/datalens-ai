"""Test multi-file pipeline on Northwind (Sprint 9)"""
import requests
import time
import os
import json

BACKEND = "http://localhost:5000"
DATA_DIR = r"C:\Users\modir\AppData\Local\Temp\northwind_data"

print("="*70)
print("SPRINT 9: Real data test (Northwind-style)")
print("="*70)
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
print(f"Files: {len(files)}")
for f in files:
    print(f"  - {f}")

print(f"\n[1] Uploading {len(files)} files...")
files_payload = []
for f in files:
    path = os.path.join(DATA_DIR, f)
    files_payload.append(("files", (f, open(path, "rb"), "text/csv")))

t0 = time.time()
r = requests.post(f"{BACKEND}/api/analyze/multi", files=files_payload, timeout=60)
for _, (_, fp, _) in files_payload:
    fp.close()
upload_time = time.time() - t0
print(f"  Upload: {r.status_code} in {upload_time:.2f}s")
result = r.json()
job_id = result.get("job_id")
print(f"  Job ID: {job_id}")

# Poll
print(f"\n[2] Polling...")
t0 = time.time()
while time.time() - t0 < 300:
    s = requests.get(f"{BACKEND}/api/status/{job_id}", timeout=10).json()
    if s.get("status") == "completed":
        print(f"  Done in {time.time()-t0:.1f}s")
        break
    elif s.get("status") == "failed":
        print(f"  FAILED: {s.get('error')}")
        exit(1)
    print(f"  [{int(time.time()-t0)}s] {s.get('status')} | {s.get('progress', '?')}/6 | {s.get('message', '')}")
    time.sleep(5)

# Get result
print(f"\n[3] Result...")
r = requests.get(f"{BACKEND}/api/status/{job_id}", timeout=10).json()
final = r.get("result", {})
multi = final.get("multi_file", {})

print(f"  Files unified: {multi.get('file_count')}")
print(f"  Total rows: {multi.get('total_rows')}")
print(f"  Relationships detected: {len(multi.get('relationships', []))}")
print(f"  Fact table: {multi.get('unified_schema', {}).get('fact_table')}")
print(f"  Dimensions: {multi.get('unified_schema', {}).get('dimension_tables')}")
print(f"  Unified: {multi.get('unified_data', {}).get('rows')} rows × {len(multi.get('unified_data', {}).get('cols', []))} cols")

print(f"\n[4] Detected relationships:")
for rel in multi.get("relationships", []):
    print(f"  {rel['from_file']}.{rel['from_column']} -> {rel['to_file']}.{rel['to_column']} ({rel['relationship_type']}, conf={rel.get('confidence', 0):.2f})")

print(f"\n[5] Data quality:")
quality = multi.get("data_quality", {}).get("summary", {})
print(f"  Overall score: {quality.get('overall_score')}/100")
print(f"  Total warnings: {quality.get('total_warnings')}")
print(f"  Files analyzed: {quality.get('files_analyzed')}")

print(f"\n[6] Lineage:")
lineage = multi.get("lineage", {}).get("summary", {})
print(f"  Total columns tracked: {lineage.get('total_columns')}")
print(f"  Passthrough: {lineage.get('passthrough_columns')}")
print(f"  Source files: {lineage.get('source_files')}")

print(f"\n[7] AI Summary:")
print(f"  {final.get('executive_summary', 'N/A')[:300]}")

# Save job_id for later
with open(r"C:\Users\modir\AppData\Local\Temp\northwind_job_id.txt", "w") as f:
    f.write(job_id)
print(f"\n[8] Job ID saved: {job_id}")

# Persist
print(f"\n[9] Checking persistence...")
p = requests.get(f"{BACKEND}/api/multi/persistence/{job_id}", timeout=10).json()
if p.get("persisted"):
    print(f"  ✅ Persisted: {p['meta']['file_count']} files")
else:
    print(f"  ❌ Not persisted")

# Time
print(f"\n⏱ Total test time: {time.time()-upload_time:.1f}s")
