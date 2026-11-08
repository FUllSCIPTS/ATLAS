#!/usr/bin/env python3
"""OPT 03 - Second-order methods: Newton's method, BFGS and L-BFGS versus gradient descent.

ATLAS link: training the anomaly classifier of ML 03 (logistic regression on data.zip) is a smooth
convex problem. Newton uses the exact curvature (Hessian), BFGS builds an approximation from gradients,
and gradient descent uses none. Count iterations and watch the error fall quadratically.
Applies to: statistics (GLMs are fitted by Newton/IRLS), engineering design, any smooth problem of
modest size; L-BFGS scales to millions of parameters.
Exercise: add Armijo backtracking to Newton and start it far from the optimum.
"""
import time

import numpy as np
from scipy.optimize import minimize

from common import ROOT, note, run, show, table


def load():
    import csv, io, zipfile
    with zipfile.ZipFile(ROOT / 'data.zip') as z:
        rows = list(csv.DictReader(io.TextIOWrapper(z.open('data/anomaly_data.csv'), encoding='utf-8')))
    X = np.log1p(np.array([[float(r[k]) for k in ('rps', 'cpu_pct', 'mem_pct')] for r in rows]))
    X = (X - X.mean(0)) / X.std(0)
    return np.c_[np.ones(len(X)), X], np.array([float(r['label']) for r in rows])


def main():
    X, y = load()
    lam = 1e-3

    def loss(w):
        z = X @ w
        return np.mean(np.logaddexp(0, z) - y * z) + lam / 2 * w @ w

    def grad(w):
        p = 1 / (1 + np.exp(-X @ w))
        return X.T @ (p - y) / len(y) + lam * w

    def hess(w):
        p = 1 / (1 + np.exp(-X @ w))
        return (X * (p * (1 - p))[:, None]).T @ X / len(y) + lam * np.eye(X.shape[1])

    w_star = minimize(loss, np.zeros(4), jac=grad, hess=hess, method='trust-exact', tol=1e-14).x
    f_star = loss(w_star)
    w = np.zeros(4)
    print('  Newton: w <- w - H^-1 g   (error = loss - optimum)')
    for k in range(7):
        print(f'    iteration {k}: error {loss(w) - f_star:.3e}')
        w = w - np.linalg.solve(hess(w), grad(w))
    rows = []
    for method in ('Newton-CG', 'BFGS', 'L-BFGS-B', 'CG'):
        t0 = time.perf_counter()
        res = minimize(loss, np.zeros(4), jac=grad, hess=hess if method == 'Newton-CG' else None, method=method,
                       options={'Newton-CG': {'xtol': 1e-12}, 'L-BFGS-B': {'gtol': 1e-9, 'ftol': 1e-15}}.get(method, {'gtol': 1e-9}))
        rows.append((method, res.nit, res.nfev, f'{res.fun - f_star:.1e}', f'{(time.perf_counter() - t0) * 1000:.0f} ms'))
    w, k = np.zeros(4), 0
    L = np.linalg.eigvalsh(hess(np.zeros(4))).max()
    t0 = time.perf_counter()
    while loss(w) - f_star > 1e-9 and k < 100000:
        w -= grad(w) / L
        k += 1
    rows.append(('gradient descent (step 1/L)', k, k, f'{loss(w) - f_star:.1e}', f'{(time.perf_counter() - t0) * 1000:.0f} ms'))
    table(['method', 'iterations', 'function evals', 'final error', 'time'], rows)
    show('optimal weights', np.round(w_star, 3).tolist())
    note('Near the optimum Newton doubles the number of correct digits each step (quadratic convergence)')
    note('but needs the Hessian: n x n memory and an n^3 solve. BFGS learns the curvature from successive')
    note('gradients (superlinear), L-BFGS keeps only the last few, so it scales. Plain gradient descent')
    note('needs hundreds of cheap steps for the same accuracy.')


if __name__ == '__main__':
    run(main, __doc__)
