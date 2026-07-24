"""Shared Gemini client factory and retry wrapper for agent nodes.

Centralizing the LLM client here means the provider/model can be swapped
in one place without touching individual agent modules.
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable

from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Importing app.config first loads backend/.env into os.environ (idempotent,
# safe when .env is missing) so GEMINI_API_KEY and the LANGCHAIN_* tracing vars
# are populated before anything below reads them.
import app.config  # noqa: F401  (import-for-side-effect: load .env)
from app.langsmith_config import init_langsmith

# Activate LangSmith tracing as soon as the LLM layer is imported. Because
# agents run through LangChain inside LangGraph, this makes every LLM call and
# graph node trace to LangSmith automatically. No-op when LANGCHAIN_API_KEY is
# absent.
init_langsmith()

DEFAULT_MODEL = "gemini-2.0-flash"

NodeFn = Callable[[dict], dict]


def get_llm(
    temperature: float = 0.3,
    model: str = DEFAULT_MODEL,
    *,
    agent: str | None = None,
    prompt_version: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ChatGoogleGenerativeAI:
    """Build a Gemini chat model from the GEMINI_API_KEY env var.

    The optional keyword args attach LangSmith run tags/metadata so traces are
    filterable per agent / prompt version. They map onto the ``tags`` and
    ``metadata`` fields LangChain chat models already expose, so tracing stays
    automatic (no per-call wrapping) and every run from this model inherits them.

    Backward compatible: ``get_llm()`` and
    ``get_llm().with_structured_output(Schema)`` keep working unchanged. Callers
    that want richer traces can pass, e.g., ``get_llm(agent="context")``. Agent
    call sites currently pass nothing, so this is purely additive — a later pass
    can thread ``agent=``/``prompt_version=`` through if desired.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    run_tags: list[str] = list(tags or [])
    if agent:
        run_tags.append(f"agent:{agent}")
    if prompt_version:
        run_tags.append(f"prompt_version:{prompt_version}")

    run_metadata: dict[str, Any] = dict(metadata or {})
    if agent:
        run_metadata.setdefault("agent", agent)
    if prompt_version:
        run_metadata.setdefault("prompt_version", prompt_version)

    # Only pass tags/metadata when present to keep the constructor call minimal.
    extra: dict[str, Any] = {}
    if run_tags:
        extra["tags"] = run_tags
    if run_metadata:
        extra["metadata"] = run_metadata

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        **extra,
    )


def with_retry(node_fn: NodeFn) -> NodeFn:
    """Decorator for LangGraph node functions.

    Retries the wrapped node up to 3 times with exponential backoff. If
    every attempt fails, the exception is caught and appended to
    ``state["errors"]`` instead of propagating, so one failing agent
    doesn't crash the whole graph run.
    """
    retrying = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )(node_fn)

    @wraps(node_fn)
    def wrapped(state: dict) -> dict:
        try:
            return retrying(state)
        except Exception as exc:  # last-resort safety net for the whole graph
            errors: list[str] = [*state.get("errors", []), f"{node_fn.__name__}: {exc}"]
            return {"errors": errors}

    return wrapped
