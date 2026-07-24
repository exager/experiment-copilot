"""Explanation Agent node.

Decides the recommendation category with the configurable recommendation rule
engine (:mod:`app.rules`), then asks the LLM to narrate a single rationale
paragraph around that decision. The LLM never picks the category itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from app.agents import llm
from app.agents.llm import with_retry
from app.rules import load_recommendation_engine
from app.schemas.agent_outputs import RationaleOutput
from app.schemas.metrics import Recommendation, RecommendationOut

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "explanation.md").read_text()


def _rule_context(statistics: dict) -> dict[str, Any]:
    """Shape statistics into the dot-path context the recommendation rules use.

    ``guardrail.regression`` and ``progress.sample_ratio`` are supplied by the
    statistics layer once it tracks them; until then they default to safe
    values (no regression, run not exhausted) so the engine falls through to
    scale/stop/continue based on winner + confidence + lift.
    """
    return {
        "statistics": {
            "winner": statistics.get("winner"),
            "confidence": statistics.get("confidence") or 0.0,
            "conversion_lift": statistics.get("conversion_lift") or 0.0,
        },
        "guardrail": {"regression": bool(statistics.get("guardrail_regression", False))},
        "progress": {"sample_ratio": statistics.get("sample_ratio") or 0.0},
    }


def decide_recommendation(statistics: dict) -> Recommendation:
    """Return the recommendation category from the shared rule engine."""
    result = load_recommendation_engine().evaluate(_rule_context(statistics))
    return cast(Recommendation, result.decision)


@with_retry
def node(state: dict) -> dict:
    statistics = state.get("statistics") or {}
    hypothesis = state.get("hypothesis") or {}

    category = decide_recommendation(statistics)

    prompt = _PROMPT.format(
        hypothesis=hypothesis.get("hypothesis", ""),
        control_conversion_rate=statistics.get("control_conversion_rate"),
        variant_conversion_rate=statistics.get("variant_conversion_rate"),
        conversion_lift=statistics.get("conversion_lift"),
        confidence=statistics.get("confidence"),
        winner=statistics.get("winner"),
        recommendation=category,
    )
    model = llm.get_llm().with_structured_output(RationaleOutput)
    result: RationaleOutput = model.invoke(prompt)

    recommendation = RecommendationOut(
        recommendation=category,
        rationale=result.rationale,
        confidence=statistics.get("confidence") or 0.0,
    )
    return {"recommendation": recommendation.model_dump()}
