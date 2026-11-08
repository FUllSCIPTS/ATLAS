#!/usr/bin/env python3
"""ML 16 - Time-series forecasting: naive baselines, Holt-Winters by hand and a lag regression.

ATLAS link: ATLAS scales and re-couples ahead of demand, so it needs tomorrow's load. The paper uses a
Bi-LSTM (atlas_sim/forecast.py); here are the classical models every forecaster must beat, on the
paper's e-commerce trace aggregated to hours.
Applies to: sales, energy demand, inventory, call centres, web traffic.
Exercise: add holiday/event flags (the trace's event mask) as regressors to the lag model.
"""
import numpy as np
from sklearn.linear_model import Ridge

from common import note, run, table, traffic


def holt_winters(y, season=24, alpha=0.3, beta=0.01, gamma=0.2, horizon=72):
    """Additive Holt-Winters: level + trend + seasonal, each updated by exponential smoothing."""
    level, trend = y[:season].mean(), (y[season:2 * season].mean() - y[:season].mean()) / season
    seas = list(y[:season] - level)
    for t in range(len(y)):
        s = seas[t % season]
        prev_level = level
        level = alpha * (y[t] - s) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seas[t % season] = gamma * (y[t] - level) + (1 - gamma) * s
    n = len(y)
    return np.array([level + (h + 1) * trend + seas[(n + h) % season] for h in range(horizon)])


def main():
    r, _, _ = traffic(days=35, seed=16, n_events=8, trend=0.2)
    hourly = r[:35 * 1440].reshape(-1, 60).mean(1)              # requests/s averaged per hour
    train, test = hourly[:-72], hourly[-72:]                    # forecast the last 3 days

    lags = [1, 2, 3, 24, 48, 168]
    def design(series, idx):
        h = idx % 24
        return np.c_[[series[idx - k] for k in lags]].T.tolist(), np.c_[np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)]
    idx = np.arange(168, len(train))
    A, B = design(train, idx)
    model = Ridge(1.0).fit(np.c_[A, B], train[idx])
    hist = list(train)
    lag_pred = []
    for t in range(len(train), len(train) + 72):                  # recursive multi-step forecast
        a, b = design(np.array(hist + [0.0]), np.array([t]))
        p = float(model.predict(np.c_[a, b])[0])
        lag_pred.append(p)
        hist.append(p)
    forecasts = {
        'persistence (last hour)': np.full(72, train[-1]),
        'seasonal naive (same hour yesterday)': np.tile(train[-24:], 3),
        'seasonal naive (same hour last week)': train[-168:-96],
        'Holt-Winters (additive, by hand)': holt_winters(train),
        'ridge on lags 1,2,3,24,48,168 + hour': np.array(lag_pred),
    }
    rows = []
    for name, f in forecasts.items():
        err = f - test
        rows.append((name, f'{np.mean(np.abs(err)):.1f}', f'{100 * np.mean(np.abs(err) / test):.1f} %', f'{np.mean(err):+.1f}'))
    table(['3-day-ahead forecast', 'MAE (req/s)', 'MAPE', 'bias'], rows)
    note('Persistence ignores the daily cycle; seasonal naive is a strong, free baseline - here the weekly')
    note('version beats every fitted model, because the trace has a weekly rhythm. Holt-Winters')
    note('tracks a drifting level and season with three smoothing constants. Multi-step forecasts feed')
    note('their own predictions back in, so errors compound - that is why the paper predicts each horizon')
    note('directly. Flash-crowd events are not in any history: no model above can foresee them.')


if __name__ == '__main__':
    run(main, __doc__)
