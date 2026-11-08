#!/usr/bin/env python3
"""OPT 01 - Gradient descent: step size, convergence and why conditioning decides the speed.

ATLAS link: fitting the CPU-per-request capacity model (ML 01) is the convex problem
min_w ||Xw - y||^2. In raw units (requests/s in the thousands next to an intercept of 1) the problem
is badly conditioned; after scaling it is easy. Same data, same optimum, very different journeys.
Applies to: every model trained by gradient methods, from linear regression to deep networks.
Exercise: prove that with step 1/L (L = largest Hessian eigenvalue) the loss never increases.
"""
import numpy as np

from common import note, run, show, table


def descend(H, w_star, step, iters=5000, tol=1e-6):
    """Gradient descent on the quadratic 0.5 (w - w*)' H (w - w*); returns iterations to tol (or None)."""
    w = np.zeros(len(w_star))
    for k in range(iters):
        grad = H @ (w - w_star)
        if np.linalg.norm(w - w_star) <= tol * np.linalg.norm(w_star):
            return k
        w = w - step * grad
        if not np.isfinite(w).all() or np.linalg.norm(w) > 1e12:
            return 'diverged'
    return f'> {iters}'


def main():
    from atlas_sim.traffic import telemetry
    from atlas_sim.traffic import ecommerce_trace
    r, _, _ = ecommerce_trace(days=3, seed=1)
    T = telemetry(r.astype(float), np.random.default_rng(101))
    x, y = T[:, 0].astype(float), T[:, 1].astype(float)
    rows = []
    for name, X in (('raw units [1, req/s]', np.c_[np.ones_like(x), x]),
                    ('kilo-requests [1, req/s / 1000]', np.c_[np.ones_like(x), x / 1000]),
                    ('standardised [1, z-score]', np.c_[np.ones_like(x), (x - x.mean()) / x.std()])):
        H = 2 * X.T @ X / len(x)                                        # Hessian of the mean squared error
        w_star = np.linalg.solve(X.T @ X, X.T @ y)
        eig = np.linalg.eigvalsh(H)
        Lmax = eig.max()
        rows.append((name, f'{eig.max() / eig.min():.3g}', descend(H, w_star, 1 / Lmax),
                     descend(H, w_star, 1.9 / Lmax), descend(H, w_star, 2.1 / Lmax)))
    table(['features', 'condition number', 'step 1/L', 'step 1.9/L', 'step 2.1/L'], rows)
    print('  (iterations until w is within 1e-6 of the exact least-squares solution)')
    show('theory', 'error shrinks by (1 - 1/kappa) per step at best; step > 2/L diverges')
    note('Gradient descent zig-zags across narrow valleys. The condition number kappa (largest / smallest')
    note('curvature) sets the pace: millions of steps in raw units, a handful after standardising. The')
    note('step size has a hard ceiling of 2/L. Fix the geometry first (scale features, precondition), then')
    note('tune the step - or use curvature directly (OPT 03).')


if __name__ == '__main__':
    run(main, __doc__)
