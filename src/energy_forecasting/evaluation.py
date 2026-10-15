"""Model evaluation metrics: MAE, RMSE, and WAPE with robust edge-case handling."""

from typing import Dict, Any, Union
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_mae(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list],
) -> float:
    """Calculates Mean Absolute Error (MAE).

    MAE = (1 / N) * sum(|y_true - y_pred|)
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: y_true ({len(yt)}) vs y_pred ({len(yp)}).")
    if len(yt) == 0:
        return 0.0

    return float(np.mean(np.abs(yt - yp)))


def calculate_rmse(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list],
) -> float:
    """Calculates Root Mean Squared Error (RMSE).

    RMSE = sqrt((1 / N) * sum((y_true - y_pred)^2))
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: y_true ({len(yt)}) vs y_pred ({len(yp)}).")
    if len(yt) == 0:
        return 0.0

    return float(np.sqrt(np.mean((yt - yp) ** 2)))


def calculate_wape(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list],
) -> float:
    """Calculates Weighted Absolute Percentage Error (WAPE).

    WAPE = (sum(|y_true - y_pred|) / sum(|y_true|)) * 100%

    Safe handling:
    If sum(|y_true|) is zero, returns 0.0 if sum(|y_true - y_pred|) == 0,
    otherwise returns NaN with a logged warning.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: y_true ({len(yt)}) vs y_pred ({len(yp)}).")
    if len(yt) == 0:
        return 0.0

    total_actual = float(np.sum(np.abs(yt)))
    total_abs_error = float(np.sum(np.abs(yt - yp)))

    if total_actual == 0.0:
        if total_abs_error == 0.0:
            return 0.0
        logger.warning("Total actual sum is zero with non-zero error; WAPE is undefined.")
        return float(np.nan)

    wape_percentage = (total_abs_error / total_actual) * 100.0
    return float(wape_percentage)


def evaluate_predictions(
    y_true: Union[np.ndarray, pd.Series, list],
    y_pred: Union[np.ndarray, pd.Series, list],
    round_digits: int = 4,
) -> Dict[str, float]:
    """Computes MAE, RMSE, and WAPE in a unified dictionary."""
    mae = calculate_mae(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)
    wape = calculate_wape(y_true, y_pred)

    return {
        "MAE": round(mae, round_digits),
        "RMSE": round(rmse, round_digits),
        "WAPE": round(wape, round_digits),
    }
