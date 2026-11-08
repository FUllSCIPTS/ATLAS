#!/usr/bin/env python3
"""ML 02 - Bias, variance and regularisation: fitting the latency curve with polynomials and ridge.

ATLAS link: latency rises like 1/(1 - rho) as the monolith fills (the queueing model inside the paper's
simulator). With only 40 measured points, how flexible should the model be?
Applies to: every model with a "complexity knob" - tree depth, number of features, network size.
Exercise: replace the polynomial with the physics: fit a + b / (1 - c * load) with scipy.optimize.
"""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from common import note, run, show, table, telemetry


def main():
    rng = np.random.default_rng(0)
    load = np.sort(rng.uniform(100, 3000, 20))            # 20 load tests, up to rho ~ 0.9
    lat = telemetry(load, seed=7)[:, 3].astype(float)
    grid = np.linspace(load.min(), load.max(), 400)
    from atlas_sim.traffic import DEMAND_MS, VISIT
    D = float((VISIT * DEMAND_MS).sum())
    truth = 12 + D / (1 - grid * D / 1000 / 16)              # the generator's noise-free curve

    rows = []
    for degree in (1, 2, 3, 5, 9, 15):
        model = make_pipeline(PolynomialFeatures(degree), StandardScaler(), Ridge(alpha=1e-8))
        model.fit(load[:, None], lat)
        train = np.sqrt(np.mean((model.predict(load[:, None]) - lat) ** 2))
        test = np.sqrt(np.mean((model.predict(grid[:, None]) - truth) ** 2))
        cv = -cross_val_score(model, load[:, None], lat, cv=KFold(5, shuffle=True, random_state=0), scoring='neg_root_mean_squared_error').mean()
        rows.append((degree, f'{train:.1f}', f'{cv:.1f}', f'{test:.1f}'))
    print('  plain least squares (no penalty), RMSE in ms (20 noisy points):')
    table(['degree', 'train', '5-fold CV', 'vs truth'], rows)

    rows = []
    for alpha in (1e-6, 1e-3, 1e-1, 1, 10, 100):
        model = make_pipeline(PolynomialFeatures(15), StandardScaler(), Ridge(alpha=alpha)).fit(load[:, None], lat)
        coef = model[-1].coef_
        test = np.sqrt(np.mean((model.predict(grid[:, None]) - truth) ** 2))
        cv = -cross_val_score(model, load[:, None], lat, cv=KFold(5, shuffle=True, random_state=0), scoring='neg_root_mean_squared_error').mean()
        rows.append((alpha, f'{np.abs(coef).sum():.1f}', f'{cv:.1f}', f'{test:.1f}'))
    print('\n  degree 15 with a ridge penalty alpha * ||w||^2:')
    table(['alpha', 'sum |w|', '5-fold CV', 'vs truth'], rows)
    show('measurement noise (sd)', '2.0 ms; "vs truth" = error against the noise-free curve')
    note('Degree 1 underfits (bias): a straight line cannot bend up near saturation. High degrees with no')
    note('penalty chase the noise (variance): the lowest training error, the worst cross-validation.')
    note('Cross-validation finds the sweet spot from the training data alone, and a ridge penalty lets a')
    note('flexible model stay calm. Read the "vs truth" column only after choosing - in practice you never see it.')


if __name__ == '__main__':
    run(main, __doc__)
