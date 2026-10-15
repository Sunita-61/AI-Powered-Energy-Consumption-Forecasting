"""Unit tests for live data connector, data freshness calculations, and mock responses."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.energy_forecasting.live_connector import (
    calculate_data_freshness,
    parse_live_zone_payload,
    fetch_live_grid_demand,
    LiveDemandReading,
)


def test_calculate_data_freshness_fresh():
    retrieval_dt = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    # 30 minutes old
    obs_dt = retrieval_dt - timedelta(minutes=30)
    age, status = calculate_data_freshness(obs_dt, retrieval_dt)
    assert age == 30.0
    assert status == "FRESH"


def test_calculate_data_freshness_stale():
    retrieval_dt = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    # 120 minutes old (between 90 and 240)
    obs_dt = retrieval_dt - timedelta(minutes=120)
    age, status = calculate_data_freshness(obs_dt, retrieval_dt)
    assert age == 120.0
    assert status == "STALE"


def test_parse_live_zone_payload_valid():
    retrieval_dt = datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    payload = {
        "zone": "IN",
        "estimation_basis": None,
        "metrics": [
            {
                "metric": "demand_met",
                "fuel": None,
                "value": 235000.0,
                "unit": "MW",
                "ts": "2026-10-15T09:30:00+00:00",
                "source": "vidyut_pravah",
                "estimated": False,
            }
        ],
    }

    reading = parse_live_zone_payload(payload, retrieval_dt)
    assert reading.zone == "IN"
    assert reading.demand_met_mw == 235000.0
    assert reading.unit == "MW"
    assert reading.data_age_minutes == 30.0
    assert reading.freshness_status == "FRESH"
    assert reading.feed_online is True


def test_parse_live_zone_payload_invalid_zone():
    retrieval_dt = datetime.now(timezone.utc)
    payload = {"zone": "US", "metrics": []}
    with pytest.raises(ValueError, match="Expected zone 'IN'"):
        parse_live_zone_payload(payload, retrieval_dt)


@patch("requests.get")
def test_fetch_live_grid_demand_offline_fallback(mock_get, tmp_path):
    # Simulate network failure
    mock_get.side_effect = Exception("Connection refused")

    reading = fetch_live_grid_demand(max_retries=1)
    # Should not raise exception; must return graceful status without fabricated data
    assert reading.zone == "IN"
    assert reading.freshness_status in ("CACHED", "UNAVAILABLE")
    assert reading.feed_online is False
    assert "https://npp.gov.in" in reading.official_portal_url
