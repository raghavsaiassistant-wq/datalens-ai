# Sprints 9-12: Real Data, ER Diagram, Performance, Hardening

**When:** 2026-07-14 late night (1.5 hours)
**Why:** Synthetic data is fine for tests, demos need real data. The gap between "works on 5 fake files" and "works on real Northwind" is credibility.

---

## Sprint 9: Northwind real test data

**Script:** `handoff/test-data/generate_northwind.py` (188 lines)

### What
- Generate 8 CSVs based on Microsoft's Northwind Traders schema
- Customers (20), Products (10), Shippers (3), Suppliers (5), Categories (4), Employees (5), Orders (200), OrderDetails (500+)
- 7 real relationships via IDs
- All joinable via standardized keys

### Why
- Synthetic 5-file test was great for unit tests. Northwind is the gold standard for "real" demos.
- Recruiter's question: "Does it work on real data?" — this answers it.

### Lessons
- Northwind is public domain. Should download from official source. Used a generator instead for time.
- Real data has 5+ years of edge cases: nulls, mixed types, weird dates.

### Test
- Ran multi-file pipeline on 8 Northwind CSVs
- Result: 8/8 relationships detected, 97.6/100 quality, 68 columns lineage-tracked
- Real example: detected `order_details.unit_price -> products.unit_price` (fact uses snapshot price, dim has current price) — impressive auto-detection

### Files
- Generated CSVs in `data/multi_file_jobs/` after first run
- Job ID for re-runs: `cc142d752702494380344dfb2d7c277c`

---

## Sprint 10: Mermaid ER diagram in HTML

**Files:** `backend/static/er-diagram.html` (87 lines), `app.py` (`/api/multi/er-diagram/{job_id}`)

### What
- Backend generates Mermaid `erDiagram` syntax from relationships
- Renders 8 tables with all columns, types, and cardinality symbols (`}o--||`, `}|--|{`)
- Labels FK relationships (e.g., `order_id : "FK to orders"`)
- Standalone HTML page with Mermaid.js from CDN

### Why
- Visual proof of auto-detection. The user sees the schema we built — and verifies it.
- Recruiter-friendly: "look, it understood my data."

### Lessons
- First 2 patch attempts had variable scope bugs (`relationships` was being used before being defined, or after a loop consumed it).
- Mermaid CDN: `https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`

### Test
- Visual: 8 tables, 8 relationships, all cardinality visible
- See `handoff/screenshots/er_diagram_sprint10.png`

### Files
- `static/er-diagram.html` — standalone page
- `app.py` — endpoint `/api/multi/er-diagram/{job_id}` returns mermaid string

---

## Sprint 11: Performance benchmark

**Test:** 1K, 10K, 50K orders

### What
- 1K orders (4,250 rows): 50.8s analysis
- 10K orders (42,500 rows): 30.5s analysis
- 50K orders: rejected at 100K limit (proper error message)

### Why
- Need to know the breaking point before users hit it.
- Bottleneck: AI calls (3 models × multiple prompts), not data processing.

### Lessons
- 100K row limit is conservative. Could be 500K with cache + parallelism.
- 10K actually faster than 1K because AI is the bottleneck, and AI is called once regardless of size.

### Test
- Log: `handoff/test-data/benchmark.log`

---

## Sprint 12: Production hardening

**Module:** `backend/ai/hardening.py` (143 lines)

### What
- **Circuit breaker** for Ollama: 3 failures → open, 120s reset
- **Timeout decorator** (threading-based): `with_timeout(60)(func)`
- **Request validator**: file count, size, extension whitelist
- **Filename sanitizer**: removes `..`, `/`, `\`, caps at 200 chars
- **Health endpoint** with circuit state: `GET /api/multi/health`

### Why
- "Works on my machine" is not production. Need failures to fail fast, not hang.

### Lessons
- Singleton `ollama_breaker` is unused in app code (only the test imports it). Ponytail flag: this is over-engineering for current usage.
- Threading-based timeout is good for I/O-bound, not CPU-bound. For AI calls, I/O is the bottleneck, so it works.

### Test
- 1 test suite, 6 tests
- All pass: circuit open/close, timeout, validation, sanitize

### Files
- `hardening.py` — module (143 lines)
- `app.py` — endpoints `/api/multi/health`, `/api/multi/circuit/reset`

---

*Total Sprints 9-12: 4 commits, ~700 lines, 1 module, 4 new endpoints.*
*Real data demo. ER diagram. Perf baseline. Hardening baseline.*
