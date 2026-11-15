"""In-memory impact store (local dev, tests)."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.impact.models import ImpactAssessment


class InMemoryImpactStore:
    def __init__(self) -> None:
        self._items: list[ImpactAssessment] = []

    def add_many(self, items: Sequence[ImpactAssessment]) -> None:
        self._items.extend(items)

    def by_ticker(self, ticker: str) -> Sequence[ImpactAssessment]:
        return [i for i in self._items if i.ticker == ticker]

    def all(self) -> Sequence[ImpactAssessment]:
        return list(self._items)
