"""JSON logging, indexable by CloudWatch or any log platform.

Secrets never reach the logs: some vendors take the key in the URL (EODHD's
api_token) or are the URL (a Discord webhook), and the HTTP client logs every
request URL, so every line is redacted before it is written.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message"}


_SECRETS = (
    (re.compile(r"((?:api_token|apikey|api_key|key|token)=)[^&\s\"']+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(/api/webhooks/)[^\s\"']+"), r"\1***"),
)


def redact(text: str) -> str:
    for pattern, replacement in _SECRETS:
        text = pattern.sub(replacement, text)
    return text


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update({k: v for k, v in record.__dict__.items() if k not in _RESERVED})
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return redact(json.dumps(payload, default=str))


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
