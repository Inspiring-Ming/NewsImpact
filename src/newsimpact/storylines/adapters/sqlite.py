"""SQLite StorylineStore: open storylines survive restarts."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.shared.sqlite import Database
from newsimpact.storylines.models import Storyline


class SqliteStorylineStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("storylines")

    def latest_for(self, ticker: str, theme: str) -> Storyline | None:
        storylines = [Storyline.model_validate_json(d) for d in self._c.find(f"{ticker}|{theme}")]
        return max(storylines, key=lambda s: s.updated_at, default=None)

    def save(self, storyline: Storyline) -> None:
        self._c.put(storyline.storyline_id, storyline.model_dump_json(),
                    tag=f"{storyline.ticker}|{storyline.theme}",
                    at=storyline.updated_at.isoformat())  # fmt: skip

    def get(self, storyline_id: str) -> Storyline | None:
        doc = self._c.get(storyline_id)
        return Storyline.model_validate_json(doc) if doc else None

    def all(self) -> Sequence[Storyline]:
        return [Storyline.model_validate_json(d) for d in self._c.find(newest_first=True)]
