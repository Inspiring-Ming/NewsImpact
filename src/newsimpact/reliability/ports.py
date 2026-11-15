"""What the reliability module needs to persist (implemented in adapters/)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from newsimpact.sources.models import Source


class TrackedSources(Protocol):
    """The outlets whose reliability we track, built from SourceRegistered events."""

    def upsert(self, source: Source) -> None: ...
    def get(self, source_id: str) -> Source | None: ...
    def all(self) -> Sequence[Source]: ...


class EvidenceStore(Protocol):
    """Track record: how many of an outlet's claims held up vs. failed."""

    def counts(self, source_id: str, topic: str) -> tuple[float, float]:
        """Return (supported, refuted) evidence weights."""
        ...

    def record(self, source_id: str, topic: str, supported: bool, weight: float = 1.0) -> None: ...

    def replace(self, source_id: str, topic: str, supported: float, refuted: float) -> None:
        """Overwrite the counts (for records recomputed from scratch each round)."""
        ...
