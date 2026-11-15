"""Text normalisation and stable ids, used by every news connector."""

from __future__ import annotations

import hashlib
import re
import unicodedata

_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return _WS.sub(" ", text).strip()


def content_hash(title: str, body: str) -> str:
    return hashlib.sha256(normalise(f"{title}\n{body}").encode()).hexdigest()


def stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
