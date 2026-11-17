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


def test_pages_read_a_time_window_whatever_offset_a_feed_used(tmp_path: Path) -> None:
    from datetime import timedelta, timezone

    store = SqliteArticleStore(Database(tmp_path / "a.db"))
    sydney = timezone(timedelta(hours=11))
    times = {"old": datetime(2026, 10, 1, tzinfo=UTC),
             "syd": datetime(2026, 11, 17, 9, tzinfo=sydney),  # = 16 Nov 22:00 UTC
             "utc": datetime(2026, 11, 16, 23, tzinfo=UTC)}  # fmt: skip
    for key, at in times.items():
        store.add(Article(article_id=key, source_id="s", url=f"https://x.test/{key}", title=key,
                          body=key, published_at=at, ingested_at=at, content_hash=key))  # fmt: skip
    after = datetime(2026, 11, 16, 21, tzinfo=UTC)
    assert [a.article_id for a in store.since(after)] == ["utc", "syd"]  # newest first, in UTC
    assert store.count() == 3 and store.get("old") is not None and store.get("nope") is None
