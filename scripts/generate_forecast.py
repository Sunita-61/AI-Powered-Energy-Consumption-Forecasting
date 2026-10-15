"""24-Hour Forecasting CLI Script for Indian Grid Electricity Demand.

Loads latest processed Indian grid history and the trained best model,
generates a 24-hour recursive autoregressive demand forecast in MW,
validates future timestamps and non-negative bounds,
and exports outputs/forecasts/forecast_24h.csv and forecast_24h.json.
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
    FORECAST_OUTPUT_CSV,
    FORECAST_OUTPUT_JSON,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
    FORECAST_HORIZON_HOURS,
)
from src.energy_forecasting.models import load_model
from src.energy_forecasting.forecasting import generate_24h_forecast

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("generate_forecast")


def main():
    logger.info("=" * 65)
    logger.info("STAGE 5: 24-HOUR RECURSIVE FORECASTING ENGINE - ALL-INDIA GRID")
    logger.info("=" * 65)

    if not BEST_MODEL_FILE.exists():
        logger.error(f"Trained model {BEST_MODEL_FILE} not found. Run train_model.py first.")
        sys.exit(1)

    if not PROCESSED_INDIA_DATA_FILE.exists():
        logger.error(f"Processed data {PROCESSED_INDIA_DATA_FILE} not found. Run prepare_data.py first.")
        sys.exit(1)

    logger.info(f"Loading trained model artifact from: {BEST_MODEL_FILE}")
    model, metadata = load_model(BEST_MODEL_FILE)
    model_name = metadata.get("best_model_name", "TrainedForecaster")
    logger.info(f"Loaded model architecture: {model_name}")

    logger.info(f"Loading historical readings from: {PROCESSED_INDIA_DATA_FILE}")
    hourly_df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
    hourly_df[TIME_COL] = pd.to_datetime(hourly_df[TIME_COL])

    origin = hourly_df[TIME_COL].max()
    logger.info(f"Forecast Origin Cutoff (T): {origin}")

    # Generate 24-hour forecast
    forecast_df = generate_24h_forecast(
        history_df=hourly_df,
        model=model,
        origin_timestamp=origin,
        horizon_hours=FORECAST_HORIZON_HOURS,
        target_col=TARGET_COL,
        time_col=TIME_COL,
        model_name=model_name,
    )

    # Save to CSV and JSON
    FORECAST_OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(FORECAST_OUTPUT_CSV, index=False)
    logger.info(f"Saved 24-hour forecast CSV to: {FORECAST_OUTPUT_CSV}")

    # Export structured JSON payload
    forecast_json_records = forecast_df.to_dict(orient="records")
    for r in forecast_json_records:
        r[TIME_COL] = str(r[TIME_COL])
        r["forecast_origin"] = str(r["forecast_origin"])

    forecast_payload = {
        "metadata": {
            "forecast_origin": str(origin),
            "horizon_hours": FORECAST_HORIZON_HOURS,
            "model_name": model_name,
            "unit": TARGET_UNIT,
            "is_synthetic": metadata.get("is_synthetic", False),
        },
        "forecast": forecast_json_records,
    }
    with open(FORECAST_OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(forecast_payload, f, indent=2)
    logger.info(f"Saved 24-hour forecast JSON to: {FORECAST_OUTPUT_JSON}")

    # Identify Peak and Minimum Forecast Hours
    peak_row = forecast_df.loc[forecast_df[TARGET_COL].idxmax()]
    min_row = forecast_df.loc[forecast_df[TARGET_COL].idxmin()]

    print("\n" + "=" * 65)
    print("24-HOUR ALL-INDIA GRID DEMAND FORECAST SUMMARY (MW)")
    print("=" * 65)
    print(forecast_df[[TIME_COL, "horizon_step", TARGET_COL, "unit"]].to_string(index=False))
    print("=" * 65)
    print(f"Peak Forecast Demand: {peak_row[TIME_COL]} -> {peak_row[TARGET_COL]:,.1f} {TARGET_UNIT}")
    print(f"Min Forecast Demand:  {min_row[TIME_COL]} -> {min_row[TARGET_COL]:,.1f} {TARGET_UNIT}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
