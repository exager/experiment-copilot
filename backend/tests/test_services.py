"""Tests for the services layer.

Uses an in-memory SQLite DB via `configure_database`. The scheduler is
stubbed with an in-memory fake so we don't need a background thread for
these tests — the `simulation_service.start` call still exercises the
lifecycle transition and job registration API.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import sessionmaker

from app.catalog import ExperimentStatus, Feature
from app.database import Base, configure_database
from app.models.metrics import Metrics
from app.models.report import Report
from app.schemas.context import ProductContextCreate
from app.schemas.metrics import StatisticsOut
from app.services import (
    context_service,
    experiment_service,
    metrics_service,
    recommendation_service,
    report_service,
    simulation_service,
    statistics_service,
    validation_service,
)
from app.utils.errors import ConflictError, NotFoundError


# ---------------------------------------------------------------------------
# In-memory DB fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def session_factory():
    engine = configure_database("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    yield Session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(session_factory):
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Fake scheduler used by simulation_service tests
# ---------------------------------------------------------------------------


class FakeScheduler:
    def __init__(self) -> None:
        self.registered: set[int] = set()

    def register(self, experiment_id: int, interval_seconds: int | None = None) -> str:
        self.registered.add(experiment_id)
        return f"fake:{experiment_id}"

    def deregister(self, experiment_id: int) -> None:
        self.registered.discard(experiment_id)

    def is_registered(self, experiment_id: int) -> bool:
        return experiment_id in self.registered

    def start(self) -> None:  # noqa: D401 - fake
        pass

    def shutdown(self, wait: bool = False) -> None:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_hypothesis() -> dict:
    return {
        "experiment_name": "Simplified Checkout",
        "hypothesis": "Reducing checkout friction increases conversion.",
        "primary_metric": "checkout_conversion",
        "secondary_metrics": ["revenue_per_user"],
        "guardrail_metrics": ["bounce_rate", "cart_abandonment_rate"],
    }


def _valid_configuration() -> dict:
    return {
        "feature_flag": "checkout_v2",
        "audience": "returning_android_users",
        "traffic_split": {"control": 0.5, "variant": 0.5},
        "duration_days": 14,
        "sample_size": 4000,
        "confidence_level": 0.95,
        "baseline_conversion_rate": 0.041,
        "expected_lift": 0.20,
    }


def _seed_context(session) -> int:
    ctx = context_service.create(
        session,
        ProductContextCreate(
            business_goal="Increase checkout conversion",
            website="https://demo-store.com",
            current_flow="Home → Product → Cart → Checkout → Payment",
            feature=Feature.CHECKOUT,
            pain_point="Users abandon payment step",
        ),
    )
    return ctx.id


def _seed_draft(session) -> int:
    ctx_id = _seed_context(session)
    exp = experiment_service.create_draft(
        session,
        context_id=ctx_id,
        hypothesis=_valid_hypothesis(),
        configuration=_valid_configuration(),
    )
    return exp.id


# ---------------------------------------------------------------------------
# context_service
# ---------------------------------------------------------------------------


class TestContextService:
    def test_create_persists_and_returns(self, session):
        ctx = context_service.create(
            session,
            ProductContextCreate(
                business_goal="Increase checkout conversion",
                feature=Feature.CHECKOUT,
            ),
        )
        assert ctx.id is not None
        assert ctx.business_goal == "Increase checkout conversion"
        assert ctx.feature == "checkout"

    def test_get_missing_raises(self, session):
        with pytest.raises(NotFoundError):
            context_service.get(session, 9999)


# ---------------------------------------------------------------------------
# experiment_service — lifecycle transitions
# ---------------------------------------------------------------------------


class TestExperimentServiceLifecycle:
    def test_create_draft(self, session):
        exp_id = _seed_draft(session)
        exp = experiment_service.get(session, exp_id)
        assert exp.status == ExperimentStatus.DRAFT
        assert exp.hypothesis["primary_metric"] == "checkout_conversion"

    def test_mark_validated_from_draft(self, session):
        exp_id = _seed_draft(session)
        exp = experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        assert exp.status == ExperimentStatus.VALIDATED
        assert exp.validation == {"decision": "approve"}

    def test_launch_requires_validated(self, session):
        exp_id = _seed_draft(session)
        with pytest.raises(ConflictError):
            experiment_service.launch(session, exp_id)

    def test_launch_after_validate(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        exp = experiment_service.launch(session, exp_id)
        assert exp.status == ExperimentStatus.RUNNING
        assert exp.started_at is not None

    def test_launch_is_idempotent(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        first = experiment_service.launch(session, exp_id).started_at
        second = experiment_service.launch(session, exp_id).started_at
        assert first == second

    def test_update_configuration_invalidates_prior_validation(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        exp = experiment_service.update_configuration(
            session, exp_id, {**_valid_configuration(), "sample_size": 8000}
        )
        assert exp.status == ExperimentStatus.DRAFT
        assert exp.validation is None
        assert exp.configuration["sample_size"] == 8000

    def test_mark_completed_and_stopped(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)
        experiment_service.mark_completed(session, exp_id)
        assert experiment_service.get(session, exp_id).status == ExperimentStatus.COMPLETED

    def test_mark_stopped(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)
        experiment_service.mark_stopped(session, exp_id)
        assert experiment_service.get(session, exp_id).status == ExperimentStatus.STOPPED


# ---------------------------------------------------------------------------
# validation_service — end-to-end rule evaluation
# ---------------------------------------------------------------------------


class TestValidationService:
    def test_happy_path_approves_and_persists(self, session):
        exp_id = _seed_draft(session)
        result = validation_service.validate(session, exp_id)
        assert result.decision == "approve"
        exp = experiment_service.get(session, exp_id)
        assert exp.status == ExperimentStatus.VALIDATED
        assert exp.validation is not None
        assert exp.validation["decision"] == "approve"

    def test_bad_draft_rejects(self, session):
        ctx_id = _seed_context(session)
        bad_config = _valid_configuration()
        bad_config["traffic_split"] = {"control": 0.7, "variant": 0.4}   # sum != 1
        bad_config["audience"] = None
        bad_hypothesis = _valid_hypothesis()
        bad_hypothesis["primary_metric"] = None
        exp = experiment_service.create_draft(
            session,
            context_id=ctx_id,
            hypothesis=bad_hypothesis,
            configuration=bad_config,
        )
        result = validation_service.validate(session, exp.id)
        assert result.decision == "reject"
        # Some specific rule ids should show up in rejected.
        rejected_ids = {r.rule_id for r in result.rules_rejected}
        assert "traffic_split_sums_to_one" in rejected_ids
        assert "audience_specified" in rejected_ids
        assert "primary_metric_defined" in rejected_ids


# ---------------------------------------------------------------------------
# simulation_service (uses FakeScheduler)
# ---------------------------------------------------------------------------


class TestSimulationService:
    def test_start_launches_and_registers(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        fake = FakeScheduler()
        simulation_service.start(session, exp_id, scheduler=fake)
        assert experiment_service.get(session, exp_id).status == ExperimentStatus.RUNNING
        assert fake.is_registered(exp_id)

    def test_stop_transitions_and_deregisters(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        fake = FakeScheduler()
        simulation_service.start(session, exp_id, scheduler=fake)
        simulation_service.stop(session, exp_id, scheduler=fake)
        assert experiment_service.get(session, exp_id).status == ExperimentStatus.STOPPED
        assert not fake.is_registered(exp_id)

    def test_resume_if_running_only_registers_when_running(self, session):
        exp_id = _seed_draft(session)
        fake = FakeScheduler()
        # Status is DRAFT — should be a no-op.
        simulation_service.resume_if_running(session, exp_id, scheduler=fake)
        assert not fake.is_registered(exp_id)

        # Move to RUNNING and try again.
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)
        simulation_service.resume_if_running(session, exp_id, scheduler=fake)
        assert fake.is_registered(exp_id)


# ---------------------------------------------------------------------------
# metrics_service + statistics_service + recommendation_service — integration
# ---------------------------------------------------------------------------


class TestMetricsStatisticsRecommendation:
    def test_variant_winning_snapshot_and_scale_recommendation(self, session):
        # Seed an experiment and a fake winning-variant metrics row directly.
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)

        row = Metrics(
            experiment_id=exp_id,
            users_control=12_000,
            users_variant=12_000,
            conversion_control=492,   # 4.10%
            conversion_variant=564,   # 4.70%
            revenue_control=5000.0,
            revenue_variant=6200.0,
        )
        session.add(row)
        session.commit()

        # metrics_service
        latest = metrics_service.latest(session, exp_id)
        assert latest is not None
        assert metrics_service.count(session, exp_id) == 1

        # statistics_service
        stats = statistics_service.snapshot(session, exp_id)
        assert isinstance(stats, StatisticsOut)
        assert stats.winner == "variant"
        assert stats.is_significant is True
        assert (stats.conversion_lift or 0.0) > 0.10

        # recommendation_service
        rec = recommendation_service.recommend(
            stats, guardrail_regressed=False, sample_ratio=0.5
        )
        assert rec.recommendation == "scale"
        assert rec.rationale != ""

    def test_snapshot_returns_inconclusive_with_no_metrics(self, session):
        exp_id = _seed_draft(session)
        stats = statistics_service.snapshot(session, exp_id)
        assert stats.winner == "inconclusive"
        assert stats.is_significant is False

    def test_rollback_when_guardrail_regresses(self, session):
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)
        # Seed a variant-winning row.
        session.add(
            Metrics(
                experiment_id=exp_id,
                users_control=12_000,
                users_variant=12_000,
                conversion_control=492,
                conversion_variant=564,
            )
        )
        session.commit()
        stats = statistics_service.snapshot(session, exp_id)
        rec = recommendation_service.recommend(
            stats, guardrail_regressed=True, sample_ratio=0.5
        )
        assert rec.recommendation == "rollback"


# ---------------------------------------------------------------------------
# report_service
# ---------------------------------------------------------------------------


class TestReportService:
    def _run_experiment(self, session) -> int:
        exp_id = _seed_draft(session)
        experiment_service.mark_validated(session, exp_id, {"decision": "approve"})
        experiment_service.launch(session, exp_id)
        return exp_id

    def test_persist_creates_report_and_completes_experiment(self, session):
        exp_id = self._run_experiment(session)
        report = report_service.persist(
            session,
            experiment_id=exp_id,
            summary="Variant B improved checkout by 14%.",
            recommendation="scale",
            business_impact="+8% projected monthly revenue",
            next_steps=["Roll out to 100%", "Monitor bounce rate for 2 weeks"],
        )
        assert report.id is not None
        assert report.recommendation == "scale"
        assert report.next_steps == [
            "Roll out to 100%",
            "Monitor bounce rate for 2 weeks",
        ]

        exp = experiment_service.get(session, exp_id)
        assert exp.status == ExperimentStatus.COMPLETED
        assert exp.completed_at is not None

    def test_persist_overwrites_existing_report(self, session):
        exp_id = self._run_experiment(session)
        report_service.persist(
            session,
            experiment_id=exp_id,
            summary="v1",
            recommendation="continue",
        )
        r2 = report_service.persist(
            session,
            experiment_id=exp_id,
            summary="v2",
            recommendation="scale",
        )
        assert r2.summary == "v2"
        assert r2.recommendation == "scale"
        # Still exactly one report row.
        assert session.query(Report).filter(Report.experiment_id == exp_id).count() == 1

    def test_cannot_report_on_draft(self, session):
        exp_id = _seed_draft(session)
        with pytest.raises(ConflictError):
            report_service.persist(
                session,
                experiment_id=exp_id,
                summary="oops",
                recommendation="scale",
            )

    def test_get_missing_raises(self, session):
        exp_id = self._run_experiment(session)
        with pytest.raises(NotFoundError):
            report_service.get(session, exp_id)