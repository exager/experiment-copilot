"""Integration tests for the compiled graph: human-in-the-loop pause/resume.

See the plan's "Testing the human-in-the-loop pause/resume" section: these
two graph.invoke() calls on the same thread_id stand in for two separate
API requests ("Generate Experiment" and "Launch") happening at different
times, using an in-process MemorySaver checkpointer.
"""

from __future__ import annotations

from app.graph.builder import build_graph

INITIAL_STATE = {
    "business_goal": "Increase checkout conversion rate by 15%",
    "website": "https://www.shopmax.com",
    "current_flow": "cart -> checkout -> payment -> confirm",
    "feature": "Checkout Page - Payment Step",
    "pain_point": "Users abandon checkout during payment",
    "errors": [],
}


def test_graph_pauses_before_simulation_then_resumes_to_report(fake_llm):
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-thread-1"}}

    result = graph.invoke(INITIAL_STATE, config)
    snapshot = graph.get_state(config)

    # The key check: a bug that silently removes the interrupt would still
    # produce a "passing-looking" final report — assert it's paused, not done.
    assert snapshot.next == ("simulation_node",)
    assert result.get("hypothesis") is not None
    assert result.get("configuration") is not None
    assert result.get("validation") is not None
    assert result.get("metrics") is None
    assert result.get("report") is None

    resumed = graph.invoke(None, config)
    final_snapshot = graph.get_state(config)

    assert final_snapshot.next == ()
    assert resumed.get("metrics") is not None
    assert resumed.get("statistics") is not None
    assert resumed.get("report") is not None


def test_two_threads_do_not_leak_state(fake_llm):
    graph = build_graph()
    config_a = {"configurable": {"thread_id": "thread-a"}}
    config_b = {"configurable": {"thread_id": "thread-b"}}

    graph.invoke(INITIAL_STATE, config_a)
    graph.invoke(INITIAL_STATE, config_b)

    graph.invoke(None, config_a)  # resume only thread A

    assert graph.get_state(config_a).next == ()
    assert graph.get_state(config_b).next == ("simulation_node",)
