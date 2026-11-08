"""DEMO_REDIRECT_URL: send visitors elsewhere without rebuilding, and never break the app doing it.

A submitted URL is fixed once it is submitted. What it points at is not, so this variable exists to
move the audience somewhere else -- another build, another machine, a tunnel -- by setting a value
and restarting, with no code change and no deploy.

The dangerous version of this feature redirects everything. The platform polls /health and /ready to
decide whether the container is alive, so a redirect there reports a healthy app as unhealthy and
takes it down; /version is what the README tells a reader to check to see which commit is running;
and /api is what anything already pointed at this engine depends on. Those are the tests below.
"""
from __future__ import annotations

import pytest

ELSEWHERE = "https://example.test/stand-in"


@pytest.fixture()
def redirected(monkeypatch, seeded):
    client, pulse_id = seeded
    monkeypatch.setenv("DEMO_REDIRECT_URL", ELSEWHERE)
    return client, pulse_id


def test_a_visitor_to_the_page_is_sent_to_the_stand_in(redirected):
    client, _ = redirected
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == f"{ELSEWHERE}/"


def test_the_path_and_query_survive_the_redirect(redirected):
    """A link someone was given has to land on the matching page of the stand-in, not its front
    door, or every deep link in the README breaks the moment this is switched on."""
    client, _ = redirected
    response = client.get("/desk?risk_id=R1043&pulse_id=P-0001", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == (
        f"{ELSEWHERE}/desk?risk_id=R1043&pulse_id=P-0001"
    )


def test_the_redirect_is_never_cached_by_the_browser(redirected):
    """302 and no-store, so switching the variable off actually switches it off. A 301 would be
    cached and would outlive the setting, stranding anyone who visited while it was on."""
    client, _ = redirected
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["cache-control"] == "no-store"


def test_the_healthcheck_still_answers_so_the_container_stays_up(redirected):
    """The one that would take the site down. Coolify polls these; a 302 is not a 200."""
    client, _ = redirected
    for path in ("/health", "/ready"):
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 200, path


def test_version_still_reports_the_commit_being_run(redirected):
    client, _ = redirected
    response = client.get("/version", follow_redirects=False)
    assert response.status_code == 200
    assert "sha" in response.json()


def test_the_api_keeps_answering_while_the_page_is_redirected(redirected):
    client, pulse_id = redirected
    response = client.get(f"/api/pulses/{pulse_id}", follow_redirects=False)
    assert response.status_code == 200
    assert response.json()["id"] == pulse_id


def test_nothing_is_redirected_when_the_variable_is_unset(seeded):
    """The default, and the state every other test in the suite runs under."""
    client, _ = seeded
    assert client.get("/health", follow_redirects=False).status_code == 200
    assert client.get("/", follow_redirects=False).status_code in (200, 404)
