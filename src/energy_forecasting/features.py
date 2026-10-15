"""Feature engineering for Indian Grid demand with strict anti-leakage guarantees."""

from typing import List, Tuple
import logging
import numpy as np
import pandas as pd

from src.energy_forecasting.config import (
    TARGET_COL,
    TIME_COL,
    FEATURE_COLUMNS,
    LAG_HOURS,
    ROLLING_WINDOW_HOURS,
)

logger = logging.getLogger(__name__)


def create_features(
    df: pd.DataFrame,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
    drop_na: bool = False,
) -> pd.DataFrame:
    """Derives temporal and historical lag features for Indian electricity demand.

    Features generated:
    - hour_of_day: 0 to 23
    - day_of_week: 0 (Monday) to 6 (Sunday)
    - is_weekend: 1 for Saturday/Sunday, 0 otherwise
    - month: 1 to 12 (captures monsoon, summer, winter seasonality)
    - lag_1: demand shifted by 1 hour (t - 1)
    - lag_24: demand shifted by 24 hours (t - 24)
    - lag_168: demand shifted by 168 hours (t - 168, 1 week prior)
    - rolling_mean_24: moving average of the preceding 24 hours (strictly excluding target at t)

    CRITICAL LEAKAGE PREVENTION:
    `rolling_mean_24` is computed as: `df[target_col].shift(1).rolling(24).mean()`.
    This guarantees that the target value at timestamp `t` is never included in the rolling window.
    """
    if df.empty:
        raise ValueError("Cannot engineer features from an empty DataFrame.")

    if time_col not in df.columns:
        raise ValueError(f"Timestamp column '{time_col}' not found.")

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found.")

    work_df = df.copy()
    work_df[time_col] = pd.to_datetime(work_df[time_col])

    # 1. Calendar / Seasonal Features
    work_df["hour_of_day"] = work_df[time_col].dt.hour
    work_df["day_of_week"] = work_df[time_col].dt.dayofweek
    work_df["is_weekend"] = (work_df[time_col].dt.dayofweek >= 5).astype(int)
    work_df["month"] = work_df[time_col].dt.month

    # 2. Historical Auto-regressive Lag Features
    for lag in LAG_HOURS:
        work_df[f"lag_{lag}"] = work_df[target_col].shift(lag)

    # 3. Rolling Statistics (Shifted by 1 to prevent current observation leakage)
    work_df[f"rolling_mean_{ROLLING_WINDOW_HOURS}"] = (
        work_df[target_col].shift(1).rolling(window=ROLLING_WINDOW_HOURS).mean()
    )

    if drop_na:
        work_df = work_df.dropna().reset_index(drop=True)

    return work_df


def get_feature_column_names() -> List[str]:
    """Returns the standardized, ordered list of input feature names."""
    return list(FEATURE_COLUMNS)


def extract_features_and_target(
    df_with_features: pd.DataFrame,
    target_col: str = TARGET_COL,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Splits a feature-engineered DataFrame into X (feature matrix) and y (target vector)."""
    feature_cols = get_feature_column_names()
    missing_cols = [c for c in feature_cols if c not in df_with_features.columns]
    if missing_cols:
        raise ValueError(f"DataFrame is missing required feature columns: {missing_cols}")

    X = df_with_features[feature_cols].copy()
    y = df_with_features[target_col].copy()
    return X, y
