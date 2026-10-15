"""Unit tests for recursive multi-step forecasting engine."""

import pytest
import pandas as pd
import numpy as np

from src.energy_forecasting.config import (
    TIME_COL,
    TARGET_COL,
    TARGET_UNIT,
    FORECAST_HORIZON_HOURS,
)
from src.energy_forecasting.models import SeasonalNaiveModel
from src.energy_forecasting.forecasting import (
    generate_24h_forecast,
    validate_forecast_output,
)


@pytest.fixture
def synthetic_history():
    timestamps = pd.date_range("2023-01-01 00:00:00", periods=200, freq="h")
    values = np.sin(np.linspace(0, 20, 200)) * 10000 + 150000.0
    return pd.DataFrame({TIME_COL: timestamps, TARGET_COL: values})


def test_generate_24h_forecast_length_and_properties(synthetic_history):
    model = SeasonalNaiveModel(seasonal_period=24)
    origin = synthetic_history[TIME_COL].max()

    forecast_df = generate_24h_forecast(
        history_df=synthetic_history,
        model=model,
        origin_timestamp=origin,
        horizon_hours=24,
    )

    assert len(forecast_df) == 24
    assert forecast_df[TIME_COL].iloc[0] == origin + pd.Timedelta(hours=1)
    assert forecast_df[TIME_COL].iloc[-1] == origin + pd.Timedelta(hours=24)
    assert (forecast_df[TARGET_COL] >= 0.0).all()
    assert not forecast_df[TARGET_COL].isna().any()
    assert (forecast_df["forecast_origin"] == origin).all()
    assert (forecast_df["unit"] == TARGET_UNIT).all()


def test_generate_24h_forecast_insufficient_history():
    timestamps = pd.date_range("2023-01-01 00:00:00", periods=50, freq="h")
    df = pd.DataFrame({TIME_COL: timestamps, TARGET_COL: np.ones(50) * 150000.0})
    model = SeasonalNaiveModel(seasonal_period=24)

    with pytest.raises(ValueError, match="requires at least 168 hours"):
        generate_24h_forecast(history_df=df, model=model)


def test_validate_forecast_output_success():
    origin = pd.Timestamp("2023-01-01 00:00:00")
    timestamps = pd.date_range(origin + pd.Timedelta(hours=1), periods=24, freq="h")
    df = pd.DataFrame(
        {
            TIME_COL: timestamps,
            TARGET_COL: np.ones(24) * 160000.0,
            "forecast_origin": origin,
        }
    )
    assert validate_forecast_output(df, expected_origin=origin, expected_horizon=24) is True
