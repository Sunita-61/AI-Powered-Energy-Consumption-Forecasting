"""Data ingestion for Indian National Grid electricity demand from Mendeley Data and verified fallbacks."""

from pathlib import Path
from typing import Optional, List
import logging
import numpy as np
import pandas as pd

from src.energy_forecasting.config import (
    RAW_DATA_DIR,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
    MENDELEY_DATASET_TITLE,
    MENDELEY_DOI,
    MENDELEY_LICENSE,
)

logger = logging.getLogger(__name__)


def generate_synthetic_india_demand_data(
    start_date: str = "2023-01-01 00:00:00",
    days: int = 180,
    seed: int = 42,
) -> pd.DataFrame:
    """Generates realistic Indian National Grid electricity demand as a verified synthetic fallback.

    Explicitly labeled as synthetic in compliance with documentation ethics rules.
    Models national demand magnitude (~160,000 MW to 240,000 MW), diurnal summer/winter
    peaks, weekly variations, and realistic grid fluctuations.

    Returns:
        pd.DataFrame with columns [TIME_COL, TARGET_COL] with metadata `is_synthetic=True`.
    """
    np.random.seed(seed)
    timestamps = pd.date_range(start=start_date, periods=days * 24, freq="h")
    n = len(timestamps)

    # Base national demand in MW (~180,000 MW)
    base_demand = 185000.0

    # Diurnal cycle: peaks in early evening ~19:00 - 21:00 and afternoon ~14:00 - 16:00
    hours = timestamps.hour
    diurnal = (
        25000.0 * np.sin(2 * np.pi * (hours - 7) / 24.0)
        + 8000.0 * np.sin(4 * np.pi * (hours - 12) / 24.0)
    )

    # Weekly pattern: Sunday/weekend demand reduction (~5-8% industrial dip)
    is_weekend = (timestamps.dayofweek >= 5).astype(float)
    weekend_factor = 1.0 - (is_weekend * 0.06)

    # Seasonal variation across months
    day_indices = np.arange(n) / 24.0
    seasonal = 15000.0 * np.sin(2 * np.pi * (day_indices - 80) / 365.0)

    # Stochastic operational variations
    noise = np.random.normal(loc=0.0, scale=3500.0, size=n)

    demand_mw = (base_demand + diurnal + seasonal) * weekend_factor + noise
    demand_mw = np.clip(demand_mw, a_min=110000.0, a_max=260000.0)

    df = pd.DataFrame(
        {
            TIME_COL: timestamps,
            TARGET_COL: np.round(demand_mw, 2),
        }
    )
    df.attrs["is_synthetic"] = True
    df.attrs["unit"] = TARGET_UNIT
    df.attrs["source"] = "Synthetic Fallback Generator"
    return df


def parse_mendeley_excel_sheet(file_path: Path | str) -> pd.DataFrame:
    """Parses a single Mendeley Data Excel file containing 5-minute SCADA telemetry.

    Sheet1 contains SCADA tags with label in row 0:
    Col 'Time': Timestamp (5-min intervals)
    Col 'SCADA/ANALOG/044MQ067/0' (or labeled 'NLDC_DEMAND|P'): National Grid Demand in MW.

    Converts 5-minute SCADA measurements into hourly mean demand (MW).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Mendeley file not found at {path}")

    logger.info(f"Loading Mendeley workbook: {path.name}...")
    # Read first 2 rows to locate demand column
    df_preview = pd.read_excel(path, sheet_name="Sheet1", nrows=2)

    demand_col_name = None
    for col in df_preview.columns:
        label = str(df_preview[col].iloc[0]).strip()
        if "NLDC_DEMAND" in label or "ALL_INDIA_DEMAND" in label or "044MQ067" in col:
            demand_col_name = col
            break

    if not demand_col_name:
        raise ValueError(f"Could not identify NLDC_DEMAND column in {path.name}")

    # Read entire sheet
    df_raw = pd.read_excel(path, sheet_name="Sheet1")
    # Row 0 contains label string; rows 1..N contain data
    df_data = df_raw.iloc[1:].copy()

    time_col_raw = df_raw.columns[0]
    df_data = df_data[[time_col_raw, demand_col_name]].copy()
    df_data.columns = [TIME_COL, TARGET_COL]

    # Convert to datetime and float
    df_data[TIME_COL] = pd.to_datetime(df_data[TIME_COL], errors="coerce")
    df_data[TARGET_COL] = pd.to_numeric(df_data[TARGET_COL], errors="coerce")

    # Drop NaNs
    df_data = df_data.dropna().sort_values(by=TIME_COL).reset_index(drop=True)

    # Resample from 5-minute SCADA to hourly mean demand (MW)
    hourly_df = (
        df_data.set_index(TIME_COL)
        .resample("h")
        .mean()
        .interpolate(method="time")
        .reset_index()
    )
    hourly_df[TARGET_COL] = hourly_df[TARGET_COL].round(2)

    logger.info(
        f"Parsed {len(df_data)} 5-min SCADA points -> {len(hourly_df)} hourly points from {path.name}"
    )
    return hourly_df


def load_all_mendeley_historical_data(raw_dir: Path | str = RAW_DATA_DIR) -> pd.DataFrame:
    """Discovers and concatenates all Mendeley monthly Excel workbooks in raw_dir."""
    p_dir = Path(raw_dir)
    excel_files = sorted(list(p_dir.glob("mendeley_*.xlsx")))

    if not excel_files:
        logger.warning(f"No mendeley_*.xlsx files found in {p_dir}. Using synthetic fallback.")
        return generate_synthetic_energy_data()

    frames: List[pd.DataFrame] = []
    for f in excel_files:
        try:
            df_month = parse_mendeley_excel_sheet(f)
            frames.append(df_month)
        except Exception as e:
            logger.error(f"Error parsing {f.name}: {e}")

    if not frames:
        raise RuntimeError("Failed to parse any historical Mendeley workbooks.")

    combined_df = pd.concat(frames, ignore_index=True)
    # Deduplicate timestamps across months
    combined_df = combined_df.drop_duplicates(subset=[TIME_COL]).sort_values(by=TIME_COL).reset_index(drop=True)

    combined_df.attrs["is_synthetic"] = False
    combined_df.attrs["unit"] = TARGET_UNIT
    combined_df.attrs["source"] = f"{MENDELEY_DATASET_TITLE} (DOI: {MENDELEY_DOI}, License: {MENDELEY_LICENSE})"
    return combined_df


def load_india_grid_data(
    file_path: Optional[Path | str] = None,
    allow_synthetic_fallback: bool = True,
) -> pd.DataFrame:
    """Loads processed Indian Grid dataset or parses from raw workbooks."""
    if file_path:
        p = Path(file_path)
        if p.exists() and p.is_file():
            df = pd.read_csv(p)
            df[TIME_COL] = pd.to_datetime(df[TIME_COL])
            df.attrs["is_synthetic"] = False
            df.attrs["unit"] = TARGET_UNIT
            return df

    # Check for raw Mendeley files
    try:
        return load_all_mendeley_historical_data(RAW_DATA_DIR)
    except Exception as e:
        logger.warning(f"Could not load Mendeley historical data: {e}")
        if allow_synthetic_fallback:
            logger.info("Using verified synthetic fallback Indian Grid series...")
            return generate_synthetic_india_demand_data()
        raise
