"""Structured JSON logs to stdout, never files. Never log secrets, tokens or full request bodies."""
from __future__ import annotations
import json
import logging
import sys
from datetime import datetime, timezone

REDACT = {"authorization", "token", "salt", "commitment_salt", "pseudonym_key", "probability"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in getattr(record, "extra_fields", {}).items():
            if key.lower() in REDACT:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure(level: str = "info") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def log(logger: logging.Logger, level: str, msg: str, **fields) -> None:
    logger.log(getattr(logging, level.upper(), logging.INFO), msg, extra={"extra_fields": fields})
