"""Synthetic metrics generator.

Pure functions — no DB, no scheduler. Given a previous cumulative snapshot
and an experiment's configuration, `next_tick` returns a `TickDelta` with
new users, conversions, revenue, and bounce events per arm, plus per-tick
guardrail metric values.

The RNG is deterministic: `seeded_rng(experiment_id, tick_index)` returns
the same numpy Generator every time, so replaying a simulation with the
same seed produces the exact same series (great for tests and demo replay).

Distribution choices
--------------------
- New users per tick:  Poisson(λ = base_traffic * split_share)
- Conversions:         Binomial(new_users, arm_rate)
- Revenue per conv:    LogNormal(μ, σ)  (right-skewed, realistic AOV)
- Bounces:             Binomial(new_users, arm_bounce_rate)
- Guardrail metrics:   Normal / LogNormal draws around each MetricSpec baseline

Variant behavior
----------------
By default the variant conversion rate is
    baseline_conversion_rate * (1 + expected_lift)
so any positive `expected_lift` biases the simulation toward variant winning.
Guardrails default to *no regression* — bounce/page-load/error draws come
from the same distribution for both arms. To demo the rollback path, set
`SimulatorInputs.guardrail_regression=True`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from app.catalog import METRICS, MetricKind, MetricRole

# ---------------------------------------------------------------------------
# Deterministic RNG
# ---------------------------------------------------------------------------


def seeded_rng(experiment_id: int, tick_index: int) -> np.random.Generator:
    """Return a numpy Generator seeded from experiment_id + tick_index.

    Uses a mixing scheme so consecutive ticks are uncorrelated but the full
    sequence is fully reproducible for any (experiment_id, tick range).
    """
    # SplitMix-style 64-bit mix to spread the seed space.
    seed = (int(experiment_id) * 0x9E3779B97F4A7C15 + int(tick_index)) & ((1 << 63) - 1)
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SimulatorInputs:
    """Everything the generator needs to produce a tick.

    Populate from an experiment's `configuration` + `hypothesis` blobs.
    """

    experiment_id: int
    baseline_conversion_rate: float
    expected_lift: float                             # relative, e.g. 0.15 = +15%
    traffic_split_control: float                     # 0..1
    traffic_split_variant: float                     # 0..1
    sample_size: int                                 # target *total* users (control+variant)
    guardrail_metric_ids: tuple[str, ...] = ()       # from hypothesis.guardrail_metrics
    guardrail_regression: bool = False               # True → variant regresses (for rollback demo)

    # Traffic knobs
    base_traffic_per_tick: int = 200                 # expected new users total per tick
    baseline_bounce_rate: float = 0.24               # control bounce rate baseline

    # Revenue distribution (LogNormal)
    revenue_lognorm_mu: float = math.log(35.0)       # median ~$35
    revenue_lognorm_sigma: float = 0.6


@dataclass
class TickDelta:
    """New (non-cumulative) counts produced this tick."""

    new_users_control: int = 0
    new_users_variant: int = 0
    new_conversion_control: int = 0
    new_conversion_variant: int = 0
    new_revenue_control: float = 0.0
    new_revenue_variant: float = 0.0
    new_bounce_events_control: int = 0
    new_bounce_events_variant: int = 0
    # Per-guardrail-metric snapshot value for this tick (control + variant averages).
    guardrails: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class TickSnapshot:
    """Cumulative snapshot after applying a delta — matches the Metrics row shape."""

    users_control: int = 0
    users_variant: int = 0
    conversion_control: int = 0
    conversion_variant: int = 0
    revenue_control: float = 0.0
    revenue_variant: float = 0.0
    bounce_events_control: int = 0
    bounce_events_variant: int = 0
    guardrails: dict[str, dict[str, float]] = field(default_factory=dict)

    @classmethod
    def zero(cls) -> "TickSnapshot":
        return cls()

    @classmethod
    def from_row(cls, row) -> "TickSnapshot":
        """Build a snapshot from an ORM `Metrics` row or a dict."""
        def g(k, default=0):
            if row is None:
                return default
            if isinstance(row, dict):
                return row.get(k, default)
            return getattr(row, k, default)

        return cls(
            users_control=int(g("users_control", 0)),
            users_variant=int(g("users_variant", 0)),
            conversion_control=int(g("conversion_control", 0)),
            conversion_variant=int(g("conversion_variant", 0)),
            revenue_control=float(g("revenue_control", 0.0)),
            revenue_variant=float(g("revenue_variant", 0.0)),
            bounce_events_control=int(g("bounce_events_control", 0)),
            bounce_events_variant=int(g("bounce_events_variant", 0)),
            guardrails=g("guardrails", None) or {},
        )


# ---------------------------------------------------------------------------
# Core tick generation
# ---------------------------------------------------------------------------


def _draw_new_users(
    rng: np.random.Generator, base_traffic: int, split_share: float
) -> int:
    """Poisson draw for new users on one arm this tick."""
    lam = max(1.0, base_traffic * split_share)
    return int(rng.poisson(lam=lam))


def _draw_conversions(rng: np.random.Generator, new_users: int, rate: float) -> int:
    if new_users <= 0:
        return 0
    rate = max(0.0, min(1.0, rate))
    return int(rng.binomial(n=new_users, p=rate))


def _draw_revenue(rng: np.random.Generator, n_converters: int, mu: float, sigma: float) -> float:
    if n_converters <= 0:
        return 0.0
    samples = rng.lognormal(mean=mu, sigma=sigma, size=n_converters)
    return float(np.sum(samples))


def _draw_bounces(rng: np.random.Generator, new_users: int, rate: float) -> int:
    if new_users <= 0:
        return 0
    rate = max(0.0, min(1.0, rate))
    return int(rng.binomial(n=new_users, p=rate))


def _draw_guardrails(
    rng: np.random.Generator,
    metric_ids: tuple[str, ...],
    *,
    regression: bool,
) -> dict[str, dict[str, float]]:
    """Per-tick guardrail metric values for control & variant.

    Each guardrail metric's baseline comes from the catalog. Control values
    fluctuate ±5% around baseline. Variant matches control unless
    `regression=True`, in which case we bias variant to be worse
    (respecting the metric's `direction`).
    """
    out: dict[str, dict[str, float]] = {}
    for metric_id in metric_ids:
        spec = METRICS.get(metric_id)
        if spec is None or MetricRole.GUARDRAIL not in spec.eligible_roles:
            continue

        baseline = spec.baseline
        # ~5% noise
        control_val = float(baseline * (1 + rng.normal(0, 0.02)))
        variant_val = float(baseline * (1 + rng.normal(0, 0.02)))

        if regression:
            # Bias variant to look ~15% worse in the metric's *bad* direction.
            worsen = 0.15
            if spec.direction.value == "higher_is_better":
                variant_val *= (1 - worsen)
            else:
                variant_val *= (1 + worsen)

        # Clamp ratios into [0, 1]
        if spec.kind == MetricKind.RATIO:
            control_val = min(max(control_val, 0.0), 1.0)
            variant_val = min(max(variant_val, 0.0), 1.0)
        else:
            control_val = max(control_val, 0.0)
            variant_val = max(variant_val, 0.0)

        out[metric_id] = {"control": control_val, "variant": variant_val}
    return out


def next_tick(
    previous: TickSnapshot | None,
    inputs: SimulatorInputs,
    tick_index: int,
) -> TickDelta:
    """Generate one tick's worth of new data (deltas, not cumulative).

    Deterministic given (`inputs.experiment_id`, `tick_index`).
    """
    rng = seeded_rng(inputs.experiment_id, tick_index)

    new_users_c = _draw_new_users(rng, inputs.base_traffic_per_tick, inputs.traffic_split_control)
    new_users_v = _draw_new_users(rng, inputs.base_traffic_per_tick, inputs.traffic_split_variant)

    # Conversion rates per arm.
    rate_c = inputs.baseline_conversion_rate
    rate_v = inputs.baseline_conversion_rate * (1 + inputs.expected_lift)
    if inputs.guardrail_regression:
        # If we're forcing a rollback demo, variant still may or may not
        # lift on the primary — but usually we still want variant primary to
        # be ahead so the rule engine has to weigh the guardrail hit.
        pass

    conv_c = _draw_conversions(rng, new_users_c, rate_c)
    conv_v = _draw_conversions(rng, new_users_v, rate_v)

    rev_c = _draw_revenue(rng, conv_c, inputs.revenue_lognorm_mu, inputs.revenue_lognorm_sigma)
    rev_v = _draw_revenue(rng, conv_v, inputs.revenue_lognorm_mu, inputs.revenue_lognorm_sigma)

    bounces_c = _draw_bounces(rng, new_users_c, inputs.baseline_bounce_rate)
    variant_bounce_rate = inputs.baseline_bounce_rate
    if inputs.guardrail_regression:
        variant_bounce_rate = min(1.0, inputs.baseline_bounce_rate * 1.4)
    bounces_v = _draw_bounces(rng, new_users_v, variant_bounce_rate)

    guardrails = _draw_guardrails(
        rng,
        inputs.guardrail_metric_ids,
        regression=inputs.guardrail_regression,
    )

    return TickDelta(
        new_users_control=new_users_c,
        new_users_variant=new_users_v,
        new_conversion_control=conv_c,
        new_conversion_variant=conv_v,
        new_revenue_control=rev_c,
        new_revenue_variant=rev_v,
        new_bounce_events_control=bounces_c,
        new_bounce_events_variant=bounces_v,
        guardrails=guardrails,
    )


def apply_delta(previous: TickSnapshot | None, delta: TickDelta) -> TickSnapshot:
    """Apply a tick delta to a previous snapshot, returning the new cumulative."""
    prev = previous or TickSnapshot.zero()
    return TickSnapshot(
        users_control=prev.users_control + delta.new_users_control,
        users_variant=prev.users_variant + delta.new_users_variant,
        conversion_control=prev.conversion_control + delta.new_conversion_control,
        conversion_variant=prev.conversion_variant + delta.new_conversion_variant,
        revenue_control=prev.revenue_control + delta.new_revenue_control,
        revenue_variant=prev.revenue_variant + delta.new_revenue_variant,
        bounce_events_control=prev.bounce_events_control + delta.new_bounce_events_control,
        bounce_events_variant=prev.bounce_events_variant + delta.new_bounce_events_variant,
        # Guardrails are point-in-time metrics: latest tick's values win.
        guardrails=delta.guardrails or prev.guardrails,
    )


# ---------------------------------------------------------------------------
# Convenience: build SimulatorInputs from an experiment dict
# ---------------------------------------------------------------------------


def inputs_from_experiment(experiment_id: int, hypothesis: dict, configuration: dict) -> SimulatorInputs:
    """Extract the fields the simulator needs from an experiment's JSON blobs."""
    split = configuration.get("traffic_split") or {}
    guardrails = tuple(hypothesis.get("guardrail_metrics") or ())
    return SimulatorInputs(
        experiment_id=experiment_id,
        baseline_conversion_rate=float(
            configuration.get("baseline_conversion_rate", 0.041)
        ),
        expected_lift=float(configuration.get("expected_lift", 0.15)),
        traffic_split_control=float(split.get("control", 0.5)),
        traffic_split_variant=float(split.get("variant", 0.5)),
        sample_size=int(configuration.get("sample_size", 10_000)),
        guardrail_metric_ids=guardrails,
        guardrail_regression=bool(configuration.get("guardrail_regression", False)),
    )