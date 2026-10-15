# Data Directory Structure

This directory stores all datasets utilized across the AI-Energy-Forecasting pipeline.

## Directory Sub-folders:
- `raw/`: Stores pristine, unmodified raw data downloads (e.g. from UCI Machine Learning Repository). Never modify files directly in this folder.
- `processed/`: Stores cleaned, validated, and aggregated time-series data (e.g. hourly energy series in kWh) produced by `src/energy_forecasting/preprocessing.py`.
- `sample/`: Stores lightweight, committed sample slices or synthetic fallback data for instant testing, continuous integration, and quick local runs.

## Data Lineage & Units
- Raw UCI readings: 15-minute average power / kW.
- Conversion: `interval_energy_kwh = average_power_kw * 0.25`
- Processed: Hourly aggregate (`energy_kwh = sum(4 intervals)`).

Refer to [dataset_and_data_contract.md](../docs/technical_documentation/dataset_and_data_contract.md) for full data contract details.
