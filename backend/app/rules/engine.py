"""Configurable rule engine.

Loads rules from JSON/YAML/dict and evaluates them against a nested context
(dot-path field access). Every evaluation produces a `ValidationResult`
containing:

  - rules_evaluated : every rule considered
  - rules_matched   : rules whose conditions were satisfied
  - rules_rejected  : rules whose conditions were NOT satisfied
  - decision        : the final decision label
  - explanation     : a human-readable summary

Rule schema (JSON):

    {
      "id": "traffic_split_sums_to_1",
      "name": "Traffic split must sum to 1.0",
      "priority": 100,
      "when": {
        "op": "eq",
        "field": "configuration.traffic_split_sum",
        "value": 1.0
      },
      "on_match":   { "decision": "approve", "message": "Traffic split OK." },
      "on_mismatch":{ "decision": "reject",  "message": "Traffic split invalid." }
    }

Composite conditions:

    {"op": "and", "conditions": [ {...}, {...} ]}
    {"op": "or",  "conditions": [ {...}, {...} ]}
    {"op": "not", "condition":  {...}}

Any leaf condition uses an operator registered in `app.rules.registry`.

Decision aggregation
--------------------
Rules are evaluated in descending `priority` order (higher = evaluated
first). The engine's final decision is chosen by this precedence:

  1. Any active decision equal to `"reject"` wins.
  2. Otherwise the highest-priority active `decision` wins.
  3. If no rule fired an active decision, default to `"approve"`.

Callers may override this by passing a custom `decider` callable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterable

from app.rules.registry import get_operator
from app.schemas.validation import RuleResult, ValidationResult
from app.utils.errors import RuleEvaluationError

Decider = Callable[[list[RuleResult]], str]

_COMPOSITE_OPS = {"and", "or", "not"}


# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------


def _get_field(context: dict, path: str) -> Any:
    """Resolve a dot-path (e.g. `configuration.traffic_split.control`) in a dict."""
    node: Any = context
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------


def _evaluate_condition(condition: dict, context: dict) -> bool:
    """Recursively evaluate a condition tree against a context."""
    op = condition.get("op")
    if op is None:
        raise RuleEvaluationError(
            "Condition missing 'op' key", details={"condition": condition}
        )

    if op == "and":
        subs = condition.get("conditions", [])
        return all(_evaluate_condition(c, context) for c in subs)

    if op == "or":
        subs = condition.get("conditions", [])
        return any(_evaluate_condition(c, context) for c in subs)

    if op == "not":
        sub = condition.get("condition")
        if sub is None:
            raise RuleEvaluationError(
                "'not' condition requires 'condition' key",
                details={"condition": condition},
            )
        return not _evaluate_condition(sub, context)

    # Leaf: operator lookup + field extraction
    field_path = condition.get("field")
    if not field_path:
        raise RuleEvaluationError(
            f"Leaf condition {op!r} missing 'field'",
            details={"condition": condition},
        )
    value = condition.get("value")
    operator = get_operator(op)
    field_value = _get_field(context, field_path)
    try:
        return bool(operator(field_value, value))
    except Exception as exc:  # noqa: BLE001 - surface as engine error
        raise RuleEvaluationError(
            f"Operator {op!r} raised an error while evaluating field "
            f"{field_path!r}: {exc}",
            details={"condition": condition, "field_value": field_value},
        ) from exc


# ---------------------------------------------------------------------------
# Default decision aggregation
# ---------------------------------------------------------------------------


def _default_decider(results: list[RuleResult]) -> str:
    """Choose the final decision from a list of evaluated rules.

    Priority: any `reject` wins; otherwise the highest-priority active
    decision; otherwise `approve`.
    """
    active = [r for r in results if r.decision]
    if any(r.decision == "reject" for r in active):
        return "reject"
    if active:
        top = max(active, key=lambda r: r.priority)
        return top.decision or "approve"
    return "approve"


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _build_explanation(
    decision: str, matched: list[RuleResult], rejected: list[RuleResult]
) -> str:
    lines = [f"Decision: {decision}."]
    if matched:
        lines.append("Matched rules:")
        for r in matched:
            msg = f" - [{r.rule_id}] {r.name}"
            if r.message:
                msg += f" — {r.message}"
            lines.append(msg)
    if rejected:
        lines.append("Rejected rules:")
        for r in rejected:
            msg = f" - [{r.rule_id}] {r.name}"
            if r.message:
                msg += f" — {r.message}"
            lines.append(msg)
    if not matched and not rejected:
        lines.append("No rules were applicable.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RuleEngine
# ---------------------------------------------------------------------------


class RuleEngine:
    """Evaluate a set of configurable rules against a context."""

    def __init__(
        self,
        rules: Iterable[dict],
        *,
        decider: Decider | None = None,
        default_decision: str = "approve",
    ) -> None:
        self._rules: list[dict] = self._normalize_rules(rules)
        self._decider: Decider = decider or _default_decider
        self._default_decision = default_decision

    # ---- Loaders ----------------------------------------------------------

    @classmethod
    def from_json_file(cls, path: str | Path, **kwargs: Any) -> "RuleEngine":
        """Instantiate an engine from a JSON file with shape `{"rules": [...]}`."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rules = data["rules"] if isinstance(data, dict) else data
        return cls(rules, **kwargs)

    @classmethod
    def from_dict(cls, data: dict, **kwargs: Any) -> "RuleEngine":
        rules = data["rules"] if "rules" in data else []
        return cls(rules, **kwargs)

    # ---- Rule normalization ----------------------------------------------

    @staticmethod
    def _normalize_rules(rules: Iterable[dict]) -> list[dict]:
        normalized: list[dict] = []
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise RuleEvaluationError(
                    f"Rule at index {idx} is not an object", details={"rule": rule}
                )
            if "when" not in rule:
                raise RuleEvaluationError(
                    f"Rule {rule.get('id', idx)!r} missing 'when' clause",
                    details={"rule": rule},
                )
            rule = {**rule}
            rule.setdefault("id", f"rule_{idx}")
            rule.setdefault("name", rule["id"])
            rule.setdefault("priority", 0)
            rule.setdefault("on_match", {})
            rule.setdefault("on_mismatch", {})
            normalized.append(rule)
        # Higher priority first — stable sort keeps declaration order for ties.
        normalized.sort(key=lambda r: r["priority"], reverse=True)
        return normalized

    # ---- Public API -------------------------------------------------------

    @property
    def rules(self) -> list[dict]:
        """Return the normalized rule list (read-only view)."""
        return list(self._rules)

    def evaluate(self, context: dict) -> ValidationResult:
        """Evaluate all rules against `context` and return a ValidationResult."""
        evaluated: list[RuleResult] = []
        matched: list[RuleResult] = []
        rejected: list[RuleResult] = []

        for rule in self._rules:
            hit = _evaluate_condition(rule["when"], context)
            outcome = rule["on_match"] if hit else rule["on_mismatch"]
            result = RuleResult(
                rule_id=rule["id"],
                name=rule["name"],
                priority=rule["priority"],
                matched=hit,
                decision=outcome.get("decision"),
                message=outcome.get("message"),
                details=outcome.get("details", {}),
            )
            evaluated.append(result)
            (matched if hit else rejected).append(result)

        decision = self._decider(evaluated) or self._default_decision
        explanation = _build_explanation(decision, matched, rejected)

        return ValidationResult(
            rules_evaluated=evaluated,
            rules_matched=matched,
            rules_rejected=rejected,
            decision=decision,
            explanation=explanation,
        )