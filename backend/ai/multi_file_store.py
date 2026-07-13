"""
multi_file_store.py — Persistent storage for multi-file jobs (Sprint 6)

Saves:
- Original files (so user can re-process)
- Unified dataframe (pickle/parquet)
- File metadata + relationship graph
- Job state

Survives server restart.
"""
import os
import json
import pickle
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger("datalens.multi_file_store")

class MultiFileStore:
    """Persistent store for multi-file analysis jobs."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = r"C:\James\engineering_lab\datalens-ai\data\multi_file_jobs"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MultiFileStore initialized at {self.base_dir}")

    def _job_dir(self, job_id: str) -> Path:
        return self.base_dir / job_id

    def save_job(
        self,
        job_id: str,
        file_bytes: Dict[str, bytes],  # {file_name: bytes}
        relationships: List[dict],
        schema: dict,
        unified_profile: dict = None,
        ai_result: dict = None,
    ) -> dict:
        """Persist all multi-file job state to disk."""
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(exist_ok=True)

        # 1. Save original files
        files_dir = job_dir / "files"
        files_dir.mkdir(exist_ok=True)
        file_hashes = {}
        for name, content in file_bytes.items():
            # Sanitize filename
            safe = name.replace("/", "_").replace("\\", "_")
            (files_dir / safe).write_bytes(content)
            # Hash for dedup
            file_hashes[name] = hashlib.md5(content).hexdigest()[:12]

        # 2. Save metadata
        meta = {
            "job_id": job_id,
            "created_at": time.time(),
            "file_count": len(file_bytes),
            "file_hashes": file_hashes,
            "file_names": list(file_bytes.keys()),
            "schema": schema,
            "relationship_count": len(relationships),
        }
        (job_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))

        # 3. Save relationships
        (job_dir / "relationships.json").write_text(
            json.dumps(relationships, indent=2, default=str)
        )

        # 4. Save profile
        if unified_profile:
            (job_dir / "profile.json").write_text(
                json.dumps(unified_profile, indent=2, default=str)
            )

        # 5. Save AI result
        if ai_result:
            (job_dir / "ai_result.json").write_text(
                json.dumps(ai_result, indent=2, default=str)
            )

        # 6. Save manifest
        manifest = {
            "job_id": job_id,
            "files": list(file_bytes.keys()),
            "size_bytes": sum(len(b) for b in file_bytes.values()),
            "persisted_at": time.time(),
        }
        (job_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        logger.info(f"Persisted job {job_id} ({len(file_bytes)} files, "
                    f"{sum(len(b) for b in file_bytes.values())/1024:.1f} KB)")
        return meta

    def load_job(self, job_id: str) -> Optional[dict]:
        """Load a previously persisted job."""
        job_dir = self._job_dir(job_id)
        if not job_dir.exists():
            return None
        meta_path = job_dir / "meta.json"
        if not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text())
            return meta
        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}")
            return None

    def get_files(self, job_id: str) -> Dict[str, bytes]:
        """Load original files for re-processing."""
        job_dir = self._job_dir(job_id)
        files_dir = job_dir / "files"
        if not files_dir.exists():
            return {}
        result = {}
        for p in files_dir.iterdir():
            if p.is_file():
                result[p.name] = p.read_bytes()
        return result

    def list_jobs(self) -> List[dict]:
        """List all persisted jobs."""
        jobs = []
        for p in self.base_dir.iterdir():
            if p.is_dir():
                meta = self.load_job(p.name)
                if meta:
                    jobs.append(meta)
        jobs.sort(key=lambda j: j.get("created_at", 0), reverse=True)
        return jobs

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and all its data."""
        job_dir = self._job_dir(job_id)
        if not job_dir.exists():
            return False
        try:
            for p in job_dir.rglob("*"):
                if p.is_file():
                    p.unlink()
            for p in sorted(job_dir.rglob("*"), reverse=True):
                if p.is_dir():
                    p.rmdir()
            job_dir.rmdir()
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False

    def disk_usage(self) -> dict:
        """Disk usage stats."""
        total = 0
        for p in self.base_dir.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
        return {
            "total_bytes": total,
            "total_kb": round(total / 1024, 1),
            "total_mb": round(total / 1024 / 1024, 2),
            "job_count": len(list(self.base_dir.iterdir())),
        }


# Global instance
multi_file_store = MultiFileStore()
