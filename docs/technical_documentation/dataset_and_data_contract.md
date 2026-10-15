# Dataset and Data Contract Specification: India National Electricity Grid

## 1. Primary Historical Dataset Source & Attribution
- **Dataset Title**: Electricity Demand, Solar and Wind Generation Data (September 2021–June 2025) of India at 1-hour interval
- **Repository**: Mendeley Data
- **Official URL**: [https://data.mendeley.com/datasets/y58jknpgs8/2](https://data.mendeley.com/datasets/y58jknpgs8/2)
- **DOI**: `10.17632/y58jknpgs8.2`
- **Contributors**: Harish Kumar, V. S. K. Murthy Balijepalli
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0). Under this license, data can be shared and adapted provided appropriate credit is given.
- **Retrieval Date**: October 2026 (via Mendeley Data REST API v2).

---

## 2. Source Investigation, Verification & Discrepancy Resolution

### A. Title vs. Actual Date Coverage Discrepancy
- **Title Claim**: The Mendeley record title states `September 2021–June 2025`.
- **Actual File List & Coverage**: Inspection of the actual workbook files released under version 2 revealed files:
  - `September 2021.xlsx` through `December 2023.xlsx`.
- **Finding & Resolution**: The published workbooks cover September 1, 2021 through December 31, 2023. June 2025 was the project's planned terminal date, but released data is complete through December 2023. The system relies strictly on verified file timestamps and does not extrapolate or fabricate non-existent 2024–2025 records.

### B. Workbook Sheet Structure & SCADA Column Mapping
- **Sheet Name**: `Sheet1` in each monthly `.xlsx` file.
- **Telemetry Frequency**: Raw observations are recorded at 5-minute intervals (288 observations per day).
- **Target Variable**: Row 0 contains variable headers. Column index 10 represents:
  - **SCADA Tag**: `SCADA/ANALOG/044MQ067/0`
  - **Descriptive Header**: `NLDC_DEMAND|P` (National Load Despatch Centre / Grid-India Total Demand Met in Megawatts).
- **Physical Unit**: Megawatts (MW). Confirmed via POSOCO / NLDC operational grid reporting standards where total instantaneous grid load is reported in MW.

### C. 5-Minute to 1-Hour Canonical Resampling
- Instantaneous power readings sampled every 5 minutes ($t_0, t_5, \dots, t_{55}$) are averaged over each clock hour:
  $$\text{demand\_mw}_h = \frac{1}{12} \sum_{i=1}^{12} P_{h, i}$$
- The resulting time series represents the canonical hourly average demand in Megawatts (MW) for the national grid.

---

## 3. Supplementary Dataset: Zenodo Record 14983362
- **Title**: Daily Indian State Electricity Demand and Weather Data
- **Official URL**: [https://zenodo.org/records/14983362](https://zenodo.org/records/14983362)
- **DOI**: `10.5281/zenodo.14983362`
- **License**: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Methodological Inspection**: This dataset provides daily aggregates at the state level alongside weather metrics (temperature, humidity, precipitation). Because our target forecasting horizon is hourly for the national grid, this supplementary dataset is documented for secondary macro-economic and seasonal feature analysis. It is explicitly not mixed or downsampled into the hourly target series to avoid artificial interpolation artifacts.

---

## 4. Input & Processed Data Schema Contracts

### A. Raw Historical Data Contract (`data/raw/`)
| Field Name | Type | Unit | Description | Constraints / Example |
| :--- | :--- | :--- | :--- | :--- |
| `Timestamp` | `datetime64[ns]` | N/A | SCADA reading timestamp | Format: `YYYY-MM-DD HH:MM:SS` (5-min step) |
| `NLDC_DEMAND\|P` | `float64` | `MW` | National Load Despatch Centre Demand Met | $50,000 \le \text{MW} \le 300,000$ |

### B. Canonical Processed Hourly Contract (`data/processed/india_hourly_demand.csv`)
| Column Name | Type | Unit | Nullable | Domain Constraints | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `timestamp` | `datetime64[ns]` | N/A | No | Strictly monotonically increasing, `freq='h'` | Start of clock hour (UTC / IST normalized) |
| `demand_mw` | `float64` | `MW` | No | $50,000 \le \text{MW} \le 350,000$ | National grid demand met in Megawatts |
| `is_synthetic` | `bool` | N/A | No | `False` for verified real data | Provenance flag indicating real vs synthetic fallback |

### C. Live Telemetry Contract (`data/cache/last_valid_live_reading.json`)
| Field Name | Type | Description |
| :--- | :--- | :--- |
| `retrieval_timestamp_utc` | `ISO 8601 string` | System clock UTC when the HTTP request was completed |
| `observation_timestamp_utc` | `ISO 8601 string` | Timestamp of observation recorded by grid telemetry |
| `zone` | `string` | Target grid zone (`IN` for All-India) |
| `metric` | `string` | Telemetry metric name (`demand_met`) |
| `demand_mw` | `float` | Demand value in Megawatts (MW) |
| `data_age_hours` | `float` | Elapsed time $(\text{retrieval} - \text{observation})$ in hours |
| `freshness_status` | `string` | `FRESH` (<2h), `STALE` (≥2h), `CACHED` (cached fallback), `UNAVAILABLE` |
| `source` | `string` | Upstream data provider identifier |
| `is_synthetic` | `bool` | Explicit provenance flag (`False`) |
