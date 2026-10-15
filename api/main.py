"""FastAPI REST Service for All-India Electricity Grid Demand Forecasting."""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.energy_forecasting.config import (
    PROCESSED_INDIA_DATA_FILE,
    BEST_MODEL_FILE,
    EVALUATION_METRICS_FILE,
    TIME_COL,
    TARGET_COL,
    TARGET_UNIT,
    FORECAST_HORIZON_HOURS,
    OFFICIAL_NPP_PORTAL_URL,
)
from src.energy_forecasting.models import load_model
from src.energy_forecasting.forecasting import (
    generate_24h_forecast,
    generate_realtime_grid_forecast,
)
from src.energy_forecasting.live_connector import (
    fetch_live_grid_demand,
    fetch_live_feed_status,
    load_cached_reading,
)

app = FastAPI(
    title="All-India Electricity Grid Demand Forecasting API",
    description="Unified REST API serving 24-hour Indian Grid multi-step demand predictions, live data freshness, and benchmark metrics.",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

MODEL_CACHE: Dict[str, Any] = {}


def get_cached_model():
    if "model" not in MODEL_CACHE:
        if not BEST_MODEL_FILE.exists():
            return None, None
        model, metadata = load_model(BEST_MODEL_FILE)
        MODEL_CACHE["model"] = model
        MODEL_CACHE["metadata"] = metadata
    return MODEL_CACHE["model"], MODEL_CACHE["metadata"]


# Response Schemas
class HealthResponse(BaseModel):
    status: str
    timestamp_utc: str
    model_loaded: bool
    model_name: Optional[str]
    target_unit: str
    live_feed_status: str
    data_age_minutes: Optional[float]
    official_portal_url: str


class ForecastItem(BaseModel):
    timestamp: str
    horizon_step: int
    demand_mw: float
    unit: str


class ForecastResponse(BaseModel):
    forecast_origin: str
    model_name: str
    horizon_hours: int
    unit: str
    peak_demand_mw: float
    peak_hour: str
    min_demand_mw: float
    min_hour: str
    generated_at_utc: str
    is_synthetic: bool
    forecast: List[ForecastItem]


class DataStatusResponse(BaseModel):
    feed_online: bool
    freshness_status: str
    demand_met_mw: float
    unit: str
    observation_time_utc: str
    retrieval_time_utc: str
    data_age_minutes: float
    is_cached: bool
    source_attribution: str
    official_verification_url: str
    error_message: Optional[str] = None


@app.get("/api/health", response_model=HealthResponse)
def get_health():
    """Health, model availability, and live feed status endpoint."""
    model, metadata = get_cached_model()
    model_loaded = model is not None
    model_name = metadata.get("best_model_name") if metadata else None

    # Check cached or live status
    cached = load_cached_reading()
    feed_status = cached.freshness_status if cached else "UNKNOWN"
    age = cached.data_age_minutes if cached else None

    return HealthResponse(
        status="healthy" if model_loaded else "degraded",
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        model_loaded=model_loaded,
        model_name=model_name,
        target_unit=TARGET_UNIT,
        live_feed_status=feed_status,
        data_age_minutes=age,
        official_portal_url=OFFICIAL_NPP_PORTAL_URL,
    )


@app.get("/api/data-status", response_model=DataStatusResponse)
def get_data_status():
    """Returns real-time data freshness, latest observation timestamp, and provider health."""
    reading = fetch_live_grid_demand()
    return DataStatusResponse(
        feed_online=reading.feed_online,
        freshness_status=reading.freshness_status,
        demand_met_mw=reading.demand_met_mw,
        unit=reading.unit,
        observation_time_utc=reading.observation_time_utc,
        retrieval_time_utc=reading.retrieval_time_utc,
        data_age_minutes=reading.data_age_minutes,
        is_cached=reading.is_cached,
        source_attribution=reading.source_attribution,
        official_verification_url=reading.official_portal_url,
        error_message=reading.error_message,
    )


@app.get("/api/metrics")
def get_metrics():
    """Returns verified chronological benchmark metrics across all candidate models."""
    if not EVALUATION_METRICS_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation metrics not found. Train models first via scripts/train_model.py.",
        )
    with open(EVALUATION_METRICS_FILE, "r", encoding="utf-8") as f:
        import json
        return json.load(f)


@app.get("/api/forecast", response_model=ForecastResponse)
def get_forecast(
    horizon_hours: int = 24,
    cutoff_timestamp: Optional[str] = None,
    mode: Optional[str] = None,
):
    """Returns next-24-hour All-India electricity grid demand forecast in MW.
    
    Supports mode='realtime' (anchored to current live telemetry) or mode='historical' (Nov 2021 holdout).
    """
    model, metadata = get_cached_model()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trained forecasting model is unavailable. Run scripts/train_model.py first.",
        )

    if not PROCESSED_INDIA_DATA_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processed Indian grid dataset is missing. Run scripts/prepare_data.py first.",
        )

    df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])

    try:
        if mode == "realtime" or (cutoff_timestamp is None and mode != "historical"):
            _, forecast_df = generate_realtime_grid_forecast(
                model=model,
                history_df=df,
                horizon_hours=horizon_hours,
                model_name=metadata.get("best_model_name", "RandomForestRegressor"),
            )
            origin = forecast_df["forecast_origin"].iloc[0]
        else:
            origin = pd.to_datetime(cutoff_timestamp) if cutoff_timestamp else df[TIME_COL].max()
            forecast_df = generate_24h_forecast(
                history_df=df,
                model=model,
                origin_timestamp=origin,
                horizon_hours=horizon_hours,
                target_col=TARGET_COL,
                time_col=TIME_COL,
                model_name=metadata.get("best_model_name", "TrainedForecaster"),
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Forecasting engine error: {str(e)}",
        )

    peak_row = forecast_df.loc[forecast_df[TARGET_COL].idxmax()]
    min_row = forecast_df.loc[forecast_df[TARGET_COL].idxmin()]

    items = [
        ForecastItem(
            timestamp=str(row[TIME_COL]),
            horizon_step=int(row["horizon_step"]),
            demand_mw=float(row[TARGET_COL]),
            unit=TARGET_UNIT,
        )
        for _, row in forecast_df.iterrows()
    ]

    return ForecastResponse(
        forecast_origin=str(origin),
        model_name=metadata.get("best_model_name", "TrainedForecaster"),
        horizon_hours=horizon_hours,
        unit=TARGET_UNIT,
        peak_demand_mw=float(peak_row[TARGET_COL]),
        peak_hour=str(peak_row[TIME_COL]),
        min_demand_mw=float(min_row[TARGET_COL]),
        min_hour=str(min_row[TIME_COL]),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        is_synthetic=metadata.get("is_synthetic", False),
        forecast=items,
    )
