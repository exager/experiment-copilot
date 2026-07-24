"""Product Context node — first step in the LangGraph pipeline.

Reads the raw product context fields and produces a structured summary
that powers the "AI Understanding" card in the New Experiment UI.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.schemas.agent_outputs import ContextUnderstanding

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "context_understanding.md").read_text()


@with_retry
def node(state: dict) -> dict:
    prompt = _PROMPT.format(
        business_goal=state.get("business_goal", ""),
        website=state.get("website") or "not provided",
        current_flow=state.get("current_flow") or "not provided",
        feature=state.get("feature") or "not provided",
        pain_point=state.get("pain_point") or "not provided",
    )
    model = llm.get_llm().with_structured_output(ContextUnderstanding)
    result: ContextUnderstanding = model.invoke(prompt)
    return {"context_understanding": result.model_dump()}
