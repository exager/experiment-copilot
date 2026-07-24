"""Explanation Agent node.

Decides the recommendation category with the shared `recommendation_service`
(the same rule engine `GET /experiments/{id}/metrics` uses), then asks the
LLM to narrate a single rationale paragraph around that decision. The LLM
never picks the category itself.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.schemas.agent_outputs import RationaleOutput
from app.schemas.metrics import Recommendation, RecommendationOut, StatisticsOut
from app.services import recommendation_service

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "explanation.md").read_text()


def decide_recommendation(statistics: dict) -> Recommendation:
    """Return the recommendation category from the shared rule engine.

    ``guardrail_regression`` / ``sample_ratio`` are extra keys `statistics`
    may carry (populated by `pending_nodes.statistics_node`); `StatisticsOut`
    ignores unknown fields, so passing the raw dict straight through is safe.
    """
    result = recommendation_service.recommend(
        StatisticsOut(**statistics),
        guardrail_regressed=bool(statistics.get("guardrail_regression", False)),
        sample_ratio=float(statistics.get("sample_ratio") or 0.0),
    )
    return result.recommendation


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
