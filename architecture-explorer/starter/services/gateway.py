import os
import re

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from packages.config import KEYS, ROOT, TOKEN, equal

app = FastAPI(title="ATLAS Demo Gateway")
TRIP_URL = os.getenv("ATLAS_TRIP_URL", "http://127.0.0.1:8001")
DISPATCH_URL = os.getenv("ATLAS_DISPATCH_URL", "http://127.0.0.1:8002")
app.mount("/assets", StaticFiles(directory=ROOT / "apps/shared"), name="assets")
ROUTES = {
    ("GET", "rider", r"trips/[a-f0-9-]{36}"): TRIP_URL,
    ("POST", "rider", "trips"): TRIP_URL,
    ("POST", "driver", r"trips/[a-f0-9-]{36}/milestones"): TRIP_URL,
    ("GET", "driver", "offers"): DISPATCH_URL,
    ("POST", "driver", r"offers/[a-f0-9-]{36}/accept"): DISPATCH_URL,
    ("PUT", "driver", "availability"): DISPATCH_URL,
}


@app.get("/healthz")
def health():
    try:
        for origin in (TRIP_URL, DISPATCH_URL):
            httpx.get(origin + "/healthz", timeout=2, trust_env=False).raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(503, "Ride service unavailable") from error
    return {"status": "ok"}


@app.get("/")
@app.get("/passenger")
def passenger():
    return FileResponse(ROOT / "apps/passenger/index.html")


@app.get("/driver")
def driver():
    return FileResponse(ROOT / "apps/driver/index.html")


@app.api_route("/v1/{role}/{path:path}", methods=["GET", "POST", "PUT"])
async def proxy(request: Request, role: str, path: str):
    origin = next((url for (method, allowed_role, pattern), url in ROUTES.items()
                   if method == request.method and role == allowed_role and re.fullmatch(pattern, path)), None)
    if origin is None:
        raise HTTPException(404, "Unknown route")
    key = request.headers.get("Authorization", "").removeprefix("Bearer ")
    actor = next((name for name, expected in KEYS.items() if equal(key, expected)), None)
    if actor is None or (role == "rider") != actor.startswith("rider-"):
        raise HTTPException(401, "Provide a valid demo key for this role")
    headers = {"X-Atlas-Actor": actor, "X-Atlas-Internal": TOKEN}
    for header in ("Content-Type", "Idempotency-Key"):
        if header in request.headers:
            headers[header] = request.headers[header]
    body = await request.body()
    if len(body) > 8192:
        raise HTTPException(413, "Request too large")
    try:
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            result = await client.request(request.method, f"{origin}/v1/{role}/{path}", headers=headers, content=body)
    except httpx.RequestError as error:
        raise HTTPException(503, "Ride service unavailable") from error
    return Response(result.content, status_code=result.status_code,
                    media_type=result.headers.get("Content-Type", "application/json"))
