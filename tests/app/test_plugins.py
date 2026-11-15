"""Plug-in tables and round steps: adding one is one entry, and wrong names fail clearly."""

import pytest

from newsimpact.app.config import Settings
from newsimpact.app.monitor import ROUND, run_step
from newsimpact.app.wiring import build_services
from newsimpact.app.wiring.plugins import (
    EVENT_BUSES,
    FEEDS,
    LLM_PROVIDERS,
    MARKET_DATA,
    STORES,
    pick,
)


def test_every_table_lists_the_documented_names() -> None:
    assert set(STORES) == {"memory", "sqlite"}
    assert set(EVENT_BUSES) == {"memory"}
    assert set(FEEDS) == {"rss", "rss_per_company", "fixture"}
    assert set(MARKET_DATA) == {"none", "eodhd", "csv"}
    assert set(LLM_PROVIDERS) == {"anthropic", "ollama"}


def test_unknown_names_fail_at_start_up_with_the_known_ones() -> None:
    with pytest.raises(ValueError, match="known: \\['memory', 'sqlite'\\]"):
        pick(STORES, "postgres", "store")
    with pytest.raises(ValueError, match="unknown store 'postgres'"):
        build_services(Settings(env="test", profile="demo", store="postgres"))


def test_round_steps_run_in_order_and_alone() -> None:
    assert [name for name, _ in ROUND] == [
        "collect", "follow_up", "track_records", "assess", "briefs", "alerts",
    ]  # fmt: skip
    svc = build_services(Settings(env="test", profile="demo"))
    run_step(svc, "collect")
    assert svc.articles.recent(100)


def test_tests_never_read_the_developers_env_file() -> None:
    s = Settings()
    assert Settings.model_config["env_file"] is None
    assert s.discord_webhook_url is None or not s.discord_webhook_url.get_secret_value()
    assert s.profile == "demo" and s.llm_preset == "off"
