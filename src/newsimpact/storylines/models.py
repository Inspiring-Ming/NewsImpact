"""Data owned by the storylines module: storylines, their stages, and playbooks.

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
    event_type: str = Field(default="", description="what this report claimed, when a stage "
                            "accepts several event types (results: better or worse)")  # fmt: skip


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
    readings: dict[str, str] = Field(
        default_factory=dict,
        description="event type -> what it says, for a stage that can read either way",
    )
    follow_up_terms: tuple[str, ...] = ()
    resolves: bool = False
    decisions: tuple[ExpectedDecision, ...] = ()


class ResearchFinding(Model):
    """A published finding on how markets usually react, with its source."""

    finding: str
    source: str = Field(description="authors (year), journal")


class Expectation(Model):
    """How this kind of event usually moves the share price, for one case, with its source.

    `when` picks the case: the company's part in a deal (buyer, target, seller), the
    results reading (e.g. 'better than expected'), or the stage the event opened with."""

    when: str
    label: str = Field(description="the case in plain words, e.g. 'company is the buyer'")
    expected: Literal["up", "down", "flat", "uncertain"] = Field(
        description="up | down | flat (no unusual move) | uncertain (an unusual move either way)"
    )
    finding: str
    source: str = Field(description="authors (year), journal")


class Playbook(Model):
    """The typical progression of one kind of storyline (reference data, not code)."""

    theme: str
    title: str = Field(default="", description="plain-English name shown to people")
    description: str
    link_window_days: int = Field(
        gt=0, description="how long a storyline stays open for new stages"
    )
    window_basis: str = Field(
        description="where the window comes from: judgment prior | calibrated"
    )
    window_why: str
    triggers: tuple[str, ...]
    stages: tuple[PlaybookStage, ...]
    research: tuple[ResearchFinding, ...] = ()
    watch: tuple[str, ...] = Field(default=(), description="what investors typically check next")
    expectations: tuple[Expectation, ...] = Field(
        default=(), description="share price expectation per case; else the opening stage's"
    )

    def stage_of(self, event_type: str) -> int | None:
        return next((i for i, s in enumerate(self.stages) if event_type in s.event_types), None)

    def event_types(self) -> set[str]:
        return set(self.triggers) | {t for s in self.stages for t in s.event_types}

    def expectation(self, keys: tuple[str | None, ...]) -> Expectation | None:
        """The first case matching a key (role, reading, opening stage), else the opening
        stage's own price expectation (keys[-1] = that stage's name), with the lead finding."""
        for key in keys:
            found = next((x for x in self.expectations if key and x.when == key), None)
            if found:
                return found
        stage = next((s for s in self.stages if s.name == keys[-1]), None)
        price = next((d.expected_direction for d in stage.decisions
                      if d.market_channel == "price"), None) if stage else None  # fmt: skip
        if stage is None or price is None or not self.research:
            return None
        return Expectation(
            when=stage.name,
            label=stage.title or stage.name,
            expected=price,
            finding=self.research[0].finding,
            source=self.research[0].source,
        )

    def terms_after(self, stage: int) -> tuple[str, ...]:
        """Search terms that would signal any later stage."""
        return tuple(t for s in self.stages[stage + 1 :] for t in s.follow_up_terms)


PUBLISHES: tuple[type[Event], ...] = (StorylineUpdated,)
