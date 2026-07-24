"""Tests for the simulation engine.

Covers:
- Deterministic RNG seeding (same seed → same output)
- Cumulative monotonicity across many ticks
- End-to-end scheduler-body scenario: after enough ticks the variant wins
  significantly and the recommendation engine returns `scale`
- Guardrail regression path drives `rollback`
- Auto-stop when sample size is reached
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from app.catalog import ExperimentStatus
from app.database import Base, configure_database
from app.models.experiment import Experiment
from app.models.metrics import Metrics
from app.models.product_context import ProductContext
from app.rules import load_recommendation_engine
from app.simulation import (
    SimulatorInputs,
    TickSnapshot,
    apply_delta,
    next_tick,
    run_one_tick,
    seeded_rng,
)


# ---------------------------------------------------------------------------
# In-memory DB fixtures (scoped to this file)
# ---------------------------------------------------------------------------


@pytest.fixture
def session_factory():
    engine = configure_database("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    yield Session
    Base.metadata.drop_all(bind=engine)


def _make_experiment(session_factory, *, guardrail_regression: bool = False) -> int:
    """Seed a product_context + experiment row and return the experiment id."""
    session = session_factory()
    try:
        ctx = ProductContext(business_goal="Increase checkout conversion")
        session.add(ctx)
        session.flush()
        exp = Experiment(
            context_id=ctx.id,
            hypothesis={
                "experiment_name": "Checkout v2",
                "primary_metric": "checkout_conversion",
                "guardrail_metrics": ["bounce_rate"],
            },
            configuration={
                "feature_flag": "checkout_v2",
                "audience": "returning_android_users",
                "traffic_split": {"control": 0.5, "variant": 0.5},
                "duration_days": 14,
                "sample_size": 4000,
                "confidence_level": 0.95,
                "baseline_conversion_rate": 0.041,
                "expected_lift": 0.20,
                "guardrail_regression": guardrail_regression,
            },
            status=ExperimentStatus.RUNNING,
        )
        session.add(exp)
        session.commit()
        return exp.id
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestSeededRng:
    def test_same_seed_same_sequence(self):
        rng1 = seeded_rng(experiment_id=42, tick_index=7)
        rng2 = seeded_rng(experiment_id=42, tick_index=7)
        a = rng1.poisson(lam=50, size=10)
        b = rng2.poisson(lam=50, size=10)
        assert list(a) == list(b)

    def test_different_experiment_different_sequence(self):
        rng1 = seeded_rng(experiment_id=1, tick_index=0)
        rng2 = seeded_rng(experiment_id=2, tick_index=0)
        assert list(rng1.poisson(lam=50, size=5)) != list(rng2.poisson(lam=50, size=5))

    def test_different_tick_different_sequence(self):
        rng1 = seeded_rng(experiment_id=1, tick_index=0)
        rng2 = seeded_rng(experiment_id=1, tick_index=1)
        assert list(rng1.poisson(lam=50, size=5)) != list(rng2.poisson(lam=50, size=5))


class TestNextTickDeterminism:
    def _inputs(self, experiment_id: int = 42):
        return SimulatorInputs(
            experiment_id=experiment_id,
            baseline_conversion_rate=0.041,
            expected_lift=0.15,
            traffic_split_control=0.5,
            traffic_split_variant=0.5,
            sample_size=10_000,
            guardrail_metric_ids=("bounce_rate",),
        )

    def test_same_inputs_same_delta(self):
        inputs = self._inputs()
        d1 = next_tick(TickSnapshot.zero(), inputs, tick_index=0)
        d2 = next_tick(TickSnapshot.zero(), inputs, tick_index=0)
        assert d1 == d2


# ---------------------------------------------------------------------------
# Cumulative behavior
# ---------------------------------------------------------------------------


class TestCumulativeSimulation:
    def test_counts_are_monotonically_non_decreasing(self):
        inputs = SimulatorInputs(
            experiment_id=42,
            baseline_conversion_rate=0.041,
            expected_lift=0.15,
            traffic_split_control=0.5,
            traffic_split_variant=0.5,
            sample_size=100_000,
        )
        snap = TickSnapshot.zero()
        for tick in range(30):
            delta = next_tick(snap, inputs, tick)
            new_snap = apply_delta(snap, delta)
            assert new_snap.users_control >= snap.users_control
            assert new_snap.users_variant >= snap.users_variant
            assert new_snap.conversion_control >= snap.conversion_control
            assert new_snap.conversion_variant >= snap.conversion_variant
            assert new_snap.revenue_control >= snap.revenue_control
            assert new_snap.revenue_variant >= snap.revenue_variant
            snap = new_snap
        # After 30 ticks we should have plenty of users.
        assert snap.users_control > 100
        assert snap.users_variant > 100

    def test_variant_wins_and_rule_engine_returns_scale(self):
        """The core demo guarantee.

        Run ~40 ticks with a +20% expected lift. The variant should be
        winning with high confidence and material lift, and the
        recommendation engine should return `scale`.
        """
        inputs = SimulatorInputs(
            experiment_id=7,
            baseline_conversion_rate=0.041,
            expected_lift=0.20,
            traffic_split_control=0.5,
            traffic_split_variant=0.5,
            sample_size=100_000,
            guardrail_metric_ids=("bounce_rate",),
        )
        snap = TickSnapshot.zero()
        for tick in range(40):
            snap = apply_delta(snap, next_tick(snap, inputs, tick))

        # Compute stats + run recommendation.
        from app.statistics import compute_statistics

        stats = compute_statistics(
            users_control=snap.users_control,
            users_variant=snap.users_variant,
            conversion_control=snap.conversion_control,
            conversion_variant=snap.conversion_variant,
        )
        assert stats.winner == "variant"
        assert stats.is_significant is True
        assert stats.conversion_lift is not None and stats.conversion_lift >= 0.05

        rec = load_recommendation_engine().evaluate(
            {
                "statistics": {
                    "winner": stats.winner,
                    "confidence": stats.confidence or 0.0,
                    "conversion_lift": stats.conversion_lift or 0.0,
                },
                "guardrail": {"regression": False},
                "progress": {"sample_ratio": 0.5},
            }
        )
        assert rec.decision == "scale"


# ---------------------------------------------------------------------------
# End-to-end scheduler body (`run_one_tick`) against an in-memory DB
# ---------------------------------------------------------------------------


class TestRunOneTick:
    def test_single_tick_inserts_metrics_row(self, session_factory):
        exp_id = _make_experiment(session_factory)
        run_one_tick(session_factory, exp_id)

        s = session_factory()
        try:
            rows = s.query(Metrics).filter(Metrics.experiment_id == exp_id).all()
            assert len(rows) == 1
            row = rows[0]
            assert row.users_control > 0
            assert row.users_variant > 0
            assert row.recommendation is not None
            # First tick typically inconclusive but must not crash.
            assert row.winner in ("variant", "control", "inconclusive")
        finally:
            s.close()

    def test_many_ticks_lead_to_scale_recommendation(self, session_factory):
        exp_id = _make_experiment(session_factory)
        # 40 ticks × 200 users/tick ≈ 8000 users — well over sample_size=4000,
        # so we'll actually auto-stop earlier. Loop generously.
        for _ in range(60):
            s = session_factory()
            try:
                exp = s.get(Experiment, exp_id)
                if exp.status != ExperimentStatus.RUNNING:
                    break
            finally:
                s.close()
            run_one_tick(session_factory, exp_id)

        s = session_factory()
        try:
            latest = (
                s.query(Metrics)
                .filter(Metrics.experiment_id == exp_id)
                .order_by(Metrics.timestamp.desc())
                .first()
            )
            assert latest is not None
            assert latest.winner == "variant"
            assert latest.recommendation == "scale"
            # Auto-stop should have fired.
            exp = s.get(Experiment, exp_id)
            assert exp.status == ExperimentStatus.COMPLETED
            assert exp.completed_at is not None
        finally:
            s.close()

    def test_guardrail_regression_drives_rollback(self, session_factory):
        exp_id = _make_experiment(session_factory, guardrail_regression=True)
        for _ in range(50):
            s = session_factory()
            try:
                exp = s.get(Experiment, exp_id)
                if exp.status != ExperimentStatus.RUNNING:
                    break
            finally:
                s.close()
            run_one_tick(session_factory, exp_id)

        s = session_factory()
        try:
            latest = (
                s.query(Metrics)
                .filter(Metrics.experiment_id == exp_id)
                .order_by(Metrics.timestamp.desc())
                .first()
            )
            assert latest is not None
            # Under regression, the rule engine should have flipped to rollback
            # at some tick. Allow either rollback OR the specific case where
            # bounce is still within the noise band (rare).
            assert latest.recommendation in ("rollback", "scale", "continue")
            # We assert at least one row across the run was rollback.
            all_recs = [
                r.recommendation
                for r in s.query(Metrics)
                .filter(Metrics.experiment_id == exp_id)
                .all()
            ]
            assert "rollback" in all_recs, f"expected rollback in {all_recs}"
        finally:
            s.close()

    def test_tick_is_noop_when_experiment_not_running(self, session_factory):
        s = session_factory()
        try:
            ctx = ProductContext(business_goal="test")
            s.add(ctx)
            s.flush()
            exp = Experiment(
                context_id=ctx.id,
                hypothesis={},
                configuration={
                    "traffic_split": {"control": 0.5, "variant": 0.5},
                    "sample_size": 1000,
                    "baseline_conversion_rate": 0.05,
                    "expected_lift": 0.1,
                },
                status=ExperimentStatus.DRAFT,   # not running
            )
            s.add(exp)
            s.commit()
            exp_id = exp.id
        finally:
            s.close()

        run_one_tick(session_factory, exp_id)

        s = session_factory()
        try:
            assert s.query(Metrics).filter(Metrics.experiment_id == exp_id).count() == 0
        finally:
            s.close()