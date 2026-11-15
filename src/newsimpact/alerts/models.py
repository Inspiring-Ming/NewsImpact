"""What alerts are about: a small snapshot of each event, and the alert itself."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from newsimpact.shared.events import Model

AlertKind = Literal["new_event", "confirmed", "unusual_move", "new_update"]


class EventSnapshot(Model):
    """The facts about one event that are worth an alert when they change."""

    event_id: str
    ticker: str
    company: str
    event_type: str
    confirmed: bool
    updates: int
    latest_update: str = Field(description="title of the latest update, e.g. 'Leader steps down'")
    headline: str
    article_url: str
    stock_move: float | None = Field(description="stock return minus its index, once measured")
    unusual: bool
    index_name: str


class Alert(Model):
    key: str = Field(description="unique per change, so the same alert is never sent twice")
    kind: AlertKind
    ticker: str
    title: str
    text: str
    article_url: str
    event_id: str
