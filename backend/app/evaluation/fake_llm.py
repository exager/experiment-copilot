"""Self-contained offline fake LLM for the evaluation harness (Developer 4).

Mirrors the ``FakeLLM`` / ``FakeStructuredLLM`` pattern in
``backend/tests/conftest.py`` but lives inside the app package so the harness
can run standalone (``python -m app.evaluation.run_eval``) with **no API key
and no pytest**.

Unlike the conftest fake (one canned response per schema), this fake is
*scenario-aware*: it peeks at the rendered prompt text and returns a response
tailored to whichever golden scenario (ShopMax checkout vs. FinTrack trial) the
agent is currently processing. That keeps the relevance evaluator meaningful
across the multi-example datasets while remaining fully deterministic.

The canned responses are deliberately "good" outputs so a default offline run
demonstrates high scores; feed the harness a real or failing LLM to see lower
ones.
"""

from __future__ import annotations

from typing import Any

from . import _compat  # noqa: F401  (install app.models.experiment shim first)

from app.schemas.agent_outputs import (
    ContextUnderstanding,
    ExperimentConfigurationOutput,
    HypothesisOutput,
    RationaleOutput,
    ReportNarrative,
    TrafficSplit,
    ValidationEnrichment,
)

# Scenario keys.
_CHECKOUT = "checkout"
_TRIAL = "trial"


# Canned "good" responses per scenario, keyed by the structured-output schema
# the agent asks for.
_RESPONSES: dict[str, dict[type, Any]] = {
    _CHECKOUT: {
        ContextUnderstanding: ContextUnderstanding(
            product_type="E-Commerce Website",
            business_goal_summary="Increase checkout conversion rate",
            problem_identified="Users abandon the checkout at the payment step",
            experiment_area="Checkout Page",
            target_users="Returning Customers",
            ai_confidence=94,
        ),
        HypothesisOutput: HypothesisOutput(
            experiment_name="Checkout Simplification",
            hypothesis=(
                "Reducing checkout friction with one-click guest checkout will "
                "increase checkout conversion by lowering payment-step drop-off"
            ),
            primary_metric="Checkout Conversion",
            secondary_metrics=["Bounce Rate", "Average Order Value"],
            guardrail_metrics=["Payment Failure Rate"],
        ),
        ExperimentConfigurationOutput: ExperimentConfigurationOutput(
            feature_flag="checkout_v2_guest",
            audience="Returning customers",
            traffic_split=TrafficSplit(control=0.5, variant=0.5),
            duration_days=14,
            sample_size=12000,
            confidence_level=0.95,
            baseline_conversion_rate=0.32,
            expected_lift=0.1,
        ),
        ValidationEnrichment: ValidationEnrichment(
            validation_score=0.92,
            warnings=[],
            suggestions=["Monitor the payment failure rate closely during rollout"],
            explanation="The checkout experiment configuration is well-formed and approved.",
        ),
        RationaleOutput: RationaleOutput(
            rationale=(
                "The variant increased checkout conversion by 14% with 97% confidence, "
                "driven by the simpler one-click guest checkout flow."
            ),
        ),
        ReportNarrative: ReportNarrative(
            summary=(
                "The checkout simplification experiment significantly improved checkout "
                "conversion, validating the hypothesis that reducing friction lifts sales."
            ),
            next_steps=[
                "Roll out the new checkout to 100% of traffic",
                "Continue monitoring the payment failure guardrail metric",
            ],
        ),
    },
    _TRIAL: {
        ContextUnderstanding: ContextUnderstanding(
            product_type="SaaS Platform",
            business_goal_summary="Increase free-trial to paid conversion",
            problem_identified="Users drop off at the credit-card step during trial signup",
            experiment_area="Trial Signup Flow",
            target_users="New Trial Signups",
            ai_confidence=88,
        ),
        HypothesisOutput: HypothesisOutput(
            experiment_name="Frictionless Trial Signup",
            hypothesis=(
                "Removing the credit-card requirement at signup will increase "
                "trial-to-paid conversion by lowering the barrier to starting a trial"
            ),
            primary_metric="Trial-to-Paid Conversion",
            secondary_metrics=["Trial Signups", "Activation Rate"],
            guardrail_metrics=["Refund Rate"],
        ),
        ExperimentConfigurationOutput: ExperimentConfigurationOutput(
            feature_flag="trial_no_cc",
            audience="New trial signups",
            traffic_split=TrafficSplit(control=0.5, variant=0.5),
            duration_days=21,
            sample_size=8000,
            confidence_level=0.95,
            baseline_conversion_rate=0.18,
            expected_lift=0.08,
        ),
        ValidationEnrichment: ValidationEnrichment(
            validation_score=0.9,
            warnings=[],
            suggestions=["Watch the refund-rate guardrail once volume increases"],
            explanation="The trial-signup experiment configuration is well-formed and approved.",
        ),
        RationaleOutput: RationaleOutput(
            rationale=(
                "The trial-signup variant shows only a 3% lift and is not yet statistically "
                "significant, so the experiment should keep running before deciding."
            ),
        ),
        ReportNarrative: ReportNarrative(
            summary=(
                "The frictionless trial-signup experiment shows an early, not-yet-significant "
                "lift in trial-to-paid conversion and needs more data."
            ),
            next_steps=[
                "Let the trial experiment run longer to reach significance",
                "Keep monitoring the refund-rate guardrail metric",
            ],
        ),
    },
}


def _detect_scenario(prompt: str) -> str:
    """Pick a scenario from the rendered prompt text (defaults to checkout).

    Uses tokens that are distinctive to the FinTrack trial scenario's *injected
    state* and won't appear in a prompt template's own boilerplate/examples
    (avoid generic words like "saas"/"signup" that leak from few-shot text).
    """
    text = prompt.lower()
    trial_markers = (
        "fintrack",
        "trial_no_cc",
        "trial-to-paid",
        "frictionless trial",
        "free-trial",
        "no-credit-card",
    )
    if any(marker in text for marker in trial_markers):
        return _TRIAL
    return _CHECKOUT


class FakeStructuredLLM:
    """Returned by :meth:`FakeLLM.with_structured_output`."""

    def __init__(self, schema: type) -> None:
        self.schema = schema

    def invoke(self, prompt: str) -> Any:
        scenario = _detect_scenario(str(prompt))
        responses = _RESPONSES[scenario]
        if self.schema not in responses:
            raise KeyError(
                f"OfflineFakeLLM has no canned response for schema {self.schema!r}"
            )
        return responses[self.schema]


class FakeLLM:
    """Drop-in stand-in for ``ChatGoogleGenerativeAI`` in offline mode."""

    def with_structured_output(self, schema: type) -> FakeStructuredLLM:
        return FakeStructuredLLM(schema)


def get_fake_llm(*args: Any, **kwargs: Any) -> FakeLLM:
    """Factory matching the ``app.agents.llm.get_llm`` signature."""
    return FakeLLM()
