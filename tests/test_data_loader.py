"""Unit tests for data_loader module."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.energy_forecasting.config import TIME_COL, TARGET_COL, TARGET_UNIT
from src.energy_forecasting.data_loader import (
    generate_synthetic_india_demand_data,
    load_india_grid_data,
)


def test_generate_synthetic_india_demand_data_schema():
    df = generate_synthetic_india_demand_data(days=5, seed=42)
    assert not df.empty
    assert TIME_COL in df.columns
    assert TARGET_COL in df.columns
    assert len(df) == 5 * 24  # 5 days * 24 hours
    assert df[TARGET_COL].min() >= 100000.0  # Real national Indian grid scale
    assert df.attrs.get("is_synthetic") is True
    assert df.attrs.get("unit") == TARGET_UNIT


def test_load_india_grid_data_from_processed(tmp_path):
    csv_file = tmp_path / "india_test.csv"
    timestamps = pd.date_range("2023-01-01", periods=10, freq="h")
    demands = np.random.uniform(150000.0, 200000.0, size=10)
    df_in = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: demands})
    df_in.to_csv(csv_file, index=False)

    df_loaded = load_india_grid_data(csv_file)
    assert len(df_loaded) == 10
    assert df_loaded.attrs.get("unit") == TARGET_UNIT
