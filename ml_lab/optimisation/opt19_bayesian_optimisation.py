#!/usr/bin/env python3
"""OPT 19 - Bayesian optimisation: tuning a forecaster in 20 evaluations with a Gaussian process.

ATLAS link: the Holt-Winters load forecaster of ML 16 on the paper's e-commerce trace has smoothing
constants (alpha for the level, gamma for the daily season). Each setting costs a full backtest, so
we want good settings in few tries. Bayesian optimisation fits a Gaussian-process surrogate to the
tries so far and picks the next one by expected improvement; grid and random search ignore history.
Applies to: hyperparameter tuning, A/B-test design, materials and drug discovery, robot gait tuning.
Exercise: switch the acquisition to an upper confidence bound and vary its exploration weight.
"""
import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

from common import note, run, show, table


def holt_winters(y, season=24, alpha=0.3, beta=0.01, gamma=0.2, horizon=72):
    """Additive Holt-Winters, as in ml_lab/machine_learning/ml16_time_series_forecasting.py."""
    level, trend = y[:season].mean(), (y[season:2 * season].mean() - y[:season].mean()) / season
    seas = list(y[:season] - level)
    for t in range(len(y)):
        s = seas[t % season]
        prev = level
        level = alpha * (y[t] - s) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev) + (1 - beta) * trend
        seas[t % season] = gamma * (y[t] - level) + (1 - gamma) * s
    return np.array([level + (h + 1) * trend + seas[(len(y) + h) % season] for h in range(horizon)])


def backtest_factory():
    from atlas_sim.traffic import ecommerce_trace
    r, _, _ = ecommerce_trace(days=35, seed=19, n_events=4, trend=0.2)
    hourly = r[:35 * 1440].reshape(-1, 60).mean(1)
    cuts = [len(hourly) - 72 * k for k in (3, 2, 1)]               # three rolling 3-day backtests

    def mae(params):
        a, g = params
        errs = [np.mean(np.abs(holt_winters(hourly[:c], alpha=a, gamma=g) - hourly[c:c + 72])) for c in cuts]
        return float(np.mean(errs))
    return mae


def main():
    import warnings
    warnings.filterwarnings('ignore', module='sklearn')
    f = backtest_factory()
    lo, hi = np.array([0.01, 0.01]), np.array([0.99, 0.99])
    budget = 20
    rng = np.random.default_rng(19)
    side = int(np.sqrt(budget))
    grid = [(a, g) for a in np.linspace(0.05, 0.95, side) for g in np.linspace(0.05, 0.95, side)][:budget]
    grid_best = min(f(p) for p in grid)
    random_best = min(f(p) for p in rng.uniform(lo, hi, (budget, 2)))

    X = list(rng.uniform(lo, hi, (4, 2)))                          # 4 random starting points
    y = [f(x) for x in X]
    trace = []
    gp = GaussianProcessRegressor(Matern(length_scale=0.2, nu=2.5) + WhiteKernel(1e-3, noise_level_bounds=(1e-8, 1)), normalize_y=True, random_state=0)
    while len(X) < budget:
        gp.fit(np.array(X), np.array(y))
        cand = rng.uniform(lo, hi, (4000, 2))
        mu, sd = gp.predict(cand, return_std=True)
        best = min(y)
        z = (best - mu) / np.maximum(sd, 1e-9)
        ei = (best - mu) * norm.cdf(z) + sd * norm.pdf(z)          # expected improvement over the best so far
        x = cand[int(np.argmax(ei))]
        X.append(x)
        y.append(f(x))
        trace.append((len(X), f'{x[0]:.2f}', f'{x[1]:.2f}', f'{y[-1]:.1f}', f'{min(y):.1f}'))
    print('  Bayesian optimisation, step by step (MAE in req/s over three 3-day backtests):')
    table(['evaluation', 'alpha', 'gamma', 'MAE', 'best so far'], trace[::3] + ([trace[-1]] if (len(trace) - 1) % 3 else []))
    dense = min(f(p) for p in rng.uniform(lo, hi, (300, 2)))
    rows = [(f'grid search ({side} x {side})', len(grid), f'{grid_best:.1f}'), ('random search', budget, f'{random_best:.1f}'),
            ('Bayesian optimisation (GP + EI)', budget, f'{min(y):.1f}'), ('reference: 300 random evaluations', 300, f'{dense:.1f}')]
    table(['method', 'evaluations', 'best MAE'], rows)
    show('default used in ML 16 (alpha 0.3, gamma 0.2)', f'{f((0.3, 0.2)):.1f}')
    note('The Gaussian process predicts both the error at untried settings and how unsure it is; expected')
    note('improvement trades off exploiting good regions against exploring uncertain ones. When each')
    note('evaluation is a day of simulation or a training run, using every past result matters.')


if __name__ == '__main__':
    run(main, __doc__)
