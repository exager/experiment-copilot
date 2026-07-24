"""Simulation scheduler.

Wraps `APScheduler.BackgroundScheduler` to run the synthetic metrics
generator every N seconds for every experiment whose status is `RUNNING`.

For each tick the scheduler:
    1. Opens a fresh DB session.
    2. Loads the experiment (bail if status != RUNNING).
    3. Loads the latest Metrics row.
    4. Generates the next tick delta + applies it to a cumulative snapshot.
    5. Computes derived statistics via the statistics engine.
    6. Runs the recommendation rule engine.
    7. INSERTs a new Metrics row.
    8. If the sample size is reached, marks the experiment COMPLETED and
       deregisters the job.

The scheduler is a thin standalone service — it does NOT know about
LangGraph or any agent code. Wiring into `main.py`'s lifespan hook and
into the API `POST /experiment/start` route happens in Phase D/F.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.catalog.status import ExperimentStatus
from app.config import get_settings
from app.database.session import SessionLocal
from app.logging_config import get_logger
from app.models.experiment import Experiment
from app.models.metrics import Metrics
from app.rules import load_recommendation_engine
from app.simulation.generator import (
    SimulatorInputs,
    TickSnapshot,
    apply_delta,
    inputs_from_experiment,
    next_tick,
)
from app.statistics import compute_statistics

logger = get_logger(__name__)

SessionFactory = Callable[[], Session]


# ---------------------------------------------------------------------------
# Guardrail regression detection
# ---------------------------------------------------------------------------


def _guardrail_regressed(guardrails: dict[str, dict[str, float]] | None) -> bool:
    """Return True if any guardrail is materially worse on variant vs control.

    "Materially worse" == >10% deterioration in the metric's *bad* direction.
    Uses the catalog's `direction` field.
    """
    if not guardrails:
        return False

    from app.catalog import METRICS, Direction

    threshold = 0.10  # 10% relative
    for metric_id, values in guardrails.items():
        spec = METRICS.get(metric_id)
        if spec is None:
            continue
        control = float(values.get("control", 0.0))
        variant = float(values.get("variant", 0.0))
        if control <= 0:
            continue
        rel_change = (variant - control) / control
        if spec.direction == Direction.LOWER_IS_BETTER and rel_change > threshold:
            return True
        if spec.direction == Direction.HIGHER_IS_BETTER and rel_change < -threshold:
            return True
    return False


# ---------------------------------------------------------------------------
# One tick — the core job body
# ---------------------------------------------------------------------------


def run_one_tick(
    session_factory: SessionFactory,
    experiment_id: int,
    on_complete: Callable[[int], None] | None = None,
) -> None:
    """Execute exactly one simulation tick for an experiment.

    Called by the scheduler on each interval. Also usable directly from
    tests to advance the simulation deterministically.
    """
    session = session_factory()
    try:
        exp = session.get(Experiment, experiment_id)
        if exp is None:
            logger.warning("Simulation tick skipped: experiment %s not found", experiment_id)
            if on_complete:
                on_complete(experiment_id)
            return
        if exp.status != ExperimentStatus.RUNNING:
            logger.info(
                "Simulation tick skipped: experiment %s is %s (not running)",
                experiment_id,
                exp.status,
            )
            if on_complete:
                on_complete(experiment_id)
            return

        # Latest metrics row for this experiment.
        latest: Metrics | None = (
            session.query(Metrics)
            .filter(Metrics.experiment_id == experiment_id)
            .order_by(Metrics.timestamp.desc())
            .first()
        )

        previous_snapshot = TickSnapshot.from_row(latest) if latest else TickSnapshot.zero()

        # How many ticks have we already produced? Used as the RNG seed offset.
        tick_index = (
            session.query(Metrics.id)
            .filter(Metrics.experiment_id == experiment_id)
            .count()
        )

        inputs: SimulatorInputs = inputs_from_experiment(
            experiment_id,
            hypothesis=exp.hypothesis or {},
            configuration=exp.configuration or {},
        )

        # Draw the tick and compute cumulative snapshot.
        delta = next_tick(previous_snapshot, inputs, tick_index)
        snapshot = apply_delta(previous_snapshot, delta)

        # Derived statistics.
        stats = compute_statistics(
            users_control=snapshot.users_control,
            users_variant=snapshot.users_variant,
            conversion_control=snapshot.conversion_control,
            conversion_variant=snapshot.conversion_variant,
        )

        # Recommendation via the rule engine.
        rule_ctx = {
            "statistics": {
                "winner": stats.winner,
                "confidence": stats.confidence or 0.0,
                "conversion_lift": stats.conversion_lift or 0.0,
            },
            "guardrail": {"regression": _guardrail_regressed(snapshot.guardrails)},
            "progress": {
                "sample_ratio": min(
                    1.0,
                    (snapshot.users_control + snapshot.users_variant)
                    / max(1, inputs.sample_size),
                )
            },
        }
        rec_result = load_recommendation_engine().evaluate(rule_ctx)
        rec_reason = (
            rec_result.rules_matched[0].message
            if rec_result.rules_matched
            else rec_result.explanation
        )

        row = Metrics(
            experiment_id=experiment_id,
            users_control=snapshot.users_control,
            users_variant=snapshot.users_variant,
            conversion_control=snapshot.conversion_control,
            conversion_variant=snapshot.conversion_variant,
            revenue_control=snapshot.revenue_control,
            revenue_variant=snapshot.revenue_variant,
            bounce_events_control=snapshot.bounce_events_control,
            bounce_events_variant=snapshot.bounce_events_variant,
            guardrails=snapshot.guardrails or None,
            confidence=stats.confidence,
            p_value=stats.p_value,
            conversion_lift=stats.conversion_lift,
            z_score=stats.z_score,
            winner=stats.winner,
            recommendation=rec_result.decision,
            recommendation_reason=rec_reason,
        )
        session.add(row)

        # Stop condition: sample size reached (or exceeded).
        total_users = snapshot.users_control + snapshot.users_variant
        completed = total_users >= inputs.sample_size
        if completed:
            exp.status = ExperimentStatus.COMPLETED
            exp.completed_at = datetime.now(tz=timezone.utc)
            logger.info(
                "Experiment %s reached sample size (%d/%d) — marking COMPLETED",
                experiment_id,
                total_users,
                inputs.sample_size,
            )

        session.commit()

        if completed and on_complete is not None:
            on_complete(experiment_id)
    except Exception:
        session.rollback()
        logger.exception("Simulation tick failed for experiment %s", experiment_id)
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Scheduler wrapper
# ---------------------------------------------------------------------------


class SimulationScheduler:
    """Thread-safe wrapper around APScheduler for experiment simulations."""

    def __init__(self, session_factory: SessionFactory | None = None) -> None:
        self._session_factory: SessionFactory = session_factory or SessionLocal
        self._scheduler = BackgroundScheduler(daemon=True)
        self._lock = threading.Lock()
        self._started = False

    def start(self) -> None:
        """Start the background scheduler. Idempotent."""
        with self._lock:
            if self._started:
                return
            self._scheduler.start()
            self._started = True
            logger.info("SimulationScheduler started")

    def shutdown(self, wait: bool = False) -> None:
        """Stop the scheduler. Idempotent."""
        with self._lock:
            if not self._started:
                return
            self._scheduler.shutdown(wait=wait)
            self._started = False
            logger.info("SimulationScheduler shut down")

    def register(self, experiment_id: int, interval_seconds: int | None = None) -> str:
        """Register a per-tick job for `experiment_id`.

        Returns the APScheduler job id.
        """
        if not self._started:
            self.start()

        interval = interval_seconds or get_settings().simulation_interval_seconds
        job_id = self._job_id(experiment_id)

        # Idempotent: replace any existing job for this experiment.
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

        self._scheduler.add_job(
            func=run_one_tick,
            trigger=IntervalTrigger(seconds=interval),
            args=[self._session_factory, experiment_id, self.deregister],
            id=job_id,
            replace_existing=True,
            max_instances=1,   # never allow overlapping ticks for one experiment
            coalesce=True,     # collapse missed ticks
            next_run_time=datetime.now(tz=timezone.utc),   # first tick immediately
        )
        logger.info(
            "Registered simulation job for experiment %s (every %ds)",
            experiment_id,
            interval,
        )
        return job_id

    def deregister(self, experiment_id: int) -> None:
        """Remove the tick job for an experiment (e.g., after completion)."""
        job_id = self._job_id(experiment_id)
        try:
            self._scheduler.remove_job(job_id)
            logger.info("Deregistered simulation job for experiment %s", experiment_id)
        except Exception:
            logger.debug("No simulation job to deregister for experiment %s", experiment_id)

    def is_registered(self, experiment_id: int) -> bool:
        return self._scheduler.get_job(self._job_id(experiment_id)) is not None

    @staticmethod
    def _job_id(experiment_id: int) -> str:
        return f"sim:experiment:{experiment_id}"


# Process-wide singleton (created lazily so tests can inject their own).
_default_scheduler: SimulationScheduler | None = None


def get_scheduler() -> SimulationScheduler:
    """Return the process-wide SimulationScheduler singleton."""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = SimulationScheduler()
    return _default_scheduler