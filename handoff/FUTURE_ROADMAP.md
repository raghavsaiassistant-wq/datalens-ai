# DataLens AI — Future Roadmap (Sprint 16+)

> **Goal:** Transform the MVP into a commercial SaaS.
> **Path:** 16-week plan (Path C), 1 sprint = ~1-1.5 days work
> **Sprint 1-15 done. Starting from Sprint 16.**

---

## Phase 1: Refactor + Stability (Sprint 16-20)

### Sprint 16: Refactor `AnalysisPipeline.run` (E(39))
- **Why:** 39 cyclomatic complexity, 4 unmaintainable functions
- **What:** Extract `_analyze_schema`, `_analyze_quality`, `_analyze_insights`, `_anomaly_check` as separate methods
- **Test:** All existing tests still pass + 2 new tests for split functions
- **Time:** 45 min

### Sprint 17: Refactor `filter_session` (E(32))
- **Why:** 32-branch function, hard to test
- **What:** Split into `_filter_by_date`, `_filter_by_category`, `_filter_by_value`
- **Test:** 4 new tests for each filter function
- **Time:** 30 min

### Sprint 18: Refactor `SmartVizSelector._charts_experiment` (F(52))
- **Why:** 52 CC — the worst in the codebase
- **What:** Split into 4 chart type handlers
- **Test:** Verify each chart type still renders
- **Time:** 60 min

### Sprint 19: Refactor `pbix_real_export._ensure_sample` (C(15))
- **Why:** PowerBI export has hidden complexity
- **What:** Flatten nested loops, extract `_add_table`, `_add_measure`
- **Test:** Generated .pbit still opens in PowerBI
- **Time:** 30 min

### Sprint 20: Add `coverage.py` to measure line coverage
- **Why:** Tests pass but we don't know what % is covered
- **What:** `pip install coverage`, run `coverage run -m pytest`, target 70%
- **Test:** Coverage report shows 70%+ lines covered
- **Time:** 30 min

---

## Phase 2: Auth + Multi-Tenancy (Sprint 21-25)

### Sprint 21: Database layer (SQLite → Postgres-ready)
- **Why:** Job store, session store, user store need persistence
- **What:** SQLAlchemy models: User, Job, Session, FileMetadata
- **Test:** All in-memory stores replaced, restart-survives
- **Time:** 90 min

### Sprint 22: User signup + login (JWT)
- **Why:** Multi-tenant SaaS needs accounts
- **What:** `/api/auth/signup`, `/api/auth/login`, JWT middleware
- **Test:** 5 new tests: signup, login, bad password, expired token, refresh
- **Time:** 90 min

### Sprint 23: Per-user data isolation
- **Why:** Security — User A shouldn't see User B's data
- **What:** All queries filtered by `user_id`, middleware checks JWT
- **Test:** 3 new tests: cross-user access blocked
- **Time:** 60 min

### Sprint 24: Stripe integration (test mode)
- **Why:** Path C = commercial SaaS
- **What:** `/api/billing/create-checkout`, webhook for subscription
- **Test:** Stripe CLI mock, webhook handler test
- **Time:** 90 min
- **Blocker:** Stripe API keys needed (test mode OK)

### Sprint 25: Free/Pro tier limits
- **Why:** Stripe needs usage tiers
- **What:** Free = 100 analyses/month, Pro = unlimited
- **Test:** Limit enforcement, upgrade flow
- **Time:** 60 min

---

## Phase 3: Real-Time + Caching (Sprint 26-30)

### Sprint 26: WebSocket for live progress
- **Why:** Long AI calls need progress feedback
- **What:** SocketIO, emit `progress: 30%` events
- **Test:** Multi-file analysis streams progress to client
- **Time:** 90 min

### Sprint 27: Redis cache for repeated queries
- **Why:** Same dataset shouldn't re-call AI
- **What:** Cache by dataset hash, TTL 24h
- **Test:** Repeat query is 10x faster
- **Time:** 60 min
- **Blocker:** Redis instance needed (free tier OK)

