# Preprocessing Specification: India National Grid Demand

## 1. Objectives & Invariants
The preprocessing subsystem cleans, validates, and aligns national SCADA electricity grid data into a canonical, continuous time-series format suitable for machine learning training and inference.

### Core Invariants:
1. **Target Unit**: All energy demand measurements must be strictly in Megawatts (`MW`).
2. **Temporal Step**: Fixed, regular hourly spacing (`freq='1h'`).
3. **Monotonicity**: Timestamps must be sorted in strictly ascending chronological order without inversions.
4. **Physical Bounds**: India national peak demand spans roughly 100,000 MW to 260,000 MW historically. Valid physical bounds are enforced at $[50,000 \text{ MW}, 400,000 \text{ MW}]$.
5. **No Synthetic Masking**: Real historical data must carry `is_synthetic: False`. Only emergency offline test data is generated with `is_synthetic: True`.

---

## 2. Ingestion & Transformation Rules

### A. Raw 5-Minute SCADA Resampling
- Input: Telemetry logged every 5 minutes from `NLDC_DEMAND|P`.
- Resampling Operation: Hourly mean aggregation:
  ```python
  df_hourly = df_raw.set_index("timestamp").resample("1h").mean().reset_index()
  ```
- Missing Minutes Policy: An hourly bucket requires at least one valid 5-minute reading to produce an hourly mean; hours with no readings are marked as missing intervals.

### B. Duplicate Timestamp Resolution
- Detection: Search for duplicate timestamps in the indexed series.
- Policy: When duplicate timestamps exist with differing readings, calculate the arithmetic mean. If duplicate timestamps have identical readings, drop subsequent duplicates.

### C. Missing Timestamp Sequence Detection & Imputation
- Detection: Compute expected full chronological range:
  ```python
  expected_range = pd.date_range(start=start_time, end=end_time, freq="1h")
  ```
- Imputation Policy:
  - Gaps $\le 3$ hours: Imputed using time-weighted linear interpolation.
  - Gaps $> 3$ hours: Documented as system telemetry outages; left unfilled or handled via forward-fill with warning in the data quality report.

### D. Outlier Clamping & Validation
- Readings below 50,000 MW or above 400,000 MW are considered telemetry recording glitches or transmission dropouts.
- Outliers are clamped to boundary thresholds $[50000.0, 400000.0]$ and logged in the data quality report.

---

## 3. Data Quality Report Contract

The function `preprocess_data()` produces both the cleaned dataframe and a structured quality dictionary:

```json
{
  "total_records_input": 2184,
  "total_records_output": 2184,
  "duplicates_resolved": 0,
  "missing_timestamps_filled": 0,
  "outliers_clamped": 0,
  "min_demand_mw": 87400.5,
  "max_demand_mw": 195240.2,
  "mean_demand_mw": 149887.49,
  "start_timestamp": "2021-09-01T00:00:00",
  "end_timestamp": "2021-11-30T23:00:00",
  "is_synthetic": false
}
```
