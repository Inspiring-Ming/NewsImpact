"""What every page reads, computed once per round and stored - not on every visit.

A snapshot holds the company cards (events, guidance, briefs) and each company's news
coverage, with when they were computed and by which analysis chain, so any number on the
website can be traced to a round and a version. The hourly round's "publish" step
replaces it (app/monitor.py). If none is stored yet, or it predates this server start
(a new release may compute pages differently), it is rebuilt on first read.

Cost: pages no longer re-read every stored article. Moving to the cloud, the store
becomes one row or object; the pages do not change.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal, Protocol

from pydantic import Field, ValidationError

from newsimpact.app.following import followed_companies
from newsimpact.app.views.companies import CompanyCard, companies, mentions, source_names
from newsimpact.app.views.system import TypeStats, event_types, outlet_coverage
from newsimpact.shared.events import Model
from newsimpact.shared.sqlite import Database
from newsimpact.sources.models import Article, OutletCoverage

if TYPE_CHECKING:  # type hints only: the wiring imports this module's stores
    from newsimpact.app.wiring import Services


STARTED = datetime.now(UTC)  # snapshots from before this start are rebuilt


class CompanyCoverage(Model):
    ticker: str
    name: str
    articles: int = Field(description="articles naming the company in the coverage window")
    sources: tuple[str, ...] = Field(description="sources of those articles")
    status: Literal["ok", "gap"] = Field(description="gap = no article in the window")


class Snapshot(Model):
    computed_at: datetime
    analysis: str = Field(description="the analysis chain that read the news (every step)")
    coverage_window_days: int
    companies: tuple[CompanyCard, ...]
    coverage: tuple[CompanyCoverage, ...]
    outlets: tuple[OutletCoverage, ...] = Field(description="each source's volume and use")
    types: tuple[TypeStats, ...] = Field(description="each event type: steps, cases, record")


def build(svc: Services) -> Snapshot:
    """Read the articles of the pages window once; derive the cards and coverage from them.
    The window is fixed (methodology.json "pages"), so a round costs the same as the store
    grows; an older event still shows its own articles."""
    articles = window_articles(svc)
    by_ticker = mentions(svc, articles)
    with_company = {a.article_id for news in by_ticker.values() for a in news}
    days = coverage_window_days(svc)
    cards = companies(svc, by_ticker)
    return Snapshot(
        computed_at=datetime.now(UTC),
        analysis=svc.semantics.model_version,
        coverage_window_days=days,
        companies=tuple(cards),
        coverage=tuple(_coverage(svc, by_ticker, days)),
        outlets=tuple(outlet_coverage(svc, articles, with_company)),
        types=tuple(event_types(svc, cards)),
    )


def latest(svc: Services) -> Snapshot:
    """The stored snapshot; rebuilt if missing or older than this server start."""
    snap = svc.snapshots.get()
    if snap is None or snap.computed_at < STARTED:
        snap = publish(svc)
    return snap


def event_summary(svc: Services, event_id: str) -> CompanyCard | None:
    """The company card with only this event (the event page)."""
    for card in latest(svc).companies:
        for e in card.events:
            if e.event_id == event_id:
                return card.model_copy(update={"events": (e,)})
    return None


def publish(svc: Services) -> Snapshot:
    snap = build(svc)
    svc.snapshots.put(snap)
    return snap


def coverage_window_days(svc: Services) -> int:
    raw = json.loads((svc.settings.reference_dir / "methodology.json").read_text())
    return int(raw["coverage"]["window_days"])


def window_articles(svc: Services) -> Sequence[Article]:
    """The pages window: the last `pages.window_days` of news we have (ending at the newest
    stored article, which is now on a live system; the demo's news is dated in the past)."""
    raw = json.loads((svc.settings.reference_dir / "methodology.json").read_text())
    newest = svc.articles.recent(1)
    end = newest[0].published_at if newest else datetime.now(UTC)
    return svc.articles.since(end - timedelta(days=int(raw["pages"]["window_days"])))


def current_cards(svc: Services) -> list[CompanyCard]:
    """Company cards computed now from the pages window (the round's steps that need fresh
    facts before the snapshot is published)."""
    return companies(svc, mentions(svc, window_articles(svc)))


def _coverage(
    svc: Services, by_ticker: dict[str, list[Article]], days: int
) -> list[CompanyCoverage]:
    since = datetime.now(UTC) - timedelta(days=days)
    names = source_names(svc)
    rows = []
    for c in followed_companies(svc):
        recent = [a for a in by_ticker.get(c.ticker, []) if a.published_at >= since]
        sources = tuple(sorted({names.get(a.source_id, a.source_id) for a in recent}))
        rows.append(CompanyCoverage(ticker=c.ticker, name=c.name, articles=len(recent),
                                    sources=sources, status="ok" if recent else "gap"))  # fmt: skip
    return sorted(rows, key=lambda r: (r.articles, r.name))


# ------------------------------------------------------------ storage
class SnapshotStore(Protocol):
    def get(self) -> Snapshot | None: ...
    def put(self, snapshot: Snapshot) -> None: ...


class InMemorySnapshots:
    def __init__(self) -> None:
        self._snap: Snapshot | None = None

    def get(self) -> Snapshot | None:
        return self._snap

    def put(self, snapshot: Snapshot) -> None:
        self._snap = snapshot


class SqliteSnapshots:
    """One row: the latest snapshot (older ones are not needed - each round replaces it)."""

    def __init__(self, db: Database) -> None:
        self._c = db.collection("snapshot")

    def get(self) -> Snapshot | None:
        doc = self._c.get("latest")
        try:
            return Snapshot.model_validate_json(doc) if doc else None
        except ValidationError:  # stored by an older release: rebuilt by latest()
            return None

    def put(self, snapshot: Snapshot) -> None:
        self._c.put("latest", snapshot.model_dump_json())
