"""SQLite ImpactStore: impact assessments survive restarts."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.impact.models import ImpactAssessment
from newsimpact.shared.sqlite import Database


class SqliteImpactStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("impacts")

    def add_many(self, items: Sequence[ImpactAssessment]) -> None:
        for i in items:
            self._c.put(f"{i.claim_id}|{i.ticker}|{i.relation}", i.model_dump_json(),
                        tag=i.ticker, at=i.as_of.isoformat())  # fmt: skip

    def by_ticker(self, ticker: str) -> Sequence[ImpactAssessment]:
        return [ImpactAssessment.model_validate_json(d) for d in self._c.find(ticker)]

    def all(self) -> Sequence[ImpactAssessment]:
        return [ImpactAssessment.model_validate_json(d) for d in self._c.find()]
