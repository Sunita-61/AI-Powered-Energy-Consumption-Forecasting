"""Unit tests for preprocessing and Indian Grid data validation."""

import pytest
import pandas as pd
import numpy as np

from src.energy_forecasting.config import TIME_COL, TARGET_COL, TARGET_UNIT
from src.energy_forecasting.preprocessing import (
    validate_grid_dataframe,
    clean_and_validate_india_demand,
)


def test_validate_grid_dataframe_valid():
    df = pd.DataFrame(
        {
            TIME_COL: pd.date_range("2023-01-01", periods=5, freq="h"),
            TARGET_COL: [150000.0, 160000.0, 170000.0, 180000.0, 190000.0],
        }
    )
    validate_grid_dataframe(df)


def test_validate_grid_dataframe_missing_column():
    df = pd.DataFrame({"invalid_col": [1, 2, 3]})
    with pytest.raises(ValueError, match="Mandatory time column"):
        validate_grid_dataframe(df)


def test_clean_and_validate_india_demand_duplicate_and_missing():
    # 2 duplicate timestamps and 1 missing hour
    timestamps = pd.to_datetime([
        "2023-01-01 00:00:00",
        "2023-01-01 00:00:00",  # duplicate
        "2023-01-01 01:00:00",
        "2023-01-01 03:00:00",  # hour 02:00 is missing
    ])
    demands = [150000.0, 170000.0, 160000.0, 180000.0]
    df_raw = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: demands})

    clean_df, report = clean_and_validate_india_demand(df_raw)
    assert report["duplicates_resolved"] == 2
    assert report["missing_intervals_interpolated"] == 1
    assert len(clean_df) == 4  # 00:00, 01:00, 02:00, 03:00
    assert clean_df[TARGET_COL].iloc[2] == 170000.0  # Linear interpolation between 160k and 180k
