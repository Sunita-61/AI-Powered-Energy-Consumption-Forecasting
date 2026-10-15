"""Recursive 24-hour multi-step forecasting engine for Indian Grid demand."""

from typing import Any, Optional, Dict
from datetime import datetime
import logging
import numpy as np
import pandas as pd

from src.energy_forecasting.config import (
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
    FORECAST_HORIZON_HOURS,
    FEATURE_COLUMNS,
    PROCESSED_INDIA_DATA_FILE,
    LIVE_HOURLY_LOG_FILE,
)

logger = logging.getLogger(__name__)


def generate_24h_forecast(
    history_df: pd.DataFrame,
    model: Any,
    origin_timestamp: Optional[pd.Timestamp] = None,
    horizon_hours: int = FORECAST_HORIZON_HOURS,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
    model_name: Optional[str] = None,
) -> pd.DataFrame:
    """Generates an autoregressive recursive 24-hour multi-step forecast for Indian Grid demand.

    Inputs:
    - history_df: Hourly demand readings in MW. Must contain at least 168 hours of continuous history.
    - model: Fitted estimator exposing predict(X).
    - origin_timestamp: Optional cutoff point T. If None, uses max timestamp from history_df.

    Returns:
        pd.DataFrame containing exactly horizon_hours predictions in MW with metadata.
    """
    if history_df.empty:
        raise ValueError("Cannot forecast from empty historical DataFrame.")

    df = history_df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(by=time_col).reset_index(drop=True)

    if origin_timestamp is None:
        origin_timestamp = df[time_col].max()
    else:
        origin_timestamp = pd.to_datetime(origin_timestamp)

    # Filter history up to origin_timestamp
    history_window = df[df[time_col] <= origin_timestamp].copy()
    if len(history_window) < 168:
        raise ValueError(
            f"Forecasting engine requires at least 168 hours of history up to cutoff, but got {len(history_window)}."
        )

    # Map timestamp -> demand value
    energy_map: Dict[pd.Timestamp, float] = dict(
        zip(history_window[time_col], history_window[target_col].astype(float))
    )

    forecast_records = []
    inferred_model_name = model_name or getattr(model, "model_name", type(model).__name__)

    for h in range(1, horizon_hours + 1):
        target_ts = origin_timestamp + pd.Timedelta(hours=h)

        # 1. Calendar Features
        hour_of_day = target_ts.hour
        day_of_week = target_ts.dayofweek
        is_weekend = 1 if day_of_week >= 5 else 0
        month = target_ts.month

        # 2. Lag Features
        ts_lag1 = target_ts - pd.Timedelta(hours=1)
        ts_lag24 = target_ts - pd.Timedelta(hours=24)
        ts_lag168 = target_ts - pd.Timedelta(hours=168)

        if ts_lag1 not in energy_map:
            raise KeyError(f"Missing lag 1 timestamp: {ts_lag1}")
        if ts_lag24 not in energy_map:
            raise KeyError(f"Missing lag 24 timestamp: {ts_lag24}")
        if ts_lag168 not in energy_map:
            raise KeyError(f"Missing lag 168 timestamp: {ts_lag168}")

        lag_1 = energy_map[ts_lag1]
        lag_24 = energy_map[ts_lag24]
        lag_168 = energy_map[ts_lag168]

        # 3. Rolling Mean 24 (Preceding 24 hours up to target_ts - 1 hour)
        rolling_timestamps = [target_ts - pd.Timedelta(hours=i) for i in range(1, 25)]
        rolling_vals = [energy_map[ts] for ts in rolling_timestamps]
        rolling_mean_24 = float(np.mean(rolling_vals))

        # Assemble single-row DataFrame matching FEATURE_COLUMNS exactly
        row_dict = {
            "hour_of_day": [hour_of_day],
            "day_of_week": [day_of_week],
            "is_weekend": [is_weekend],
            "month": [month],
            "lag_1": [lag_1],
            "lag_24": [lag_24],
            "lag_168": [lag_168],
            "rolling_mean_24": [rolling_mean_24],
        }
        X_step = pd.DataFrame(row_dict)[FEATURE_COLUMNS]

        # 4. Predict
        raw_pred = float(model.predict(X_step)[0])
        predicted_mw = max(0.0, raw_pred)

        # Store in map for subsequent autoregressive recursive steps
        energy_map[target_ts] = predicted_mw

        forecast_records.append(
            {
                time_col: target_ts,
                "forecast_origin": origin_timestamp,
                target_col: round(predicted_mw, 2),
                "model_name": inferred_model_name,
                "unit": TARGET_UNIT,
                "horizon_step": h,
            }
        )

    forecast_df = pd.DataFrame(forecast_records)
    validate_forecast_output(
        forecast_df,
        expected_origin=origin_timestamp,
        expected_horizon=horizon_hours,
        target_col=target_col,
        time_col=time_col,
    )
    return forecast_df


