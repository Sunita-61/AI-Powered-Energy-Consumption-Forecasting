"""Unit tests for evaluation metrics (MAE, RMSE, WAPE)."""

import pytest
import numpy as np

from src.energy_forecasting.evaluation import (
    calculate_mae,
    calculate_rmse,
    calculate_wape,
    evaluate_predictions,
)


def test_calculate_mae_hand_calculated():
    y_true = [10.0, 20.0, 30.0]
    y_pred = [12.0, 18.0, 33.0]
    # Abs errors: 2.0, 2.0, 3.0 -> Mean = 7.0 / 3 = 2.3333...
    assert pytest.approx(calculate_mae(y_true, y_pred), 0.0001) == 2.3333333333333335


def test_calculate_rmse_hand_calculated():
    y_true = [10.0, 20.0]
    y_pred = [13.0, 16.0]
    # Squared errors: 9.0, 16.0 -> Mean = 12.5 -> Sqrt = 3.5355339...
    assert pytest.approx(calculate_rmse(y_true, y_pred), 0.0001) == np.sqrt(12.5)


def test_calculate_wape_hand_calculated():
    y_true = [100.0, 200.0]
    y_pred = [110.0, 180.0]
    # Abs errors: 10 + 20 = 30. Total actual = 300. WAPE = (30/300)*100 = 10.0%
    assert pytest.approx(calculate_wape(y_true, y_pred), 0.0001) == 10.0


def test_calculate_wape_zero_division_safety():
    # If both true and pred are zero
    assert calculate_wape([0.0, 0.0], [0.0, 0.0]) == 0.0

    # If true is zero but pred is non-zero, should return NaN
    assert np.isnan(calculate_wape([0.0, 0.0], [5.0, 5.0]))


def test_evaluate_predictions_dictionary():
    metrics = evaluate_predictions([10.0, 20.0], [10.0, 20.0])
    assert metrics["MAE"] == 0.0
    assert metrics["RMSE"] == 0.0
    assert metrics["WAPE"] == 0.0
