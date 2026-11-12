"""Shared fixtures for the app-building task tests.

The implementation under test is chosen with the APP_TASKS_IMPL environment variable:
  starter   (default) python_lab/app_tasks/starter.py   - your work
  solution            python_lab/app_tasks/solution.py  - the reference
  <path>              any other .py file with the same functions
grade.py sets this for you.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[2]            # python_lab/
TASKS = LAB / "app_tasks"
sys.path.insert(0, str(LAB))
import app_integration as ai  # noqa: E402


def _load_impl():
    choice = os.environ.get("APP_TASKS_IMPL", "starter")
    path = TASKS / f"{choice}.py" if choice in ("starter", "solution") else Path(choice).resolve()
    spec = importlib.util.spec_from_file_location(f"app_tasks_impl_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IMPL = _load_impl()


@pytest.fixture
def impl():
    return IMPL


@pytest.fixture
def make_app():
    """make_app(drivers=3, rides=0, ...) -> a running App; all are closed after the test."""
    apps = []

    def factory(**options):
        options.setdefault("drivers", 3)
        app = ai.App(**options)
        apps.append(app)
        return app

    yield factory
    for app in apps:
        app.close()


class FakeClock:
    """A clock the test controls: clock() returns now; clock.advance(seconds)."""

    def __init__(self, start=1_000.0):
        self.now = float(start)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture
def clock():
    return FakeClock()


GOOD_RIDE = {"passenger": "Aoife", "pickup": "UCC", "destination": "Cork Airport", "distance_km": 5.8}


def book(app, **changes):
    """POST a ride directly to the API (bypassing the screen) and return the Response."""
    return app.client.post("/api/rides", {**GOOD_RIDE, **changes})


def set_status(app, ride_id, status, driver_id=None):
    """Put a ride straight into a state (test set-up only - bypasses the API)."""
    with app.db.lock:
        app.db.conn.execute("UPDATE rides SET status = ?, driver_id = COALESCE(?, driver_id) WHERE id = ?",
                            (status, driver_id, ride_id))
