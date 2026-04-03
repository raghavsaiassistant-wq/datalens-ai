"""
session_store.py

In-memory store for analysis results. Allows Q&A to reference previously analyzed data.
"""
import threading
import time
from typing import Optional, Dict

class SessionStore:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()
        
    def save(self, session_id: str, data: dict) -> None:
        self.cleanup_expired()
        with self._lock:
            self._store[session_id] = {
                "data": data,
                "created_at": time.time()
            }
            
    def get(self, session_id: str) -> Optional[dict]:
        with self._lock:
            session = self._store.get(session_id)
            if not session:
                return None
            return session["data"]
            
    def delete(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                
    def cleanup_expired(self, expiry_seconds: int = 7200) -> int:
        """Deletes sessions older than 2 hours (7200 seconds)."""
        now = time.time()
        expired_keys = []
        with self._lock:
            for sid, val in self._store.items():
                if now - val["created_at"] > expiry_seconds:
                    expired_keys.append(sid)
            for sid in expired_keys:
                del self._store[sid]
        return len(expired_keys)
