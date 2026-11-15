"""Data owned by the impact module: expected effect of claims on companies."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from newsimpact.shared.events import Event, Model


class ImpactAssessment(Model):
    claim_id: str
    ticker: str
    aspect: str = Field(description="business aspect from the taxonomy")
    relation: str = Field(description="direct | supplier | customer | competitor | sector")
    direction: float = Field(ge=-1.0, le=1.0, description="expected sign and strength")
    confidence: float = Field(ge=0.0, le=1.0, description="reliability-weighted")
    as_of: datetime
    model_version: str


class ImpactAssessed(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.impact.assessed.v1"
    article_id: str
    assessments: tuple[ImpactAssessment, ...]


PUBLISHES: tuple[type[Event], ...] = (ImpactAssessed,)
