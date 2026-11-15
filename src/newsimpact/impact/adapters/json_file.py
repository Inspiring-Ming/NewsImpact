"""RelationshipGraph from JSON: {"relations": {"TICKER": [[related, relation, weight]]}}."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path


class JsonRelationshipGraph:
    def __init__(self, relations: dict[str, list[tuple[str, str, float]]]) -> None:
        self._relations = relations

    @classmethod
    def from_file(cls, path: Path) -> JsonRelationshipGraph:
        raw = json.loads(path.read_text())["relations"]
        return cls({t: [(r[0], r[1], float(r[2])) for r in rels] for t, rels in raw.items()})

    def related(self, ticker: str) -> Sequence[tuple[str, str, float]]:
        return self._relations.get(ticker, [])
