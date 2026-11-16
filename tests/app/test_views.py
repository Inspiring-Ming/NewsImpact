"""Guidance: priority rules, check wording, and the brief's safety checks."""

from datetime import UTC, date, datetime, timedelta

from newsimpact.app.views.briefs import _safe, rules_brief
from newsimpact.app.views.guidance import checks, close_after, priority
from newsimpact.shared.guardrails import ADVICE

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
    assert not any(ADVICE.search(c.text) for c in items)


def test_brief_checks_reject_advice_and_invented_numbers() -> None:
    facts = {"market": "The stock did 18.5% worse than the S&P 500.", "confirmed": True,
             "latest_update": "Leader steps down", "headline": "CEO resigns", "research": None,
             "next_update": None}  # fmt: skip
    assert _safe("The stock did 18.5% worse than the S&P 500.", facts)
    assert not _safe("Investors should sell now.", facts)
    assert not _safe("The stock fell 25%.", facts)  # 25 is not in the facts
    assert rules_brief(facts).bullets[0].endswith("Confirmed.")


class FakeLlm:
    """Stands in for the LLM gateway: returns a fixed answer, or fails."""

    def __init__(self, data: dict[str, str] | None = None, error: Exception | None = None) -> None:
        self.data, self.error = data, error

    def complete_json(self, request: object) -> object:
        if self.error:
            raise self.error
        from newsimpact.llm.models import LlmResult

        return LlmResult(data=self.data or {}, model="fake", cost_usd=0.0, cached=False)


FACTS = {"market": "The stock did 18.5% worse than the S&P 500.", "confirmed": True,
         "latest_update": "Leader steps down", "headline": "CEO resigns", "research": None,
         "next_update": None}  # fmt: skip


def test_ai_brief_is_used_only_when_it_passes_the_checks() -> None:
    from newsimpact.app.views.briefs import ai_brief
    from newsimpact.llm.models import BudgetExceededError

    good = {"what_happened": "The CEO resigned; confirmed.",
            "market": "The stock did 18.5% worse than the S&P 500.",
            "why_it_matters": "Leadership changes raise price swings."}  # fmt: skip
    brief = ai_brief(FakeLlm(good), FACTS)  # type: ignore[arg-type]
    assert brief is not None and brief.by == "ai"
    advice = {**good, "why_it_matters": "Investors should sell."}
    assert ai_brief(FakeLlm(advice), FACTS) is None  # type: ignore[arg-type]
    assert ai_brief(FakeLlm(error=BudgetExceededError("cap")), FACTS) is None  # type: ignore[arg-type]
    assert ai_brief(FakeLlm(error=RuntimeError("down")), FACTS) is None  # type: ignore[arg-type]
