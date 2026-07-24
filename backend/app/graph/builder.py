"""LangGraph assembly: nodes, edges, human-in-the-loop interrupt, checkpointer.

Pipeline:
    context_agent -> hypothesis_agent -> [INTERRUPT: wait for user launch]
    -> validation_agent -> simulation_node -> statistics_node
    -> explanation_agent -> report_agent -> END

The graph pauses right after `hypothesis_agent` so the user can review the
proposed hypothesis and success metrics. Everything after the interrupt
(validation onward) is wired for a future "launch"/resume phase and does not
run in the current hypothesis-review flow.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents import (
    context_agent,
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
    graph.add_node("validation_agent", validation_agent.node)
    graph.add_node("simulation_node", simulation_node)
    graph.add_node("statistics_node", statistics_node)
    graph.add_node("explanation_agent", explanation_agent.node)
    graph.add_node("report_agent", report_agent.node)

    graph.add_edge(START, "context_agent")
    graph.add_edge("context_agent", "hypothesis_agent")
    # `experiment_design_agent` removed: pause after hypothesis for user review.
    graph.add_edge("hypothesis_agent", "validation_agent")
    graph.add_edge("validation_agent", "simulation_node")
    graph.add_edge("simulation_node", "statistics_node")
    graph.add_edge("statistics_node", "explanation_agent")
    graph.add_edge("explanation_agent", "report_agent")
    graph.add_edge("report_agent", END)

    checkpointer = MemorySaver()
    # Pause right after `hypothesis_agent` so the user can review the proposed
    # hypothesis + success metrics before anything downstream runs.
    return graph.compile(checkpointer=checkpointer, interrupt_before=["validation_agent"])


_graph = None


def get_graph():
    """Lazily-built, process-wide shared graph instance for real usage."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def start_experiment(thread_id: str, initial_state: dict) -> dict:
    """Run the graph up to the human-in-the-loop pause before simulation."""
    config = {
        "configurable": {"thread_id": thread_id},
        **get_run_config("experiment_pipeline.start", thread_id),
    }
    return get_graph().invoke(initial_state, config)


def resume_experiment(thread_id: str) -> dict:
    """Resume a paused graph after the user launches the experiment."""
    config = {
        "configurable": {"thread_id": thread_id},
        **get_run_config("experiment_pipeline.resume", thread_id),
    }
    return get_graph().invoke(None, config)
