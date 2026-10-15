"""Live data connector for Indian National Grid electricity demand.

Connects to verified public live feeds, implements retry with exponential backoff,
calculates data age and freshness status, caches last valid readings, and provides
graceful fallbacks with links to official portals without data fabrication.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import time
import json
import logging
import requests
import pandas as pd

from src.energy_forecasting.config import (
    LIVE_API_BASE_URL,
    LIVE_ZONE_IN_ENDPOINT,
    LIVE_STATUS_ENDPOINT,
    LIVE_CACHE_FILE,
    LIVE_HOURLY_LOG_FILE,
    OFFICIAL_NPP_PORTAL_URL,
    FRESH_THRESHOLD_MINUTES,
    STALE_THRESHOLD_MINUTES,
    HTTP_TIMEOUT_SECONDS,
    HTTP_MAX_RETRIES,
    HTTP_BACKOFF_FACTOR,
)

logger = logging.getLogger(__name__)


@dataclass
class LiveDemandReading:
    zone: str
    demand_met_mw: float
    unit: str
    source_attribution: str
    observation_time_utc: str
    retrieval_time_utc: str
    data_age_minutes: float
    freshness_status: str  # FRESH, STALE, CACHED, UNAVAILABLE
    feed_online: bool
    is_cached: bool
    error_message: Optional[str] = None
    official_portal_url: str = OFFICIAL_NPP_PORTAL_URL

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_data_freshness(observation_dt: datetime, retrieval_dt: datetime) -> tuple[float, str]:
    """Calculates data age in minutes and categorizes freshness status."""
    if observation_dt.tzinfo is None:
        observation_dt = observation_dt.replace(tzinfo=timezone.utc)
    if retrieval_dt.tzinfo is None:
        retrieval_dt = retrieval_dt.replace(tzinfo=timezone.utc)

    diff = (retrieval_dt - observation_dt).total_seconds() / 60.0
    data_age_minutes = max(0.0, round(diff, 1))

    if data_age_minutes <= FRESH_THRESHOLD_MINUTES:
        status = "FRESH"
    elif data_age_minutes <= STALE_THRESHOLD_MINUTES:
        status = "STALE"
    else:
        status = "VERY_STALE"

    return data_age_minutes, status


def parse_live_zone_payload(payload: Dict[str, Any], retrieval_dt: datetime) -> LiveDemandReading:
    """Validates and parses the national zone live payload."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object.")

    zone = payload.get("zone")
    if zone != "IN":
        raise ValueError(f"Expected zone 'IN', got '{zone}'.")

    metrics = payload.get("metrics", [])
    if not isinstance(metrics, list) or len(metrics) == 0:
        raise ValueError("Payload does not contain valid metrics list.")

    demand_metric = None
    for m in metrics:
        if m.get("metric") == "demand_met":
            demand_metric = m
            break

    if not demand_metric:
        raise ValueError("Metric 'demand_met' not found in live metrics payload.")

    raw_val = demand_metric.get("value")
    if raw_val is None or not isinstance(raw_val, (int, float)):
        raise ValueError(f"Invalid demand value: {raw_val}")

    demand_mw = float(raw_val)
    unit = demand_metric.get("unit", "MW")
    source = demand_metric.get("source", "vidyut_pravah")
    ts_str = demand_metric.get("ts")

    if not ts_str:
        raise ValueError("Missing observation timestamp 'ts' in metric.")

    obs_dt = pd.to_datetime(ts_str).to_pydatetime()
    data_age_min, freshness = calculate_data_freshness(obs_dt, retrieval_dt)

    return LiveDemandReading(
        zone=zone,
        demand_met_mw=round(demand_mw, 2),
        unit=unit,
        source_attribution=f"Candidate Aggregator (source: {source})",
        observation_time_utc=obs_dt.isoformat(),
        retrieval_time_utc=retrieval_dt.isoformat(),
        data_age_minutes=data_age_min,
        freshness_status=freshness,
        feed_online=True,
        is_cached=False,
    )


