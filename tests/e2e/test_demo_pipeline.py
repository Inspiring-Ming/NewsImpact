"""Whole system on the fictional dataset, through the real wiring."""

import pytest

from newsimpact.app.config import Settings
from newsimpact.app.demo import DemoRun, run_demo
from newsimpact.app.wiring import Services, build_services
from newsimpact.storylines.models import StorylineStatus


@pytest.fixture(scope="module")
def demo() -> tuple[Services, DemoRun]:
    svc = build_services(Settings(env="test", profile="demo"))
    return svc, run_demo(svc)


def test_feeds_dedupe_and_follow_up_discovery(demo: tuple[Services, DemoRun]) -> None:
    svc, run = demo
    assert run.from_feeds == 5  # incl. 1 syndicated copy, kept but marked as a copy
    # probe, CEO departure (3 outlets incl. the company), successor - not in any feed
    assert run.from_follow_up == 5
    assert not svc.bus.dead_letters
    assert all(e.correlation_id for e in svc.bus.published if e.source != "/sources")


def test_every_listed_outlet_is_tracked(demo: tuple[Services, DemoRun]) -> None:
    svc, _ = demo
    listed = {s.source_id for s in svc.sources.listed()}
    assert {s.source_id for s in svc.reliability.sources()} == listed


def test_leadership_storyline_is_chained_and_resolved(demo: tuple[Services, DemoRun]) -> None:
    svc, _ = demo
    storylines = {(s.ticker, s.theme): s for s in svc.storyline_store.all()}
    crisis = storylines[("GLBX", "leadership_crisis")]
    assert [e.stage_name for e in crisis.events] == [
        "public_pressure", "leader_departure", "succession",
    ]  # fmt: skip
    assert crisis.status is StorylineStatus.RESOLVED

    safety = storylines[("GLBX", "product_safety")]
    assert [e.stage_name for e in safety.events] == ["recall", "regulatory_action"]
    assert safety.status is StorylineStatus.ESCALATING


def test_reliability_and_rumour_discount(demo: tuple[Services, DemoRun]) -> None:
    svc, _ = demo
    assert svc.reliability.score_source("wire-alpha").score > 0.85
    assert svc.reliability.score_source("rumor-blog").score < 0.5
    rumour = [e for s in svc.storyline_store.all() if s.ticker == "HLXC" for e in s.events]
    assert rumour and max(e.claim_reliability for e in rumour) < 0.4  # blog + rumour wording


def test_departure_shows_negative_abnormal_return(demo: tuple[Services, DemoRun]) -> None:
    svc, _ = demo
    assert svc.market is not None
    crisis = next(s for s in svc.storyline_store.all() if s.theme == "leadership_crisis")
    departure = crisis.events[1]
    res = svc.market.event_study("GLBX", departure.published_at, (0, 1))
    assert res.cumulative_abnormal_return < -0.02


def test_departure_is_confirmed_by_three_outlets_including_the_company(
    demo: tuple[Services, DemoRun],
) -> None:
    svc, _ = demo
    crisis = next(s for s in svc.storyline_store.all() if s.theme == "leadership_crisis")
    assessment = svc.validation.assess(crisis)
    departure = assessment.stages[1]
    assert departure.claim.status == "confirmed" and departure.claim.authoritative
    assert set(departure.claim.outlets) == {"globex-ir", "wire-alpha", "daily-markets"}
    assert "company_statement" in departure.claim.origins
    assert assessment.stages[0].claim.status == "single_source"


def test_assessment_checks_expected_decisions_against_the_market(
    demo: tuple[Services, DemoRun],
) -> None:
    svc, _ = demo
    crisis = next(s for s in svc.storyline_store.all() if s.theme == "leadership_crisis")
    a = svc.validation.assess(crisis)
    price = next(d for d in a.stages[1].decisions if d.channel == "price")
    assert price.verdict == "consistent" and price.evidence is not None
    assert any(d.verdict == "not_measurable" for s in a.stages for d in s.decisions)
    assert a.market_support is not None and a.conclusion and a.suggestions
    assert a.provenance.components["semantics"].startswith("sentence-extractor")
    assert "reference/taxonomy.json" in a.provenance.reference_data


def test_syndicated_copy_is_marked_and_not_independent(demo: tuple[Services, DemoRun]) -> None:
    svc, _ = demo
    copies = [a for a in svc.articles.recent(100) if a.copy_of]
    assert [(a.source_id, a.copy_of_source) for a in copies] == [("daily-markets", "wire-alpha")]
