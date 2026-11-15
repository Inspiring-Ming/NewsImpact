"""Data owned by the reliability module: outlet and claim credibility scores."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from newsimpact.semantics.models import Claim
from newsimpact.shared.events import Event, Model
from newsimpact.sources.models import SourceType


class ReliabilityScore(Model):
    source_id: str
    topic: str = "all"
    score: float = Field(ge=0.0, le=1.0, description="posterior mean P(claim holds up)")
    ci_low: float = Field(ge=0.0, le=1.0)
    ci_high: float = Field(ge=0.0, le=1.0)
    evidence_count: float = Field(ge=0.0)
    prior: float = Field(
        default=0.0, ge=0.0, le=1.0, description="starting estimate for the source type"
    )
    supported: float = Field(default=0.0, ge=0.0, description="reports later confirmed")
    refuted: float = Field(
        default=0.0, ge=0.0, description="reports refuted, or never confirmed (weighted)"
    )
    as_of: datetime
    model_version: str


class ClaimReliability(Model):
    claim_id: str
    source_reliability: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)
    as_of: datetime
    model_version: str


class ClaimsScored(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.claims.scored.v1"
    article_id: str
    source_id: str
    source_type: SourceType = SourceType.UNKNOWN
    published_at: datetime
    source_reliability: ReliabilityScore
    claims: tuple[Claim, ...]
    claim_reliability: tuple[ClaimReliability, ...]


PUBLISHES: tuple[type[Event], ...] = (ClaimsScored,)
