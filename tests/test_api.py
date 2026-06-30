"""
tests/test_api.py
──────────────────
FastAPI endpoint integration tests using httpx TestClient.
Tests all 5 route groups: executive, attrition, manager-effect, pay-fairness, retention.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def client():
    """Create FastAPI test client."""
    from backend.app.main import app
    return TestClient(app)


def test_health_check(client):
    """API should return healthy status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root(client):
    """Root endpoint should return welcome message."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "PeopleLens" in resp.json()["message"]


def test_executive_kpis_endpoint(client):
    """Executive KPIs endpoint should return either data or 503 (data not generated yet)."""
    resp = client.get("/api/v1/executive/kpis")
    assert resp.status_code in [200, 503]
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] == "ok"
        assert "data" in data


def test_attrition_by_dimension_valid(client):
    """Valid dimension should return 200 or 503."""
    resp = client.get("/api/v1/attrition/by-dimension?dimension=department")
    assert resp.status_code in [200, 503]


def test_attrition_by_dimension_invalid(client):
    """Invalid dimension should return 400."""
    resp = client.get("/api/v1/attrition/by-dimension?dimension=invalid_col")
    assert resp.status_code == 400


def test_attrition_tenure_bands(client):
    """Tenure band endpoint should return 200 or 503."""
    resp = client.get("/api/v1/attrition/tenure-bands")
    assert resp.status_code in [200, 503]


def test_manager_rankings_endpoint(client):
    """Manager rankings should return 200 or 503."""
    resp = client.get("/api/v1/manager-effect/rankings")
    assert resp.status_code in [200, 503]


def test_manager_rankings_top_n(client):
    """top_n parameter bounds should be respected."""
    resp = client.get("/api/v1/manager-effect/rankings?top_n=5")
    assert resp.status_code in [200, 503]
    if resp.status_code == 200:
        data = resp.json()["data"]
        assert len(data) <= 5


def test_pay_fairness_overall(client):
    """Pay fairness overall KPIs should return 200 or 503."""
    resp = client.get("/api/v1/pay-fairness/overall")
    assert resp.status_code in [200, 503]


def test_retention_cohort_table(client):
    """Retention cohort table should return 200 or 503."""
    resp = client.get("/api/v1/retention/cohort-table")
    assert resp.status_code in [200, 503]


def test_retention_kaplan_meier(client):
    """KM endpoint should return 200, 503, or 200 with lifelines_not_installed status."""
    resp = client.get("/api/v1/retention/kaplan-meier")
    assert resp.status_code in [200, 503]
