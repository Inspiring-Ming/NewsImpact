"""Feed and NewsSearch over a local JSON file (demo and tests, no network).

File layout: {"feed": [...], "archive": [...]}
`feed` = what the outlets' regular feeds deliver;
`archive` = only findable by searching (tests follow-up discovery).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from newsimpact.shared.text import content_hash, stable_id
from newsimpact.sources.models import Article, SearchHit, Source, domain_of


def _article(row: dict[str, Any], now: datetime) -> Article:
    return Article(
        article_id=stable_id(row["url"]),
        source_id=row["source_id"],
        url=row["url"],
        title=row["title"],
        body=row["body"],
        language=row.get("language", "en"),
        published_at=datetime.fromisoformat(row["published_at"]),
        ingested_at=now,
        content_hash=content_hash(row["title"], row["body"]),
    )


class FixtureFeed:
    """The `feed` items of one outlet."""

    def __init__(self, source: Source, path: Path) -> None:
        self._source = source
        self._path = path

    def fetch(self, since: datetime | None = None) -> Iterable[Article]:
        now = datetime.now(UTC)
        for row in json.loads(self._path.read_text())["feed"]:
            article = _article(row, now)
            if article.source_id == self._source.source_id and (
                since is None or article.published_at > since
            ):
                yield article


class FixtureSearch:
    """Case-insensitive match: entity name AND any term, within [since, until]."""

    def __init__(self, path: Path) -> None:
        raw = json.loads(path.read_text())
        self._rows: list[dict[str, Any]] = raw["feed"] + raw["archive"]

    def search(
        self,
        entity_name: str,
        terms: Sequence[str],
        since: datetime,
        until: datetime,
        domains: Sequence[str] = (),
    ) -> Iterable[SearchHit]:
        now = datetime.now(UTC)
        name = entity_name.lower()
        hits: list[SearchHit] = []
        for row in self._rows:
            article = _article(row, now)
            domain = domain_of(article.url)
            text = f"{article.title} {article.body}".lower()
            if (
                since <= article.published_at <= until
                and (not domains or domain in domains)
                and name in text
                and any(t.lower() in text for t in terms)
            ):
                hits.append(SearchHit(domain=domain, article=article))
        return sorted(hits, key=lambda h: h.article.published_at)
