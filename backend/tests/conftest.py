"""Shared pytest fixtures for the agent/graph test suite.

Historically this file installed a fake `app.models.experiment` module in
`sys.modules` because the real ORM didn't exist yet. It does now, so we
only fall back to the fake when the real module can't be imported (e.g.
a broken working tree).
"""

from __future__ import annotations

import enum
import importlib
import sys
import types

try:
    importlib.import_module("app.models.experiment")
except Exception:  # pragma: no cover — only used when the real model is broken
    if "app.models.experiment" not in sys.modules:
        _fake_experiment_model = types.ModuleType("app.models.experiment")

        class ExperimentStatus(str, enum.Enum):
            DRAFT = "draft"
            VALIDATED = "validated"
            RUNNING = "running"
            COMPLETED = "completed"
            STOPPED = "stopped"

        _fake_experiment_model.ExperimentStatus = ExperimentStatus
        sys.modules["app.models.experiment"] = _fake_experiment_model

import pytest

from app.schemas.agent_outputs import (
    ContextUnderstanding,
    ExperimentConfigurationOutput,
    HypothesisOutput,
    RationaleOutput,
    ReportNarrative,
    TrafficSplit,
    ValidationEnrichment,
)

FAKE_RESPONSES = {
    ContextUnderstanding: ContextUnderstanding(
        product_type="E-Commerce Website",
        business_goal_summary="Increase checkout conversion",
        problem_identified="Users abandon checkout during payment",
        experiment_area="Checkout Page",
        target_users="Returning Customers",
        ai_confidence=94,
    ),
    HypothesisOutput: HypothesisOutput(
        experiment_name="Checkout Simplification",
        hypothesis="Reducing checkout friction improves conversion",
        primary_metric="Checkout Conversion",
        secondary_metrics=["Bounce Rate", "Average Order Value"],
        guardrail_metrics=["Payment Failure Rate"],
    ),
    ExperimentConfigurationOutput: ExperimentConfigurationOutput(
        feature_flag="checkout_v2",
        audience="Returning customers",
        traffic_split=TrafficSplit(control=0.5, variant=0.5),
        duration_days=14,
        sample_size=5000,
    ),
    ValidationEnrichment: ValidationEnrichment(
        validation_score=0.92, warnings=[], suggestions=[], explanation="Looks good"
    ),
    RationaleOutput: RationaleOutput(
        rationale="Variant B increased conversion by 14%, driven by a simpler checkout flow."
    ),
    ReportNarrative: ReportNarrative(
        summary="Checkout simplification improved conversion significantly.",
        next_steps=["Roll out to 100%"],
    ),
}


class FakeStructuredLLM:
    def __init__(self, schema):
        self.schema = schema

    def invoke(self, prompt):
        return FAKE_RESPONSES[self.schema]


class FakeLLM:
    def with_structured_output(self, schema):
        return FakeStructuredLLM(schema)


class RaisingStructuredLLM:
    def invoke(self, prompt):
        raise RuntimeError("simulated LLM failure")


class RaisingLLM:
    def with_structured_output(self, schema):
        return RaisingStructuredLLM()


@pytest.fixture
def fake_llm(monkeypatch):
    """Patches app.agents.llm.get_llm to return fixed structured responses."""
    monkeypatch.setattr("app.agents.llm.get_llm", lambda *a, **kw: FakeLLM())


@pytest.fixture
def failing_llm(monkeypatch):
    """Patches app.agents.llm.get_llm so every call raises, for retry/error tests."""
    monkeypatch.setattr("app.agents.llm.get_llm", lambda *a, **kw: RaisingLLM())
