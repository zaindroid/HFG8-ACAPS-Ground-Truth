"""Runtime settings. Fail loudly at startup if a required secret is missing -- never silently default
(zorc hard rule). Local development reads engine/.env.example values via your shell or `make dev-env`."""
from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime, timezone

# When this process started. True by construction, which is the point: it is the one field in
# /version that cannot go stale, because nothing sets it by hand.
STARTED_AT = datetime.now(timezone.utc).isoformat(timespec="seconds")


class MissingSetting(RuntimeError):
    pass


def _required(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise MissingSetting(
            f"{name} is not set. This process refuses to start without it. "
            f"In development: copy engine/.env.example and export it (see `make dev`). "
            f"In production: declare it in app.yaml's env: section so zorc generates it."
        )
    return v


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    commitment_salt: str
    pseudonym_key: str
    git_sha: str
    built_at: str
    started_at: str
    branch: str
    k_min: int
    asked_by: str

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"


def load() -> Settings:
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        commitment_salt=_required("COMMITMENT_SALT"),
        pseudonym_key=_required("PSEUDONYM_KEY"),
        # The platform's own answer first. Coolify injects SOURCE_COMMIT on every build, so the
        # sha corrects itself on each deploy; GIT_SHA is set once by `deploy` and a later
        # `redeploy` reuses the old value, which is how /version came to report a commit that had
        # not been running for an hour. A field that has to be remembered will eventually lie.
        git_sha=(os.environ.get("SOURCE_COMMIT", "").strip()[:7]
                 or os.environ.get("GIT_SHA", "").strip()
                 or "unknown"),
        built_at=os.environ.get("BUILT_AT", "").strip() or STARTED_AT,
        started_at=STARTED_AT,
        branch=os.environ.get("COOLIFY_BRANCH", "").strip() or "unknown",
        k_min=int(os.environ.get("K_MIN", "5")),
        # Who the card says is asking. The card is meant to read like a note from a colleague
        # (section 8), and a note from nobody is a survey.
        asked_by=os.environ.get("ASKED_BY", "Alex, ACAPS Risk Radar"),
    )
