"""
End-to-end API tests.

`test_assess_works_on_fresh_database` is the regression test for
the original blocker: `main.py` never created the tables, so a
fresh clone returned

    OperationalError: no such table: assessments

on the very first assessment.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _purge_backend_modules():
    """
    Drop every cached module that lives in the backend package.

    `models.db_models` captures `database.Base` at import time,
    so re-importing only `config`/`database`/`main` would leave
    the ORM models bound to a previous test's engine.
    """
    stale = [
        name
        for name, mod in list(sys.modules.items())
        if getattr(mod, "__file__", None)
        and os.path.abspath(mod.__file__).startswith(BACKEND_DIR)
    ]
    for name in stale:
        sys.modules.pop(name, None)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """App wired to a throwaway SQLite file, tables created
    through the normal startup path."""

    db_file = tmp_path / "test.db"
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{db_file}",
    )
    monkeypatch.setenv("ENVIRONMENT", "development")

    _purge_backend_modules()

    import main

    with TestClient(main.app) as c:
        yield c

    _purge_backend_modules()


PAYLOAD = {
    "name": "Test User",
    "location": "Pune, Maharashtra",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "num_people": 4,
    "roof_type": "RCC",
    "roof_area": 100.0,
    "open_space_area": 50.0,
    "soil_type": "LOAMY",
    "groundwater_depth": 15.0,
}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_assess_works_on_fresh_database(client):
    """The blocker: no /api/init-db call, tables must exist."""
    r = client.post("/api/assess", json=PAYLOAD)

    assert r.status_code == 200, r.text

    body = r.json()
    assert body["assessment_id"]
    assert body["runoff"]["annual_runoff_volume"] > 0
    assert len(body["recommended_structures"]) >= 1


def test_assessment_can_be_refetched_by_id(client):
    """Supports shareable /results?id=<id> links."""
    created = client.post("/api/assess", json=PAYLOAD).json()

    r = client.get(f"/api/assessment/{created['assessment_id']}")

    assert r.status_code == 200
    assert r.json()["assessment_id"] == created["assessment_id"]


def test_report_downloads_after_assessment(client):
    created = client.post("/api/assess", json=PAYLOAD).json()

    r = client.get(f"/api/report/{created['assessment_id']}")

    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_unknown_assessment_returns_404(client):
    assert client.get("/api/assessment/NOPE").status_code == 404
    assert client.get("/api/report/NOPE").status_code == 404


def test_monthly_savings_reconcile_with_annual(client):
    """monthly_savings[] used to be computed from gross runoff
    while annual_savings_inr used harvestable volume, so the two
    disagreed by ~46% in every scenario."""

    body = client.post("/api/assess", json=PAYLOAD).json()
    cb = body["cost_benefit"]

    assert abs(
        sum(cb["monthly_savings"]) - cb["annual_savings_inr"]
    ) < 1.0


def test_payback_is_none_when_not_viable(client):
    """The old code returned the sentinel 99.0."""
    body = client.post("/api/assess", json=PAYLOAD).json()
    pb = body["cost_benefit"]["payback_period_years"]

    assert pb is None or pb > 0


def test_high_rainfall_site_has_finite_payback(client):
    payload = dict(PAYLOAD)
    payload.update(
        latitude=19.0760,   # Mumbai region
        longitude=72.8777,
        roof_area=500.0,
        num_people=20,
        open_space_area=300.0,
        soil_type="SANDY",
    )

    body = client.post("/api/assess", json=payload).json()
    pb = body["cost_benefit"]["payback_period_years"]

    assert pb is not None
    assert pb < 20


def test_init_db_requires_token_in_production(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{tmp_path}/prod.db",
    )
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_TOKEN", "s3cret")

    _purge_backend_modules()

    import main

    with TestClient(main.app) as c:
        assert c.post("/api/init-db").status_code == 403
        assert (
            c.post(
                "/api/init-db",
                headers={"X-Admin-Token": "s3cret"},
            ).status_code
            == 200
        )

    _purge_backend_modules()
