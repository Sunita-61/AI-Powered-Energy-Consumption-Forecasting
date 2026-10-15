# Module Specification: System Architecture & Responsibilities

## 1. Package Structure
All core algorithmic and data engineering logic resides inside `src/energy_forecasting/`, organized into single-responsibility modules:

```
src/energy_forecasting/
├── __init__.py           # Package namespace initialization
├── config.py             # Global constants, directory paths, grid parameters
├── data_loader.py        # Historical Mendeley Excel parsing & telemetry extraction
├── preprocessing.py      # Resampling, quality checks, missing imputation
├── features.py           # Temporal extraction & leakage-free autoregressive lags
├── models.py             # Model wrappers (Seasonal-Naive, Linear, Random Forest)
├── training.py           # Chronological splitting, training & selection harness
├── evaluation.py         # MAE, RMSE, WAPE metric calculations
├── forecasting.py        # 24-step recursive autoregressive generator
├── live_connector.py     # Resilient HTTP adapter for real-time India grid data
└── simulation.py         # Peak-shaving scenario generator
```

---

## 2. Module Interfaces & Responsibilities

### A. `config.py`
- **Constants**:
  - `TARGET_COL = "demand_mw"`
  - `TARGET_UNIT = "MW"`
  - `PORTS`: Reverse Proxy `8501`, Streamlit `8502`, FastAPI `8000`.
  - `MENDELEY_DATASET_ID = "y58jknpgs8"`
  - `LIVE_ENDPOINT_DEFAULT = "https://india-energy-data.vercel.app/api/v1/zone/IN/live"`
- **Path Resolution**: Sets absolute base paths for `data/raw/`, `data/processed/`, `data/cache/`, `models/`, and `outputs/`.

### B. `data_loader.py`
- `parse_mendeley_excel_sheet(file_path: Path) -> pd.DataFrame`:
  - Parses sheet, extracts column index 10 (`NLDC_DEMAND|P`), casts to numeric MW, and computes 1-hour resampled means.
- `load_all_mendeley_historical_data() -> pd.DataFrame`:
  - Iterates over available monthly workbooks and concatenates chronological records.
- `generate_synthetic_india_demand_data(...) -> pd.DataFrame`:
  - Generates realistic diurnal load series strictly tagged with `is_synthetic = True` for offline test resilience.

### C. `preprocessing.py`
- `preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]`:
  - Validates monotonic order, eliminates duplicates, imputes short gaps via time-interpolation, clamps extreme anomalies ($[50k, 400k]$ MW), and outputs structured data quality dictionary.

### D. `features.py`
- `create_features(df: pd.DataFrame) -> pd.DataFrame`:
  - Derives `hour_of_day`, `day_of_week`, `is_weekend`, `month`.
  - Computes `lag_1`, `lag_24`, `lag_168`, and leakage-free `rolling_mean_24 = df[TARGET_COL].shift(1).rolling(24).mean()`.
  - Drops initial 168 lookback `NaN` rows.

### E. `models.py`
- `SeasonalNaiveModel`: Implements `fit(X, y)` and `predict(X)` using 24-hour lagged demand.
- `LinearRegressionWrapper`: Scikit-learn OLS wrapper with serialization hooks.
- `RandomForestWrapper`: 100-tree non-linear ensemble with depth limitation.
- `save_model(model, filepath)`, `load_model(filepath)`.

### F. `training.py`
- `chronological_split(df, train_frac=0.70, val_frac=0.15)`: Sequential 70/15/15 partitioner.
- `train_and_evaluate_all_models(X_train, y_train, X_val, y_val)`: Trains all 3 models, evaluates on validation set, and selects model with lowest MAE.

### G. `evaluation.py`
- `calculate_metrics(y_true, y_pred) -> Dict[str, float]`: Computes MAE (MW), RMSE (MW), and WAPE (%) with zero-division guard.

### H. `forecasting.py`
- `generate_forecast_24h(model, df_history, feature_cols) -> pd.DataFrame`:
  - Executes 24-step recursive roll-forward prediction with dynamic buffer update and sanity clamping.

### I. `live_connector.py`
- `fetch_live_india_demand(timeout_sec=10, max_retries=3) -> Dict`:
  - Queries `https://india-energy-data.vercel.app/api/v1/zone/IN/live` with exponential backoff.
  - Computes observation age in hours.
  - Categorizes status: `FRESH` (<2h), `STALE` (≥2h), `CACHED` (disk cache), `UNAVAILABLE`.
  - Persists latest valid observation to `data/cache/last_valid_live_reading.json`.

### J. `simulation.py`
- `simulate_peak_shaving(df_forecast, reduction_pct=0.10) -> pd.DataFrame`:
  - Evaluates peak reduction scenarios while preserving total megawatt-hours across off-peak recovery periods (`is_simulated = True`).
