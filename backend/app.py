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

# Add backend directory to sys path so internal imports resolve correctly
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_router import FileRouter
from ai.findings_generator import FindingsGenerator
from ai.nim_client import NIMClient
from utils.session_store import SessionStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__)
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
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "models_available": list(nim_client._clients.keys()) if hasattr(nim_client, '_clients') else [],
        "supported_extensions": router.get_supported_extensions()
    })

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file parameter found"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in router.get_supported_extensions():
        return jsonify({"error": f"Unsupported file extension {ext}"}), 400
        
    # Save file
    safe_name = secure_filename(file.filename)
    if not safe_name: safe_name = "upload" + ext
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{safe_name}")
    file.save(save_path)
    
    try:
        # Route and Profile
        profile = router.route(save_path, safe_name, nim_client=nim_client)
        # AI Generator Pipeline
        analysis_result = generator.generate(profile, nim_client)
    except ValueError as ve:
        return jsonify({"error": f"Validation Error: {str(ve)}"}), 422
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"AI Processing Error: {str(e)}"}), 500
    finally:
        # Cleanup file
        if os.path.exists(save_path):
            os.remove(save_path)
            
    # Save session
    session_id = str(uuid.uuid4())
    session_data = {
        "result": analysis_result,
        "profile_text": profile.text_content if hasattr(profile, "text_content") else "",
        "file_name": safe_name
    }
    session_store.save(session_id, session_data)
    
    return jsonify({
        "status": "success",
        "session_id": session_id,
        "processing_time": analysis_result.get("processing_time", 0),
        "data": analysis_result
    })

@app.route("/api/ask", methods=["POST"])
def ask():
    req = request.get_json()
    if not req or "question" not in req or "session_id" not in req:
        return jsonify({"error": "Missing question or session_id payload"}), 400
        
    session_id = req["session_id"]
    question = req["question"]
    
    session = session_store.get(session_id)
    if not session:
        return jsonify({"error": "Session expired or not found. Please re-upload your data."}), 404
        
    profile_text = session.get("profile_text", "")
    
    system = "You are a data analyst assistant. Answer questions about the dataset concisely using only the data provided. If the answer is not in the data, say so clearly."
    user = f"Dataset context:\n{profile_text}\n\nQuestion: {question}"
    
    try:
        # Default to Llama 8b (fast), if missing fallback to primary fast model (Mistral)
        model_name = "llama_8b"
        if "llama_8b" not in nim_client._clients:
            model_name = "mistral_7b"
            
        answer = nim_client.chat(model_name=model_name, user_prompt=user, system_prompt=system, max_tokens=300)
        answer = nim_client._strip_thinking(answer)
    except Exception as e:
        return jsonify({"error": f"Chat Failed: {str(e)}"}), 500
        
    return jsonify({
        "status": "success",
        "answer": answer,
        "session_id": session_id
    })

@app.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id):
    session = session_store.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({
        "status": "success",
        "session_id": session_id,
        "data": session["result"]
    })

@app.route("/api/session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    session_store.delete(session_id)
    return jsonify({"status": "deleted"})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": f"File exceeds maximum allowed size"}), 413

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
