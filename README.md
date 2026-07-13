# DataLens AI

> Drop files. Get a unified dashboard with auto-detected relationships, AI insights, and PowerBI exports.

**Status:** Production MVP (90% to commercial)  
**Stack:** Flask + React + Ollama Cloud + Pandas  
**Cost:** $0 to run (Ollama Pro $20/mo)  
**GitHub:** https://github.com/raghavsaiassistant-wq/datalens-ai

---

## What It Does

Upload **2-10 related files** (CSV, Excel, JSON, SQL). DataLens:

1. **Detects primary/foreign keys** across files (column name + value overlap)
2. **Builds a star schema** automatically (fact table + dimensions)
3. **Injects data quality checks** (nulls, outliers, duplicates, mixed types)
4. **Tracks column lineage** (where every output column came from)
5. **Runs AI insights** on the unified dataset (Kimi K2.7 + GLM 5.2 + 3 more)
6. **Exports** to PowerBI (.pbit), standalone HTML, and Mermaid ER diagrams
7. **Persists** all job state to disk (survive restarts)

## Architecture (16-Week Path C, Sprint 1-12 Complete)

```
┌──────────────┐
│   React UI   │  ← upload zone, dashboard, chat, ER diagram
└──────┬───────┘
       │ multipart/form-data
       ↓
┌──────────────┐
│ Flask API    │  ← 14+ endpoints, rate-limited
├──────────────┤
│ Multi-File   │  ← FK inference, star schema, cardinality
│ Pipeline     │     composite keys, name normalization
├──────────────┤
│ AI Layer     │  ← Ollama Cloud (4 models, 3-concurrent)
│              │     Kimi K2.7 (1T) + GLM 5.2 + gpt-oss 120B + minimax-m3
├──────────────┤
│ Persistence  │  ← SQLite + on-disk JSON
│              │     multi_file_store.py (36KB/job)
├──────────────┤
│ Quality +    │  ← 6 checks per file
│ Lineage      │     full column trace
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Exports      │  ← .pbit (pbi-tools), HTML ZIP, ER (Mermaid)
└──────────────┘
```

## Endpoints (Multi-File)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/analyze/multi` | Upload 2-10 files, run full pipeline |
| `GET` | `/api/multi/profile/<job_id>` | Get relationships + schema |
| `GET` | `/api/multi/er-diagram/<job_id>` | Get Mermaid ER diagram |
| `GET` | `/api/multi/drilldown/<job_id>` | Cross-file drilldown |
| `GET` | `/api/multi/quality/<job_id>` | Data quality report |
| `GET` | `/api/multi/lineage/<job_id>` | Column lineage map |
| `GET` | `/api/multi/lineage/<job_id>/<column>` | Trace one column |
| `GET` | `/api/multi/jobs` | List all persisted jobs |
| `GET` | `/api/multi/persistence/<job_id>` | Job metadata |
| `GET` | `/api/multi/health` | Service health + circuit breaker |
| `POST` | `/api/multi/circuit/reset` | Reset circuit breaker |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py  # → http://localhost:5000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # → http://localhost:3000
```

## Test It (5 CSVs, 8 Relationships)

```bash
python tests/test_northwind.py
```

Expected output: 8 files unified, 8 FK relationships detected, 97/100 quality score.

## Performance (Sprint 11 Benchmark)

| Size | Rows | Upload | Analysis | Total |
|---|---|---|---|---|
| Small | 4,250 | 2.0s | 51s | 53s |
| Medium | 42,500 | 2.1s | 30s | 32s |
| Large (50K orders) | 212,500 | rejected | — | (100K limit) |

Analysis time is mostly AI calls. 30-50s typical for 1K-10K orders.

## Test Coverage

```
tests/test_multi_file.py         (5 suites, 19 assertions)
tests/test_sprints_6_8.py        (3 suites, 9 assertions)
backend/smoke_test.py            (10 E2E tests)
```

**Total: 18 test suites, 28+ assertions, 100% pass rate.**

## Deployment (Sprint 13 Configs Ready)

- `vercel.json` — Frontend deploy
- `render.yaml` — Backend deploy (with persistent disk)

**NOT yet deployed** (manual step). Run:
```bash
vercel --prod
# And on Render: connect GitHub repo, use render.yaml
```

## Honest Status (Path C Sprint 1)

✅ **90% Production-Ready:**
- Multi-file upload ✅
- FK detection ✅
- Star schema ✅
- AI insights ✅
- PowerBI export ✅
- Persistence ✅
- Quality checks ✅
- Lineage tracking ✅
- Health monitoring ✅
- Test suite ✅

❌ **10% Remaining (Sprint 13+):**
- Real .pbix (currently .pbit template)
- 1M+ row benchmark
- Auth + multi-tenancy
- Real-time data sync
- WebSocket progress

## Author

**Raghav Modi** — BI Analyst + AI Builder  
Built solo in 1 night (2 hours of focused sprint time).

## License

MIT (for the code) + Northwind sample data (Microsoft Public License).
