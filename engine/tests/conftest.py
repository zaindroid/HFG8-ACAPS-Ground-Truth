"""Test environment. The engine refuses to start without its secrets, so the suite supplies
development values before anything imports the app."""
from __future__ import annotations
import os
import sys
from pathlib import Path

# So `from helpers import ...` works however pytest was invoked. tests/ is not a package (there
# is no __init__.py) and pytest's rootdir insertion puts the repo on the path, not this folder.
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("COMMITMENT_SALT", "test-salt")
os.environ.setdefault("PSEUDONYM_KEY", "test-pseudonym-key")
os.environ.setdefault("COMMITTEE_KEY", "test-committee-key")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "warning")
os.environ.setdefault("SEED_ON_START", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def seeded():
    """A client over a freshly seeded store: synthetic panel, one pulse, eight sealed answers."""
    from engine.api import ALERTS, HARD, REACH, STORE, SETTINGS, app
    from engine.seeding import seed_contacts, seed_demo

    from engine.api import REPORTS_OFF
    REPORTS_OFF.clear()
    HARD.reset()
    pulse_id = seed_demo(STORE, SETTINGS)
    seed_contacts(REACH, STORE)
    # The alert store is module-global too. Without this, a dismissed or approved event from an
    # earlier test is still dismissed or approved in the next one.
    ALERTS.reset()
    with TestClient(app) as client:
        yield client, pulse_id


@pytest.fixture()
def empty():
    """A client over an empty store, for the paths that must refuse to do anything."""
    from engine.api import ALERTS, HARD, REACH, STORE, app

    STORE.reset()
    ALERTS.reset()
    HARD.reset()
    REACH.reset()
    with TestClient(app) as client:
        yield client
