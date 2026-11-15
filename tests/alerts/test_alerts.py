"""Alerts: only followed companies, only real changes, never twice, baseline first."""

from pathlib import Path

import httpx
import pytest

from newsimpact.alerts.adapters.discord import DiscordNotifier
from newsimpact.alerts.adapters.memory import InMemoryAlertState
from newsimpact.alerts.adapters.shared import SharedChannels
from newsimpact.alerts.adapters.sqlite import SqliteAlertState
from newsimpact.alerts.models import Alert, EventSnapshot
from newsimpact.alerts.service import AlertsService
from newsimpact.shared.sqlite import Database


def _event(**kw: object) -> EventSnapshot:
    base = dict(event_id="e1", ticker="NVDA", company="Nvidia", event_type="Leadership change",
                confirmed=False, updates=1, latest_update="Leader under pressure",
                headline="Nvidia board reviews CEO", article_url="https://x.test/a",
                stock_move=None, unusual=False, index_name="S&P 500")  # fmt: skip
    return EventSnapshot.model_validate({**base, **kw})


class Collect:
    def __init__(self) -> None:
        self.sent: list[Alert] = []

    def send(self, alert: Alert, event_link: str) -> None:
        self.sent.append(alert)


def test_baseline_then_changes_for_followed_companies_only() -> None:
    out = Collect()
    svc = AlertsService(InMemoryAlertState(), SharedChannels([out]), "http://site.test")
    svc.follow("ana", "NVDA")
    assert svc.check([_event(), _event(event_id="e2", ticker="AAPL")]) == []  # baseline
    changed = _event(confirmed=True, updates=2, stock_move=-0.185, unusual=True)
    kinds = [a.kind for a in svc.check([changed, _event(event_id="e2", ticker="AAPL", updates=3)])]
    assert kinds == ["confirmed", "unusual_move", "new_update"]  # AAPL is not followed
    assert svc.check([changed]) == []  # nothing new: nothing sent again
    assert [a.kind for a in svc.check([changed, _event(event_id="e3")])] == ["new_event"]


def test_discord_posts_an_embed_and_never_leaks_the_webhook() -> None:
    posted: list[httpx.Request] = []
    ok = httpx.Client(
        transport=httpx.MockTransport(lambda r: posted.append(r) or httpx.Response(204))
    )
    alert = Alert(key="k", kind="new_event", ticker="NVDA", title="T", text="x",
                  article_url="https://x.test/a", event_id="e1")  # fmt: skip
    DiscordNotifier(ok, "https://discord.test/api/webhooks/secret").send(alert, "http://site.test")
    assert b'"embeds"' in posted[0].content
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401)))
    with pytest.raises(RuntimeError) as exc:
        DiscordNotifier(bad, "https://discord.test/api/webhooks/secret").send(alert, "")
    assert "secret" not in str(exc.value)


def test_each_user_gets_only_their_companies_and_each_alert_once() -> None:
    out = Collect()
    svc = AlertsService(InMemoryAlertState(), SharedChannels([out]), "http://site.test")
    svc.follow("ana", "NVDA")
    svc.follow("ben", "NVDA")
    svc.follow("ben", "AAPL")
    svc.check([_event(), _event(event_id="e2", ticker="AAPL")])  # baseline
    svc.check([_event(updates=2), _event(event_id="e2", ticker="AAPL", updates=2)])
    assert sorted(a.ticker for a in out.sent) == ["AAPL", "NVDA", "NVDA"]  # ana 1, ben 2
    assert svc.followed("ana") == {"NVDA"}


class Broken:
    def send(self, alert: Alert, event_link: str) -> None:
        raise RuntimeError("channel down")


def test_a_failed_channel_is_retried_next_round_and_test_needs_a_channel() -> None:
    state = InMemoryAlertState()
    svc = AlertsService(state, SharedChannels([Broken()]), "http://site.test")
    svc.follow("ana", "NVDA")
    svc.check([_event()])  # baseline
    assert svc.check([_event(updates=2)]) == []  # not delivered: not marked as sent
    assert not state.was_sent("ana", "e1|update2")
    with pytest.raises(RuntimeError):
        AlertsService(state, SharedChannels([]), "http://site.test").test("ana")


def test_sqlite_state_keeps_each_users_list_and_sent_alerts(tmp_path: Path) -> None:
    state = SqliteAlertState(Database(tmp_path / "a.db"))
    state.set_followed("ana", "NVDA", True)
    state.set_followed("ben", "AAPL", True)
    state.set_followed("ben", "AAPL", False)
    assert state.followed("ana") == {"NVDA"} and state.followers() == {"ana": {"NVDA"}}
    state.save_snapshot([_event()])
    assert set(state.snapshot() or {}) == {"e1"}
    state.mark_sent("ana", "k")
    assert state.was_sent("ana", "k") and not state.was_sent("ben", "k")
