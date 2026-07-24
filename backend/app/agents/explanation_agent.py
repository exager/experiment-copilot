"""Explanation Agent node.

Decides the recommendation category deterministically from the computed
statistics, then asks the LLM to narrate a single rationale paragraph
around that decision. The LLM never picks the category itself.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.schemas.agent_outputs import RationaleOutput
from app.schemas.metrics import Recommendation, RecommendationOut

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "explanation.md").read_text()


def decide_recommendation(statistics: dict) -> Recommendation:
    """Deterministic recommendation rules.

    scale     - significant, positive lift above threshold
    stop      - lift is negative
    continue  - anything else (not yet conclusive)

    TODO: guardrail-metric regression isn't modeled in MetricPoint yet —
    once Dev 2 adds per-guardrail tracking, this should force "rollback"
    whenever a guardrail regresses materially, regardless of primary-metric
    lift, per the journey doc's rule set.
    """
    confidence = statistics.get("confidence") or 0.0
    lift = statistics.get("conversion_lift") or 0.0
    is_significant = statistics.get("is_significant", False)

    if lift < 0:
        return "stop"
    if is_significant and confidence >= 0.95 and lift > 0.05:
        return "scale"
    return "continue"


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
