"""Guidance: priority rules, check wording, the brief's safety checks, and how a type's
record is judged against chance."""

from datetime import UTC, date, datetime, timedelta

from newsimpact.app.views.briefs import _safe, rules_brief
from newsimpact.app.views.guidance import checks, close_after, group_record, met, priority
from newsimpact.shared.guardrails import ADVICE
from newsimpact.storylines.models import Expectation

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


def test_moved_as_expected_is_judged_against_chance() -> None:
    assert met("up", 0.001, False) and not met("down", 0.001, False)
    assert met("uncertain", -0.04, True) and not met("uncertain", -0.04, False)
    assert met("flat", 0.01, False) and not met("flat", 0.08, True)
    buyer = Expectation(when="buyer", label="company is the buyer", expected="flat",
                        finding="Buyers move little.", source="A (2001), J")  # fmt: skip
    few = group_record(buyer, [(0.01, False)] * 5, min_events=20, z_needed=1.96)
    assert few.verdict == "too_few" and few.met == 5 and few.chance == 0.95
    up = buyer.model_copy(update={"expected": "up"})
    rises = group_record(up, [(0.02, False)] * 18 + [(-0.01, False)] * 2, min_events=20,
                         z_needed=1.96)  # fmt: skip
    coin = group_record(up, [(0.02, False), (-0.02, False)] * 10, min_events=20, z_needed=1.96)
    assert rises.verdict == "supports" and coin.verdict == "no_pattern"
    falls = group_record(up, [(-0.02, False)] * 20, min_events=20, z_needed=1.96)
    assert falls.verdict == "against" and falls.average == -0.02


def test_companies_are_followed_when_the_news_names_them() -> None:
    from newsimpact.app.following import FollowingPolicy, decide, feed_tickers

    policy = FollowingPolicy(min_articles=3, window_days=7, keep_days=30, max_followed=2,
                             discover_per_round=2)  # fmt: skip
    days = lambda *ago: [NOW - timedelta(days=d) for d in ago]  # noqa: E731
    seen = {"AAA": days(1, 2, 3, 4), "BBB": days(1, 2, 3), "CCC": days(1, 2), "DDD": days(20)}
    first = decide(policy, seen, pinned=(), previous=None, now=NOW)
    assert first.followed == ("AAA", "BBB")  # 3+ articles in 7 days, most named first
    assert first.mentions["CCC"] == 2 and "DDD" not in first.mentions  # outside the window
    # A user's company is always followed, ahead of the cap.
    assert decide(policy, seen, pinned=("ZZZ",), previous=None, now=NOW).followed == ("ZZZ", "AAA")
    # Quiet for less than keep_days: kept; longer: dropped.
    quiet = {"AAA": days(10), "BBB": days(40)}
    assert decide(policy, quiet, (), first, NOW).followed == ("AAA",)
    # Feeds: followed ones, then a discovery slice of the others that moves on each round.
    universe = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    assert feed_tickers(first, universe, 2) == ["AAA", "BBB", "CCC", "DDD"]
    moved = first.model_copy(update={"discover_from": 2})
    assert feed_tickers(moved, universe, 2) == ["AAA", "BBB", "EEE", "CCC"]
    # A company with a recent event stays followed even with few articles.
    assert "EEE" in decide(policy, {}, (), None, NOW, with_events=("EEE",)).followed
