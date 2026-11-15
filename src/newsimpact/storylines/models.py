"""Data owned by the storylines module: stories, their stages, and playbooks.

Example chain: public apology -> leader steps down -> successor named.
Each stage carries the decisions market participants typically make and
the market channel through which those decisions show up.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import Field

from newsimpact.shared.events import Event, Model
from newsimpact.sources.models import SourceType


class MarketChannel(StrEnum):
    PRICE = "price"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    LIQUIDITY = "liquidity"
    ANALYST_REVISIONS = "analyst_revisions"
    CREDIT_SPREADS = "credit_spreads"
    PEER_SPILLOVER = "peer_spillover"
    CONFIDENCE = "confidence"


class ExpectedDecision(Model):
    actor: str = Field(description="e.g. institutional_investors, sell_side_analysts, board")
    decision: str
    market_channel: MarketChannel | None = Field(
        default=None, description="None = real-economy decision, not directly a market metric"
    )
    expected_direction: Literal["up", "down", "uncertain"] = "uncertain"
    horizon: Literal["intraday", "days", "weeks", "months"] = "days"


class StorylineStatus(StrEnum):
    DEVELOPING = "developing"
    ESCALATING = "escalating"
    RESOLVED = "resolved"


class Report(Model):
    """One outlet reporting a stage. Several reports = corroboration."""

    source_id: str
    source_type: SourceType
    article_id: str
    published_at: datetime
    claim_reliability: float = Field(ge=0.0, le=1.0)
    origin: str = Field(description="independent origin: the outlet itself, a cited outlet, "
                        "the company, a filing, or the outlet it copied")  # fmt: skip
    attribution_kind: str = "own_reporting"


class StorylineEvent(Model):
    """One stage of a storyline, with every outlet that reported it."""

    claim_id: str = Field(description="claim of the first report")
    article_id: str
    event_type: str
    stage: int
    stage_name: str
    published_at: datetime = Field(description="first report")
    claim_reliability: float = Field(ge=0.0, le=1.0, description="best single report")
    summary: str
    tone: float = Field(default=0.0, ge=-1.0, le=1.0, description="sentiment of the first report")
    is_rumour: bool = Field(default=False, description="hedged or 'sources say' wording")
    reports: tuple[Report, ...] = ()


class Storyline(Model):
    storyline_id: str
    ticker: str
    entity_name: str
    theme: str
    status: StorylineStatus
    events: tuple[StorylineEvent, ...]
    current_stage: int
    max_stage: int
    opened_at: datetime
    updated_at: datetime
    model_version: str


class FollowUpRequest(Model):
    """Asks the sources module to search for the next stages of a storyline."""

    entity_name: str
    terms: tuple[str, ...]
    since: datetime
    until: datetime


class StorylineUpdated(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.storyline.updated.v1"
    storyline: Storyline
    latest: StorylineEvent
    is_new: bool
    escalated: bool
    corroborated: bool = Field(default=False, description="another outlet reported a known stage")
    expected_decisions: tuple[ExpectedDecision, ...]
    follow_up: FollowUpRequest | None = None


# ---------------------------------------------------------------- playbooks
class PlaybookStage(Model):
    name: str
    title: str = Field(default="", description="plain-English name shown to people")
    event_types: tuple[str, ...]
    follow_up_terms: tuple[str, ...] = ()
    resolves: bool = False
    decisions: tuple[ExpectedDecision, ...] = ()


class Playbook(Model):
    """The typical progression of one kind of story (reference data, not code)."""

    theme: str
    title: str = Field(default="", description="plain-English name shown to people")
    description: str
    link_window_days: int = Field(gt=0, description="how long a story stays open for new stages")
    window_basis: str = Field(
        description="where the window comes from: judgment prior | calibrated"
    )
    window_why: str
    triggers: tuple[str, ...]
    stages: tuple[PlaybookStage, ...]

    def stage_of(self, event_type: str) -> int | None:
        return next((i for i, s in enumerate(self.stages) if event_type in s.event_types), None)

    def event_types(self) -> set[str]:
        return set(self.triggers) | {t for s in self.stages for t in s.event_types}

    def terms_after(self, stage: int) -> tuple[str, ...]:
        """Search terms that would signal any later stage."""
        return tuple(t for s in self.stages[stage + 1 :] for t in s.follow_up_terms)


PUBLISHES: tuple[type[Event], ...] = (StorylineUpdated,)
