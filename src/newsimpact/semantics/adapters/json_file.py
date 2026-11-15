"""JSON reference files for semantics: entity aliases and the taxonomy."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from newsimpact.semantics.models import Taxonomy


class JsonEntityResolver:
    """{"aliases": {"Name": "TICKER"}}"""

    def __init__(self, aliases: dict[str, str]) -> None:
        self._aliases = {k.lower(): v for k, v in aliases.items()}
        self._names = list(aliases)

    @classmethod
    def from_file(cls, path: Path) -> JsonEntityResolver:
        return cls(json.loads(path.read_text())["aliases"])

    def resolve(self, name: str) -> str | None:
        return self._aliases.get(name.lower())

    def known_names(self) -> Sequence[str]:
        return list(self._names)


def load_taxonomy(path: Path) -> Taxonomy:
    raw = {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}
    return Taxonomy.model_validate(raw)
