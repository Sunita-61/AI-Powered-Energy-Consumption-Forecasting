"""Model Training and Benchmarking CLI Script for Indian Grid Demand.

Loads processed Indian hourly demand data, creates anti-leakage features,
splits chronologically (Train 70%, Val 15%, Test 15%),
trains Baseline, Linear Regression, and Random Forest,
benchmarks validation metrics (MAE, RMSE, WAPE in MW),
saves the best model to models/best_model.joblib,
and writes outputs/metrics/evaluation_metrics.json.
"""

import sys
import json
import logging
from pathlib import Path
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.energy_forecasting.config import (
    PROCESSED_INDIA_DATA_FILE,
    BEST_MODEL_FILE,
    EVALUATION_METRICS_FILE,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
)
from src.energy_forecasting.training import train_and_benchmark
from src.energy_forecasting.models import save_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_model")


def main():
    logger.info("=" * 65)
    logger.info("STAGE 4: MODEL TRAINING & CHRONOLOGICAL BENCHMARKING (INDIA GRID)")
    logger.info("=" * 65)

    if not PROCESSED_INDIA_DATA_FILE.exists():
        logger.error(f"Processed data file {PROCESSED_INDIA_DATA_FILE} not found. Run prepare_data.py first.")
        sys.exit(1)

    logger.info(f"Loading processed hourly Indian Grid demand from: {PROCESSED_INDIA_DATA_FILE}")
    hourly_df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
    hourly_df[TIME_COL] = pd.to_datetime(hourly_df[TIME_COL])

    # Train and benchmark models
    benchmark_results, best_model, metadata = train_and_benchmark(
        hourly_df, target_col=TARGET_COL, time_col=TIME_COL
    )

    # Save best model artifact
    save_model(best_model, BEST_MODEL_FILE, metadata=metadata)
    logger.info(f"Saved best model ({metadata['best_model_name']}) to: {BEST_MODEL_FILE}")

    # Save metrics JSON
    EVALUATION_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(EVALUATION_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)
    logger.info(f"Saved evaluation metrics to: {EVALUATION_METRICS_FILE}")

    print("\n" + "=" * 65)
    print(f"BENCHMARK EVALUATION RESULTS - ALL-INDIA GRID DEMAND ({TARGET_UNIT})")
    print("=" * 65)
    print(json.dumps(benchmark_results, indent=2))
    print("=" * 65)
    print(f"Selected Best Model: {metadata['best_model_name']}")
    print(f"Validation MAE: {metadata['validation_mae']:,.2f} {TARGET_UNIT}")
    print(f"Test MAE (Held-out): {metadata['test_metrics']['MAE']:,.2f} {TARGET_UNIT}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
