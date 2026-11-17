"""In-memory stores for the sources module (demo, tests). Lost when the process stops."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from newsimpact.sources.models import Article
from newsimpact.storylines.models import FollowUpRequest


class InMemoryArticleStore:
    def __init__(self) -> None:
        self._articles: list[Article] = []
        self._hashes: set[str] = set()

    def add(self, article: Article) -> None:
        self._articles.append(article)
        self._hashes.add(article.content_hash)

    def exists_hash(self, content_hash: str) -> bool:
        return content_hash in self._hashes

    def recent(self, limit: int) -> Sequence[Article]:
        return sorted(self._articles, key=lambda a: a.published_at, reverse=True)[:limit]

    def since(self, after: datetime) -> Sequence[Article]:
        return [a for a in self.recent(len(self._articles)) if a.published_at >= after]

    def get(self, article_id: str) -> Article | None:
        return next((a for a in self._articles if a.article_id == article_id), None)

    def count(self) -> int:
        return len(self._articles)


class InMemorySeenSources:
    def __init__(self) -> None:
        self._ids: set[str] = set()

    def add(self, source_id: str) -> bool:
        is_new = source_id not in self._ids
        self._ids.add(source_id)
        return is_new


class InMemoryWatchStore:
    def __init__(self) -> None:
        self._items: dict[str, FollowUpRequest] = {}

    def put(self, storyline_id: str, request: FollowUpRequest) -> None:
        self._items[storyline_id] = request

    def remove(self, storyline_id: str) -> None:
        self._items.pop(storyline_id, None)

    def all(self) -> dict[str, FollowUpRequest]:
        return dict(self._items)
