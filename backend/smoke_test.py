#!/usr/bin/env python3
"""
smoke_test.py — End-to-end test of the full DataLens AI pipeline.

Tests:
  1. /api/health
  2. Upload sample CSV
  3. Wait for analysis
  4. /api/dataset returns records
  5. /api/filter with region=APAC
  6. /api/filter with multi-column filter
  7. /api/drilldown
  8. /api/export/dashboard (HTML ZIP)
  9. /api/export/pbix (real PowerBI .pbit)
  10. /api/ask/sync (chat with data)
"""
import sys
import os
import time
import json
import requests
import tempfile

BASE = "http://localhost:5000"
SAMPLE_CSV = r"C:\Users\modir\AppData\Local\Temp\datalens_test.csv"

# Recreate sample if missing
if not os.path.exists(SAMPLE_CSV):
    print(f"Sample CSV missing, regenerating...")
    import shutil
    sample = '''date,region,product_category,customer_segment,revenue,units_sold
2025-01-15,APAC,Electronics,B2B,8200,45
2025-02-20,APAC,Clothing,B2C,5400,80
2025-03-10,EU,Electronics,B2B,9100,50
2025-04-05,NA,Home,B2C,4200,30
2025-05-12,EU,Clothing,B2B,7500,90
2025-06-18,APAC,Electronics,B2C,6800,38
2025-07-22,NA,Home,B2B,5500,32
2025-08-30,EU,Electronics,B2B,9900,55
2025-09-14,APAC,Clothing,B2C,6200,75
2025-10-25,NA,Home,B2C,4800,28
2025-11-08,EU,Electronics,B2C,8700,48
2025-12-19,APAC,Home,B2B,7100,40
2025-01-30,NA,Electronics,B2B,8900,52
2025-02-12,EU,Clothing,B2C,5800,85
2025-03-25,APAC,Home,B2C,4500,25
2025-04-18,EU,Electronics,B2B,9500,53
2025-05-22,NA,Clothing,B2C,6700,95
2025-06-30,APAC,Electronics,B2B,8800,49
2025-07-15,EU,Home,B2C,5200,33
2025-08-28,NA,Electronics,B2C,7600,42
2025-09-05,APAC,Clothing,B2B,8500,110
2025-10-12,EU,Home,B2B,6300,38
2025-11-19,NA,Clothing,B2C,5500,82
2025-12-22,APAC,Electronics,B2C,7900,44
2025-01-08,EU,Home,B2B,4800,27
2025-02-14,NA,Electronics,B2B,9300,51
2025-03-21,APAC,Clothing,B2C,5700,87
2025-04-09,EU,Electronics,B2C,8400,46
2025-05-17,NA,Home,B2B,5900,35
2025-06-26,APAC,Electronics,B2B,42000,200'''
    with open(SAMPLE_CSV, "w") as f:
        f.write(sample)
    print(f"  Created {SAMPLE_CSV}")


