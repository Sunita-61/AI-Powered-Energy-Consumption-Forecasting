# Feature Engineering Specification: India Grid Demand

## 1. Feature Strategy & Leakage Prevention Rules

In time series forecasting, **target leakage** occurs whenever information from the target timestamp $t$ or future timestamps $t+k$ is erroneously incorporated into the feature representation at time $t$.

### Strict Leakage Prevention Invariants:
1. **No Concurrent Target Value**: The feature vector for forecasting demand at hour $t$ must never contain `demand_mw` at hour $t$.
2. **Lag Calculation**: All autoregressive lags are strictly referenced backwards ($t-k$ for $k \ge 1$).
3. **Rolling Window Alignment**: Rolling statistics (such as 24-hour moving average) must be calculated over shifted data:
   $$\text{rolling\_mean\_24}_t = \frac{1}{24} \sum_{i=1}^{24} y_{t-i}$$
   In Pandas, this is enforced using `.shift(1).rolling(24).mean()`. Using unshifted `.rolling(24).mean()` would leak the contemporaneous target $y_t$.

---

## 2. Feature Schema & Definitions

| Feature Name | Type | Physical / Mathematical Definition | Range / Domain |
| :--- | :--- | :--- | :--- |
| `hour_of_day` | `int64` | Hour component of timestamp (`ts.hour`) | $[0, 23]$ |
| `day_of_week` | `int64` | Day of week (`ts.dayofweek`), Monday=0, Sunday=6 | $[0, 6]$ |
| `is_weekend` | `int64` | Binary indicator: 1 if Saturday or Sunday, else 0 | $\{0, 1\}$ |
| `month` | `int64` | Month of year (`ts.month`) representing seasonal load | $[1, 12]$ |
| `lag_1` | `float64` | National demand met 1 hour prior ($y_{t-1}$) in MW | $[50000, 400000]$ |
| `lag_24` | `float64` | National demand met 24 hours prior ($y_{t-24}$) in MW | $[50000, 400000]$ |
| `lag_168` | `float64` | National demand met 168 hours prior (same hour last week) in MW | $[50000, 400000]$ |
| `rolling_mean_24` | `float64` | Mean demand over preceding 24 hours ($[t-24, t-1]$) in MW | $[50000, 400000]$ |

---

## 3. Rationale for Feature Selection
- **`hour_of_day`**: Captures strong diurnal cycle (morning commercial ramp up, evening domestic lighting/cooling peak, late-night trough).
- **`day_of_week` & `is_weekend`**: Reflects commercial and industrial factory load reduction on Sundays and Saturdays.
- **`month`**: Captures seasonal monsoon, summer air conditioning peaks, and winter heating/agricultural pumping load variations across India.
- **`lag_1`**: Encodes short-term system momentum and inertia.
- **`lag_24`**: Strongest daily periodicity baseline (demand at 2:00 PM today strongly correlates with demand at 2:00 PM yesterday).
- **`lag_168`**: Weekly seasonality capturing day-of-week recurrence.
- **`rolling_mean_24`**: Smooths transient hourly noise and captures base-load trajectory.

---

## 4. Multi-Step Recursive Feature Updates
During 24-hour ahead forecasting, actual target observations $y_{t+k}$ are unavailable. The forecasting engine updates the feature matrix recursively:
1. For step $k=1$, compute features from known historical lags.
2. Predict $\hat{y}_{t+1}$.
3. For step $k=2$, append $\hat{y}_{t+1}$ to the demand history buffer so that `lag_1` becomes $\hat{y}_{t+1}$.
4. Recompute calendar features for timestamp $t+k$ and update rolling statistics over the updated buffer.
5. Repeat through $k=24$.
