"""
ollama_client.py

Ollama Cloud client for DataLens AI.
Replaces NIMClient — single API key, 33 cloud models, no key expiry.
Live-verified 2026-07-13.

Endpoints:
  /v1/chat/completions   — OpenAI-compatible (used for /api/analyze + /api/ask)
  /api/chat               — native, used for streaming (cleaner SSE chunks)

No embeddings on cloud. Local Ollama at localhost:11434 for nomic-embed-text.
"""
import os
import time
import json
import logging
import asyncio
from typing import AsyncIterator, Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(asctime)s] %(name)s: %(message)s")
logger = logging.getLogger("OllamaClient")

# ── Configuration ────────────────────────────────────────────────────────────
BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
LOCAL_URL = os.getenv("OLLAMA_LOCAL_URL", "http://localhost:11434")
API_KEY = os.getenv("OLLAMA_API_KEY", "")

# ── Model registry (4 roles + 1 backup chain) ────────────────────────────────
MODELS = {
    # ROLE: reasoner — L3 board narrative, anomaly explanations, JSON insights
    "reasoner": {
        "primary": "gpt-oss:120b-cloud",  # 3.0s JSON, best open-weight reasoning
        "fallback": ["deepseek-v4-flash", "ministral-3:8b", "kimi-k2.6"],
        "ctx_window": 32768,
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    # ROLE: analyst — L1+L2 facts+causes (fast, structured)
    "analyst": {
        "primary": "minimax-m3:cloud",    # 1.5s, JSON-reliable
        "fallback": ["ministral-3:8b", "deepseek-v4-flash"],
        "ctx_window": 32768,
        "max_tokens": 3000,
        "temperature": 0.2,
    },
    # ROLE: fast_qa — /api/ask chat (lowest latency)
    "fast_qa": {
        "primary": "deepseek-v4-flash",   # 0.6s, best for citation grounding
        "fallback": ["ministral-3:8b", "gpt-oss:120b-cloud"],
        "ctx_window": 16384,
        "max_tokens": 800,
        "temperature": 0.4,
    },
    # ROLE: code — parsers, schema inference (rarely used)
    "code": {
        "primary": "ministral-3:8b",
        "fallback": ["minimax-m3:cloud"],
        "ctx_window": 16384,
        "max_tokens": 2000,
        "temperature": 0.2,
    },
}


class OllamaClient:
    """
    Async client for Ollama Cloud.
    Single API key (OLLAMA_API_KEY) covers all chat models.
    Embeddings are LOCAL only (use OllamaClientLocal helper for that).
    """

    def __init__(self, api_key: str = None):
        self._key = api_key or API_KEY
        if not self._key:
            logger.warning("OLLAMA_API_KEY not set — all chat calls will fail")
        self._client: Optional[httpx.AsyncClient] = None
        self._client_loop: Optional[asyncio.AbstractEventLoop] = None
        logger.info(f"OllamaClient ready · base={BASE_URL} · 4 roles loaded")

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-create async client bound to the current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if self._client is None or self._client_loop is not current_loop:
            if self._client is not None:
                try: await self._client.aclose()
                except: pass
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
            self._client_loop = current_loop
        return self._client

    async def aclose(self):
        if self._client is not None:
            try: await self._client.aclose()
            except: pass
            self._client = None
            self._client_loop = None

    # ── Core API ────────────────────────────────────────────────────────────
    async def chat(
        self,
        role: str,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = None,
        temperature: float = None,
        json_mode: bool = False,
        timeout: float = 60.0,
    ) -> str:
        """
        Chat completion with automatic role→model resolution + fallback chain.
        Returns the content string (with any <thinking>...</thinking> stripped).
        """
        if role not in MODELS:
            raise ValueError(f"Unknown role: {role}. Available: {list(MODELS.keys())}")

        spec = MODELS[role]
        chain = [spec["primary"]] + spec["fallback"]
        last_err = None

        for model_name in chain:
            try:
                return await self._chat_with_model(
                    model_name, messages,
                    max_tokens=max_tokens or spec["max_tokens"],
                    temperature=temperature if temperature is not None else spec["temperature"],
                    json_mode=json_mode,
                    timeout=timeout,
                )
            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                last_err = e
                status = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
                logger.warning(f"Model {model_name} failed ({status}): {e}. Trying fallback.")
                continue

        raise RuntimeError(f"All fallbacks exhausted for role={role}. Last error: {last_err}")

    async def _chat_with_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        timeout: float,
    ) -> str:
        """Single model call, returns content with thinking stripped."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        client = await self._get_client()
        r = await client.post("/v1/chat/completions", json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()

        content = data["choices"][0]["message"]["content"]

        # Strip <thinking>...</thinking> (gpt-oss-120b emits these)
        if content:
            content = self._strip_thinking(content)
        return content or ""

    async def stream(
        self,
        role: str,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = None,
        temperature: float = None,
    ) -> AsyncIterator[str]:
        """Streaming chat (yields content tokens)."""
        spec = MODELS.get(role, MODELS["fast_qa"])
        model = spec["primary"]
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens or spec["max_tokens"],
            "temperature": temperature if temperature is not None else spec["temperature"],
            "stream": True,
        }
        client = await self._get_client()
        async with client.stream("POST", "/v1/chat/completions", json=payload, timeout=120.0) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    # ── Health ──────────────────────────────────────────────────────────────
    async def health(self) -> bool:
        """Quick health check — returns True if Ollama Cloud is reachable."""
        try:
            client = await self._get_client()
            r = await client.get("/api/tags", timeout=10.0)
            return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """Return available cloud model names."""
        client = await self._get_client()
        r = await client.get("/api/tags", timeout=10.0)
        r.raise_for_status()
        data = r.json()
        return [m["name"] for m in data.get("models", [])]

    @staticmethod
    def _strip_thinking(content: str) -> str:
        """Remove <thinking>...</thinking> blocks emitted by reasoning models."""
        import re
        # Strip <think>...</think> (some models use Chinese chars)
        content = re.sub(r"<think(?:ing)?>.*?</think(?:ing)?>", "", content, flags=re.DOTALL)
        return content.strip()


class OllamaClientLocal:
    """
    Local Ollama client for embeddings (nomic-embed-text).
    Run `ollama serve` and `ollama pull nomic-embed-text` before using.
    """

    def __init__(self, base_url: str = None, model: str = "nomic-embed-text"):
        self.base_url = (base_url or LOCAL_URL).rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def aclose(self):
        await self._client.aclose()

    async def embed(self, text: str) -> List[float]:
        """Embed a single text string. Returns 768-dim vector (nomic-embed-text)."""
        r = await self._client.post(
            "/api/embeddings",
            json={"model": self.model, "prompt": text},
        )
        r.raise_for_status()
        return r.json()["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in sequence (nomic-embed has no batch API)."""
        return [await self.embed(t) for t in texts]

    async def health(self) -> bool:
        try:
            r = await self._client.get("/api/tags", timeout=5.0)
            return r.status_code == 200 and any(
                m["name"].startswith(self.model) for m in r.json().get("models", [])
            )
        except Exception:
            return False


# ── Synchronous wrappers (for non-async code) ────────────────────────────────
def chat_sync(role: str, messages: List[Dict[str, str]], **kwargs) -> str:
    """Synchronous wrapper for OllamaClient.chat()."""
    return asyncio.run(OllamaClient().chat(role, messages, **kwargs))


def stream_sync(role: str, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
    """Returns an async iterator (call with async for)."""
    return OllamaClient().stream(role, messages, **kwargs)


# ── CLI smoke test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    async def _test():
        client = OllamaClient()
        if not await client.health():
            print("FAIL: Ollama Cloud not reachable")
            return
        r = await client.chat(
            "fast_qa",
            [{"role": "user", "content": "Reply with just: OK. Nothing else."}],
            max_tokens=20,
        )
        print(f"PASS: Ollama Cloud fast_qa → {r!r}")
        await client.aclose()
    asyncio.run(_test())
