# Architecture Decision Records (ADRs)

## ADR 001: Target Selection — India National Grid Demand in Megawatts (MW)
- **Status**: Accepted
- **Context**: Accurate forecasting of national electricity demand is essential for power system operators (Grid-India / POSOCO), distribution companies (DISCOMs), and renewable generators.
- **Decision**: Target the aggregate All-India grid demand met (`NLDC_DEMAND|P` / `demand_met`) in Megawatts (MW) as the canonical target variable.
- **Consequences**: Provides high societal relevance, standardizes on instantaneous power demand (MW), and allows direct comparison between historical SCADA records and real-time live telemetry.

---

## ADR 002: Single-Origin Gateway via Caddy Reverse Proxy on Port 8501
- **Status**: Accepted
- **Context**: The user requires a single browser URL (`http://localhost:8501`) providing access to both an interactive Streamlit UI and a production-grade FastAPI microservice.
- **Decision**: Deploy Caddy v2 as a lightweight reverse proxy listening on port 8501. Caddy routes `/api/*` requests to FastAPI on internal port 8000 and all other traffic (`/*`) to Streamlit on internal port 8502.
- **Consequences**: Eliminates CORS complications, presents a unified entry point, and maintains complete separation of concerns between presentation and API layers.

---

## ADR 003: Resolution of Mendeley Historical Telemetry to Hourly Canonical Means
- **Status**: Accepted
- **Context**: The primary historical dataset (Mendeley Data DOI: `10.17632/y58jknpgs8.2`) records SCADA measurements at 5-minute frequency, while the forecasting task is for next-24-hour hourly demand. Furthermore, the dataset title claims coverage through June 2025, but released workbooks cover through December 2023.
- **Decision**: Extract column index 10 (`NLDC_DEMAND|P`) representing total national demand in MW and resample 5-minute readings to 1-hour arithmetic means. Use verified timestamps from existing workbooks without fabricating unreleased 2024–2025 data.
- **Consequences**: Produces a clean, continuous hourly time series aligned with standard day-ahead electricity market dispatch cycles.

---

## ADR 004: Live Connector Resilience, Data Age Status & Non-Fabrication Policy
- **Status**: Accepted
- **Context**: Real-time grid telemetry is fetched from a third-party aggregator (`india-energy-data.vercel.app/api/v1/zone/IN/live`). Third-party APIs may experience latency, rate-limiting, or downtime.
- **Decision**: Implement a resilient client with 10s timeout, exponential backoff (1s, 2s, 4s), and 3 retries. Distinguish observation timestamp from retrieval timestamp. Categorize freshness as `FRESH` (<2h), `STALE` (≥2h), `CACHED` (disk fallback), or `UNAVAILABLE`. If live data is inaccessible, never fabricate numbers; surface `CACHED` / `UNAVAILABLE` states and link to the official National Power Portal (NPP).
- **Consequences**: Protects operational integrity, prevents false confidence, and informs operators of true telemetry health.

---

## ADR 005: Strict Leakage Prevention & Autoregressive 24-Step Recursive Horizon
- **Status**: Accepted
- **Context**: Forecasting 24 hours ahead requires features that are legally available at forecast origin $t$.
- **Decision**: Calculate rolling 24-hour statistics using `.shift(1).rolling(24).mean()` to avoid contemporaneous target leakage. Use a recursive multi-step forecaster that generates $\hat{y}_{t+k}$, appends it to the dynamic history buffer, and recalculates subsequent lags and rolling means dynamically.
- **Consequences**: Guarantees zero lookahead bias during training and evaluation while enabling multi-step forecasts for any arbitrary horizon up to 24 hours.

---

## ADR 006: Chronological 70/15/15 Data Partitioning
- **Status**: Accepted
- **Context**: Standard random cross-validation leaks future information into past predictions.
- **Decision**: Enforce sequential chronological partitioning: Training (70%), Validation (15%), Test (15%). Validation is used for model selection; Test is used for final unbiased reporting.
- **Consequences**: Model evaluation metrics reflect true out-of-sample generalization.

---

## ADR 007: Unified Process Launcher with Signal Trapping (`run_system.ps1`)
- **Status**: Accepted
- **Context**: Starting multiple backend processes across terminals risks orphaned background listeners when a terminal is closed.
- **Decision**: Provide a unified PowerShell script `run_system.ps1` that spawns FastAPI, Streamlit, and Caddy as tracked background jobs, monitors startup health, and traps `Ctrl+C` to terminate all child processes cleanly.
- **Consequences**: Provides seamless developer experience on Windows and eliminates zombie port conflicts.
