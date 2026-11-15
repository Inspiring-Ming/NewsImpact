"""Opinion and feature pieces talk about news; they must not open events."""

from datetime import UTC, datetime

import pytest

from newsimpact.app.config import Settings
from newsimpact.app.wiring import build_services
from newsimpact.semantics.models import OTHER
from newsimpact.sources.models import Article

T = datetime(2026, 11, 15, tzinfo=UTC)


def _article(title: str) -> Article:
    return Article(article_id=title[:8], source_id="x", url="https://x.test/a", title=title,
                   body=f"{title}. Globex Motors chief executive resigned on Monday.",
                   published_at=T, ingested_at=T, content_hash=title)  # fmt: skip


@pytest.mark.parametrize(
    ("title", "commentary"),
    [
        ("Should you buy Globex Motors stock right now?", True),
        ("Here's why Globex Motors could be a millionaire-maker", True),
        ("How the Globex Motors scandal knocked thousands off your 401(k)", True),
        ("Globex Motors CEO on company's turnaround and the AI boom", True),
        ("Globex Motors CEO on Monday resigned after a board review", False),
        ("Globex Motors chief executive resigns", False),
    ],
)
def test_commentary_headlines_open_no_events(title: str, commentary: bool) -> None:
    svc = build_services(Settings(env="test", profile="demo"))
    claims = svc.semantics.claims_for(_article(title))
    assert claims and svc.semantics.is_commentary(_article(title)) is commentary
    assert all(c.event_type == OTHER for c in claims) is commentary
