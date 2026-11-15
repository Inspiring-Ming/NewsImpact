from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta

import pytest

from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.shared.text import content_hash, stable_id
from newsimpact.sources.adapters.json_file import JsonSourceRegistry
from newsimpact.sources.adapters.memory import (
    InMemoryArticleStore,
    InMemorySeenSources,
    InMemoryWatchStore,
)
from newsimpact.sources.models import (
    Article,
    ArticleIngested,
    FeedConfig,
    SearchHit,
    Source,
    SourceListing,
    SourceRegistered,
)
from newsimpact.sources.ports import Feed
from newsimpact.sources.service import SourcesService
from newsimpact.storylines.models import (
    FollowUpRequest,
    Storyline,
    StorylineEvent,
    StorylineStatus,
    StorylineUpdated,
)

T = datetime(2026, 3, 16, tzinfo=UTC)
LISTED = SourceListing(source_id="wire", name="Wire", domains=("wire.example",),
                       feeds=(FeedConfig(kind="fake"),))  # fmt: skip
BROKEN = SourceListing(source_id="broken", name="Broken", domains=("broken.example",),
                       feeds=(FeedConfig(kind="fail"),))  # fmt: skip
OFF = SourceListing(source_id="off", name="Off", domains=("off.example",),
                    feeds=(FeedConfig(kind="fake"),), enabled=False)  # fmt: skip


def _article(url: str, body: str, source_id: str = "wire") -> Article:
    return Article(article_id=stable_id(url), source_id=source_id, url=url, title="t", body=body,
                   published_at=T, ingested_at=T, content_hash=content_hash("t", body))  # fmt: skip


class FakeFeed:
    def __init__(self, articles: list[Article]) -> None:
        self._articles = articles

    def fetch(self, since: datetime | None = None) -> Iterable[Article]:
        return self._articles


class FailingFeed:
    def fetch(self, since: datetime | None = None) -> Iterable[Article]:
        raise ConnectionError("site down")


def _feeds(source: Source, config: FeedConfig) -> Feed:
    if config.kind == "fail":
        return FailingFeed()
    return FakeFeed([_article("https://wire.example/1", "same text"),
                     _article("https://wire.example/2", "same  TEXT")])  # fmt: skip


class FakeSearch:
    def __init__(self, hits: list[SearchHit]) -> None:
        self.hits = hits
        self.domains: Sequence[str] = ()

    def search(self, entity_name: str, terms: Sequence[str], since: datetime, until: datetime,
               domains: Sequence[str] = ()) -> Iterable[SearchHit]:  # fmt: skip
        self.domains = domains
        return self.hits


def _service(
    search: FakeSearch, *, accept_unlisted: bool = False
) -> tuple[SourcesService, InMemoryEventBus]:
    bus = InMemoryEventBus()
    svc = SourcesService(bus, JsonSourceRegistry([LISTED, BROKEN, OFF]), _feeds, search,
                         InMemoryArticleStore(), InMemorySeenSources(), InMemoryWatchStore(),
                         accept_unlisted=accept_unlisted)  # fmt: skip
    return svc, bus


def _count(bus: InMemoryEventBus, event_type: str) -> int:
    return sum(e.type == event_type for e in bus.published)


def test_registers_each_listed_outlet_once() -> None:
    svc, bus = _service(FakeSearch([]))
    assert svc.register_listed() == 3
    assert svc.register_listed() == 0
    assert _count(bus, SourceRegistered.EVENT_TYPE) == 3


def test_collect_dedupes_skips_disabled_and_survives_broken_feeds() -> None:
    svc, bus = _service(FakeSearch([]))
    assert svc.collect() == {"wire": 1, "broken": 0}  # duplicate dropped, "off" not read
    assert _count(bus, ArticleIngested.EVENT_TYPE) == 1


def _open_storyline(svc: SourcesService, bus: InMemoryEventBus) -> None:
    ev = StorylineEvent(claim_id="c", article_id="a", event_type="leadership_apology",
                        stage=0, stage_name="public_pressure", published_at=T,
                        claim_reliability=0.9, summary="x")  # fmt: skip
    story = Storyline(storyline_id="st1", ticker="GLBX", entity_name="Globex Motors",
                      theme="leadership_crisis", status=StorylineStatus.DEVELOPING, events=(ev,),
                      current_stage=0, max_stage=0, opened_at=T, updated_at=T,
                      model_version="t")  # fmt: skip
    req = FollowUpRequest(entity_name="Globex Motors", terms=("steps down",), since=T,
                          until=T + timedelta(days=30))  # fmt: skip
    update = StorylineUpdated(storyline=story, latest=ev, is_new=True, escalated=False,
                              expected_decisions=(), follow_up=req)  # fmt: skip
    bus.publish(update.to_envelope("/test"))
    assert svc.active_watches


HITS = [
    SearchHit(domain="news.wire.example",
              article=_article("https://news.wire.example/ceo", "CEO steps down", "?")),
    SearchHit(domain="random-blog.example",
              article=_article("https://random-blog.example/x", "CEO steps down?", "?")),
]  # fmt: skip


def test_follow_up_searches_only_listed_enabled_outlets() -> None:
    search = FakeSearch(HITS)
    svc, bus = _service(search)
    _open_storyline(svc, bus)
    assert svc.follow_up() == 1  # the blog is not on our list
    assert set(search.domains) == {"wire.example", "broken.example"}
    found = [ArticleIngested.model_validate(e.data) for e in bus.published
             if e.type == ArticleIngested.EVENT_TYPE]  # fmt: skip
    assert found[0].discovered_by == "follow_up"
    assert found[0].article.source_id == "wire"  # sub-domain resolved to the listed outlet


def test_unlisted_outlets_can_be_allowed() -> None:
    search = FakeSearch(HITS)
    svc, bus = _service(search, accept_unlisted=True)
    _open_storyline(svc, bus)
    assert svc.follow_up() == 2
    assert search.domains == ()
    registered = [SourceRegistered.model_validate(e.data).source for e in bus.published
                  if e.type == SourceRegistered.EVENT_TYPE]  # fmt: skip
    assert any(s.source_id == "random-blog.example" and not s.listed for s in registered)


def test_duplicate_source_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        JsonSourceRegistry([LISTED, LISTED])


class RateLimitedSearch(FakeSearch):
    def search(self, entity_name: str, terms: Sequence[str], since: datetime, until: datetime,
               domains: Sequence[str] = ()) -> Iterable[SearchHit]:  # fmt: skip
        raise ConnectionError("429 Too Many Requests")


def test_failing_follow_up_search_is_skipped_and_watch_kept() -> None:
    svc, bus = _service(RateLimitedSearch([]))
    _open_storyline(svc, bus)
    assert svc.follow_up() == 0
    assert svc.active_watches  # retried next round
