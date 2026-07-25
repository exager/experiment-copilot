"""
LangSmith tracing configuration for the LangGraph pipeline (Developer 4).

The agents use LangChain (`ChatGoogleGenerativeAI`) inside a LangGraph, so once
the ``LANGCHAIN_*`` environment variables are exported, EVERY LLM call and graph
node is traced to LangSmith automatically — no per-call wiring needed.

Usage:
    from app.langsmith_config import init_langsmith
    init_langsmith()          # call once at startup (llm.py does this on import)

    # For richer, filterable traces, pass run config to graph.invoke:
    from app.langsmith_config import get_run_config
    graph.invoke(state, {**config, **get_run_config("experiment_pipeline", thread_id)})
"""

from __future__ import annotations

import os
import time
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

_INITIALIZED = False
_DEFAULT_PROJECT = "experiment-copilot"
_DEFAULT_ENDPOINT = "https://api.smith.langchain.com"


def _load_dotenv() -> None:
    """Ensure backend/.env is loaded.

    Delegates to the single loader in ``app.config`` so there is exactly one
    dotenv implementation in the codebase. Falls back to a no-op if that import
    is unavailable, keeping this module import-safe.
    """
    try:
        from app.config import load_env
    except Exception:  # pragma: no cover - defensive
        return
    load_env()


def init_langsmith() -> bool:
    """
    Export the LANGCHAIN_* env vars LangChain reads for auto-tracing.

    Idempotent. Returns True if tracing is active (enabled + API key present).
    """
    global _INITIALIZED
    if not _INITIALIZED:
        _load_dotenv()
        _INITIALIZED = True

    tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "true").lower() != "false"
    api_key_present = bool(os.environ.get("LANGCHAIN_API_KEY"))

    # Only actually turn on auto-tracing when a key is present. Otherwise
    # LangChain tries (and fails) to ingest every run, spamming 401 errors in
    # tests and local dev. Tracing flips on automatically once a key is added.
    active = tracing_enabled and api_key_present
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if active else "false"
    os.environ.setdefault("LANGCHAIN_PROJECT", _DEFAULT_PROJECT)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", _DEFAULT_ENDPOINT)

    return active


def tracing_status() -> dict[str, Any]:
    """Human-readable snapshot of the current tracing configuration."""
    return {
        "tracing_enabled": os.environ.get("LANGCHAIN_TRACING_V2") == "true",
        "api_key_present": bool(os.environ.get("LANGCHAIN_API_KEY")),
        "project": os.environ.get("LANGCHAIN_PROJECT", _DEFAULT_PROJECT),
        "endpoint": os.environ.get("LANGCHAIN_ENDPOINT", _DEFAULT_ENDPOINT),
    }


def get_run_config(run_name: str, thread_id: str = "", agent: str = "") -> dict[str, Any]:
    """Build a LangChain/LangGraph run config with tags + metadata for filtering."""
    tags = [t for t in ("experiment-copilot", agent) if t]
    metadata = {"thread_id": thread_id} if thread_id else {}
    return {"run_name": run_name, "tags": tags, "metadata": metadata}


# ── Optional local aggregation callbacks (provider-agnostic) ─────────────


class TokenMonitor(BaseCallbackHandler):
    """Aggregate token usage across LLM calls (best-effort, provider-agnostic)."""

    def __init__(self) -> None:
        super().__init__()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        self.call_count += 1
        usage: dict[str, Any] = {}
        # LangChain 1.x surfaces usage on the message; fall back to llm_output.
        try:
            msg = response.generations[0][0].message  # type: ignore[attr-defined]
            usage = getattr(msg, "usage_metadata", None) or {}
        except Exception:
            usage = (response.llm_output or {}).get("token_usage", {}) or {}
        self.total_input_tokens += usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
        self.total_output_tokens += usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }


class LatencyTracker(BaseCallbackHandler):
    """Track per-call latency."""

    def __init__(self) -> None:
        super().__init__()
        self.latencies: list[float] = []
        self._starts: dict[str, float] = {}

    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], *, run_id: Any, **kwargs: Any) -> None:
        self._starts[str(run_id)] = time.time()

    def on_llm_end(self, response: LLMResult, *, run_id: Any, **kwargs: Any) -> None:
        start = self._starts.pop(str(run_id), None)
        if start is not None:
            self.latencies.append(time.time() - start)

    def get_summary(self) -> dict[str, Any]:
        if not self.latencies:
            return {"total_calls": 0, "avg_latency_ms": 0, "max_latency_ms": 0}
        return {
            "total_calls": len(self.latencies),
            "avg_latency_ms": round(sum(self.latencies) / len(self.latencies) * 1000, 2),
            "min_latency_ms": round(min(self.latencies) * 1000, 2),
            "max_latency_ms": round(max(self.latencies) * 1000, 2),
        }
