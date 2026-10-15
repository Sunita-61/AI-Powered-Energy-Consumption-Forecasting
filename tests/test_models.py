"""Unit tests for models and serialization."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.energy_forecasting.models import (
    SeasonalNaiveModel,
    LinearRegressionWrapper,
    RandomForestWrapper,
    save_model,
    load_model,
)


@pytest.fixture
def dummy_train_data():
    X = pd.DataFrame(
        {
            "hour_of_day": [0, 1, 2, 3],
            "day_of_week": [0, 0, 0, 0],
            "is_weekend": [0, 0, 0, 0],
            "month": [9, 9, 9, 9],
            "lag_1": [150000.0, 151000.0, 152000.0, 153000.0],
            "lag_24": [150500.0, 151500.0, 152500.0, 153500.0],
            "lag_168": [149000.0, 150000.0, 151000.0, 152000.0],
            "rolling_mean_24": [151000.0, 151000.0, 151000.0, 151000.0],
        }
    )
    y = pd.Series([151000.0, 152000.0, 153000.0, 154000.0])
    return X, y


def test_seasonal_naive_model(dummy_train_data):
    X, y = dummy_train_data
    model = SeasonalNaiveModel(seasonal_period=24)
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == len(X)
    np.testing.assert_array_equal(preds, X["lag_24"].values)


def test_linear_regression_wrapper(dummy_train_data):
    X, y = dummy_train_data
    model = LinearRegressionWrapper()
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == len(X)
    assert (preds >= 0).all()


def test_random_forest_wrapper(dummy_train_data):
    X, y = dummy_train_data
    model = RandomForestWrapper(n_estimators=10, max_depth=3, random_state=42)
    model.fit(X, y)
    preds = model.predict(X)
    assert len(preds) == len(X)
    assert (preds >= 0).all()


def test_save_load_roundtrip(tmp_path, dummy_train_data):
    X, y = dummy_train_data
    model = LinearRegressionWrapper()
    model.fit(X, y)
    meta = {"test_metric": 42.0, "best_model_name": "LinearRegression"}

    save_path = tmp_path / "model.joblib"
    save_model(model, save_path, metadata=meta)

    loaded_model, loaded_meta = load_model(save_path)
    assert loaded_meta["test_metric"] == 42.0
    preds = loaded_model.predict(X)
    assert len(preds) == len(X)
