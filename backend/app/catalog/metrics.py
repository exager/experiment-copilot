"""Metric catalog.

Defines every metric the platform knows about, plus a `MetricSpec` describing:
  - kind (ratio, currency, duration, count)
  - direction (higher is better vs. lower is better)
  - eligible roles (primary / secondary / guardrail)
  - baseline (control-arm starting value used by the simulator)
  - unit (for display)

Downstream consumers:
  - Pydantic schemas validate agent output against this registry.
  - Simulation engine uses `kind` + `baseline` to pick a distribution.
  - Statistics engine uses `kind` to decide which test to run.
  - Recommendation engine uses `direction` to decide what "regression" means.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MetricKind(StrEnum):
    """The mathematical shape of a metric."""

    RATIO = "ratio"          # 0..1 (converters / users)
    CURRENCY = "currency"    # $ per user or per order
    DURATION = "duration"    # seconds or milliseconds
    COUNT = "count"          # integer count per user


class Direction(StrEnum):
    """Whether higher or lower values are considered better."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class MetricRole(StrEnum):
    """Roles a metric can play in an experiment."""

    PRIMARY = "primary"      # single success metric — gets the z-test
    SECONDARY = "secondary"  # supporting evidence
    GUARDRAIL = "guardrail"  # must not regress


@dataclass(frozen=True)
class MetricSpec:
    """Metadata describing a single metric."""

    id: str
    label: str
    kind: MetricKind
    direction: Direction
    eligible_roles: tuple[MetricRole, ...]
    baseline: float
    unit: str
    description: str

    def allows_role(self, role: MetricRole) -> bool:
        return role in self.eligible_roles


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_METRIC_LIST: tuple[MetricSpec, ...] = (
    MetricSpec(
        id="checkout_conversion",
        label="Checkout Conversion",
        kind=MetricKind.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.PRIMARY,),
        baseline=0.041,
        unit="%",
        description="Fraction of sessions that complete a checkout.",
    ),
    MetricSpec(
        id="add_to_cart_rate",
        label="Add-to-Cart Rate",
        kind=MetricKind.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.PRIMARY, MetricRole.SECONDARY),
        baseline=0.180,
        unit="%",
        description="Fraction of product-page sessions that add a product to cart.",
    ),
    MetricSpec(
        id="signup_completion_rate",
        label="Signup Completion Rate",
        kind=MetricKind.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.PRIMARY,),
        baseline=0.220,
        unit="%",
        description="Fraction of signup-page visitors who complete registration.",
    ),
    MetricSpec(
        id="search_click_through",
        label="Search Click-Through Rate",
        kind=MetricKind.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.PRIMARY, MetricRole.SECONDARY),
        baseline=0.310,
        unit="%",
        description="Fraction of search results pages that lead to a click.",
    ),
    MetricSpec(
        id="revenue_per_user",
        label="Revenue per User",
        kind=MetricKind.CURRENCY,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.PRIMARY, MetricRole.SECONDARY),
        baseline=6.20,
        unit="$",
        description="Average revenue generated per exposed user.",
    ),
    MetricSpec(
        id="average_order_value",
        label="Average Order Value",
        kind=MetricKind.CURRENCY,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.SECONDARY,),
        baseline=47.50,
        unit="$",
        description="Average value of a single order.",
    ),
    MetricSpec(
        id="session_duration",
        label="Session Duration",
        kind=MetricKind.DURATION,
        direction=Direction.HIGHER_IS_BETTER,
        eligible_roles=(MetricRole.SECONDARY,),
        baseline=128.0,
        unit="sec",
        description="Average length of a user session, in seconds.",
    ),
    MetricSpec(
        id="bounce_rate",
        label="Bounce Rate",
        kind=MetricKind.RATIO,
        direction=Direction.LOWER_IS_BETTER,
        eligible_roles=(MetricRole.GUARDRAIL,),
        baseline=0.240,
        unit="%",
        description="Fraction of sessions with a single page view.",
    ),
    MetricSpec(
        id="cart_abandonment_rate",
        label="Cart Abandonment Rate",
        kind=MetricKind.RATIO,
        direction=Direction.LOWER_IS_BETTER,
        eligible_roles=(MetricRole.GUARDRAIL,),
        baseline=0.680,
        unit="%",
        description="Fraction of carts that never reach checkout completion.",
    ),
    MetricSpec(
        id="page_load_time_ms",
        label="Page Load Time (ms)",
        kind=MetricKind.DURATION,
        direction=Direction.LOWER_IS_BETTER,
        eligible_roles=(MetricRole.GUARDRAIL,),
        baseline=1200.0,
        unit="ms",
        description="Average page load time in milliseconds.",
    ),
    MetricSpec(
        id="error_rate",
        label="Error Rate",
        kind=MetricKind.RATIO,
        direction=Direction.LOWER_IS_BETTER,
        eligible_roles=(MetricRole.GUARDRAIL,),
        baseline=0.008,
        unit="%",
        description="Fraction of sessions that hit a client-side error.",
    ),
)


METRICS: dict[str, MetricSpec] = {m.id: m for m in _METRIC_LIST}

METRIC_IDS: tuple[str, ...] = tuple(METRICS)

PRIMARY_METRICS: tuple[str, ...] = tuple(
    m.id for m in _METRIC_LIST if MetricRole.PRIMARY in m.eligible_roles
)
SECONDARY_METRICS: tuple[str, ...] = tuple(
    m.id for m in _METRIC_LIST if MetricRole.SECONDARY in m.eligible_roles
)
GUARDRAIL_METRICS: tuple[str, ...] = tuple(
    m.id for m in _METRIC_LIST if MetricRole.GUARDRAIL in m.eligible_roles
)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_metric(metric_id: str) -> MetricSpec:
    """Return the MetricSpec for `metric_id` or raise `KeyError`."""
    try:
        return METRICS[metric_id]
    except KeyError as exc:
        raise KeyError(
            f"Unknown metric {metric_id!r}. Registered: {list(METRICS)}"
        ) from exc


def is_valid_metric(metric_id: str) -> bool:
    return metric_id in METRICS


def is_valid_primary(metric_id: str) -> bool:
    return metric_id in METRICS and METRICS[metric_id].allows_role(MetricRole.PRIMARY)


def is_valid_secondary(metric_id: str) -> bool:
    return metric_id in METRICS and METRICS[metric_id].allows_role(
        MetricRole.SECONDARY
    )


def is_valid_guardrail(metric_id: str) -> bool:
    return metric_id in METRICS and METRICS[metric_id].allows_role(
        MetricRole.GUARDRAIL
    )