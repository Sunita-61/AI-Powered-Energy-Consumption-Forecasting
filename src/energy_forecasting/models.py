"""Forecasting model wrappers: Seasonal-Naive baseline, Linear Regression, and Random Forest."""

from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

from src.energy_forecasting.config import RANDOM_SEED, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class SeasonalNaiveModel:
    """Deterministic seasonal-naive benchmark forecaster.

    Predicts the consumption observed at the same hour on the previous day (lag 24).
    Has 0 trainable parameters and provides an essential performance benchmark.
    """

    def __init__(self, seasonal_period: int = 24):
        self.seasonal_period = seasonal_period
        self.model_name = "SeasonalNaiveBaseline"
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "SeasonalNaiveModel":
        """Fits the seasonal naive model (validates availability of lag_24)."""
        lag_col = f"lag_{self.seasonal_period}"
        if lag_col not in X.columns:
            raise ValueError(f"Seasonal naive baseline requires column '{lag_col}' in X.")
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts energy consumption using lag 24 values."""
        lag_col = f"lag_{self.seasonal_period}"
        if lag_col not in X.columns:
            raise ValueError(f"Seasonal naive baseline requires column '{lag_col}' in X.")
        preds = X[lag_col].values.astype(float)
        # Clip negative values
        return np.clip(preds, a_min=0.0, a_max=None)


class LinearRegressionWrapper:
    """Interpretable linear regression model wrapper."""

    def __init__(self, **kwargs):
        self.model_name = "LinearRegression"
        self.estimator = LinearRegression(**kwargs)
        self.feature_names: List[str] = []
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LinearRegressionWrapper":
        self.feature_names = list(X.columns)
        self.estimator.fit(X[self.feature_names], y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")
        preds = self.estimator.predict(X[self.feature_names])
        return np.clip(preds, a_min=0.0, a_max=None)


class RandomForestWrapper:
    """Non-linear ensemble Random Forest Regressor wrapper."""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = 12,
        random_state: int = RANDOM_SEED,
        n_jobs: int = -1,
        **kwargs,
    ):
        self.model_name = "RandomForestRegressor"
        self.estimator = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=n_jobs,
            **kwargs,
        )
        self.feature_names: List[str] = []
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RandomForestWrapper":
        self.feature_names = list(X.columns)
        self.estimator.fit(X[self.feature_names], y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict() is called.")
        preds = self.estimator.predict(X[self.feature_names])
        return np.clip(preds, a_min=0.0, a_max=None)


def save_model(model: Any, file_path: Union[Path, str], metadata: Dict[str, Any]) -> None:
    """Serializes a fitted model and its configuration metadata to disk via joblib."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model,
        "metadata": metadata,
    }
    joblib.dump(payload, path)
    logger.info(f"Model serialized successfully to {path}")


def load_model(file_path: Union[Path, str]) -> Tuple[Any, Dict[str, Any]]:
    """Loads a serialized model and its metadata dictionary from disk."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"No serialized model found at {path}")
    payload = joblib.load(path)
    if isinstance(payload, dict) and "model" in payload and "metadata" in payload:
        return payload["model"], payload["metadata"]
    return payload, {}
