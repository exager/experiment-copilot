"""Integration tests for the compiled graph: human-in-the-loop pause.

The graph runs `context_agent -> hypothesis_agent` and then pauses at the
interrupt before `validation_agent`, so the user can review the proposed
hypothesis + success metrics before launching. Everything after the interrupt
(validation onward) is deferred to a future launch/resume phase.
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


def test_graph_pauses_after_hypothesis(fake_llm):
    graph = build_graph()
    config = {"configurable": {"thread_id": "test-thread-1"}}

    result = graph.invoke(INITIAL_STATE, config)
    snapshot = graph.get_state(config)

    # The key check: a bug that silently removes the interrupt would keep
    # running past hypothesis — assert it's paused right after hypothesis.
    assert snapshot.next == ("validation_agent",)
    assert result.get("context_understanding") is not None
    assert result.get("hypothesis") is not None
    # Nothing downstream of the interrupt should have run yet.
    assert result.get("configuration") is None
    assert result.get("validation") is None
    assert result.get("metrics") is None
    assert result.get("report") is None


def test_two_threads_do_not_leak_state(fake_llm):
    graph = build_graph()
    config_a = {"configurable": {"thread_id": "thread-a"}}
    config_b = {"configurable": {"thread_id": "thread-b"}}

    graph.invoke(INITIAL_STATE, config_a)
    graph.invoke(INITIAL_STATE, config_b)

    # Both threads independently pause at the same interrupt point.
    assert graph.get_state(config_a).next == ("validation_agent",)
    assert graph.get_state(config_b).next == ("validation_agent",)
