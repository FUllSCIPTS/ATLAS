from functools import lru_cache
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ml import forecast
from ml.registry import MODELS, read_json
from ml.rl import current_policy
from packages.config import DATA

app = FastAPI(title="ATLAS Model Serving")


class Candidate(BaseModel):
    driver_id: str
    distance_km: float = Field(ge=0, le=50)
    speed_kph: float = Field(ge=0, le=250)


class ScoringRequest(BaseModel):
    zone: Literal["cork-centre", "cork-north"]
    drivers: list[Candidate] = Field(min_length=1, max_length=20)


@lru_cache(maxsize=2)
def models(version):
    directory = MODELS / version
    return forecast.load(directory), joblib.load(directory / "acceptance.joblib"), joblib.load(directory / "anomaly.joblib")


def active():
    manifest = read_json(MODELS / "active-models.json")
    if manifest is None:
        raise HTTPException(503, "Run python -m ml.train first")
    return manifest


@app.get("/healthz")
def health():
    manifest = active()
    models(manifest["version"])
    return {"status": "ok", "models": manifest["version"], "policy": current_policy()["version"]}


@app.post("/internal/v1/score")
def score(payload: ScoringRequest):
    manifest = active()
    lstm, acceptance, anomaly = models(manifest["version"])
    counts = read_json(DATA / "demand.json", {}).get(payload.zone, manifest["seed_window"])
    demand = forecast.predict(lstm, counts)
    bucket = int(demand >= 8)
    features = [[d.distance_km, d.speed_kph] for d in payload.drivers]
    probabilities = acceptance.predict_proba(features)[:, 1]
    flags = anomaly.predict(features)
    policy = current_policy()
    actions = policy["actions"]
    return {
        "model_version": manifest["version"], "forecast": round(demand, 4), "bucket": bucket,
        "action": actions.get(str(bucket), actions.get(bucket, 0)), "policy_version": policy["version"],
        "drivers": [{"driver_id": d.driver_id, "acceptance": float(p), "anomaly_flag": bool(flag == -1)}
                    for d, p, flag in zip(payload.drivers, probabilities, flags, strict=True)],
    }
