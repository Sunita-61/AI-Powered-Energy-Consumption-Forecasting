"""Hourly Live Grid Data Polling Script.

Connects to candidate live source, records national IN grid demand (MW),
evaluates data age and freshness, logs new observations, and caches results.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.energy_forecasting.live_connector import fetch_live_grid_demand, fetch_live_feed_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("poll_live_data")


def main():
    logger.info("=" * 60)
    logger.info("POLLING LIVE INDIAN GRID ELECTRICITY DEMAND")
    logger.info("=" * 60)

    reading = fetch_live_grid_demand()
    status_info = fetch_live_feed_status()

    print("\n" + "=" * 60)
    print("LIVE DEMAND METRIC READING")
    print("=" * 60)
    print(json.dumps(reading.to_dict(), indent=2))
    print("=" * 60)
    print(f"Aggregator Feed Status: {status_info.get('status')}")
    print(f"Demand Met: {reading.demand_met_mw:,.1f} {reading.unit}")
    print(f"Data Freshness: {reading.freshness_status} (Age: {reading.data_age_minutes} min)")
    print(f"Observation Time (UTC): {reading.observation_time_utc}")
    print(f"Official Verification Portal: {reading.official_portal_url}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
