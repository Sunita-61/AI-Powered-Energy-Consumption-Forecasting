# System Limitations and Future Work

## 1. Current System Limitations

### A. Third-Party Live Telemetry Dependency
- **Limitation**: The candidate live data connector relies on a third-party aggregator (`india-energy-data.vercel.app`), which aggregates data from Vidyut Pravah. While functioning, it is not an official government enterprise API with an enforced SLA.
- **Mitigation**: The system implements an explicit data freshness state machine (`FRESH`, `STALE`, `CACHED`, `UNAVAILABLE`), preserves last-known good readings in local disk cache, and provides immediate links to the official National Power Portal (NPP).

### B. Historical Horizon Coverage
- **Limitation**: The Mendeley Data dataset record claims "September 2021–June 2025" in its title, but the published workbooks released under version 2 cover September 2021 through December 2023.
- **Mitigation**: The system operates exclusively on verified file timestamps and does not extrapolate unverified dates.

### C. Exogenous Feature Integration
- **Limitation**: The current model relies purely on endogenous autoregressive lags (`lag_1`, `lag_24`, `lag_168`), rolling averages, and calendar features (`hour`, `dayofweek`, `is_weekend`, `month`). It does not incorporate real-time All-India weather telemetry (temperature, cooling degree days, solar irradiance, wind speed).
- **Impact**: Extreme heatwave spikes or sudden unseasonal monsoon deluges cannot be anticipated ahead of the 24-hour lag horizon.

### D. Single-Node In-Memory Execution
- **Limitation**: The recursive forecaster and model inference operate synchronously in Python memory on a single machine. While fast (<100ms for 24 steps), scaling to regional 5-minute telemetry across all 5 regional load despatch centres (Northern, Western, Southern, Eastern, North Eastern) would require distributed stream processing.

---

## 2. Roadmap for Future Work

### Phase 1: Direct Integration with National Power Portal (NPP) & POSOCO Telemetry
- Implement direct authenticated connectors to CEA (Central Electricity Authority) and Grid-India open data portals once official public APIs or standardized daily operational bulletins are accessible.

### Phase 2: Exogenous Weather & Solar/Wind Integration
- Ingest real-time and numerical weather prediction (NWP) forecasts from India Meteorological Department (IMD) / ECMWF / Open-Meteo across major load centers (Delhi, Mumbai, Chennai, Kolkata, Bengaluru).
- Forecast net demand by subtracting solar and wind generation profiles from gross electricity demand.

### Phase 3: Advanced Deep Learning & Probabilistic Forecasting
- Implement state-of-the-art probabilistic time-series architectures (Temporal Fusion Transformer, PatchTST, Chronos) to output prediction intervals ($P_{10}, P_{50}, P_{90}$) rather than point forecasts, enabling risk-aware spinning reserve scheduling.

### Phase 4: Regional Grid Decomposition
- Expand forecasting beyond the All-India aggregate to individual regional grids (NR, WR, SR, ER, NER) and state distribution companies (DISCOMs) to assist in inter-regional transmission constraint management.
