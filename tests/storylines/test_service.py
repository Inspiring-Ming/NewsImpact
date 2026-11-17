from datetime import UTC, datetime, timedelta
from pathlib import Path

from newsimpact.app.views.companies import _reading
from newsimpact.reliability.models import ClaimReliability, ClaimsScored, ReliabilityScore
from newsimpact.semantics.models import Claim, EntityMention
from newsimpact.shared.bus import InMemoryEventBus
from newsimpact.storylines.adapters.json_file import JsonPlaybookCatalog
from newsimpact.storylines.adapters.memory import InMemoryStorylineStore
from newsimpact.storylines.models import StorylineStatus, StorylineUpdated
from newsimpact.storylines.service import StorylinesService

PLAYBOOKS = Path(__file__).resolve().parents[2] / "data" / "reference" / "playbooks.json"
CATALOG = JsonPlaybookCatalog.from_file(PLAYBOOKS)
T0 = datetime(2026, 3, 16, tzinfo=UTC)


class Harness:
    def __init__(self) -> None:
        self.bus = InMemoryEventBus()
        self.store = InMemoryStorylineStore()
        StorylinesService(self.bus, self.store, JsonPlaybookCatalog.from_file(PLAYBOOKS))
        self._n = 0

    def news(
        self, event_type: str, days: int = 0, ticker: str = "GLBX", source: str = "s"
    ) -> StorylineUpdated | None:
        self._n += 1
        at = T0 + timedelta(days=days)
        cid = f"c{self._n}"
        claim = Claim(
            claim_id=cid, article_id=f"a{self._n}", text=event_type, sentiment=-0.5,
            event_type=event_type, model_version="t",
            entities=(EntityMention(name="Globex Motors", entity_type="company", ticker=ticker),),
        )  # fmt: skip
        score = ReliabilityScore(source_id="s", score=0.9, ci_low=0.8, ci_high=1, evidence_count=9,
                                 as_of=at, model_version="t")  # fmt: skip
        rel = ClaimReliability(claim_id=cid, source_reliability=0.9, score=0.9, as_of=at,
                               model_version="t")  # fmt: skip
        before = len(self.bus.published)
        self.bus.publish(ClaimsScored(article_id=f"a{self._n}", source_id=source, published_at=at,
                                      source_reliability=score, claims=(claim,),
                                      claim_reliability=(rel,)).to_envelope("/test"))  # fmt: skip
        out = [e for e in self.bus.published[before:] if e.type == StorylineUpdated.EVENT_TYPE]
        return StorylineUpdated.model_validate(out[0].data) if out else None


def test_apology_departure_succession_chain() -> None:
    h = Harness()
    opened = h.news("leadership_apology")
    assert opened and opened.is_new and opened.storyline.theme == "leadership_crisis"
    assert opened.follow_up and "steps down" in opened.follow_up.terms
    assert any(d.actor == "institutional_investors" for d in opened.expected_decisions)

    departed = h.news("leadership_departure", days=4)
    assert departed and departed.escalated and not departed.is_new
    assert departed.storyline.status is StorylineStatus.ESCALATING
    assert departed.storyline.storyline_id == opened.storyline.storyline_id

    succeeded = h.news("leadership_appointment", days=11)
    assert succeeded and succeeded.storyline.status is StorylineStatus.RESOLVED
    assert succeeded.follow_up is None
    assert [e.stage for e in succeeded.storyline.events] == [0, 1, 2]


def test_non_trigger_event_does_not_open_storyline() -> None:
    assert Harness().news("legal_resolution") is None  # an outcome needs its case first


def test_a_standalone_lawsuit_opens_a_legal_event_but_joins_an_open_recall() -> None:
    h = Harness()
    suit = h.news("litigation")
    fine = h.news("regulatory_action", days=3, source="other")
    settled = h.news("legal_resolution", days=40)
    assert suit and suit.storyline.theme == "legal_regulatory"
    assert fine and settled and settled.storyline.storyline_id == suit.storyline.storyline_id
    legal = next(p for p in CATALOG.playbooks() if p.theme == "legal_regulatory")
    assert _reading(fine.storyline, legal) == "mixed"  # a regulator and a lawsuit
    recall = Harness()
    first = recall.news("product_recall", ticker="ACME")
    probe = recall.news("regulatory_action", days=5, ticker="ACME")
    assert first and probe and probe.storyline.theme == "product_safety"


def test_dividends_and_buybacks_read_raised_or_cut() -> None:
    h = Harness()
    raised = h.news("capital_return_up")
    assert raised and raised.storyline.theme == "capital_return"
    payout = next(p for p in CATALOG.playbooks() if p.theme == "capital_return")
    assert _reading(raised.storyline, payout) == "raised"
    assert payout.expectation(("raised", "payout_change")).expected == "up"  # type: ignore[union-attr]


