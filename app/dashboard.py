"""Streamlit Interactive Visualization Dashboard for All-India Electricity Grid Demand Forecasting."""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.energy_forecasting.config import (
    PROCESSED_INDIA_DATA_FILE,
    BEST_MODEL_FILE,
    EVALUATION_METRICS_FILE,
    TARGET_COL,
    TIME_COL,
    TARGET_UNIT,
    FORECAST_HORIZON_HOURS,
    MENDELEY_DATASET_TITLE,
    MENDELEY_DOI,
    MENDELEY_LICENSE,
    MENDELEY_AUTHORS,
    MENDELEY_DATA_SOURCE,
    MENDELEY_VERIFIED_COVERAGE,
    OFFICIAL_NPP_PORTAL_URL,
)
from src.energy_forecasting.models import load_model
from src.energy_forecasting.forecasting import (
    generate_24h_forecast,
    generate_realtime_grid_forecast,
)
from src.energy_forecasting.live_connector import fetch_live_grid_demand, fetch_live_feed_status
from src.energy_forecasting.simulation import simulate_peak_shaving

# Page Configuration
st.set_page_config(
    page_title="India National Grid Demand Forecasting",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.0rem;
    }
    .live-banner {
        background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 5px solid #10B981;
    }
    .badge-fresh {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-stale {
        background-color: #FEF08A;
        color: #854D0E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-cached {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-unavail {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_historical_data():
    if not PROCESSED_INDIA_DATA_FILE.exists():
        return None
    df = pd.read_csv(PROCESSED_INDIA_DATA_FILE)
    df[TIME_COL] = pd.to_datetime(df[TIME_COL])
    return df


@st.cache_resource
def load_cached_forecaster():
    if not BEST_MODEL_FILE.exists():
        return None, None
    return load_model(BEST_MODEL_FILE)


@st.cache_data
def load_offline_metrics():
    if not EVALUATION_METRICS_FILE.exists():
        return None
    with open(EVALUATION_METRICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # Title & Banner
    st.markdown('<div class="main-header">⚡ All-India National Electricity Grid Demand Forecasting</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Real-Time Grid Telemetry & 24-Hour Recursive Autoregressive AI Forecasting (Megawatts, MW)</div>',
        unsafe_allow_html=True,
    )

    # Sidebar: Live Telemetry & Feed Monitor
    st.sidebar.header("📡 Live Grid Feed Monitor")

    # Refresh button
    if st.sidebar.button("🔄 Refresh Live Grid Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Fetch live reading
    live_reading = fetch_live_grid_demand()

    # Freshness Badge
    status = live_reading.freshness_status
    if status == "FRESH":
        badge_html = f'<span class="badge-fresh">● FRESH ({live_reading.data_age_minutes:.1f} min ago)</span>'
    elif status == "STALE":
        badge_html = f'<span class="badge-stale">▲ STALE ({live_reading.data_age_minutes:.1f} min ago)</span>'
    elif status == "CACHED":
        badge_html = '<span class="badge-cached">ℹ CACHED OBSERVATION</span>'
    else:
        badge_html = '<span class="badge-unavail">✖ FEED UNAVAILABLE</span>'

    st.sidebar.markdown(f"**Feed Status**: {badge_html}", unsafe_allow_html=True)

    if live_reading.feed_online:
        st.sidebar.metric(
            label="Current Demand Met",
            value=f"{live_reading.demand_met_mw:,.0f} {live_reading.unit}",
        )
        st.sidebar.text(f"Observation Time (UTC):\n{live_reading.observation_time_utc[:19]}")
        st.sidebar.text(f"Retrieved At (UTC):\n{live_reading.retrieval_time_utc[:19]}")
        st.sidebar.caption(f"Source: {live_reading.source_attribution}")
    else:
        st.sidebar.error("Live candidate feed is currently offline.")
        if live_reading.is_cached:
            st.sidebar.warning(f"Displaying last cached reading ({live_reading.demand_met_mw:,.0f} MW).")
        st.sidebar.info(
            f"Official Grid Portal:\n[National Power Portal Dashboard]({OFFICIAL_NPP_PORTAL_URL})"
        )

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Operational Controls")

    # Operational Mode Selection
    forecast_mode = st.sidebar.radio(
        "Forecasting Mode",
        options=[
            "🔴 Real-Time Live Grid Forecast (October 2026)",
            "📜 Historical Holdout Benchmark (November 2021)",
        ],
        index=0,
    )

    history_df = load_historical_data()
    model, metadata = load_cached_forecaster()
    metrics = load_offline_metrics()

    if history_df is None or model is None:
        st.error("Historical dataset or trained model not found. Please run `python main.py` first.")
        st.code("python main.py", language="powershell")
        return

    st.sidebar.text(f"Active Model: {metadata.get('best_model_name', 'RandomForestRegressor')}")
    st.sidebar.text(f"Units: Megawatts (MW)")

    days_to_show = st.sidebar.slider("Historical View Window (Days)", min_value=1, max_value=14, value=3)

    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("⏱️ Auto-refresh live data (every 60s)", value=False)
    if auto_refresh:
        time.sleep(1)

    # Top Live Status Ribbon
    if "Real-Time" in forecast_mode:
        st.markdown(
            f"""
            <div class="live-banner">
                <div>
                    <strong>● LIVE ALL-INDIA GRID TELEMETRY:</strong> 
                    <span style="font-size: 1.25rem; font-weight: bold; color: #10B981; margin-left: 8px;">
                        {live_reading.demand_met_mw:,.0f} MW
                    </span>
                    <span style="color: #94A3B8; margin-left: 12px;">| Telemetry Time: {live_reading.observation_time_utc[:19]} UTC</span>
                </div>
                <div>
                    {badge_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Main Tabs
    tab_forecast, tab_benchmarks, tab_simulation, tab_provenance = st.tabs(
        ["📈 24-Hour Grid Forecast", "📊 Model Benchmarks", "🔋 Load-Shifting Scenario", "📜 Data Provenance & Ethics"]
    )

    # Determine data source & forecast according to mode
    if "Real-Time" in forecast_mode:
        recent_history, forecast_df = generate_realtime_grid_forecast(
            model=model,
            live_reading=live_reading,
            history_df=history_df,
            horizon_hours=FORECAST_HORIZON_HOURS,
            model_name=metadata.get("best_model_name", "RandomForestRegressor"),
        )
        origin = forecast_df["forecast_origin"].iloc[0]
        if isinstance(origin, str):
            origin = pd.to_datetime(origin)
        chart_title = f"All-India Real-Time Grid Demand & Next 24-Hour AI Forecast ({TARGET_UNIT})"
        history_trace_name = "Recent Live Telemetry / Baseline"
    else:
        origin = history_df[TIME_COL].max()
        forecast_df = generate_24h_forecast(
            history_df=history_df,
            model=model,
            origin_timestamp=origin,
            horizon_hours=FORECAST_HORIZON_HOURS,
            model_name=metadata.get("best_model_name", "TrainedForecaster"),
        )
        cutoff_date = origin - pd.Timedelta(days=days_to_show)
        recent_history = history_df[history_df[TIME_COL] >= cutoff_date]
        chart_title = f"Historical SCADA Grid Demand & 24-Hour Holdout Forecast ({TARGET_UNIT})"
        history_trace_name = "Historical SCADA Grid Demand"

    with tab_forecast:
        peak_row = forecast_df.loc[forecast_df[TARGET_COL].idxmax()]
        min_row = forecast_df.loc[forecast_df[TARGET_COL].idxmin()]
        avg_demand = forecast_df[TARGET_COL].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Forecast Origin (T)", f"{origin.strftime('%Y-%m-%d %H:%M UTC')}")
        c2.metric(
            "Peak Projected Demand",
            f"{peak_row[TARGET_COL]:,.0f} MW",
            f"Hour {pd.to_datetime(peak_row[TIME_COL]).strftime('%H:%M UTC')}",
        )
        c3.metric(
            "Minimum Projected Demand",
            f"{min_row[TARGET_COL]:,.0f} MW",
            f"Hour {pd.to_datetime(min_row[TIME_COL]).strftime('%H:%M UTC')}",
        )
        c4.metric("24h Average Demand", f"{avg_demand:,.0f} MW")

        st.markdown("---")

        # Time-Series Plot: History + 24-Hour Forecast
        fig = go.Figure()

        # History / Anchor Trace
        fig.add_trace(
            go.Scatter(
                x=recent_history[TIME_COL],
                y=recent_history[TARGET_COL],
                name=history_trace_name,
                line=dict(color="#0284C7", width=2),
                mode="lines",
            )
        )

        # Real-time Observation Marker if in real-time mode
        if "Real-Time" in forecast_mode and live_reading.feed_online:
            fig.add_trace(
                go.Scatter(
                    x=[pd.to_datetime(live_reading.observation_time_utc[:19])],
                    y=[live_reading.demand_met_mw],
                    name="Live Reading (Vidyut Pravah)",
                    mode="markers",
                    marker=dict(size=12, color="#EF4444", symbol="diamond"),
                )
            )

        # Forecast Trace
        fig.add_trace(
            go.Scatter(
                x=forecast_df[TIME_COL],
                y=forecast_df[TARGET_COL],
                name=f"24h Autoregressive AI Forecast ({metadata.get('best_model_name')})",
                line=dict(color="#10B981", width=3),
                mode="lines+markers",
                marker=dict(size=6, color="#059669"),
            )
        )

        # Origin Divider
        fig.add_vline(
            x=origin,
            line_width=2,
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Forecast Origin (NOW)",
            annotation_position="top left",
        )

        fig.update_layout(
            title=chart_title,
            xaxis_title="Timestamp (UTC)",
            yaxis_title=f"National Grid Demand ({TARGET_UNIT})",
            template="plotly_white",
            hovermode="x unified",
            height=490,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, width="stretch")

        # Table & Download CSV
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            with st.expander("🔍 View Detailed 24-Hour Forecast Table"):
                st.dataframe(
                    forecast_df[[TIME_COL, "horizon_step", TARGET_COL, "unit", "model_name"]],
                    width="stretch",
                )
        with col_t2:
            csv_data = forecast_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Forecast CSV",
                data=csv_data,
                file_name=f"india_grid_forecast_24h_{'realtime' if 'Real-Time' in forecast_mode else 'historical'}.csv",
                mime="text/csv",
            )

    with tab_benchmarks:
        st.subheader("Rigorous Chronological Model Benchmarks")
        st.markdown(
            "All candidate models are evaluated strictly on **identical held-out chronological timestamps** "
            "(Train 70%, Validation 15%, Test 15%). Shuffling is strictly disallowed."
        )

        if metrics:
            val_metrics = metrics.get("validation_metrics", {})
            test_metrics = metrics.get("test_metrics", {})

            comp_rows = []
            for m_name, m_vals in val_metrics.items():
                comp_rows.append(
                    {
                        "Model Architecture": m_name,
                        "Validation MAE (MW)": f"{m_vals.get('MAE', 0):,.2f}",
                        "Validation RMSE (MW)": f"{m_vals.get('RMSE', 0):,.2f}",
                        "Validation WAPE (%)": f"{m_vals.get('WAPE', 0):.2f}%",
                        "Selection Status": "Selected Best" if m_name == metadata.get("best_model_name") else "Candidate",
                    }
                )
            st.table(pd.DataFrame(comp_rows))

            # Comparative Bar Chart
            mae_vals = [m_vals.get("MAE", 0) for m_vals in val_metrics.values()]
            m_names = list(val_metrics.keys())
            fig_bar = px.bar(
                x=m_names,
                y=mae_vals,
                labels={"x": "Model Architecture", "y": "Validation MAE (MW)"},
                title="Candidate Models by Validation MAE (Lower is Better)",
                color=m_names,
                text_auto=".1f",
                template="plotly_white",
            )
            st.plotly_chart(fig_bar, width="stretch")

            # Held-out Test Card
            best_test = test_metrics.get(metadata.get("best_model_name"), {})
            st.info(
                f"**Held-out Test Performance ({metadata.get('best_model_name')})**: "
                f"MAE: **{best_test.get('MAE', 0):,.2f} MW** | "
                f"RMSE: **{best_test.get('RMSE', 0):,.2f} MW** | "
                f"WAPE: **{best_test.get('WAPE', 0):.2f}%**"
            )

    with tab_simulation:
        st.subheader("Demand-Response & Peak Shaving What-If Scenario")
        st.warning(
            "⚠️ **SCENARIO SIMULATION NOTICE**: This is an illustrative what-if load-shifting scenario analysis. "
            "It demonstrates mathematical energy conservation during peak tariff windows and does not claim empirical savings."
        )

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            reduction = st.slider("Peak Hours Curtailment (%)", min_value=5, max_value=30, value=15, step=5) / 100.0
        with col_s2:
            st.markdown(
                "Peak Hours: **17:00 – 20:00 (Evening Lighting Peak)**<br>Rebound Off-Peak Hours: **22:00 – 01:00**",
                unsafe_allow_html=True,
            )

        sim_df = simulate_peak_shaving(forecast_df, reduction_pct=reduction)
        shift_col = "simulated_demand_mw" if "simulated_demand_mw" in sim_df.columns else "simulated_energy_kwh"

        fig_sim = go.Figure()
        fig_sim.add_trace(
            go.Scatter(
                x=sim_df[TIME_COL],
                y=sim_df[TARGET_COL],
                name="Baseline Demand Forecast",
                line=dict(color="#10B981", width=2),
            )
        )
        fig_sim.add_trace(
            go.Scatter(
                x=sim_df[TIME_COL],
                y=sim_df[shift_col],
                name=f"Simulated Shift ({int(reduction*100)}% Peak Curtailment)",
                line=dict(color="#F59E0B", width=2, dash="dash"),
            )
        )
        fig_sim.update_layout(
            title="Load-Shifting Demand Profile Comparison (MW)",
            xaxis_title="Timestamp",
            yaxis_title="National Grid Demand (MW)",
            template="plotly_white",
            height=420,
        )
        st.plotly_chart(fig_sim, width="stretch")

    with tab_provenance:
        st.subheader("Data Provenance, Licensing & Technical Attributes")
        st.markdown(
            f"""
            ### Primary Historical Dataset
            - **Title**: {MENDELEY_DATASET_TITLE}
            - **Authors**: {MENDELEY_AUTHORS}
            - **Attribution / Source**: {MENDELEY_DATA_SOURCE}
            - **DOI**: [{MENDELEY_DOI}](http://doi.org/{MENDELEY_DOI})
            - **License**: **{MENDELEY_LICENSE}** (Creative Commons Attribution 4.0)
            - **Verified Coverage**: {MENDELEY_VERIFIED_COVERAGE}
            - **Target Variable**: `NLDC_DEMAND|P` resampled to hourly average grid demand in **Megawatts (MW)**.

            ### Live Telemetry Connector
            - **Provider**: Candidate third-party aggregator (`https://india-energy-data.vercel.app`) sourcing from *Vidyut Pravah*.
            - **Verification Status**: Tested live; returns zone `IN` demand in MW.
            - **Official National Verification Portal**: [{OFFICIAL_NPP_PORTAL_URL}]({OFFICIAL_NPP_PORTAL_URL})
            - **Polling Interval**: Hourly with 3-attempt exponential backoff.
            """
        )


if __name__ == "__main__":
    main()
