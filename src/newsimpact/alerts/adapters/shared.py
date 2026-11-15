"""Every person's alerts go to the same configured channels (one user, or one team).

Per-person channels (each user's own Discord link or email) replace this with
an adapter that reads them from the user's settings.
"""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.alerts.ports import Notifier


class SharedChannels:
    def __init__(self, notifiers: Sequence[Notifier]) -> None:
        self._notifiers = tuple(notifiers)

    def for_user(self, user_id: str) -> Sequence[Notifier]:
        return self._notifiers
