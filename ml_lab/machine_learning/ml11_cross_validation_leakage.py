#!/usr/bin/env python3
"""ML 11 - Cross-validation and leakage: why a random split flatters a time-series model.

ATLAS link: forecasting next-minute load from the last few minutes on the paper's e-commerce trace.
Shuffled k-fold puts tomorrow's neighbours in the training set; forward-chaining (TimeSeriesSplit)
only ever trains on the past, as production must. A leaked feature makes it worse still.
Applies to: any data with time, users or groups - stock prices, patients, sensors, sessions.
Exercise: use GroupKFold with day as the group and compare.
"""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, TimeSeriesSplit, cross_val_score

from common import note, run, table, traffic


def main():
    r, _, _ = traffic(days=7, seed=11, n_events=6)
    lags, horizon = 10, 15                                       # predict 15 minutes ahead
    idx = np.arange(lags, len(r) - horizon)
    X = np.stack([r[idx - k] for k in range(lags)], 1)
    y = r[idx + horizon]
    leak = r[idx + horizon - 1]                                  # a feature from the future (a common bug)
    rows = []
    for name, model in (('ridge on 10 lags', Ridge(1.0)),
                        ('random forest on 10 lags', RandomForestRegressor(30, min_samples_leaf=20, random_state=0, n_jobs=-1))):
        for cv_name, cv in (('shuffled 5-fold', KFold(5, shuffle=True, random_state=0)),
                            ('time-series 5-fold', TimeSeriesSplit(5))):
            mae = -cross_val_score(model, X, y, cv=cv, scoring='neg_mean_absolute_error').mean()
            rows.append((name, cv_name, f'{mae:.1f}'))
    Xl = np.c_[X, leak]
    mae = -cross_val_score(Ridge(1.0), Xl, y, cv=TimeSeriesSplit(5), scoring='neg_mean_absolute_error').mean()
    rows.append(('ridge + leaked t+14 value', 'time-series 5-fold', f'{mae:.1f}'))
    naive = np.mean(np.abs(y - X[:, 0]))
    rows.append(('baseline: "same as now"', '-', f'{naive:.1f}'))
    table(['model', 'validation', 'MAE (req/s)'], rows)
    note('Under shuffled folds the forest beats the "same as now" baseline; under forward-chaining, which')
    note('is what production does, it loses to it. Shuffling put neighbouring minutes in both train and test,')
    note('so the forest partly memorised. The leaked feature lifts even plain ridge above every honest model -')
    note('always ask "would I know this value at prediction time?" And always report a naive baseline.')

if __name__ == '__main__':
    run(main, __doc__)
