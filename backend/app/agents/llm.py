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

DEFAULT_MODEL = "gemini-2.0-flash"

NodeFn = Callable[[dict], dict]


def get_llm(temperature: float = 0.3, model: str = DEFAULT_MODEL) -> ChatGoogleGenerativeAI:
    """Build a Gemini chat model from the GEMINI_API_KEY env var."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=temperature)


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
