"""Unit tests for training module and chronological splitting."""

import pytest
import pandas as pd
import numpy as np

from src.energy_forecasting.config import TIME_COL, TARGET_COL
from src.energy_forecasting.training import (
    chronological_train_val_test_split,
    train_and_benchmark,
)


def test_chronological_split():
    timestamps = pd.date_range("2023-01-01", periods=100, freq="h")
    df = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: range(100)})

    train_df, val_df, test_df = chronological_train_val_test_split(
        df, train_ratio=0.70, val_ratio=0.15
    )

    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15
    assert train_df[TIME_COL].max() < val_df[TIME_COL].min()
    assert val_df[TIME_COL].max() < test_df[TIME_COL].min()


def test_train_and_benchmark_execution():
    timestamps = pd.date_range("2023-01-01", periods=300, freq="h")
    vals = 160000.0 + 15000.0 * np.sin(np.arange(300) * 2 * np.pi / 24.0)
    df = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: vals})

    benchmark_results, best_model, metadata = train_and_benchmark(df)

    assert "validation_metrics" in benchmark_results
    assert "SeasonalNaiveBaseline" in benchmark_results["validation_metrics"]
    assert "LinearRegression" in benchmark_results["validation_metrics"]
    assert "RandomForestRegressor" in benchmark_results["validation_metrics"]
    assert metadata["best_model_name"] in benchmark_results["validation_metrics"]
    assert "test_metrics" in benchmark_results
