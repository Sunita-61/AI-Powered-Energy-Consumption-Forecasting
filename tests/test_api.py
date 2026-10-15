"""Integration tests for FastAPI endpoints with /api routing."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert data["target_unit"] == "MW"
    assert "https://npp.gov.in" in data["official_portal_url"]


def test_api_metrics_endpoint(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "validation_metrics" in data
    assert data["target_unit"] == "MW"


def test_api_forecast_endpoint(client):
    response = client.get("/api/forecast?horizon_hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_hours"] == 24
    assert len(data["forecast"]) == 24
    assert data["unit"] == "MW"
    assert data["peak_demand_mw"] > 0.0


def test_api_data_status_endpoint(client):
    response = client.get("/api/data-status")
    assert response.status_code == 200
    data = response.json()
    assert "freshness_status" in data
    assert "demand_met_mw" in data
    assert data["unit"] == "MW"
