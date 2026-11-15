"""Alerts: only followed companies, only real changes, never twice, baseline first."""

import httpx
import pytest

from newsimpact.alerts.adapters.discord import DiscordNotifier
from newsimpact.alerts.adapters.memory import InMemoryAlertState
from newsimpact.alerts.models import Alert, EventSnapshot
from newsimpact.alerts.service import AlertsService


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
    svc = AlertsService(InMemoryAlertState(), [out], "http://site.test")
    svc.follow("NVDA")
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
