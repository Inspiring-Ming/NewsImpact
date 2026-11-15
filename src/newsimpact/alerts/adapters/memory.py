"""In-memory AlertState (tests, demo)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from newsimpact.alerts.models import EventSnapshot


class InMemoryAlertState:
    def __init__(self) -> None:
        self._followed: set[str] = set()
        self._snapshot: dict[str, EventSnapshot] | None = None
        self._sent: set[str] = set()

    def followed(self) -> set[str]:
        return set(self._followed)

    def set_followed(self, ticker: str, follow: bool) -> None:
        (self._followed.add if follow else self._followed.discard)(ticker)

    def snapshot(self) -> Mapping[str, EventSnapshot] | None:
        return self._snapshot

    def save_snapshot(self, events: Sequence[EventSnapshot]) -> None:
        self._snapshot = {e.event_id: e for e in events}

    def was_sent(self, key: str) -> bool:
        return key in self._sent

    def mark_sent(self, key: str) -> None:
        self._sent.add(key)
