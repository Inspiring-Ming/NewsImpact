"""Data owned by the market module: price/volume history and measured reactions."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from newsimpact.shared.events import Event, Model


class Bar(Model):
    """One trading day of one instrument."""

    day: date
    ret: float = Field(description="close-to-close return")
    volume: float = Field(ge=0.0)


class EventStudyResult(Model):
    ticker: str
    event_time: datetime
    estimation_alpha: float
    estimation_beta: float
    residual_sd: float = Field(description="normal daily abnormal-return noise")
    abnormal_returns: tuple[float, ...]
    cumulative_abnormal_return: float
    t_stat: float | None
    model_version: str


Direction = Literal["up", "down", "flat"]


class ChannelObservation(Model):
    """What a market channel actually did after an event, and whether it stands out."""

    ticker: str
    channel: str = Field(description="price | volume | volatility | ...")
    metric: str = Field(description="how it was measured, e.g. CAR[0,+1]")
    value: float
    statistic: float | None = Field(description="z/t statistic vs. normal days")
    direction: Direction
    significant: bool
    provider: str = Field(description="data provider + method version (reproducibility)")


class ExchangeRule(Model):
    timezone: str
    close: str = Field(description="HH:MM local closing time")
    benchmark: str = Field(description="market factor for stocks listed here")
    benchmark_name: str = Field(description="how people call that market, e.g. S&P 500")
    vendor_suffix: str = Field(description="exchange code at the price vendor, e.g. .US / .AU")


class MeasurementPolicy(Model):
    """How reactions are measured. Values and reasons: data/reference/methodology.json "market"."""

    estimation_days: int = Field(gt=0)
    gap_days: int = Field(ge=0)
    windows: dict[str, tuple[int, int]] = Field(description="channel -> [first, last] trading day")
    significance_z: float = Field(gt=0)
    exchanges: dict[str, ExchangeRule]
    ticker_suffixes: dict[str, str] = Field(
        description="ticker suffix -> exchange, e.g. .AX -> ASX"
    )
    default_exchange: str

    def exchange_of(self, ticker: str) -> str:
        return next((ex for sfx, ex in self.ticker_suffixes.items() if ticker.endswith(sfx)),
                    self.default_exchange)  # fmt: skip

    def vendor_symbol(self, ticker: str) -> str:
        """'BHP.AX' -> 'BHP.AU', 'NVDA' -> 'NVDA.US' (vendor codes from the exchange rules)."""
        exchange = self.exchange_of(ticker)
        base = next((ticker[: -len(s)] for s in self.ticker_suffixes if ticker.endswith(s)), ticker)
        return f"{base}{self.exchanges[exchange].vendor_suffix}"


class PricePoint(Model):
    day: date
    stock: float = Field(description="price index, 100 at the start")
    benchmark: float


class PricePath(Model):
    """Stock vs. its benchmark, both rebased to 100 - for charts."""

    ticker: str
    benchmark: str
    points: tuple[PricePoint, ...]


class WindowNotComplete(ValueError):  # noqa: N818 - reads as a state, which it is
    """The event window has not finished yet: measure again later."""


PUBLISHES: tuple[type[Event], ...] = ()
