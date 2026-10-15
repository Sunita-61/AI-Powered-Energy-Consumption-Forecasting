# Technical Glossary: Power Systems & Machine Learning

## Power System Terminology
- **Grid-India / POSOCO**: Power System Operation Corporation Limited (now Grid Controller of India Limited), the national apex organization overseeing the Indian National Electricity Grid.
- **NLDC (National Load Despatch Centre)**: Apex body operating the national grid, coordinating regional load despatch centres (RLDCs), and monitoring All-India load dispatch.
- **Demand Met (MW)**: The total instantaneous active power supplied across all national transmission networks to satisfy end-user demand at a given moment.
- **Megawatt (MW)**: Standard unit of electrical power ($10^6$ Watts). Standard measure of instantaneous grid capacity and demand.
- **Megawatt-hour (MWh)**: Unit of electrical energy equivalent to 1 Megawatt of power sustained over a one-hour period.
- **SCADA (Supervisory Control and Data Acquisition)**: High-speed telemetry systems logging voltage, frequency, and active power at 5-minute or sub-second intervals across substations and power plants.
- **Peak Shaving**: The deliberate management of electricity demand during peak consumption hours through battery storage, demand-side response, or load shifting to avoid grid congestion.
- **Vidyut Pravah**: Ministry of Power portal and mobile application providing transparent public data on electricity demand, market prices, and transmission capacity across Indian states.

## Machine Learning & Time-Series Terminology
- **Target Leakage (Lookahead Bias)**: The erroneous inclusion of information from the prediction target or future periods into the training feature matrix, creating artificially inflated evaluation scores that fail in real-world deployment.
- **Autoregressive Lag**: A feature derived by sampling historical values of the target series from previous time steps (e.g., $y_{t-1}, y_{t-24}, y_{t-168}$).
- **Recursive Multi-Step Forecasting**: Generating forecasts multiple steps into the future by feeding step $k$ model predictions back as input lags for step $k+1$.
- **Chronological Splitting**: Partitioning time-series data strictly by sequential date ranges (past to future) to preserve temporal ordering and prevent future information leakage into model training.
- **Seasonal-Naive Model**: A heuristic forecasting model that predicts the target value will equal the value observed exactly one seasonal period prior ($\hat{y}_t = y_{t-24}$).
- **Random Forest Regressor**: An ensemble machine learning algorithm that builds multiple de-correlated decision trees on bootstrap subsets of training data and outputs their mean prediction.
- **MAE (Mean Absolute Error)**: Average absolute magnitude of errors between predicted and actual demand in MW.
- **RMSE (Root Mean Squared Error)**: Square root of the mean squared errors in MW; penalizes large prediction errors more severely than MAE.
- **WAPE (Weighted Absolute Percentage Error)**: Total absolute error divided by total actual demand, expressed as a percentage. Robust against division-by-zero artifacts common with standard MAPE.

## Software Architecture Terminology
- **Single-Origin URL**: Serving multiple heterogeneous web services and APIs from a single hostname and port (`http://localhost:8501`), avoiding CORS restrictions.
- **Reverse Proxy**: A server (e.g., Caddy) placed in front of web applications that forwards client requests to internal services based on route rules.
- **Graceful Degradation**: Software design pattern where a failure of an external resource (e.g., live telemetry API) causes the system to fall back to a safe, cached state with clear disclosures rather than crashing.
