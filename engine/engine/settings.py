"""Runtime settings. Fail loudly at startup if a required secret is missing -- never silently default
(zorc hard rule). Local development reads engine/.env.example values via your shell or `make dev-env`."""
from __future__ import annotations
import os
from dataclasses import dataclass


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
    k_min: int

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"


def load() -> Settings:
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        commitment_salt=_required("COMMITMENT_SALT"),
        pseudonym_key=_required("PSEUDONYM_KEY"),
        git_sha=os.environ.get("GIT_SHA", "unknown"),
        built_at=os.environ.get("BUILT_AT", "unknown"),
        k_min=int(os.environ.get("K_MIN", "5")),
    )
