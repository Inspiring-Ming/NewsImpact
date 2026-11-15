"""What the sources module needs from the outside world (implemented in adapters/)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from typing import Protocol

from newsimpact.sources.models import Article, FeedConfig, SearchHit, Source, SourceListing
from newsimpact.storylines.models import FollowUpRequest


class SourceRegistry(Protocol):
    """The curated list of outlets we read."""

    def listings(self) -> Sequence[SourceListing]: ...


class Feed(Protocol):
    """One feed of one outlet (RSS, a provider API, a filings feed...)."""

    def fetch(self, since: datetime | None = None) -> Iterable[Article]: ...


# Builds the right Feed for a FeedConfig.kind; supplied by app/wiring (plugins.py FEEDS).
FeedFactory = Callable[[Source, FeedConfig], Feed]


class NewsSearch(Protocol):
    """Query-driven search across the web (GDELT, news-search APIs...)."""

    def search(
        self,
        entity_name: str,
        terms: Sequence[str],
        since: datetime,
        until: datetime,
        domains: Sequence[str] = (),
    ) -> Iterable[SearchHit]:
        """`domains` narrows the search to those outlets; empty = anywhere."""
        ...


class ArticleStore(Protocol):
    def add(self, article: Article) -> None: ...
    def exists_hash(self, content_hash: str) -> bool: ...
    def recent(self, limit: int) -> Sequence[Article]: ...


class SeenSources(Protocol):
    """Every outlet we have announced, so each is registered exactly once."""

    def add(self, source_id: str) -> bool:
        """Remember the outlet; return True if it was new."""
        ...


class WatchStore(Protocol):
    """Open follow-up searches (one per open storyline), kept across restarts."""

    def put(self, storyline_id: str, request: FollowUpRequest) -> None: ...
    def remove(self, storyline_id: str) -> None: ...
    def all(self) -> dict[str, FollowUpRequest]: ...
