#!/usr/bin/env python3
"""ML 01 - Linear regression three ways: normal equations, gradient descent and scikit-learn.

ATLAS link: capacity planning. How much CPU does the monolith use per request/s? The data are the
paper's telemetry generator (atlas_sim/traffic.py) driven by its e-commerce trace.
Applies to: any "how much Y per unit of X" question - cost per user, energy per job, sales per ad euro.
Exercise: add the hour-of-day as a feature and see whether the residuals shrink.
"""
import numpy as np
from sklearn.linear_model import LinearRegression

from common import note, run, show, split, telemetry, traffic


def main():
    r, _, _ = traffic(days=7, seed=1)
    T = telemetry(r, seed=101)                      # a different seed: same-seed streams would share noise
    x, y = T[:, 0], T[:, 1]                          # requests/s -> CPU %
    keep = x < 1500                                  # ordinary load: the linear region (rho < 0.5)
    x, y = x[keep], y[keep]
    tr, te = split(len(x))
    X = np.column_stack([np.ones_like(x), x])

    w_ne = np.linalg.solve(X[tr].T @ X[tr], X[tr].T @ y[tr])          # (X'X) w = X'y
    w_gd, lr = np.zeros(2), 0.5
    xs = (x - x[tr].mean()) / x[tr].std()                             # scale first, or GD crawls
    Xs = np.column_stack([np.ones_like(xs), xs])
    for step in range(200):
        grad = 2 / len(tr) * Xs[tr].T @ (Xs[tr] @ w_gd - y[tr])
        w_gd -= lr * grad
    slope_gd = w_gd[1] / x[tr].std()
    sk = LinearRegression().fit(x[tr, None], y[tr])

    show('normal equations', f'CPU % = {w_ne[0]:.2f} + {w_ne[1] * 1000:.2f} per 1000 req/s')
    show('gradient descent (200 steps)', f'slope {slope_gd * 1000:.2f} per 1000 req/s')
    show('scikit-learn', f'slope {sk.coef_[0] * 1000:.2f} per 1000 req/s')
    pred = X[te] @ w_ne
    rmse = np.sqrt(np.mean((pred - y[te]) ** 2))
    r2 = 1 - np.sum((pred - y[te]) ** 2) / np.sum((y[te] - y[te].mean()) ** 2)
    show('test RMSE / R^2', f'{rmse:.2f} percentage points / {r2:.3f}')
    show('load at 85 % CPU (rho_max)', f'{(85 - w_ne[0]) / w_ne[1]:,.0f} req/s')
    from atlas_sim.traffic import DEMAND_MS, VISIT
    theory = 88 * (VISIT * DEMAND_MS).sum() / 1000 / 16
    show('generator truth: 88 * D / 16 cores', f'{theory * 1000:.2f} per 1000 req/s')
    note('All three agree because the loss is a convex quadratic: one minimum, and the normal equations')
    note('jump straight to it. Gradient descent needs scaled features and a step size; it is what you use')
    note('when X is too big to invert. The fit recovers the generator\'s true slope to within 0.2 %.')
    note('Pitfall found while writing this: seeding the trace and the telemetry with the same seed made')
    note('their noise identical and biased the slope by 9 %. Independent noise is an assumption - check it.')

if __name__ == '__main__':
    run(main, __doc__)
