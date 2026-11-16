"""Assessing events: what is measured now, and what must wait for trading days."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from newsimpact.market.models import ChannelObservation, WindowNotComplete
from newsimpact.sources.models import SourceType
from newsimpact.storylines.adapters.json_file import JsonPlaybookCatalog
from newsimpact.storylines.models import Report, Storyline, StorylineEvent, StorylineStatus
from newsimpact.validation.adapters.memory import InMemoryAssessmentStore
from newsimpact.validation.models import Provenance, ValidationPolicy
from newsimpact.validation.service import ValidationService

PLAYBOOKS = Path(__file__).resolve().parents[2] / "data" / "reference" / "playbooks.json"
T = datetime(2026, 11, 9, 20, tzinfo=UTC)


class TooEarlyForTheLastUpdate:
    """Each update can be measured, but the move across all of them needs days not yet traded."""

    def observe(self, ticker: str, channel: str, at: datetime) -> ChannelObservation | None:
        return ChannelObservation(ticker=ticker, channel=channel, metric="CAR", value=-0.05,
                                  statistic=-1.0, direction="flat", significant=False,
                                  provider="t")  # fmt: skip

    def observe_span(self, ticker: str, first: datetime, last: datetime) -> ChannelObservation:
        raise WindowNotComplete("the window after the last update has not closed")


def _event(stage: int, name: str, event_type: str, days: float) -> StorylineEvent:
    at = T + timedelta(days=days)
    report = Report(source_id="a", source_type=SourceType.WIRE, article_id=f"x{stage}",
                    published_at=at, claim_reliability=0.9, origin="a")  # fmt: skip
    return StorylineEvent(claim_id=f"c{stage}", article_id=f"x{stage}", event_type=event_type,
                          stage=stage, stage_name=name, published_at=at, claim_reliability=0.9,
                          summary="", reports=(report,))  # fmt: skip


def test_a_move_across_close_updates_is_pending_until_its_days_have_traded(
    validation_policy: ValidationPolicy,
) -> None:
    catalog = JsonPlaybookCatalog.from_file(PLAYBOOKS)
    provenance = Provenance(components={}, reference_data={})
    service = ValidationService(catalog, TooEarlyForTheLastUpdate(), InMemoryAssessmentStore(),
                                validation_policy, provenance)  # fmt: skip
    events = (_event(0, "public_pressure", "leadership_misconduct", 0),
              _event(1, "leader_departure", "leadership_departure", 2),
              _event(2, "succession", "leadership_appointment", 3.3))  # fmt: skip
    story = Storyline(storyline_id="s", ticker="NVDA", entity_name="Nvidia",
                      theme="leadership_crisis", status=StorylineStatus.RESOLVED, events=events,
                      current_stage=2, max_stage=2, opened_at=T, updated_at=events[-1].published_at,
                      model_version="t")  # fmt: skip
    a = service.assess(story)
    assert a.combined_reaction is None and a.combined_pending  # not silently dropped
