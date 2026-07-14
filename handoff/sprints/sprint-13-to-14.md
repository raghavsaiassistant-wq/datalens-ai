# Sprints 13-14: Deploy Configs + Documentation

**When:** 2026-07-14 late night (15 min)
**Why:** Code without deploy story = hobby project. Code with configs = production-ready.

---

## Sprint 13: Vercel + Render configs (NOT deployed)

**Files:** `vercel.json`, `render.yaml`

### What
- `vercel.json`: Vite static build, route to `/dist`
- `render.yaml`: Python web service, free plan, health check on `/api/health`
- Both ready to deploy — just need `vercel --prod` and `git push render main`

### Why
- Sir paused redeploy ("Extended deadline to 4 AM and apart from the redeploy complete all the things")
- But configs should be ready for the day he wants to push

### Lessons
- Render free tier: 750 hrs/mo, sleeps after 15 min inactivity. Cold start = 30-60s.
- Vercel free tier: 100GB bandwidth, fast CDN. Perfect for static React.

### What's needed to deploy
1. Vercel: `vercel login`, `vercel link`, `vercel env add VITE_API_URL`, `vercel --prod`
2. Render: `render.yaml` auto-detected if repo connected, just click "Apply"

---

## Sprint 14: README + demo video script

**Files:** `README.md` (152 lines), `docs/DEMO_SCRIPT.md` (59 lines)

### What
- `README.md`: pitch, features, quickstart, architecture, roadmap
- `DEMO_SCRIPT.md`: 2-minute screen-by-screen demo narration

### Why
- Recruiter's first question: "What is this?" README answers in 30 sec.
- "Show me it working." Demo script answers in 2 min.

### Lessons
- The README pitch is "Drop files. Get a unified dashboard with auto-detected relationships, AI insights, and PowerBI exports."
- 30 seconds, 3 actions, 3 outputs. That's the entire value prop.

### Files
- `README.md` — public-facing
- `docs/DEMO_SCRIPT.md` — for screencast

---

*Total Sprints 13-14: 2 commits, ~210 lines, 4 config/doc files.*
*Ready to deploy. Ready to demo. Just need Sir's go.*
