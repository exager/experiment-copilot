"""End-to-end HTTP tests for the API layer.

Uses a `TestClient` bound to `app.main.app`, with:
- In-memory SQLite DB via `configure_database`.
- A `FakeScheduler` injected in place of `get_scheduler`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

import tempfile
from pathlib import Path

from app.catalog.status import ExperimentStatus
from app.database import Base, configure_database, get_db
from app.main import app
from app.models.metrics import Metrics
from app.models.report import Report
from app.simulation import scheduler as scheduler_module


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class FakeScheduler:
    def __init__(self) -> None:
        self.registered: set[int] = set()
        self.started = False

    def start(self) -> None:
        self.started = True

    def shutdown(self, wait: bool = False) -> None:
        self.started = False

    def register(self, experiment_id: int, interval_seconds: int | None = None) -> str:
        self.registered.add(experiment_id)
        return f"fake:{experiment_id}"

    def deregister(self, experiment_id: int) -> None:
        self.registered.discard(experiment_id)

    def is_registered(self, experiment_id: int) -> bool:
        return experiment_id in self.registered


@pytest.fixture
def fake_scheduler(monkeypatch) -> FakeScheduler:
    fake = FakeScheduler()
    monkeypatch.setattr(scheduler_module, "_default_scheduler", fake)
    monkeypatch.setattr(scheduler_module, "get_scheduler", lambda: fake)
    return fake


@pytest.fixture
def client(fake_scheduler, tmp_path):
    # A per-test SQLite file so all connections in the pool see the same tables.
    # `:memory:` doesn't work across connections; a temp file does.
    db_path = tmp_path / "test.db"
    engine = configure_database(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------


def _valid_context_payload() -> dict:
    return {
        "business_goal": "Increase checkout conversion by 10%",
        "website": "https://demo-store.com",
        "current_flow": "Home → Product → Cart → Checkout → Payment",
        "feature": "checkout",
        "pain_point": "Users abandon the payment page after entering address.",
    }


def _valid_hypothesis_payload() -> dict:
    return {
        "experiment_name": "Simplified Checkout Payment",
        "hypothesis": "Reducing checkout friction increases conversion.",
        "primary_metric": "checkout_conversion",
        "secondary_metrics": ["revenue_per_user"],
        "guardrail_metrics": ["bounce_rate", "cart_abandonment_rate"],
    }


def _valid_configuration_payload() -> dict:
    return {
        "feature_flag": "checkout_v2",
        "audience": "returning_android_users",
        "traffic_split_option": "50_50",
        "duration_days": 14,
        "sample_size": 10_000,
        "confidence_level": 0.95,
        "baseline_conversion_rate": 0.041,
        "expected_lift": 0.20,
    }


def _create_context(client: TestClient) -> int:
    r = client.post("/context", json=_valid_context_payload())
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_experiment(client: TestClient, context_id: int) -> int:
    r = client.post(
        "/experiments",
        json={
            "context_id": context_id,
            "hypothesis": _valid_hypothesis_payload(),
            "configuration": _valid_configuration_payload(),
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ---------------------------------------------------------------------------
# /health + /catalog
# ---------------------------------------------------------------------------


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_catalog(client):
    r = client.get("/catalog")
    assert r.status_code == 200
    payload = r.json()
    assert "features" in payload
    assert "audiences" in payload
    assert "metrics" in payload
    assert "traffic_splits" in payload
    assert len(payload["metrics"]) > 0


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------


def test_cors_preflight(client):
    """OPTIONS preflight must return `access-control-allow-origin: *`."""
    r = client.options(
        "/context",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "*"
    # Wildcard origins require credentials to be disabled.
    assert r.headers.get("access-control-allow-credentials") != "true"


def test_cors_simple_request_includes_origin(client):
    r = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "*"


# ---------------------------------------------------------------------------
# /context
# ---------------------------------------------------------------------------


class TestPostContext:
    def test_happy_path(self, client):
        r = client.post("/context", json=_valid_context_payload())
        assert r.status_code == 201
        body = r.json()
        assert body["id"] > 0
        assert body["business_goal"] == "Increase checkout conversion by 10%"
        assert body["feature"] == "checkout"

    def test_rejects_unknown_feature(self, client):
        payload = _valid_context_payload()
        payload["feature"] = "mars_landing"
        r = client.post("/context", json=payload)
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# /context/{id}/hypothesis  (run agents -> pause -> review)
# ---------------------------------------------------------------------------


class TestGenerateHypothesis:
    def _selected(self, options: list[dict]) -> set[str]:
        return {opt["id"] for opt in options if opt["selected"]}

    def test_happy_path(self, client, fake_llm):
        ctx_id = _create_context(client)
        r = client.post(f"/context/{ctx_id}/hypothesis")
        assert r.status_code == 200, r.text
        body = r.json()

        assert body["experiment_id"] > 0
        assert body["thread_id"] == str(body["experiment_id"])
        assert body["experiment_name"]
        assert body["hypothesis"]
        # problem_statement comes from the context understanding card.
        assert body["problem_statement"] == "Users abandon checkout during payment"

        # Each role returns the full catalog list with the AI's picks selected.
        assert self._selected(body["primary_metric"]) == {"checkout_conversion"}
        assert all(
            opt["id"] != "checkout_conversion" or opt["selected"]
            for opt in body["primary_metric"]
        )
        assert self._selected(body["secondary_metrics"]) == {"average_order_value"}
        assert self._selected(body["guardrail_metrics"]) == {"bounce_rate"}

        # Options carry labels and cover more than just the selected metric.
        assert all(opt["label"] for opt in body["primary_metric"])
        assert len(body["primary_metric"]) > 1

    def test_missing_context_returns_404(self, client, fake_llm):
        r = client.post("/context/9999/hypothesis")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Full graph-driven flow: /context/{id}/hypothesis -> /validate (metric
# update, resumes the same graph thread) -> /launch (resumes to completion)
# ---------------------------------------------------------------------------


class TestGraphDrivenFlow:
    def test_full_flow_reaches_completed_report(self, client, fake_llm):
        ctx_id = _create_context(client)

        # Generate hypothesis: pauses right after hypothesis_agent.
        r = client.post(f"/context/{ctx_id}/hypothesis")
        assert r.status_code == 200, r.text
        review = r.json()
        exp_id = review["experiment_id"]

        # Newly-created experiment already carries the AI hypothesis, in DRAFT.
        exp = client.get(f"/experiments/{exp_id}").json()
        assert exp["status"] == "draft"
        assert exp["hypothesis"]["primary_metric"] == "checkout_conversion"

        # PM edits secondary metrics: drop average_order_value, add revenue_per_user.
        primary_toggles = [
            {"id": opt["id"], "selected": opt["id"] == "checkout_conversion"}
            for opt in review["primary_metric"]
        ]
        secondary_toggles = [
            {"id": opt["id"], "selected": opt["id"] == "revenue_per_user"}
            for opt in review["secondary_metrics"]
        ]

        r = client.post(
            f"/experiments/{exp_id}/validate",
            json={"primary_metric": primary_toggles, "secondary_metrics": secondary_toggles},
        )
        assert r.status_code == 200, r.text
        assert r.json()["decision"] == "approve"

        # experiment_design_agent + validation_agent ran and persisted.
        exp = client.get(f"/experiments/{exp_id}").json()
        assert exp["status"] == "validated"
        assert exp["configuration"]["feature_flag"] == "checkout_v2"
        assert exp["hypothesis"]["secondary_metrics"] == ["revenue_per_user"]

        # Launch resumes simulation -> statistics -> explanation -> report -> END.
        r = client.post(f"/experiments/{exp_id}/launch")
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed"

        # A real, persisted simulation series exists (not the empty stub).
        r = client.get(f"/experiments/{exp_id}/metrics")
        assert r.status_code == 200
        metrics_body = r.json()
        assert metrics_body["latest"] is not None
        assert len(metrics_body["series"]) > 0

        # report_agent persisted a real Report row via report_service.
        override = app.dependency_overrides[get_db]
        gen = override()
        session = next(gen)
        try:
            report = session.query(Report).filter(Report.experiment_id == exp_id).one()
        finally:
            gen.close()
        assert report.summary == "Checkout simplification improved conversion significantly."
        assert report.next_steps == ["Roll out to 100%"]


# ---------------------------------------------------------------------------
# /experiments  (create + get + launch + stop)
# ---------------------------------------------------------------------------


class TestExperimentRoutes:
    def test_create_and_get(self, client):
        ctx_id = _create_context(client)
        exp_id = _create_experiment(client, ctx_id)

        r = client.get(f"/experiments/{exp_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == exp_id
        assert body["status"] == "draft"
        assert body["hypothesis"]["primary_metric"] == "checkout_conversion"

    def test_get_missing_returns_404(self, client):
        r = client.get("/experiments/9999")
        assert r.status_code == 404

    def test_create_rejects_bad_metric(self, client):
        ctx_id = _create_context(client)
        bad_hypothesis = _valid_hypothesis_payload()
        bad_hypothesis["primary_metric"] = "bounce_rate"   # guardrail-only, not primary
        r = client.post(
            "/experiments",
            json={
                "context_id": ctx_id,
                "hypothesis": bad_hypothesis,
                "configuration": _valid_configuration_payload(),
            },
        )
        assert r.status_code == 422

    def test_launch_requires_validation(self, client):
        ctx_id = _create_context(client)
        exp_id = _create_experiment(client, ctx_id)
        r = client.post(f"/experiments/{exp_id}/launch")
        # Draft can't launch — conflict.
        assert r.status_code == 409

    def test_full_launch_flow(self, client, fake_scheduler):
        ctx_id = _create_context(client)
        exp_id = _create_experiment(client, ctx_id)

        # Validate first.
        r = client.post(f"/experiments/{exp_id}/validate")
        assert r.status_code == 200
        assert r.json()["decision"] == "approve"

        # Launch.
        r = client.post(f"/experiments/{exp_id}/launch")
        assert r.status_code == 200
        assert r.json()["status"] == "running"
        assert exp_id in fake_scheduler.registered

        # Stop.
        r = client.post(f"/experiments/{exp_id}/stop")
        assert r.status_code == 200
        assert r.json()["status"] == "stopped"
        assert exp_id not in fake_scheduler.registered


# ---------------------------------------------------------------------------
# /experiments/{id}/validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_happy_path_approves(self, client):
        ctx_id = _create_context(client)
        exp_id = _create_experiment(client, ctx_id)
        r = client.post(f"/experiments/{exp_id}/validate")
        assert r.status_code == 200
        result = r.json()
        assert result["decision"] == "approve"
        # Deterministic score is filled even without LLM enrichment.
        assert result["validation_score"] is not None
        assert result["validation_score"] >= 0.85
        # Experiment moved to VALIDATED.
        r2 = client.get(f"/experiments/{exp_id}")
        assert r2.json()["status"] == "validated"

    def test_graph_validate_survives_llm_failure(self, client, fake_llm, monkeypatch):
        """A resumed graph validate must not 500 and must fill a non-null score
        even if the LLM quota is exhausted mid-flow."""
        from app.catalog import PRIMARY_METRICS, SECONDARY_METRICS

        ctx_id = _create_context(client)
        rev = client.post(f"/context/{ctx_id}/hypothesis")
        assert rev.status_code == 200
        exp_id = rev.json()["experiment_id"]

        class _RaisingStructured:
            def invoke(self, prompt):
                raise RuntimeError("simulated quota exhausted")

        class _RaisingLLM:
            def with_structured_output(self, schema):
                return _RaisingStructured()

        monkeypatch.setattr("app.agents.llm.get_llm", lambda *a, **k: _RaisingLLM())

        body = {
            "primary_metric": [
                {"id": m, "selected": m == "checkout_conversion"} for m in PRIMARY_METRICS
            ],
            "secondary_metrics": [
                {"id": m, "selected": m == "revenue_per_user"} for m in SECONDARY_METRICS
            ],
        }
        r = client.post(f"/experiments/{exp_id}/validate", json=body)
        assert r.status_code == 200  # graceful degradation, not a 500
        assert r.json()["validation_score"] is not None


# ---------------------------------------------------------------------------
# /experiments/{id}/metrics + /report
# ---------------------------------------------------------------------------


def _seed_winning_metrics_row(session_factory, experiment_id: int) -> None:
    session = session_factory()
    try:
        row = Metrics(
            experiment_id=experiment_id,
            users_control=12_000,
            users_variant=12_000,
            conversion_control=492,
            conversion_variant=564,
            revenue_control=5000.0,
            revenue_variant=6200.0,
        )
        session.add(row)
        session.commit()
    finally:
        session.close()


class TestMetricsAndReport:
    def _launch(self, client) -> int:
        ctx_id = _create_context(client)
        exp_id = _create_experiment(client, ctx_id)
        client.post(f"/experiments/{exp_id}/validate")
        client.post(f"/experiments/{exp_id}/launch")
        return exp_id

    def test_metrics_snapshot_before_ticks(self, client):
        exp_id = self._launch(client)
        r = client.get(f"/experiments/{exp_id}/metrics")
        assert r.status_code == 200
        body = r.json()
        assert body["experiment_id"] == exp_id
        assert body["latest"] is None
        assert body["series"] == []
        assert body["statistics"]["winner"] == "inconclusive"

    def test_metrics_snapshot_variant_winning(self, client):
        # Seed a winning row directly via the overridden session factory.
        exp_id = self._launch(client)

        # The dependency override binds get_db to our test Session.
        # We need to reach into it to insert a row using the same engine.
        # Easiest: run one_tick via the DB session used by the override.
        # Simpler: fetch a fresh session from the same override.
        override = app.dependency_overrides[get_db]
        # override is a generator function — instantiate it and grab the yielded session
        gen = override()
        session = next(gen)
        try:
            session.add(
                Metrics(
                    experiment_id=exp_id,
                    users_control=12_000,
                    users_variant=12_000,
                    conversion_control=492,
                    conversion_variant=564,
                    revenue_control=5000.0,
                    revenue_variant=6200.0,
                )
            )
            session.commit()
        finally:
            gen.close()

        r = client.get(f"/experiments/{exp_id}/metrics")
        assert r.status_code == 200
        body = r.json()
        assert body["latest"] is not None
        assert body["statistics"]["winner"] == "variant"
        assert body["statistics"]["is_significant"] is True
        assert body["recommendation"]["recommendation"] == "scale"

    def test_generate_report(self, client):
        exp_id = self._launch(client)
        # Seed a winning row so the report can pick "scale".
        override = app.dependency_overrides[get_db]
        gen = override()
        session = next(gen)
        try:
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
        finally:
            gen.close()

        r = client.post(f"/experiments/{exp_id}/report")
        assert r.status_code == 200
        body = r.json()
        assert body["experiment_id"] == exp_id
        assert body["recommendation"] == "scale"
        assert body["summary"]
        assert isinstance(body["next_steps"], list) and len(body["next_steps"]) >= 1

        # Report call should have flipped the experiment to COMPLETED.
        r2 = client.get(f"/experiments/{exp_id}")
        assert r2.json()["status"] == "completed"

    def test_report_accepts_overrides(self, client):
        exp_id = self._launch(client)
        r = client.post(
            f"/experiments/{exp_id}/report",
            json={
                "summary": "Custom summary from LLM.",
                "recommendation": "continue",
                "next_steps": ["Extend the experiment by 2 weeks."],
                "business_impact": "Modest projected uplift.",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["summary"] == "Custom summary from LLM."
        assert body["recommendation"] == "continue"
        assert body["next_steps"] == ["Extend the experiment by 2 weeks."]
        assert body["business_impact"] == "Modest projected uplift."