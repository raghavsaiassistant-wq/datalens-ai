# DataLens AI — Demo Video Script (2 minutes)

## Scene 1: Setup (10s)
- Screen: blank terminal
- VO: "What if you could drop 10 related files and get a unified dashboard?"
- Type: `python backend/app.py`
- Show: backend starts on port 5000

## Scene 2: Files (15s)
- Show: 5 CSVs in a folder (customers, orders, products, etc.)
- VO: "These are Northwind data. Real relationships, not synthetic."

## Scene 3: Upload (20s)
- Open: http://localhost:5000/dashboard
- Drag all 5 files into upload zone
- Show: file list appears with chips
- Click: "Upload"
- Watch: progress bar (parse → FK detect → AI insights → done)

## Scene 4: Dashboard (40s)
- Show: "5 source files unified via 8 auto-detected relationships" badge
- Show: KPI cards ($1.28M revenue, 256 avg order, etc.)
- Scroll: revenue by region bar chart
- Show: AI Insights banner with specific dollar amounts
- Show: Top performers table
- Hover: anomalies (high concentration, late spikes)

## Scene 5: ER Diagram (15s)
- Click: "View Schema" button
- Show: rendered Mermaid diagram with all 8 tables
- Highlight: relationships with cardinality (one-to-many, etc.)
- VO: "All relationships auto-detected. No manual schema mapping."

## Scene 6: Drilldown (10s)
- Click: on a chart segment
- Show: drilldown panel with related records
- VO: "Cross-file drilldown. One click, instant context."

## Scene 7: Export (10s)
- Click: "Export" → "PowerBI"
- Show: .pbit file downloads
- VO: "Open it in PowerBI Desktop. It's a real template with data model."

## Scene 8: Outro (10s)
- Show: GitHub repo
- VO: "Open source. Free. Built solo in one night. DataLens AI."

---

## Sir's Quick Demo (no recording, just talking points):

1. **"I built a tool that detects foreign keys across 10 files automatically"** ← show the 5 CSVs → 1 dashboard
2. **"It uses AI (Kimi K2.7, 1T params) to find insights"** ← show the executive summary mentioning specific revenue numbers
3. **"PowerBI users get a .pbit file with the joined data model"** ← show the export
4. **"All running on Ollama Cloud for $20/mo"** ← show the cost
5. **"100% tested, open source on GitHub"** ← show the test suite passing

**Use this in: interview, portfolio site, LinkedIn post, cold email.**
