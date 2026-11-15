"""SQLite stores for the reliability module: track records survive restarts."""

from __future__ import annotations

import json
from collections.abc import Sequence

from newsimpact.shared.sqlite import Database
from newsimpact.sources.models import Source


class SqliteTrackedSources:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("tracked_sources")

    def upsert(self, source: Source) -> None:
        self._c.put(source.source_id, source.model_dump_json())

    def get(self, source_id: str) -> Source | None:
        doc = self._c.get(source_id)
        return Source.model_validate_json(doc) if doc else None

    def all(self) -> Sequence[Source]:
        return [Source.model_validate_json(d) for d in self._c.find()]


class SqliteEvidenceStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("evidence")

    def counts(self, source_id: str, topic: str) -> tuple[float, float]:
        doc = self._c.get(f"{source_id}|{topic}")
        supported, refuted = json.loads(doc) if doc else (0.0, 0.0)
        return float(supported), float(refuted)

    def record(self, source_id: str, topic: str, supported: bool, weight: float = 1.0) -> None:
        s, r = self.counts(source_id, topic)
        s, r = (s + weight, r) if supported else (s, r + weight)
        self.replace(source_id, topic, s, r)

    def replace(self, source_id: str, topic: str, supported: float, refuted: float) -> None:
        self._c.put(f"{source_id}|{topic}", json.dumps([supported, refuted]), tag=source_id)
