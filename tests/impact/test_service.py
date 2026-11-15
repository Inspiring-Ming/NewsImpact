from datetime import UTC, datetime

from newsimpact.impact.adapters.json_file import JsonRelationshipGraph
from newsimpact.impact.adapters.memory import InMemoryImpactStore
from newsimpact.impact.service import ImpactService
from newsimpact.reliability.models import ClaimReliability, ClaimsScored, ReliabilityScore
from newsimpact.semantics.models import Claim, EntityMention
from newsimpact.shared.bus import InMemoryEventBus

T = datetime(2026, 3, 12, tzinfo=UTC)


def _scored(sentiment: float) -> ClaimsScored:
    claim = Claim(
        claim_id="c1", article_id="a1", text="x", sentiment=sentiment, model_version="t",
        entities=(EntityMention(name="Globex", entity_type="company", ticker="GLBX"),),
    )  # fmt: skip
    score = ReliabilityScore(source_id="s", score=0.8, ci_low=0.7, ci_high=0.9,
                             evidence_count=10, as_of=T, model_version="t")  # fmt: skip
    rel = ClaimReliability(claim_id="c1", source_reliability=0.8, score=0.8, as_of=T,
                           model_version="t")  # fmt: skip
    return ClaimsScored(
        article_id="a1", source_id="s", published_at=T,
        source_reliability=score, claims=(claim,), claim_reliability=(rel,),
    )  # fmt: skip


def _run(sentiment: float) -> InMemoryImpactStore:
    bus, store = InMemoryEventBus(), InMemoryImpactStore()
    graph = JsonRelationshipGraph({"GLBX": [("ORBT", "competitor", -0.25)]})
    ImpactService(bus, graph, store)
    bus.publish(_scored(sentiment).to_envelope("/test"))
    return store


def test_negative_news_helps_competitor() -> None:
    store = _run(-0.6)
    direct = store.by_ticker("GLBX")[0]
    rival = store.by_ticker("ORBT")[0]
    assert direct.direction < 0 < rival.direction
    assert rival.confidence < direct.confidence


def test_neutral_news_is_not_propagated() -> None:
    store = _run(0.0)
    assert store.by_ticker("GLBX")
    assert not store.by_ticker("ORBT")
