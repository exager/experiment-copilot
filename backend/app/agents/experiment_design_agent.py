"""Experiment Design Agent node.

Turns the hypothesis into a launchable experiment configuration, including
the baseline/expected-lift assumptions that seed Dev 2's simulation engine.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.catalog import catalog_summary
from app.schemas.experiment import ExperimentConfiguration

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "experiment_design.md").read_text()


@with_retry
def node(state: dict) -> dict:
    hypothesis = state.get("hypothesis") or {}
    prompt = _PROMPT.format(
        experiment_name=hypothesis.get("experiment_name", ""),
        hypothesis=hypothesis.get("hypothesis", ""),
        primary_metric=hypothesis.get("primary_metric", ""),
        secondary_metrics=", ".join(hypothesis.get("secondary_metrics", [])),
        guardrail_metrics=", ".join(hypothesis.get("guardrail_metrics", [])),
        catalog=catalog_summary(),
    )
    # ExperimentConfiguration constrains audience/traffic-split to the catalog
    # and derives the concrete traffic_split from the chosen option.
    model = llm.get_llm().with_structured_output(ExperimentConfiguration)
    result: ExperimentConfiguration = model.invoke(prompt)
    return {"configuration": result.model_dump(mode="json")}
