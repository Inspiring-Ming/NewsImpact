"""Monitoring through the real wiring, with state kept in SQLite across restarts."""

from pathlib import Path

from newsimpact.app.config import Settings
from newsimpact.app.monitor import BackgroundMonitor
from newsimpact.app.wiring import build_services


def test_rounds_repeat_and_state_survives_a_restart(tmp_path: Path) -> None:
    settings = Settings(env="test", profile="demo", store="sqlite", db_path=tmp_path / "ni.db")
    monitor = BackgroundMonitor(build_services(settings), every_minutes=0)
    first, second, third = monitor.run_now(), monitor.run_now(), monitor.run_now()
    assert first.new_total == 10  # 5 feed articles (1 is a copy) + 5 found by follow-up
    assert second.new_total == third.new_total == 0  # nothing new: everything was deduplicated
    # Round 2 re-scores once: sources now have a track record from round 1's assessments.
    # The track record depends only on which reports were confirmed, so round 3 is stable.
    assert first.assessments_updated >= 3 and third.assessments_updated == 0
    assert monitor.last is third

    restarted = build_services(settings)  # e.g. after a crash or redeploy
    assert len(restarted.articles.recent(100)) == 10
    assert {s.theme for s in restarted.storyline_store.all()} >= {"leadership_crisis"}
    assert not restarted.bus.published  # outlets were already registered before
