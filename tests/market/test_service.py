from datetime import UTC, date, datetime

import pytest

from newsimpact.market.adapters.synthetic import SyntheticMarketData
from newsimpact.market.models import Bar, MeasurementPolicy, WindowNotComplete
from newsimpact.market.service import MarketService

NEWS_DAY = datetime(2026, 3, 20, 13, tzinfo=UTC)  # 09:00 in New York, before the open


def _service(policy: MeasurementPolicy) -> MarketService:
    shocks = {("GLBX", date(2026, 3, 20)): -0.06}
    return MarketService(
        SyntheticMarketData({"GLBX": 1.1}, "MKT", shocks), policy, benchmark_override="MKT"
    )


def test_observes_price_volume_and_volatility_after_a_shock(
    measurement_policy: MeasurementPolicy,
) -> None:
    svc = _service(measurement_policy)
    price = svc.observe("GLBX", "price", NEWS_DAY)
    volume = svc.observe("GLBX", "volume", NEWS_DAY)
    vol = svc.observe("GLBX", "volatility", NEWS_DAY)
    assert price and price.direction == "down" and price.significant
    assert price.metric == "CAR[+0,+1]"  # window taken from methodology.json
    assert volume and volume.direction == "up" and volume.significant
    assert vol and vol.value > 1
    assert price.provider.startswith("synthetic")


def test_channels_without_data_return_none(measurement_policy: MeasurementPolicy) -> None:
    assert _service(measurement_policy).observe("GLBX", "credit_spreads", NEWS_DAY) is None


def test_news_after_the_close_counts_from_the_next_trading_day(
    measurement_policy: MeasurementPolicy,
) -> None:
    svc = _service(measurement_policy)
    at = datetime(2026, 3, 20, 19, tzinfo=UTC)  # 15:00 New York, 06:00 next day Sydney
    assert svc.event_day("NVDA", at) == date(2026, 3, 20)
    assert svc.event_day("NVDA", datetime(2026, 3, 20, 21, tzinfo=UTC)) == date(2026, 3, 21)
    assert svc.event_day("BHP.AX", at) == date(2026, 3, 21)  # before Sydney's close
    assert svc.event_day("BHP.AX", datetime(2026, 3, 20, 6, tzinfo=UTC)) == date(2026, 3, 21)


def test_exchange_rules_pick_benchmark_and_vendor_symbol(
    measurement_policy: MeasurementPolicy,
) -> None:
    p = measurement_policy
    assert (p.exchange_of("BHP.AX"), p.exchange_of("NVDA")) == ("ASX", "US")
    assert (p.vendor_symbol("BHP.AX"), p.vendor_symbol("NVDA")) == ("BHP.AU", "NVDA.US")
    live = MarketService(SyntheticMarketData({}, "SPY"), p)
    assert live.benchmark_for("CBA.AX") == "STW.AX" and live.benchmark_for("NVDA") == "SPY"


def test_combined_reaction_over_close_stages(measurement_policy: MeasurementPolicy) -> None:
    svc = _service(measurement_policy)
    obs = svc.observe_span("GLBX", datetime(2026, 3, 18, 13, tzinfo=UTC), NEWS_DAY)
    assert obs.channel == "price" and obs.direction == "down"
    assert obs.metric.startswith("CAR first..last stage")


class UntilToday:
    version = "stub"

    def __init__(self, last: date) -> None:
        self._inner = SyntheticMarketData({"GLBX": 1.1}, "MKT")
        self._last = last

    def daily_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        return list(self._inner.daily_bars(ticker, start, min(end, self._last)))


def test_window_not_finished_yet_is_reported_as_such(
    measurement_policy: MeasurementPolicy,
) -> None:
    svc = MarketService(UntilToday(date(2026, 3, 20)), measurement_policy, benchmark_override="MKT")
    with pytest.raises(WindowNotComplete):
        svc.observe("GLBX", "price", NEWS_DAY)  # needs day +1, data ends on day 0
