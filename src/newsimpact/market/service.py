"""Measure what the market did around an event: event studies, channel observations,
combined reactions over several stages, and price paths for charts.

All windows, thresholds, trading sessions and benchmarks come from a
MeasurementPolicy (data/reference/methodology.json), per exchange - a US
stock is measured on New York's session against SPY, an ASX stock on Sydney's
session against STW.

A new channel (credit spreads, analyst revisions, options) = a new data port
+ adapter here and one branch in `observe()`.
"""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from newsimpact.market.logic import (
    MODEL_VERSION,
    abnormal_volume,
    market_model_event_study,
    volatility_ratio,
)
from newsimpact.market.models import (
    Bar,
    ChannelObservation,
    Direction,
    EventStudyResult,
    MeasurementPolicy,
    PricePath,
    PricePoint,
    WindowNotComplete,
)
from newsimpact.market.ports import MarketData

SUPPORTED_CHANNELS = ("price", "volume", "volatility")


class MarketService:
    def __init__(
        self,
        market_data: MarketData,
        policy: MeasurementPolicy,
        *,
        benchmark_override: str | None = None,
    ) -> None:
        self._md = market_data
        self._p = policy
        self._benchmark_override = benchmark_override  # the demo's synthetic market

    @property
    def version(self) -> str:
        return f"{self._md.version}/{MODEL_VERSION}"

    def benchmark_for(self, ticker: str) -> str:
        if self._benchmark_override:
            return self._benchmark_override
        return self._p.exchanges[self._p.exchange_of(ticker)].benchmark

    def event_day(self, ticker: str, at: datetime) -> date:
        """First day the home exchange could react (after-close news -> next day)."""
        rule = self._p.exchanges[self._p.exchange_of(ticker)]
        hour, minute = (int(x) for x in rule.close.split(":"))
        local = at.astimezone(ZoneInfo(rule.timezone))
        after_close = local.time() >= time(hour, minute)
        return local.date() + timedelta(days=1) if after_close else local.date()

    # ---------------------------------------------------------- measures
    def event_study(
        self, ticker: str, event_time: datetime, window: tuple[int, int]
    ) -> EventStudyResult:
        stock, market, est, evt = self._windows(ticker, event_time, window)
        return market_model_event_study(
            ticker,
            event_time,
            [stock[d].ret for d in est],
            [market[d].ret for d in est],
            [stock[d].ret for d in evt],
            [market[d].ret for d in evt],
        )

    def observe(self, ticker: str, channel: str, at: datetime) -> ChannelObservation | None:
        """None = no data for this channel. Raises WindowNotComplete if it is too early."""
        if channel not in SUPPORTED_CHANNELS or channel not in self._p.windows:
            return None
        window = self._p.windows[channel]
        label = f"[{window[0]:+d},{window[1]:+d}]"
        if channel == "price":
            res = self.event_study(ticker, at, window)
            return self._obs(ticker, channel, f"CAR{label}", res.cumulative_abnormal_return,
                             res.t_stat, centre=0.0)  # fmt: skip
        if channel == "volume":
            stock, _, est, evt = self._windows(ticker, at, window, estimation_days=60)
            log_ratio, z = abnormal_volume([stock[d].volume for d in est],
                                           [stock[d].volume for d in evt])  # fmt: skip
            return self._obs(ticker, channel, f"volume ratio {label}", math.exp(log_ratio), z,
                             centre=1.0)  # fmt: skip
        res = self.event_study(ticker, at, window)
        ratio, z = volatility_ratio(res.abnormal_returns, res.residual_sd)
        return self._obs(ticker, channel, f"volatility ratio {label}", ratio, z, centre=1.0)

    def observe_span(self, ticker: str, first: datetime, last: datetime) -> ChannelObservation:
        """One price reaction from the first stage to one day after the last stage.

        Used when stages are so close that their windows overlap (e.g. misconduct
        reported and resignation in the same week): only the combined move is
        measurable.
        """
        start, end = self.event_day(ticker, first), self.event_day(ticker, last)
        weekdays = sum((start + timedelta(days=i)).weekday() < 5 for i in range((end - start).days))
        span = (0, weekdays + self._p.windows["price"][1])
        res = self.event_study(ticker, first, span)
        return self._obs(ticker, "price", f"CAR first..last stage [+0,+{span[1]}]",
                         res.cumulative_abnormal_return, res.t_stat, centre=0.0)  # fmt: skip

    def price_path(self, ticker: str, start: date, end: date) -> PricePath:
        benchmark = self.benchmark_for(ticker)
        stock = {b.day: b for b in self._md.daily_bars(ticker, start, end)}
        market = {b.day: b for b in self._md.daily_bars(benchmark, start, end)}
        points: list[PricePoint] = []
        s_idx = m_idx = 100.0
        for day in sorted(set(stock) & set(market)):
            s_idx *= 1 + stock[day].ret
            m_idx *= 1 + market[day].ret
            points.append(PricePoint(day=day, stock=round(s_idx, 3), benchmark=round(m_idx, 3)))
        return PricePath(ticker=ticker, benchmark=benchmark, points=tuple(points))

    # ----------------------------------------------------------- helpers
    def _obs(
        self, ticker: str, channel: str, metric: str, value: float, z: float | None, centre: float
    ) -> ChannelObservation:
        significant = z is not None and abs(z) >= self._p.significance_z
        direction: Direction = "flat" if not significant else ("up" if value > centre else "down")
        return ChannelObservation(
            ticker=ticker,
            channel=channel,
            metric=metric,
            value=round(value, 6),
            statistic=None if z is None else round(z, 3),
            direction=direction,
            significant=significant,
            provider=self.version,
        )

    def _windows(
        self,
        ticker: str,
        at: datetime,
        window: tuple[int, int],
        *,
        estimation_days: int | None = None,
    ) -> tuple[dict[date, Bar], dict[date, Bar], list[date], list[date]]:
        first, last = window
        est_days = estimation_days or self._p.estimation_days
        event_day = self.event_day(ticker, at)
        start = event_day - timedelta(days=int((est_days + self._p.gap_days - first) * 1.6) + 10)
        end = event_day + timedelta(days=last * 2 + 7)
        stock = {b.day: b for b in self._md.daily_bars(ticker, start, end)}
        market = {b.day: b for b in self._md.daily_bars(self.benchmark_for(ticker), start, end)}
        days = sorted(set(stock) & set(market))
        idx = next((i for i, d in enumerate(days) if d >= event_day), None)
        if idx is None or idx + last >= len(days):
            raise WindowNotComplete(f"{ticker}: window {window} after {event_day} not complete yet")
        evt = days[max(0, idx + first) : idx + last + 1]
        est_end = max(0, idx + first - self._p.gap_days)
        est = days[max(0, est_end - est_days) : est_end]
        return stock, market, est, evt
