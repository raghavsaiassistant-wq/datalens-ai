# DataLens AI — Handoff & Continuation Guide

> **Last session:** 2026-07-14 12:48 PM IST
> **What was built:** 15 sprints, ~3,500 lines, 13+ git commits
> **Why this handoff:** Sir is pausing the project to focus on job search. We will resume building after a job is landed.
> **Where to start:** This folder.

---

## 📁 Folder Structure

```
D:/Datalens.ai/datalens-ai/
├── backend/                    # Flask + AI pipeline
│   ├── app.py                  # 31 routes
│   ├── ai/                     # 19 AI modules
│   │   ├── multi_file.py       # Sprint 1-5 (FK detection, star schema)
│   │   ├── multi_file_store.py # Sprint 6 (persistence)
│   │   ├── data_quality.py     # Sprint 7
│   │   ├── lineage.py          # Sprint 8
│   │   ├── hardening.py        # Sprint 12 (circuit breaker, validators)
│   │   └── ... 14 more
│   ├── parsers/                # CSV, Excel, JSON, SQL, PDF, Image
│   ├── static/                 # dashboard.html, er-diagram.html
│   └── utils/                  # data_profiler, session_store, job_store
├── tests/                      # 50+ assertions, 3/3 suites passing
├── docs/                       # DEMO_SCRIPT.md
├── handoff/                    # 👈 YOU ARE HERE
│   ├── README.md               # this file
│   ├── CURRENT_STATUS.md       # what works, what doesn't
│   ├── FUTURE_ROADMAP.md       # 15+ sprints planned
│   ├── sprints/                # per-sprint notes (what + why)
│   │   ├── sprint-01-to-05.md  # multi-file MVP
│   │   ├── sprint-06-to-08.md  # persistence + quality + lineage
│   │   ├── sprint-09-to-12.md  # real data + ER + perf + hardening
│   │   ├── sprint-13-to-14.md  # deploy configs + docs
│   │   └── sprint-15.md        # code quality cleanup
│   ├── screenshots/
│   │   ├── er_diagram_sprint10.png  # 8-table Mermaid diagram
│   │   └── northwind_final.png      # full dashboard with real data
│   └── test-data/
│       ├── multi_test_sprint6c.log
│       └── benchmark.log
├── README.md
├── vercel.json
├── render.yaml
└── .gitignore
```

---

## 🚀 Resume From Here

### Step 1: Verify environment
```bash
cd D:/Datalens.ai/datalens-ai
python -m ruff check backend/        # 0 issues expected
python tests/test_multi_file.py      # ALL PASSED
python tests/test_sprints_6_8.py     # ALL PASSED
python tests/test_sprint_12.py       # ALL PASSED
```

### Step 2: Start the server
```bash
cd D:/Datalens.ai/datalens-ai/backend
python app.py
# Health: http://localhost:5000/api/health
# Multi:  http://localhost:5000/api/multi/health
```

### Step 3: Test with real data
```bash
# Use the Northwind CSVs in tests/ (or upload your own 2-10 related files)
# Go to http://localhost:5000/static/dashboard.html
# Upload 2+ CSVs → get unified dashboard
```

### Step 4: Read what's next
- `handoff/CURRENT_STATUS.md` — what works, what doesn't, what's blocked
- `handoff/FUTURE_ROADMAP.md` — 15+ sprints waiting
- `handoff/sprints/` — what each sprint did

---

## 🐴 The Ponytail Way

This project follows **Ponytail philosophy** (see `~/.hermes/skills/ponytail/`):

- ✅ **Multi-model orchestration** — Kimi (author) + GLM (refiner) + minimax-m3 (scorer)
- ✅ **Different labs** — vendor diversity on purpose
- ✅ **Plan-critique-refine-code** — never skip a step
- ✅ **No Claude, no shortcuts** — only what's been tested

Every new sprint should:
1. Plan (1-2 lines: what + why)
2. Critique (will it break X?)
3. Refine (what's the simpler way?)
4. Code
5. Test
6. Commit + push

---

## 🔐 Critical Context (do not lose)

| Item | Value |
|---|---|
| GitHub repo | `github.com/raghavsaiassistant-wq/datalens-ai` |
| Branch | `ollama-migration` |
| Models | Kimi K2.7, GLM 5.2, minimax-m3, gpt-oss-120b (4 roles) |
| Ollama | Cloud, Pro $20/mo, 3 concurrent |
| Resume | `C:\Users\modir\Downloads\Resume.pdf` |
| Telegram bot | `jamijam`, chat_id `7141439282` |
| `.env` | `C:\Users\modir\AppData\Local\hermes\.env` |
| 2captcha key | NOT in .env (add when needed) |
| Vercel | NOT redeployed (Sprint 16+ work) |
| Render | NOT redeployed (Sprint 16+ work) |

---

## 💼 Job Search Reminders

These are still pending in `C:\Users\modir\AppData\Local\hermes\jobs\`:
- **MasterCard** — 1-day deadline was 2026-07-13 (likely expired, check)
- **BlackRock** — final submit, Sir to do manually
- **Qatar Airways** — Taleo login needed
- **S&P Global** — applied 2026-07-13

**Once a job is landed, the agent resumes DataLens from Sprint 16.**

---

*Last updated: 2026-07-14 12:48 PM by James*
