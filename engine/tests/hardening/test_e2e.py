"""End-to-end answer encryption (hardening/e2e.py): the routes open an envelope and carry on as with
a plain body, refuse one that was altered or sealed for another link or route, and open what the
browser module (ui/src/e2e.ts) actually produces."""
from __future__ import annotations
import base64
import json
from pathlib import Path

import pytest

from engine.hardening import e2e
from helpers import DEFAULT, open_token

VECTOR = Path(__file__).resolve().parent / "vectors" / "e2e_browser_vector.json"


def _sealed(client, body: dict, token: str, route: str) -> dict:
    published = client.get("/api/answer-key").json()
    return e2e.seal(body, token, e2e.ROUTES[route], published)


def test_the_answer_key_is_published_and_stable(seeded):
    client, _ = seeded
    key = client.get("/api/answer-key").json()
    assert key["enabled"] is True and key["v"] == 1
    assert key["suite"].startswith("ML-KEM-768 + X25519")
    assert len(base64.b64decode(key["ml_kem_768_pub"])) == 1184
    assert len(base64.b64decode(key["x25519_pub"])) == 32
    # Derived from COMMITTEE_KEY, so the same on every call and across restarts.
    assert client.get("/api/answer-key").json()["kid"] == key["kid"] == e2e.key_id()


def test_draft_confirm_and_correct_round_trip_encrypted(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    drafted = client.post(f"/api/e/{token}/answer",
                          json=_sealed(client, {**DEFAULT, "probability": 0.7}, token, "draft"))
    assert drafted.status_code == 200, drafted.text
    assert drafted.json()["probability_used"] == 0.7
    confirmed = client.post(f"/api/e/{token}/confirm", json=_sealed(
        client, {"confirm_token": drafted.json()["confirm_token"]}, token, "confirm"))
    assert confirmed.status_code == 201, confirmed.text
    corrected = client.put(f"/api/e/{token}/answer", json=_sealed(
        client, {**DEFAULT, "likelihood_word": "unlikely"}, token, "correct"))
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["version"] == 2


def test_a_tampered_ciphertext_is_refused(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    for field in ("ct", "kem_ct", "x25519_pub", "nonce"):
        sealed = _sealed(client, DEFAULT, token, "draft")
        raw = bytearray(base64.b64decode(sealed["e2e"][field]))
        raw[len(raw) // 2] ^= 0x01
        sealed["e2e"][field] = base64.b64encode(bytes(raw)).decode()
        refused = client.post(f"/api/e/{token}/answer", json=sealed)
        assert refused.status_code == 400, (field, refused.text)
    # Nothing was drafted from the refused envelopes, so the untouched one still goes through.
    assert client.post(f"/api/e/{token}/answer",
                       json=_sealed(client, DEFAULT, token, "draft")).status_code == 200


def test_an_envelope_sealed_for_another_link_or_route_is_refused(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    other = next(t for t, (p, e) in STORE.tokens.items()
                 if p == pulse_id and t != token and not STORE.answered(p, e))
    for_other = _sealed(client, DEFAULT, other, "draft")
    refused = client.post(f"/api/e/{token}/answer", json=for_other)
    assert refused.status_code == 400
    assert "another link or route" in refused.json()["detail"]
    # Sealed for this link, but for the correction route.
    wrong_route = _sealed(client, DEFAULT, token, "correct")
    assert client.post(f"/api/e/{token}/answer", json=wrong_route).status_code == 400


def test_malformed_envelopes_are_refused_not_crashed_on(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    good = _sealed(client, DEFAULT, token, "draft")
    cases = [
        {"e2e": "nope"},
        {"e2e": {**good["e2e"], "v": 2}},
        {"e2e": {**good["e2e"], "kid": "0" * 16}},
        {"e2e": {**good["e2e"], "ct": "***"}},
        {"e2e": {**good["e2e"], "nonce": base64.b64encode(b"short").decode()}},
        {**good, "mask": "known"},
    ]
    for case in cases:
        assert client.post(f"/api/e/{token}/answer", json=case).status_code == 400, case


def test_a_plain_body_is_still_accepted(seeded):
    client, pulse_id = seeded
    from engine.api import STORE

    token = open_token(STORE, pulse_id)
    assert client.post(f"/api/e/{token}/answer", json=DEFAULT).status_code == 200


def test_the_flag_turns_the_card_off_but_the_engine_still_opens_envelopes(seeded, monkeypatch):
    client, pulse_id = seeded
    from engine.api import STORE

    monkeypatch.setenv("FF_E2E", "off")
    assert client.get("/api/answer-key").json()["enabled"] is False
    token = open_token(STORE, pulse_id)
    assert client.post(f"/api/e/{token}/answer",
                       json=_sealed(client, DEFAULT, token, "draft")).status_code == 200


def test_an_envelope_from_the_browser_module_opens_in_python(monkeypatch):
    """The interoperability check: @noble/post-quantum's ML-KEM-768 ciphertext, decapsulated by
    kyber_py, and the rest of the envelope built by ui/src/e2e.ts. Regenerate with
    ui/scripts/make-e2e-vector.ts."""
    vector = json.loads(VECTOR.read_text(encoding="utf-8"))
    monkeypatch.setenv("COMMITTEE_KEY", vector["committee_key"])
    assert e2e.key_id() == vector["kid"]
    route = e2e.ROUTES[vector["route"]]
    assert e2e.open_body(vector["envelope"], vector["token"], route) == vector["body"]
    with pytest.raises(e2e.EnvelopeError):
        e2e.open_body(vector["envelope"], "another-token", route)
    with pytest.raises(e2e.EnvelopeError):
        e2e.open_body(vector["envelope"], vector["token"], e2e.ROUTES["confirm"])
