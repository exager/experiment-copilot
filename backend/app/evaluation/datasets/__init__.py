"""Golden evaluation datasets for the six LangGraph agents (Developer 4).

Each :class:`Example` bundles:

* ``input_state`` — an ``ExperimentState``-shaped dict passed straight to the
  target agent's ``node(state)`` function (the agents read state via
  ``state.get(...)``).
* ``expected`` — lightweight "what a good output looks like" hints consumed by
  the evaluators in :mod:`app.evaluation.evaluators` (relevance keywords,
  minimum list lengths, expected decision, etc.). These are intentionally
  loose: the offline harness scores *properties* of the output, not exact
  string matches.

Two end-to-end scenarios are modelled so every agent gets a couple of golden
examples that stay consistent as data flows down the pipeline:

* **ShopMax** — an e-commerce checkout-conversion experiment. This is the same
  scenario used by ``backend/tests/conftest.py`` so the harness lines up with
  the existing fake-LLM fixtures.
* **FinTrack** — a SaaS free-trial-to-paid experiment, for a little variety.

Public API::

    from app.evaluation.datasets import Example, get_dataset, list_agents, DATASETS
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Example:
    """A single golden example for one agent."""

    name: str
    agent: str
    input_state: dict[str, Any]
    expected: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def state(self) -> dict[str, Any]:
        """A fresh, mutable copy of the input state for a node to consume."""
        import copy

        return copy.deepcopy(self.input_state)


# ─────────────────────────────────────────────────────────────────────────
# Scenario A — ShopMax checkout conversion (matches conftest.py)
# ─────────────────────────────────────────────────────────────────────────

SHOPMAX_CONTEXT: dict[str, Any] = {
    "business_goal": "Increase checkout conversion rate",
    "website": "shopmax.com",
    "current_flow": "A 5-step checkout that forces shoppers to create an account before paying",
    "feature": "One-click guest checkout",
    "pain_point": "Most users abandon the checkout at the payment step",
}

SHOPMAX_HYPOTHESIS: dict[str, Any] = {
    "experiment_name": "Checkout Simplification",
    "hypothesis": (
        "Reducing checkout friction with a one-click guest checkout will "
        "increase checkout conversion, because fewer steps lower payment-step drop-off"
    ),
    "primary_metric": "Checkout Conversion",
    "secondary_metrics": ["Bounce Rate", "Average Order Value"],
    "guardrail_metrics": ["Payment Failure Rate"],
}

SHOPMAX_CONFIG: dict[str, Any] = {
    "feature_flag": "checkout_v2_guest",
    "audience": "Returning customers",
    "traffic_split": {"control": 0.5, "variant": 0.5},
    "duration_days": 14,
    "sample_size": 12000,
    "confidence_level": 0.95,
    "baseline_conversion_rate": 0.32,
    "expected_lift": 0.1,
}

SHOPMAX_STATISTICS: dict[str, Any] = {
    "p_value": 0.01,
    "confidence": 0.97,
    "conversion_lift": 0.14,
    "z_score": 2.6,
    "control_conversion_rate": 0.32,
    "variant_conversion_rate": 0.365,
    "winner": "variant",
    "is_significant": True,
}

SHOPMAX_METRICS: dict[str, Any] = {
    "revenue_control": 100000.0,
    "revenue_variant": 114000.0,
}

SHOPMAX_RECOMMENDATION: dict[str, Any] = {
    "recommendation": "scale",
    "rationale": "Variant B increased checkout conversion by 14% with 97% confidence.",
    "confidence": 0.97,
}


# ─────────────────────────────────────────────────────────────────────────
# Scenario B — FinTrack SaaS free-trial conversion
# ─────────────────────────────────────────────────────────────────────────

FINTRACK_CONTEXT: dict[str, Any] = {
    "business_goal": "Increase free-trial to paid conversion",
    "website": "fintrack.io",
    "current_flow": "A 14-day trial that requires a credit card up front during signup",
    "feature": "No-credit-card trial signup",
    "pain_point": "Users drop off at the credit-card step during trial signup",
}

FINTRACK_HYPOTHESIS: dict[str, Any] = {
    "experiment_name": "Frictionless Trial Signup",
    "hypothesis": (
        "Removing the credit-card requirement at signup will increase trial-to-paid "
        "conversion, because it lowers the barrier to starting a trial"
    ),
    "primary_metric": "Trial-to-Paid Conversion",
    "secondary_metrics": ["Trial Signups", "Activation Rate"],
    "guardrail_metrics": ["Refund Rate"],
}

FINTRACK_CONFIG: dict[str, Any] = {
    "feature_flag": "trial_no_cc",
    "audience": "New trial signups",
    "traffic_split": {"control": 0.5, "variant": 0.5},
    "duration_days": 21,
    "sample_size": 8000,
    "confidence_level": 0.95,
    "baseline_conversion_rate": 0.18,
    "expected_lift": 0.08,
}

FINTRACK_STATISTICS: dict[str, Any] = {
    "p_value": 0.2,
    "confidence": 0.8,
    "conversion_lift": 0.03,
    "z_score": 1.1,
    "control_conversion_rate": 0.18,
    "variant_conversion_rate": 0.185,
    "winner": "inconclusive",
    "is_significant": False,
}

FINTRACK_METRICS: dict[str, Any] = {
    "revenue_control": 50000.0,
    "revenue_variant": 51500.0,
}

FINTRACK_RECOMMENDATION: dict[str, Any] = {
    "recommendation": "continue",
    "rationale": "The trial-signup lift is not yet statistically significant.",
    "confidence": 0.8,
}


# ─────────────────────────────────────────────────────────────────────────
# Per-agent golden datasets
# ─────────────────────────────────────────────────────────────────────────

CONTEXT_DATASET: list[Example] = [
    Example(
        name="shopmax_checkout",
        agent="context",
        input_state=dict(SHOPMAX_CONTEXT),
        expected={"keywords": ["checkout", "conversion"]},
        notes="Should recognise an e-commerce checkout-conversion problem with high confidence.",
    ),
    Example(
        name="fintrack_trial",
        agent="context",
        input_state=dict(FINTRACK_CONTEXT),
        expected={"keywords": ["trial", "signup"]},
        notes="Should recognise a SaaS trial-signup conversion problem.",
    ),
]

HYPOTHESIS_DATASET: list[Example] = [
    Example(
        name="shopmax_checkout",
        agent="hypothesis",
        input_state=dict(SHOPMAX_CONTEXT),
        expected={"keywords": ["checkout"], "min_guardrails": 1, "min_secondary": 1},
        notes="Testable checkout hypothesis with at least one guardrail metric.",
    ),
    Example(
        name="fintrack_trial",
        agent="hypothesis",
        input_state=dict(FINTRACK_CONTEXT),
        expected={"keywords": ["trial", "signup"], "min_guardrails": 1, "min_secondary": 1},
        notes="Testable trial-signup hypothesis with at least one guardrail metric.",
    ),
]

EXPERIMENT_DESIGN_DATASET: list[Example] = [
    Example(
        name="shopmax_checkout",
        agent="experiment_design",
        input_state={"hypothesis": dict(SHOPMAX_HYPOTHESIS)},
        expected={"keywords": []},
        notes="Traffic split must sum to 1.0; duration/sample size must be sane.",
    ),
    Example(
        name="fintrack_trial",
        agent="experiment_design",
        input_state={"hypothesis": dict(FINTRACK_HYPOTHESIS)},
        expected={"keywords": []},
        notes="Traffic split must sum to 1.0; duration/sample size must be sane.",
    ),
]

VALIDATION_DATASET: list[Example] = [
    Example(
        name="shopmax_valid_config",
        agent="validation",
        input_state={
            "configuration": dict(SHOPMAX_CONFIG),
            "hypothesis": dict(SHOPMAX_HYPOTHESIS),
        },
        expected={"keywords": [], "expected_decision": "approve"},
        notes="A well-formed config should be approved with a high validation score.",
    ),
    Example(
        name="fintrack_valid_config",
        agent="validation",
        input_state={
            "configuration": dict(FINTRACK_CONFIG),
            "hypothesis": dict(FINTRACK_HYPOTHESIS),
        },
        expected={"keywords": [], "expected_decision": "approve"},
        notes="A well-formed config should be approved with a high validation score.",
    ),
]

EXPLANATION_DATASET: list[Example] = [
    Example(
        name="shopmax_significant_win",
        agent="explanation",
        input_state={
            "statistics": dict(SHOPMAX_STATISTICS),
            "hypothesis": dict(SHOPMAX_HYPOTHESIS),
        },
        expected={"keywords": ["conversion"], "expected_recommendation": "scale"},
        notes="Significant positive lift -> scale, with a rationale that cites the numbers.",
    ),
    Example(
        name="fintrack_inconclusive",
        agent="explanation",
        input_state={
            "statistics": dict(FINTRACK_STATISTICS),
            "hypothesis": dict(FINTRACK_HYPOTHESIS),
        },
        expected={"keywords": ["trial"], "expected_recommendation": "continue"},
        notes="Not significant -> continue; rationale should stay cautious.",
    ),
]

REPORT_DATASET: list[Example] = [
    Example(
        name="shopmax_scale_report",
        agent="report",
        input_state={
            "business_goal": SHOPMAX_CONTEXT["business_goal"],
            "hypothesis": dict(SHOPMAX_HYPOTHESIS),
            "configuration": dict(SHOPMAX_CONFIG),
            "statistics": dict(SHOPMAX_STATISTICS),
            "metrics": dict(SHOPMAX_METRICS),
            "recommendation": dict(SHOPMAX_RECOMMENDATION),
        },
        expected={"keywords": ["checkout"], "expected_recommendation": "scale"},
        notes="Executive summary plus concrete next steps consistent with 'scale'.",
    ),
    Example(
        name="fintrack_continue_report",
        agent="report",
        input_state={
            "business_goal": FINTRACK_CONTEXT["business_goal"],
            "hypothesis": dict(FINTRACK_HYPOTHESIS),
            "configuration": dict(FINTRACK_CONFIG),
            "statistics": dict(FINTRACK_STATISTICS),
            "metrics": dict(FINTRACK_METRICS),
            "recommendation": dict(FINTRACK_RECOMMENDATION),
        },
        expected={"keywords": ["trial"], "expected_recommendation": "continue"},
        notes="Executive summary plus next steps consistent with 'continue'.",
    ),
]


DATASETS: dict[str, list[Example]] = {
    "context": CONTEXT_DATASET,
    "hypothesis": HYPOTHESIS_DATASET,
    "experiment_design": EXPERIMENT_DESIGN_DATASET,
    "validation": VALIDATION_DATASET,
    "explanation": EXPLANATION_DATASET,
    "report": REPORT_DATASET,
}


def list_agents() -> list[str]:
    """Names of every agent that has a golden dataset."""
    return list(DATASETS)


def get_dataset(agent_name: str) -> list[Example]:
    """Return the golden examples for ``agent_name`` (raises if unknown)."""
    if agent_name not in DATASETS:
        raise ValueError(
            f"No dataset for '{agent_name}'. Available: {list(DATASETS)}"
        )
    return DATASETS[agent_name]
