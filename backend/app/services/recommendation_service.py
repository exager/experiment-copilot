"""Recommendation service — decides scale/rollback/stop/continue.

Wraps the recommendation rule engine with a friendlier signature. The
`rationale` field carries the highest-priority matched rule's message;
Developer 4's Explanation Agent can overwrite it with an LLM narration.
"""

from __future__ import annotations

from app.rules import load_recommendation_engine
from app.schemas.metrics import RecommendationOut, StatisticsOut


def recommend(
    statistics: StatisticsOut,
    *,
    guardrail_regressed: bool = False,
    sample_ratio: float = 0.0,
) -> RecommendationOut:
    """Run the recommendation rules and return a `RecommendationOut`.

    Parameters
    ----------
    statistics : the latest StatisticsOut from `statistics_service.snapshot`
    guardrail_regressed : True if any guardrail metric is materially worse
        on variant (see `simulation.scheduler._guardrail_regressed`)
    sample_ratio : total users so far divided by target sample_size, in [0, 1]
    """
    ctx = {
        "statistics": {
            "winner": statistics.winner,
            "confidence": statistics.confidence or 0.0,
            "conversion_lift": statistics.conversion_lift or 0.0,
        },
        "guardrail": {"regression": bool(guardrail_regressed)},
        "progress": {"sample_ratio": max(0.0, min(1.0, float(sample_ratio)))},
    }
    result = load_recommendation_engine().evaluate(ctx)
    rationale = (
        result.rules_matched[0].message
        if result.rules_matched
        else result.explanation
    )
    return RecommendationOut(
        recommendation=result.decision,   # scale | continue | stop | rollback
        rationale=rationale or "",
        confidence=statistics.confidence or 0.0,
    )