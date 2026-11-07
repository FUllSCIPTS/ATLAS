import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score


def train(directory):
    rng = np.random.default_rng(11)
    normal = np.column_stack([rng.uniform(.1, 12, 800), rng.normal(28, 9, 800)])
    normal[:, 1] = np.maximum(normal[:, 1], 0)
    probability = 1 / (1 + np.exp(-(.9 - .25 * normal[:, 0] + .045 * normal[:, 1])))
    accepted = rng.binomial(1, probability)
    acceptance = LogisticRegression(random_state=11).fit(normal[:640], accepted[:640])
    anomaly = IsolationForest(n_estimators=35, contamination=.03, random_state=11).fit(normal[:640])
    anomalous = np.column_stack([rng.uniform(17, 35, 100), rng.uniform(115, 200, 100)])
    evaluation = np.vstack([normal[640:], anomalous])
    joblib.dump(acceptance, directory / "acceptance.joblib")
    joblib.dump(anomaly, directory / "anomaly.joblib")
    return {
        "acceptance_brier": round(brier_score_loss(accepted[640:], acceptance.predict_proba(normal[640:])[:, 1]), 4),
        "anomaly_roc_auc": round(roc_auc_score([0] * 160 + [1] * 100, -anomaly.score_samples(evaluation)), 4),
    }
