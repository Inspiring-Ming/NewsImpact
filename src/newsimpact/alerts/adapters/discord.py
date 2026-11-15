"""Send alerts to a Discord channel through an incoming webhook.

The webhook URL is a secret (anyone with it can post to the channel): it comes
from NI_DISCORD_WEBHOOK_URL in the git-ignored .env and never reaches logs;
errors are re-raised without it.
"""

from __future__ import annotations

import httpx

from newsimpact.alerts.models import Alert

COLOURS = {"new_event": 0x1F4FD1, "confirmed": 0x1D7A4C, "unusual_move": 0xB3261E,
           "new_update": 0x996000}  # fmt: skip


class DiscordNotifier:
    def __init__(self, client: httpx.Client, webhook_url: str) -> None:
        self._client = client
        self._url = webhook_url

    def send(self, alert: Alert, event_link: str) -> None:
        embed = {"title": alert.title[:256], "description": alert.text[:4000], "url": event_link,
                 "color": COLOURS.get(alert.kind, 0x5F6368)}  # fmt: skip
        if alert.article_url:
            embed["fields"] = [{"name": "Original article", "value": alert.article_url[:1000]}]
        try:
            self._client.post(self._url, json={"embeds": [embed]}).raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Discord rejected the alert ({type(exc).__name__})") from None
