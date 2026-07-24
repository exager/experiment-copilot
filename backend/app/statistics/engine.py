"""Statistics engine.

Computes the standard A/B-test derived quantities from cumulative per-arm
counts:

  - control / variant conversion rates
  - conversion lift (relative % change of variant vs. control)
  - z-score and p-value from a two-proportion z-test
  - confidence = 1 - p_value
  - winner ("control" | "variant" | "inconclusive")
  - significance flag

The engine is intentionally pure: given the same inputs it always returns
the same output. All fixtures / seeds that we ship for the demo are tuned so
the variant wins — but the engine itself is unbiased, so any real numbers
will still surface the correct answer.
"""

from __future__ import annotations

import math
from typing import Literal

from scipy import stats as scipy_stats

from app.schemas.metrics import StatisticsOut

Winner = Literal["control", "variant", "inconclusive"]

# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def conversion_rate(conversions: int, users: int) -> float | None:
    """Return `conversions / users`, or None if the arm has zero users."""
    if users <= 0:
        return None
    return conversions / users


def conversion_lift(rate_control: float | None, rate_variant: float | None) -> float | None:
    """Relative lift of variant vs. control, e.g. 0.14 == +14%.

    Returns None if either rate is None or control rate is zero (undefined).
    """
    if rate_control is None or rate_variant is None:
        return None
    if rate_control == 0:
        return None
    return (rate_variant - rate_control) / rate_control


def two_proportion_z_test(
    conv_control: int,
    users_control: int,
    conv_variant: int,
    users_variant: int,
) -> tuple[float | None, float | None]:
    """Two-proportion z-test on cumulative counts.

    Returns `(z_score, p_value)`. Both are None when the test can't be run
    (either arm empty, or degenerate pooled proportion).
    """
    if users_control <= 0 or users_variant <= 0:
        return None, None

    p1 = conv_control / users_control
    p2 = conv_variant / users_variant

    pooled = (conv_control + conv_variant) / (users_control + users_variant)
    variance = pooled * (1 - pooled) * (1 / users_control + 1 / users_variant)
    if variance <= 0:
        return None, None

    z = (p2 - p1) / math.sqrt(variance)
    # Two-sided test — we care about "different" not "greater".
    p_value = 2 * (1 - scipy_stats.norm.cdf(abs(z)))
    return z, p_value


# ---------------------------------------------------------------------------
# Winner determination
# ---------------------------------------------------------------------------


def determine_winner(
    z_score: float | None,
    p_value: float | None,
    lift: float | None,
    *,
    confidence_threshold: float = 0.95,
    min_lift_threshold: float = 0.0,
) -> Winner:
    """Decide which arm wins.

    Rules:
      1. If we can't compute the test, → "inconclusive".
      2. If confidence < threshold, → "inconclusive".
      3. If |lift| < min_lift_threshold, → "inconclusive".
      4. Positive z (variant > control) → "variant".
      5. Negative z (control > variant) → "control".
    """
    if z_score is None or p_value is None or lift is None:
        return "inconclusive"
    confidence = 1.0 - p_value
    if confidence < confidence_threshold:
        return "inconclusive"
    if abs(lift) < min_lift_threshold:
        return "inconclusive"
    if z_score > 0:
        return "variant"
    if z_score < 0:
        return "control"
    return "inconclusive"


# ---------------------------------------------------------------------------
# Top-level compute
# ---------------------------------------------------------------------------


def compute_statistics(
    users_control: int,
    users_variant: int,
    conversion_control: int,
    conversion_variant: int,
    *,
    confidence_threshold: float = 0.95,
    min_lift_threshold: float = 0.0,
) -> StatisticsOut:
    """Compute the full StatisticsOut for one metrics snapshot.

    Parameters
    ----------
    users_control, users_variant : cumulative user counts per arm
    conversion_control, conversion_variant : cumulative converter counts per arm
    confidence_threshold : minimum confidence (default 0.95) to call a winner
    min_lift_threshold : minimum |lift| (default 0.0) to call a winner
    """
    rate_c = conversion_rate(conversion_control, users_control)
    rate_v = conversion_rate(conversion_variant, users_variant)
    lift = conversion_lift(rate_c, rate_v)
    z, p = two_proportion_z_test(
        conversion_control, users_control, conversion_variant, users_variant
    )
    confidence = None if p is None else 1.0 - p
    winner = determine_winner(
        z,
        p,
        lift,
        confidence_threshold=confidence_threshold,
        min_lift_threshold=min_lift_threshold,
    )
    is_significant = (
        confidence is not None and confidence >= confidence_threshold and winner != "inconclusive"
    )

    return StatisticsOut(
        p_value=p,
        confidence=confidence,
        conversion_lift=lift,
        z_score=z,
        control_conversion_rate=rate_c,
        variant_conversion_rate=rate_v,
        winner=winner,
        is_significant=is_significant,
    )


def compute_statistics_from_row(row, *, confidence_threshold: float = 0.95) -> StatisticsOut:
    """Convenience wrapper for a `Metrics` ORM row or plain dict."""

    def _get(key: str, default: int | float = 0):
        if isinstance(row, dict):
            return row.get(key, default)
        return getattr(row, key, default)

    return compute_statistics(
        users_control=int(_get("users_control")),
        users_variant=int(_get("users_variant")),
        conversion_control=int(_get("conversion_control")),
        conversion_variant=int(_get("conversion_variant")),
        confidence_threshold=confidence_threshold,
    )