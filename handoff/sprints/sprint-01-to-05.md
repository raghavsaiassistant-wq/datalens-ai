# Sprints 1-5: Multi-File MVP (the foundation)

**When:** 2026-07-14 evening (5 hours)
**Why:** Path C = 16-week commercial SaaS. Multi-file is the differentiator.
**Result:** Working MVP, 8 test suites passing.

---

## Sprint 1: Multi-file pipeline (FK detection, star schema)

**Module:** `backend/ai/multi_file.py` (616 lines)

### What
- Accept 2-10 files (CSV, Excel, JSON, SQL)
- Profile each file: columns, dtypes, nulls, uniques
- Detect primary keys: uniqueness ratio > 0.95 + non-null
- Detect foreign keys: name match (normalized) + value overlap (sampled 500)
- Build join graph, find fact table (most FKs)
- Build star schema: 1 fact + N dimensions

### Why
- **Differentiator.** Single-file analysis = commodity. Multi-file = insight.
- **Real problem.** Every analyst has 5+ related files; nobody wants to JOIN them by hand.

### Lessons
- Started with 1 join strategy, ended with star schema (1 fact + many dimensions) — the only way to scale beyond 4 files.
- Value overlap sampling at 500 is the sweet spot: fast enough, accurate enough.

### Test
- 5 CSVs (customers, products, orders, regions, sales_reps)
- 4 relationships detected
- Star schema built correctly
- Unified DataFrame has 30+ columns

---

## Sprint 2: Composite keys + cross-file drilldown

**Module:** `backend/ai/multi_file.py` (added ~150 lines)

### What
- Composite key detection: PK with 2+ columns
- Cross-file drilldown: click a number in dashboard, see source rows from all files
- Endpoint: `POST /api/multi/drilldown` with `{"output_col": "total_revenue", "value": 5000}`

### Why
- Composite keys are real (e.g., `order_details: (order_id, product_id)`)
- Drilldown is the "so what?" — KPI without drilldown is decoration

### Lessons
- Composite key detection = all subsets of columns that are unique together. O(2^n) in theory, but n rarely > 4.

---

## Sprint 3: 5 test suites, 15+ assertions

**Module:** `tests/test_multi_file.py`

### What
- 5 test suites: FK detection, schema building, drilldown, export, edge cases
- 15+ assertions across them
- All pass

### Why
- Ponytail principle: test before claim. We had to test the multi-file logic before we trusted the AI to use it.

### Lessons
- Edge cases > happy path. Tested: empty file, single column, all-null, all-same values, name collision.

---

## Sprint 4: Multi-file upload UI

**Module:** `backend/static/dashboard.html` (60KB)

### What
- Drag-drop area for 2-10 files
- Live preview of detected relationships (rendered as cards)
- "Analyze all" button → POST `/api/analyze/multi`
- Progress indicator

### Why
- Backend is invisible without UI. The "drop 10 files → unified dashboard" pitch needs to be clickable.

### Lessons
- Used vanilla HTML/JS, no React. Kept it portable. The Vite/React frontend is a Sprint 31+ concern.

---

## Sprint 5: Cardinality inference (1:1, 1:M, M:1, M:N)

**Module:** `backend/ai/multi_file.py` (added ~80 lines)

### What
- After FK detection, infer cardinality:
  - **1:1** — every PK in dim matches exactly 1 row in fact
  - **1:M** — fact has many rows per dim (most common)
  - **M:1** — many dims map to 1 fact (rare, but real)
  - **M:N** — both sides have multiple matches
- Endpoint: `GET /api/multi/relationships/{job_id}` returns list with cardinality

### Why
- Cardinality = how the data flows. A M:N relationship means the schema is wrong (need a junction table).
- Real example: `order_details:products` is M:1 (many order details per product), not 1:1.

### Lessons
- Initial implementation: just check uniqueness ratio on the FK side. Fast and 95% accurate.
- Edge case: when both sides are large, sampling is needed.

---

*Total Sprints 1-5: 5 commits, ~2,000 lines, 1 module.*
*All pushed to `ollama-migration` branch.*
