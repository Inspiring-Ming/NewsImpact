"""Caches any MarketData in SQLite, so repeated validation rounds cost no API calls.

Each ticker's bars are stored once; the cache is refreshed only when a
request reaches past the cached range and the last fetch is older than
`refresh_hours` (daily bars change once a day).
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
        if doc:
            cached = json.loads(doc)
            lo, hi = date.fromisoformat(cached["start"]), date.fromisoformat(cached["end"])
            fetched = datetime.fromisoformat(cached["fetched_at"])
            fresh = end <= hi or self._now() - fetched < self._refresh
            if lo <= start and fresh:
                bars = [Bar.model_validate(b) for b in cached["bars"]]
                return [b for b in bars if start <= b.day <= end]
            start = min(start, lo)
        bars = list(self._inner.daily_bars(ticker, start, end))
        self._c.put(ticker, json.dumps({
            "start": start.isoformat(), "end": end.isoformat(),
            "fetched_at": self._now().isoformat(),
            "bars": [b.model_dump(mode="json") for b in bars],
        }))  # fmt: skip
        return bars
