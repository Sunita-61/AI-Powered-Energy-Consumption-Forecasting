"""Load-shifting and peak-shaving simulation module.

Enables what-if grid scenario analyses for Indian National Grid demand.
CRITICAL TRANSPARENCY RULE: All outputs are explicitly labeled as simulated scenarios
and never presented as verified empirical savings.
"""

from typing import List, Optional
import logging
import pandas as pd
import numpy as np

from src.energy_forecasting.config import TARGET_COL, TIME_COL

logger = logging.getLogger(__name__)


def simulate_peak_shaving(
    forecast_df: pd.DataFrame,
    peak_hours: Optional[List[int]] = None,
    reduction_pct: float = 0.15,
    rebound_hours: Optional[List[int]] = None,
    target_col: str = TARGET_COL,
    time_col: str = TIME_COL,
) -> pd.DataFrame:
    """Simulates a demand-response or battery storage load-shifting scenario over the 24-hour horizon.

    Algorithm:
    1. Identifies forecast hours falling into `peak_hours` (default: 17:00 - 20:00, evening peak).
    2. Curtails demand in peak hours by `reduction_pct` (e.g. 15%).
    3. Conservatively shifts the curtailed energy into specified `rebound_hours` (e.g. 22:00 - 01:00),
       strictly preserving total energy conservation.
    4. Adds explicit audit column `is_simulated_scenario=True`.

    Returns:
        pd.DataFrame with added columns ['simulated_energy_kwh', 'load_shift_delta_kwh', 'is_simulated'].
    """
    if forecast_df.empty:
        raise ValueError("Cannot simulate on an empty forecast DataFrame.")

    if peak_hours is None:
        peak_hours = [17, 18, 19, 20]
    if rebound_hours is None:
        rebound_hours = [22, 23, 0, 1]

    if not (0.0 <= reduction_pct <= 0.80):
        raise ValueError(f"reduction_pct must be between 0.0 and 0.80, got {reduction_pct}.")

    sim_df = forecast_df.copy()
    sim_df[time_col] = pd.to_datetime(sim_df[time_col])

    hours = sim_df[time_col].dt.hour
    baseline = sim_df[target_col].astype(float).values

    curtailed_energy = 0.0
    simulated_values = baseline.copy()

    # Step 1: Curtail peak hours
    for idx, hour in enumerate(hours):
        if hour in peak_hours:
            curtailment = baseline[idx] * reduction_pct
            simulated_values[idx] -= curtailment
            curtailed_energy += curtailment

    # Step 2: Rebound energy during off-peak hours
    rebound_indices = [idx for idx, hour in enumerate(hours) if hour in rebound_hours]
    if rebound_indices and curtailed_energy > 0:
        addition_per_slot = curtailed_energy / len(rebound_indices)
        for idx in rebound_indices:
            simulated_values[idx] += addition_per_slot

    sim_df["simulated_energy_kwh"] = np.round(simulated_values, 2)
    sim_df["simulated_demand_mw"] = np.round(simulated_values, 2)
    sim_df["load_shift_delta_kwh"] = np.round(simulated_values - baseline, 2)
    sim_df["load_shift_delta_mw"] = np.round(simulated_values - baseline, 2)
    sim_df["is_simulated"] = True
    sim_df["simulation_type"] = f"Peak Shaving ({int(reduction_pct*100)}% shift)"

    return sim_df
