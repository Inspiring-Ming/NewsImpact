"""Link claims into storylines using playbooks.

Linking rule (v0.2, deterministic and explainable):
  1. A claim is relevant if its event type appears in some playbook.
  2. If a storyline exists for the same ticker + theme and its last event
     was within that playbook's link window, the claim belongs to it:
       * a stage it already has  -> another outlet's report (corroboration);
       * a new stage             -> the storyline moves on (maybe escalates/resolves);
     outlets report events out of order, so a resolved storyline still absorbs
     reports of its earlier stages published within `late_report_days` of its
     latest stage, without being reopened; later reports start a new storyline.
  3. Otherwise the claim opens a new storyline if its event type is one of
     that playbook's triggers.
Roadmap: embedding similarity and LLM adjudication for ambiguous links.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from newsimpact.reliability.models import ClaimsScored
from newsimpact.semantics.models import OTHER, Claim, EntityMention
from newsimpact.shared.bus import EventBus
from newsimpact.shared.events import EventEnvelope
from newsimpact.shared.text import stable_id
from newsimpact.storylines.models import (
    FollowUpRequest,
    Playbook,
    Report,
    Storyline,
    StorylineEvent,
    StorylineStatus,
    StorylineUpdated,
)
from newsimpact.storylines.ports import PlaybookCatalog, StorylineStore

EVENT_SOURCE = "/storylines"
MODEL_VERSION = "storylines-playbook-v0.2"


class StorylinesService:
    def __init__(self, bus: EventBus, store: StorylineStore, catalog: PlaybookCatalog) -> None:
        self._bus = bus
        self._store = store
        self._catalog = catalog
        bus.subscribe(ClaimsScored.EVENT_TYPE, self.on_claims_scored)

    def on_claims_scored(self, envelope: EventEnvelope) -> None:
        event = ClaimsScored.model_validate(envelope.data)
        reliability = {r.claim_id: r.score for r in event.claim_reliability}
        seen: set[tuple[str, str]] = set()
        for claim in event.claims:
            entity = next((e for e in claim.entities if e.ticker), None)
            if claim.event_type == OTHER or entity is None or entity.ticker is None:
                continue
            key = (entity.ticker, claim.event_type)
            if key in seen:  # one storyline event per ticker/event type per article
                continue
            seen.add(key)
            report = Report(
                source_id=event.source_id,
                source_type=event.source_type,
                article_id=claim.article_id,
                published_at=event.published_at,
                claim_reliability=reliability.get(claim.claim_id, 0.0),
                origin=claim.attribution.origin(event.source_id),
                attribution_kind=claim.attribution.kind,
                event_type=claim.event_type,
            )
            self._apply(claim, entity, report, envelope)

    # ------------------------------------------------------------- linking
    def _apply(
        self, claim: Claim, entity: EntityMention, report: Report, cause: EventEnvelope
    ) -> None:
        ticker = entity.ticker or ""
        storyline, playbook = self._find_open(ticker, claim.event_type, report.published_at)
        if playbook is None:
            playbook = next(
                (p for p in self._catalog.playbooks() if claim.event_type in p.triggers), None
            )
            if playbook is None:
                return  # relevant event type, but cannot start a storyline on its own
        stage = playbook.stage_of(claim.event_type)
        if stage is None:
            return

        known = next((e for e in storyline.events if e.stage == stage), None) if storyline else None
        if storyline is not None and known is not None:
            self._corroborate(storyline, known, report, playbook, cause)
        else:
            self._advance(storyline, playbook, stage, claim, entity, report, cause)

    def _corroborate(
        self,
        storyline: Storyline,
        known: StorylineEvent,
        report: Report,
        playbook: Playbook,
        cause: EventEnvelope,
    ) -> None:
        if any(r.source_id == report.source_id for r in known.reports):
            return  # same outlet again: not independent evidence
        updated = known.model_copy(
            update={
                "reports": (*known.reports, report),
                "claim_reliability": max(known.claim_reliability, report.claim_reliability),
            }
        )
        events = tuple(updated if e is known else e for e in storyline.events)
        storyline = storyline.model_copy(
            update={"events": events, "updated_at": max(storyline.updated_at, report.published_at)}
        )
        self._store.save(storyline)
        self._publish(storyline, updated, playbook, cause, corroborated=True)

    def _advance(
        self,
        storyline: Storyline | None,
        playbook: Playbook,
        stage: int,
        claim: Claim,
        entity: EntityMention,
        report: Report,
        cause: EventEnvelope,
    ) -> None:
        stage_def = playbook.stages[stage]
        new_event = StorylineEvent(
            claim_id=claim.claim_id,
            article_id=claim.article_id,
            event_type=claim.event_type,
            stage=stage,
            stage_name=stage_def.name,
            published_at=report.published_at,
            claim_reliability=report.claim_reliability,
            summary=claim.text,
            tone=claim.sentiment,
            is_rumour=claim.is_speculative,
            reports=(report,),
        )
        is_new = storyline is None
        escalated = storyline is not None and stage > storyline.max_stage
        late = storyline is not None and stage < storyline.max_stage  # reported out of order
        resolved_before = storyline is not None and storyline.status is StorylineStatus.RESOLVED
        if stage_def.resolves or (late and resolved_before):
            status = StorylineStatus.RESOLVED
        elif escalated:
            status = StorylineStatus.ESCALATING
        elif late and storyline is not None:
            status = storyline.status  # an earlier stage reported late changes nothing
        else:
            status = StorylineStatus.DEVELOPING
        if storyline is None:
            storyline = Storyline(
                storyline_id=stable_id(entity.ticker or "", playbook.theme, claim.claim_id),
                ticker=entity.ticker or "",
                entity_name=entity.name,
                theme=playbook.theme,
                status=status,
                events=(new_event,),
                current_stage=stage,
                max_stage=stage,
                opened_at=report.published_at,
                updated_at=report.published_at,
                model_version=MODEL_VERSION,
            )
        else:
            storyline = storyline.model_copy(
                update={
                    "events": (*storyline.events, new_event),
                    "status": status,
                    "current_stage": max(stage, storyline.current_stage),
                    "max_stage": max(stage, storyline.max_stage),
                    "updated_at": max(report.published_at, storyline.updated_at),
                }
            )
        self._store.save(storyline)
        self._publish(storyline, new_event, playbook, cause, is_new=is_new, escalated=escalated)

    # ------------------------------------------------------------- helpers
    def _publish(
        self,
        storyline: Storyline,
        latest: StorylineEvent,
        playbook: Playbook,
        cause: EventEnvelope,
        *,
        is_new: bool = False,
        escalated: bool = False,
        corroborated: bool = False,
    ) -> None:
        terms = playbook.terms_after(storyline.max_stage)
        follow_up = (
            FollowUpRequest(
                entity_name=storyline.entity_name,
                terms=terms,
                since=latest.published_at,
                until=latest.published_at + timedelta(days=playbook.link_window_days),
            )
            if terms and storyline.status is not StorylineStatus.RESOLVED
            else None
        )
        self._bus.publish(
            StorylineUpdated(
                storyline=storyline,
                latest=latest,
                is_new=is_new,
                escalated=escalated,
                corroborated=corroborated,
                expected_decisions=() if corroborated else playbook.stages[latest.stage].decisions,
                follow_up=follow_up,
            ).follow(EVENT_SOURCE, cause)
        )

    def _find_open(
        self, ticker: str, event_type: str, at: datetime
    ) -> tuple[Storyline | None, Playbook | None]:
        """The storyline this claim belongs to, if any.

        A resolved storyline still absorbs late reports of stages it already
        has (corroboration), but a new stage after resolution starts a new storyline.
        """
        for playbook in self._catalog.playbooks():
            stage = playbook.stage_of(event_type)
            if stage is None:
                continue
            storyline = self._store.latest_for(ticker, playbook.theme)
            if storyline is None or abs(at - storyline.updated_at) > timedelta(
                days=playbook.link_window_days
            ):
                continue
            if storyline.status is StorylineStatus.RESOLVED and (
                stage > storyline.max_stage
                or at - storyline.updated_at > timedelta(days=self._catalog.late_report_days)
            ):
                continue
            return storyline, playbook
        return None, None