def save_cached_reading(reading: LiveDemandReading) -> None:
    """Persists last-known valid reading to disk cache."""
    try:
        LIVE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LIVE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(reading.to_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to persist live reading cache: {e}")


def load_cached_reading() -> Optional[LiveDemandReading]:
    """Retrieves last-known valid reading from disk cache."""
    if not LIVE_CACHE_FILE.exists():
        return None
    try:
        with open(LIVE_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["is_cached"] = True
        data["freshness_status"] = "CACHED"
        return LiveDemandReading(**data)
    except Exception as e:
        logger.warning(f"Failed to read live cache: {e}")
        return None


def log_hourly_reading(reading: LiveDemandReading) -> None:
    """Appends unique hourly live observations to a continuous CSV log."""
    try:
        LIVE_HOURLY_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "observation_time_utc": reading.observation_time_utc,
            "retrieval_time_utc": reading.retrieval_time_utc,
            "demand_mw": reading.demand_met_mw,
            "unit": reading.unit,
            "data_age_min": reading.data_age_minutes,
            "source": reading.source_attribution,
        }
        df_new = pd.DataFrame([row])
        if not LIVE_HOURLY_LOG_FILE.exists():
            df_new.to_csv(LIVE_HOURLY_LOG_FILE, index=False)
        else:
            df_existing = pd.read_csv(LIVE_HOURLY_LOG_FILE)
            if reading.observation_time_utc not in df_existing["observation_time_utc"].values:
                df_new.to_csv(LIVE_HOURLY_LOG_FILE, mode="a", header=False, index=False)
    except Exception as e:
        logger.warning(f"Failed to append to hourly live log: {e}")


def fetch_live_grid_demand(
    base_url: str = LIVE_API_BASE_URL,
    endpoint: str = LIVE_ZONE_IN_ENDPOINT,
    timeout: int = HTTP_TIMEOUT_SECONDS,
    max_retries: int = HTTP_MAX_RETRIES,
    backoff_factor: float = HTTP_BACKOFF_FACTOR,
) -> LiveDemandReading:
    """Fetches real-time National Grid demand with retries, validation, and caching.

    Returns:
        LiveDemandReading with verified metrics or cached fallback with explicit status.
    """
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"User-Agent": "AI-Energy-Forecasting/1.0 (+https://github.com)"}

    last_error: Optional[str] = None
    for attempt in range(1, max_retries + 1):
        retrieval_dt = datetime.now(timezone.utc)
        try:
            logger.info(f"Polling live grid demand from {url} (attempt {attempt}/{max_retries})...")
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                payload = response.json()
                reading = parse_live_zone_payload(payload, retrieval_dt)
                # Persist cache and log
                save_cached_reading(reading)
                log_hourly_reading(reading)
                return reading
            else:
                last_error = f"HTTP {response.status_code}: {response.text[:150]}"
                logger.warning(f"Live API non-200 response: {last_error}")
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Live API attempt {attempt} failed: {e}")

        if attempt < max_retries:
            sleep_duration = backoff_factor ** (attempt - 1)
            time.sleep(sleep_duration)

    # All retries failed - handle gracefully
    logger.error(f"Live source unavailable after {max_retries} attempts: {last_error}")
    cached = load_cached_reading()
    if cached:
        cached.feed_online = False
        cached.error_message = f"Live feed offline: {last_error}. Showing last cached reading."
        return cached

    # No cache available: Return explicit UNAVAILABLE state without fabricating data
    return LiveDemandReading(
        zone="IN",
        demand_met_mw=0.0,
        unit="MW",
        source_attribution="Unavailable",
        observation_time_utc="",
        retrieval_time_utc=datetime.now(timezone.utc).isoformat(),
        data_age_minutes=-1.0,
        freshness_status="UNAVAILABLE",
        feed_online=False,
        is_cached=False,
        error_message=f"Live feed unreachable ({last_error}). Official verification portal: {OFFICIAL_NPP_PORTAL_URL}",
    )


def fetch_live_feed_status(base_url: str = LIVE_API_BASE_URL) -> Dict[str, Any]:
    """Queries candidate live aggregator status endpoint."""
    url = f"{base_url.rstrip('/')}/{LIVE_STATUS_ENDPOINT.lstrip('/')}"
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            return {"status": "ONLINE", "details": r.json()}
        return {"status": "DEGRADED", "http_status": r.status_code}
    except Exception as e:
        return {"status": "OFFLINE", "error": str(e), "official_portal": OFFICIAL_NPP_PORTAL_URL}