### Sprint 28: Email notifications (SMTP)
- **Why:** "Your analysis is ready" emails
- **What:** SendGrid or SMTP, template system
- **Test:** Mock SMTP, verify email content
- **Time:** 60 min
- **Blocker:** API key needed

### Sprint 29: Background job queue (Celery)
- **Why:** Don't block HTTP thread on long jobs
- **What:** Celery + Redis, `/api/analyze` returns job_id immediately
- **Test:** Multiple parallel jobs, no thread starvation
- **Time:** 90 min

### Sprint 30: Rate limiting per user (not per IP)
- **Why:** Current rate limit is per IP, breaks shared offices
- **What:** Flask-Limiter with JWT user_id as key
- **Test:** Same user, different IPs, same limit
- **Time:** 30 min

---

## Phase 4: Polish (Sprint 31-40)

### Sprint 31: Dark mode toggle
### Sprint 32: Excel export (.xlsx)
### Sprint 33: PDF export (charts + tables)
### Sprint 34: Drag-drop file reordering
### Sprint 35: Keyboard shortcuts (Ctrl+U for upload)
### Sprint 36: i18n setup (en + hi-IN)
### Sprint 37: Onboarding tour (first-time user)
### Sprint 38: Empty states + loading skeletons
### Sprint 39: Mobile responsive (tablet first)
### Sprint 40: PWA + offline mode

---

## Phase 5: Production (Sprint 41-50)

### Sprint 41: Vercel redeploy (frontend)
### Sprint 42: Render redeploy (backend)
### Sprint 43: Custom domain + SSL
### Sprint 44: Sentry error monitoring
### Sprint 45: Logging aggregation (Loki or Datadog free)
### Sprint 46: Uptime monitoring (UptimeRobot free)
### Sprint 47: CDN for static assets
### Sprint 48: Performance audit (Lighthouse 90+)
### Sprint 49: SEO + landing page
### Sprint 50: Launch (ProductHunt, HN, Twitter)

---

## Phase 6: Growth (Sprint 51+)

### Sprint 51-60: User feedback iteration
### Sprint 61-70: Enterprise features (SSO, audit logs)
### Sprint 71-80: Mobile app (React Native)
### Sprint 81+: Scale (1M+ users)

---

## 🎯 Decision Tree: What To Build First

| Sir's priority | Start at |
|---|---|
| Get paying users fast | Sprint 24 (Stripe) |
| Get to 100 users | Sprint 26 (WebSocket) + 30 (rate limit) |
| Get acquired | Sprint 40-50 (production + launch) |
| Have fun / learn | Sprint 16-19 (refactors) |
| Make Sir hireable | Sprint 31-39 (polish for portfolio) |

---

## 💰 Cost Estimate (if running in production)

| Service | Free Tier | Paid |
|---|---|---|
| Vercel | 100GB bandwidth | $20/mo Pro |
| Render | 750 hrs/mo | $7/mo Starter |
| Ollama Pro | 3 concurrent | $20/mo |
| Postgres (Neon) | 0.5GB | $19/mo |
| Redis (Upstash) | 10K req/day | $10/mo |
| SendGrid | 100 emails/day | $20/mo |
| Stripe | — | 2.9% + 30¢ per tx |
| **Total** | **$0** | **$96/mo + tx fees** |

**Path C budget: <$100/mo for first 100 users, <$500/mo for 1K users.**

---

## 📊 Sprint Velocity Target

| Phase | Sprints | Time |
|---|--:|--:|
| Phase 1 (refactor) | 5 | 1 week |
| Phase 2 (auth) | 5 | 1 week |
| Phase 3 (real-time) | 5 | 1 week |
| Phase 4 (polish) | 10 | 2 weeks |
| Phase 5 (production) | 10 | 2 weeks |
| Phase 6 (growth) | ongoing | — |
| **Total to launch** | **35** | **~7 weeks** |

If Sir resumes full-time after a job, **35 sprints = 7 weeks to commercial launch.**

---

*This is the path. Pick the next sprint when ready.*
