"""Data owned by the sources module: outlets, their feeds, and articles.

Point-in-time rule (ADR 0006): `published_at` = when it happened,
`ingested_at` = when we knew it. Backtests only use what was known.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import ClassVar, Literal
from urllib.parse import urlparse

from pydantic import Field

from newsimpact.shared.events import Event, Model


class SourceType(StrEnum):
    """Kind of outlet. Sets the starting reliability before any track record exists."""

    WIRE = "wire"
    MAJOR_OUTLET = "major_outlet"
    AGGREGATOR = "aggregator"
    REGULATORY_FILING = "regulatory_filing"
    COMPANY_PRESS_RELEASE = "company_press_release"
    BLOG = "blog"
    SOCIAL = "social"
    UNKNOWN = "unknown"


class Source(Model):
    """A news outlet. Reliability is tracked per outlet."""

    source_id: str
    name: str
    source_type: SourceType = SourceType.UNKNOWN
    domains: tuple[str, ...] = Field(description="web domains this outlet publishes on")
    country: str | None = None
    listed: bool = Field(default=True, description="on our curated list (sources.json)")

    def covers(self, url_or_domain: str) -> bool:
        host = domain_of(url_or_domain)
        return any(host == d or host.endswith(f".{d}") for d in self.domains)


class FeedConfig(Model):
    """How to read one feed of a source. `kind` picks the adapter (app/wiring/plugins.py)."""

    kind: str = Field(description="rss | rss_per_company | fixture | ...")
    url: str = ""


class SourceListing(Source):
    """One row of sources.json: the outlet plus how we collect it."""

    feeds: tuple[FeedConfig, ...] = ()
    enabled: bool = True
    note: str | None = None

    def as_source(self) -> Source:
        return Source.model_validate(self.model_dump(include=set(Source.model_fields)))


class Article(Model):
    article_id: str = Field(description="stable id derived from the URL")
    source_id: str
    url: str
    title: str
    body: str
    language: str = Field(default="en", description="ISO 639-1 code of the original text")
    translated_body: str | None = Field(default=None, description="English pivot translation")
    published_at: datetime
    ingested_at: datetime
    content_hash: str = Field(description="hash of normalised text, used for dedupe")
    copy_of: str | None = Field(default=None, description="earlier article this one copies")
    copy_of_source: str | None = Field(default=None, description="outlet of that earlier article")


class SearchHit(Model):
    """An article found by searching the web; its outlet is not yet resolved."""

    domain: str
    country: str | None = None
    article: Article


class DuplicatePolicy(Model):
    """When an article counts as a copy (values and reasons: methodology.json "sources")."""

    near_duplicate_jaccard: float = Field(gt=0, le=1)
    near_duplicate_days: int = Field(gt=0)
    copy_novelty: float = Field(ge=0, le=1)


class OutletCoverage(Model):
    """Evidence for keeping, adding or dropping an outlet (see docs/07)."""

    source_id: str
    articles: int
    per_day: float
    with_company: float = Field(description="share of articles naming a company we recognise")
    in_stories: float = Field(description="share of articles that became part of a story")
    copies: float = Field(description="share that copy another outlet's article")
    stages_reported: int
    stages_first: int = Field(description="storyline stages this outlet reported first")


def domain_of(url_or_domain: str) -> str:
    """'https://www.bbc.co.uk/news/x' -> 'bbc.co.uk'."""
    host = urlparse(url_or_domain).hostname if "://" in url_or_domain else url_or_domain
    host = (host or "").lower()
    return host.removeprefix("www.")


# ------------------------------------------------------------------ events
class SourceRegistered(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.source.registered.v1"
    source: Source


class ArticleIngested(Event):
    EVENT_TYPE: ClassVar[str] = "newsimpact.article.ingested.v1"
    article: Article
    discovered_by: Literal["feed", "follow_up"] = "feed"


PUBLISHES: tuple[type[Event], ...] = (SourceRegistered, ArticleIngested)
