"""Test environment. The engine refuses to start without its secrets, so the suite supplies
development values before anything imports the app."""
from __future__ import annotations
import os

os.environ.setdefault("COMMITMENT_SALT", "test-salt")
os.environ.setdefault("PSEUDONYM_KEY", "test-pseudonym-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "warning")
os.environ.setdefault("SEED_ON_START", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def seeded():
    """A client over a freshly seeded store: synthetic panel, one pulse, eight sealed answers."""
    from engine.api import ALERTS, STORE, SETTINGS, app
    from engine.seeding import seed_demo

    pulse_id = seed_demo(STORE, SETTINGS)
    # The alert store is module-global too. Without this, a dismissed or approved event from an
    # earlier test is still dismissed or approved in the next one.
    ALERTS.reset()
    with TestClient(app) as client:
        yield client, pulse_id


@pytest.fixture()
def empty():
    """A client over an empty store, for the paths that must refuse to do anything."""
    from engine.api import ALERTS, STORE, app

    STORE.reset()
    ALERTS.reset()
    with TestClient(app) as client:
        yield client
