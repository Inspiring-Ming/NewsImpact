"""In-memory AlertState (tests, demo)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from newsimpact.alerts.models import EventSnapshot


class InMemoryAlertState:
    def __init__(self) -> None:
        self._followed: dict[str, set[str]] = defaultdict(set)
        self._snapshot: dict[str, EventSnapshot] | None = None
        self._sent: set[tuple[str, str]] = set()

    def followed(self, user_id: str) -> set[str]:
        return set(self._followed.get(user_id, set()))

    def set_followed(self, user_id: str, ticker: str, follow: bool) -> None:
        (self._followed[user_id].add if follow else self._followed[user_id].discard)(ticker)

    def followers(self) -> Mapping[str, set[str]]:
        return {u: set(t) for u, t in self._followed.items() if t}

    def snapshot(self) -> Mapping[str, EventSnapshot] | None:
        return self._snapshot

    def save_snapshot(self, events: Sequence[EventSnapshot]) -> None:
        self._snapshot = {e.event_id: e for e in events}

    def was_sent(self, user_id: str, key: str) -> bool:
        return (user_id, key) in self._sent

    def mark_sent(self, user_id: str, key: str) -> None:
        self._sent.add((user_id, key))
