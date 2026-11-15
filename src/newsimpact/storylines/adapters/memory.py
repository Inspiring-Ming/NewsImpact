"""In-memory StorylineStore (demo, tests)."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.storylines.models import Storyline


class InMemoryStorylineStore:
    def __init__(self) -> None:
        self._by_id: dict[str, Storyline] = {}

    def latest_for(self, ticker: str, theme: str) -> Storyline | None:
        candidates = [s for s in self._by_id.values() if s.ticker == ticker and s.theme == theme]
        return max(candidates, key=lambda s: s.updated_at, default=None)

    def save(self, storyline: Storyline) -> None:
        self._by_id[storyline.storyline_id] = storyline

    def get(self, storyline_id: str) -> Storyline | None:
        return self._by_id.get(storyline_id)

    def all(self) -> Sequence[Storyline]:
        return sorted(self._by_id.values(), key=lambda s: s.updated_at, reverse=True)
