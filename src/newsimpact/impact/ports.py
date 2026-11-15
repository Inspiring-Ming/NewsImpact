"""What the impact module needs: a company relationship graph and a place to store results."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from newsimpact.impact.models import ImpactAssessment


class RelationshipGraph(Protocol):
    def related(self, ticker: str) -> Sequence[tuple[str, str, float]]:
        """(related_ticker, relation, propagation_weight); negative = opposite direction."""
        ...


class ImpactStore(Protocol):
    def add_many(self, items: Sequence[ImpactAssessment]) -> None: ...
    def by_ticker(self, ticker: str) -> Sequence[ImpactAssessment]: ...
    def all(self) -> Sequence[ImpactAssessment]: ...
