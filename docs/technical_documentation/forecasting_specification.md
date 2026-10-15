# Forecasting Specification: 24-Hour Horizon

## 1. Forecast Horizon & Objective
The operational objective of the forecasting engine is to predict All-India national electricity grid demand ($y_{t+1}, y_{t+2}, \dots, y_{t+24}$) for the next 24 chronological hours in Megawatts (MW).

---

## 2. Multi-Step Recursive Forecasting Architecture

Because future ground truth values ($y_{t+1}, \dots, y_{t+23}$) are not available at forecast origin $t$, predictions are generated autoregressively:

```
Origin Time t (Known History)
     │
     ├──> Step 1: Predict y_hat_{t+1} using known lags [y_t, y_{t-23}, y_{t-167}]
     │            Append y_hat_{t+1} to buffer
     │
     ├──> Step 2: Predict y_hat_{t+2} using [y_hat_{t+1}, y_{t-22}, y_{t-166}]
     │            Append y_hat_{t+2} to buffer
     │
     ...
     │
     └──> Step 24: Predict y_hat_{t+24} using [y_hat_{t+23}, y_hat_t, y_{t-144}]
```

### Dynamic Feature Recalculation per Step
For each step $k \in [1, 24]$:
1. Target timestamp $t_k = t + k \times \text{1 hour}$ is determined.
2. Calendar attributes are extracted: `hour_of_day`, `day_of_week`, `is_weekend`, `month`.
3. Lags are sampled dynamically from the appended buffer:
   - `lag_1 = buffer[-1]`
   - `lag_24 = buffer[-24]`
   - `lag_168 = buffer[-168]`
4. Rolling mean is updated:
   - `rolling_mean_24 = np.mean(buffer[-24:])`
5. Model inference predicts $\hat{y}_{t_k}$.
6. Physical sanity check: $\hat{y}_{t_k} = \text{clip}(\hat{y}_{t_k}, 50000.0, 400000.0)$.
7. $\hat{y}_{t_k}$ is appended to the buffer for subsequent steps.

---

## 3. Output Forecast Schema & Storage

Forecast outputs are serialized in both tabular CSV (`outputs/forecasts/forecast_24h.csv`) and REST-compatible JSON (`outputs/forecasts/forecast_24h.json`).

| Field | Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `ISO 8601 string` | Target forecast hour in UTC |
| `forecast_demand_mw` | `float` | Predicted national demand in Megawatts (MW) |
| `horizon_step` | `int` | Horizon step index ($1 \dots 24$) |
| `model_name` | `string` | Model identifier (`RandomForestRegressor`) |
| `origin_timestamp` | `ISO 8601 string` | Timestamp of the last available historical observation |
| `forecast_generated_at` | `ISO 8601 string` | System clock UTC when the forecast was executed |

---

## 4. Actual vs. Predicted Monitoring Strategy
When real telemetry observations become available in subsequent hours (via the hourly live data connector), the system compares $\hat{y}_t$ against verified $y_t$:
- Computes hourly absolute error $|\hat{y}_t - y_t|$ and percentage error $\frac{|\hat{y}_t - y_t|}{y_t} \times 100\%$.
- Renders tracking curves on the Streamlit dashboard to audit real-time forecast degradation.
