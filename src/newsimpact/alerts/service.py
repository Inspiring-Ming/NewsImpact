"""Compare each round's events with the last and notify followers of what changed."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from newsimpact.alerts.logic import changes
from newsimpact.alerts.models import Alert, EventSnapshot
from newsimpact.alerts.ports import AlertState, Notifier

log = logging.getLogger(__name__)


class AlertsService:
    def __init__(self, state: AlertState, notifier: Notifier | None, site_url: str) -> None:
        """notifier None = alerts are worked out and remembered but not sent (no channel set)."""
        self._state = state
        self._notifier = notifier
        self._site = site_url.rstrip("/")

    @property
    def channel(self) -> str:
        return "on" if self._notifier else "off"

    def followed(self) -> set[str]:
        return self._state.followed()

    def follow(self, ticker: str, follow: bool = True) -> None:
        self._state.set_followed(ticker, follow)

    def check(self, events: Sequence[EventSnapshot]) -> list[Alert]:
        """Send the alerts for what changed since the last round; return what was sent."""
        previous = self._state.snapshot()
        self._state.save_snapshot(events)
        if previous is None:  # first round: baseline only
            return []
        sent: list[Alert] = []
        for alert in changes(previous, events, self._state.followed()):
            if self._state.was_sent(alert.key):
                continue
            if self._notifier is not None:
                try:
                    self._notifier.send(alert, self.link(alert.event_id))
                except Exception:
                    log.exception("alert not sent", extra={"kind": alert.kind})
                    continue
            self._state.mark_sent(alert.key)
            sent.append(alert)
        return sent

    def link(self, event_id: str) -> str:
        return f"{self._site}/#/event/{event_id}"

    def test(self) -> None:
        """Send one test message, to check the channel works."""
        if self._notifier is None:
            raise RuntimeError("no alert channel configured")
        self._notifier.send(
            Alert(key="test", kind="new_event", ticker="TEST", event_id="", article_url="",
                  title="NewsImpact alerts are on",
                  text="You will get a message here when something changes for a company you "
                       "follow."),
            self._site,
        )  # fmt: skip
