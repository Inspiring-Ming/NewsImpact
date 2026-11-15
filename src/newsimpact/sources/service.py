"""Collect articles from the listed outlets, dedupe, announce; chase storyline follow-ups.

Three entry points:
  register_listed()  announce every outlet on the curated list (done at start-up)
  collect()          read every enabled feed once (run on a schedule)
  follow_up()        search the listed outlets for the next chapter of open storylines
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Literal

from newsimpact.shared.bus import EventBus
from newsimpact.shared.events import EventEnvelope
from newsimpact.sources.logic import resemblance, shingles
from newsimpact.sources.models import (
    Article,
    ArticleIngested,
    DuplicatePolicy,
    SearchHit,
    Source,
    SourceListing,
    SourceRegistered,
    SourceType,
    domain_of,
)
from newsimpact.sources.ports import (
    ArticleStore,
    FeedFactory,
    NewsSearch,
    SeenSources,
    SourceRegistry,
    WatchStore,
)
from newsimpact.storylines.models import FollowUpRequest, StorylineUpdated

log = logging.getLogger(__name__)

EVENT_SOURCE = "/sources"
Origin = Literal["feed", "follow_up"]


class SourcesService:
    def __init__(
        self,
        bus: EventBus,
        registry: SourceRegistry,
        feeds: FeedFactory,
        search: NewsSearch,
        articles: ArticleStore,
        seen: SeenSources,
        watches: WatchStore,
        *,
        accept_unlisted: bool = False,
        duplicates: DuplicatePolicy | None = None,
    ) -> None:
        self._bus = bus
        self._registry = registry
        self._feeds = feeds
        self._search = search
        self._articles = articles
        self._seen = seen
        self._accept_unlisted = accept_unlisted
        self._watches = watches
        self._dup = duplicates or DuplicatePolicy(
            near_duplicate_jaccard=0.8, near_duplicate_days=3, copy_novelty=0.2
        )
        self._recent: list[tuple[Article, frozenset[str]]] | None = None  # lazy copy index
        bus.subscribe(StorylineUpdated.EVENT_TYPE, self.on_storyline_updated)

    # ------------------------------------------------------------ the list
    def listed(self) -> Sequence[SourceListing]:
        return self._registry.listings()

    def register_listed(self) -> int:
        """Announce every listed outlet not announced before. Returns how many."""
        return sum(self._register(listing.as_source()) for listing in self.listed())

    # ----------------------------------------------------------- collecting
    def collect(self, since: datetime | None = None) -> dict[str, int]:
        """Read every feed of every enabled outlet. Returns new articles per outlet.

        Articles from all outlets are processed oldest first, so storylines are
        built in the order events happened (feeds list newest first). A failing
        feed is logged and skipped, so one broken site never stops the rest.
        """
        counts: dict[str, int] = {}
        batch: list[tuple[Source, Article]] = []
        for listing in self.listed():
            if not listing.enabled:
                continue
            source = listing.as_source()
            counts[source.source_id] = 0
            for config in listing.feeds:
                try:
                    batch += [(source, a) for a in self._feeds(source, config).fetch(since)]
                except Exception:
                    log.exception("feed failed", extra={"source_id": source.source_id})
        for source, article in sorted(batch, key=lambda sa: sa[1].published_at):
            counts[source.source_id] += self.accept(source, article)
        return counts

    def accept(self, source: Source, article: Article, discovered_by: Origin = "feed") -> bool:
        """Store and announce one article. Returns False if it adds nothing.

        * same outlet, same (or nearly the same) text  -> dropped (a repeat)
        * another outlet, same or nearly the same text -> kept, marked as a copy,
          so it is not counted as independent confirmation
        """
        self._register(source)
        if any(seen.article_id == article.article_id for seen, _ in self._index()):
            return False  # same URL read again (feeds repeat their items every round)
        original = self._find_original(article)
        if original is not None:
            if original.source_id == source.source_id:
                return False
            article = article.model_copy(  # point at the root, not at another copy
                update={
                    "copy_of": original.copy_of or original.article_id,
                    "copy_of_source": original.copy_of_source or original.source_id,
                }
            )
        elif self._articles.exists_hash(article.content_hash):
            return False  # older than the copy window: a stale repeat
        self._articles.add(article)
        self._remember(article)
        self._bus.publish(
            ArticleIngested(article=article, discovered_by=discovered_by).to_envelope(
                EVENT_SOURCE, correlation_id=article.article_id
            )
        )
        return True

    def _find_original(self, article: Article) -> Article | None:
        """The earliest earlier article this one copies, within the copy window."""
        sig = shingles(f"{article.title} {article.body}")
        horizon = timedelta(days=self._dup.near_duplicate_days)
        for earlier, earlier_sig in self._index():
            if earlier.article_id == article.article_id:
                continue
            if abs(article.published_at - earlier.published_at) > horizon:
                continue
            same = earlier.content_hash == article.content_hash
            if same or resemblance(sig, earlier_sig) >= self._dup.near_duplicate_jaccard:
                return earlier
        return None

    def _index(self) -> list[tuple[Article, frozenset[str]]]:
        if self._recent is None:  # rebuilt from the store after a restart
            self._recent = []
            for a in sorted(self._articles.recent(2000), key=lambda a: a.published_at):
                self._recent.append((a, shingles(f"{a.title} {a.body}")))
        return self._recent

    def _remember(self, article: Article) -> None:
        index = self._index()
        index.append((article, shingles(f"{article.title} {article.body}")))
        if len(index) > 5000:  # bounded memory; the copy window is only days long
            del index[:1000]

    # ------------------------------------------------- follow-up discovery
    @property
    def active_watches(self) -> dict[str, FollowUpRequest]:
        return self._watches.all()

    def on_storyline_updated(self, envelope: EventEnvelope) -> None:
        event = StorylineUpdated.model_validate(envelope.data)
        storyline_id = event.storyline.storyline_id
        if event.follow_up is None:
            self._watches.remove(storyline_id)
        else:
            self._watches.put(storyline_id, event.follow_up)

    def follow_up(self, max_rounds: int = 5) -> int:
        """Search for every open storyline; repeat while discoveries open new ones.

        A failing search is logged and skipped; its watch stays open for the next round.
        """
        domains = () if self._accept_unlisted else self._listed_domains()
        total = 0
        for _ in range(max_rounds):
            found = 0
            for storyline_id, req in self._watches.all().items():
                try:
                    hits = list(
                        self._search.search(
                            req.entity_name, req.terms, req.since, req.until, domains
                        )
                    )
                except Exception:  # e.g. rate-limited: retry next round, keep the others going
                    log.exception("follow-up search failed", extra={"storyline_id": storyline_id})
                    continue
                found += sum(self._accept_hit(hit) for hit in hits)
            total += found
            if found == 0:
                break
        return total

    # ------------------------------------------------------------- helpers
    def _accept_hit(self, hit: SearchHit) -> bool:
        source = self._source_for(hit)
        if source is None:
            return False
        article = hit.article.model_copy(update={"source_id": source.source_id})
        return self.accept(source, article, discovered_by="follow_up")

    def _source_for(self, hit: SearchHit) -> Source | None:
        """The listed outlet behind a search hit, or an 'unlisted' one if allowed."""
        for listing in self.listed():
            if listing.covers(hit.domain):
                return listing.as_source()
        if not self._accept_unlisted:
            return None
        domain = domain_of(hit.domain)
        return Source(
            source_id=domain,
            name=domain,
            source_type=SourceType.UNKNOWN,
            domains=(domain,),
            country=hit.country,
            listed=False,
        )

    def _listed_domains(self) -> tuple[str, ...]:
        return tuple(d for listing in self.listed() if listing.enabled for d in listing.domains)

    def _register(self, source: Source) -> bool:
        if not self._seen.add(source.source_id):
            return False
        self._bus.publish(SourceRegistered(source=source).to_envelope(EVENT_SOURCE))
        return True
