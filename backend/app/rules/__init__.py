"""Configurable rule engine package.

Public API:
  - `RuleEngine`     — load & evaluate rules against a context.
  - `register_operator` / `get_operator` / `list_operators` — extensibility.
  - `load_validation_engine` / `load_recommendation_engine` — convenience
    factories that build engines from the bundled rule files.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.rules.engine import RuleEngine
from app.rules.registry import get_operator, list_operators, register_operator

_RULES_DIR = Path(__file__).parent
VALIDATION_RULES_PATH = _RULES_DIR / "validation_rules.json"
RECOMMENDATION_RULES_PATH = _RULES_DIR / "recommendation_rules.json"


def _recommendation_decider(results):
    """For recommendations, the highest-priority matched rule wins."""
    matched = [r for r in results if r.matched and r.decision]
    if not matched:
        return "continue"
    return max(matched, key=lambda r: r.priority).decision


@lru_cache(maxsize=1)
def load_validation_engine() -> RuleEngine:
    """Return a cached RuleEngine loaded from `validation_rules.json`."""
    return RuleEngine.from_json_file(VALIDATION_RULES_PATH)


@lru_cache(maxsize=1)
def load_recommendation_engine() -> RuleEngine:
    """Return a cached RuleEngine loaded from `recommendation_rules.json`."""
    return RuleEngine.from_json_file(
        RECOMMENDATION_RULES_PATH,
        decider=_recommendation_decider,
        default_decision="continue",
    )


__all__ = [
    "RuleEngine",
    "get_operator",
    "list_operators",
    "load_recommendation_engine",
    "load_validation_engine",
    "register_operator",
]