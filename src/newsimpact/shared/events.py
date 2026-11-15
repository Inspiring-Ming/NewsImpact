"""Base classes for module data and events, plus the event envelope.

Every module's `models.py` builds on `Model` (immutable data) and `Event`
(something that happened, announced on the bus). The envelope uses CloudEvents
1.0 attribute names so the same events can later travel over SNS/SQS,
EventBridge or Kafka unchanged (docs/adr/0003).

Change rules for events: additive only within a version; a breaking change
gets a new `...vN` event type.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    """Immutable data that rejects unknown fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    specversion: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str = Field(description="publishing module, e.g. /sources")
    type: str
    time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    datacontenttype: str = "application/json"
    tenant_id: str | None = Field(default=None, description="client tenant (multi-tenant ready)")
    correlation_id: str | None = Field(default=None, description="traces one article end-to-end")
    data: dict[str, Any]


class Event(Model):
    """Something a module announces. Subclasses set EVENT_TYPE = 'newsimpact.<x>.<verb>.v1'."""

    EVENT_TYPE: ClassVar[str]

    def to_envelope(
        self, source: str, correlation_id: str | None = None, tenant_id: str | None = None
    ) -> EventEnvelope:
        return EventEnvelope(
            source=source,
            type=self.EVENT_TYPE,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            data=self.model_dump(mode="json"),
        )

    def follow(self, source: str, cause: EventEnvelope) -> EventEnvelope:
        """Envelope for an event caused by `cause`, keeping trace and tenant."""
        return self.to_envelope(source, cause.correlation_id, cause.tenant_id)
