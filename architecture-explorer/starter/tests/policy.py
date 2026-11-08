from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ml import rl
from ml.registry import write_json


def reject(action, expected):
    try:
        action()
    except ValueError as error:
        assert expected in str(error), error
    else:
        raise AssertionError("Expected approval to fail")


with TemporaryDirectory() as path, patch.object(rl, "MODELS", Path(path)):
    candidate = rl.fit(rl.fixture(), "synthetic-demo")
    version = candidate["version"]
    reject(lambda: rl.approve(version), "require --allow-demo")
    active = rl.approve(version, allow_demo=True)
    assert active["actions"] == {"0": 0, "1": 1}
    assert rl.current_policy()["version"] == version
    candidate["source"] = "recorded-rides"
    candidate["evaluation"]["1:1"]["count"] = 0
    write_json(rl.MODELS / "policies" / f"{version}.json", candidate)
    reject(lambda: rl.approve(version), "Insufficient held-out support")
    assert rl.current_policy()["version"] == version
    with patch("sys.argv", ["ml.rl", "rollback"]):
        rl.main()
    assert rl.current_policy()["version"] == "baseline"
    print("PASS policy candidate, approval gate, support check and rollback")
