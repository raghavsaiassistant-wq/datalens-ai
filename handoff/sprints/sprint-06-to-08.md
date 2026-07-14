# Sprints 6-8: Production Foundations

**When:** 2026-07-14 night (1.5 hours)
**Why:** A demo that crashes on restart is not production. Trust requires persistence, quality, lineage.

---

## Sprint 6: Persistence to disk

**Module:** `backend/ai/multi_file_store.py` (174 lines)

### What
- Save job state to `data/multi_file_jobs/{job_id}/`
- 5 files per job: meta.json, profile.json, relationships.json, ai_result.json, manifest.json
- Survives server restart
- Endpoints: `GET /api/multi/persistence/{job_id}`, `GET /api/multi/jobs`

### Why
- Demo for a recruiter: "upload, share the job_id, share the dashboard." If the job dies on restart, the demo dies.

### Lessons
- First patch attempt: didn't match actual `run_multi()` function structure. Wasted 10 min.
- Second attempt: same issue (used `files_payload` wrong).
- Third attempt: `files_payload` is `[(file_id, file_name, content_bytes)]` tuple list. Fixed.
- **Lesson:** read the actual code before patching.

### Test
- 1 test suite, 4 assertions
- Real test: 5-file job persisted to 36KB on disk, 5 original files saved

### Files
- `multi_file_store.py` — module (174 lines)
- `app.py` — wired `multi_file_store.save_job_state()` into `run_multi()`
- New endpoints: `/api/multi/persistence/{job_id}`, `/api/multi/jobs`

---

## Sprint 7: Data quality checks

**Module:** `backend/ai/data_quality.py` (165 lines)

### What
- 6 checks per file:
  1. **Null check** — % nulls per column, warn if > 50%
  2. **Constant columns** — low value, low score
  3. **Outliers** — IQR method, warn if > 10%
  4. **Cardinality** — high cardinality warnings (likely IDs)
  5. **Mixed types** — same column with multiple Python types
  6. **Date freshness** — min/max/range_days for date columns
  7. **Duplicate rows** — count + percentage
- 0-100 score per file, deductions for each issue
- Endpoint: `GET /api/multi/quality/{job_id}`

### Why
- "Garbage in, garbage out." Quality score tells the user: trust this analysis? Or fix the data first?

### Lessons
- Started with 7 checks; could collapse to 3 (nulls, outliers, duplicates) but the others are cheap.
- Mixed types detection: `df[col].dropna().apply(type).unique()` — works but slow. Future: use `df.dtypes` + sampling.

### Test
- 1 test suite, 3 assertions
- Real test: 5 Northwind files scored 97.6/100, 1 warning (22% outliers in credit_limit)

### Files
- `data_quality.py` — module (165 lines)
- `app.py` — endpoint `/api/multi/quality/{job_id}`

---

## Sprint 8: Column-level lineage

**Module:** `backend/ai/lineage.py` (111 lines)

### What
- For each output column: source file + source column + transformation + join chain
- Transformations: `passthrough`, `prefix_added`, `join_key`, `derived`
- Auto-prefixes collisions (`name` in 2 files → `customers_name`, `employees_name`)
- Trace single column to source: `GET /api/multi/lineage/{job_id}/{column}`

### Why
- "Where did this number come from?" — the most-asked question in data analysis.
- Trust: if you can trace the column, you can trust the insight.

### Lessons
- Initial design: 4 separate transformations. Realized: 2 (passthrough vs join_key) covers 95% of cases.
- Joined columns need the chain, not just the source. A fact column came from the fact table but its name came from the dim.

### Test
- 1 test suite, 2 assertions
- Real test: 68 columns tracked in Northwind, all sourceable

### Files
- `lineage.py` — module (111 lines)
- `app.py` — endpoints `/api/multi/lineage/{job_id}`, `/api/multi/lineage/{job_id}/{column}`

---

*Total Sprints 6-8: 3 commits, ~450 lines, 3 modules, 5 new endpoints.*
*All tested. All pushed.*
