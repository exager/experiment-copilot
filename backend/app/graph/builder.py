"""LangGraph assembly: nodes, edges, human-in-the-loop interrupts, checkpointer.

Pipeline:
    context_agent -> hypothesis_agent -> [INTERRUPT: wait for metric review]
    -> experiment_design_agent -> validation_agent -> [INTERRUPT: wait for launch]
    -> simulation_node -> statistics_node -> explanation_agent -> report_agent -> END

Two human-in-the-loop pauses:
  1. Right after `hypothesis_agent` — the user reviews/edits the proposed
     success metrics before experiment design + validation run.
  2. Right after `validation_agent` — the user reviews the validated
     configuration before simulation actually runs.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents import (
    context_agent,
    experiment_design_agent,
    explanation_agent,
    hypothesis_agent,
    report_agent,
    validation_agent,
)
from app.graph.pending_nodes import simulation_node, statistics_node
from app.graph.state import ExperimentState
from app.langsmith_config import get_run_config


def build_graph():
    """Assemble and compile a fresh graph with its own checkpointer.

    Called directly (fresh instance) by tests that need isolation; wrapped
    by get_graph() below for a single shared instance in normal use.
    """
    graph = StateGraph(ExperimentState)

    graph.add_node("context_agent", context_agent.node)
    graph.add_node("hypothesis_agent", hypothesis_agent.node)
    graph.add_node("experiment_design_agent", experiment_design_agent.node)
    graph.add_node("validation_agent", validation_agent.node)
    graph.add_node("simulation_node", simulation_node)
    graph.add_node("statistics_node", statistics_node)
    graph.add_node("explanation_agent", explanation_agent.node)
    graph.add_node("report_agent", report_agent.node)

    graph.add_edge(START, "context_agent")
    graph.add_edge("context_agent", "hypothesis_agent")
    graph.add_edge("hypothesis_agent", "experiment_design_agent")
    graph.add_edge("experiment_design_agent", "validation_agent")
    graph.add_edge("validation_agent", "simulation_node")
    graph.add_edge("simulation_node", "statistics_node")
    graph.add_edge("statistics_node", "explanation_agent")
    graph.add_edge("explanation_agent", "report_agent")
    graph.add_edge("report_agent", END)

    checkpointer = MemorySaver()
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["experiment_design_agent", "simulation_node"],
    )


_graph = None


def get_graph():
    """Lazily-built, process-wide shared graph instance for real usage."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def start_experiment(thread_id: str, initial_state: dict) -> dict:
    """Run the graph up to the first pause, right after `hypothesis_agent`."""
    config = {
        "configurable": {"thread_id": thread_id},
        **get_run_config("experiment_pipeline.start", thread_id),
    }
    return get_graph().invoke(initial_state, config)


def resume_experiment(thread_id: str) -> dict:
    """Resume a paused graph from whichever interrupt it's currently sitting at."""
    config = {
        "configurable": {"thread_id": thread_id},
        **get_run_config("experiment_pipeline.resume", thread_id),
    }
    return get_graph().invoke(None, config)


def update_experiment_state(thread_id: str, values: dict) -> None:
    """Patch a paused thread's checkpointed state (e.g. an edited hypothesis)
    before resuming it — lets the API layer apply user edits without
    re-running any already-completed node."""
    config = {"configurable": {"thread_id": thread_id}}
    get_graph().update_state(config, values)


def get_experiment_snapshot(thread_id: str):
    """Inspect a thread's current checkpoint. `.next` is empty/falsy when the
    thread was never started or has already run to completion — callers use
    this to distinguish a graph-driven experiment (paused, resumable) from
    one created through the manual (non-graph) API path."""
    config = {"configurable": {"thread_id": thread_id}}
    return get_graph().get_state(config)
