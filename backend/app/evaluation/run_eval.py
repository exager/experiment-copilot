"""Evaluation runner for the six LangGraph agents (Developer 4).

Loads the golden datasets, runs each target agent's ``node(state)``, scores the
outputs with :mod:`app.evaluation.evaluators`, and produces a printable
"AI quality report".

Two modes
=========

**OFFLINE** (default) — ``run_offline()``
    Runs the *real* agent nodes but swaps in a deterministic fake LLM, so it
    needs **no API key**, never calls Gemini, and never imports ``langsmith``.
    Focuses on schema-validity + rule-based checks. Three ways to supply the
    LLM:

    * ``get_llm=None`` (default): use the built-in offline fake
      (:mod:`app.evaluation.fake_llm`). This is what CI / a standalone
      ``python -m app.evaluation.run_eval`` uses.
    * ``get_llm=<callable>``: inject your own factory; it patches
      ``app.agents.llm.get_llm`` for the duration of the run.
    * ``get_llm="current"``: leave ``app.agents.llm.get_llm`` untouched — use
      this when a pytest test has already ``monkeypatch``-ed it (matches the
      existing ``fake_llm`` fixture in ``conftest.py``).

**ONLINE** (optional) — ``run_online()``
    Uses the real Gemini client (requires ``GEMINI_API_KEY``) and, optionally,
    an LLM-as-judge relevance score and LangSmith logging. ``langsmith`` is
    imported lazily *inside* this function, so importing or running the offline
    path never requires it.

Public API
==========

    run_offline(agents=None, get_llm=None, judge=None) -> dict
    run_online(agents=None, use_judge=True, use_langsmith=False,
               get_llm="current") -> dict
    summarize(results) -> str

Run from the ``backend/`` directory::

    python -m app.evaluation.run_eval                 # offline, all agents
    python -m app.evaluation.run_eval --agent report  # offline, one agent
    python -m app.evaluation.run_eval --online        # needs GEMINI_API_KEY
    python -m app.evaluation.run_eval --output eval.json
"""

from __future__ import annotations

import app.config  # noqa: F401  (load backend/.env so GEMINI/LANGCHAIN keys are set)

import argparse
import json
import sys
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional

from app.evaluation import evaluators
from app.evaluation.datasets import Example, get_dataset, list_agents
from app.evaluation.evaluators import EvalScore
from app.evaluation.fake_llm import get_fake_llm

# State key each agent writes its primary output under.
OUTPUT_KEY: dict[str, str] = {
    "context": "context_understanding",
    "hypothesis": "hypothesis",
    "experiment_design": "configuration",
    "validation": "validation",
    "explanation": "recommendation",
    "report": "report",
}

# Sentinel: "don't touch app.agents.llm.get_llm" (respect an external patch).
USE_CURRENT = "current"


def _load_nodes() -> dict[str, Callable[[dict], dict]]:
    """Import agent node functions lazily (keeps import side effects contained)."""
    from app.agents import (
        context_agent,
        experiment_design_agent,
        explanation_agent,
        hypothesis_agent,
        report_agent,
        validation_agent,
    )

    return {
        "context": context_agent.node,
        "hypothesis": hypothesis_agent.node,
        "experiment_design": experiment_design_agent.node,
        "validation": validation_agent.node,
        "explanation": explanation_agent.node,
        "report": report_agent.node,
    }


@contextmanager
def _patched_llm(get_llm: Optional[Callable[..., Any]] | str) -> Iterator[None]:
    """Temporarily point ``app.agents.llm.get_llm`` at ``get_llm``.

    ``USE_CURRENT`` leaves the module untouched (so an external monkeypatch is
    respected); any other callable replaces ``get_llm`` for the duration and is
    restored afterwards.
    """
    if get_llm == USE_CURRENT:
        yield
        return

    from app.agents import llm as llm_module

    original = llm_module.get_llm
    llm_module.get_llm = get_llm  # type: ignore[assignment]
    try:
        yield
    finally:
        llm_module.get_llm = original


