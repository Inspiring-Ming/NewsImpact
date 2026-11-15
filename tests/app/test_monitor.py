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


class FakeLlm:
    """A language model that always writes the same safe brief."""

    calls = 0

    def complete_json(self, request: object) -> object:
        from newsimpact.llm.models import LlmResult

        FakeLlm.calls += 1
        return LlmResult(data={"what_happened": "Leadership news about the company.",
                               "market": "Measured against its market index.",
                               "why_it_matters": "Leadership changes tend to raise price swings."},
                         model="fake", cost_usd=0.0, cached=False)  # fmt: skip

    def new_round(self) -> None: ...


def test_briefs_are_written_once_per_change_and_shown() -> None:
    from dataclasses import replace

    from newsimpact.app.demo import run_demo
    from newsimpact.app.monitor import write_briefs
    from newsimpact.app.views.companies import companies

    svc = build_services(Settings(env="test", profile="demo"))
    run_demo(svc)
    svc = replace(svc, llm=FakeLlm())  # type: ignore[arg-type]
    written = write_briefs(svc)
    assert written > 0 and write_briefs(svc) == 0  # unchanged facts: not written again
    assert all(e.brief_by == "ai" for c in companies(svc) for e in c.events)


def test_background_monitor_runs_on_its_timer_and_stops() -> None:
    import time

    svc = build_services(Settings(env="test", profile="demo"))
    monitor = BackgroundMonitor(svc, every_minutes=0.001)
    monitor.start()
    for _ in range(50):
        if monitor.last is not None:
            break
        time.sleep(0.1)
    monitor.stop()
    assert monitor.last is not None
