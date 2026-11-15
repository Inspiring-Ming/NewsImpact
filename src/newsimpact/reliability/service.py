"""Score outlets and claims; learn from outcomes (the feedback loop)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from newsimpact.reliability.logic import (
    MODEL_VERSION,
    PRIOR_MEANS,
    PRIORS,
    beta_posterior,
    claim_reliability,
)
from newsimpact.reliability.models import ClaimReliability, ClaimsScored, ReliabilityScore
from newsimpact.reliability.ports import EvidenceStore, TrackedSources
from newsimpact.semantics.models import ClaimsExtracted
from newsimpact.shared.bus import EventBus
from newsimpact.shared.events import EventEnvelope
from newsimpact.sources.models import Source, SourceRegistered, SourceType

EVENT_SOURCE = "/reliability"
# Evidence topic for the corroboration record (see set_corroboration).
CORROBORATION = "corroboration"


class ReliabilityService:
    def __init__(self, bus: EventBus, sources: TrackedSources, evidence: EvidenceStore) -> None:
        self._bus = bus
        self._sources = sources
        self._evidence = evidence
        bus.subscribe(SourceRegistered.EVENT_TYPE, self.on_source_registered)
        bus.subscribe(ClaimsExtracted.EVENT_TYPE, self.on_claims_extracted)

    # ------------------------------------------------------------ queries
    def sources(self) -> Sequence[Source]:
        return self._sources.all()

    def score_source(self, source_id: str, topic: str = "all") -> ReliabilityScore:
        source_type = self._source_type(source_id)
        supported, refuted = self._evidence.counts(source_id, topic)
        if topic == "all":  # plus the corroboration record rebuilt each round
            s2, r2 = self._evidence.counts(source_id, CORROBORATION)
            supported, refuted = supported + s2, refuted + r2
        mean, low, high = beta_posterior(PRIORS[source_type], supported, refuted)
        return ReliabilityScore(
            source_id=source_id,
            topic=topic,
            score=round(mean, 6),
            ci_low=round(low, 6),
            ci_high=round(high, 6),
            evidence_count=supported + refuted,
            prior=PRIOR_MEANS[source_type],
            supported=supported,
            refuted=refuted,
            as_of=datetime.now(UTC),
            model_version=MODEL_VERSION,
        )

    def _source_type(self, source_id: str) -> SourceType:
        source = self._sources.get(source_id)
        return source.source_type if source else SourceType.UNKNOWN

    # ------------------------------------------------------ feedback loop
    def record_outcome(self, source_id: str, topic: str, *, supported: bool) -> None:
        """Called when a claim is later confirmed or retracted."""
        self._evidence.record(source_id, topic, supported)
        if topic != "all":
            self._evidence.record(source_id, "all", supported)

    def set_corroboration(self, source_id: str, confirmed: float, unconfirmed: float) -> None:
        """Replace a source's corroboration record: reports later confirmed by an independent
        source count for it; reports never confirmed count against it (already weighted)."""
        self._evidence.replace(source_id, CORROBORATION, confirmed, unconfirmed)

    # ----------------------------------------------------- event handlers
    def on_source_registered(self, envelope: EventEnvelope) -> None:
        self._sources.upsert(SourceRegistered.model_validate(envelope.data).source)

    def on_claims_extracted(self, envelope: EventEnvelope) -> None:
        event = ClaimsExtracted.model_validate(envelope.data)
        source_score = self.score_source(event.source_id)
        claim_scores = tuple(
            ClaimReliability(
                claim_id=c.claim_id,
                source_reliability=source_score.score,
                score=claim_reliability(source_score.score, is_speculative=c.is_speculative),
                as_of=source_score.as_of,
                model_version=MODEL_VERSION,
            )
            for c in event.claims
        )
        self._bus.publish(
            ClaimsScored(
                article_id=event.article_id,
                source_id=event.source_id,
                source_type=self._source_type(event.source_id),
                published_at=event.published_at,
                source_reliability=source_score,
                claims=event.claims,
                claim_reliability=claim_scores,
            ).follow(EVENT_SOURCE, envelope)
        )
