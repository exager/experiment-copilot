"""Rule-operator registry — the extensibility hook of the rule engine.

Operators are small pure functions that take a `field_value` and a
`comparison_value` (both possibly None) and return `bool`. New operators can
be added without modifying the engine by using the `@register_operator`
decorator, so the platform can grow new rule types with minimal code change.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Callable

Operator = Callable[[Any, Any], bool]

_OPERATORS: dict[str, Operator] = {}


def register_operator(name: str) -> Callable[[Operator], Operator]:
    """Decorator to register a comparison operator under a given name."""

    def decorator(func: Operator) -> Operator:
        if name in _OPERATORS:
            raise ValueError(f"Operator already registered: {name!r}")
        _OPERATORS[name] = func
        return func

    return decorator


def get_operator(name: str) -> Operator:
    """Look up a registered operator by name.

    Raises `KeyError` if the operator is unknown so the engine can surface
    a helpful error to the caller.
    """
    try:
        return _OPERATORS[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown operator {name!r}. Registered: {sorted(_OPERATORS)}"
        ) from exc


def list_operators() -> list[str]:
    """Return every registered operator name (useful for API introspection)."""
    return sorted(_OPERATORS)


# --- Helpers ----------------------------------------------------------------


def _to_date(value: Any) -> date | None:
    """Best-effort coercion of common inputs to a `date`."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


# --- Numeric operators ------------------------------------------------------


@register_operator("eq")
def _eq(a: Any, b: Any) -> bool:
    return a == b


@register_operator("ne")
def _ne(a: Any, b: Any) -> bool:
    return a != b


@register_operator("gt")
def _gt(a: Any, b: Any) -> bool:
    return a is not None and b is not None and a > b


@register_operator("gte")
def _gte(a: Any, b: Any) -> bool:
    return a is not None and b is not None and a >= b


@register_operator("lt")
def _lt(a: Any, b: Any) -> bool:
    return a is not None and b is not None and a < b


@register_operator("lte")
def _lte(a: Any, b: Any) -> bool:
    return a is not None and b is not None and a <= b


@register_operator("between")
def _between(a: Any, b: Any) -> bool:
    """`b` must be a two-element sequence [low, high] (inclusive)."""
    if a is None or not isinstance(b, (list, tuple)) or len(b) != 2:
        return False
    low, high = b
    return low <= a <= high


# --- Boolean operator -------------------------------------------------------


@register_operator("is_true")
def _is_true(a: Any, _b: Any) -> bool:
    return bool(a)


@register_operator("is_false")
def _is_false(a: Any, _b: Any) -> bool:
    return not bool(a)


@register_operator("is_null")
def _is_null(a: Any, _b: Any) -> bool:
    return a is None


@register_operator("is_not_null")
def _is_not_null(a: Any, _b: Any) -> bool:
    return a is not None


# --- String operators -------------------------------------------------------


@register_operator("equals_ci")
def _equals_ci(a: Any, b: Any) -> bool:
    return isinstance(a, str) and isinstance(b, str) and a.lower() == b.lower()


@register_operator("contains")
def _contains(a: Any, b: Any) -> bool:
    return isinstance(a, str) and isinstance(b, str) and b in a


@register_operator("starts_with")
def _starts_with(a: Any, b: Any) -> bool:
    return isinstance(a, str) and isinstance(b, str) and a.startswith(b)


@register_operator("ends_with")
def _ends_with(a: Any, b: Any) -> bool:
    return isinstance(a, str) and isinstance(b, str) and a.endswith(b)


@register_operator("regex")
def _regex(a: Any, b: Any) -> bool:
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    try:
        return re.search(b, a) is not None
    except re.error:
        return False


@register_operator("in")
def _in(a: Any, b: Any) -> bool:
    return isinstance(b, (list, tuple, set)) and a in b


@register_operator("not_in")
def _not_in(a: Any, b: Any) -> bool:
    return isinstance(b, (list, tuple, set)) and a not in b


# --- Date operators ---------------------------------------------------------


@register_operator("before")
def _before(a: Any, b: Any) -> bool:
    da, db = _to_date(a), _to_date(b)
    return da is not None and db is not None and da < db


@register_operator("after")
def _after(a: Any, b: Any) -> bool:
    da, db = _to_date(a), _to_date(b)
    return da is not None and db is not None and da > db


@register_operator("on_or_before")
def _on_or_before(a: Any, b: Any) -> bool:
    da, db = _to_date(a), _to_date(b)
    return da is not None and db is not None and da <= db


@register_operator("on_or_after")
def _on_or_after(a: Any, b: Any) -> bool:
    da, db = _to_date(a), _to_date(b)
    return da is not None and db is not None and da >= db