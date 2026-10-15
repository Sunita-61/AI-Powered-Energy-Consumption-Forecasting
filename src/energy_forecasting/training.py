"""Model training pipeline: chronological partitioning, multi-model benchmarking, and model selection."""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import logging
import numpy as np
import pandas as pd

from src.energy_forecasting.config import (
    TRAIN_RATIO,
    VAL_RATIO,
    TEST_RATIO,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
    RANDOM_SEED,
)
from src.energy_forecasting.features import create_features, extract_features_and_target
from src.energy_forecasting.evaluation import evaluate_predictions
from src.energy_forecasting.models import (
    SeasonalNaiveModel,
    LinearRegressionWrapper,
    RandomForestWrapper,
    save_model,
)

logger = logging.getLogger(__name__)


def chronological_train_val_test_split(
    df: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partitions time-series data chronologically into Train, Validation, and Test sets.

    STRICT TIME-SERIES REQUIREMENT:
    Data rows are ordered by timestamp and never randomly shuffled.
    - Train (70%): Used for model parameter learning.
    - Validation (15%): Used for model comparison & hyperparameter tuning.
    - Test (15%): Held-out strictly for final unbiased evaluation.
    """
    if not (0.0 < train_ratio < 1.0):
        raise ValueError(f"train_ratio must be between 0 and 1, got {train_ratio}.")
    if not (0.0 < val_ratio < 1.0):
        raise ValueError(f"val_ratio must be between 0 and 1, got {val_ratio}.")
    if train_ratio + val_ratio >= 1.0:
        raise ValueError(
            f"train_ratio + val_ratio must be < 1.0 to leave room for test set."
        )

    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_df = df.iloc[:train_end].copy().reset_index(drop=True)
    val_df = df.iloc[train_end:val_end].copy().reset_index(drop=True)
    test_df = df.iloc[val_end:].copy().reset_index(drop=True)

    logger.info(
        f"Chronological split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}"
    )
    return train_df, val_df, test_df


def train_and_benchmark(
    hourly_df: pd.DataFrame,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
) -> Tuple[Dict[str, Any], Any, Dict[str, Any]]:
    """Generates features, partitions chronologically, trains candidates, and benchmarks models.

    Models evaluated:
    - Model A: Seasonal-Naive baseline (predicts lag_24)
    - Model B: Linear Regression
    - Model C: Random Forest Regressor

    Returns:
        Tuple of (all_metrics_dict, best_fitted_model, selection_metadata).
    """
    logger.info("Generating anti-leakage features for model training...")
    df_features = create_features(hourly_df, target_col=target_col, time_col=time_col, drop_na=True)

    train_df, val_df, test_df = chronological_train_val_test_split(df_features)

    X_train, y_train = extract_features_and_target(train_df, target_col=target_col)
    X_val, y_val = extract_features_and_target(val_df, target_col=target_col)
    X_test, y_test = extract_features_and_target(test_df, target_col=target_col)

    candidates = {
        "SeasonalNaiveBaseline": SeasonalNaiveModel(seasonal_period=24),
        "LinearRegression": LinearRegressionWrapper(),
        "RandomForestRegressor": RandomForestWrapper(
            n_estimators=100, max_depth=12, random_state=RANDOM_SEED
        ),
    }

    benchmark_results: Dict[str, Any] = {
        "target_variable": target_col,
        "target_unit": TARGET_UNIT,
        "split_summary": {
            "total_samples": len(df_features),
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "train_range": [str(train_df[time_col].min()), str(train_df[time_col].max())],
            "val_range": [str(val_df[time_col].min()), str(val_df[time_col].max())],
            "test_range": [str(test_df[time_col].min()), str(test_df[time_col].max())],
        },
        "validation_metrics": {},
        "test_metrics": {},
    }

    best_model_name: Optional[str] = None
    lowest_val_mae = float("inf")
    fitted_models: Dict[str, Any] = {}

    for name, model in candidates.items():
        logger.info(f"Fitting candidate model: {name}...")
        model.fit(X_train, y_train)
        fitted_models[name] = model

        val_preds = model.predict(X_val)
        val_metrics = evaluate_predictions(y_val, val_preds)
        benchmark_results["validation_metrics"][name] = val_metrics
        logger.info(f"{name} Validation Metrics: {val_metrics}")

        if val_metrics["MAE"] < lowest_val_mae:
            lowest_val_mae = val_metrics["MAE"]
            best_model_name = name

    logger.info(f"Selected Best Model based on Validation MAE: {best_model_name}")

    best_model = fitted_models[best_model_name]
    # Final unbiased evaluation on held-out test set
    test_preds = best_model.predict(X_test)
    test_metrics = evaluate_predictions(y_test, test_preds)
    benchmark_results["test_metrics"][best_model_name] = test_metrics
    logger.info(f"{best_model_name} Test Metrics: {test_metrics}")

    metadata = {
        "best_model_name": best_model_name,
        "selected_criterion": "Lowest Validation MAE",
        "validation_mae": lowest_val_mae,
        "test_metrics": test_metrics,
        "feature_names": list(X_train.columns),
        "target_col": target_col,
        "target_unit": TARGET_UNIT,
        "training_timestamp": datetime.now().isoformat(),
        "is_synthetic": hourly_df.attrs.get("is_synthetic", False),
    }

    return benchmark_results, best_model, metadata
