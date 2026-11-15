from datetime import UTC, datetime

import pytest

from newsimpact.market.models import ChannelObservation
from newsimpact.sources.models import SourceType
from newsimpact.storylines.models import ExpectedDecision, MarketChannel, Report
from newsimpact.validation.logic import (
    check_claim,
    check_decision,
    confidence,
    overlapping,
    verdict,
)
from newsimpact.validation.models import ClaimCheck, StageCheck, ValidationPolicy

T = datetime(2026, 3, 20, tzinfo=UTC)


def _report(
    source_id: str,
    source_type: SourceType = SourceType.MAJOR_OUTLET,
    origin: str | None = None,
    kind: str = "own_reporting",
) -> Report:
    return Report(source_id=source_id, source_type=source_type, article_id="a", published_at=T,
                  claim_reliability=0.8, origin=origin or source_id,
                  attribution_kind=kind)  # fmt: skip


def _obs(direction: str, significant: bool = True) -> ChannelObservation:
    return ChannelObservation(
        ticker="X", channel="price", metric="CAR", value=-0.03, statistic=-2.5,
        direction=direction, significant=significant, provider="t",
    )  # fmt: skip


@pytest.mark.parametrize(
    ("reports", "status"),
    [
        ([_report("a")], "single_source"),
        ([_report("a"), _report("a")], "single_source"),  # same outlet twice is not independent
        ([_report("a"), _report("b")], "corroborated"),
        ([_report("a"), _report("b"), _report("c")], "confirmed"),
        ([_report("ir", SourceType.COMPANY_PRESS_RELEASE)], "confirmed"),
        # three outlets repeating one Bloomberg scoop are ONE origin
        (
            [_report(x, origin="outlet:bloomberg", kind="cites_outlet") for x in "abc"],
            "single_source",
        ),
        ([_report("a", kind="company_statement", origin="company_statement")], "confirmed"),
    ],
)
def test_claim_status(
    reports: list[Report], status: str, validation_policy: ValidationPolicy
) -> None:
    assert check_claim(reports, validation_policy).status == status


@pytest.mark.parametrize(
    ("expected", "obs", "result"),
    [
        ("down", _obs("down"), "consistent"),
        ("up", _obs("down"), "inconsistent"),
        ("down", _obs("flat", significant=False), "not_significant"),
        ("uncertain", _obs("up"), "consistent"),
        ("down", None, "no_evidence"),
    ],
)
def test_verdict(expected: str, obs: ChannelObservation | None, result: str) -> None:
    assert verdict(expected, obs) == result


def test_real_economy_decisions_are_not_measurable() -> None:
    d = ExpectedDecision(actor="board", decision="review", market_channel=None)
    assert check_decision(d, None).verdict == "not_measurable"
    d2 = ExpectedDecision(actor="x", decision="y", market_channel=MarketChannel.PRICE,
                          expected_direction="down")  # fmt: skip
    assert check_decision(d2, _obs("down")).verdict == "consistent"


def _stage(status: str) -> StageCheck:
    claim = ClaimCheck(status=status, outlets=("a",), origins=("a",), authoritative=False,
                       best_reliability=0.8)  # fmt: skip
    return StageCheck(stage=0, stage_name="s", published_at=T, claim=claim, decisions=())


def test_confidence_needs_both_corroboration_and_market_support_for_high(
    validation_policy: ValidationPolicy,
) -> None:
    p = validation_policy
    assert confidence([_stage("confirmed")], 0.8, p) == "high"
    assert confidence([_stage("single_source")], 0.8, p) == "medium"
    assert confidence([_stage("confirmed")], None, p) == "medium"
    assert confidence([_stage("single_source")], 0.1, p) == "low"


def test_pending_when_the_window_is_not_finished() -> None:
    d = ExpectedDecision(actor="x", decision="y", market_channel=MarketChannel.PRICE,
                         expected_direction="down")  # fmt: skip
    assert check_decision(d, None, pending=True).verdict == "pending"


def test_stages_within_a_trading_week_overlap(validation_policy: ValidationPolicy) -> None:
    fri = datetime(2026, 11, 6, tzinfo=UTC)
    times = [fri, fri.replace(day=12), fri.replace(day=13), fri.replace(day=30)]
    # Fri -> Thu = 4 trading days (overlap), Thu -> Fri = 1, Fri -> Mon 2+ weeks = no
    assert overlapping(times, validation_policy) == [False, True, True, False]
