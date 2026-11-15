"""Guidance: priority rules, check wording, and the brief's safety checks."""

from datetime import UTC, date, datetime, timedelta

from newsimpact.app.views.briefs import FORBIDDEN, _safe, rules_brief
from newsimpact.app.views.guidance import checks, close_after, priority

NOW = datetime(2026, 11, 16, 12, tzinfo=UTC)


def test_priority_levels() -> None:
    old, fresh = NOW - timedelta(days=3), NOW - timedelta(hours=2)
    assert priority(confirmed=True, unusual=True, last_update=old, now=NOW)[0] == "act"
    assert priority(confirmed=True, unusual=False, last_update=fresh, now=NOW)[0] == "act"
    assert priority(confirmed=True, unusual=False, last_update=old, now=NOW)[0] == "check"
    assert priority(confirmed=False, unusual=True, last_update=old, now=NOW)[0] == "check"
    assert priority(confirmed=False, unusual=False, last_update=fresh, now=NOW)[0] == "background"


def test_close_after_skips_weekends() -> None:
    assert close_after(date(2026, 11, 13), 1) == date(2026, 11, 16)  # Fri -> Mon
    assert close_after(date(2026, 11, 14), 1) == date(2026, 11, 17)  # Sat counts from Mon


def test_checks_never_give_advice() -> None:
    items = checks(
        url="https://x.test",
        confirmed=False,
        unusual=True,
        final_on=date(2026, 11, 17),
        sector="Information Technology",
        next_update="New leader named",
        window_days=60,
    )
    assert items[0].url == "https://x.test"
    assert not any(FORBIDDEN.search(c.text) for c in items)


def test_brief_checks_reject_advice_and_invented_numbers() -> None:
    facts = {"market": "The stock did 18.5% worse than the S&P 500.", "confirmed": True,
             "latest_update": "Leader steps down", "headline": "CEO resigns", "research": None,
             "next_update": None}  # fmt: skip
    assert _safe("The stock did 18.5% worse than the S&P 500.", facts)
    assert not _safe("Investors should sell now.", facts)
    assert not _safe("The stock fell 25%.", facts)  # 25 is not in the facts
    assert rules_brief(facts).bullets[0].endswith("Confirmed.")
