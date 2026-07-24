"""
Evaluation datasets for the LangGraph agents (Developer 4).

Each example's ``input`` is an ExperimentState-shaped dict passed straight to the
corresponding agent ``node(state)``. ``expected`` holds values the ground-truth
checks assert against.
"""

from __future__ import annotations

from typing import Any

# ── Context / Hypothesis inputs (raw product context) ────────

_PRODUCT_CONTEXTS: list[dict[str, Any]] = [
    {
        "business_goal": "Increase checkout completion rate",
        "website": "ecommerce-store.com",
        "current_flow": "5-step checkout with separate shipping, billing, review pages",
        "feature": "Checkout page",
        "pain_point": "68% of users drop off at step 3 of checkout",
    },
    {
        "business_goal": "Increase user signups by 25%",
        "website": "saas-platform.com",
        "current_flow": "Landing page -> long signup form -> email verification -> onboarding",
        "feature": "Signup page",
        "pain_point": "Only 12% of landing page visitors complete signup; the form feels too long",
    },
    {
        "business_goal": "Reduce cart abandonment from 72% to under 60%",
        "website": "fashion-retail.com",
        "current_flow": "Browse -> add to cart -> cart page -> checkout",
        "feature": "Cart page",
        "pain_point": "Users add items but leave without checking out; no urgency or trust signals",
    },
]


CONTEXT_DATASET: list[dict[str, Any]] = [
    {"input": _PRODUCT_CONTEXTS[0], "expected": {}},
    {"input": _PRODUCT_CONTEXTS[1], "expected": {}},
    {"input": _PRODUCT_CONTEXTS[2], "expected": {}},
]


HYPOTHESIS_DATASET: list[dict[str, Any]] = [
    {
        "input": _PRODUCT_CONTEXTS[0],
        "expected": {"name_contains": "checkout", "min_guardrails": 1,
                     "hypothesis_mentions": ["checkout"]},
    },
    {
        "input": _PRODUCT_CONTEXTS[1],
        "expected": {"name_contains": "signup", "min_guardrails": 1,
                     "hypothesis_mentions": ["signup"]},
    },
    {
        "input": _PRODUCT_CONTEXTS[2],
        "expected": {"name_contains": "cart", "min_guardrails": 1,
                     "hypothesis_mentions": ["cart"]},
    },
]


# ── Experiment design inputs (need an upstream hypothesis in state) ──

EXPERIMENT_DESIGN_DATASET: list[dict[str, Any]] = [
    {
        "input": {
            **_PRODUCT_CONTEXTS[0],
            "hypothesis": {
                "experiment_name": "Streamlined Checkout",
                "hypothesis": "If we reduce checkout to 3 steps, checkout_completion_rate "
                "will increase by 10%, because fewer steps reduce friction.",
                "primary_metric": "checkout_completion_rate",
                "secondary_metrics": ["revenue_per_user"],
                "guardrail_metrics": ["page_load_time"],
            },
        },
        "expected": {},
    },
]


_DATASETS: dict[str, list[dict[str, Any]]] = {
    "context": CONTEXT_DATASET,
    "hypothesis": HYPOTHESIS_DATASET,
    "experiment_design": EXPERIMENT_DESIGN_DATASET,
}


def get_dataset(agent_name: str) -> list[dict[str, Any]]:
    if agent_name not in _DATASETS:
        raise ValueError(f"No dataset for '{agent_name}'. Available: {list(_DATASETS)}")
    return _DATASETS[agent_name]


def get_dataset_names() -> list[str]:
    return list(_DATASETS)
