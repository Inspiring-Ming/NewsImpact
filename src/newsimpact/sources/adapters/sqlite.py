"""SQLite stores for the sources module (state survives restarts; see shared/sqlite.py)."""

from __future__ import annotations

from collections.abc import Sequence

from newsimpact.shared.sqlite import Database
from newsimpact.sources.models import Article
from newsimpact.storylines.models import FollowUpRequest


class SqliteArticleStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("articles")

    def add(self, article: Article) -> None:
        self._c.put(article.article_id, article.model_dump_json(), tag=article.content_hash,
                    at=article.published_at.isoformat())  # fmt: skip

    def exists_hash(self, content_hash: str) -> bool:
        return self._c.has_tag(content_hash)

    def recent(self, limit: int) -> Sequence[Article]:
        return [
            Article.model_validate_json(d) for d in self._c.find(newest_first=True, limit=limit)
        ]


class SqliteSeenSources:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("seen_sources")

    def add(self, source_id: str) -> bool:
        if self._c.get(source_id) is not None:
            return False
        self._c.put(source_id, "{}")
        return True


class SqliteWatchStore:
    def __init__(self, db: Database) -> None:
        self._c = db.collection("watches")
        self._db = db

    def put(self, storyline_id: str, request: FollowUpRequest) -> None:
        self._c.put(storyline_id, request.model_dump_json())

    def remove(self, storyline_id: str) -> None:
        self._c.delete(storyline_id)

    def all(self) -> dict[str, FollowUpRequest]:
        rows = self._db.execute(
            "SELECT key, doc FROM documents WHERE collection='watches' ORDER BY key"
        )
        return {k: FollowUpRequest.model_validate_json(d) for k, d in rows}
