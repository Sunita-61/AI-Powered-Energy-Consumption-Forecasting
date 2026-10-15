"""Unit tests for feature engineering and data leakage prevention."""

import pytest
import pandas as pd
import numpy as np

from src.energy_forecasting.config import TARGET_COL, TIME_COL
from src.energy_forecasting.features import (
    create_features,
    extract_features_and_target,
    get_feature_column_names,
)


def test_create_features_leakage_prevention():
    n_hours = 200
    timestamps = pd.date_range("2023-01-01 00:00:00", periods=n_hours, freq="h")
    values = np.arange(1.0, n_hours + 1.0)
    df = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: values})

    df_feats = create_features(df, target_col=TARGET_COL, time_col=TIME_COL)

    # Check month
    assert "month" in df_feats.columns
    assert df_feats["month"].iloc[0] == 1

    # Check lag_1 at index i is exactly values[i-1]
    assert df_feats["lag_1"].iloc[10] == values[9]

    # Check lag_24 at index i is exactly values[i-24]
    assert df_feats["lag_24"].iloc[30] == values[6]

    # Check lag_168 at index i is exactly values[i-168]
    assert df_feats["lag_168"].iloc[170] == values[2]

    # Check rolling_mean_24 at index i does NOT include values[i] (current target)
    expected_rolling = np.mean(values[10:34])
    actual_rolling = df_feats["rolling_mean_24"].iloc[34]
    assert pytest.approx(actual_rolling, 0.0001) == expected_rolling


def test_extract_features_and_target():
    n_hours = 200
    timestamps = pd.date_range("2023-01-01 00:00:00", periods=n_hours, freq="h")
    df = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: np.ones(n_hours) * 150000.0})
    df_feats = create_features(df, drop_na=True)

    X, y = extract_features_and_target(df_feats)
    assert len(X) == len(y)
    assert list(X.columns) == get_feature_column_names()
    assert TARGET_COL not in X.columns
