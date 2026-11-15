"""In-memory TrackedSources and EvidenceStore (local dev, tests)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from newsimpact.sources.models import Source


class InMemoryTrackedSources:
    def __init__(self) -> None:
        self._sources: dict[str, Source] = {}

    def upsert(self, source: Source) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def all(self) -> Sequence[Source]:
        return list(self._sources.values())


class InMemoryEvidenceStore:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str], list[float]] = defaultdict(lambda: [0.0, 0.0])

    def counts(self, source_id: str, topic: str) -> tuple[float, float]:
        supported, refuted = self._counts[(source_id, topic)]
        return supported, refuted

    def record(self, source_id: str, topic: str, supported: bool, weight: float = 1.0) -> None:
        self._counts[(source_id, topic)][0 if supported else 1] += weight
