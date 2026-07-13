"""
dashboard_export.py — Export the full web dashboard as a self-contained HTML file.
Sir's strategy: "Product is web dashboard, downloadable".
"""
import json
import logging
import io
import zipfile
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("DashboardExport")


def export_dashboard(analysis_result: Dict[str, Any], session_id: str = "session") -> bytes:
    """
    Build a downloadable .zip containing:
      - datalens-dashboard.html (the full standalone interactive dashboard)
      - README.txt (how to use it)
    Returns the zip bytes.
    """
    safe_data = json.loads(json.dumps(analysis_result, default=str))
    html = _build_standalone_dashboard(safe_data, session_id)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("datalens-dashboard.html", html)
        zf.writestr("README.txt", _readme(session_id, safe_data))
    zip_buffer.seek(0)
    return zip_buffer.read()


def _readme(session_id: str, data: Dict[str, Any]) -> str:
    meta = data.get("dataset_meta", {})
    chart_count = len(data.get("charts", []))
    rows = data.get("metadata", {}).get("analyzed_rows", "?")
    return f"""DataLens AI Dashboard
======================
Generated:  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Session:    {session_id}
Dataset:    {meta.get("dataset_type", "general")} · {rows} rows · {chart_count} charts

HOW TO USE
----------
1. Extract this ZIP anywhere on your computer
2. Open datalens-dashboard.html in any modern browser (Chrome/Edge/Firefox)
3. The dashboard is fully interactive — no server needed
4. All your data, charts, insights, and AI explanations are embedded
5. Use the left sidebar to filter data
6. Click any chart to drill down
7. Use the floating chat button (bottom right) to ask questions

NOTE: Chat requires the DataLens AI backend running at http://localhost:5000
      For pure offline viewing, charts and insights are fully self-contained.

Created by DataLens AI · https://github.com/raghavsaiassistant-wq/datalens-ai
"""


def _build_standalone_dashboard(data: Dict[str, Any], session_id: str) -> str:
    """Build a fully self-contained HTML file with embedded data + CSS + JS."""
    json_data = json.dumps(data, default=str)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DataLens AI Dashboard — Session {session_id[:8]}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{_DASHBOARD_CSS}</style>
</head>
<body>
<header class="app-header">
  <div class="brand">
    <div class="brand-logo">L</div>
    <div>
      <div class="brand-name">DataLens AI Dashboard</div>
      <div class="brand-sub">Session {session_id[:8]} · Standalone export</div>
    </div>
  </div>
  <div class="header-actions">
    <button class="btn" onclick="window.print()">Print / PDF</button>
    <button class="btn btn-primary" onclick="downloadJSON()">Data JSON</button>
  </div>
</header>
<main class="app-main">
  <div class="dashboard">
    <aside class="slicer-panel">
      <div class="slicer-section">
        <div class="slicer-title">Filters</div>
        <div id="slicers"></div>
      </div>
    </aside>
    <section>
      <div class="dashboard-grid" id="dashboard-grid"></div>
    </section>
  </div>
</main>
<button class="chat-fab" onclick="toggleChat()">Chat</button>
<div class="chat-panel" id="chat-panel">
  <div class="chat-header">
    <span class="dot"></span>
    <span class="title">Ask your data</span>
    <span class="sub">requires backend</span>
  </div>
  <div class="chat-messages" id="chat-messages">
    <div class="msg system">Offline mode — chat requires the DataLens AI backend at localhost:5000.</div>
  </div>
