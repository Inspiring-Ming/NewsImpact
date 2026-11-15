"""What the market module needs: daily price and volume history from a (licensed) vendor."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from newsimpact.market.models import Bar


class MarketData(Protocol):
    version: str

    def daily_bars(self, ticker: str, start: date, end: date) -> Sequence[Bar]: ...
