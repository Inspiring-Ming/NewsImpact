"""Assess storylines against independent evidence; calibrate playbooks across storylines.

assess()            one storyline now (API, report)
assess_and_store()  many storylines, keeping history (each monitoring round)
calibrate()         does each stage really move each channel? are link windows right?
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from newsimpact.market.models import ChannelObservation, WindowNotComplete
from newsimpact.storylines.models import ExpectedDecision, Report, Storyline, StorylineEvent
from newsimpact.validation.logic import (
    MODEL_VERSION,
    calibrate_reactions,
    calibrate_windows,
    check_claim,
    check_decision,
    conclude,
    confidence,
    market_support,
    overlapping,
    track_records,
)
from newsimpact.validation.models import (
    Assessment,
    DecisionCheck,
    Provenance,
    StageChannelCalibration,
    StageCheck,
    TrackRecord,
    ValidationPolicy,
    WindowCalibration,
)
from newsimpact.validation.ports import AssessmentStore, MarketEvidence, Playbooks

log = logging.getLogger(__name__)


class ValidationService:
    def __init__(
        self,
        playbooks: Playbooks,
        market: MarketEvidence | None,
        store: AssessmentStore,
        policy: ValidationPolicy,
        provenance: Provenance,
        current_reliability: Callable[[str, bool], float] | None = None,
    ) -> None:
        """`current_reliability(source_id, is_rumour)`: today's chance a report from that source
        holds up. Given, claims are re-scored with it, so confidence follows each source's
        track record; otherwise the score stored when the report arrived is used."""
        self._playbooks = {p.theme: p for p in playbooks.playbooks()}
        self._reliability = current_reliability
        self._market = market
        self._store = store
        self._policy = policy
        self._provenance = provenance

    def assess(self, storyline: Storyline) -> Assessment:
        playbook = self._playbooks[storyline.theme]
        events = sorted(
            storyline.events, key=lambda e: e.published_at
        )  # in the order they happened
        close = overlapping([e.published_at for e in events], self._policy)
        stages = tuple(
            StageCheck(
                stage=e.stage,
                stage_name=e.stage_name,
                published_at=e.published_at,
                claim=check_claim(self._rescored(e), self._policy),
                decisions=tuple(
                    self._check(storyline.ticker, d, e.published_at)
                    for d in playbook.stages[e.stage].decisions
                ),
                overlaps_previous=close[i],
            )
            for i, e in enumerate(events)
        )
        combined = self._combined(storyline.ticker, events, close)
        support = market_support(stages)
        text, suggestions = conclude(storyline, playbook, stages, support, combined)
        return Assessment(
            storyline_id=storyline.storyline_id,
            ticker=storyline.ticker,
            theme=storyline.theme,
            status=storyline.status.value,
            stages=stages,
            combined_reaction=combined,
            market_support=support,
            confidence=confidence(stages, support, self._policy),
            conclusion=text,
            suggestions=suggestions,
            as_of=datetime.now(UTC),
            model_version=MODEL_VERSION,
            provenance=self._provenance,
        )

    def assess_and_store(self, storylines: Sequence[Storyline]) -> list[Assessment]:
        """Re-assess and keep the result when anything changed (new stage, matured evidence)."""
        changed = []
        for story in storylines:
            fresh = self.assess(story)
            previous = self._store.latest(story.storyline_id)
            if previous is None or _fingerprint(previous) != _fingerprint(fresh):
                self._store.add(fresh)
                changed.append(fresh)
        return changed

    def latest(self, storyline_id: str) -> Assessment | None:
        """The stored assessment, unless it was made under older rules (then re-assess)."""
        found = self._store.latest(storyline_id)
        return found if found and found.model_version == MODEL_VERSION else None

    def _rescored(self, event: StorylineEvent) -> tuple[Report, ...]:
        if self._reliability is None:
            return event.reports
        score = self._reliability
        return tuple(
            r.model_copy(update={"claim_reliability": score(r.source_id, event.is_rumour)})
            for r in event.reports
        )

    @property
    def policy(self) -> ValidationPolicy:
        return self._policy

    def track_records(self, now: datetime | None = None) -> list[TrackRecord]:
        """Per source: reports later confirmed by an independent origin vs. never confirmed."""
        return track_records(self._store.latest_all(), now or datetime.now(UTC), self._policy)

    def calibrate(
        self, storylines: Sequence[Storyline]
    ) -> tuple[list[StageChannelCalibration], list[WindowCalibration]]:
        reactions = calibrate_reactions(self._store.latest_all(), self._policy)
        windows = calibrate_windows(storylines, list(self._playbooks.values()), self._policy)
        return reactions, windows

    def _combined(
        self, ticker: str, events: list[StorylineEvent], close: list[bool]
    ) -> ChannelObservation | None:
        """One reaction for the first run of stages too close to separate (not the whole story)."""
        if self._market is None or not any(close):
            return None
        start = close.index(True) - 1
        end = start + 1
        while end + 1 < len(close) and close[end + 1]:
            end += 1
        try:
            return self._market.observe_span(ticker, events[start].published_at,
                                             events[end].published_at)  # fmt: skip
        except ValueError:  # incl. WindowNotComplete: measured in a later round
            return None

    def _check(self, ticker: str, decision: ExpectedDecision, at: datetime) -> DecisionCheck:
        channel = decision.market_channel.value if decision.market_channel else None
        if channel is None or self._market is None:
            return check_decision(decision, None)
        try:
            return check_decision(decision, self._market.observe(ticker, channel, at))
        except WindowNotComplete:
            return check_decision(decision, None, pending=True)
        except ValueError:  # e.g. not enough price history before the event
            log.warning("no market evidence", extra={"ticker": ticker, "channel": channel})
            return check_decision(decision, None)


def _fingerprint(a: Assessment) -> str:
    """What makes two assessments different (ignores the timestamp)."""
    return a.model_copy(update={"as_of": datetime.min.replace(tzinfo=UTC)}).model_dump_json()