def _run_example(
    node: Callable[[dict], dict],
    agent: str,
    example: Example,
    judge: Optional[evaluators.LLMJudge],
) -> dict[str, Any]:
    """Run one node over one example and score the result."""
    out_key = OUTPUT_KEY[agent]
    try:
        update = node(example.state())
    except Exception as exc:  # defensive: node should catch its own, but be safe
        return {"name": example.name, "error": f"{type(exc).__name__}: {exc}",
                "output": None, "scores": {}}

    if out_key not in update:
        err = update.get("errors") or ["no output produced"]
        return {"name": example.name, "error": str(err), "output": None, "scores": {}}

    output = update[out_key]
    scores: list[EvalScore] = evaluators.evaluate_output(agent, output, example.expected, judge)
    return {
        "name": example.name,
        "error": None,
        "output": output,
        "scores": {s.metric: {"score": s.score, "reason": s.reason} for s in scores},
    }


def _aggregate_agent(example_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Average each metric across the examples of one agent."""
    metric_totals: dict[str, list[float]] = {}
    for res in example_results:
        for metric, payload in res["scores"].items():
            metric_totals.setdefault(metric, []).append(payload["score"])

    metric_averages = {
        m: round(sum(vals) / len(vals), 3) for m, vals in metric_totals.items()
    }
    average = (
        round(sum(metric_averages.values()) / len(metric_averages), 3)
        if metric_averages
        else 0.0
    )
    return {"metric_averages": metric_averages, "average": average}


def _run(
    agents: list[str],
    get_llm: Optional[Callable[..., Any]] | str,
    mode: str,
    judge: Optional[evaluators.LLMJudge],
) -> dict[str, Any]:
    """Shared driver for both offline and online modes."""
    nodes = _load_nodes()
    agents_out: dict[str, Any] = {}
    errors: list[str] = []

    with _patched_llm(get_llm):
        for agent in agents:
            if agent not in nodes:
                raise ValueError(f"Unknown agent '{agent}'. Available: {list(nodes)}")
            example_results = [
                _run_example(nodes[agent], agent, ex, judge)
                for ex in get_dataset(agent)
            ]
            for res in example_results:
                if res["error"]:
                    errors.append(f"{agent}/{res['name']}: {res['error']}")
            agg = _aggregate_agent(example_results)
            agents_out[agent] = {"examples": example_results, **agg}

    # Overall roll-up across all agents/metrics.
    all_metric_vals: dict[str, list[float]] = {}
    num_examples = 0
    for agent_data in agents_out.values():
        num_examples += len(agent_data["examples"])
        for metric, val in agent_data["metric_averages"].items():
            all_metric_vals.setdefault(metric, []).append(val)

    metric_averages = {
        m: round(sum(v) / len(v), 3) for m, v in all_metric_vals.items()
    }
    overall = (
        round(sum(metric_averages.values()) / len(metric_averages), 3)
        if metric_averages
        else 0.0
    )

    return {
        "mode": mode,
        "agents": agents_out,
        "summary": {
            "overall_score": overall,
            "metric_averages": metric_averages,
            "num_agents": len(agents_out),
            "num_examples": num_examples,
            "errors": errors,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────

def run_offline(
    agents: Optional[list[str]] = None,
    get_llm: Optional[Callable[..., Any]] | str = None,
    judge: Optional[evaluators.LLMJudge] = None,
) -> dict[str, Any]:
    """Run the offline (schema + rule-based) evaluation.

    Args:
        agents: agent names to evaluate (defaults to all six).
        get_llm: ``None`` -> built-in offline fake; a callable -> injected
            factory (patched onto ``app.agents.llm.get_llm``); the string
            ``"current"`` -> leave the module's ``get_llm`` as-is (respect an
            external pytest monkeypatch).
        judge: optional extra evaluator (normally ``None`` offline).

    Returns:
        A JSON-serializable results dict (see module docstring for shape).
    """
    agents = agents or list_agents()
    factory: Optional[Callable[..., Any]] | str
    factory = get_fake_llm if get_llm is None else get_llm
    return _run(agents, factory, mode="offline", judge=judge)


def run_online(
    agents: Optional[list[str]] = None,
    use_judge: bool = True,
    use_langsmith: bool = False,
    get_llm: Optional[Callable[..., Any]] | str = USE_CURRENT,
) -> dict[str, Any]:
    """Run online evaluation against the real Gemini client.

    Requires ``GEMINI_API_KEY`` (unless a fake ``get_llm`` is injected). When
    ``use_judge`` is set, an LLM-as-judge relevance score is added. When
    ``use_langsmith`` is set, ``langsmith`` is imported lazily and a dataset run
    is logged; if ``langsmith`` isn't installed this degrades to a note rather
    than an error.
    """
    import os

    agents = agents or list_agents()

    if get_llm == USE_CURRENT and not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError(
            "run_online requires GEMINI_API_KEY (or inject get_llm=<factory>). "
            "Use run_offline() for keyless evaluation."
        )

    judge = evaluators.make_llm_judge(None if get_llm == USE_CURRENT else get_llm) if use_judge else None

    results = _run(agents, get_llm, mode="online", judge=judge)

    if use_langsmith:
        results["summary"]["langsmith"] = _maybe_log_langsmith(results)

    return results


def _maybe_log_langsmith(results: dict[str, Any]) -> str:
    """Best-effort LangSmith note; imported lazily so offline never needs it."""
    try:
        import langsmith  # noqa: F401
    except Exception:
        return "langsmith not installed — skipped online logging"
    # Actual dataset/experiment upload is left to the LangSmith-owning agent;
    # here we simply confirm the client is importable and configured.
    try:
        from app.langsmith_config import tracing_status

        status = tracing_status()
        return f"langsmith available; tracing_status={status}"
    except Exception as exc:  # pragma: no cover - defensive
        return f"langsmith available but status check failed: {exc}"


def summarize(results: dict[str, Any]) -> str:
    """Render a short markdown 'AI quality report' from a results dict."""
    summary = results.get("summary", {})
    agents = results.get("agents", {})

    # Column order: offline metrics first, then any extras (e.g. llm_relevance).
    metric_order: list[str] = list(evaluators.OFFLINE_EVALUATORS)
    for agent_data in agents.values():
        for metric in agent_data["metric_averages"]:
            if metric not in metric_order:
                metric_order.append(metric)

    lines: list[str] = []
    lines.append(f"# AI Quality Report ({results.get('mode', 'offline')})")
    lines.append("")
    lines.append(
        f"- Overall score: **{summary.get('overall_score', 0.0)}**  "
        f"({summary.get('num_agents', 0)} agents, {summary.get('num_examples', 0)} examples)"
    )
    if summary.get("errors"):
        lines.append(f"- Errors: {len(summary['errors'])}")
    lines.append("")

    header = "| Agent | " + " | ".join(metric_order) + " | Avg |"
    divider = "|" + "---|" * (len(metric_order) + 2)
    lines.append(header)
    lines.append(divider)

    for agent, data in agents.items():
        cells = [
            f"{data['metric_averages'].get(m, '-')}" for m in metric_order
        ]
        lines.append(f"| {agent} | " + " | ".join(cells) + f" | {data['average']} |")

    # Overall row.
    overall_cells = [
        f"{summary.get('metric_averages', {}).get(m, '-')}" for m in metric_order
    ]
    lines.append(
        f"| **overall** | " + " | ".join(overall_cells) + f" | {summary.get('overall_score', 0.0)} |"
    )

    if summary.get("errors"):
        lines.append("")
        lines.append("## Errors")
        for err in summary["errors"]:
            lines.append(f"- {err}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the LangGraph agents")
    parser.add_argument(
        "--agent",
        choices=list_agents(),
        help="Evaluate a single agent (default: all).",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Use the real Gemini client (requires GEMINI_API_KEY).",
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Disable the LLM-as-judge relevance score in online mode.",
    )
    parser.add_argument(
        "--langsmith",
        action="store_true",
        help="Enable LangSmith logging in online mode.",
    )
    parser.add_argument("--output", help="Also write the raw results JSON here.")
    args = parser.parse_args(argv)

    agents = [args.agent] if args.agent else None

    if args.online:
        results = run_online(
            agents=agents,
            use_judge=not args.no_judge,
            use_langsmith=args.langsmith,
        )
    else:
        results = run_offline(agents=agents)

    report = summarize(results)
    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, default=str)
        print(f"\nRaw results written to {args.output}")

    # Non-zero exit if anything errored, so CI can gate on it.
    return 1 if results["summary"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
