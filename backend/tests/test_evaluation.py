"""End-to-end tests for the offline evaluation harness (Developer 4, Phase 4).

Runs the real agent nodes through the evaluation harness against a deterministic
fake LLM (no API key, no Gemini, no LangSmith) and asserts the returned scores
have the documented shape and sane value ranges.

Two LLM paths are exercised:

* ``run_offline()`` with the built-in scenario-aware fake
  (:mod:`app.evaluation.fake_llm`) — the standalone / CI path.
* the existing ``fake_llm`` conftest fixture + ``run_offline(get_llm="current")``
  — proves the harness respects an external pytest monkeypatch.

``conftest.py`` installs the ``app.models.experiment`` shim before these imports.
"""

from __future__ import annotations

from app.evaluation import run_offline, summarize
from app.evaluation.datasets import list_agents
from app.evaluation.evaluators import OFFLINE_EVALUATORS

ALL_AGENTS = list_agents()


def _assert_score(value: object, where: str) -> None:
    assert isinstance(value, (int, float)), f"{where} is not numeric: {value!r}"
    assert 0.0 <= float(value) <= 1.0, f"{where} out of 0..1 range: {value}"


def _assert_results_shape(results: dict) -> None:
    # Top-level keys.
    assert set(results) >= {"mode", "agents", "summary"}
    assert results["mode"] == "offline"

    agents = results["agents"]
    summary = results["summary"]

    # Summary shape and value ranges.
    assert set(summary) >= {
        "overall_score",
        "metric_averages",
        "num_agents",
        "num_examples",
        "errors",
    }
    _assert_score(summary["overall_score"], "summary.overall_score")
    assert summary["num_agents"] == len(agents)
    assert summary["num_agents"] >= 1, "no agents were evaluated"
    assert isinstance(summary["errors"], list)
    for metric, avg in summary["metric_averages"].items():
        _assert_score(avg, f"summary.metric_averages[{metric}]")

    # num_examples must match what the per-agent breakdown actually contains.
    total_examples = sum(len(data["examples"]) for data in agents.values())
    assert summary["num_examples"] == total_examples
    assert total_examples >= 1, "no examples were evaluated"

    # Per-agent breakdown.
    for name, data in agents.items():
        assert set(data) >= {"examples", "metric_averages", "average"}
        assert data["examples"], f"agent {name} has no example results"
        _assert_score(data["average"], f"agents[{name}].average")
        for metric, avg in data["metric_averages"].items():
            _assert_score(avg, f"agents[{name}].metric_averages[{metric}]")

        # Every example carries per-metric scores in range (unless it errored).
        for ex in data["examples"]:
            assert "name" in ex and "scores" in ex
            for metric, payload in ex["scores"].items():
                _assert_score(payload["score"], f"{name}/{ex['name']}.{metric}")


def test_run_offline_builtin_fake_full_shape() -> None:
    """Built-in fake: all six agents, high scores, no errors."""
    results = run_offline()

    _assert_results_shape(results)

    summary = results["summary"]
    assert summary["num_agents"] == len(ALL_AGENTS)
    assert set(results["agents"]) == set(ALL_AGENTS)
    # Two golden examples per agent are defined in the datasets module.
    assert summary["num_examples"] == 2 * len(ALL_AGENTS)

    # The canned fake outputs are deliberately "good", so the offline metric
    # suite should be present and the overall score high with zero errors.
    assert summary["errors"] == [], f"unexpected eval errors: {summary['errors']}"
    for metric in OFFLINE_EVALUATORS:
        assert metric in summary["metric_averages"], f"missing metric {metric}"
    assert summary["overall_score"] >= 0.9, (
        f"built-in fake should score high, got {summary['overall_score']}"
    )


def test_run_offline_single_agent() -> None:
    """Selecting one agent evaluates only that agent."""
    results = run_offline(agents=["report"])
    _assert_results_shape(results)
    assert set(results["agents"]) == {"report"}
    assert results["summary"]["num_agents"] == 1


def test_run_offline_respects_external_monkeypatch(fake_llm) -> None:
    """``get_llm="current"`` uses the conftest ``fake_llm`` fixture's patch."""
    results = run_offline(get_llm="current")

    _assert_results_shape(results)
    # The conftest fake returns schema-valid canned outputs, so nothing errors.
    assert results["summary"]["errors"] == [], (
        f"unexpected eval errors: {results['summary']['errors']}"
    )


def test_summarize_renders_markdown_report() -> None:
    results = run_offline(agents=["context"])
    report = summarize(results)

    assert isinstance(report, str)
    assert "AI Quality Report" in report
    assert "context" in report
    # The metric columns should appear in the rendered table header.
    for metric in OFFLINE_EVALUATORS:
        assert metric in report
