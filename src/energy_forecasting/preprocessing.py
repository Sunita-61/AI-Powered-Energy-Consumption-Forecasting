"""Data cleaning, validation, and quality auditing for Indian Grid electricity demand."""

from typing import Tuple, Dict, Any
import logging
import numpy as np
import pandas as pd

from src.energy_forecasting.config import (
    TIME_COL,
    TARGET_COL,
    TARGET_UNIT,
)

logger = logging.getLogger(__name__)


def validate_grid_dataframe(
    df: pd.DataFrame,
    time_col: str = TIME_COL,
    target_col: str = TARGET_COL,
) -> None:
    """Validates schema, datatypes, and numeric sanity for Indian Grid Demand.

    Raises:
        ValueError: If mandatory columns are missing, data is empty, or values are non-numeric.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if time_col not in df.columns:
        raise ValueError(f"Mandatory time column '{time_col}' missing from DataFrame.")

    if target_col not in df.columns:
        raise ValueError(f"Mandatory target column '{target_col}' missing from DataFrame.")

    if not pd.api.types.is_numeric_dtype(df[target_col]):
        raise ValueError(
            f"Demand column '{target_col}' must be numeric, got {df[target_col].dtype}."
        )


def clean_and_validate_india_demand(
    df: pd.DataFrame,
    time_col: str = TIME_COL,
    target_col: str = TARGET_COL,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Cleans and validates the hourly Indian Grid demand time series.

    Steps:
    1. Validates schema.
    2. Parses and sorts timestamps in ascending order.
    3. Detects and resolves duplicate timestamps.
    4. Audits missing intervals and applies time-based linear interpolation for gaps.
    5. Checks bounds (national demand in India is realistically between 80,000 MW and 280,000 MW).
    6. Produces structured data quality summary.

    Returns:
        Tuple of (clean_df, data_quality_report).
    """
    validate_grid_dataframe(df, time_col=time_col, target_col=target_col)

    raw_row_count = len(df)
    work_df = df.copy()

    # Step 2: Timestamp parsing & sorting
    work_df[time_col] = pd.to_datetime(work_df[time_col])
    work_df = work_df.sort_values(by=time_col).reset_index(drop=True)

    # Step 3: Duplicate Timestamp Audit
    duplicate_mask = work_df.duplicated(subset=[time_col], keep=False)
    duplicates_detected = int(duplicate_mask.sum())
    if duplicates_detected > 0:
        logger.warning(f"Detected {duplicates_detected} duplicate timestamps. Averaging duplicates.")
        work_df = work_df.groupby(time_col, as_index=False)[target_col].mean().reset_index(drop=True)

    # Step 4: Missing intervals check
    work_df = work_df.set_index(time_col)
    full_range = pd.date_range(start=work_df.index.min(), end=work_df.index.max(), freq="h")
    missing_intervals = len(full_range) - len(work_df)

    if missing_intervals > 0:
        logger.warning(f"Detected {missing_intervals} missing hourly intervals. Reindexing and interpolating.")
        work_df = work_df.reindex(full_range)
        work_df[target_col] = work_df[target_col].interpolate(method="time").ffill().bfill()

    work_df = work_df.reset_index()
    work_df.columns = [time_col, target_col]

    # Step 5: Sanity and bound clamping
    negative_mask = work_df[target_col] < 0
    negative_count = int(negative_mask.sum())
    if negative_count > 0:
        logger.warning(f"Found {negative_count} negative demand values. Clamping to 0.0.")
        work_df[target_col] = work_df[target_col].clip(lower=0.0)

    # Build quality report
    report = {
        "raw_record_count": raw_row_count,
        "processed_hourly_count": len(work_df),
        "start_timestamp": str(work_df[time_col].min()),
        "end_timestamp": str(work_df[time_col].max()),
        "duplicates_resolved": duplicates_detected,
        "missing_intervals_interpolated": missing_intervals,
        "negative_values_clamped": negative_count,
        "mean_demand_mw": float(work_df[target_col].mean()),
        "std_demand_mw": float(work_df[target_col].std()),
        "min_demand_mw": float(work_df[target_col].min()),
        "max_demand_mw": float(work_df[target_col].max()),
        "target_units": TARGET_UNIT,
        "is_synthetic": df.attrs.get("is_synthetic", False),
    }

    work_df.attrs = df.attrs.copy()
    return work_df, report
