"""JSON reference files for semantics: the companies we follow and the taxonomy."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from newsimpact.semantics.models import Company, Taxonomy


class JsonEntityResolver:
    """{"companies": [{"ticker", "name", "country", "aliases": [...]}]}"""

    def __init__(self, companies: Sequence[Company]) -> None:
        self._companies = tuple(companies)
        self._aliases = {a.lower(): c.ticker for c in companies for a in c.aliases}
        self._names = [a for c in companies for a in c.aliases]

    @classmethod
    def from_file(cls, path: Path) -> JsonEntityResolver:
        rows = json.loads(path.read_text())["companies"]
        return cls([Company.model_validate(r) for r in rows])

    def resolve(self, name: str) -> str | None:
        return self._aliases.get(name.lower())

    def known_names(self) -> Sequence[str]:
        return list(self._names)

    def companies(self) -> Sequence[Company]:
        return self._companies


def load_taxonomy(path: Path) -> Taxonomy:
    raw = {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}
    return Taxonomy.model_validate(raw)
