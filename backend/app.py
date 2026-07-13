"""
app.py — DataLens AI · Ollama Cloud migration (2026-07-13)
Flask REST API: file drop → interactive dashboard + chat.
"""
import time
import os
import uuid
import logging
import re
import threading
import sys
import json
import asyncio
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from utils.file_router import FileRouter
from ai.pipeline import AnalysisPipeline
from ai.ollama_client import OllamaClient
from ai.prompts import QA_SYSTEM
from utils.session_store import SessionStore
from utils.job_store import JobStore
from ai.date_intelligence import DateIntelligence
from ai.filter_trigger import FilterTrigger
from utils.data_serializer import DataSerializer
from ai.hallucination_guard import HallucinationGuard
from ai.prompts import QA_SYSTEM as _QA_BASE  # legacy import (kept for back-compat)
from ai.dashboard_export import export_dashboard
from ai.pbix_real_export import build_pbix as build_real_pbix

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataLensAI")

# ── Flask app + middleware ───────────────────────────────────────────────────
app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=[], storage_uri="memory://")
job_store = JobStore()
JOB_TTL_SECONDS = 3600

# CORS — wildcard covers all Vercel preview formats (incl. -git- branch previews)
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "https://datalens-ai.vercel.app",
    "https://datalensai.vercel.app",
    "https://datalens-ai.onrender.com",
], supports_credentials=False)

CORS_ORIGIN_REGEX = r"https://datalens-?ai(-.*)?\.vercel\.app$"


@app.after_request
def add_cors_headers(response):
    """Match Vercel preview URLs (incl. -git-branch-name format)."""
    origin = request.headers.get("Origin", "")
    if origin and re.match(CORS_ORIGIN_REGEX, origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


# ── Config ───────────────────────────────────────────────────────────────────
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 25)) * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Singletons ──────────────────────────────────────────────────────────────
ollama = OllamaClient()
pipeline = AnalysisPipeline(ollama=ollama)
router = FileRouter()
session_store = SessionStore()
data_serializer = DataSerializer()

# In-memory preview cache (cleared per session, 5 min TTL)
_preview_cache = {}
_PREVIEW_TTL = 300


