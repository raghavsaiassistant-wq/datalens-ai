"""
Production hardening module (Sprint 12)
- Timeouts on AI calls
- Circuit breaker for Ollama
- Error recovery
- Request validation
"""
import time
import logging
import threading
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger("datalens.hardening")


class CircuitBreaker:
    """Circuit breaker pattern: stop calling failing service temporarily."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed = OK, open = failing
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker."""
        with self._lock:
            if self.state == "open":
                # Check if reset period has passed
                if self.last_failure_time and (
                    time.time() - self.last_failure_time > self.reset_timeout
                ):
                    self.state = "half_open"
                    logger.info("Circuit breaker: half-open (testing)")
                else:
                    raise Exception("Circuit breaker is OPEN (too many failures)")

        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == "half_open":
                    self.state = "closed"
                    self.failures = 0
                    logger.info("Circuit breaker: closed (recovered)")
            return result
        except Exception as e:
            with self._lock:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "open"
                    logger.warning(f"Circuit breaker: OPEN after {self.failures} failures")
            raise


class TimeoutError(Exception):
    pass


def with_timeout(seconds: int, default=None):
    """Decorator: timeout a function (uses threading)."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_box = {"value": default, "exception": None}

            def target():
                try:
                    result_box["value"] = func(*args, **kwargs)
                except Exception as e:
                    result_box["exception"] = e

            t = threading.Thread(target=target, daemon=True)
            t.start()
            t.join(timeout=seconds)
            if t.is_alive():
                logger.warning(f"{func.__name__} timed out after {seconds}s, returning default")
                return default
            if result_box["exception"]:
                raise result_box["exception"]
            return result_box["value"]
        return wrapper
    return decorator


class RequestValidator:
    """Validate common API requests."""

    @staticmethod
    def validate_multi_file_request(files, max_files: int = 10, max_size_mb: int = 25) -> Dict[str, Any]:
        """Validate multi-file upload request."""
        if not files:
            return {"valid": False, "error": "No files provided"}
        if len(files) < 2:
            return {"valid": False, "error": "Need at least 2 files"}
        if len(files) > max_files:
            return {"valid": False, "error": f"Max {max_files} files allowed, got {len(files)}"}

        allowed_extensions = {".csv", ".xlsx", ".xls", ".json", ".sql"}
        for f in files:
            if isinstance(f, tuple):
                # (field, (filename, fp, mimetype))
                filename = f[1][0] if len(f) > 1 and isinstance(f[1], tuple) else "unknown"
            else:
                filename = getattr(f, "filename", "unknown")
            ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in allowed_extensions:
                return {"valid": False, "error": f"Unsupported file type: {filename}"}

        return {"valid": True, "file_count": len(files)}

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove dangerous characters from filename."""
        import re
        # Remove path traversal
        name = name.replace("..", "_").replace("/", "_").replace("\\", "_")
        # Keep only safe chars
        name = re.sub(r'[^a-zA-Z0-9._-]', '_', name)
        return name[:200]  # cap length


# Global circuit breaker for Ollama
ollama_breaker = CircuitBreaker(failure_threshold=3, reset_timeout=120)


def health_check() -> Dict[str, Any]:
    """Overall health check for monitoring."""
    return {
        "ollama_circuit": ollama_breaker.state,
        "ollama_failures": ollama_breaker.failures,
        "timestamp": datetime.now().isoformat(),
        "uptime_s": int(time.time() - _start_time),
    }


_start_time = time.time()
