"""Data Preparation CLI Script for Indian National Grid Demand.

Ingests historical SCADA telemetry from Mendeley Data workbooks (or verified synthetic fallback),
validates schema, removes duplicate timestamps, interpolates missing intervals,
and exports data/processed/india_hourly_demand.csv and data/sample/sample_india_demand.csv.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.energy_forecasting.config import (
    PROCESSED_INDIA_DATA_FILE,
    SAMPLE_INDIA_DATA_FILE,
    TARGET_COL,
    TIME_COL,
    RAW_DATA_DIR,
)
from src.energy_forecasting.data_loader import load_india_grid_data
from src.energy_forecasting.preprocessing import clean_and_validate_india_demand

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prepare_data")


def main():
    logger.info("=" * 65)
    logger.info("STAGE 3: DATA PREPARATION - ALL-INDIA ELECTRICITY GRID DEMAND")
    logger.info("=" * 65)

    # Ingest historical data from Mendeley Excel files
    raw_df = load_india_grid_data(allow_synthetic_fallback=True)
    logger.info(f"Loaded {len(raw_df)} initial hourly observations. Columns: {list(raw_df.columns)}")

    # Clean and validate
    clean_df, quality_report = clean_and_validate_india_demand(
        raw_df, time_col=TIME_COL, target_col=TARGET_COL
    )

    # Save processed hourly dataset
    PROCESSED_INDIA_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_INDIA_DATA_FILE, index=False)
    logger.info(f"Saved {len(clean_df)} processed hourly records to: {PROCESSED_INDIA_DATA_FILE}")

    # Save lightweight sample slice (last 720 hours = 30 days) for quick test benchmark
    sample_slice = clean_df.tail(720).copy().reset_index(drop=True)
    SAMPLE_INDIA_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    sample_slice.to_csv(SAMPLE_INDIA_DATA_FILE, index=False)
    logger.info(f"Saved {len(sample_slice)} sample hourly records to: {SAMPLE_INDIA_DATA_FILE}")

    print("\n" + "=" * 65)
    print("DATA QUALITY AUDIT REPORT - ALL-INDIA GRID DEMAND")
    print("=" * 65)
    print(json.dumps(quality_report, indent=2))
    print("=" * 65)
    print("\nFirst 5 Processed Records:")
    print(clean_df.head())
    print("\nLast 5 Processed Records:")
    print(clean_df.tail())
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