# ── Helpers ─────────────────────────────────────────────────────────────────
def _allowed_ext(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in router.get_supported_extensions()


def _serialize_response(obj):
    """JSON-safe serializer (handles pandas Timestamps, numpy, dataclasses)."""
    return json.loads(json.dumps(obj, default=str))


# ── Health ──────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "HEAD"])
def root():
    """Root: redirect to dashboard."""
    from flask import redirect
    return redirect("/dashboard", code=302)


@app.route("/preview", methods=["GET"])
def preview_page():
    """Design preview / status page showing what's being built."""
    from flask import send_from_directory
    return send_from_directory("static", "preview.html")


@app.route("/test", methods=["GET"])
def test_console():
    """Browser test console — see the full pipeline in action."""
    from flask import send_from_directory
    return send_from_directory("static", "test.html")


@app.route("/dashboard-figma", methods=["GET"])
def dashboard_figma():
    """New dashboard matching Figma 'Analytics Dashboard Community' style."""
    from flask import send_from_directory
    return send_from_directory("static", "dashboard-figma.html")


@app.route("/dashboard", methods=["GET"])
def dashboard_old():
    """Original dark dashboard (legacy)."""
    from flask import send_from_directory
    return send_from_directory("static", "dashboard.html")


@app.route("/dashboard-light", methods=["GET"])
def dashboard_light():
    """Sneat-style light dashboard (subagent built)."""
    from flask import send_from_directory
    return send_from_directory("static", "dashboard-light.html")


@app.route("/", methods=["GET", "HEAD"])
def root_index():
    """Root redirects to /dashboard."""
    from flask import redirect
    return redirect("/dashboard")


@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    """Sync health endpoint. Tests Ollama Cloud reachability (cached for 30s)."""
    global _health_cache_ts, _health_cache_result
    now = time.time()
    if now - _health_cache_ts > 30 or _health_cache_result is None:
        try:
            import asyncio
            _health_cache_result = asyncio.run(ollama.health())
        except Exception as e:
            logger.error(f"Health check error: {e}")
            _health_cache_result = False
        _health_cache_ts = now
    return jsonify({
        "status": "ok" if _health_cache_result else "degraded",
        "ollama_cloud": _health_cache_result,
        "version": "2.0.0-ollama",
        "models_registered": 4,
    }), 200 if _health_cache_result else 503


_health_cache_ts = 0
_health_cache_result = None


# ── /api/preview — NEW · <500ms, no LLM ───────────────────────────────────
@app.route("/api/preview", methods=["POST"])
def preview():
    """Fast file preview: rows, columns, types, 5 sample rows. No LLM."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file parameter"}), 400
    file = request.files["file"]
    if not file.filename or not _allowed_ext(file.filename):
        return jsonify({"success": False, "error": "Unsupported file type"}), 400
    try:
        file_id = uuid.uuid4().hex[:12]
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{secure_filename(file.filename)}")
        file.save(file_path)
        from parsers.csv_parser import CSVParser
        parser = CSVParser()  # Fast: only reads first 500 rows for preview
        profile = parser.parse(file_path, file.filename, max_rows=500)
        sample_records = profile.df.head(5).fillna("").astype(str).to_dict(orient="records")
        column_types = {col: str(profile.column_types.get(col, "unknown")) for col in profile.columns}
        preview_data = {
            "success": True,
            "file_id": file_id,
            "file_name": file.filename,
            "rows": profile.rows,
            "cols": profile.cols,
            "columns": profile.columns,
            "column_types": column_types,
            "kpi_columns": profile.kpi_columns[:10],
            "has_datetime": profile.has_datetime,
            "duplicates": profile.duplicates,
            "null_count": sum(profile.nulls.values()) if profile.nulls else 0,
            "sample": sample_records,
            "warnings": profile.warnings,
        }
        _preview_cache[file_id] = (file_path, time.time())
        return jsonify(_serialize_response(preview_data)), 200
    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ── /api/analyze — async via JobStore ───────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
@limiter.limit("5 per minute")
def analyze():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file parameter"}), 400
    file = request.files["file"]
    if not file.filename or not _allowed_ext(file.filename):
        return jsonify({"success": False, "error": "Unsupported file type"}), 400

    job_id = uuid.uuid4().hex
    file_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{secure_filename(file.filename)}")
    file.save(file_path)
    job_store.create(job_id, file.filename)

    def run_analysis():
        import asyncio
        async def _run():
            from parsers.csv_parser import CSVParser
            parser = CSVParser()
            try:
                job_store.update(job_id, status="processing", progress=1, message="📂 Parsing file...")
                profile = parser.parse(file_path, file.filename, max_rows=30000)
                job_store.update(job_id, progress=2, message="🔍 Classifying dataset...")
                result = await pipeline.run(
                    profile,
                    progress_callback=lambda s, m: job_store.update(job_id, progress=s, message=m)
                )
                session_store.save(job_id, result)
                job_store.update(job_id, status="completed", progress=6,
                                  message="✅ Analysis complete", result=result)
            except Exception as e:
                logger.error(f"Analysis failed for {job_id}: {e}", exc_info=True)
                job_store.update(job_id, status="failed", error=str(e))
            finally:
                try: os.remove(file_path)
                except: pass
        asyncio.run(_run())

    t = threading.Thread(target=run_analysis, daemon=True)
    t.start()
    return jsonify({"success": True, "job_id": job_id}), 202


# ── /api/status/<job_id> — poll endpoint ────────────────────────────────────
@app.route("/api/status/<job_id>", methods=["GET"])
def status(job_id):
    job = job_store.get(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    return jsonify(_serialize_response({
        "success": True,
        "job_id": job_id,
        "status": job.get("status", "processing"),
        "progress": job.get("progress", 1),
        "message": job.get("message", ""),
        "result": job.get("result") if job.get("status") == "completed" else None,
        "error": job.get("error"),
    }))


# ── /api/ask — chat with data (SSE streaming) ───────────────────────────────
@app.route("/api/ask", methods=["POST"])
def ask():
    """Chat with the analyzed data. Streams response tokens via SSE."""
    data = request.get_json()
    if not data or "session_id" not in data or "question" not in data:
        return jsonify({"success": False, "error": "Missing session_id or question"}), 400
    session_id = data["session_id"]
    question = data["question"]
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session expired or not found"}), 404

    # Build context from session insights
    insights = session.get("insights", {})
    charts = session.get("charts", [])
    warnings = session.get("warnings", [])
    meta = session.get("dataset_meta", {})

    context_lines = [
        f"Dataset type: {meta.get('dataset_type', 'general')}",
        f"Rows: {session.get('metadata', {}).get('analyzed_rows', '?')}",
        f"Columns: {len(meta.get('column_roles', {}))}",
        f"Charts: {len(charts)} (types: {', '.join(c.get('chart_type', '?') for c in charts[:5])})",
    ]
    if insights.get("l1_facts"):
        context_lines.append("Key facts:")
        for f in insights["l1_facts"][:5]:
            context_lines.append(f"  - {f}")
    if insights.get("l3_insights"):
        context_lines.append("Board decisions:")
        for i in insights["l3_insights"][:3]:
            if isinstance(i, dict):
                context_lines.append(f"  - {i.get('title', '')}: {i.get('insight', '')}")
    if warnings:
        context_lines.append(f"Notable: {warnings[0] if warnings else ''}")

    context = "\n".join(context_lines)
    system_msg = (
        "You are a senior data analyst. The user is asking a question about an uploaded dataset. "
        "Answer based ONLY on the data context provided below. If the answer requires a "
        "calculation you can't verify from the context, say so. Every number you cite must appear "
        "in the context. Be concise (2-4 sentences for most questions). Use business language, no "
        "statistical jargon. Format numbers readably (1.2M, 47k, 12%).\n\n"
        f"=== DATASET CONTEXT ===\n{context}\n=== END CONTEXT ==="
    )
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": question},
    ]

    def generate():
        try:
            import asyncio
            from ai.ollama_client import OllamaClient
            client = OllamaClient()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            gen = client.stream("fast_qa", messages)
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            for token in loop.run_until_complete(_collect_stream(gen)):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def _collect_stream(gen):
    """Collect all tokens from an async stream into a list (for sync SSE)."""
    tokens = []
    async for token in gen:
        tokens.append(token)
    return tokens


# ── /api/filter — re-render KPIs/charts/anomalies for a filtered subset ─────
@app.route("/api/filter", methods=["POST"])
def filter_session():
    """
    Apply user-selected filters to the stored records and re-derive
    KPIs, charts, and anomaly counts. NO LLM call (fast, <500ms).

    Body: {"session_id": "...", "filters": {"region": "APAC", "category": "X"}}
    Returns: {charts, anomalies, stats, total_rows, filtered_rows}
    """
    body = request.get_json(force=True) or {}
    session_id = body.get("session_id")
    filters = body.get("filters", {}) or {}
    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id"}), 400
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404

    records = session.get("records", [])
    if not records:
        return jsonify({"success": False, "error": "No records in session"}), 400

    # Apply filters
    filtered = records
    for col, val in filters.items():
        if val is None or val == "" or val == "All":
            continue
        filtered = [r for r in filtered if str(r.get(col, "")) == str(val)]

    # Re-derive KPIs/charts/anomalies from filtered subset (no LLM)
    try:
        import pandas as pd
        df = pd.DataFrame(filtered)
        if df.empty:
            return jsonify({
                "success": True,
                "charts": [],
                "anomalies": [],
                "stats": {"total_rows": len(records), "filtered_rows": 0},
                "filters": filters,
            })

        from ai.smart_viz_selector import SmartVizSelector
        from ai.dataset_classifier import DatasetClassifier
        from ai.anomaly_detector import AnomalyDetector
        from ai.analytical_engine import AnalyticalEngine
        from parsers.base_parser import DataProfile
        from utils.data_serializer import DataSerializer

        # Classify the filtered subset
        meta = DatasetClassifier().classify(df, None)
        # Build a full DataProfile that all downstream code can use
        column_types = {c: ("datetime" if df[c].dtype.kind == 'M' else
                            "numeric" if df[c].dtype.kind in ('i','f') else
                            "categorical") for c in df.columns}
        text_content = " | ".join(
            f"{c}={df[c].iloc[0]}" for c in df.columns[:5]
        ) if not df.empty else ""
        profile = DataProfile(
            df=df, source_type="filtered", file_name="filtered",
            rows=len(df), cols=df.shape[1], columns=list(df.columns),
            dtypes={c: str(df[c].dtype) for c in df.columns},
            nulls={c: int(df[c].isna().sum()) for c in df.columns},
            null_pct={c: float(df[c].isna().mean() * 100) for c in df.columns},
            duplicates=int(df.duplicated().sum()),
            numeric_summary={c: {} for c in df.columns if df[c].dtype.kind in ('i','f')},
            sample=df.head(5).to_dict(orient="records") if not df.empty else [],
            text_content=text_content,
            column_types=column_types,
            has_datetime=any(df[c].dtype.kind == 'M' for c in df.columns),
            has_numeric=any(df[c].dtype.kind in ('i','f') for c in df.columns),
            kpi_columns=meta.kpi_columns if hasattr(meta, "kpi_columns") else [],
            processing_time=0.0,
            warnings=[],
        )
        findings = AnalyticalEngine().analyze(df, meta, profile)
        charts = SmartVizSelector().select_charts(df, meta, findings)
        anomalies = AnomalyDetector().detect(profile, ollama_client=None)

        # Serialize
        chart_dicts = [dict(c.__dict__) if hasattr(c, "__dict__") else c for c in charts]
        anomaly_dicts = [a.__dict__ if hasattr(a, "__dict__") else a for a in anomalies]

        return jsonify({
            "success": True,
            "charts": chart_dicts,
            "anomalies": anomaly_dicts,
            "stats": {
                "total_rows": len(records),
                "filtered_rows": len(filtered),
                "filter_pct": round(len(filtered) / max(len(records), 1) * 100, 1),
            },
            "filters": filters,
        })
    except Exception as e:
        logger.error(f"Filter error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ── /api/drilldown — return the actual rows behind a chart bar/data point ────
@app.route("/api/drilldown", methods=["POST"])
def drilldown():
    """
    Return the raw records matching a chart's category + value range.
    Used when user clicks a bar in a chart.

    Body: {
        "session_id": "...",
        "column": "region",         # x-axis column
        "value": "APAC",            # clicked value
        "value_column": "revenue",  # y-axis column (optional, for context)
        "filters": {...},           # active cross-filters
        "limit": 50
    }
    Returns: {"rows": [...], "total": 42, "column": "region", "value": "APAC"}
    """
    body = request.get_json(force=True) or {}
    session_id = body.get("session_id")
    column = body.get("column")
    value = body.get("value")
    filters = body.get("filters", {}) or {}
    limit = min(int(body.get("limit", 50)), 500)

    if not session_id or column is None:
        return jsonify({"success": False, "error": "Missing session_id or column"}), 400
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404

    records = session.get("records", [])
    if not records:
        return jsonify({"success": False, "error": "No records in session"}), 400

    # Apply cross-filters first
    filtered = records
    for col, val in filters.items():
        if val is None or val == "" or val == "All" or col == column:
            continue
        filtered = [r for r in filtered if str(r.get(col, "")) == str(val)]

    # Then filter to clicked value
    matching = [r for r in filtered if str(r.get(column, "")) == str(value)]

    # Add a row number
    rows = []
    for i, r in enumerate(matching[:limit], 1):
        row = {"#": i}
        row.update(r)
        rows.append(row)

    return jsonify({
        "success": True,
        "column": column,
        "value": str(value),
        "total": len(matching),
        "shown": len(rows),
        "rows": rows,
        "columns": list(matching[0].keys()) if matching else [],
    })


# ── /api/export/dashboard — downloadable standalone HTML dashboard ZIP ──────
@app.route("/api/export/dashboard", methods=["POST", "GET"])
def export_dashboard_zip():
    """Download the entire dashboard as a self-contained HTML ZIP file."""
    session_id = (request.args.get("session_id") or
                  (request.get_json(silent=True) or {}).get("session_id") or
                  (request.form.get("session_id") if request.form else None))
    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id"}), 400
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    try:
        zip_bytes = export_dashboard(session, session_id)
        from flask import Response
        return Response(
            zip_bytes,
            mimetype="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=datalens-dashboard-{session_id[:8]}.zip",
                "Content-Length": str(len(zip_bytes)),
            },
        )
    except Exception as e:
        logger.error(f"Dashboard export failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ── /api/export/pbix — real PowerBI .pbit via pbi-tools ─────────────────────
@app.route("/api/export/pbix", methods=["GET", "POST"])
def export_pbix_real():
    """
    Download a real PowerBI .pbit file that opens in PowerBI Desktop
    with editable DAX, data model, and visuals.

    Built using pbi-tools (pbi.tools) — a .NET CLI for offline PBIX manipulation.
    """
    session_id = (request.args.get("session_id") or
                  (request.get_json(silent=True) or {}).get("session_id"))
    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id"}), 400
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    if not session.get("records"):
        return jsonify({"success": False, "error": "No records in session"}), 400
    try:
        pbix_path = build_real_pbix(session, session_id)
        from flask import send_file
        return send_file(
            pbix_path,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=f"datalens-dashboard-{session_id[:8]}.pbit"
        )
    except Exception as e:
        logger.error(f"PBIX export failed: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ── /api/ask/sync — non-streaming fallback (for testing) ────────────────────
@app.route("/api/ask/sync", methods=["POST"])
def ask_sync():
    data = request.get_json()
    session_id = data.get("session_id")
    question = data.get("question")
    session = session_store.get(session_id) if session_id else None
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    # Build context from session (same as streaming ask)
    insights = session.get("insights", {})
    charts = session.get("charts", [])
    warnings = session.get("warnings", [])
    meta = session.get("dataset_meta", {})
    context_lines = [
        f"Dataset type: {meta.get('dataset_type', 'general') if isinstance(meta, dict) else getattr(meta, 'dataset_type', 'general')}",
        f"Rows: {session.get('metadata', {}).get('analyzed_rows', '?')}",
        f"Charts: {len(charts)}",
    ]
    if insights.get("l1_facts"):
        context_lines.append("Key facts:")
        for f in insights["l1_facts"][:5]:
            context_lines.append(f"  - {f}")
    if insights.get("l3_insights"):
        context_lines.append("Board decisions:")
        for i in insights["l3_insights"][:3]:
            if isinstance(i, dict):
                context_lines.append(f"  - {i.get('insight', '')}")
    if session.get("anomalies"):
        context_lines.append("Anomalies:")
        for a in session.get("anomalies", [])[:3]:
            if isinstance(a, dict):
                context_lines.append(f"  - {a.get('column', '?')}: {a.get('explanation', '')}")
    context = "\n".join(context_lines)
    system_msg = (
        "You are a senior data analyst. The user is asking a question about an uploaded dataset. "
        "Answer based ONLY on the data context provided below. Be concise (2-4 sentences). "
        "Every number you cite must appear in the context.\n\n"
        f"=== DATASET CONTEXT ===\n{context}\n=== END CONTEXT ==="
    )
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": question},
    ]
    try:
        answer = asyncio.run(ollama.chat("fast_qa", messages, max_tokens=600))
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── /api/dataset/<session_id> — return raw records (for frontend filter) ──
@app.route("/api/dataset/<session_id>", methods=["GET"])
def get_dataset(session_id):
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify(_serialize_response({
        "success": True,
        "charts": session.get("charts", []),
        "anomalies": session.get("anomalies", []),
        "warnings": session.get("warnings", []),
        "metadata": session.get("metadata", {}),
        # NEW: for slicers + drill-down
        "records": session.get("records", []),
        "records_columns": session.get("records_columns", []),
        "filterable_columns": session.get("filterable_columns", []),
    }))


# ════════════════════════════════════════════════════════════════════════════
# MULTI-FILE PIPELINE — Phase 1: 2026-07-14
# ════════════════════════════════════════════════════════════════════════════
# Accepts 2-10 files, detects PKs/FKs, builds star schema, runs AI on unified data.
# MVP scope: synchronous, in-memory, 100K row cap, simple FK detection.
# ════════════════════════════════════════════════════════════════════════════

from ai.multi_file import run_multi_file_pipeline, get_unified_dataframe_from_result
from parsers.csv_parser import CSVParser
from utils.data_serializer import DataSerializer


@app.route("/api/analyze/multi", methods=["POST"])
@limiter.limit("3 per minute")
def analyze_multi():
    """Multi-file analysis: accept N files, detect relationships, build unified dashboard."""
    if "files" not in request.files:
        return jsonify({"success": False, "error": "No 'files' field in request. Use multipart/form-data with field name 'files'"}), 400

    # Get all files (request.files is a MultiDict)
    file_list = request.files.getlist("files")
    if not file_list or len(file_list) < 2:
        return jsonify({"success": False, "error": "Need at least 2 files for multi-file analysis"}), 400
    if len(file_list) > 10:
        return jsonify({"success": False, "error": "Maximum 10 files allowed"}), 400

    # Read content + metadata
    files_payload = []
    for f in file_list:
        if not f.filename:
            continue
        content = f.read()
        if len(content) == 0:
            continue
        file_id = f.filename.rsplit('.', 1)[0]  # use filename stem as ID
        files_payload.append((file_id, f.filename, content))

    if len(files_payload) < 2:
        return jsonify({"success": False, "error": "Need at least 2 non-empty files"}), 400

    job_id = uuid.uuid4().hex
    job_store.create(job_id, f"multi_file_{len(files_payload)}_files")

    def run_multi():
        import asyncio
        try:
            job_store.update(job_id, status="processing", progress=1,
                              message=f"📂 Parsing {len(files_payload)} files...")
            # Step 1: Multi-file pipeline (parse + FK detection + star schema)
            pipeline_result = run_multi_file_pipeline(files_payload)
            if not pipeline_result.get("success"):
                job_store.update(job_id, status="failed", error=pipeline_result.get("error", "Pipeline failed"))
                return

            job_store.update(job_id, progress=3, message=f"🔗 Found {len(pipeline_result['relationships'])} relationships...")

            # Step 2: Build DataProfile from unified dataframe
            unified_df = get_unified_dataframe_from_result(pipeline_result, files_payload)
            if unified_df is None or len(unified_df) == 0:
                job_store.update(job_id, status="failed", error="Empty unified dataframe")
                return

            # Adapt unified DF to DataProfile format (use DataProfiler)
            from parsers.base_parser import DataProfile
            from utils.data_profiler import DataProfiler
            import time
            t0 = time.time()
            profile = DataProfiler.profile(
                df=unified_df,
                source_type='multi_file',
                file_name=f"multi_file_{job_id}.csv",
                processing_time=time.time() - t0,
                warnings=[],
            )

            job_store.update(job_id, progress=4, message="🤖 Running AI insights on unified data...")
            # Step 3: Run existing AI pipeline on unified data
            result = asyncio.run(pipeline.run(
                profile,
                progress_callback=lambda s, m: job_store.update(job_id, progress=s, message=m)
            ))

            # Add multi-file metadata
            result['multi_file'] = pipeline_result
            result['mode'] = 'multi_file'
            session_store.save(job_id, result)
            job_store.update(job_id, status="completed", progress=6,
                              message="✅ Multi-file analysis complete", result=result)
        except Exception as e:
            logger.error(f"Multi-file analysis failed: {e}", exc_info=True)
            job_store.update(job_id, status="failed", error=str(e))

    t = threading.Thread(target=run_multi, daemon=True)
    t.start()
    return jsonify({"success": True, "job_id": job_id, "file_count": len(files_payload)}), 202


@app.route("/api/multi/profile/<job_id>", methods=["GET"])
def get_multi_profile(job_id):
    """Get the multi-file pipeline profile (relationships, schema, etc.) for a job."""
    job = job_store.get(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"}), 404
    if job.get("status") != "completed":
        return jsonify({"success": False, "error": f"Job not completed: {job.get('status')}"}), 400
    result = job.get("result", {})
    multi = result.get("multi_file", {})
    if not multi:
        return jsonify({"success": False, "error": "No multi-file data"}), 404
    # Remove the heavy unified_data sample (already in records)
    if "unified_data" in multi:
        del multi["unified_data"]["sample_records"]
    return jsonify({"success": True, **multi})


# ── Error handlers ────────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"}), 413


@app.errorhandler(429)
def rate_limited(e):
    return jsonify({"success": False, "error": "Rate limit hit. Wait 60s and retry."}), 429


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
