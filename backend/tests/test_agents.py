"""Unit tests for individual agent nodes and their deterministic helpers."""

from __future__ import annotations

from app.agents import (
    context_agent,
    experiment_design_agent,
    explanation_agent,
    hypothesis_agent,
    report_agent,
    validation_agent,
)
from app.agents.explanation_agent import decide_recommendation
from app.agents.report_agent import estimate_business_impact
from app.agents.validation_agent import evaluate_rules

CONTEXT_STATE = {
    "business_goal": "Increase checkout conversion by 15%",
    "website": "https://www.shopmax.com",
    "current_flow": "cart -> checkout -> payment -> confirm",
    "feature": "Checkout Page",
    "pain_point": "Users abandon checkout during payment",
    "errors": [],
}


def test_context_agent_node(fake_llm):
    result = context_agent.node(CONTEXT_STATE)
    assert result["context_understanding"]["ai_confidence"] == 94
    assert result["context_understanding"]["experiment_area"] == "Checkout Page"


def test_hypothesis_agent_node(fake_llm):
    result = hypothesis_agent.node(CONTEXT_STATE)
    assert result["hypothesis"]["primary_metric"] == "checkout_conversion"
    assert result["hypothesis"]["guardrail_metrics"]


def test_experiment_design_agent_node(fake_llm):
    state = {
        **CONTEXT_STATE,
        "hypothesis": {
            "experiment_name": "x",
            "hypothesis": "y",
            "primary_metric": "z",
            "secondary_metrics": [],
            "guardrail_metrics": [],
        },
    }
    result = experiment_design_agent.node(state)
    assert result["configuration"]["feature_flag"] == "checkout_v2"
    assert result["configuration"]["traffic_split"] == {"control": 0.5, "variant": 0.5}


def test_validation_agent_node(fake_llm):
    state = {
        **CONTEXT_STATE,
        "hypothesis": {
            "primary_metric": "Checkout Conversion",
            "guardrail_metrics": ["Payment Failure Rate"],
        },
        "configuration": {
            "feature_flag": "checkout_v2",
            "audience": "returning_users",
            "traffic_split": {"control": 0.5, "variant": 0.5},
            "duration_days": 14,
            "sample_size": 5000,
            "confidence_level": 0.95,
            "baseline_conversion_rate": 0.1,
            "expected_lift": 0.05,
        },
    }
    result = validation_agent.node(state)
    assert result["validation"]["decision"] == "approve"
    assert result["validation"]["validation_score"] == 0.92
    assert result["validation"]["rules_rejected"] == []


def test_explanation_agent_node(fake_llm):
    state = {
        **CONTEXT_STATE,
        "hypothesis": {"hypothesis": "y"},
        "statistics": {
            "confidence": 0.963,
            "conversion_lift": 0.144,
            "is_significant": True,
            "control_conversion_rate": 0.0433,
            "variant_conversion_rate": 0.0496,
            "winner": "variant",
        },
    }
    result = explanation_agent.node(state)
    assert result["recommendation"]["recommendation"] == "scale"
    assert result["recommendation"]["confidence"] == 0.963
    assert result["recommendation"]["rationale"]


def test_report_agent_node(fake_llm):
    state = {
        **CONTEXT_STATE,
        "hypothesis": {"hypothesis": "y"},
        "configuration": {},
        "statistics": {"conversion_lift": 0.144},
        "metrics": {"revenue_control": 542.0, "revenue_variant": 616.0},
        "recommendation": {"recommendation": "scale"},
    }
    result = report_agent.node(state)
    assert result["report"]["recommendation"] == "scale"
    assert result["report"]["summary"]
    assert result["report"]["next_steps"]
    assert result["report"]["details"]["business_goal"] == CONTEXT_STATE["business_goal"]


def test_node_catches_llm_failure_into_errors(failing_llm):
    result = hypothesis_agent.node({**CONTEXT_STATE})
    assert "errors" in result
    assert any("node" in msg for msg in result["errors"])


# ---- Deterministic helpers: no LLM involved, category must never depend on it ----


def test_decide_recommendation_scale():
    stats = {"winner": "variant", "confidence": 0.96, "conversion_lift": 0.14}
    assert decide_recommendation(stats) == "scale"


def test_decide_recommendation_stop_when_control_wins():
    stats = {"winner": "control", "confidence": 0.97, "conversion_lift": -0.05}
    assert decide_recommendation(stats) == "stop"


def test_decide_recommendation_continue_when_not_significant():
    stats = {"winner": "inconclusive", "confidence": 0.80, "conversion_lift": 0.03}
    assert decide_recommendation(stats) == "continue"


def test_decide_recommendation_rollback_on_guardrail_regression():
    stats = {
        "winner": "variant",
        "confidence": 0.95,
        "conversion_lift": 0.10,
        "guardrail_regression": True,
    }
    assert decide_recommendation(stats) == "rollback"


def test_estimate_business_impact_uses_revenue_when_available():
    impact = estimate_business_impact({"conversion_lift": 0.05}, {"revenue_control": 500, "revenue_variant": 550})
    assert "10.0%" in impact


def test_estimate_business_impact_falls_back_to_lift():
    impact = estimate_business_impact({"conversion_lift": 0.08}, {})
    assert "8.0%" in impact


def test_evaluate_rules_rejects_bad_traffic_split():
    result = evaluate_rules(
        {
            "traffic_split": {"control": 0.5, "variant": 0.6},
            "audience": "x",
            "duration_days": 10,
            "sample_size": 100,
            "feature_flag": "y",
        }
    )
    assert result.decision == "reject"
    assert any(r.rule_id == "traffic_split_sums_to_one" for r in result.rules_rejected)


def test_evaluate_rules_approves_sane_configuration():
    result = evaluate_rules(
        {
            "traffic_split": {"control": 0.5, "variant": 0.5},
            "audience": "x",
            "duration_days": 10,
            "sample_size": 5000,
            "feature_flag": "checkout_v2",
            "confidence_level": 0.95,
        },
        hypothesis={
            "primary_metric": "Checkout Conversion",
            "guardrail_metrics": ["Payment Failure Rate"],
        },
    )
    assert result.decision == "approve"
    assert not result.rules_rejected
