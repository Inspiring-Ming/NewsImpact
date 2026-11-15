"""MarketData from CSV files: <dir>/<TICKER>.csv with columns date,adj_close,volume.

Vendor-neutral and reproducible: export from any licensed vendor once, keep
the files with the analysis, and the same numbers come out every time.
"""

from __future__ import annotations

import csv
import itertools
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from newsimpact.market.models import Bar


class CsvMarketData:
    version = "csv-v1"

    def __init__(self, directory: Path) -> None:
        self._dir = directory

    def daily_bars(self, ticker: str, start: date, end: date) -> Sequence[Bar]:
        path = self._dir / f"{ticker.upper()}.csv"
        if not path.exists():
            return []
        with path.open(newline="") as f:
            rows = sorted(csv.DictReader(f), key=lambda r: r["date"])
        bars: list[Bar] = []
        for prev, row in itertools.pairwise(rows):
            day = date.fromisoformat(row["date"][:10])
            if start <= day <= end:
                ret = float(row["adj_close"]) / float(prev["adj_close"]) - 1
                bars.append(Bar(day=day, ret=ret, volume=float(row["volume"])))
        return bars
