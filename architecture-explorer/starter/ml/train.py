from datetime import datetime, timezone
from uuid import uuid4

from ml import discrete, forecast
from ml.registry import MODELS, write_json


def train():
    version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:8]
    directory = MODELS / version
    directory.mkdir(parents=True)
    metrics = {**forecast.train(directory), **discrete.train(directory)}
    manifest = {"version": version, "training_data": "synthetic-demo-v1", **metrics}
    write_json(directory / "manifest.json", manifest)
    write_json(MODELS / "active-models.json", manifest)
    print(manifest)


if __name__ == "__main__":
    train()
