"""Integration tests verifying single-origin reverse proxy routes on port 8501."""

import pytest
import requests


def test_single_origin_routes():
    base_url = "http://localhost:8501"
    try:
        r_health = requests.get(f"{base_url}/api/health", timeout=2)
    except Exception:
        pytest.skip("Single-origin Caddy service is not running locally on port 8501.")

    assert r_health.status_code == 200
    assert r_health.json()["target_unit"] == "MW"

    r_forecast = requests.get(f"{base_url}/api/forecast", timeout=3)
    assert r_forecast.status_code == 200
    assert r_forecast.json()["unit"] == "MW"

    r_status = requests.get(f"{base_url}/api/data-status", timeout=3)
    assert r_status.status_code == 200
    assert "freshness_status" in r_status.json()

    r_metrics = requests.get(f"{base_url}/api/metrics", timeout=2)
    assert r_metrics.status_code == 200

    r_docs = requests.get(f"{base_url}/api/docs", timeout=2)
    assert r_docs.status_code == 200

    r_root = requests.get(f"{base_url}/", timeout=2)
    assert r_root.status_code == 200
