from datetime import UTC, datetime, timedelta

from newsimpact.market.models import ChannelObservation
from newsimpact.sources.models import SourceType
from newsimpact.storylines.models import (
    ExpectedDecision,
    MarketChannel,
    Playbook,
    PlaybookStage,
    Report,
    Storyline,
    StorylineEvent,
    StorylineStatus,
)
from newsimpact.validation.logic import calibrate_reactions, calibrate_windows, check_decision
from newsimpact.validation.models import (
    Assessment,
    ClaimCheck,
    Provenance,
    StageCheck,
    ValidationPolicy,
)

T = datetime(2026, 3, 1, tzinfo=UTC)
DECISION = ExpectedDecision(actor="investors", decision="sell", market_channel=MarketChannel.PRICE,
                            expected_direction="down")  # fmt: skip


def _assessment(i: int, z: float) -> Assessment:
    obs = ChannelObservation(ticker="X", channel="price", metric="CAR", value=z / 100,
                             statistic=z, direction="down" if z < -1.96 else "flat",
                             significant=z < -1.96, provider="t")  # fmt: skip
    claim = ClaimCheck(status="confirmed", outlets=("a",), origins=("a",), authoritative=True,
                       best_reliability=0.9)  # fmt: skip
    stage = StageCheck(stage=1, stage_name="leader_departure", published_at=T, claim=claim,
                       decisions=(check_decision(DECISION, obs),))  # fmt: skip
    return Assessment(storyline_id=f"s{i}", ticker="X", theme="leadership_crisis",
                      status="resolved",
                      stages=(stage,), market_support=None, confidence="medium", conclusion="",
                      suggestions=(), as_of=T, model_version="t",
                      provenance=Provenance(components={}, reference_data={}))  # fmt: skip


def test_reaction_is_supported_only_with_enough_events(validation_policy: ValidationPolicy) -> None:
    few = calibrate_reactions([_assessment(i, -2.5) for i in range(5)], validation_policy)
    assert few[0].finding == "indicative" and few[0].n_events == 5
    many = calibrate_reactions(
        [_assessment(i, -2.5 + (i % 3) * 0.5) for i in range(25)], validation_policy
    )
    assert many[0].finding == "supported" and many[0].cross_sectional_z is not None


def _story(i: int, gap_days: float) -> Storyline:
    def event(stage: int, at: datetime) -> StorylineEvent:
        report = Report(source_id="a", source_type=SourceType.WIRE, article_id="x",
                        published_at=at, claim_reliability=0.9, origin="a")  # fmt: skip
        return StorylineEvent(claim_id=f"c{stage}", article_id="x", event_type="e", stage=stage,
                              stage_name=f"s{stage}", published_at=at, claim_reliability=0.9,
                              summary="", reports=(report,))  # fmt: skip

    return Storyline(storyline_id=f"s{i}", ticker="X", entity_name="X", theme="t",
                     status=StorylineStatus.RESOLVED,
                     events=(event(0, T), event(1, T + timedelta(days=gap_days))),
                     current_stage=1, max_stage=1, opened_at=T, updated_at=T,
                     model_version="t")  # fmt: skip


def test_window_suggestion_needs_enough_gaps(validation_policy: ValidationPolicy) -> None:
    pb = Playbook(theme="t", description="", link_window_days=30, window_basis="judgment prior",
                  window_why="", triggers=("e",),
                  stages=(PlaybookStage(name="s0", event_types=("e",)),))  # fmt: skip
    (few,) = calibrate_windows([_story(i, 10) for i in range(3)], [pb], validation_policy)
    assert few.suggested_days is None and few.median_days == 10
    (many,) = calibrate_windows([_story(i, 2 + i) for i in range(30)], [pb], validation_policy)
    assert many.suggested_days is not None and many.suggested_days > many.quantile_days  # type: ignore[operator]
