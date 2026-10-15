# Setup and Execution Guide: India Grid Demand Forecasting

## 1. System Requirements & Prerequisites
- **Operating System**: Windows 10/11, Linux, or macOS.
- **Python Version**: Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Reverse Proxy**: Caddy v2 (installed via `winget install CaddyServer.Caddy` on Windows or package manager on Linux/macOS). The system includes an auto-detection locator in `run_system.ps1`.
- **Hardware**: Minimum 4 GB RAM, 2 CPU cores.

---

## 2. Installation Steps

### Step 1: Clone or Navigate to Repository
```powershell
cd "c:\Diploma Course\AI\AI-Powered Energy Consumption Forecasting"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Verify Caddy Installation
```powershell
caddy version
```
*(If installed via WinGet, `run_system.ps1` automatically discovers Caddy in `$env:LOCALAPPDATA\Microsoft\WinGet\Packages\`)*.

---

## 3. End-to-End Pipeline Execution (Data & ML Model)

Before running the server, execute the full pipeline to download historical data, preprocess, train candidate models, select the best model, and produce the initial 24-hour forecast:

```powershell
python main.py
```

Expected output:
```
[1/6] Loading Mendeley Historical Data... Loaded 2184 records.
[2/6] Preprocessing and Quality Checks... Complete (0 duplicates, 0 missing).
[3/6] Generating Leakage-Free Lag & Temporal Features... Complete.
[4/6] Chronological 70/15/15 Partitioning & Training...
      Seasonal-Naive: Val MAE = 3288.61 MW
      Linear Regression: Val MAE = 3931.02 MW
      Random Forest: Val MAE = 2968.77 MW (Selected Best!)
[5/6] Final Test Evaluation (Held-out 15%)... Test MAE = 3475.26 MW (WAPE = 2.47%)
[6/6] Generating 24-Hour Autoregressive Forecast... Complete.
```

---

## 4. Single-Origin Unified System Launch

Start all services (FastAPI, Streamlit, and Caddy Reverse Proxy) with a single command:

```powershell
.\run_system.ps1
```

### The Single Browser Entry Point:
Open your browser to:
**[http://localhost:8501](http://localhost:8501)**

All routes are unified on port `8501`:
| Endpoint / URL | Service Handled | Description |
| :--- | :--- | :--- |
| **`http://localhost:8501/`** | Streamlit | Interactive Dashboard & Visualizations |
| **`http://localhost:8501/api/health`** | FastAPI | Service health & data freshness check |
| **`http://localhost:8501/api/data-status`**| FastAPI | Live connector status & data age |
| **`http://localhost:8501/api/forecast`** | FastAPI | Next 24-hour grid demand forecast |
| **`http://localhost:8501/api/metrics`** | FastAPI | Empirical model validation metrics |
| **`http://localhost:8501/api/docs`** | FastAPI | Interactive OpenAPI / Swagger Documentation |

### Clean Shutdown:
Press `Ctrl+C` in the PowerShell window. The launcher cleanly traps the signal and terminates all background processes (`uvicorn`, `streamlit`, `caddy`) without leaving dangling socket listeners.

---

## 5. Automated Verification & Testing
Execute the unit and integration test suite:

```powershell
pytest -v
```
All 32 tests will execute and confirm schema contracts, leakage prevention, reverse-proxy routing, and live connector caching.
