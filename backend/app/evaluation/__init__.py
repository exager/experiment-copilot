"""Experiment Copilot evaluation harness (Developer 4).

Offline (keyless, deterministic) and online (real-LLM + optional LangSmith)
scoring of the six LangGraph agents.

    from app.evaluation import run_offline, summarize
    results = run_offline()
    print(summarize(results))

Exports are resolved lazily via ``__getattr__`` so that
``python -m app.evaluation.run_eval`` doesn't import ``run_eval`` twice.
"""

from __future__ import annotations

from typing import Any

from . import _compat  # noqa: F401  (install app.models.experiment shim first)

__all__ = ["run_offline", "run_online", "summarize"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from app.evaluation import run_eval

        return getattr(run_eval, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
