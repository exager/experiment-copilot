"""Scoring functions for agent outputs (Developer 4 evaluation harness).

Four offline, deterministic evaluators (no API key required):

* :func:`schema_validity` — does the output parse into the correct Pydantic
  schema from :mod:`app.schemas.agent_outputs`?
* :func:`completeness` — are the required fields present/non-empty and do lists
  meet minimum-length expectations (e.g. ``guardrail_metrics`` non-empty)?
* :func:`correctness` — rule-based consistency checks (traffic split sums to
  1.0, ``ai_confidence`` in 0–100, ``validation_score`` consistent with the
  rule-engine decision, recommendation category is valid, …).
* :func:`relevance` — lightweight keyword/heuristic coverage against the
  example's expected keywords.

Every evaluator returns an :class:`EvalScore` (``metric``, ``score`` in 0.0–1.0,
and a short human-readable ``reason``).

An optional LLM-as-judge relevance scorer (:func:`llm_relevance` /
:func:`make_llm_judge`) is provided for *online* mode only; it is never invoked
by the offline evaluators and imports nothing that requires a key at module
import time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Optional

from pydantic import BaseModel, ValidationError

from app.schemas.agent_outputs import (
    ContextUnderstanding,
    RationaleOutput,
    ReportNarrative,
    ValidationEnrichment,
)
from app.schemas.experiment import ExperimentConfiguration, Hypothesis

VALID_RECOMMENDATIONS = {"scale", "continue", "stop", "rollback"}


@dataclass
class EvalScore:
    """One metric's result for one output."""

    metric: str
    score: float  # normalized 0.0 – 1.0
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# agent -> (schema, subset_fields_or_None)
# ``None`` means validate the whole output dict; a list means validate only that
# subset of keys (used where the node merges LLM output with deterministic
# fields, so only part of the dict maps to an agent_outputs schema).
_SCHEMA_FOR_AGENT: dict[str, tuple[type[BaseModel], Optional[list[str]]]] = {
    "context": (ContextUnderstanding, None),
    "hypothesis": (Hypothesis, None),
    "experiment_design": (ExperimentConfiguration, None),
    "validation": (
        ValidationEnrichment,
        ["validation_score", "warnings", "suggestions", "explanation"],
    ),
    "explanation": (RationaleOutput, ["rationale"]),
    "report": (ReportNarrative, ["summary", "next_steps"]),
}

# Required (must be present & non-empty) fields per agent.
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "context": [
        "product_type",
        "business_goal_summary",
        "problem_identified",
        "experiment_area",
        "target_users",
        "ai_confidence",
    ],
    "hypothesis": ["experiment_name", "hypothesis", "primary_metric"],
    "experiment_design": [
        "feature_flag",
        "audience",
        "traffic_split",
        "duration_days",
        "sample_size",
    ],
    "validation": ["decision", "explanation", "validation_score"],
    "explanation": ["recommendation", "rationale", "confidence"],
    "report": ["summary", "recommendation", "next_steps"],
}

# List fields that must have at least N entries.
_MIN_LIST_LENGTHS: dict[str, dict[str, int]] = {
    "hypothesis": {"secondary_metrics": 1, "guardrail_metrics": 1},
    "report": {"next_steps": 1},
}


# ─────────────────────────────────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────────────────────────────────

def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return True  # numbers, bools count as present


def _collect_text(value: Any) -> str:
    """Flatten all string content in a nested structure to one lowercase blob."""
    parts: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, dict):
            for item in v.values():
                walk(item)
        elif isinstance(v, (list, tuple)):
            for item in v:
                walk(item)

    walk(value)
    return " ".join(parts).lower()


def _fraction(passed: int, total: int) -> float:
    return round(passed / total, 3) if total else 1.0


# ─────────────────────────────────────────────────────────────────────────
# Evaluators
# ─────────────────────────────────────────────────────────────────────────

