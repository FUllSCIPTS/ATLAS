#!/usr/bin/env python3
"""ML 09 - A neural network from scratch: forward pass, backpropagation and mini-batch training.

ATLAS link: the paper forecasts load with a Bi-LSTM (atlas_sim/forecast.py, PyTorch). Every deep model
rests on the same mechanics shown here in numpy: layers, a non-linearity, the chain rule, gradient steps.
Task: name the incident kind (6 classes incl. normal) from the basic host monitor plus queue depth.
Applies to: vision, speech, language, forecasting - wherever features are learned rather than designed.
Exercise: remove the hidden layer and confirm the network collapses to logistic regression.
"""
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier

from common import load_anomaly, note, run, show, split, standardise


def main():
    X, y, cat = load_anomaly()
    X = np.log1p(np.abs(X[:, [0, 1, 2, 5]]))                 # rps, CPU, memory, queue depth
    tr, te = split(len(y), seed=9)
    Xtr, Xte = standardise(X[tr], X[te])
    Y = np.eye(6)[cat[tr]]
    rng = np.random.default_rng(9)
    H = 32
    W1, b1 = rng.normal(0, np.sqrt(2 / 4), (4, H)), np.zeros(H)          # He initialisation
    W2, b2 = rng.normal(0, np.sqrt(1 / H), (H, 6)), np.zeros(6)
    lr, weights = 0.05, np.where(cat[tr] == 0, 1.0, 5.0)                # up-weight the rare kinds
    for epoch in range(60):
        order = rng.permutation(len(tr))
        for start in range(0, len(tr), 64):
            i = order[start:start + 64]
            z1 = Xtr[i] @ W1 + b1
            h = np.maximum(z1, 0)                                         # ReLU
            z2 = h @ W2 + b2
            p = np.exp(z2 - z2.max(1, keepdims=True))
            p /= p.sum(1, keepdims=True)                                  # softmax
            d2 = (p - Y[i]) * weights[i, None] / len(i)                   # dLoss/dz2 for cross-entropy
            d1 = (d2 @ W2.T) * (z1 > 0)                                    # chain rule through ReLU
            W2 -= lr * h.T @ d2
            b2 -= lr * d2.sum(0)
            W1 -= lr * Xtr[i].T @ d1
            b1 -= lr * d1.sum(0)
        if epoch in (0, 4, 19, 59):
            pred = (np.maximum(Xte @ W1 + b1, 0) @ W2 + b2).argmax(1)
            show(f'epoch {epoch + 1:>2}: test accuracy', f'{accuracy_score(cat[te], pred):.3f}')
    pred = (np.maximum(Xte @ W1 + b1, 0) @ W2 + b2).argmax(1)
    kinds = cat[te] > 0
    show('ours: accuracy on incident minutes only', f'{accuracy_score(cat[te][kinds], pred[kinds]):.3f}')
    sk = MLPClassifier((32,), max_iter=400, random_state=0).fit(Xtr, cat[tr])
    show('scikit-learn MLP (unweighted)', f'overall {sk.score(Xte, cat[te]):.3f}, incidents only '
         f'{accuracy_score(cat[te][kinds], sk.predict(Xte[kinds])):.3f}')
    eps, i = 1e-5, (0, 0)                                                  # gradient check on one weight
    def loss(W):
        z = np.maximum(Xtr[:64] @ W + b1, 0) @ W2 + b2
        q = np.exp(z - z.max(1, keepdims=True)); q /= q.sum(1, keepdims=True)
        return -np.mean(np.log(q[np.arange(64), cat[tr][:64]] + 1e-12))
    Wp, Wm = W1.copy(), W1.copy(); Wp[i] += eps; Wm[i] -= eps
    z1 = Xtr[:64] @ W1 + b1; h = np.maximum(z1, 0); z = h @ W2 + b2
    q = np.exp(z - z.max(1, keepdims=True)); q /= q.sum(1, keepdims=True)
    analytic = (Xtr[:64].T @ (((q - np.eye(6)[cat[tr][:64]]) / 64) @ W2.T * (z1 > 0)))[i]
    show('gradient check: backprop vs finite difference', f'{analytic:.6f} vs {(loss(Wp) - loss(Wm)) / (2 * eps):.6f}')
    note('Backpropagation is the chain rule applied layer by layer; the gradient check proves ours is')
    note('right. Overall accuracy flatters any model here (95 % of minutes are normal), so look at the')
    note('incidents-only line: up-weighting the rare kinds 5x is how you tell the loss what matters.')
    note('Compare with the library model trained without weights.')


if __name__ == '__main__':
    run(main, __doc__)
