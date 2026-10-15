"""Unit tests for demand-response and peak-shaving simulation."""

import pytest
import pandas as pd
import numpy as np

from src.energy_forecasting.config import TIME_COL, TARGET_COL
from src.energy_forecasting.simulation import simulate_peak_shaving


def test_simulate_peak_shaving_energy_conservation():
    timestamps = pd.date_range("2023-01-01 00:00:00", periods=24, freq="h")
    df = pd.DataFrame(
        {
            TIME_COL: timestamps,
            TARGET_COL: np.ones(24) * 150000.0,
            "horizon_step": range(1, 25),
        }
    )

    sim_df = simulate_peak_shaving(
        df,
        peak_hours=[17, 18, 19, 20],
        reduction_pct=0.20,
        rebound_hours=[22, 23, 0, 1],
    )

    assert "simulated_energy_kwh" in sim_df.columns
    assert "load_shift_delta_kwh" in sim_df.columns
    assert sim_df["is_simulated"].all()

    # Total energy must be conserved between baseline and simulation
    baseline_total = df[TARGET_COL].sum()
    simulated_total = sim_df["simulated_energy_kwh"].sum()
    assert pytest.approx(simulated_total, 0.001) == baseline_total

    # Peak hours should have reduced energy (150,000 * 0.8 = 120,000 MW)
    peak_rows = sim_df[sim_df[TIME_COL].dt.hour.isin([17, 18, 19, 20])]
    assert (peak_rows["simulated_energy_kwh"] == 120000.0).all()
