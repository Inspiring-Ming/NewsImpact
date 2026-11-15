"""Map reliability-weighted claims onto tickers and propagate through the graph."""

from __future__ import annotations

from datetime import UTC, datetime

from newsimpact.impact.models import ImpactAssessed, ImpactAssessment
from newsimpact.impact.ports import ImpactStore, RelationshipGraph
from newsimpact.reliability.models import ClaimsScored
from newsimpact.semantics.models import Claim
from newsimpact.shared.bus import EventBus
from newsimpact.shared.events import EventEnvelope

EVENT_SOURCE = "/impact"
MODEL_VERSION = "impact-graph-v0.1"
NOVELTY_FLOOR = 0.2  # stale news still matters a little


def _clip(x: float) -> float:
    return round(max(-1.0, min(1.0, x)), 6)


class ImpactService:
    def __init__(self, bus: EventBus, graph: RelationshipGraph, store: ImpactStore) -> None:
        self._bus = bus
        self._graph = graph
        self._store = store
        bus.subscribe(ClaimsScored.EVENT_TYPE, self.on_claims_scored)

    def on_claims_scored(self, envelope: EventEnvelope) -> None:
        event = ClaimsScored.model_validate(envelope.data)
        reliability = {r.claim_id: r.score for r in event.claim_reliability}
        now = datetime.now(UTC)
        out: list[ImpactAssessment] = []

        def add(claim: Claim, ticker: str, relation: str, direction: float, conf: float) -> None:
            out.append(
                ImpactAssessment(
                    claim_id=claim.claim_id,
                    ticker=ticker,
                    aspect=claim.aspect,
                    relation=relation,
                    direction=_clip(direction),
                    confidence=round(conf, 6),
                    as_of=now,
                    model_version=MODEL_VERSION,
                )
            )

        for claim in event.claims:
            conf = reliability.get(claim.claim_id, 0.0)
            signal = claim.sentiment * max(claim.novelty, NOVELTY_FLOOR)
            for entity in claim.entities:
                if entity.ticker is None:
                    continue
                add(claim, entity.ticker, "direct", signal, conf)
                if signal == 0:
                    continue  # neutral news: record the mention, don't propagate
                for related, relation, weight in self._graph.related(entity.ticker):
                    add(claim, related, relation, signal * weight, conf * abs(weight))

        if out:
            self._store.add_many(out)
            self._bus.publish(
                ImpactAssessed(article_id=event.article_id, assessments=tuple(out)).follow(
                    EVENT_SOURCE, envelope
                )
            )
