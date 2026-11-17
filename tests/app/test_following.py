"""The round's follow step: who the news names decides who is followed, kept between rounds."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from newsimpact.app.config import Settings
from newsimpact.app.demo import run_demo
from newsimpact.app.following import FollowingPolicy, followed_companies, refresh
from newsimpact.app.wiring import build_services

POLICY = FollowingPolicy(min_articles=2, window_days=7, keep_days=30, max_followed=10,
                         discover_per_round=1)  # fmt: skip


def test_the_follow_step_decides_from_the_stored_news_and_keeps_its_decision(
    tmp_path: Path,
) -> None:
    settings = Settings(env="test", profile="demo", store="sqlite", db_path=tmp_path / "ni.db")
    demo = build_services(settings)
    assert followed_companies(demo) == list(demo.companies)  # no universe: all followed
    run_demo(demo)
    svc = replace(demo, following_policy=POLICY)  # as with a universe (live profile)
    newest = max(a.published_at for a in svc.articles.recent(100))
    first = refresh(svc, newest + timedelta(days=1))
    assert first is not None and first.followed  # named in 2+ demo articles that week
    assert {c.ticker for c in followed_companies(svc)} == set(first.followed)
    assert svc.following.get() == first.model_copy(update={"discover_from": first.discover_from})
    later = refresh(svc, newest + timedelta(days=60))  # no news for two months: dropped
    assert later is not None and set(later.followed) <= set(first.followed)
    assert later.discover_from == first.discover_from + POLICY.discover_per_round