def schema_validity(agent: str, output: dict[str, Any]) -> EvalScore:
    """1.0 if the (relevant subset of the) output parses into its schema."""
    if agent not in _SCHEMA_FOR_AGENT:
        return EvalScore("schema_validity", 0.0, f"unknown agent '{agent}'")

    schema, subset = _SCHEMA_FOR_AGENT[agent]
    payload = output if subset is None else {k: output.get(k) for k in subset}
    try:
        schema.model_validate(payload)
        return EvalScore("schema_validity", 1.0, f"parses as {schema.__name__}")
    except ValidationError as exc:
        errors = "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        return EvalScore("schema_validity", 0.0, f"{schema.__name__} invalid: {errors}")


def completeness(agent: str, output: dict[str, Any]) -> EvalScore:
    """Fraction of required fields present & non-empty (plus list-length rules)."""
    required = _REQUIRED_FIELDS.get(agent, [])
    checks: dict[str, bool] = {
        f"{field}_present": _is_nonempty(output.get(field)) for field in required
    }
    for field, minimum in _MIN_LIST_LENGTHS.get(agent, {}).items():
        value = output.get(field) or []
        checks[f"{field}_ge_{minimum}"] = isinstance(value, (list, tuple)) and len(value) >= minimum

    passed = sum(1 for ok in checks.values() if ok)
    missing = [name for name, ok in checks.items() if not ok]
    reason = "all required fields present" if not missing else f"missing/empty: {missing}"
    return EvalScore("completeness", _fraction(passed, len(checks)), reason)


def correctness(agent: str, output: dict[str, Any]) -> EvalScore:
    """Rule-based consistency checks; score = fraction of rules satisfied."""
    checks: dict[str, bool] = {}

    if agent == "context":
        conf = output.get("ai_confidence")
        checks["ai_confidence_int_0_100"] = isinstance(conf, int) and 0 <= conf <= 100

    elif agent == "hypothesis":
        checks["primary_metric_present"] = _is_nonempty(output.get("primary_metric"))
        checks["guardrails_non_empty"] = len(output.get("guardrail_metrics") or []) >= 1
        primary = (output.get("primary_metric") or "").strip().lower()
        secondaries = [s.strip().lower() for s in (output.get("secondary_metrics") or [])]
        checks["primary_not_in_secondary"] = primary not in secondaries if primary else True

    elif agent == "experiment_design":
        split = output.get("traffic_split") or {}
        total = (split.get("control") or 0) + (split.get("variant") or 0)
        checks["traffic_split_sums_to_one"] = abs(total - 1.0) < 1e-6
        checks["duration_in_range"] = 1 <= (output.get("duration_days") or 0) <= 365
        checks["sample_size_positive"] = (output.get("sample_size") or 0) >= 1
        checks["confidence_level_valid"] = 0.5 <= (output.get("confidence_level") or 0) <= 0.999
        checks["baseline_rate_valid"] = 0.0 <= (output.get("baseline_conversion_rate") or -1) <= 1.0
        checks["expected_lift_valid"] = -1.0 <= (output.get("expected_lift") or 0) <= 5.0

    elif agent == "validation":
        score = output.get("validation_score")
        checks["score_in_0_1"] = isinstance(score, (int, float)) and 0.0 <= score <= 1.0
        decision = output.get("decision")
        # Consistency: an "approve" decision should carry a passing score, a
        # "reject" a failing one.
        if decision == "approve" and isinstance(score, (int, float)):
            checks["score_consistent_with_decision"] = score >= 0.5
        elif decision == "reject" and isinstance(score, (int, float)):
            checks["score_consistent_with_decision"] = score < 0.5

    elif agent == "explanation":
        conf = output.get("confidence")
        checks["confidence_in_0_1"] = isinstance(conf, (int, float)) and 0.0 <= conf <= 1.0
        checks["recommendation_valid"] = output.get("recommendation") in VALID_RECOMMENDATIONS
        checks["rationale_present"] = _is_nonempty(output.get("rationale"))

    elif agent == "report":
        checks["recommendation_valid"] = output.get("recommendation") in VALID_RECOMMENDATIONS
        checks["next_steps_non_empty"] = len(output.get("next_steps") or []) >= 1
        checks["summary_present"] = _is_nonempty(output.get("summary"))

    if not checks:
        return EvalScore("correctness", 1.0, "no correctness rules for this agent")

    passed = sum(1 for ok in checks.values() if ok)
    failed = [name for name, ok in checks.items() if not ok]
    reason = "all rules satisfied" if not failed else f"failed: {failed}"
    return EvalScore("correctness", _fraction(passed, len(checks)), reason)


