from datetime import UTC, datetime, timedelta

from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.shared.text import content_hash, stable_id
from newsimpact.sources.adapters.json_file import JsonSourceRegistry
from newsimpact.sources.adapters.memory import (
    InMemoryArticleStore,
    InMemorySeenSources,
    InMemoryWatchStore,
)
from newsimpact.sources.logic import resemblance, shingles
from newsimpact.sources.models import Article, ArticleIngested, FeedConfig, SearchHit, Source
from newsimpact.sources.ports import Feed
from newsimpact.sources.service import SourcesService

T = datetime(2026, 3, 20, 13, tzinfo=UTC)
WIRE = Source(source_id="wire", name="Wire", domains=("wire.example",))
PAPER = Source(source_id="paper", name="Paper", domains=("paper.example",))
STORY = ("Globex Motors said chief executive Dana Reyes will step down at the end of the month "
         "after a review of the braking defect and its handling by management.")  # fmt: skip


def _article(source: Source, body: str, hours: float = 0) -> Article:
    url = f"https://{source.domains[0]}/{hours}"
    return Article(article_id=stable_id(url), source_id=source.source_id, url=url, title="t",
                   body=body, published_at=T + timedelta(hours=hours), ingested_at=T,
                   content_hash=content_hash("t", body))  # fmt: skip


class NoSearch:
    def search(self, *_: object) -> list[SearchHit]:
        return []


def _no_feed(source: Source, config: FeedConfig) -> Feed:
    raise AssertionError("not used")


def _service() -> tuple[SourcesService, InMemoryEventBus]:
    bus = InMemoryEventBus()
    svc = SourcesService(bus, JsonSourceRegistry([]), _no_feed, NoSearch(),
                         InMemoryArticleStore(), InMemorySeenSources(),
                         InMemoryWatchStore())  # fmt: skip
    return svc, bus


def _stored(bus: InMemoryEventBus) -> list[Article]:
    return [ArticleIngested.model_validate(e.data).article for e in bus.published
            if e.type == ArticleIngested.EVENT_TYPE]  # fmt: skip


def test_resemblance_of_light_rewrites_is_high_and_of_different_stories_low() -> None:
    rewrite = STORY.replace("said", "announced that")
    assert resemblance(shingles(STORY), shingles(rewrite)) > 0.6
    assert resemblance(shingles(STORY), shingles("Acme beat revenue guidance.")) == 0


def test_repeat_from_same_outlet_is_dropped_copy_from_other_outlet_is_marked() -> None:
    svc, bus = _service()
    assert svc.accept(WIRE, _article(WIRE, STORY))
    assert not svc.accept(WIRE, _article(WIRE, STORY, hours=1))  # same outlet again
    assert svc.accept(PAPER, _article(PAPER, STORY, hours=2))
    stored = {a.source_id: a for a in _stored(bus)}
    assert stored["paper"].copy_of_source == "wire"


def test_copies_point_at_the_root_and_old_stories_are_not_copies() -> None:
    svc, bus = _service()
    third = Source(source_id="third", name="Third", domains=("third.example",))
    svc.accept(WIRE, _article(WIRE, STORY))
    svc.accept(PAPER, _article(PAPER, STORY, hours=1))
    svc.accept(third, _article(third, STORY, hours=2))
    later = _article(PAPER, STORY + " Shares fell.", hours=24 * 10)  # outside the 3-day window
    assert svc.accept(PAPER, later)
    by_url = {a.url: a for a in _stored(bus)}
    assert by_url["https://third.example/2"].copy_of_source == "wire"
    assert by_url[later.url].copy_of is None
