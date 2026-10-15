# AI-Powered Energy Consumption Forecasting: India National Grid Demand

[![Automated Tests](https://img.shields.io/badge/pytest-32%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-81%25-green.svg)](tests/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

An end-to-end, production-grade Artificial Intelligence forecasting system for **India's National Electricity Grid Demand** in Megawatts (MW). Designed with rigorous time-series engineering, leakage prevention, verified historical training data from Grid-India / NLDC SCADA, a resilient live telemetry connector polled hourly, and unified behind a single browser URL on **`http://localhost:8501`** via Caddy reverse proxy.

---

## ⚡ Key Highlights
- **Single Browser URL**: Accessible strictly through **`http://localhost:8501`**. Caddy seamlessly proxies root `/*` to Streamlit (port 8502) and `/api/*` to FastAPI (port 8000).
- **Verified Public Historical Training Data**: Ingests monthly SCADA telemetry from Mendeley Data ([DOI: 10.17632/y58jknpgs8.2](https://data.mendeley.com/datasets/y58jknpgs8/2), CC BY 4.0). Extracts `NLDC_DEMAND|P` (National Load Despatch Centre demand in MW) at 5-minute frequency, resampled to 1-hour canonical means.
- **Hourly Live Data Connector**: Integrates candidate aggregator (`https://india-energy-data.vercel.app/api/v1/zone/IN/live`) with 10s timeout, exponential backoff, data age classification (`FRESH`, `STALE`, `CACHED`, `UNAVAILABLE`), local disk cache fallback, and explicit links to the official [National Power Portal (NPP)](https://npp.gov.in/dashBoard/gc-map-dashboard-meritchart).
- **Zero Target Leakage**: Enforces strict chronological partitioning (70% Train, 15% Validation, 15% Test) and shifted lag / rolling features ($t-1, t-24, t-168, \text{rolling\_mean\_24}$).
- **Empirical Model Benchmarks**: Evaluates Seasonal-Naive baseline, Linear Regression, and Random Forest Regressor using real held-out observations:
  - Random Forest selected as best: **Validation MAE: 2,968.77 MW**, **Validation WAPE: 2.13%**, **Test MAE: 3,475.26 MW** (~2.4% error on ~150,000 MW mean load).
- **24-Hour Recursive Multi-Step Forecaster**: Autoregressively projects demand 24 steps into the future with physical sanity bound checks ($[50k, 400k]$ MW).
- **Unified Windows Process Launcher**: `run_system.ps1` starts FastAPI, Streamlit, and Caddy concurrently and handles graceful child process termination on `Ctrl+C`.
- **100% Verified Tests**: 32 passing automated tests across 10 test modules with 81% core library coverage.

---

## 🌐 Single-Origin Architecture

All services are accessible through a single entry point:

```
                            Client Browser / API Consumer
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │ Caddy Reverse Proxy     │
                            │ http://localhost:8501   │
                            └────────────┬────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     │                                       │
           Route: /* (Web UI)                      Route: /api/* (API)
                     │                                       │
                     ▼                                       ▼
        ┌─────────────────────────┐             ┌─────────────────────────┐
        │ Streamlit Application   │             │ FastAPI Microservice    │
        │ Internal: 127.0.0.1:8502│             │ Internal: 127.0.0.1:8000│
        └─────────────────────────┘             └─────────────────────────┘
```

| Public Route | Service Handled | Description |
| :--- | :--- | :--- |
| **`http://localhost:8501/`** | Streamlit | Interactive Dashboard with Plotly Visualizations |
| **`http://localhost:8501/api/health`** | FastAPI | Service health, model status, and cache check |
| **`http://localhost:8501/api/data-status`** | FastAPI | Live connector status, freshness, and observation age |
| **`http://localhost:8501/api/forecast`** | FastAPI | Next 24-hour demand predictions in MW |
| **`http://localhost:8501/api/metrics`** | FastAPI | Empirical validation and test metrics |
| **`http://localhost:8501/api/docs`** | FastAPI | Interactive OpenAPI / Swagger UI documentation |

---

## 📂 Project Structure

```text
AI-Energy-Forecasting/
├── data/
│   ├── raw/                   # Monthly Mendeley Excel files (NLDC_DEMAND|P)
│   ├── processed/             # Canonical hourly demand CSV (MW)
│   ├── cache/                 # Local disk cache for live telemetry
│   └── live/                  # Logged hourly live readings
├── docs/
│   └── technical_documentation/ # SINGLE SOURCE OF TRUTH (17 specification documents)
├── models/                    # Serialized best model artifact (.joblib)
├── outputs/
│   ├── forecasts/             # 24h forecast CSV and JSON
│   └── metrics/               # Empirical evaluation metrics JSON
├── src/
│   └── energy_forecasting/    # Core Python library
│       ├── config.py          # Central paths, ports, units, constants
│       ├── data_loader.py     # Mendeley Excel parser & telemetry extractor
│       ├── preprocessing.py   # Resampling, quality checks, missing imputation
│       ├── features.py        # Temporal features & leakage-free autoregressive lags
│       ├── models.py          # Model wrappers (Seasonal-Naive, Linear, Random Forest)
│       ├── training.py        # Chronological 70/15/15 trainer & model selector
│       ├── evaluation.py      # MAE, RMSE, WAPE calculation engine
│       ├── forecasting.py     # 24-step recursive autoregressive engine
│       ├── live_connector.py  # Resilient live data adapter with backoff & caching
│       └── simulation.py      # Peak-shaving scenario analysis
├── app/
│   └── dashboard.py           # Streamlit interactive UI
├── api/
│   └── main.py                # FastAPI REST endpoints
├── tests/                     # 32 automated unit & integration tests
├── Caddyfile                  # Reverse proxy configuration for port 8501
├── run_system.ps1             # PowerShell unified launcher with clean teardown
├── main.py                    # End-to-end pipeline orchestrator
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quickstart

### 1. Installation & Environment Setup
```powershell
# Navigate to the workspace directory
cd "c:\Diploma Course\AI\AI-Powered Energy Consumption Forecasting"

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the Full ML Pipeline (Ingestion, Training, Forecasting)
```powershell
python main.py
```
This downloads and validates Mendeley data, trains the candidate models, selects the best model, and writes the 24-hour forecast to `outputs/forecasts/`.

### 3. Launch the Complete System (One Command)
```powershell
.\run_system.ps1
```
This starts FastAPI (`:8000`), Streamlit (`:8502`), and Caddy (`:8501`).

Open your browser to:
👉 **[http://localhost:8501](http://localhost:8501)**

### 4. Run Automated Tests
```powershell
pytest -v
```

---

## 📖 Technical Documentation

The single source of truth for all mathematical formulations, architecture diagrams, data contracts, and verification logs is located in:
👉 **[docs/technical_documentation/](docs/technical_documentation/README.md)**

---

## 📜 Attribution & Licenses
- **Historical Dataset**: Mendeley Data, DOI: [10.17632/y58jknpgs8.2](https://doi.org/10.17632/y58jknpgs8.2), License: CC BY 4.0.
- **Candidate Aggregator**: [India-Energy-Data](https://github.com/ADIMANV/India-Energy-Data) (derived from Vidyut Pravah / Grid-India).
- **Official Grid Reference**: [National Power Portal (NPP)](https://npp.gov.in/dashBoard/gc-map-dashboard-meritchart).
