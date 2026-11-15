"""In-memory AssessmentStore (demo, tests)."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.validation.models import Assessment


class InMemoryAssessmentStore:
    def __init__(self) -> None:
        self._history: dict[str, list[Assessment]] = {}

    def add(self, assessment: Assessment) -> None:
        self._history.setdefault(assessment.storyline_id, []).append(assessment)

    def latest(self, storyline_id: str) -> Assessment | None:
        items = self._history.get(storyline_id)
        return items[-1] if items else None

    def latest_all(self) -> Sequence[Assessment]:
        return [items[-1] for items in self._history.values() if items]
