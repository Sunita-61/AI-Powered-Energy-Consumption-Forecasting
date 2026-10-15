# Validation Plan: India Grid Demand Forecasting

## 1. Validation Strategy & Scope
Validation ensures scientific rigor, data integrity, and operational safety before the forecasting system is deployed.

### Core Testing Pillars:
1. **Data Ingestion & Contract Compliance**: Verifies that Mendeley Excel workbooks and live JSON payloads parse strictly into expected types and physical units (MW).
2. **Leakage Prevention Verification**: Verifies mathematically and programmatically that future target information is never accessible to the feature matrix at time $t$.
3. **Partition Independence**: Verifies chronological strictness without random shuffling or overlap.
4. **Physical Sanity Bounds**: Verifies that recursive forecasting predictions remain within realistic national grid boundaries $[50,000, 400,000]$ MW.
5. **Live Connector Resilience**: Verifies timeout, exponential backoff, disk caching, and failure transparency.
6. **Single-Origin Proxy Integrity**: Verifies reverse proxy routing to both UI and API over port `8501`.

---

## 2. Test Matrix & Acceptance Criteria

| Subsystem | Test Objective | Assertion / Condition | Status |
| :--- | :--- | :--- | :--- |
| `data_loader` | Parse Mendeley Excel | `NLDC_DEMAND\|P` extracted and resampled to 1-hour MW | PASSED |
| `preprocessing` | Duplicate & Missing | Zero duplicates; monotonic timestamp index; short gaps interpolated | PASSED |
| `features` | Target Leakage Check | Current `demand_mw` not present in $X$; `rolling_mean_24` uses `.shift(1)` | PASSED |
| `training` | Chronological Split | $\max(\text{train\_ts}) < \min(\text{val\_ts}) < \min(\text{test\_ts})$ | PASSED |
| `models` | Candidate Fitting | All 3 models fit without error; produce finite real-valued predictions | PASSED |
| `evaluation` | Metric Mathematics | MAE, RMSE, WAPE calculations correct; safe against zero division | PASSED |
| `forecasting` | 24-Hour Horizon | Produces exactly 24 sequential hourly predictions within $[50k, 400k]$ MW | PASSED |
| `live_connector`| Cached Fallback | Falls back to disk cache when upstream fails; flags `CACHED` status | PASSED |
| `live_connector`| Unavailable State | Returns `UNAVAILABLE` and official NPP URL when no cache is available | PASSED |
| `api` | Endpoint Contracts | HTTP 200 on `/health`, `/data-status`, `/metrics`, `/forecast` with valid schemas | PASSED |
| `caddy` | Single-Origin Routing | Port 8501 serves Streamlit at `/` and FastAPI at `/api/*` | PASSED |

---

## 3. Metric Evaluation Formulas
To prevent ambiguity, evaluation metrics are implemented with explicit mathematical definitions:

1. **Mean Absolute Error (MAE)**:
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$
   *Unit: Megawatts (MW)*

2. **Root Mean Squared Error (RMSE)**:
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2}$$
   *Unit: Megawatts (MW)*

3. **Weighted Absolute Percentage Error (WAPE)**:
   $$\text{WAPE} = \frac{\sum_{i=1}^{N} |y_i - \hat{y}_i|}{\sum_{i=1}^{N} y_i} \times 100\%$$
   *Unit: Percentage (%) - robust against division-by-zero on low hourly observations.*
