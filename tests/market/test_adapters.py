from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from newsimpact.market.adapters.cached import CachedMarketData
from newsimpact.market.adapters.csv_file import CsvMarketData
from newsimpact.market.adapters.eodhd import EodhdMarketData, MarketDataUnavailable
from newsimpact.market.models import Bar
from newsimpact.shared.sqlite import Database


def test_eodhd_maps_symbols_uses_adjusted_prices_and_hides_the_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "FAIL" in str(request.url):
            return httpx.Response(402)
        return httpx.Response(200, json=[
            {"date": "2026-03-19", "adjusted_close": 100.0, "volume": 1e6},
            {"date": "2026-03-20", "adjusted_close": 95.0, "volume": 3e6},
        ])  # fmt: skip

    client = httpx.Client(transport=httpx.MockTransport(handler))
    md = EodhdMarketData(client, "secret", lambda t: t.replace(".AX", ".AU"))
    (bar,) = md.daily_bars("BHP.AX", date(2026, 3, 20), date(2026, 3, 20))
    assert bar.ret == pytest.approx(-0.05) and bar.volume == 3e6
    assert "/eod/BHP.AU" in str(seen[0].url)
    with pytest.raises(MarketDataUnavailable) as err:
        md.daily_bars("FAIL", date(2026, 3, 20), date(2026, 3, 20))
    assert "secret" not in str(err.value) and "402" in str(err.value)


def test_csv_files_give_reproducible_bars(tmp_path: Path) -> None:
    (tmp_path / "GLBX.csv").write_text(
        "date,adj_close,volume\n2026-03-19,10,100\n2026-03-20,11,300\n"
    )
    md = CsvMarketData(tmp_path)
    (bar,) = md.daily_bars("glbx", date(2026, 3, 1), date(2026, 3, 31))
    assert bar.ret == pytest.approx(0.1)
    assert md.daily_bars("MISSING", date(2026, 3, 1), date(2026, 3, 31)) == []


class CountingData:
    version = "counting"

    def __init__(self) -> None:
        self.calls = 0

    def daily_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        self.calls += 1
        days = (end - start).days + 1
        return [Bar(day=start + timedelta(days=i), ret=0.0, volume=1) for i in range(days)]


def test_cache_serves_repeat_requests_without_calling_the_vendor(tmp_path: Path) -> None:
    inner = CountingData()
    now = datetime(2026, 3, 30, tzinfo=UTC)
    md = CachedMarketData(inner, Database(tmp_path / "c.db"), now=lambda: now)
    md.daily_bars("X", date(2026, 3, 1), date(2026, 3, 20))
    again = md.daily_bars("X", date(2026, 3, 5), date(2026, 3, 10))
    assert inner.calls == 1 and len(again) == 6


def test_an_older_request_never_shrinks_the_cached_range(tmp_path: Path) -> None:
    inner = CountingData()
    now = datetime(2026, 3, 30, tzinfo=UTC)
    md = CachedMarketData(inner, Database(tmp_path / "c.db"), now=lambda: now)
    md.daily_bars("SPY", date(2026, 3, 1), date(2026, 3, 20))  # a recent event
    older = md.daily_bars("SPY", date(2026, 1, 1), date(2026, 2, 1))  # then an old one
    recent = md.daily_bars("SPY", date(2026, 3, 1), date(2026, 3, 20))
    assert len(older) == 32 and len(recent) == 20 and inner.calls == 2


def test_a_cached_range_ending_before_its_fetch_day_is_refreshed(tmp_path: Path) -> None:
    inner = CountingData()
    now = datetime(2026, 3, 30, tzinfo=UTC)
    md = CachedMarketData(inner, Database(tmp_path / "c.db"), now=lambda: now)
    md.daily_bars("SPY", date(2026, 1, 1), date(2026, 2, 1))
    later = md.daily_bars("SPY", date(2026, 3, 1), date(2026, 3, 20))  # past the cached end
    assert inner.calls == 2 and len(later) == 20
