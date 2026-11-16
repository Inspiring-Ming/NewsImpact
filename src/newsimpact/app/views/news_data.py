"""What the assistant's tools (and MCP clients) may read: the latest snapshot and the stored
articles, as plain values formatted the way the website shows them ("-18.5%", "2026-11-13").

Implements the assistant module's NewsData port. Everything comes from live data; nothing
here is written by hand. Article search scans stored articles: fine for thousands; with
Postgres it becomes one full-text query (same port, other adapter).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from newsimpact.app.views import snapshot
from newsimpact.app.views.companies import CompanyCard, EventCard, source_names

if TYPE_CHECKING:
    from newsimpact.app.wiring import Services


class SnapshotNewsData:
    def __init__(self, svc: Services) -> None:
        self._svc = svc

    def companies(self) -> list[dict[str, Any]]:
        return [{"ticker": c.ticker, "name": c.name, "country": c.country, "sector": c.sector}
                for c in self._svc.companies]  # fmt: skip

    def events(self, ticker: str | None, days: int) -> list[dict[str, Any]]:
        since = datetime.now(UTC) - timedelta(days=days)
        rows = [(c, e) for c in self._cards(ticker) for e in c.events
                if e.updates and e.updates[-1].published_at >= since]  # fmt: skip
        rows.sort(key=lambda ce: ce[1].updates[-1].published_at, reverse=True)
        return [_summary(c, e) for c, e in rows]

    def event(self, event_id: str) -> dict[str, Any] | None:
        for c in snapshot.latest(self._svc).companies:
            for e in c.events:
                if e.event_id == event_id:
                    return _detail(c, e)
        return None

    def articles(self, text: str, ticker: str | None, days: int) -> list[dict[str, Any]]:
        words = [w for w in text.lower().split() if w]
        since = datetime.now(UTC) - timedelta(days=days)
        names = source_names(self._svc)
        found = []
        for a in self._svc.articles.recent(10**6):
            if a.published_at < since:
                continue
            body = f"{a.title} {a.body}".lower()
            if not all(w in body for w in words):
                continue
            if ticker and ticker.upper() not in self._svc.semantics.mentioned_tickers(a):
                continue
            found.append({"title": a.title, "url": a.url,
                          "source": names.get(a.source_id, a.source_id),
                          "date": a.published_at.date().isoformat()})  # fmt: skip
        return sorted(found, key=lambda r: r["date"], reverse=True)

    def _cards(self, ticker: str | None) -> list[CompanyCard]:
        cards = snapshot.latest(self._svc).companies
        return [c for c in cards if ticker is None or c.ticker == ticker.upper()]


def _pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def _move(c: CompanyCard, e: EventCard) -> str:
    if e.stock_move is not None:
        kind = "unusual" if e.stock_move_unusual else "within its normal range"
        return f"{_pct(e.stock_move)} vs {c.index_name} ({e.stock_move_period}), {kind}"
    if e.move_so_far is not None:
        return f"so far {_pct(e.move_so_far)} vs {c.index_name} to {e.so_far_through} (provisional)"
    return "not measured yet"


def _summary(c: CompanyCard, e: EventCard) -> dict[str, Any]:
    return {
        "event_id": e.event_id, "company": c.name, "ticker": c.ticker,
        "event": f"{e.event_type} ({e.reading})" if e.reading else e.event_type,
        "latest_update": e.updates[-1].title, "date": e.updates[-1].published_at.date().isoformat(),
        "headline": e.latest_headline, "confirmed": e.verified, "sources": e.sources,
        "stock_vs_index": _move(c, e), "priority": e.priority,
    }  # fmt: skip


def _detail(c: CompanyCard, e: EventCard) -> dict[str, Any]:
    return {
        **_summary(c, e),
        "sector": c.sector, "source_names": list(e.source_names), "is_rumour": e.is_rumour,
        "trading_volume": f"{e.volume_ratio:.1f}x a normal day" if e.volume_ratio else None,
        "updates": [{"date": u.published_at.date().isoformat(), "title": u.title,
                     "articles": [{"title": a.title, "url": a.url, "source": a.source,
                                   "date": a.published_at.date().isoformat()}
                                  for a in u.articles]}
                    for u in e.updates],
        "next_usual_update": e.next_update,
        "research": [{"finding": r.finding, "source": r.source} for r in e.research],
        "what_to_check": [k.text for k in e.checks],
        "brief": list(e.brief),
    }  # fmt: skip
