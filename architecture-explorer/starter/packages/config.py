import hmac
import os
from pathlib import Path

from fastapi import HTTPException, Request

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("ATLAS_DATA", ROOT / ".data"))
TOKEN = os.getenv("ATLAS_INTERNAL_TOKEN", "local-internal-only")
TOPIC = "atlas.ride.v1"
DRIVERS = ("driver-a", "driver-b")
KEYS = {
    "rider-a": os.getenv("ATLAS_RIDER_KEY", "rider-demo"),
    "driver-a": os.getenv("ATLAS_DRIVER_A_KEY", "driver-a-demo"),
    "driver-b": os.getenv("ATLAS_DRIVER_B_KEY", "driver-b-demo"),
}


def equal(left, right):
    return hmac.compare_digest(left.encode(), right.encode())


def internal_actor(request: Request, role: str) -> str:
    actor = request.headers.get("X-Atlas-Actor", "")
    if not equal(request.headers.get("X-Atlas-Internal", ""), TOKEN):
        raise HTTPException(403, "Internal service")
    if actor not in (DRIVERS if role == "driver" else ("rider-a",)):
        raise HTTPException(403, "Wrong actor role")
    return actor
