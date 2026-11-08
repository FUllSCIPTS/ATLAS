#!/usr/bin/env python3
"""OPT 02 - Momentum, Nesterov and Adam: faster first-order methods on hard valleys.

ATLAS link: the paper trains its Bi-LSTM load forecaster with Adam (atlas_sim/forecast.py), and the
existing lab (ml_optimisation_lab.py section 5) compares Adam with plain gradient descent on the same
forecaster. Here the optimisers race on two classic test landscapes so each mechanism is visible.
Applies to: training any neural network; large-scale logistic regression; matrix factorisation.
Exercise: add learning-rate decay to plain gradient descent and see how close it gets to Adam.
"""
import numpy as np

from common import note, run, table


def rosenbrock(x):
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2


def rosenbrock_grad(x):
    return np.array([-2 * (1 - x[0]) - 400 * x[0] * (x[1] - x[0] ** 2), 200 * (x[1] - x[0] ** 2)])


def valley(x):                      # an ill-conditioned quadratic (curvatures 1 and 100)
    return 0.5 * (x[0] ** 2 + 100 * x[1] ** 2)


def valley_grad(x):
    return np.array([x[0], 100 * x[1]])


def optimise(method, f, grad, x0, lr, steps=10000, tol=1e-6, f_star=0.0):
    x, v, m, s = x0.copy(), np.zeros(2), np.zeros(2), np.zeros(2)
    for t in range(1, steps + 1):
        if f(x) - f_star < tol:
            return t
        if method == 'gradient descent':
            x = x - lr * grad(x)
        elif method == 'momentum (heavy ball)':
            v = 0.9 * v - lr * grad(x)
            x = x + v
        elif method == 'Nesterov':
            g = grad(x + 0.9 * v)                     # look ahead before computing the gradient
            v = 0.9 * v - lr * g
            x = x + v
        else:                                         # Adam: per-coordinate step from gradient moments
            g = grad(x)
            m = 0.9 * m + 0.1 * g
            s = 0.999 * s + 0.001 * g * g
            x = x - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(s / (1 - 0.999 ** t)) + 1e-8)
        if not np.isfinite(x).all() or np.abs(x).max() > 1e6:
            return 'diverged'
    return f'> {steps}'


def best(method, f, grad, x0):
    """Try a grid of step sizes and keep the fastest - a fair race needs each method at its best."""
    results = []
    for lr in np.geomspace(1e-4, 1.0, 29):
        steps = optimise(method, f, grad, x0, lr)
        if isinstance(steps, int):
            results.append((steps, lr))
    return min(results) if results else ('-', None)


def main():
    np.seterr(all='ignore')
    rows = []
    for method in ('gradient descent', 'momentum (heavy ball)', 'Nesterov', 'Adam'):
        (sv, lv), (sr, lr_) = best(method, valley, valley_grad, np.array([10.0, 1.0])), \
            best(method, rosenbrock, rosenbrock_grad, np.array([-1.2, 1.0]))
        rows.append((method, f'{sv} (lr {lv:.2g})', f'{sr} (lr {lr_:.2g})'))
    table(['method', 'steps: valley (kappa 100)', 'steps: Rosenbrock banana'], rows)
    print('  (steps until f is within 1e-6 of the minimum, each method at its best step size from a grid)')
    note('Momentum accumulates velocity along the valley floor and damps the zig-zag across it: about')
    note('sqrt(kappa) instead of kappa steps. Nesterov evaluates the gradient where momentum is about to take')
    note('it, which corrects overshoot. Adam rescales every coordinate by its own gradient history, so it')
    note('works with one large step size on both landscapes - the reason it is the default for neural')
    note('networks. There is no overall winner: the best method depends on the landscape.')


if __name__ == '__main__':
    run(main, __doc__)
