"""Centralized project configuration, dataset parameters, and service constants.

All-India Electricity Grid Demand Forecasting System.
"""

from pathlib import Path
from typing import List

# Project Root Directory Resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
CACHE_DATA_DIR = DATA_DIR / "cache"
LIVE_DATA_DIR = DATA_DIR / "live"

# Artifact, Output, and Model Directories
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FORECASTS_DIR = OUTPUTS_DIR / "forecasts"
METRICS_DIR = OUTPUTS_DIR / "metrics"
FIGURES_DIR = OUTPUTS_DIR / "figures"
LOGS_DIR = OUTPUTS_DIR / "logs"

# Ensure all write directories exist
for path in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    SAMPLE_DATA_DIR,
    CACHE_DATA_DIR,
    LIVE_DATA_DIR,
    MODELS_DIR,
    FORECASTS_DIR,
    METRICS_DIR,
    FIGURES_DIR,
    LOGS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)

# Primary Dataset Metadata (Mendeley Data v2)
MENDELEY_DATASET_TITLE = (
    "Electricity Demand, Solar and Wind Generation Data (September 2021- June 2025) of India at 1-hour interval"
)
MENDELEY_DOI = "10.17632/y58jknpgs8.2"
MENDELEY_LICENSE = "CC BY 4.0"
MENDELEY_AUTHORS = "Debanjan Mukherjee, Karuna Kalita, Subhash Kumar"
MENDELEY_DATA_SOURCE = "North-Eastern Regional Load Despatch Centre, Grid-India under Ministry of Power"
MENDELEY_VERIFIED_COVERAGE = "September 2021 - December 2023 (Verified from actual workbook sheets)"

# Live Data Connector Configuration
# Candidate aggregator: https://github.com/ADIMANV/India-Energy-Data
LIVE_API_BASE_URL = "https://india-energy-data.vercel.app/api"
LIVE_ZONE_IN_ENDPOINT = "/v1/zone/IN/live"
LIVE_STATUS_ENDPOINT = "/v1/status"
LIVE_EXPORT_CSV_ENDPOINT = "/v1/export/live.csv"
LIVE_NATIONAL_ZONE = "IN"
LIVE_TARGET_METRIC = "demand_met"  # target: demand_met in MW

# Official Fallback Source (when candidate API is unavailable)
OFFICIAL_NPP_PORTAL_URL = "https://npp.gov.in/dashBoard/gc-map-dashboard-meritchart"

# Data Freshness Thresholds (Minutes)
FRESH_THRESHOLD_MINUTES = 90
STALE_THRESHOLD_MINUTES = 240

# Network & Resilience Parameters
HTTP_TIMEOUT_SECONDS = 10
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 1.5

# Canonical Target and Schema
TARGET_COL = "demand_mw"
TARGET_UNIT = "MW"
TIME_COL = "timestamp"

# Historical Feature Specifications
LAG_HOURS = [1, 24, 168]
ROLLING_WINDOW_HOURS = 24
FORECAST_HORIZON_HOURS = 24

FEATURE_COLUMNS: List[str] = [
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "month",
    "lag_1",
    "lag_24",
    "lag_168",
    "rolling_mean_24",
]

# Chronological Split Ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Default Random Seed
RANDOM_SEED = 42

# Artifact File Paths
PROCESSED_INDIA_DATA_FILE = PROCESSED_DATA_DIR / "india_hourly_demand.csv"
SAMPLE_INDIA_DATA_FILE = SAMPLE_DATA_DIR / "sample_india_demand.csv"
LIVE_CACHE_FILE = CACHE_DATA_DIR / "last_valid_live_reading.json"
LIVE_HOURLY_LOG_FILE = LIVE_DATA_DIR / "hourly_live_demand.csv"
BEST_MODEL_FILE = MODELS_DIR / "best_model.joblib"
EVALUATION_METRICS_FILE = METRICS_DIR / "evaluation_metrics.json"
FORECAST_OUTPUT_CSV = FORECASTS_DIR / "forecast_24h.csv"
FORECAST_OUTPUT_JSON = FORECASTS_DIR / "forecast_24h.json"

# Architecture Port Mappings
CADDY_PUBLIC_PORT = 8501
STREAMLIT_INTERNAL_PORT = 8502
FASTAPI_INTERNAL_PORT = 8000
