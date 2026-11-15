"""What the storylines module needs: playbooks and a storyline store."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from newsimpact.storylines.models import Playbook, Storyline


class PlaybookCatalog(Protocol):
    late_report_days: int  # see playbooks.json late_report_why

    def playbooks(self) -> Sequence[Playbook]: ...


class StorylineStore(Protocol):
    def latest_for(self, ticker: str, theme: str) -> Storyline | None:
        """Most recent storyline for this ticker and theme (any status)."""
        ...

    def save(self, storyline: Storyline) -> None: ...
    def get(self, storyline_id: str) -> Storyline | None: ...
    def all(self) -> Sequence[Storyline]: ...