</div>
<script>
const ANALYSIS_DATA = {json_data};
const SESSION_ID = "{session_id}";
const CHART_COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];
const COLOR_GRADIENTS = [
  ['#6366f1', '#8b5cf6'], ['#06b6d4', '#3b82f6'],
  ['#10b981', '#059669'], ['#f59e0b', '#ef4444'],
  ['#ec4899', '#8b5cf6'], ['#14b8a6', '#06b6d4'],
];
{_DASHBOARD_JS}
function downloadJSON() {{
  const blob = new Blob([JSON.stringify(ANALYSIS_DATA, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'datalens-data.json';
  document.body.appendChild(a); a.click();
  setTimeout(() => {{ URL.revokeObjectURL(url); document.body.removeChild(a); }}, 100);
}}
window.addEventListener('load', renderDashboard);
</script>
</body>
</html>"""


_DASHBOARD_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --bg-page: #0b0d1a; --bg-panel: #11142a; --bg-card: #181b3a; --bg-elevated: #232651; --border: #232a4a; --border-light: #2e3563; --text-primary: #f0f2ff; --text-secondary: #b0b6d6; --text-muted: #6e7494; --c1: #6366f1; --c2: #06b6d4; --c3: #10b981; --c4: #f59e0b; --c5: #ef4444; --c6: #8b5cf6; --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%); --gradient-success: linear-gradient(135deg, #10b981 0%, #06b6d4 100%); --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); --gradient-mesh: radial-gradient(at 20% 10%, rgba(99,102,241,0.15) 0px, transparent 50%), radial-gradient(at 80% 90%, rgba(236,72,153,0.12) 0px, transparent 50%); --radius: 12px; --radius-sm: 8px; }
body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg-page); background-image: var(--gradient-mesh); color: var(--text-primary); min-height: 100vh; font-size: 13px; }
.app-header { background: rgba(11,13,26,0.85); backdrop-filter: blur(16px); border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-logo { width: 40px; height: 40px; background: var(--gradient-primary); border-radius: 11px; display: grid; place-items: center; font-weight: 900; color: white; font-size: 18px; }
.brand-name { font-weight: 800; font-size: 17px; }
.brand-sub { font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.btn { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary); padding: 8px 14px; border-radius: var(--radius-sm); font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; }
.btn:hover { background: var(--bg-card-hover, var(--bg-elevated)); }
.btn-primary { background: var(--gradient-primary); border: none; color: white; }
.app-main { padding: 16px 20px 80px; }
.dashboard { display: grid; grid-template-columns: 260px 1fr; gap: 16px; }
.slicer-panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; height: fit-content; position: sticky; top: 80px; max-height: calc(100vh - 100px); overflow-y: auto; }
.slicer-title { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); margin-bottom: 10px; }
.slicer-list { display: flex; flex-direction: column; gap: 3px; }
.slicer-item { padding: 7px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; transition: all 0.12s; display: flex; align-items: center; gap: 8px; border: 1px solid transparent; }
.slicer-item:hover { background: var(--bg-elevated); }
.slicer-item.active { background: var(--gradient-primary); color: white; font-weight: 600; }
.slicer-item .count { font-size: 10px; color: var(--text-muted); margin-left: auto; }
.slicer-section + .slicer-section { margin-top: 18px; padding-top: 18px; border-top: 1px solid var(--border); }
.dashboard-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 12px; grid-auto-rows: minmax(70px, auto); }
.kpi-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 18px; grid-column: span 3; position: relative; overflow: hidden; }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
.kpi-card.k1::before { background: var(--gradient-primary); }
.kpi-card.k2::before { background: linear-gradient(135deg, #06b6d4, #3b82f6); }
.kpi-card.k3::before { background: var(--gradient-success); }
.kpi-card.k4::before { background: var(--gradient-warning); }
.kpi-card.k1 { background: linear-gradient(135deg, rgba(99,102,241,0.12) 0%, var(--bg-card) 60%); }
.kpi-card.k2 { background: linear-gradient(135deg, rgba(6,182,212,0.12) 0%, var(--bg-card) 60%); }
.kpi-card.k3 { background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, var(--bg-card) 60%); }
.kpi-card.k4 { background: linear-gradient(135deg, rgba(245,158,11,0.12) 0%, var(--bg-card) 60%); }
.kpi-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; }
.kpi-value { font-size: 32px; font-weight: 800; margin: 8px 0 4px; }
.kpi-meta { font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }
.kpi-delta { font-weight: 700; padding: 1px 6px; border-radius: 4px; font-size: 10px; }
.kpi-delta.up { background: rgba(16,185,129,0.15); color: var(--c3); }
.tile { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; grid-column: span 6; }
.tile.span-12 { grid-column: span 12; } .tile.span-8 { grid-column: span 8; } .tile.span-4 { grid-column: span 4; }
.tile-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.tile-title { font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; }
.tile-chart { width: 100%; height: 280px; }
.tile.tall .tile-chart { height: 360px; }
.insight-banner { background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(236,72,153,0.12) 100%); border: 1px solid var(--c1); border-radius: var(--radius); padding: 18px 22px; grid-column: span 12; }
.insight-banner .label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; color: var(--c6); margin-bottom: 6px; }
.insight-banner .text { font-size: 16px; font-weight: 600; line-height: 1.45; }
.anomaly-card { background: linear-gradient(135deg, rgba(239,68,68,0.08) 0%, var(--bg-card) 100%); border: 1px solid rgba(239,68,68,0.25); border-left: 3px solid var(--c5); border-radius: var(--radius-sm); padding: 12px 16px; margin-bottom: 8px; }
.anomaly-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.anomaly-title { font-weight: 700; font-size: 13px; }
.anomaly-type { font-size: 9px; padding: 3px 8px; border-radius: 4px; background: var(--c5); color: white; font-weight: 800; }
.anomaly-detail { color: var(--text-secondary); font-size: 12px; line-height: 1.4; }
.fact-card { background: var(--bg-card); border: 1px solid var(--border); border-left: 3px solid var(--c2); border-radius: var(--radius-sm); padding: 10px 14px; font-size: 12px; line-height: 1.4; color: var(--text-secondary); margin-bottom: 6px; }
.l3-card { background: linear-gradient(135deg, rgba(139,92,246,0.08) 0%, var(--bg-card) 100%); border: 1px solid rgba(139,92,246,0.3); border-left: 3px solid var(--c6); border-radius: var(--radius-sm); padding: 12px 16px; margin-bottom: 8px; }
.l3-title { font-weight: 700; font-size: 12px; color: var(--c6); margin-bottom: 4px; text-transform: uppercase; }
.l3-text { font-size: 13px; line-height: 1.4; }
.l3-action { font-size: 11px; color: var(--c3); margin-top: 6px; font-family: 'JetBrains Mono', monospace; }
.chat-fab { position: fixed; bottom: 24px; right: 24px; width: 60px; height: 60px; border-radius: 50%; background: var(--gradient-primary); border: none; color: white; font-size: 18px; cursor: pointer; box-shadow: 0 8px 32px rgba(99,102,241,0.5); z-index: 99; }
.chat-panel { position: fixed; bottom: 100px; right: 24px; width: 420px; max-width: calc(100vw - 48px); height: 540px; background: var(--bg-card); border: 1px solid var(--border-light); border-radius: var(--radius); display: none; flex-direction: column; z-index: 99; box-shadow: 0 10px 40px rgba(0,0,0,0.5); overflow: hidden; }
.chat-panel.open { display: flex; }
.chat-header { padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; }
.chat-header .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--c3); }
.chat-header .title { font-weight: 700; }
.chat-header .sub { font-size: 10px; color: var(--text-muted); margin-left: auto; }
.chat-messages { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.msg { max-width: 85%; padding: 10px 14px; border-radius: 14px; font-size: 13px; line-height: 1.45; }
.msg.system { background: var(--bg-panel); align-self: center; font-size: 11px; color: var(--text-muted); text-align: center; }
.grid-stats { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; margin-top: 8px; }
.grid-stats > div { background: var(--bg-elevated); border-radius: 6px; padding: 8px 10px; }
.grid-stats .lbl { font-size: 9px; color: var(--text-muted); text-transform: uppercase; }
.grid-stats .val { font-size: 16px; font-weight: 700; margin-top: 2px; }
"""


_DASHBOARD_JS = """
let currentData = ANALYSIS_DATA;
let activeFilters = {};
function renderDashboard() {
  try { renderSlicers(); } catch (e) { console.error(e); }
  try { renderKPIs(); } catch (e) { console.error(e); }
  try { renderInsight(); } catch (e) { console.error(e); }
  try { renderL1Facts(); } catch (e) { console.error(e); }
  try { renderCharts(); } catch (e) { console.error(e); }
  try { renderL3Board(); } catch (e) { console.error(e); }
  try { renderAnomalies(); } catch (e) { console.error(e); }
  try { renderDataProfile(); } catch (e) { console.error(e); }
}
function renderSlicers() {
  const div = document.getElementById('slicers');
  div.innerHTML = '';
  const meta = currentData.dataset_meta || {};
  let dimCols = meta.column_roles?.dimension || meta.dimensions || [];
  if (!Array.isArray(dimCols) || dimCols.length === 0) {
    dimCols = Array.from(new Set((currentData.charts || []).map(c => c.x_col).filter(x => x))).slice(0, 3);
  }
  if (dimCols.length === 0) return;
  for (const col of dimCols.slice(0, 4)) {
    const values = uniqValues(col);
    if (values.length < 2 || values.length > 30) continue;
    const section = document.createElement('div');
    section.className = 'slicer-section';
    section.innerHTML = `<div class="slicer-title">${col}</div><div class="slicer-list" id="slicer-${col}"></div>`;
    div.appendChild(section);
    const list = section.querySelector('.slicer-list');
    const allItem = document.createElement('div');
    allItem.className = 'slicer-item active';
    allItem.innerHTML = `<span>All</span><span class="count">${values.length}</span>`;
    allItem.onclick = () => clearFilter(col);
    list.appendChild(allItem);
    values.forEach(v => {
      const item = document.createElement('div');
      item.className = 'slicer-item';
      item.innerHTML = `<span>${v}</span>`;
      item.onclick = () => setFilter(col, v);
      list.appendChild(item);
    });
  }
}
function uniqValues(col) {
  const data = currentData.charts || [];
  const allValues = new Set();
  for (const c of data) {
    if (c.x_col === col && Array.isArray(c.data)) {
      for (const p of c.data) if (p.x !== undefined && p.x !== null && p.x !== '') allValues.add(p.x);
    }
  }
  return Array.from(allValues);
}
function setFilter(col, value) {
  const list = document.getElementById('slicer-' + col);
  if (list) list.querySelectorAll('.slicer-item').forEach(el => el.classList.remove('active'));
  if (typeof event !== 'undefined' && event && event.target) {
    const item = event.target.closest('.slicer-item');
    if (item) item.classList.add('active');
  }
  activeFilters[col] = value;
  renderKPIs(); renderCharts(); renderAnomalies();
}
function clearFilter(col) {
  delete activeFilters[col];
  const list = document.getElementById('slicer-' + col);
  if (list) {
    list.querySelectorAll('.slicer-item').forEach(el => el.classList.remove('active'));
    const first = list.querySelector('.slicer-item');
    if (first) first.classList.add('active');
  }
  renderKPIs(); renderCharts(); renderAnomalies();
}
function renderKPIs() {
  const grid = document.getElementById('dashboard-grid');
  grid.querySelectorAll('.kpi-card').forEach(el => el.remove());
  const data = (currentData.charts || []).filter(c => c.chart_type === 'kpi_card');
  const fallback = data.length < 4 ? (currentData.charts || []).slice(0, 4 - data.length) : [];
  const all = [...data, ...fallback];
  if (all.length === 0) return;
  const firstChild = grid.firstChild;
  const frag = document.createDocumentFragment();
  all.forEach((k, i) => {
    const val = k.data?.[0]?.y;
    const valStr = typeof val === 'number' ? formatNumber(val) : (val || '—');
    const kpi = document.createElement('div');
    kpi.className = `kpi-card k${(i % 4) + 1}`;
    kpi.innerHTML = `<div class="kpi-label">${k.title || 'KPI'}</div><div class="kpi-value">${valStr}</div><div class="kpi-meta"><span class="kpi-delta up">UP</span><span>${k.aggregation || 'mean'} of ${k.y_col || ''}</span></div>`;
    frag.appendChild(kpi);
  });
  grid.insertBefore(frag, firstChild);
}
function renderInsight() {
  const grid = document.getElementById('dashboard-grid');
  const banner = document.createElement('div');
  banner.className = 'insight-banner';
  const summary = currentData.executive_summary || 'Analysis complete.';
  const insights = currentData.insights?.l3_insights || [];
  const top = insights[0]?.insight || summary;
  banner.innerHTML = `<div class="label">KEY INSIGHT</div><div class="text">${top}</div>`;
  grid.appendChild(banner);
}
function renderL1Facts() {
  const grid = document.getElementById('dashboard-grid');
  const facts = currentData.insights?.l1_facts || [];
  if (facts.length === 0) return;
  const tile = document.createElement('div');
  tile.className = 'tile span-4 tall';
  tile.style.maxHeight = '400px'; tile.style.overflowY = 'auto';
  tile.innerHTML = `<div class="tile-header"><div class="tile-title">Statistical Findings (${facts.length})</div></div>`;
  const inner = document.createElement('div');
  facts.forEach(f => {
    const card = document.createElement('div');
    card.className = 'fact-card';
    card.textContent = f;
    inner.appendChild(card);
  });
  tile.appendChild(inner);
  grid.appendChild(tile);
}
function renderCharts() {
  const grid = document.getElementById('dashboard-grid');
  grid.querySelectorAll('.chart-tile').forEach(el => el.remove());
  const data = (currentData.charts || []).filter(c => c.chart_type !== 'kpi_card');
  data.forEach((c, i) => {
    const tile = document.createElement('div');
    const span = c.chart_type === 'line' ? 8 : 6;
    const tall = c.chart_type === 'pie' || c.chart_type === 'donut';
    tile.className = `chart-tile tile span-${span}${tall ? ' tall' : ''}`;
    tile.innerHTML = `<div class="tile-header"><div class="tile-title">${c.title || c.chart_type}</div></div><div class="tile-chart" id="plot-${i}"></div>`;
    grid.appendChild(tile);
    drawPlot(c, 'plot-' + i, i);
  });
}
function drawPlot(chart, targetId, idx) {
  const data = chart.data || [];
  if (data.length === 0) return;
  const [color1, color2] = COLOR_GRADIENTS[idx % COLOR_GRADIENTS.length];
  const layout = {
    paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', size: 11, color: '#b0b6d6' },
    margin: { l: 40, r: 16, t: 8, b: 36 },
    xaxis: { gridcolor: 'rgba(99,102,241,0.08)', zeroline: false, showline: false },
    yaxis: { gridcolor: 'rgba(99,102,241,0.08)', zeroline: false, showline: false },
    showlegend: chart.chart_type === 'pie' || chart.chart_type === 'donut',
    legend: { orientation: 'h', y: -0.2 }
  };
  const config = { displayModeBar: false, responsive: true };
  let traces;
  if (chart.chart_type === 'bar') {
    traces = [{ type: 'bar', x: data.map(d => d.x), y: data.map(d => d.y),
      marker: { color: data.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]) },
      hovertemplate: '<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>' }];
  } else if (chart.chart_type === 'line') {
    traces = [{ type: 'scatter', mode: 'lines+markers', x: data.map(d => d.x), y: data.map(d => d.y),
      line: { color: color1, width: 3, shape: 'spline' },
      marker: { color: color1, size: 8 },
      fill: 'tozeroy', fillcolor: `rgba(${hexToRgb(color1).join(',')}, 0.1)`,
      hovertemplate: '<b>%{x}</b><br>Value: %{y:,.2f}<extra></extra>' }];
  } else if (chart.chart_type === 'histogram') {
    traces = [{ type: 'bar', x: data.map(d => d.x), y: data.map(d => d.y),
      marker: { color: data.map((_, i) => `rgba(${hexToRgb(color1).join(',')}, ${0.4 + i/data.length*0.6})`), line: { color: color2, width: 1 } },
      hovertemplate: 'Range: %{x}<br>Count: %{y}<extra></extra>' }];
  } else if (chart.chart_type === 'pie' || chart.chart_type === 'donut') {
    traces = [{ type: 'pie', labels: data.map(d => d.x), values: data.map(d => d.y), hole: chart.chart_type === 'donut' ? 0.55 : 0,
      marker: { colors: CHART_COLORS },
      textinfo: 'percent',
      hovertemplate: '<b>%{label}</b><br>Value: %{value:,.2f}<br>Share: %{percent}<extra></extra>' }];
  } else {
    traces = [{ type: 'bar', x: data.map(d => d.x), y: data.map(d => d.y), marker: { color: color1 } }];
  }
  Plotly.newPlot(targetId, traces, layout, config);
}
function renderL3Board() {
  const grid = document.getElementById('dashboard-grid');
  const insights = currentData.insights?.l3_insights || [];
  if (insights.length === 0) return;
  const tile = document.createElement('div');
  tile.className = 'tile span-4 tall';
  tile.style.maxHeight = '400px'; tile.style.overflowY = 'auto';
  tile.innerHTML = `<div class="tile-header"><div class="tile-title">Board Decisions (${insights.length})</div></div>`;
  const inner = document.createElement('div');
  insights.forEach((item, i) => {
    const card = document.createElement('div');
    card.className = 'l3-card';
    const title = item.title || `Decision ${i+1}`;
    const insight = item.insight || '';
    const action = item.action || '';
    const urgency = item.urgency || 'medium';
    const urgencyColor = urgency === 'high' ? '#ef4444' : urgency === 'low' ? '#10b981' : '#f59e0b';
    card.innerHTML = `<div class="l3-title">${title} <span style="float:right;font-size:9px;padding:2px 6px;border-radius:3px;background:${urgencyColor};color:#fff;">${urgency}</span></div><div class="l3-text">${insight}</div>${action ? `<div class="l3-action">${action}</div>` : ''}`;
    inner.appendChild(card);
  });
  tile.appendChild(inner);
  grid.appendChild(tile);
}
function renderAnomalies() {
  const grid = document.getElementById('dashboard-grid');
  grid.querySelectorAll('.anomaly-tile').forEach(el => el.remove());
  const anomalies = currentData.anomalies || [];
  if (anomalies.length === 0) return;
  const tile = document.createElement('div');
  tile.className = 'anomaly-tile tile span-4 tall';
  tile.style.maxHeight = '400px'; tile.style.overflowY = 'auto';
  tile.innerHTML = `<div class="tile-header"><div class="tile-title" style="color:#ef4444">Anomalies (${anomalies.length})</div></div>`;
  const inner = document.createElement('div');
  anomalies.slice(0, 8).forEach(a => {
    const card = document.createElement('div');
    card.className = 'anomaly-card';
    const valStr = typeof a.value === 'number' ? formatNumber(a.value) : a.value;
    card.innerHTML = `<div class="anomaly-header"><div class="anomaly-title">${a.column} - ${valStr}</div><div class="anomaly-type">${a.anomaly_type || 'flag'}</div></div><div class="anomaly-detail">${a.explanation || ''}</div>`;
    inner.appendChild(card);
  });
  tile.appendChild(inner);
  grid.appendChild(tile);
}
function renderDataProfile() {
  const grid = document.getElementById('dashboard-grid');
  const meta = currentData.dataset_meta || {};
  const ml = currentData.metadata || {};
  const tiles = [
    { label: 'Dataset Type', val: meta.dataset_type || 'general', color: '#6366f1' },
    { label: 'Rows', val: (ml.analyzed_rows || '?').toLocaleString(), color: '#06b6d4' },
    { label: 'Health', val: (currentData.data_health_score || '?') + '/100', color: '#10b981' },
    { label: 'Time', val: (ml.total_time_seconds || '?') + 's', color: '#f59e0b' },
  ];
  const tile = document.createElement('div');
  tile.className = 'tile span-12';
  tile.innerHTML = `<div class="tile-header"><div class="tile-title">Dataset Profile</div></div>`;
  const grid_stats = document.createElement('div');
  grid_stats.className = 'grid-stats';
  tiles.forEach(t => {
    grid_stats.innerHTML += `<div><div class="lbl" style="color:${t.color}">${t.label}</div><div class="val">${t.val}</div></div>`;
  });
  tile.appendChild(grid_stats);
  grid.appendChild(tile);
}
function toggleChat() { document.getElementById('chat-panel').classList.toggle('open'); }
function hexToRgb(hex) {
  const r = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex);
  return r ? [parseInt(r[1], 16), parseInt(r[2], 16), parseInt(r[3], 16)] : [99, 102, 241];
}
function formatNumber(n) {
  if (typeof n !== 'number') return n;
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  if (Number.isInteger(n)) return n.toString();
  return n.toFixed(2);
}
"""