def test_event_outside_window_opens_new_storyline() -> None:
    h = Harness()
    first = h.news("leadership_apology")
    later = h.news("leadership_departure", days=90)  # beyond the 60-day link window
    assert first and later and later.is_new
    assert later.storyline.storyline_id != first.storyline.storyline_id


def test_other_company_gets_its_own_storyline() -> None:
    h = Harness()
    h.news("leadership_apology", ticker="GLBX")
    other = h.news("leadership_departure", days=1, ticker="ACMX")
    assert other and other.is_new and other.storyline.ticker == "ACMX"


def test_same_stage_from_another_outlet_corroborates_instead_of_repeating() -> None:
    h = Harness()
    h.news("leadership_apology", source="wire")
    first = h.news("leadership_departure", days=4, source="wire")
    again = h.news("leadership_departure", days=4, source="paper")
    assert first and again and again.corroborated and not again.escalated
    assert again.expected_decisions == ()  # decisions were already announced
    (storyline,) = h.store.all()
    assert [e.stage_name for e in storyline.events] == ["public_pressure", "leader_departure"]
    assert [r.source_id for r in storyline.events[1].reports] == ["wire", "paper"]


def test_same_outlet_repeating_itself_is_not_corroboration() -> None:
    h = Harness()
    h.news("leadership_apology", source="wire")
    assert h.news("leadership_apology", days=1, source="wire") is None


def test_resolved_storyline_absorbs_late_reports_but_new_trigger_starts_new_story() -> None:
    h = Harness()
    h.news("leadership_departure", source="wire")
    resolved = h.news("leadership_appointment", days=2, source="wire")
    assert resolved and resolved.storyline.status.value == "resolved"
    late = h.news("leadership_departure", days=3, source="paper")  # late report, known stage
    assert late and late.corroborated and late.storyline.status.value == "resolved"
    fresh = h.news("leadership_apology", days=10, source="wire")  # weeks later: a new storyline
    assert fresh and fresh.is_new


def test_out_of_order_reports_join_the_resolved_story_without_reopening_it() -> None:
    """As with Nvidia: 'interim CEO in charge' was published before the resignation storyline."""
    h = Harness()
    opened = h.news("leadership_misconduct", source="bbc")
    h.news("leadership_appointment", days=3, source="bbc")  # resolves the storyline
    late = h.news("leadership_departure", days=3, source="nyt")  # same day, published later
    assert opened and late and not late.is_new
    assert late.storyline.storyline_id == opened.storyline.storyline_id
    assert late.storyline.status.value == "resolved"
    assert sorted(e.stage_name for e in late.storyline.events) == [
        "leader_departure", "public_pressure", "succession",
    ]  # fmt: skip


def test_a_new_leader_named_on_its_own_starts_an_event() -> None:
    named = Harness().news("leadership_appointment")  # a planned succession, no departure first
    assert named and named.is_new and named.storyline.theme == "leadership_crisis"


def test_a_results_release_is_one_event_even_when_reports_disagree() -> None:
    h = Harness()
    beat = h.news("earnings_positive", source="outlet-a")
    miss = h.news(
        "earnings_negative", days=1, source="outlet-b"
    )  # "...yet the outlook disappointed"
    assert beat and miss and beat.storyline.theme == "results"
    assert miss.storyline.storyline_id == beat.storyline.storyline_id
    reports = miss.storyline.events[0].reports
    assert [r.event_type for r in reports] == ["earnings_positive", "earnings_negative"]
    results = next(p for p in CATALOG.playbooks() if p.theme == "results")
    assert _reading(beat.storyline, results) == "better than expected"
    assert _reading(miss.storyline, results) == "mixed"  # shown as "Results · mixed"


def test_a_dividend_announced_with_results_is_part_of_the_results_event() -> None:
    results = next(p for p in CATALOG.playbooks() if p.theme == "results")
    assert "capital_return_up" in results.absorbs and results.absorbs_why
    service = StorylinesService(InMemoryEventBus(), InMemoryStorylineStore(), CATALOG)
    who = (EntityMention(name="Globex Motors", entity_type="company", ticker="GLBX"),)
    claims = [Claim(claim_id=f"c{t}", article_id="a", text=t, event_type=t, model_version="t",
                    entities=who) for t in ("earnings_positive", "capital_return_up")]  # fmt: skip
    assert service._absorbed(claims) == {
        ("GLBX", "capital_return_up"),
        ("GLBX", "capital_return_down"),
    }
    assert service._absorbed(claims[1:]) == set()  # a dividend on its own is its own event
