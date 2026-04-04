"""
app.py

Flask REST API serving DataLens AI frontend.
Routes files to FileRouter, processes through FindingsGenerator, and supports Q&A.
"""
import os
import uuid
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import threading
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_router import FileRouter
from ai.findings_generator import FindingsGenerator
from ai.nim_client import NIMClient
from utils.session_store import SessionStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)

# Job Store for Polling
# Format: { job_id: { "status": "processing", "progress": 1, "message": "...", "result": None, "error": None } }
JOBS = {}
JOBS_LOCK = threading.Lock()
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "https://datalens-ai.vercel.app",
    "https://*.vercel.app",
    "https://datalens-ai.onrender.com",
    "https://datalensai.vercel.app",
])

# Config
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 25)) * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
UPLOAD_FOLDER = "/tmp/datalens_uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Module Singletons
nim_client = NIMClient()
generator = FindingsGenerator()
router = FileRouter()
session_store = SessionStore()

@app.route("/api/health", methods=["GET"])
def health():
    nim_status = nim_client.health_check()
    is_healthy = all("ok" in s for s in nim_status.values() if s != "no_key")
    return jsonify({
        "success": True,
        "data": {
            "status": "healthy" if is_healthy else "degraded",
            "nim": nim_status,
            "version": "1.0.0"
        },
        "error": None
    })

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"success": False, "data": None, "error": "No file parameter found"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "data": None, "error": "Empty filename"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in router.get_supported_extensions():
        return jsonify({"success": False, "data": None, "error": f"Unsupported file extension {ext}"}), 400
        
    # Save file
    safe_name = secure_filename(file.filename)
    if not safe_name: safe_name = "upload" + ext
    file_id = str(uuid.uuid4())
    job_id = f"job_{file_id}"
    save_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{safe_name}")
    file.save(save_path)
    
    # Initialize Job
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "processing",
            "progress": 1,
            "message": "📂 Reading your file...",
            "result": None,
            "error": None,
            "file_name": safe_name,
            "created_at": time.time()
        }

    # Run Analysis in Background
    def background_analysis(jid, path, name):
        try:
            def update_cb(step, msg):
                with JOBS_LOCK:
                    if jid in JOBS:
                        JOBS[jid]["progress"] = step
                        JOBS[jid]["message"] = msg

            # 1. Route/Profile (Step 1-2 happens inside generator now via callback)
            profile = router.route(path, name, nim_client=nim_client)
            
            # 2. AI Generation
            analysis_result = generator.generate(profile, nim_client, progress_callback=update_cb)
            
            # 3. Finalize
            session_id = str(uuid.uuid4())
            session_data = {
                "result": analysis_result,
                "profile_text": profile.text_content if hasattr(profile, "text_content") else "",
                "file_name": name
            }
            session_store.save(session_id, session_data)
            
            with JOBS_LOCK:
                if jid in JOBS:
                    JOBS[jid]["status"] = "completed"
                    JOBS[jid]["progress"] = 6
                    JOBS[jid]["message"] = "🎉 Analysis complete!"
                    JOBS[jid]["result"] = {
                        "session_id": session_id,
                        "data": analysis_result
                    }
        except Exception as e:
            logging.error(f"Job {jid} failed: {e}")
            with JOBS_LOCK:
                if jid in JOBS:
                    JOBS[jid]["status"] = "failed"
                    JOBS[jid]["error"] = str(e)
        finally:
            if os.path.exists(path):
                os.remove(path)

    thread = threading.Thread(target=background_analysis, args=(job_id, save_path, safe_name))
    thread.start()
    
    return jsonify({
        "success": True,
        "data": {
            "job_id": job_id
        },
        "error": None
    })

@app.route("/api/status/<job_id>", methods=["GET"])
def get_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"success": False, "data": None, "error": "Job not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                "status": job["status"],
                "progress": job["progress"],
                "message": job["message"],
                "result": job["result"]
            },
            "error": job["error"]
        })

@app.route("/api/ask", methods=["POST"])
def ask():
    req = request.get_json()
    if not req or "question" not in req or "session_id" not in req:
        return jsonify({"success": False, "data": None, "error": "Missing question or session_id payload"}), 400
        
    session_id = req["session_id"]
    question = req["question"]
    
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "data": None, "error": "Session expired or not found. Please re-upload your data."}), 404
        
    profile_text = session.get("profile_text", "")
    
    system = "You are a data analyst assistant. Answer questions about the dataset concisely using only the data provided. If the answer is not in the data, say so clearly."
    user = f"Dataset context:\n{profile_text}\n\nQuestion: {question}"
    
    try:
        # Default to Llama 8b (fast), if missing fallback to primary fast model (Mistral)
        model_name = "llama_8b"
        if "llama_8b" not in nim_client._clients:
            model_name = "mistral_7b"
            
        answer = nim_client.chat(model_name=model_name, user_prompt=user, system_prompt=system, max_tokens=300)
    except Exception as e:
        return jsonify({"success": False, "data": None, "error": f"Chat Failed: {str(e)}"}), 500
        
    return jsonify({
        "success": True,
        "data": {
            "answer": answer,
            "session_id": session_id
        },
        "error": None
    })

@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id):
    session = session_store.get(session_id)
    if not session:
        return jsonify({"success": False, "data": None, "error": "Session not found"}), 404
    return jsonify({
        "success": True,
        "data": session["result"],
        "error": None
    })

@app.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    session_store.delete(session_id)
    return jsonify({"status": "deleted"})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "data": None, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "data": None, "error": "Internal server error"}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"success": False, "data": None, "error": "File exceeds 25MB limit"}), 413

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