def validate_forecast_output(
    forecast_df: pd.DataFrame,
    expected_origin: pd.Timestamp,
    expected_horizon: int = FORECAST_HORIZON_HOURS,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
) -> bool:
    """Enforces correctness criteria and physical output validity on the generated forecast."""
    if len(forecast_df) != expected_horizon:
        raise ValueError(
            f"Forecast length mismatch: expected {expected_horizon} rows, got {len(forecast_df)}."
        )

    # Check timestamps are strictly in the future relative to origin
    min_ts = forecast_df[time_col].min()
    if min_ts <= expected_origin:
        raise ValueError(
            f"Earliest forecast timestamp ({min_ts}) must be after origin ({expected_origin})."
        )

    # Check timestamp monotonicity and 1-hour spacing
    expected_timestamps = pd.date_range(
        start=expected_origin + pd.Timedelta(hours=1),
        periods=expected_horizon,
        freq="h",
    )
    if not (forecast_df[time_col].values == expected_timestamps.values).all():
        raise ValueError("Forecast timestamps do not form a continuous, 1-hour spaced series.")

    # Check for NaN, Inf, or negative values
    if forecast_df[target_col].isna().any():
        raise ValueError("Forecast contains NaN values.")
    if np.isinf(forecast_df[target_col]).any():
        raise ValueError("Forecast contains Infinite values.")
    if (forecast_df[target_col] < 0).any():
        raise ValueError("Forecast contains physically invalid negative demand values.")

    return True


def generate_realtime_grid_forecast(
    model: Any,
    live_reading: Any = None,
    history_df: Optional[pd.DataFrame] = None,
    horizon_hours: int = FORECAST_HORIZON_HOURS,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
    model_name: Optional[str] = None,
):
    """Generates next-24-hour real-time grid demand forecast anchored to latest live telemetry.

    Constructs the preceding national diurnal baseline history, anchors the current hour to the
    real-time live observation (in MW), dynamically scales through the trained model, and outputs
    both the recent live trajectory and the next 24-hour predictions.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (recent_history_df, forecast_df)
    """
    if live_reading is None:
        from src.energy_forecasting.live_connector import fetch_live_grid_demand
        live_reading = fetch_live_grid_demand()

    live_demand = float(getattr(live_reading, "demand_met_mw", 240000.0))
    obs_raw = getattr(live_reading, "observation_time_utc", "2026-10-15T08:00:00+00:00")
    obs_ts = pd.to_datetime(obs_raw)
    if obs_ts.tzinfo is not None:
        obs_ts = obs_ts.tz_convert(None)
    origin_ts = obs_ts.floor("h")

    # Load historical reference for profile and base mean
    if history_df is None or history_df.empty:
        if PROCESSED_INDIA_DATA_FILE.exists():
            history_df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
            history_df[time_col] = pd.to_datetime(history_df[time_col])
        else:
            from src.energy_forecasting.data_loader import generate_synthetic_india_demand_data
            history_df = generate_synthetic_india_demand_data()

    hist_mean = float(history_df[target_col].mean())
    hourly_means = history_df.groupby(pd.to_datetime(history_df[time_col]).dt.hour)[target_col].mean()
    norm_profile = hourly_means / hourly_means.mean()

    cur_factor = float(norm_profile.get(origin_ts.hour, 1.0))
    base_demand = live_demand / max(cur_factor, 0.1)

    # Build 169 hours of baseline history leading up to origin_ts
    ts_range = pd.date_range(end=origin_ts, periods=169, freq="h")
    sim_hist = []
    for t in ts_range:
        h = t.hour
        dow = t.dayofweek
        dow_factor = 0.96 if dow >= 5 else 1.01
        val = base_demand * float(norm_profile.get(h, 1.0)) * dow_factor
        sim_hist.append({time_col: t, target_col: round(val, 2)})

    sim_df = pd.DataFrame(sim_hist)
    # Anchor the exact origin observation to the live telemetry reading
    sim_df.iloc[-1, sim_df.columns.get_loc(target_col)] = live_demand

    # Merge logged live readings if present
    if LIVE_HOURLY_LOG_FILE.exists():
        try:
            live_log = pd.read_csv(LIVE_HOURLY_LOG_FILE)
            if not live_log.empty and "observation_time_utc" in live_log.columns:
                live_log["ts"] = pd.to_datetime(live_log["observation_time_utc"]).dt.floor("h")
                if live_log["ts"].dt.tz is not None:
                    live_log["ts"] = live_log["ts"].dt.tz_convert(None)
                val_map = dict(zip(live_log["ts"], live_log["demand_mw"].astype(float)))
                for idx, row in sim_df.iterrows():
                    if row[time_col] in val_map:
                        sim_df.at[idx, target_col] = val_map[row[time_col]]
        except Exception as e:
            logger.warning(f"Could not merge live log file: {e}")

    # Scale input by national load growth ratio
    scale_factor = live_demand / max(hist_mean, 1.0)
    sim_df_scaled = sim_df.copy()
    sim_df_scaled[target_col] = sim_df_scaled[target_col] / scale_factor

    fc_scaled = generate_24h_forecast(
        history_df=sim_df_scaled,
        model=model,
        origin_timestamp=origin_ts,
        horizon_hours=horizon_hours,
        target_col=target_col,
        time_col=time_col,
        model_name=model_name,
    )

    forecast_df = fc_scaled.copy()
    forecast_df[target_col] = np.round(forecast_df[target_col] * scale_factor, 2)
    # Also ensure bounds
    forecast_df[target_col] = forecast_df[target_col].clip(50000.0, 400000.0)

    recent_history = sim_df.tail(48).reset_index(drop=True)
    return recent_history, forecast_df

