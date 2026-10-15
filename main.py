"""End-to-End Execution Orchestrator for All-India Grid Demand Forecasting.

Runs the complete lifecycle pipeline:
1. Ingests and processes historical Indian Grid demand from Mendeley Data (MW)
2. Generates anti-leakage calendar and historical lag features
3. Trains and benchmarks Seasonal-Naive, Linear Regression, and Random Forest models
4. Selects the best performing model on validation data and evaluates on held-out test data
5. Generates the 24-hour horizon recursive demand forecast in MW
6. Validates outputs and displays unified single-origin startup commands
"""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_data import main as prepare_data_main
from scripts.train_model import main as train_model_main
from scripts.generate_forecast import main as generate_forecast_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("orchestrator")


def run_pipeline():
    logger.info("=" * 70)
    logger.info("ALL-INDIA ELECTRICITY GRID DEMAND FORECASTING PIPELINE")
    logger.info("=" * 70)

    # Step 1: Ingest & Preprocess
    logger.info(">>> STEP 1: PREPARING HISTORICAL INDIAN GRID DATA (MENDELEY / POSOCO)")
    prepare_data_main()

    # Step 2: Feature Engineering, Split & Model Training
    logger.info(">>> STEP 2: TRAINING & BENCHMARKING FORECASTING MODELS (MW)")
    train_model_main()

    # Step 3: Recursive Multi-step Forecast
    logger.info(">>> STEP 3: GENERATING 24-HOUR HORIZON DEMAND FORECAST (MW)")
    generate_forecast_main()

    logger.info("=" * 70)
    logger.info("PIPELINE EXECUTED SUCCESSFULLY!")
    logger.info("Artifacts Generated:")
    logger.info(" - Clean Hourly Data: data/processed/india_hourly_demand.csv")
    logger.info(" - Trained Model:     models/best_model.joblib")
    logger.info(" - Evaluation Metrics:outputs/metrics/evaluation_metrics.json")
    logger.info(" - 24-Hour Forecast:  outputs/forecasts/forecast_24h.csv & .json")
    logger.info("=" * 70)
    logger.info("Single-Origin System Launch (Port 8501 via Caddy):")
    logger.info("  PowerShell Launcher:  .\\run_system.ps1")
    logger.info("  Unified Dashboard:    http://localhost:8501/")
    logger.info("  Unified API Docs:     http://localhost:8501/api/docs")
    logger.info("  Unified Live Status:  http://localhost:8501/api/data-status")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_pipeline()
