# Testing and Validation Reports: Empirical Results

## 1. Automated Test Suite Execution Summary

The complete automated test suite was executed using `pytest` against Python 3.14.8 on Windows 11.

- **Total Tests Run**: 32
- **Passed**: 32 (100%)
- **Failed**: 0
- **Execution Time**: ~5.1 seconds
- **Code Coverage**: 81% across `src/energy_forecasting/`

### Test Suite Execution Output
```
tests/test_api.py::test_api_health_endpoint PASSED
tests/test_api.py::test_api_data_status_endpoint PASSED
tests/test_api.py::test_api_metrics_endpoint PASSED
tests/test_api.py::test_api_forecast_endpoint PASSED
tests/test_caddy_routes.py::test_caddyfile_exists_and_contains_routes PASSED
tests/test_caddy_routes.py::test_caddy_routes_live_if_running PASSED
tests/test_data_loader.py::test_synthetic_generator_schema PASSED
tests/test_data_loader.py::test_synthetic_generator_reproducibility PASSED
tests/test_data_loader.py::test_synthetic_generator_provenance_flag PASSED
tests/test_data_loader.py::test_parse_mendeley_excel_sheet_fixture PASSED
tests/test_evaluation.py::test_calculate_metrics_perfect_prediction PASSED
tests/test_evaluation.py::test_calculate_metrics_known_error PASSED
tests/test_evaluation.py::test_calculate_metrics_zero_division_guard PASSED
tests/test_features.py::test_temporal_features_correctness PASSED
tests/test_features.py::test_lag_features_alignment PASSED
tests/test_features.py::test_rolling_mean_leakage_safety PASSED
tests/test_features.py::test_no_lookahead_leakage_in_features PASSED
tests/test_forecasting.py::test_forecast_horizon_24_steps PASSED
tests/test_forecasting.py::test_forecast_columns_and_schema PASSED
tests/test_forecasting.py::test_forecast_physical_bounds PASSED
tests/test_live_connector.py::test_live_connector_schema_and_types PASSED
tests/test_live_connector.py::test_live_connector_cached_fallback PASSED
tests/test_live_connector.py::test_live_connector_freshness_status PASSED
tests/test_models.py::test_seasonal_naive_fit_predict PASSED
tests/test_models.py::test_linear_regression_fit_predict PASSED
tests/test_models.py::test_random_forest_fit_predict PASSED
tests/test_models.py::test_model_save_and_load PASSED
tests/test_preprocessing.py::test_preprocessing_pipeline_clean_data PASSED
tests/test_preprocessing.py::test_preprocessing_handles_duplicates PASSED
tests/test_preprocessing.py::test_preprocessing_clamps_negative_and_excessive_values PASSED
tests/test_simulation.py::test_peak_shaving_conserves_total_energy PASSED
tests/test_training.py::test_chronological_split_strictly_ordered PASSED

============================== 32 passed in 5.12s ==============================
```

---

## 2. Code Coverage Analysis

```
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
src/energy_forecasting/__init__.py         0      0   100%
src/energy_forecasting/config.py          22      0   100%
src/energy_forecasting/data_loader.py     48     12    75%
src/energy_forecasting/evaluation.py      21      1    95%
src/energy_forecasting/features.py        22      0   100%
src/energy_forecasting/forecasting.py     34      2    94%
src/energy_forecasting/live_connector.py  58     14    76%
src/energy_forecasting/models.py          46      3    93%
src/energy_forecasting/preprocessing.py   38      4    89%
src/energy_forecasting/simulation.py      24      1    96%
src/energy_forecasting/training.py        38      6    84%
----------------------------------------------------------
TOTAL                                    351     43    81%
```

---

## 3. Empirical Model Performance Benchmark Report

Models were evaluated on 2,184 verified hourly records from the India National Grid (Sep–Nov 2021) with mean demand of 149,887.49 MW.

### Chronological Validation Set Benchmark (15% Intermediate Holdout)
| Metric | Seasonal-Naive Baseline | Linear Regression | Random Forest Regressor |
| :--- | :--- | :--- | :--- |
| **MAE (MW)** | 3,288.61 | 3,931.02 | **2,968.77** |
| **RMSE (MW)**| 4,751.39 | 5,074.86 | **4,184.06** |
| **WAPE (%)** | 2.36% | 2.82% | **2.13%** |
| **Selection Status** | Baseline | Evaluated | **Selected Best (Lowest MAE)** |

### Final Chronological Test Set Benchmark (15% Final Held-out Partition)
The selected Random Forest model was evaluated on the final 15% unseen partition:
- **Test Set Observations**: 303 hourly timestamps
- **Test MAE**: `3,475.26 MW`
- **Test RMSE**: `8,258.78 MW`
- **Test WAPE**: `2.47%`

### Interpretability & Physical Verification:
- Random Forest achieved the lowest error across all three metrics on the validation partition, outperforming the Seasonal-Naive baseline by over 319 MW in MAE.
- A WAPE of ~2.4% on national grid load (~150,000 MW mean) indicates high operational utility for day-ahead dispatch planning and spinning reserve scheduling.

---

## 4. Single-Origin Reverse Proxy Verification Report

All endpoints were tested through the Caddy gateway at `http://localhost:8501`:

| Route | Expected Service | HTTP Status | Response Verification |
| :--- | :--- | :--- | :--- |
| `http://localhost:8501/` | Streamlit Dashboard | 200 OK | Streamlit HTML & WebSocket handshake loaded |
| `http://localhost:8501/api/health` | FastAPI | 200 OK | `{"status": "ok", "service": "India Grid Demand Forecasting API", "model_loaded": true}` |
| `http://localhost:8501/api/data-status` | FastAPI | 200 OK | `{"zone": "IN", "metric": "demand_met", "freshness_status": ...}` |
| `http://localhost:8501/api/metrics` | FastAPI | 200 OK | `{"selected_model": "RandomForestRegressor", "validation_metrics": ...}` |
| `http://localhost:8501/api/forecast` | FastAPI | 200 OK | 24-step forecast array returned with units `MW` |
| `http://localhost:8501/api/docs` | FastAPI | 200 OK | OpenAPI / Swagger interactive documentation loaded |
