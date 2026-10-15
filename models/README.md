# Models Directory

This directory stores trained, serialized machine learning models (e.g. `.joblib` artifacts) generated during the training pipeline.

## Model Artifact Storage:
- Serialized estimators: `models/<model_name>.joblib`
- Metadata: Training timestamp, hyperparameter records, and input feature lists.
- Model loading and persistence is handled via `src.energy_forecasting.models`.
