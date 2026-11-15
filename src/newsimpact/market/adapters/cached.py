"""Caches any MarketData in SQLite, so repeated validation rounds cost no API calls.

Each ticker's bars are stored once, as one range that only ever grows: a
request outside it fetches the union, so an old event never shrinks the range
a recent event needs. A request past the cached end is served from cache only
if that end was already past the last fetch day and the fetch is recent
(daily bars change once a day).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime, timedelta

from newsimpact.market.models import Bar
from newsimpact.market.ports import MarketData
from newsimpact.shared.sqlite import Database


class CachedMarketData:
    def __init__(
        self,
        inner: MarketData,
        db: Database,
        refresh_hours: float = 12,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._inner = inner
        self._c = db.collection(f"bars:{inner.version}")
        self._refresh = timedelta(hours=refresh_hours)
        self._now = now
        self.version = inner.version

    def daily_bars(self, ticker: str, start: date, end: date) -> Sequence[Bar]:
        doc = self._c.get(ticker)
        lo, hi = start, end
        if doc:
            cached = json.loads(doc)
            c_lo, c_hi = date.fromisoformat(cached["start"]), date.fromisoformat(cached["end"])
            fetched = datetime.fromisoformat(cached["fetched_at"])
            recent = self._now() - fetched < self._refresh
            fresh = end <= c_hi or (recent and c_hi >= fetched.date())
            if c_lo <= start and fresh:
                bars = [Bar.model_validate(b) for b in cached["bars"]]
                return [b for b in bars if start <= b.day <= end]
            lo, hi = min(start, c_lo), max(end, c_hi)
        bars = list(self._inner.daily_bars(ticker, lo, hi))
        self._c.put(ticker, json.dumps({
            "start": lo.isoformat(), "end": hi.isoformat(),
            "fetched_at": self._now().isoformat(),
            "bars": [b.model_dump(mode="json") for b in bars],
        }))  # fmt: skip
        return [b for b in bars if start <= b.day <= end]
