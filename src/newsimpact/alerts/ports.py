"""What the alerts module needs: where to send alerts, and somewhere to remember."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from newsimpact.alerts.models import Alert, EventSnapshot


class Notifier(Protocol):
    def send(self, alert: Alert, event_link: str) -> None: ...


class Channels(Protocol):
    """Where each person's alerts go (their Discord, their email...)."""

    def for_user(self, user_id: str) -> Sequence[Notifier]: ...


class AlertState(Protocol):
    """Per person: followed companies and alerts already sent. Shared: the last snapshot."""

    def followed(self, user_id: str) -> set[str]: ...
    def set_followed(self, user_id: str, ticker: str, follow: bool) -> None: ...
    def followers(self) -> Mapping[str, set[str]]:
        """user_id -> followed tickers, for everyone who follows something."""
        ...

    def snapshot(self) -> Mapping[str, EventSnapshot] | None: ...
    def save_snapshot(self, events: Sequence[EventSnapshot]) -> None: ...
    def was_sent(self, user_id: str, key: str) -> bool: ...
    def mark_sent(self, user_id: str, key: str) -> None: ...
