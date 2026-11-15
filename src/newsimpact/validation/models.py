"""Data owned by the validation module: checks, conclusions, calibration and provenance."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from newsimpact.market.models import ChannelObservation
from newsimpact.shared.events import Event, Model

DISCLAIMER = "Research evidence for analysis, not investment advice."

ClaimStatus = Literal["confirmed", "corroborated", "single_source"]
Verdict = Literal[
    "consistent", "inconsistent", "not_significant", "pending", "no_evidence", "not_measurable"
]
Confidence = Literal["low", "medium", "high"]
Finding = Literal["supported", "contradicted", "not_significant", "indicative", "no_data"]


class ValidationPolicy(Model):
    """Thresholds for conclusions. Values and reasons: methodology.json "validation"."""

    confirming_origins: int = Field(gt=0)
    corroborating_origins: int = Field(gt=0)
    high_support: float = Field(ge=0, le=1)
    medium_support: float = Field(ge=0, le=1)
    min_events_for_calibration: int = Field(gt=0)
    significance_z: float = Field(gt=0)
    overlap_trading_days: int = Field(ge=0)
    window_quantile: float = Field(gt=0, le=1)
    window_margin: float = Field(ge=1)
    confirmation_days: int = Field(gt=0)
    unconfirmed_weight: float = Field(ge=0, le=1)


class TrackRecord(Model):
    """How often a source's reports were later confirmed by an independent source."""

    source_id: str
    confirmed: int = Field(ge=0, description="reports backed by another independent origin")
    unconfirmed: int = Field(ge=0, description="reports nobody confirmed within the window")


class ClaimCheck(Model):
    """Is the stage's claim backed by independent sources?"""

    status: ClaimStatus
    outlets: tuple[str, ...] = Field(description="listed outlets that reported it")
    origins: tuple[str, ...] = Field(description="independent origins behind those reports")
    authoritative: bool = Field(description="a filing or the company itself confirmed it")
    best_reliability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="chance at least one independent origin is right: 1 - product of (1 - "
                    "best reliability per origin); copies of one origin count once",
    )  # fmt: skip


class DecisionCheck(Model):
    """Did an expected decision show up where the playbook says it would?"""

    actor: str
    decision: str
    channel: str | None
    expected: str
    verdict: Verdict
    evidence: ChannelObservation | None = None


class StageCheck(Model):
    stage: int
    stage_name: str
    published_at: datetime
    claim: ClaimCheck
    decisions: tuple[DecisionCheck, ...]
    overlaps_previous: bool = Field(
        default=False, description="too close to the previous stage to measure separately"
    )


class Provenance(Model):
    """Everything needed to reproduce a result."""

    components: dict[str, str] = Field(description="component -> model/method version")
    reference_data: dict[str, str] = Field(description="reference file -> content hash")


class Assessment(Model):
    storyline_id: str
    ticker: str
    theme: str
    status: str
    stages: tuple[StageCheck, ...]
    combined_reaction: ChannelObservation | None = Field(
        default=None, description="price move over overlapping stages, measured as one event"
    )
    market_support: float | None = Field(
        description="share of measured expectations the market confirmed; None = nothing measured"
    )
    confidence: Confidence
    conclusion: str
    suggestions: tuple[str, ...]
    as_of: datetime
    model_version: str
    provenance: Provenance
    disclaimer: str = DISCLAIMER


# ------------------------------------------------------------ calibration
class StageChannelCalibration(Model):
    """Across all storylines: does this stage move this channel the way the playbook says?"""

    theme: str
    stage_name: str
    channel: str
    expected: str
    n_events: int
    mean_statistic: float | None = Field(description="average per-event z/t statistic")
    cross_sectional_z: float | None = Field(description="BMP (1991) test of that average")
    share_consistent: float | None
    finding: Finding


class WindowCalibration(Model):
    """Across all storylines: how long until the next stage, versus the configured window?"""

    theme: str
    n_gaps: int
    median_days: float | None
    quantile_days: float | None
    configured_days: int
    suggested_days: int | None = Field(description="None until enough gaps are observed")


PUBLISHES: tuple[type[Event], ...] = ()
