"""Pages read a snapshot computed once per round, traceable to its time and analysis chain."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from newsimpact.app.config import Settings
from newsimpact.app.demo import run_demo
from newsimpact.app.monitor import run_step
from newsimpact.app.views import snapshot
from newsimpact.app.views.companies import companies
from newsimpact.app.wiring import build_services


def test_the_round_publishes_what_pages_read_and_when_and_how(tmp_path: Path) -> None:
    settings = Settings(env="test", profile="demo", store="sqlite", db_path=tmp_path / "ni.db")
    svc = build_services(settings)
    run_demo(svc)
    snap = svc.snapshots.get()
    assert snap is not None
    assert snap.analysis == svc.semantics.model_version  # which reading made these numbers
    assert [c.ticker for c in snap.companies] == [c.ticker for c in companies(svc)]
    assert snapshot.latest(svc) == snap  # a page visit does not recompute

    run_step(svc, "publish")
    newer = snapshot.latest(svc)
    assert newer.computed_at > snap.computed_at
    restarted = build_services(settings)  # stored: survives a restart
    assert restarted.snapshots.get() == newer


def test_a_snapshot_from_before_this_start_is_rebuilt() -> None:
    svc = build_services(Settings(env="test", profile="demo"))
    old = snapshot.build(svc).model_copy(update={"computed_at": snapshot.STARTED - timedelta(1)})
    svc.snapshots.put(old)
    assert snapshot.latest(svc).computed_at >= snapshot.STARTED


def test_coverage_flags_companies_with_no_news_in_the_window() -> None:
    svc = build_services(Settings(env="test", profile="demo"))
    run_demo(svc)
    snap = snapshot.latest(svc)
    assert snap.coverage_window_days == 7  # methodology.json "coverage"
    by_ticker = {c.ticker: c for c in snap.coverage}
    assert set(by_ticker) == {c.ticker for c in svc.companies}
    named = {t for a in svc.articles.recent(100)
             if a.published_at >= datetime.now(UTC) - timedelta(days=7)
             for t in svc.semantics.mentioned_tickers(a)}  # fmt: skip
    for ticker, row in by_ticker.items():
        assert (row.status == "ok") == (ticker in named)
        assert (row.articles > 0) == (row.status == "ok")
