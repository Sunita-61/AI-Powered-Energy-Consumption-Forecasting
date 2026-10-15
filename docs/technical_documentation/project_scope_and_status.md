# Project Scope and Status: India National Grid Demand Forecasting

## 1. Project Objective & Vision
The goal of this system is to provide an end-to-end, production-grade Artificial Intelligence forecasting platform for **India's National Electricity Grid Demand** in Megawatts (MW). 

The platform combines verified historical SCADA training data, an independently verified live telemetry connector polled hourly, leakage-free machine learning models, and an interactive dual-surface application (Streamlit dashboard + FastAPI REST service) unified seamlessly behind a single browser origin at **`http://localhost:8501`**.

---

## 2. Current Implementation Status

| Milestone / Requirement | Target Specification | Current Status | Notes |
| :--- | :--- | :--- | :--- |
| **Single Local URL** | `http://localhost:8501` | **COMPLETED** | Caddy reverse proxy on port 8501 routing `/` (Streamlit: 8502) and `/api/*` (FastAPI: 8000) |
| **Historical Data Source** | Mendeley Data (`10.17632/y58jknpgs8.2`) | **COMPLETED** | Downloaded monthly workbooks; resolved Sep 2021–Dec 2023 coverage; resampled 5-min SCADA `NLDC_DEMAND\|P` to 1-hour MW |
| **Live Telemetry Connector** | `india-energy-data.vercel.app` (IN Zone) | **COMPLETED** | Hourly polling, exponential backoff, UTC normalization, data freshness classification, fallback to local disk cache & NPP portal link |
| **Machine Learning Engine** | SN, LR, Random Forest Models | **COMPLETED** | Chronological 70/15/15 split, leakage-free lags + rolling mean, RF achieved Val MAE 2,968.77 MW (selected best) |
| **24-Hour Forecaster** | Autoregressive recursive multi-step | **COMPLETED** | Generates 24 hourly predictions in MW with grid sanity clamping |
| **FastAPI Microservice** | REST Endpoints (`/health`, `/forecast`, etc.)| **COMPLETED** | Fully operational and documented at `/api/docs` |
| **Streamlit Dashboard** | Plotly charts, live badges, metrics | **COMPLETED** | Live grid demand, 24h predictions, benchmark comparison, peak shaving simulation |
| **Process Launcher** | PowerShell unified runner | **COMPLETED** | `run_system.ps1` starts and cleanly stops all 3 services |
| **Automated Verification** | `pytest` test suite | **COMPLETED** | 32 passed, 0 failed, 81% test coverage across core modules |
| **Technical Documentation** | 17 Markdown documents | **COMPLETED** | Complete single source of truth in `docs/technical_documentation/` |

---

## 3. Discrepancy & Verification Findings

1. **Mendeley Title vs. Data Range**:
   - The dataset title notes `September 2021–June 2025`. However, actual workbook files published on Mendeley Data end in December 2023. The system processes actual verified files (Sep–Nov 2021 in initial batch: 2,184 hourly points) and documents this coverage discrepancy honestly without fabricating non-existent dates.
2. **Third-Party Aggregator Caveat**:
   - The candidate aggregator (`https://india-energy-data.vercel.app/api/v1/zone/IN/live`) is a community aggregator sourcing from Vidyut Pravah / Grid-India, not an official government SLA endpoint. The system treats it with defensive retry policies, data age classification, and transparent fallback links to the official National Power Portal (NPP).
3. **Single Origin Guarantee**:
   - Users need only bookmark `http://localhost:8501`. Direct internal ports (`8502` and `8000`) are not presented to users.
