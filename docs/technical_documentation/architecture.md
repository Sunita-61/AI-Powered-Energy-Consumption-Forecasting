# System Architecture: India Grid Demand Forecasting

## 1. Architectural Overview & Single-Origin Topology

The system is deployed using a single-origin reverse proxy topology to provide unified access on `http://localhost:8501`. 

Users and external clients interact exclusively with port `8501`. Internally, Caddy routes incoming requests between the interactive Streamlit dashboard and the FastAPI REST microservice based on URL path prefixes:

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
        └────────────┬────────────┘             └────────────┬────────────┘
                     │                                       │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌─────────────────────────────────────┐
                      │ Shared Core Python Engine           │
                      │ (src/energy_forecasting/)           │
                      │ • data_loader.py  • preprocessing.py│
                      │ • features.py     • models.py       │
                      │ • training.py     • evaluation.py   │
                      │ • forecasting.py  • live_connector.py│
                      └──────────────────┬──────────────────┘
                                         │
                        ┌────────────────┴────────────────┐
                        ▼                                 ▼
             Local Artifact Storage             External Data Sources
             • data/raw/                        • Mendeley Data (Historical)
             • data/processed/                  • India Energy Live Aggregator
             • data/cache/                      • National Power Portal (Ref)
             • models/
             • outputs/metrics/ & forecasts/
```

---

## 2. Component Specifications

### A. Caddy Reverse Proxy (Port 8501)
- **Role**: Public gateway and SSL-ready reverse proxy.
- **Rules**:
  - `handle_path /api/*`: Strips `/api` prefix and reverse-proxies directly to `127.0.0.1:8000/*`.
  - `handle /*`: Proxies all other traffic to Streamlit at `127.0.0.1:8502`, preserving WebSockets for interactive bi-directional dashboard updates.
- **Header Forwarding**: Preserves `Host`, `X-Real-IP`, and `X-Forwarded-For`.

### B. Streamlit Dashboard (Internal Port 8502)
- **Role**: Rich graphical user interface providing interactive exploration of historical grid patterns, real-time grid telemetry, model benchmarks, 24-hour load predictions, what-if peak shaving, and data provenance disclosures.
- **Headless Mode**: Configured with `--server.headless true --server.port 8502`.

### C. FastAPI Application (Internal Port 8000)
- **Role**: High-performance REST API serving JSON contracts for integration with grid management systems, SCADA dashboards, and automated downstream controllers.
- **Documentation**: Automatic OpenAPI / Swagger UI served at `/api/docs`.

### D. Live Data Polling & Connector (`live_connector.py`)
- **Adapter**: Connects to the candidate aggregator `https://india-energy-data.vercel.app/api/v1/zone/IN/live`.
- **Resilience Engine**: Implements HTTP timeouts (10s), exponential backoff with jitter (1s, 2s, 4s), and maximum 3 retries.
- **Data Freshness State Machine**:
  - `FRESH`: Observation age < 2.0 hours.
  - `STALE`: Observation age ≥ 2.0 hours.
  - `CACHED`: Live request failed, but cached reading from disk (`data/cache/last_valid_live_reading.json`) was successfully loaded.
  - `UNAVAILABLE`: Live request failed and no disk cache exists.
- **Fallback Transparency**: When external connectivity fails, the connector discloses the failure clearly and provides reference links to the official National Power Portal (NPP).

### E. Unified Windows Process Launcher (`run_system.ps1`)
- Launches FastAPI, Streamlit, and Caddy concurrently.
- Verifies startup health across all three services.
- Traps termination signals (`Ctrl+C`, `SIGINT`, `SIGTERM`) and reliably terminates all spawned child processes to avoid zombie background listeners.
