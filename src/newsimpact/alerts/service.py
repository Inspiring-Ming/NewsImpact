"""Compare each round's events with the last and tell each follower what changed."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from newsimpact.alerts.logic import changes
from newsimpact.alerts.models import Alert, EventSnapshot
from newsimpact.alerts.ports import AlertState, Channels

log = logging.getLogger(__name__)


class AlertsService:
    def __init__(self, state: AlertState, channels: Channels, site_url: str) -> None:
        """No channels for a user = their alerts are worked out and remembered, not sent."""
        self._state = state
        self._channels = channels
        self._site = site_url.rstrip("/")

    def channel(self, user_id: str) -> str:
        return "on" if self._channels.for_user(user_id) else "off"

    def followed(self, user_id: str) -> set[str]:
        return self._state.followed(user_id)

    def follow(self, user_id: str, ticker: str, follow: bool = True) -> None:
        self._state.set_followed(user_id, ticker, follow)

    def check(self, events: Sequence[EventSnapshot]) -> list[Alert]:
        """Send each follower the alerts for what changed since the last round."""
        previous = self._state.snapshot()
        self._state.save_snapshot(events)
        if previous is None:  # first round: baseline only
            return []
        sent: list[Alert] = []
        for user_id, tickers in self._state.followers().items():
            notifiers = self._channels.for_user(user_id)
            for alert in changes(previous, events, tickers):
                if self._state.was_sent(user_id, alert.key):
                    continue
                delivered = 0
                for notifier in notifiers:
                    try:
                        notifier.send(alert, self.link(alert.event_id))
                        delivered += 1
                    except Exception:
                        log.exception("alert not sent", extra={"kind": alert.kind})
                if notifiers and not delivered:
                    continue  # every channel failed: try again next round
                self._state.mark_sent(user_id, alert.key)
                sent.append(alert)
        return sent

    def link(self, event_id: str) -> str:
        return f"{self._site}/#/event/{event_id}"

    def test(self, user_id: str) -> None:
        """Send one test message to the user's channels, to check they work."""
        notifiers = self._channels.for_user(user_id)
        if not notifiers:
            raise RuntimeError("no alert channel configured")
        alert = Alert(key="test", kind="new_event", ticker="TEST", event_id="", article_url="",
                      title="NewsImpact alerts are on",
                      text="You will get a message here when something changes for a company "
                           "you follow.")  # fmt: skip
        for notifier in notifiers:
            notifier.send(alert, self._site)