def relevance(agent: str, output: dict[str, Any], expected: dict[str, Any]) -> EvalScore:
    """Keyword-coverage heuristic against the example's expected keywords."""
    keywords = [k.lower() for k in (expected or {}).get("keywords", [])]
    if not keywords:
        return EvalScore("relevance", 1.0, "no keywords specified for this example")

    text = _collect_text(output)
    found = [k for k in keywords if k in text]
    missing = [k for k in keywords if k not in text]
    reason = f"matched {found}" + (f", missing {missing}" if missing else "")
    return EvalScore("relevance", _fraction(len(found), len(keywords)), reason)


# The offline metric suite, in report order.
OFFLINE_EVALUATORS = ("schema_validity", "completeness", "correctness", "relevance")


def evaluate_output(
    agent: str,
    output: dict[str, Any],
    expected: dict[str, Any] | None = None,
    judge: Optional["LLMJudge"] = None,
) -> list[EvalScore]:
    """Run every offline evaluator (plus the LLM judge if supplied)."""
    expected = expected or {}
    scores = [
        schema_validity(agent, output),
        completeness(agent, output),
        correctness(agent, output),
        relevance(agent, output, expected),
    ]
    if judge is not None:
        scores.append(judge(agent, output, expected))
    return scores


# ─────────────────────────────────────────────────────────────────────────
# Optional LLM-as-judge (ONLINE ONLY)
# ─────────────────────────────────────────────────────────────────────────

class _JudgeVerdict(BaseModel):
    """Structured output for the LLM relevance judge."""

    score: float
    reason: str


LLMJudge = Callable[[str, dict, dict], EvalScore]


def make_llm_judge(get_llm: Optional[Callable[..., Any]] = None) -> LLMJudge:
    """Build an LLM-as-judge relevance scorer for online mode.

    ``get_llm`` defaults to ``app.agents.llm.get_llm`` (a real Gemini client
    needing ``GEMINI_API_KEY``); inject your own for testing. The returned
    callable has the same ``(agent, output, expected) -> EvalScore`` signature
    as the offline evaluators, so it slots straight into
    :func:`evaluate_output`.
    """

    def _judge(agent: str, output: dict[str, Any], expected: dict[str, Any]) -> EvalScore:
        factory = get_llm
        if factory is None:
            from app.agents import llm as _llm  # lazy: avoids import at offline time

            factory = _llm.get_llm

        prompt = (
            "You are grading the output of an A/B-testing copilot agent for "
            "RELEVANCE and quality on a 0.0-1.0 scale.\n"
            f"Agent: {agent}\n"
            f"Reviewer notes / expectations: {expected}\n"
            f"Agent output (JSON): {output}\n\n"
            "Return a JSON object with a numeric 'score' between 0 and 1 and a "
            "one-sentence 'reason'."
        )
        try:
            model = factory().with_structured_output(_JudgeVerdict)
            verdict: _JudgeVerdict = model.invoke(prompt)
            score = max(0.0, min(1.0, float(verdict.score)))
            return EvalScore("llm_relevance", round(score, 3), verdict.reason)
        except Exception as exc:  # judge failures must never break a run
            return EvalScore("llm_relevance", 0.0, f"judge error: {exc}")

    return _judge
