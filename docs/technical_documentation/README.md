# Technical Documentation Index & Governance: India Grid Demand Forecasting

Welcome to the **Single Source of Truth** for the **India National Grid Demand Forecasting System**. Every architectural specification, dataset contract, machine learning methodology, testing evidence, and chronological engineering decision is maintained here.

---

## 1. Documentation Index

| File | Description | Current Status |
| :--- | :--- | :--- |
| [project_scope_and_status.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/project_scope_and_status.md) | Problem statement, operational boundaries, lifecycle tracking, and status matrix | `VALIDATED` |
| [architecture.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/architecture.md) | Single-origin reverse proxy topology, Caddy routing, and component diagrams | `VALIDATED` |
| [data_flow.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/data_flow.md) | End-to-end data lifecycle, 5-min to hourly resampling, feature generation & inference | `VALIDATED` |
| [dataset_and_data_contract.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/dataset_and_data_contract.md) | Mendeley SCADA dataset source, schema, MW units, and live feed JSON contracts | `VALIDATED` |
| [preprocessing_specification.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/preprocessing_specification.md) | Missing data rules, timestamp alignment, 5-min to hourly aggregation logic | `VALIDATED` |
| [feature_engineering_specification.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/feature_engineering_specification.md) | Temporal features, lag variables, rolling statistics, strict leakage prevention | `VALIDATED` |
| [model_learning_and_training.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/model_learning_and_training.md) | Chronological splits, Seasonal-Naive, Linear Regression, Random Forest benchmarks | `VALIDATED` |
| [forecasting_specification.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/forecasting_specification.md) | 24-hour horizon recursive multi-step forecasting engine contract & sanity bounds | `VALIDATED` |
| [module_specification.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/module_specification.md) | Detailed interface specifications for every Python module in `src/` | `VALIDATED` |
| [validation_plan.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/validation_plan.md) | Test plan, acceptance gates, unit and integration test checklist | `VALIDATED` |
| [testing_and_validation_reports.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/testing_and_validation_reports.md) | Concrete test execution results (32 passed), 81% coverage, and empirical metrics | `VALIDATED` |
| [implementation_log.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/implementation_log.md) | Chronological log of execution commands, output summaries, and verification steps | `VALIDATED` |
| [architecture_decisions.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/architecture_decisions.md) | Architecture Decision Records (ADRs) explaining technical tradeoffs | `VALIDATED` |
| [glossary.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/glossary.md) | Glossary of time-series, power grid, and architectural terminology | `VALIDATED` |
| [setup_and_execution_guide.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/setup_and_execution_guide.md) | Reproducible environment setup, CLI execution, dashboard and API run guide | `VALIDATED` |
| [limitations_and_future_work.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/limitations_and_future_work.md) | Explicit limitations, operational boundaries, and future roadmap | `VALIDATED` |

---

## 2. Documentation Governance Rules

1. **Strict Realism & Zero Fabrication**:
   - Never record a test result as passing unless the test command was physically executed and verified.
   - Never claim a metric (e.g. MAE, RMSE, WAPE) that was not output by the actual evaluation pipeline.
   - Never report a feature as `IMPLEMENTED` if it exists solely as a design specification.
2. **Explicit Status Classification**:
   - `PLANNED`: Documented design, no execution code yet written.
   - `IMPLEMENTED`: Code written and syntactically valid.
   - `TESTED`: Unit or integration tests written and passing.
   - `VALIDATED`: End-to-end verified with real data, outputs inspected and persisted.
3. **Continuous Synchronous Updating**:
   - Whenever code changes, corresponding specifications and the [implementation_log.md](file:///c:/Diploma%20Course/AI/AI-Powered%20Energy%20Consumption%20Forecasting/docs/technical_documentation/implementation_log.md) are updated in the same work session.