def run():
    print("=" * 70)
    print("DataLens AI — Smoke Test")
    print("=" * 70)
    passed = 0
    failed = 0

    # 1. Health
    print("\n[1] /api/health...")
    try:
        r = requests.get(f"{BASE}/api/health", timeout=10)
        d = r.json()
        assert d.get("status") == "ok" and d.get("ollama_cloud")
        print(f"  ✓ Ollama Cloud live · {d.get('models_registered')} models")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1
        return  # No point continuing

    # 2. Upload
    print("\n[2] Upload sample CSV...")
    try:
        r = requests.post(f"{BASE}/api/analyze",
                          files={"file": open(SAMPLE_CSV, "rb")}, timeout=120)
        d = r.json()
        assert d.get("success")
        job_id = d["job_id"]
        print(f"  ✓ Job created: {job_id}")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1
        return

    # 3. Wait for analysis
    print("\n[3] Wait for analysis (up to 60s)...")
    for i in range(40):
        s = requests.get(f"{BASE}/api/status/{job_id}", timeout=30).json()
        if s.get("status") in ("completed", "failed"):
            break
        time.sleep(2)
    if s.get("status") != "completed":
        print(f"  ✗ FAILED: {s.get('status')} - {s.get('error', 'no error')}")
        failed += 1
        return
    print(f"  ✓ Completed in ~{i*2}s")
    passed += 1

    # 4. Dataset
    print("\n[4] /api/dataset/<id>...")
    try:
        r = requests.get(f"{BASE}/api/dataset/{job_id}", timeout=10)
        d = r.json()
        assert len(d.get("records", [])) > 0
        assert len(d.get("filterable_columns", [])) > 0
        print(f"  ✓ {len(d['records'])} records, {len(d['filterable_columns'])} filterable columns")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 5. Filter (single)
    print("\n[5] /api/filter region=APAC...")
    try:
        r = requests.post(f"{BASE}/api/filter",
                          json={"session_id": job_id, "filters": {"region": "APAC"}}, timeout=30)
        d = r.json()
        assert d.get("success")
        stats = d.get("stats", {})
        print(f"  ✓ Filtered: {stats.get('filtered_rows')}/{stats.get('total_rows')} ({stats.get('filter_pct')}%)")
        assert stats.get("filtered_rows") < stats.get("total_rows")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 6. Filter (multi-column)
    print("\n[6] /api/filter EU + B2B + Electronics...")
    try:
        r = requests.post(f"{BASE}/api/filter",
                          json={"session_id": job_id, "filters": {"region": "EU", "customer_segment": "B2B", "product_category": "Electronics"}}, timeout=30)
        d = r.json()
        assert d.get("success")
        print(f"  ✓ {d['stats']['filtered_rows']}/{d['stats']['total_rows']} rows")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 7. Drilldown
    print("\n[7] /api/drilldown region=APAC...")
    try:
        r = requests.post(f"{BASE}/api/drilldown",
                          json={"session_id": job_id, "column": "region", "value": "APAC", "limit": 5}, timeout=10)
        d = r.json()
        assert d.get("total", 0) > 0
        print(f"  ✓ {d['total']} matching rows, showing {d['shown']}")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 8. Dashboard export
    print("\n[8] /api/export/dashboard (HTML ZIP)...")
    try:
        r = requests.get(f"{BASE}/api/export/dashboard?session_id={job_id}", timeout=30, stream=True)
        assert r.status_code == 200
        size = sum(len(chunk) for chunk in r.iter_content(8192))
        print(f"  ✓ Downloaded: {size:,} bytes")
        assert size > 1000
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 9. PBIT export
    print("\n[9] /api/export/pbix (real PowerBI .pbit)...")
    try:
        r = requests.get(f"{BASE}/api/export/pbix?session_id={job_id}", timeout=120, stream=True)
        if r.status_code != 200:
            print(f"  ✗ FAILED: {r.status_code} {r.text[:200]}")
            failed += 1
        else:
            tmp = tempfile.NamedTemporaryFile(suffix=".pbit", delete=False)
            for chunk in r.iter_content(8192):
                tmp.write(chunk)
            tmp.close()
            size = os.path.getsize(tmp.name)
            # Verify it's a valid ZIP
            import zipfile
            with zipfile.ZipFile(tmp.name) as zf:
                names = zf.namelist()
            has_model = any("DataModel" in n for n in names)
            has_report = any("Report/Layout" in n for n in names)
            print(f"  ✓ {size:,} bytes · {len(names)} files · DataModel={has_model} Report={has_report}")
            assert has_model and has_report
            os.unlink(tmp.name)
            passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    # 10. Chat
    print("\n[10] /api/ask/sync...")
    try:
        r = requests.post(f"{BASE}/api/ask/sync",
                          json={"session_id": job_id, "question": "What's the total revenue?"}, timeout=60)
        d = r.json()
        assert d.get("success")
        ans = d.get("answer", "")
        print(f"  ✓ Answer ({len(ans)} chars): {ans[:120]}...")
        passed += 1
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
