"""MarketData from EODHD end-of-day prices (https://eodhd.com) - US and ASX in one feed.

Why EODHD: one subscription covers both markets we watch (US and ASX), with
adjusted closes and volumes and an official ASX redistribution licence.
Free tier (20 calls/day, personal use) is enough for development; a client
product needs EODHD's commercial licence (docs/07).

EODHD takes the key in the query string, so it must never reach logs:
errors are re-raised without the URL.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from datetime import date, timedelta

import httpx

from newsimpact.market.models import Bar

API = "https://eodhd.com/api/eod/{symbol}"


class MarketDataUnavailable(ValueError):  # noqa: N818 - a state, like WindowNotComplete
    """The vendor could not provide prices (network, quota, unknown symbol)."""


class EodhdMarketData:
    version = "eodhd-eod-v1"

    def __init__(
        self, client: httpx.Client, api_key: str, vendor_symbol: Callable[[str], str]
    ) -> None:
        self._client = client
        self._key = api_key
        self._symbol = vendor_symbol

    def daily_bars(self, ticker: str, start: date, end: date) -> Sequence[Bar]:
        symbol = self._symbol(ticker)
        try:
            resp = self._client.get(
                API.format(symbol=symbol),
                # one extra week before `start` so the first bar has a previous close
                params={"api_token": self._key, "fmt": "json",
                        "from": (start - timedelta(days=7)).isoformat(), "to": end.isoformat()},
            )  # fmt: skip
            resp.raise_for_status()
            rows = sorted(resp.json(), key=lambda r: r["date"])
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            status = getattr(getattr(exc, "response", None), "status_code", "no response")
            raise MarketDataUnavailable(
                f"EODHD {symbol}: {type(exc).__name__} ({status})"
            ) from None
        bars: list[Bar] = []
        for prev, row in itertools.pairwise(rows):
            day = date.fromisoformat(row["date"])
            if day >= start and prev.get("adjusted_close"):
                ret = row["adjusted_close"] / prev["adjusted_close"] - 1
                bars.append(Bar(day=day, ret=ret, volume=float(row.get("volume") or 0)))
        return bars
