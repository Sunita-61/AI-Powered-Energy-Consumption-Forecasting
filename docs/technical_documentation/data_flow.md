# Data Flow Architecture: India Grid Demand Forecasting

## 1. End-to-End Information Pipeline

The data architecture operates across two synchronized lifecycles: **Batch ML Training Pipeline** and **Real-Time Live Telemetry / Inference Pipeline**.

```
[Mendeley Data Repository]              [Live Data Aggregator API]
(5-min SCADA Excel Workbooks)          (Candidate: India-Energy-Data)
           │                                          │
           ▼                                          ▼
   data_loader.py                              live_connector.py
(NLDC_DEMAND|P extraction)               (HTTP 10s timeout, retries)
           │                                          │
           ▼                                          ▼
   preprocessing.py                      Freshness Engine & Cache Check
(Resample 5m -> 1h Mean MW,              (FRESH / STALE / CACHED / UNAVAILABLE)
 missing imputation, bounds)                          │
           │                                          ▼
           ▼                             data/cache/last_valid_live_reading.json
      features.py                                     │
(Calendar + Shifted Lags)                             │
           │                                          │
           ▼                                          │
      training.py                                     │
(Chronological 70/15/15 split,                        │
 Train SN, LR, RF -> select best)                     │
           │                                          │
           ▼                                          ▼
    forecasting.py <──────────────────────────────────┘
(24-Hour Recursive Autoregressive Engine)
           │
           ├──────────────────────────────┐
           ▼                              ▼
    FastAPI Endpoints             Streamlit UI
    http://localhost:8501/api/*   http://localhost:8501/
```

---

## 2. Ingestion & Transformation Lifecycle

### Stage 1: Mendeley Historical Ingestion (`data_loader.py`)
1. Download monthly Excel files from Mendeley Data API (`September 2021.xlsx`, etc.).
2. Extract the National Load Despatch Centre SCADA column `NLDC_DEMAND|P` at index 10.
3. Parse timestamps and cast readings to float Megawatts (`MW`).
4. Average 5-minute readings into 1-hour intervals via `.resample('1h').mean()`.
5. Persist canonical hourly series to `data/processed/india_hourly_demand.csv`.

### Stage 2: Quality Assurance & Preprocessing (`preprocessing.py`)
1. Check monotonic chronology and resolve duplicate timestamps.
2. Construct full hourly grid index and interpolate short telemetry dropouts (<3 hours) using time-weighted interpolation.
3. Clamp non-physical outliers ($50,000 \le \text{demand\_mw} \le 400,000$).
4. Generate comprehensive data quality report (`data_quality_report.json`).

### Stage 3: Feature Engineering (`features.py`)
1. Extract temporal cyclical indicators: `hour_of_day` (0–23), `day_of_week` (0–6), `is_weekend` (0/1), `month` (1–12).
2. Compute autoregressive lagged demand:
   - `lag_1`: Demand at $t-1$ hour.
   - `lag_24`: Demand at $t-24$ hours (same hour previous day).
   - `lag_168`: Demand at $t-168$ hours (same hour previous week).
3. Compute rolling window statistic:
   - `rolling_mean_24`: Mean of previous 24 hours computed as `.shift(1).rolling(24).mean()` strictly preventing current-hour target leakage.
4. Drop rows with `NaN` due to historical lookback (first 168 hours).

### Stage 4: Training & Model Selection (`training.py`)
1. Split dataset chronologically:
   - **Training Set (70%)**: First 70% of chronological timeline.
   - **Validation Set (15%)**: Next 15% used for model tuning and selection.
   - **Test Set (15%)**: Final 15% held out exclusively for final unbiased reporting.
2. Fit candidate models: Seasonal-Naive baseline, Linear Regression, and Random Forest Regressor.
3. Evaluate validation MAE, RMSE, and WAPE.
4. Save best performing model artifact to `models/best_model.joblib` and metrics to `outputs/metrics/evaluation_metrics.json`.

### Stage 5: Live Telemetry & 24-Hour Forecasting (`live_connector.py`, `forecasting.py`)
1. Query `https://india-energy-data.vercel.app/api/v1/zone/IN/live`.
2. Extract `demand_met` in MW and observation timestamp.
3. Compute data age relative to current UTC clock.
4. If upstream is unreachable, fall back to cached reading in `data/cache/last_valid_live_reading.json` and flag as `CACHED`. If no cache, report `UNAVAILABLE`.
5. Roll forward 24 hourly steps recursively using the trained model, appending forecast values to input lags dynamically.
6. Persist forecasts to `outputs/forecasts/forecast_24h.csv` and serve via `/api/forecast` and Streamlit.
