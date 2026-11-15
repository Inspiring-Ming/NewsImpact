"""Event bus: how modules talk without importing each other.

`EventBus` is the interface; `InMemoryEventBus` runs everything in one
process. Cloud versions (SNS/SQS, EventBridge) implement the same interface
and are selected by NI_EVENT_BUS (app/wiring/plugins.py EVENT_BUSES).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Protocol

from newsimpact.shared.events import EventEnvelope

log = logging.getLogger(__name__)

EventHandler = Callable[[EventEnvelope], None]


class EventBus(Protocol):
    def publish(self, event: EventEnvelope) -> None: ...
    def subscribe(self, event_type: str, handler: EventHandler) -> None: ...


class InMemoryEventBus:
    """Synchronous pub/sub. A failing handler never breaks other handlers;
    the event goes to `dead_letters`, mirroring an SQS dead-letter queue."""

    def __init__(self) -> None:
        self._subs: dict[str, list[EventHandler]] = defaultdict(list)
        self.published: list[EventEnvelope] = []
        self.dead_letters: list[tuple[EventEnvelope, str]] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subs[event_type].append(handler)

    def publish(self, event: EventEnvelope) -> None:
        self.published.append(event)
        for handler in self._subs.get(event.type, []):
            try:
                handler(event)
            except Exception as exc:
                log.exception("handler failed", extra={"event_type": event.type})
                self.dead_letters.append((event, repr(exc)))
