"""Shared test helpers.

`commit_answer` exists because v3.4 split answering in two: `POST /e/{token}/answer` drafts and
`POST /e/{token}/confirm` commits. A test that posts an answer and expects a commitment back is
testing the version of the card where a link click could answer for you, so every test goes
through both steps the way the card does.
"""
from __future__ import annotations

DEFAULT = {"mask": "pseudonym", "stance": "estimate", "likelihood_word": "likely"}


def draft_answer(client, token: str, **body):
    """Step one. Returns the raw response, so a test can assert on a refusal."""
    return client.post(f"/api/e/{token}/answer", json={**DEFAULT, **body})


def commit_answer(client, token: str, **body):
    """Both steps. Returns the confirmation response."""
    drafted = draft_answer(client, token, **body)
    assert drafted.status_code == 200, drafted.text
    payload = drafted.json()
    assert payload["committed"] is False, "a draft must not commit anything"
    extras = {key: body[key] for key in ("credential", "zk_proof") if key in body}
    return client.post(f"/api/e/{token}/confirm",
                       json={"confirm_token": payload["confirm_token"], **extras})


def open_token(store, pulse_id: str) -> str:
    """A magic link for this pulse that has not answered yet."""
    return next(token for token, (pulse, expert) in store.tokens.items()
                if pulse == pulse_id and not store.answered(pulse, expert))


def reveal_now(client, pulse_id: str):
    """Reveal a round whose deadline is still 24 hours away, which is every seeded round.

    `force` is the recorded analyst override: the response says `revealed_reason:
    analyst_before_deadline`, so nothing in a test can accidentally assert that the deadline
    mechanism fired when it did not."""
    return client.post(f"/api/pulses/{pulse_id}/reveal", json={"force": True})
