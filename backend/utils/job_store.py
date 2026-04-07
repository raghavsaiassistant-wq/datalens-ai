"""
job_store.py

SQLite-backed job store. Shared across all gunicorn workers via /tmp/datalens_jobs.db.
Replaces the in-memory JOBS dict that caused race conditions with --workers > 1.
"""
import sqlite3
import json
import time
import os
from typing import Optional

DB_PATH = os.getenv("JOB_DB_PATH", "/tmp/datalens_jobs.db")


class JobStore:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self._db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")  # concurrent readers + 1 writer
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id     TEXT PRIMARY KEY,
                    status     TEXT NOT NULL DEFAULT 'processing',
                    progress   INTEGER NOT NULL DEFAULT 1,
                    message    TEXT,
                    result     TEXT,
                    error      TEXT,
                    file_name  TEXT,
                    created_at REAL
                )
            """)

    def create(self, job_id: str, file_name: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, file_name, created_at) VALUES (?,?,?)",
                (job_id, file_name, time.time())
            )

    def update(self, job_id: str, **kwargs) -> None:
        if not kwargs:
            return
        if "result" in kwargs and kwargs["result"] is not None:
            kwargs["result"] = json.dumps(kwargs["result"])
        cols = ", ".join(f"{k} = ?" for k in kwargs)
        vals = list(kwargs.values()) + [job_id]
        with self._conn() as conn:
            conn.execute(f"UPDATE jobs SET {cols} WHERE job_id = ?", vals)

    def get(self, job_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("result"):
            d["result"] = json.loads(d["result"])
        return d

    def cleanup(self, ttl_seconds: int = 3600) -> None:
        cutoff = time.time() - ttl_seconds
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM jobs WHERE status IN ('completed','failed') AND created_at < ?",
                (cutoff,)
            )
