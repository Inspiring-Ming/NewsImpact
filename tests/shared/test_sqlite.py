from datetime import UTC, datetime
from pathlib import Path

from newsimpact.reliability.adapters.sqlite import SqliteEvidenceStore
from newsimpact.shared.sqlite import Database
from newsimpact.sources.adapters.sqlite import SqliteArticleStore, SqliteSeenSources
from newsimpact.sources.models import Article

T = datetime(2026, 3, 20, tzinfo=UTC)


def test_state_survives_reopening_the_database(tmp_path: Path) -> None:
    path = tmp_path / "ni.db"
    db = Database(path)
    article = Article(article_id="a1", source_id="s", url="u", title="t", body="b",
                      published_at=T, ingested_at=T, content_hash="h1")  # fmt: skip
    SqliteArticleStore(db).add(article)
    assert SqliteSeenSources(db).add("s")
    SqliteEvidenceStore(db).record("s", "all", supported=True)

    reopened = Database(path)
    assert SqliteArticleStore(reopened).exists_hash("h1")
    assert SqliteArticleStore(reopened).recent(5) == [article]
    assert not SqliteSeenSources(reopened).add("s")
    assert SqliteEvidenceStore(reopened).counts("s", "all") == (1.0, 0.0)
