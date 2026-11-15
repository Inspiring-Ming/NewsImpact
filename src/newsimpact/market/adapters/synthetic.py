"""Deterministic synthetic prices for demos/tests - NOT real market data.

Replace with a licensed vendor adapter for client work (unofficial website
scrapers are not licensed for commercial products).
"""

from __future__ import annotations

import json
import math
import random
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

from newsimpact.market.models import Bar


class SyntheticMarketData:
    version = "synthetic-v2"

    def __init__(
        self,
        betas: dict[str, float],
        benchmark: str,
        shocks: dict[tuple[str, date], float] | None = None,
        seed: int = 7,
    ) -> None:
        self._betas = betas
        self._benchmark = benchmark
        self._shocks = shocks or {}
        self._seed = seed

    @classmethod
    def from_file(cls, path: Path, benchmark: str) -> SyntheticMarketData:
        raw = json.loads(path.read_text())
        shocks = {(s["ticker"], date.fromisoformat(s["date"])): s["return"] for s in raw["shocks"]}
        return cls(raw["betas"], benchmark, shocks)

    def _rng(self, key: str, d: date) -> random.Random:
        return random.Random(f"{self._seed}-{key}-{d}")  # noqa: S311 - not crypto

    def daily_bars(self, ticker: str, start: date, end: date) -> Sequence[Bar]:
        out: list[Bar] = []
        d = start
        previous_shock = 0.0  # news moves trading on the next trading day too
        while d <= end:
            if d.weekday() < 5:
                m = self._rng(self._benchmark, d).gauss(0.0004, 0.01)
                shock = self._shocks.get((ticker, d), 0.0)
                if ticker == self._benchmark:
                    r = m
                else:
                    noise = self._rng(ticker, d).gauss(0.0, 0.012)
                    r = 0.0002 + self._betas.get(ticker, 1.0) * m + noise + shock
                # News days trade more: volume scales with the size of the shock.
                base = 1e6 * math.exp(self._rng(f"vol-{ticker}", d).gauss(0.0, 0.2))
                volume = base * (1 + 40 * abs(shock) + 20 * abs(previous_shock))
                out.append(Bar(day=d, ret=r, volume=volume))
                previous_shock = shock
            d += timedelta(days=1)
        return out
