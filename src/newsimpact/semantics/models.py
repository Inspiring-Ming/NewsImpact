"""Data owned by the semantics module: claims, and the taxonomy that classifies them.

Event types and aspects are plain strings defined in the taxonomy
(data/reference/taxonomy.json), not code, so analysts can add new ones
without a release. "other" means nothing in the taxonomy matched.
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Literal

from pydantic import Field

from newsimpact.shared.events import Event, Model

OTHER = "other"


# ---------------------------------------------------------------- taxonomy
class EventTypeDef(Model):
    """One kind of real-world event a sentence can report (a semantic trigger)."""

    name: str
    description: str = ""
    patterns: tuple[str, ...]
    speculative: bool | None = Field(
        default=None, description="True/False: only hedged/unhedged sentences; None: either"
    )


class AttributionLexicon(Model):
    """Wording that reveals where a claim comes from."""

    cues: tuple[str, ...] = Field(
        description="'according to', 'reported'... before/after an outlet"
    )
    company_statement: tuple[str, ...]
    filing: tuple[str, ...]
    anonymous: tuple[str, ...]
    outlets: dict[str, tuple[str, ...]] = Field(description="outlet id -> names as written in text")


class Taxonomy(Model):
    """Everything the analyzers look for. Loaded from taxonomy.json."""

    version: str
    event_types: tuple[EventTypeDef, ...]
    aspects: dict[str, tuple[str, ...]] = Field(description="business aspect -> keywords")
    word_lists: dict[str, tuple[str, ...]] = Field(
        description="positive, negative, speculative, uncertainty, background, ..."
    )
    attribution: AttributionLexicon

    def event_type_names(self) -> set[str]:
        return {e.name for e in self.event_types}

    def words(self, name: str) -> tuple[str, ...]:
        return self.word_lists.get(name, ())


# ------------------------------------------------------------------ claims
AttributionKind = Literal[
    "own_reporting", "cites_outlet", "company_statement", "filing", "anonymous"
]


class Attribution(Model):
    """Where a claim comes from. Decides what counts as *independent* confirmation:
    ten outlets repeating one Bloomberg scoop are one origin, not ten."""

    kind: AttributionKind = "own_reporting"
    cited_outlets: tuple[str, ...] = Field(default=(), description="outlet ids named as the source")
    copy_of_source: str | None = Field(
        default=None, description="the article is a (near-)copy of this outlet's earlier article"
    )

    def origin(self, reporting_source_id: str) -> str:
        """Key of the independent origin behind a report."""
        if self.copy_of_source:
            return self.copy_of_source
        if self.kind == "cites_outlet" and self.cited_outlets:
            return f"outlet:{self.cited_outlets[0]}"
        if self.kind in ("company_statement", "filing"):
            return f"{self.kind}"
        return reporting_source_id


class Company(Model):
    """A company we follow: how to show it, and how the news names it."""

    ticker: str = Field(description="bare = US listing, '.AX' = ASX")
    name: str
    country: str = Field(description="ISO country code, e.g. US, AU")
    sector: str = Field(default="", description="GICS sector, e.g. Information Technology")
    aliases: tuple[str, ...]


class EntityMention(Model):
    name: str
    entity_type: str = Field(description="company | person | country | product | ...")
    ticker: str | None = None


class Claim(Model):
    """A single checkable statement extracted from an article.

    Fixed fields are what every downstream module relies on; `signals` holds
    extra measurements (e.g. "uncertainty") that new analysis steps add
    without changing this schema.
    """

    claim_id: str
    article_id: str
    text: str
    entities: tuple[EntityMention, ...] = ()
    event_type: str = Field(default=OTHER, description="name from the taxonomy")
    aspect: str = Field(default=OTHER, description="business aspect from the taxonomy")
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    is_speculative: bool = Field(default=False, description="rumour / 'sources say' / hedged")
    novelty: float = Field(default=1.0, ge=0.0, le=1.0, description="1 = genuinely new info")
    attribution: Attribution = Field(default_factory=Attribution)
    signals: dict[str, float] = Field(default_factory=dict)
    model_version: str = Field(default="", description="every analysis step that produced it")


# ------------------------------------------------------------------ events
class ClaimsExtracted(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.claims.extracted.v1"
    article_id: str
    source_id: str
    published_at: datetime
    claims: tuple[Claim, ...]


PUBLISHES: tuple[type[Event], ...] = (ClaimsExtracted,)
