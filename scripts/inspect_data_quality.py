"""Data Quality Inspection CLI Script for All-India Electricity Grid Demand.

Inspects raw SCADA records, resampled hourly observations, and processed datasets,
confirms schema integrity, timestamp monotonicity, and physical bounds (MW).
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
    SAMPLE_INDIA_DATA_FILE,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
)
from src.energy_forecasting.preprocessing import clean_and_validate_india_demand

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("inspect_data_quality")


def main():
    logger.info("=" * 65)
    logger.info("DATA QUALITY AUDIT - ALL-INDIA ELECTRICITY GRID DEMAND")
    logger.info("=" * 65)

    if not PROCESSED_INDIA_DATA_FILE.exists():
        logger.error(f"Processed file {PROCESSED_INDIA_DATA_FILE} not found. Run prepare_data.py first.")
        sys.exit(1)

    df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
    logger.info(f"Loaded {len(df)} records from {PROCESSED_INDIA_DATA_FILE}")

    clean_df, report = clean_and_validate_india_demand(df, time_col=TIME_COL, target_col=TARGET_COL)

    print("\n" + "=" * 65)
    print("DATA QUALITY AUDIT REPORT")
    print("=" * 65)
    print(json.dumps(report, indent=2))
    print("=" * 65)

    print("\nSample Hourly Records (First 5):")
    print(clean_df.head())
    print("\nSample Hourly Records (Last 5):")
    print(clean_df.tail())
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
