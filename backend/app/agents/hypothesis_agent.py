"""Hypothesis Agent node.

Reads product context and proposes a testable hypothesis plus the metrics
that should judge it. Output powers the "Suggested Success Metrics" panel.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.schemas.agent_outputs import HypothesisOutput

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "hypothesis.md").read_text()


@with_retry
def node(state: dict) -> dict:
    prompt = _PROMPT.format(
        business_goal=state.get("business_goal", ""),
        website=state.get("website") or "not provided",
        current_flow=state.get("current_flow") or "not provided",
        feature=state.get("feature") or "not provided",
        pain_point=state.get("pain_point") or "not provided",
    )
    model = llm.get_llm().with_structured_output(HypothesisOutput)
    result: HypothesisOutput = model.invoke(prompt)
    return {"hypothesis": result.model_dump()}
